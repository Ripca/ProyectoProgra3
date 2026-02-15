"""
Flask Web Application for UMG Biometric System
Attendance management platform for professors
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime, date
import logging
from pathlib import Path

from config import Config
from database.models import CursoDAO, AsistenciaDAO, InscripcionDAO
from web.auth import authenticate_user, create_session, destroy_session, login_required, catedratico_required
from web.attendance_tree import AttendanceTree
from web.pdf_reports import PDFReportGenerator
from modules.registro.email_sender import EmailSender
from utils.helpers import format_date
import face_recognition
import numpy as np
import base64
import io
from PIL import Image
from database.models import PersonaDAO

# Initialize Flask app
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Home page - redirect to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        success, user_data, message = authenticate_user(email, password)
        
        if success:
            create_session(user_data)
            flash(f'Bienvenido/a {user_data["nombre"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    destroy_session()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - show professor's courses"""
    try:
        user_id = session.get('user_id')
        cursos = CursoDAO.get_by_catedratico(user_id)
        
        return render_template('dashboard.html', cursos=cursos)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error al cargar el dashboard', 'danger')
        return redirect(url_for('login'))


@app.route('/curso/<int:curso_id>/asistencia')
@login_required
@catedratico_required
def ver_asistencia(curso_id):
    """View attendance tree for a course"""
    try:
        # Get attendance data
        attendance_data = AttendanceTree.get_course_attendance(curso_id)
        
        if not attendance_data:
            flash('No se pudo cargar la información de asistencia', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if user is the course professor
        if attendance_data['curso']['catedratico_id'] != session.get('user_id'):
            flash('No tiene permiso para ver este curso', 'danger')
            return redirect(url_for('dashboard'))
        
        return render_template('asistencia.html', data=attendance_data)
        
    except Exception as e:
        logger.error(f"Error viewing attendance: {e}")
        flash('Error al cargar la asistencia', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/curso/<int:curso_id>/confirmar', methods=['POST'])
@login_required
@catedratico_required
def confirmar_asistencia(curso_id):
    """Confirm attendance for a course"""
    try:
        # Get attendance data
        attendance_data = AttendanceTree.get_course_attendance(curso_id)
        
        if not attendance_data:
            flash('No se pudo cargar la información de asistencia', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if user is the course professor
        if attendance_data['curso']['catedratico_id'] != session.get('user_id'):
            flash('No tiene permiso para confirmar este curso', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if already confirmed today
        fecha_hoy = date.today()
        estudiantes = attendance_data['estudiantes']
        
        if estudiantes and AsistenciaDAO.exists(estudiantes[0]['id'], curso_id, fecha_hoy):
            flash('La asistencia de hoy ya fue confirmada anteriormente', 'warning')
            return redirect(url_for('ver_asistencia', curso_id=curso_id))
        
        # Create attendance records
        confirmado_por = session.get('user_id')
        fecha_confirmacion = datetime.now()
        
        attendance_records = []
        for estudiante in estudiantes:
            attendance_records.append((
                estudiante['id'],
                curso_id,
                fecha_hoy,
                estudiante['presente'],
                confirmado_por,
                fecha_confirmacion
            ))
        
        # Batch insert
        AsistenciaDAO.create_batch(attendance_records)
        
        # Generate PDF report
        pdf_filename = f"Asistencia_{attendance_data['curso']['codigo']}_{fecha_hoy.strftime('%Y%m%d')}.pdf"
        pdf_path = Config.REPORTS_DIR / pdf_filename
        
        if PDFReportGenerator.generate_attendance_report(attendance_data, pdf_path):
            # Send email to professor
            catedratico_email = session.get('email')
            EmailSender.send_attendance_report(
                catedratico_email,
                attendance_data['curso']['nombre'],
                pdf_path,
                format_date(fecha_hoy)
            )
            
            flash(f'Asistencia confirmada exitosamente. Reporte enviado a {catedratico_email}', 'success')
            
            # Return PDF for download
            return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
        else:
            flash('Asistencia confirmada pero hubo un error al generar el PDF', 'warning')
            return redirect(url_for('ver_asistencia', curso_id=curso_id))
        
    except Exception as e:
        logger.error(f"Error confirming attendance: {e}")
        flash(f'Error al confirmar asistencia: {str(e)}', 'danger')
        return redirect(url_for('ver_asistencia', curso_id=curso_id))


@app.route('/registro_facial')
def registro_facial():
    """Page for facial registration"""
    return render_template('registro_facial.html')


@app.route('/api/registrar_rostro', methods=['POST'])
def registrar_rostro():
    """API to handle face registration from webcam"""
    try:
        data = request.json
        image_data = data.get('image')
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        email = data.get('email')
        telefono = data.get('telefono')
        tipo_persona = data.get('tipo_persona')
        codigo_carnet = data.get('codigo_carnet')

        if not all([image_data, nombre, apellido, email, tipo_persona, codigo_carnet]):
            return {'success': False, 'message': 'Faltan datos requeridos'}, 400

        # Decode base64 image
        header, encoded = image_data.split(",", 1)
        binary_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(binary_data)).convert('RGB')
        image_np = np.array(image)

        # Detect face
        face_locations = face_recognition.face_locations(image_np)
        if not face_locations:
            return {'success': False, 'message': 'No se detectó ningún rostro'}, 400
        
        if len(face_locations) > 1:
            return {'success': False, 'message': 'Se detectó más de un rostro'}, 400

        # Encode face
        face_encodings = face_recognition.face_encodings(image_np, face_locations)
        if not face_encodings:
             return {'success': False, 'message': 'No se pudo codificar el rostro'}, 400
            
        encoding = face_encodings[0]

        # Save to DB
        # Note: We need to save the image file too ideally, but for now we focus on the encoding
        # Let's save the image to disk
        filename = f"{codigo_carnet}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        filepath = Config.PHOTOS_DIR / filename
        image.save(filepath)

        # Create Persona
        # We need a default password or handle it. Let's assume a default for now or generated one.
        # Ideally this should comes from the form or be auto-generated.
        default_pass = '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2' # "docente123" hash
        
        PersonaDAO.create(
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            email=email,
            tipo_persona=tipo_persona,
            carrera="N/A", # Simple default
            seccion="A", # Simple default
            foto_path=str(filepath),
            encoding_facial=encoding,
            codigo_carnet=codigo_carnet,
            password_hash=default_pass
        )

        return {'success': True, 'message': 'Usuario registrado exitosamente'}

    except Exception as e:
        logger.error(f"Error in registration: {e}")
        return {'success': False, 'message': str(e)}, 500


@app.template_filter('datetime')
def format_datetime_filter(value, format='%d/%m/%Y %H:%M'):
    """Template filter for datetime formatting"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime(format)


def run_web_app(host='0.0.0.0', port=5000, debug=True):
    """Run the Flask web application"""
    logger.info(f"Starting web application on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_web_app()
