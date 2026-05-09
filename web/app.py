"""
Flask Web Application for UMG Biometric System
Attendance management platform for professors
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime, date
import logging
from pathlib import Path

import sys
import os
# Add parent directory to path to allow importing config and database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from database.models import CursoDAO, AsistenciaClaseDAO, AsignacionCursoDAO
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
from PIL import Image
from database.models import PersonaDAO, TipoPersonaDAO, SalonDAO, SeccionDAO, CarreraDAO
from web.id_card_generator import IDCardGenerator
from modules.registro.email_sender import EmailSender
import uuid

# Initialize Flask app
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask import send_from_directory

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from the assets directory"""
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets'), filename)


@app.route('/photos/<path:filename>')
def serve_photos(filename):
    """Serve student photos"""
    return send_from_directory(Config.PHOTOS_DIR, filename)


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


@app.route('/curso/<int:assignment_id>/asistencia')
@login_required
@catedratico_required
def ver_asistencia(assignment_id):
    """View attendance tree for a specific class assignment"""
    try:
        # Get date from query string if present
        fecha_str = request.args.get('fecha')
        fecha_obj = None
        search_performed = False
        if fecha_str:
            try:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                search_performed = True
            except ValueError:
                pass

        # Get attendance data using assignment_id
        attendance_data = AttendanceTree.get_course_attendance(assignment_id, fecha_obj)
        
        if not attendance_data:
            flash('No se pudo cargar la información de asistencia', 'danger')
            return redirect(url_for('dashboard'))
            
        attendance_data['search_performed'] = search_performed
        if not search_performed:
            attendance_data['estudiantes'] = []
            attendance_data['estadisticas'] = {
                'total': 0, 'presentes': 0, 'ausentes': 0, 'porcentaje_asistencia': 0
            }
        
        # Check if user is the assigned professor
        if attendance_data['curso']['catedratico_id'] != session.get('user_id'):
            flash('No tiene permiso para ver esta clase', 'danger')
            return redirect(url_for('dashboard'))
        
        return render_template('asistencia.html', data=attendance_data)
        
    except Exception as e:
        logger.error(f"Error viewing attendance: {e}")
        flash('Error al cargar la asistencia', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/curso/<int:assignment_id>/confirmar', methods=['POST'])
@login_required
@catedratico_required
def confirmar_asistencia(assignment_id):
    """Confirm attendance for a specific class assignment"""
    try:
        # Get date from form if present
        fecha_str = request.form.get('fecha')
        fecha_obj = None
        if fecha_str:
            try:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Get attendance data
        attendance_data = AttendanceTree.get_course_attendance(assignment_id, fecha_obj)
        
        if not attendance_data:
            flash('No se pudo cargar la información de asistencia', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if user is the assigned professor
        if attendance_data['curso']['catedratico_id'] != session.get('user_id'):
            flash('No tiene permiso para confirmar esta clase', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if already confirmed for this date
        fecha_hoy = fecha_obj if fecha_obj else date.today()
        estudiantes = attendance_data['estudiantes']
        curso_id = attendance_data['curso']['id']
        
        if estudiantes and AsistenciaClaseDAO.exists(estudiantes[0]['id'], curso_id, fecha_hoy):
            flash(f'La asistencia para el {fecha_hoy.strftime("%d/%m/%Y")} ya fue confirmada anteriormente', 'warning')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_hoy.strftime('%Y-%m-%d')))
        
        # Create attendance records
        confirmado_por = session.get('user_id')
        
        attendance_records = []
        # Get salon_id from the assignment data
        salon_id = attendance_data['assignment']['salon_id']
        
        for estudiante in estudiantes:
            attendance_records.append((
                estudiante['id'],
                curso_id,
                salon_id,
                datetime.combine(fecha_hoy, datetime.now().time()),
                'MANUAL',
                confirmado_por,
                None
            ))
        
        # Batch insert
        AsistenciaClaseDAO.create_batch(attendance_records)
        
        # Generate PDF report
        pdf_filename = f"Asistencia_{attendance_data['curso']['codigo']}_{attendance_data['seccion']}_{fecha_hoy.strftime('%Y%m%d')}.pdf"
        pdf_path = Config.REPORTS_DIR / pdf_filename
        
        if PDFReportGenerator.generate_attendance_report(attendance_data, pdf_path):
            # Send email to professor
            catedratico_email = session.get('email')
            EmailSender.send_attendance_report(
                catedratico_email,
                f"{attendance_data['curso']['nombre']} - Sección {attendance_data['seccion']}",
                pdf_path,
                format_date(fecha_hoy)
            )
            
            flash(f'Asistencia confirmada exitosamente. Reporte enviado a {catedratico_email}', 'success')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_hoy.strftime('%Y-%m-%d')))
        else:
            flash('Asistencia confirmada pero hubo un error al generar el PDF', 'warning')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_hoy.strftime('%Y-%m-%d')))
        
    except Exception as e:
        logger.error(f"Error confirming attendance: {e}")
        flash(f'Error al confirmar asistencia: {str(e)}', 'danger')
        return redirect(url_for('ver_asistencia', assignment_id=assignment_id))


@app.route('/curso/<int:assignment_id>/reporte')
@login_required
@catedratico_required
def descargar_asistencia(assignment_id):
    """Download attendance report for an assignment without confirming"""
    try:
        # Get date from query string if present
        fecha_str = request.args.get('fecha')
        fecha_obj = None
        if fecha_str:
            try:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Get attendance data
        attendance_data = AttendanceTree.get_course_attendance(assignment_id, fecha_obj)
        
        if not attendance_data:
            flash('No se pudo cargar la información de asistencia', 'danger')
            return redirect(url_for('dashboard'))
            
        # Check permission
        if attendance_data['curso']['catedratico_id'] != session.get('user_id'):
            flash('No tiene permiso para descargar este reporte', 'danger')
            return redirect(url_for('dashboard'))
            
        fecha_hoy = fecha_obj if fecha_obj else date.today()
        
        # Generate PDF
        pdf_filename = f"Reporte_{attendance_data['curso']['codigo']}_{attendance_data['seccion']}_{fecha_hoy.strftime('%Y%m%d')}.pdf"
        pdf_path = Config.REPORTS_DIR / pdf_filename
        
        if PDFReportGenerator.generate_attendance_report(attendance_data, pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
        else:
            flash('Error al generar el PDF', 'danger')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id))
            
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        flash(f'Error al descargar reporte: {str(e)}', 'danger')
        return redirect(url_for('ver_asistencia', assignment_id=assignment_id))


@app.route('/registro_facial')
def registro_facial():
    """Page for facial registration"""
    tipos_persona = TipoPersonaDAO.get_all()
    secciones = SeccionDAO.get_all()
    carreras = CarreraDAO.get_all()
    return render_template('registro_facial.html', tipos_persona=tipos_persona, secciones=secciones, carreras=carreras)


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
        seccion_id = data.get('seccion_id')
        carrera_id = data.get('carrera_id')

        if not all([image_data, nombre, apellido, email, tipo_persona, codigo_carnet]):
            return {'success': False, 'message': 'Faltan datos requeridos'}, 400

        if not email.strip().lower().endswith('@miumg.edu.gt'):
            return {'success': False, 'message': 'El correo electrónico debe ser del dominio @miumg.edu.gt'}, 400

        # Decode base64 image (Photo)
        header, encoded = image_data.split(",", 1)
        binary_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(binary_data)).convert('RGB')
        image_np = np.array(image)
        
        # Decode base64 signature
        firma_data = data.get('firma')
        firma_path_str = None
        if firma_data:
            try:
                header_sig, encoded_sig = firma_data.split(",", 1)
                binary_sig = base64.b64decode(encoded_sig)
                firma_img = Image.open(io.BytesIO(binary_sig)).convert('RGBA')
                
                firma_filename = f"sig_{codigo_carnet}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                firma_path = Config.PHOTOS_DIR / firma_filename
                firma_img.save(firma_path)
                firma_path_str = str(firma_path)
            except Exception as e:
                logger.error(f"Error saving signature: {e}")

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

        # Save Photo to DB
        filename = f"{codigo_carnet}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        filepath = Config.PHOTOS_DIR / filename
        image.save(filepath)

        
        # Create Persona
        default_pass = 'admin'
        
        # Create person
        restriccion_ingreso = 1 if data.get('restriccion_ingreso') else 0
        persona_id = PersonaDAO.create(
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            email=email,
            tipo_persona_id=tipo_persona, 
            foto_path=str(filepath),
            firma_path=firma_path_str,
            encoding_facial=encoding,
            codigo_carnet=codigo_carnet,
            seccion_id=seccion_id,
            carrera_id=carrera_id,
            password_hash=default_pass,
            restriccion_ingreso=restriccion_ingreso
        )

        # Auto-Enrollment (Inscripcion Automatica)
        tipo_obj = TipoPersonaDAO.get_by_id(tipo_persona)
        if tipo_obj and tipo_obj['nombre'].lower() == 'estudiante' and persona_id:
            try:
                cursos = CursoDAO.get_all()
                count_inscripciones = 0
                for curso in cursos:
                    try:
                        AsignacionCursoDAO.create(persona_id, curso['id'])
                        count_inscripciones += 1
                    except Exception as e:
                        pass
                logger.info(f"Auto-enrolled student {codigo_carnet} in {count_inscripciones} courses.")
            except Exception as e:
                logger.error(f"Error in auto-enrollment: {e}")

        # Generate ID Card PDF
        try:
            pdf_filename = f"Carnet_{codigo_carnet}.pdf"
            pdf_path = Config.REPORTS_DIR / pdf_filename
            
            # Get role name / career name
            carrera_nombre = "Usuario UMG"
            if carrera_id:
                carrera_obj = CarreraDAO.get_by_id(carrera_id)
                if carrera_obj:
                    carrera_nombre = carrera_obj['nombre']
            elif tipo_obj:
                carrera_nombre = tipo_obj['nombre']

            # QR Content: Carnet
            qr_content = f"{codigo_carnet}"
            
            IDCardGenerator.generate(
                nombre=nombre,
                apellido=apellido,
                codigo_carnet=codigo_carnet, 
                carrera=carrera_nombre, 
                foto_path=str(filepath),
                firma_path=firma_path_str,
                output_path=str(pdf_path),
                qr_data=qr_content
            )
            
            # Send Email
            EmailSender.send_id_card(email, nombre, str(pdf_path))
            
        except Exception as pdf_err:
            logger.error(f"Error generating PDF/Email: {pdf_err}")
            # Non-blocking error

        return {'success': True, 'message': 'Usuario registrado exitosamente. Se ha enviado el carnet al correo.'}

    except Exception as e:
        logger.error(f"Error in registration: {e}")
        return {'success': False, 'message': str(e)}, 500


@app.route('/monitor')
@login_required
def monitor_global():
    """Global attendance monitor by building/floors/rooms"""
    try:
        # Debugging session roles
        logger.info(f"DEBUG - Session User: {session.get('email')}, Role: {session.get('role')}, Tipo: {session.get('tipo_persona')}")
        
        # Check permissions (Admin or Professor)
        user_role = str(session.get('role', '')).lower()
        user_tipo = str(session.get('tipo_persona', '')).lower()
        
        allowed_roles = ['admin', 'catedratico', 'catedrático', 'administrativo']
        
        if not any(r in user_role for r in allowed_roles) and not any(r in user_tipo for r in allowed_roles):
            flash('No tiene permiso para acceder al monitor global', 'danger')
            return redirect(url_for('dashboard'))
            
        # Get date from query string
        fecha_str = request.args.get('fecha')
        fecha_obj = None
        search_performed = False
        if fecha_str:
            try:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                search_performed = True
            except ValueError:
                pass
                
        # Get hierarchical tree
        campus_data = AttendanceTree.get_building_tree(fecha_obj)
        
        if campus_data:
            campus_data['search_performed'] = search_performed
            if not search_performed:
                # Clear data if search not performed yet
                campus_data['salones'] = []
                campus_data['accesos_generales'] = []
        
        return render_template('monitor.html', data=campus_data)
        
    except Exception as e:
        logger.error(f"Error in monitor global: {e}")
        flash('Error al cargar el monitor global', 'danger')
        return redirect(url_for('dashboard'))


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
