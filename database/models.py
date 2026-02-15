"""
Data Access Objects for UMG Biometric System
Provides CRUD operations for all database tables
"""
import json
from datetime import datetime, date, timedelta
from database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class CarreraDAO:
    """Data access for carreras table"""
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM carreras ORDER BY nombre")

    @staticmethod
    def get_by_id(carrera_id):
        """Get career by ID"""
        query = "SELECT * FROM carreras WHERE id = %s"
        results = DatabaseManager.execute_query(query, (carrera_id,))
        return results[0] if results else None

class SeccionDAO:
    """Data access for secciones table"""
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM secciones ORDER BY nombre")

class PersonaDAO:
    """Data access for personas table"""
    
    @staticmethod
    def create(nombre, apellido, dpi, telefono, email, tipo_persona, carrera_id, seccion_id, 
               foto_path, firma_path, encoding_facial, codigo_carnet, password_hash=None):
        """Create a new person record"""
        query = """
            INSERT INTO personas 
            (nombre, apellido, dpi, telefono, email, role, tipo_persona, carrera_id, seccion_id, 
             foto_path, firma_path, encoding_facial, codigo_carnet, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Convert encoding to JSON string
        encoding_json = json.dumps(encoding_facial.tolist()) if encoding_facial is not None else None
        
        # Sync role and tipo_persona
        role = tipo_persona 
        
        params = (nombre, apellido, dpi, telefono, email, role, tipo_persona, carrera_id, seccion_id,
                 foto_path, firma_path, encoding_json, codigo_carnet, password_hash)
        
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_by_id(persona_id):
        """Get person by ID"""
        query = "SELECT * FROM personas WHERE id = %s"
        results = DatabaseManager.execute_query(query, (persona_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_email(email):
        """Get person by email"""
        query = "SELECT * FROM personas WHERE email = %s"
        results = DatabaseManager.execute_query(query, (email,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_codigo_carnet(codigo):
        """Get person by carnet code"""
        query = "SELECT * FROM personas WHERE codigo_carnet = %s"
        results = DatabaseManager.execute_query(query, (codigo,))
        return results[0] if results else None
    
    @staticmethod
    def get_all_encodings():
        """Get all facial encodings for recognition"""
        query = """
            SELECT id, nombre, apellido, encoding_facial, restriccion_ingreso 
            FROM personas 
            WHERE encoding_facial IS NOT NULL
        """
        results = DatabaseManager.execute_query(query)
        
        # Convert JSON encodings back to lists
        for person in results:
            if person['encoding_facial']:
                person['encoding_facial'] = json.loads(person['encoding_facial'])
        
        return results
    
    @staticmethod
    def get_by_type(tipo_persona):
        """Get all persons of a specific type"""
        query = "SELECT * FROM personas WHERE role = %s ORDER BY apellido, nombre"
        return DatabaseManager.execute_query(query, (tipo_persona,))
    
    @staticmethod
    def update_password(persona_id, password_hash):
        """Update person's password"""
        query = "UPDATE personas SET password_hash = %s WHERE id = %s"
        return DatabaseManager.execute_query(query, (password_hash, persona_id), fetch=False)
    
    @staticmethod
    def get_all():
        """Get all persons"""
        query = "SELECT * FROM personas ORDER BY role, apellido, nombre"
        return DatabaseManager.execute_query(query)


class CursoDAO:
    """Data access for cursos table"""
    
    @staticmethod
    def create(nombre, codigo, horario, salon, catedratico_id):
        """Create a new course"""
        query = """
            INSERT INTO cursos (nombre, codigo, horario, salon, catedratico_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (nombre, codigo, horario, salon, catedratico_id)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_by_id(curso_id):
        """Get course by ID"""
        query = """
            SELECT c.*, p.nombre as catedratico_nombre, p.apellido as catedratico_apellido
            FROM cursos c
            LEFT JOIN personas p ON c.catedratico_id = p.id
            WHERE c.id = %s
        """
        results = DatabaseManager.execute_query(query, (curso_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_catedratico(catedratico_id):
        """Get all courses for a professor"""
        query = "SELECT * FROM cursos WHERE catedratico_id = %s ORDER BY nombre"
        return DatabaseManager.execute_query(query, (catedratico_id,))
    
    @staticmethod
    def get_all():
        """Get all courses"""
        query = """
            SELECT c.*, p.nombre as catedratico_nombre, p.apellido as catedratico_apellido
            FROM cursos c
            LEFT JOIN personas p ON c.catedratico_id = p.id
            ORDER BY c.nombre
        """
        return DatabaseManager.execute_query(query)


class InscripcionDAO:
    """Data access for inscripciones table"""
    
    @staticmethod
    def create(estudiante_id, curso_id):
        """Enroll a student in a course"""
        query = "INSERT INTO inscripciones (estudiante_id, curso_id) VALUES (%s, %s)"
        return DatabaseManager.execute_insert(query, (estudiante_id, curso_id))
    
    @staticmethod
    def get_estudiantes_by_curso(curso_id):
        """Get all students enrolled in a course"""
        query = """
            SELECT p.* 
            FROM personas p
            INNER JOIN inscripciones i ON p.id = i.estudiante_id
            WHERE i.curso_id = %s
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (curso_id,))
    
    @staticmethod
    def get_cursos_by_estudiante(estudiante_id):
        """Get all courses for a student"""
        query = """
            SELECT c.* 
            FROM cursos c
            INNER JOIN inscripciones i ON c.id = i.curso_id
            WHERE i.estudiante_id = %s
            ORDER BY c.nombre
        """
        return DatabaseManager.execute_query(query, (estudiante_id,))
    
    @staticmethod
    def delete(estudiante_id, curso_id):
        """Remove student from course"""
        query = "DELETE FROM inscripciones WHERE estudiante_id = %s AND curso_id = %s"
        return DatabaseManager.execute_query(query, (estudiante_id, curso_id), fetch=False)


class RegistroAccesoDAO:
    """Data access for registros_acceso table"""
    
    @staticmethod
    def create(persona_id, ubicacion, tipo_acceso, salon=None):
        """Create an access log entry"""
        query = """
            INSERT INTO registros_acceso (persona_id, ubicacion, tipo_acceso, salon)
            VALUES (%s, %s, %s, %s)
        """
        params = (persona_id, ubicacion, tipo_acceso, salon)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_recent_by_person(persona_id, minutes=5):
        """Check if person has accessed recently (for cooldown)"""
        query = """
            SELECT * FROM registros_acceso 
            WHERE persona_id = %s 
            AND fecha_hora >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
            ORDER BY fecha_hora DESC
            LIMIT 1
        """
        results = DatabaseManager.execute_query(query, (persona_id, minutes))
        return results[0] if results else None
    
    @staticmethod
    def get_by_date_and_location(fecha, ubicacion=None, tipo_acceso=None):
        """Get access logs for a specific date and location"""
        query = "SELECT * FROM registros_acceso WHERE DATE(fecha_hora) = %s"
        params = [fecha]
        
        if ubicacion:
            query += " AND ubicacion = %s"
            params.append(ubicacion)
        
        if tipo_acceso:
            query += " AND tipo_acceso = %s"
            params.append(tipo_acceso)
        
        query += " ORDER BY fecha_hora DESC"
        return DatabaseManager.execute_query(query, tuple(params))
    
    @staticmethod
    def get_by_salon_and_date(salon, fecha):
        """Get all access logs for a classroom on a specific date"""
        query = """
            SELECT ra.*, p.nombre, p.apellido, p.email, p.foto_path
            FROM registros_acceso ra
            INNER JOIN personas p ON ra.persona_id = p.id
            WHERE ra.salon = %s 
            AND DATE(ra.fecha_hora) = %s
            AND ra.tipo_acceso = 'salon'
            ORDER BY ra.fecha_hora
        """
        return DatabaseManager.execute_query(query, (salon, fecha))
    
    @staticmethod
    def get_today_by_salon(salon):
        """Get today's access logs for a classroom"""
        query = """
            SELECT ra.*, p.nombre, p.apellido, p.email, p.foto_path
            FROM registros_acceso ra
            INNER JOIN personas p ON ra.persona_id = p.id
            WHERE ra.salon = %s 
            AND DATE(ra.fecha_hora) = CURDATE()
            AND ra.tipo_acceso = 'salon'
            ORDER BY ra.fecha_hora
        """
        return DatabaseManager.execute_query(query, (salon,))


class AsistenciaDAO:
    """Data access for asistencias table"""
    
    @staticmethod
    def create(estudiante_id, curso_id, fecha, presente, confirmado_por=None):
        """Create an attendance record"""
        query = """
            INSERT INTO asistencias 
            (estudiante_id, curso_id, fecha, presente, confirmado_por, fecha_confirmacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        fecha_conf = datetime.now() if confirmado_por else None
        params = (estudiante_id, curso_id, fecha, presente, confirmado_por, fecha_conf)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def create_batch(attendance_records):
        """Create multiple attendance records at once"""
        query = """
            INSERT INTO asistencias 
            (estudiante_id, curso_id, fecha, presente, confirmado_por, fecha_confirmacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return DatabaseManager.execute_many(query, attendance_records)
    
    @staticmethod
    def get_by_curso_and_fecha(curso_id, fecha):
        """Get attendance for a course on a specific date"""
        query = """
            SELECT a.*, p.nombre, p.apellido, p.email, p.foto_path
            FROM asistencias a
            INNER JOIN personas p ON a.estudiante_id = p.id
            WHERE a.curso_id = %s AND a.fecha = %s
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (curso_id, fecha))
    
    @staticmethod
    def exists(estudiante_id, curso_id, fecha):
        """Check if attendance record exists"""
        query = """
            SELECT COUNT(*) as count 
            FROM asistencias 
            WHERE estudiante_id = %s AND curso_id = %s AND fecha = %s
        """
        result = DatabaseManager.execute_query(query, (estudiante_id, curso_id, fecha))
        return result[0]['count'] > 0 if result else False
    
    @staticmethod
    def get_by_estudiante(estudiante_id, curso_id=None):
        """Get attendance history for a student"""
        if curso_id:
            query = """
                SELECT * FROM asistencias 
                WHERE estudiante_id = %s AND curso_id = %s
                ORDER BY fecha DESC
            """
            params = (estudiante_id, curso_id)
        else:
            query = """
                SELECT a.*, c.nombre as curso_nombre
                FROM asistencias a
                INNER JOIN cursos c ON a.curso_id = c.id
                WHERE a.estudiante_id = %s
                ORDER BY a.fecha DESC
            """
            params = (estudiante_id,)
        
        return DatabaseManager.execute_query(query, params)
