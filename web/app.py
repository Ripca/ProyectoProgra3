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
from web.recognition_service import WebRecognitionService
from modules.registro.email_sender import EmailSender
from utils.helpers import format_date
from utils.image_validator import ImageValidator
import face_recognition
import numpy as np
import base64
import io
from PIL import Image
from PIL import Image
from database.models import PersonaDAO, TipoPersonaDAO, SalonDAO, SeccionDAO, CarreraDAO, ProgramacionAcademicaDAO, SesionClaseDAO, AsistenciaClaseDAO, AsignacionCursoDAO, CursoDAO, SedeDAO, JornadaDAO, PersonaCarnetDAO
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
recognition_service = WebRecognitionService()
FACE_QUALITY_BLUR_THRESHOLD = 12.0


def _user_can_manage_people():
    role = str(session.get('role', '')).lower()
    tipo = str(session.get('tipo_persona', '')).lower()
    allowed = ['admin', 'administrativo', 'catedratico', 'catedrático']
    return any(value in role for value in allowed) or any(value in tipo for value in allowed)


def _public_error_message(error):
    error_msg = str(error)
    if "1062" in error_msg or "Duplicate entry" in error_msg:
        if "codigo_carnet" in error_msg or "persona_carnets" in error_msg:
            return "El carnet ingresado ya está registrado. Revise el dato e intente con otro."
        if "email" in error_msg:
            return "El correo institucional ya está registrado."
        if "dpi" in error_msg:
            return "El DPI ingresado ya está registrado."
        return "Algunos datos ya existen en el sistema. Revise la información e intente de nuevo."
    return "No se pudo completar la operación. Revise los datos e intente nuevamente."

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
        
        return render_template('dashboard.html', cursos=cursos, today=date.today())
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error al cargar el dashboard', 'danger')
        return redirect(url_for('login'))


@app.route('/perfil_docente')
@login_required
def mi_perfil_docente():
    """Current teacher profile."""
    return redirect(url_for('perfil_docente', persona_id=session.get('user_id')))


@app.route('/perfil_docente/<int:persona_id>')
@login_required
def perfil_docente(persona_id):
    """Teacher profile with assigned academic schedule."""
    try:
        if persona_id != session.get('user_id') and not _user_can_manage_people():
            flash('No tiene permiso para ver este perfil docente', 'danger')
            return redirect(url_for('dashboard'))

        persona = PersonaDAO.get_by_id(persona_id)
        if not persona:
            flash('Docente no encontrado', 'danger')
            return redirect(url_for('dashboard'))

        tipo_persona = (persona.get('tipo_persona_nombre') or '').lower()
        if 'catedr' not in tipo_persona and not _user_can_manage_people():
            flash('Este perfil no corresponde a un docente', 'warning')
            return redirect(url_for('dashboard'))

        cursos = CursoDAO.get_by_catedratico(persona_id)
        sedes = sorted({curso.get('sede_nombre') for curso in cursos if curso.get('sede_nombre')})
        jornadas = sorted({curso.get('jornada_nombre') for curso in cursos if curso.get('jornada_nombre')})
        carreras = sorted({curso.get('carrera_nombre') for curso in cursos if curso.get('carrera_nombre')})

        return render_template(
            'perfil_docente.html',
            persona=persona,
            cursos=cursos,
            sedes=sedes,
            jornadas=jornadas,
            carreras=carreras
        )
    except Exception as e:
        logger.error(f"Error loading teacher profile: {e}")
        flash('Error al cargar el perfil docente', 'danger')
        return redirect(url_for('dashboard'))


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
        if attendance_data['curso']['catedratico_id'] != session.get('user_id') and not _user_can_manage_people():
            flash('No tiene permiso para ver esta clase', 'danger')
            return redirect(url_for('dashboard'))
        
        sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, fecha_obj) if search_performed else None
        attendance_confirmed = bool(sesion and sesion.get('estado') == 'FINALIZADA')
        return render_template('asistencia.html', data=attendance_data, attendance_confirmed=attendance_confirmed)
        
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
        if attendance_data['curso']['catedratico_id'] != session.get('user_id') and not _user_can_manage_people():
            flash('No tiene permiso para confirmar esta clase', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if already confirmed for this date
        fecha_hoy = fecha_obj if fecha_obj else date.today()
        estudiantes = attendance_data['estudiantes']
        existing_sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, fecha_hoy)
        if existing_sesion and existing_sesion.get('estado') == 'FINALIZADA':
            flash(f'La asistencia para el {fecha_hoy.strftime("%d/%m/%Y")} ya fue confirmada anteriormente', 'warning')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_hoy.strftime('%Y-%m-%d')))
        
        if estudiantes and AsistenciaClaseDAO.exists(estudiantes[0]['id'], assignment_id, fecha_hoy):
            flash(f'La asistencia para el {fecha_hoy.strftime("%d/%m/%Y")} ya fue confirmada anteriormente', 'warning')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_hoy.strftime('%Y-%m-%d')))
        
        # Check if session exists, create if not
        sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, fecha_hoy)
        if not sesion:
            hora_inicio = attendance_data['assignment']['hora_inicio']
            hora_fin = attendance_data['assignment']['hora_fin']
            sesion_id = SesionClaseDAO.create(assignment_id, fecha_hoy, hora_inicio, hora_fin, 'FINALIZADA')
        else:
            sesion_id = sesion['id']
            SesionClaseDAO.update_estado(sesion_id, 'FINALIZADA', 'Asistencia confirmada')
            
        # Create attendance records
        confirmado_por = session.get('user_id')
        
        attendance_records = []
        
        for estudiante in estudiantes:
            if not estudiante.get('presente'):
                continue
            attendance_records.append((
                sesion_id,
                estudiante['id'],
                estudiante.get('hora_acceso') or datetime.combine(fecha_hoy, datetime.now().time()),
                'MANUAL',
                confirmado_por,
                None
            ))
        
        # Batch insert
        if attendance_records:
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


@app.route('/curso/<int:assignment_id>/enviar-confirmada', methods=['POST'])
@login_required
@catedratico_required
def enviar_asistencia_confirmada(assignment_id):
    """Send the already confirmed attendance report by email."""
    try:
        fecha_str = request.form.get('fecha')
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        attendance_data = AttendanceTree.get_course_attendance(assignment_id, fecha_obj)

        if not attendance_data:
            flash('No se pudo cargar la asistencia confirmada', 'danger')
            return redirect(url_for('dashboard'))

        if attendance_data['curso']['catedratico_id'] != session.get('user_id') and not _user_can_manage_people():
            flash('No tiene permiso para enviar esta asistencia', 'danger')
            return redirect(url_for('dashboard'))

        sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, fecha_obj)
        if not sesion or sesion.get('estado') != 'FINALIZADA':
            flash('Primero debe confirmar la asistencia antes de enviarla.', 'warning')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_obj.strftime('%Y-%m-%d')))

        pdf_filename = f"Asistencia_Confirmada_{attendance_data['curso']['codigo']}_{attendance_data['seccion']}_{fecha_obj.strftime('%Y%m%d')}.pdf"
        pdf_path = Config.REPORTS_DIR / pdf_filename

        if not PDFReportGenerator.generate_attendance_report(attendance_data, pdf_path):
            flash('No se pudo generar el PDF confirmado.', 'danger')
            return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_obj.strftime('%Y-%m-%d')))

        EmailSender.send_attendance_report(
            session.get('email'),
            f"{attendance_data['curso']['nombre']} - Sección {attendance_data['seccion']}",
            pdf_path,
            format_date(fecha_obj)
        )

        flash(f'Asistencia confirmada enviada a {session.get("email")}', 'success')
        return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_obj.strftime('%Y-%m-%d')))

    except Exception as e:
        logger.error(f"Error sending confirmed attendance: {e}")
        flash(f'Error al enviar asistencia confirmada: {str(e)}', 'danger')
        return redirect(url_for('ver_asistencia', assignment_id=assignment_id))


@app.route('/curso/<int:assignment_id>/borrar-confirmacion', methods=['POST'])
@login_required
@catedratico_required
def borrar_confirmacion_asistencia(assignment_id):
    """Delete confirmed attendance records for a date so the flow can be tested again."""
    try:
        fecha_str = request.form.get('fecha')
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        attendance_data = AttendanceTree.get_course_attendance(assignment_id, fecha_obj)

        if not attendance_data:
            flash('No se pudo cargar la clase', 'danger')
            return redirect(url_for('dashboard'))

        if attendance_data['curso']['catedratico_id'] != session.get('user_id') and not _user_can_manage_people():
            flash('No tiene permiso para borrar esta confirmación', 'danger')
            return redirect(url_for('dashboard'))

        deleted = AsistenciaClaseDAO.delete_by_curso_and_fecha(assignment_id, fecha_obj)
        flash(f'Confirmación eliminada. Registros removidos: {deleted}', 'success')
        return redirect(url_for('ver_asistencia', assignment_id=assignment_id, fecha=fecha_obj.strftime('%Y-%m-%d')))

    except Exception as e:
        logger.error(f"Error deleting confirmed attendance: {e}")
        flash(f'Error al borrar confirmación: {str(e)}', 'danger')
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
        if attendance_data['curso']['catedratico_id'] != session.get('user_id') and not _user_can_manage_people():
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
    return render_template('registro_facial.html', tipos_persona=tipos_persona)


@app.route('/api/validar_rostro_vivo', methods=['POST'])
def validar_rostro_vivo():
    """API to provide live feedback on face quality"""
    try:
        data = request.json
        image_data = data.get('image')
        if not image_data:
            return {'success': False, 'message': 'No se recibió imagen.'}, 200

        if "," in image_data:
            _, encoded = image_data.split(",", 1)
        else:
            encoded = image_data
            
        binary_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(binary_data)).convert('RGB')
        image_np = np.array(image)

        face_locations = face_recognition.face_locations(image_np)
        if not face_locations:
            return {'success': False, 'message': 'No se detectó ningún rostro.'}, 200
        
        if len(face_locations) > 1:
            return {'success': False, 'message': 'Se detectó más de un rostro.'}, 200

        is_valid, validation_msg = ImageValidator.validate_quality(
            image_np,
            face_locations,
            blur_threshold=FACE_QUALITY_BLUR_THRESHOLD
        )
        return {'success': is_valid, 'message': validation_msg}, 200

    except Exception as e:
        logger.error(f"Error en validación en vivo: {e}")
        return {'success': False, 'message': 'Error procesando la imagen.'}, 200


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
        import re as _re
        codigo_carnet = (data.get('codigo_carnet') or '').strip()
        # Remove any characters that are unsafe in file paths or db identifiers
        codigo_carnet = _re.sub(r'[^\w\-.]', '_', codigo_carnet).strip('_')
        tipo_obj = TipoPersonaDAO.get_by_id(tipo_persona)
        tipo_nombre = (tipo_obj['nombre'] if tipo_obj else '').lower()
        es_estudiante = 'estudiante' in tipo_nombre
        es_catedratico = 'catedr' in tipo_nombre

        if not all([image_data, nombre, apellido, email, tipo_persona]):
            return {'success': False, 'message': 'Faltan datos requeridos'}, 400

        if not codigo_carnet:
            return {'success': False, 'message': 'El código de carnet o identificación es requerido.'}, 400

        if not email.strip().lower().endswith('@miumg.edu.gt'):
            return {'success': False, 'message': 'El correo electrónico debe ser del dominio @miumg.edu.gt'}, 400

        # Pre-validaciones
        from database.db_manager import DatabaseManager
        # Validar correo
        if PersonaDAO.get_by_email(email.strip()):
            return {'success': False, 'message': 'El correo institucional ya está registrado.'}, 400
            
        # Validar carnet
        if codigo_carnet:
            existing_carnet = DatabaseManager.execute_query(
                "SELECT 1 FROM persona_carnets WHERE codigo_carnet = %s", (codigo_carnet,)
            )
            if existing_carnet:
                return {'success': False, 'message': 'El carnet ingresado ya está registrado.'}, 400

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
                
                file_key = codigo_carnet or f"docente_{uuid.uuid4().hex[:8]}"
                firma_filename = f"sig_{file_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                firma_path = Config.PHOTOS_DIR / firma_filename
                firma_img.save(firma_path)
                firma_path_str = str(firma_path)
            except Exception as e:
                logger.error(f"Error saving signature: {e}")

        # Detect face and validate quality
        face_locations = face_recognition.face_locations(image_np)
        is_valid, validation_msg = ImageValidator.validate_quality(
            image_np,
            face_locations,
            blur_threshold=FACE_QUALITY_BLUR_THRESHOLD
        )
        
        if not is_valid:
            return {'success': False, 'message': validation_msg}, 400

        # Encode face
        face_encodings = face_recognition.face_encodings(image_np, face_locations)
        if not face_encodings:
             return {'success': False, 'message': 'No se pudo codificar el rostro'}, 400
            
        encoding = face_encodings[0]

        import re as _re2
        safe_carnet = _re2.sub(r'[^\w\-]', '_', codigo_carnet).strip('_') if codigo_carnet else f"usr_{uuid.uuid4().hex[:8]}"
        if not safe_carnet:
            safe_carnet = f"usr_{uuid.uuid4().hex[:8]}"
        filename = f"{safe_carnet}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
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
            codigo_carnet=codigo_carnet or None,
            password_hash=default_pass,
            restriccion_ingreso=restriccion_ingreso
        )

        # Auto-Enrollment removido para flujo en dos pasos
        # Redirigir al módulo de Asignación Académica en el Paso 2
        # Generate ID Card PDF
        try:
            if codigo_carnet:
                pdf_filename = f"Carnet_{codigo_carnet}.pdf"
                pdf_path = Config.REPORTS_DIR / pdf_filename
                
                # Get role name / career name
                carrera_nombre = "Usuario UMG"
                if tipo_obj:
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

        message = 'Usuario registrado exitosamente.'
        if codigo_carnet:
            message = 'Usuario registrado exitosamente. Se ha enviado el carnet al correo.'
        return {'success': True, 'message': message, 'persona_id': persona_id, 'tipo_persona_nombre': tipo_obj['nombre'] if tipo_obj else 'Usuario'}

    except Exception as e:
        logger.error(f"Error procesando registro facial: {e}")
        status_code = 400 if ("1062" in str(e) or "Duplicate entry" in str(e)) else 500
        return {'success': False, 'message': _public_error_message(e), 'raw_error': str(e)}, status_code


@app.route('/asignaciones')
@login_required
def asignaciones():
    """List people so academic assignments can be completed later."""
    if not _user_can_manage_people():
        flash('No tiene permiso para administrar asignaciones', 'danger')
        return redirect(url_for('dashboard'))

    personas = PersonaDAO.get_assignable()
    return render_template('asignaciones.html', personas=personas)


@app.route('/asignacion_academica/<int:persona_id>')
def asignacion_academica(persona_id):
    """Paso 2: Academic Assignment (Enrollment/Schedule)"""
    try:
        if session.get('user_id') and persona_id != session.get('user_id') and not _user_can_manage_people():
            flash('No tiene permiso para administrar esta asignación', 'danger')
            return redirect(url_for('dashboard'))

        persona = PersonaDAO.get_by_id(persona_id)
        if not persona:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('registro_facial'))
        
        # Catalogs for filters
        sedes = SedeDAO.get_all()
        jornadas = JornadaDAO.get_all()
        carreras = CarreraDAO.get_all()
        secciones = SeccionDAO.get_all()
        cursos = CursoDAO.get_all()
        salones = SalonDAO.get_all()
        
        # Load available courses from ProgramacionAcademica
        programaciones = ProgramacionAcademicaDAO.get_all()
        inscripciones = AsignacionCursoDAO.get_cursos_by_persona(persona_id)
        cursos_catedratico = CursoDAO.get_by_catedratico(persona_id)
        programaciones_docente = ProgramacionAcademicaDAO.get_disponibles_para_catedratico(persona_id)
        carnets_by_sede = {
            carnet['sede_id']: carnet['codigo_carnet']
            for carnet in PersonaCarnetDAO.get_by_persona(persona_id)
        }
        
        return render_template('asignacion_academica.html', 
                             persona=persona, 
                             sedes=sedes, 
                             jornadas=jornadas, 
                             carreras=carreras,
                             secciones=secciones,
                             cursos=cursos,
                             salones=salones,
                             today=date.today(),
                             programaciones=programaciones,
                             inscripciones=inscripciones,
                             cursos_catedratico=cursos_catedratico,
                             programaciones_docente=programaciones_docente,
                             carnets_by_sede=carnets_by_sede)
    except Exception as e:
        logger.error(f"Error loading asignacion_academica: {e}")
        flash('Error al cargar la asignación', 'danger')
        return redirect(url_for('registro_facial'))

@app.route('/api/inscribir_cursos', methods=['POST'])
def inscribir_cursos():
    """API to handle course enrollment (Paso 2)"""
    try:
        from database.db_manager import DatabaseManager
        data = request.json or {}
        persona_id = data.get('persona_id')
        programaciones_ids = data.get('programaciones', [])
        carnets_sede = data.get('carnets_sede') or {}
        
        if not persona_id:
            return {'success': False, 'message': 'ID de persona no proporcionado'}, 400

        persona_id = int(persona_id)
        if session.get('user_id') and persona_id != session.get('user_id') and not _user_can_manage_people():
            return {'success': False, 'message': 'No tiene permiso para administrar esta asignación.'}, 403

        persona = PersonaDAO.get_by_id(persona_id)
        tipo_persona = (persona.get('tipo_persona_nombre') or '').lower() if persona else ''
        if 'estudiante' not in tipo_persona:
            return {'success': False, 'message': 'La inscripción de cursos aplica únicamente para estudiantes. Para catedráticos se administra la programación académica.'}, 400

        if not programaciones_ids:
            return {'success': False, 'message': 'Debe seleccionar al menos un curso.'}, 400

        placeholders = ','.join(['%s'] * len(programaciones_ids))
        selected_programaciones = DatabaseManager.execute_query(
            f"""
            SELECT id, sede_id, carrera_id, seccion_id
            FROM programacion_academica
            WHERE id IN ({placeholders})
            """,
            tuple(programaciones_ids)
        )

        for prog in selected_programaciones:
            sede_id = prog['sede_id']
            carnet = str(carnets_sede.get(str(sede_id)) or carnets_sede.get(sede_id) or '').strip()
            if carnet:
                PersonaCarnetDAO.upsert(persona_id, sede_id, carnet)
            elif not PersonaCarnetDAO.has_for_sede(persona_id, sede_id):
                return {'success': False, 'message': 'Debe registrar un carnet para cada sede seleccionada antes de inscribir cursos.'}, 400

        count = 0
        for prog in selected_programaciones:
            try:
                DatabaseManager.execute_insert("INSERT IGNORE INTO persona_carreras (persona_id, carrera_id) VALUES (%s, %s)", (persona_id, prog['carrera_id']))
                DatabaseManager.execute_insert("INSERT IGNORE INTO persona_secciones (persona_id, seccion_id) VALUES (%s, %s)", (persona_id, prog['seccion_id']))
                AsignacionCursoDAO.create(persona_id, prog['id'])
                count += 1
            except Exception as e:
                logger.error(f"Error enrolling in prog {prog['id']}: {e}")
                
        return {'success': True, 'message': f'Inscrito en {count} cursos exitosamente.'}
        
    except Exception as e:
        logger.error(f"Error inscribiendo cursos: {e}")
        return {'success': False, 'message': _public_error_message(e)}, 500


@app.route('/api/asignar_cursos_catedratico', methods=['POST'])
@login_required
def asignar_cursos_catedratico():
    """Assign an existing academic schedule to a professor if the period is free."""
    if not _user_can_manage_people():
        return {'success': False, 'message': 'No tiene permiso para administrar programaciones.'}, 403

    try:
        data = request.json or {}
        if not data.get('persona_id') or not data.get('programacion_id'):
            return {'success': False, 'message': 'Seleccione una programación para asignar.'}, 400

        persona_id = int(data.get('persona_id'))
        programacion_id = int(data.get('programacion_id'))
        persona = PersonaDAO.get_by_id(persona_id)
        tipo_persona = (persona.get('tipo_persona_nombre') or '').lower() if persona else ''
        if not persona or 'catedr' not in tipo_persona:
            return {'success': False, 'message': 'La persona seleccionada no es catedrático.'}, 400

        success, message = ProgramacionAcademicaDAO.asignar_existente_a_catedratico(programacion_id, persona_id)
        status = 200 if success else 400
        return {'success': success, 'message': message}, status

    except Exception as e:
        logger.error(f"Error asignando curso a catedrático: {e}")
        return {'success': False, 'message': _public_error_message(e)}, 500


@app.route('/mi_asignacion')
@login_required
def mi_asignacion():
    """Persistent menu: view/manage my academic assignments"""
    user_id = session.get('user_id')
    return redirect(url_for('asignacion_academica', persona_id=user_id))


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
            
        sedes = SedeDAO.get_all()
        sede_id = request.args.get('sede_id')
        sede_id_int = int(sede_id) if sede_id else None

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
        campus_data = AttendanceTree.get_building_tree(fecha_obj, sede_id=sede_id_int)
        
        if campus_data:
            campus_data['search_performed'] = search_performed
            campus_data['sedes'] = sedes
            campus_data['selected_sede_id'] = sede_id_int
            selected_sede = next((s for s in sedes if s.get('id') == sede_id_int), None)
            campus_data['sede_nombre'] = selected_sede['nombre'] if selected_sede else None
            if not search_performed:
                # Clear data if search not performed yet
                campus_data['salones'] = []
                campus_data['accesos_generales'] = []
        
        return render_template('monitor.html', data=campus_data)
        
    except Exception as e:
        logger.error(f"Error in monitor global: {e}")
        flash('Error al cargar el monitor global', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/reconocimiento')
@login_required
def reconocimiento():
    """Web facial recognition console."""
    if not _user_can_manage_people():
        flash('No tiene permiso para usar el reconocimiento facial', 'danger')
        return redirect(url_for('dashboard'))

    cursos = CursoDAO.get_all_assignments()
    sedes = SedeDAO.get_all()
    jornadas = JornadaDAO.get_all()
    secciones = SeccionDAO.get_all()
    cursos_catalogo = CursoDAO.get_all()
    return render_template(
        'reconocimiento.html',
        cursos=cursos,
        sedes=sedes,
        jornadas=jornadas,
        secciones=secciones,
        cursos_catalogo=cursos_catalogo
    )


@app.route('/api/reconocimiento/recargar', methods=['POST'])
@login_required
def recargar_rostros():
    if not _user_can_manage_people():
        return {'success': False, 'message': 'No tiene permiso para esta acción.'}, 403

    try:
        total = recognition_service.load_known_faces()
        return {'success': True, 'message': f'Se recargaron {total} rostros registrados.', 'total': total}
    except Exception as e:
        logger.error(f"Error recargando rostros: {e}")
        return {'success': False, 'message': 'No se pudieron recargar los rostros.'}, 500


@app.route('/api/reconocimiento/procesar', methods=['POST'])
@login_required
def procesar_reconocimiento():
    if not _user_can_manage_people():
        return {'success': False, 'message': 'No tiene permiso para esta acción.'}, 403

    try:
        data = request.json or {}
        image_data = data.get('image')
        mode = data.get('mode', 'general')
        assignment_id = data.get('assignment_id')
        sede_id = data.get('sede_id')

        if not image_data:
            return {'success': False, 'message': 'No se recibió imagen para procesar.'}, 400

        if mode == 'clase' and not assignment_id:
            return {'success': False, 'message': 'Seleccione una clase para registrar asistencia.'}, 400
        if mode == 'general' and not sede_id:
            return {'success': False, 'message': 'Seleccione la sede donde se registrará la entrada.'}, 400

        assignment_id = int(assignment_id) if assignment_id else None
        sede_id = int(sede_id) if sede_id else None
        result = recognition_service.recognize_image(image_data, mode=mode, assignment_id=assignment_id, sede_id=sede_id)
        return result
    except Exception as e:
        logger.error(f"Error procesando reconocimiento web: {e}")
        return {'success': False, 'message': 'No se pudo procesar el reconocimiento.'}, 500


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
