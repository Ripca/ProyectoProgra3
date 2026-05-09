"""
Data Access Objects for UMG Biometric System
Provides CRUD operations for all database tables
"""
import json
from datetime import datetime, date, timedelta
from database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class TipoPersonaDAO:
    """Data access for tipos_persona table"""
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM tipos_persona ORDER BY nombre")

    @staticmethod
    def get_by_id(tipo_id):
        query = "SELECT * FROM tipos_persona WHERE id = %s"
        results = DatabaseManager.execute_query(query, (tipo_id,))
        return results[0] if results else None


class SeccionDAO:
    """Data access for secciones table"""
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM secciones ORDER BY nombre")

    @staticmethod
    def get_by_id(seccion_id):
        query = "SELECT * FROM secciones WHERE id = %s"
        results = DatabaseManager.execute_query(query, (seccion_id,))
        return results[0] if results else None


class CarreraDAO:
    """Data access for carreras table"""
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM carreras ORDER BY nombre")

    @staticmethod
    def get_by_id(carrera_id):
        query = "SELECT * FROM carreras WHERE id = %s"
        results = DatabaseManager.execute_query(query, (carrera_id,))
        return results[0] if results else None


class SalonDAO:
    """Data access for salones table"""
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM salones WHERE activo = 1 ORDER BY codigo")

    @staticmethod
    def get_by_id(salon_id):
        query = "SELECT * FROM salones WHERE id = %s"
        results = DatabaseManager.execute_query(query, (salon_id,))
        return results[0] if results else None


class PersonaDAO:
    """Data access for personas table"""
    
    @staticmethod
    def create(nombre, apellido, telefono, email, tipo_persona_id, 
               foto_path, firma_path, encoding_facial, codigo_carnet, seccion_id=None, carrera_id=None, password_hash=None, restriccion_ingreso=0):
        """Create a new person record"""
        query = """
            INSERT INTO personas 
            (nombre, apellido, telefono, email, tipo_persona_id, 
             foto_path, firma_path, encoding_facial, codigo_carnet, seccion_id, carrera_id, password_hash, restriccion_ingreso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Convert encoding to JSON string
        encoding_json = json.dumps(encoding_facial.tolist()) if encoding_facial is not None else None
        
        params = (nombre, apellido, telefono, email, tipo_persona_id,
                 foto_path, firma_path, encoding_json, codigo_carnet, seccion_id, carrera_id, password_hash, restriccion_ingreso)
        
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_by_id(persona_id):
        """Get person by ID"""
        query = "SELECT p.*, t.nombre as tipo_persona_nombre FROM personas p LEFT JOIN tipos_persona t ON p.tipo_persona_id = t.id WHERE p.id = %s"
        results = DatabaseManager.execute_query(query, (persona_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_email(email):
        """Get person by email"""
        query = "SELECT p.*, t.nombre as tipo_persona_nombre FROM personas p LEFT JOIN tipos_persona t ON p.tipo_persona_id = t.id WHERE p.email = %s"
        results = DatabaseManager.execute_query(query, (email,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_codigo_carnet(codigo):
        """Get person by carnet code"""
        query = "SELECT p.*, t.nombre as tipo_persona_nombre FROM personas p LEFT JOIN tipos_persona t ON p.tipo_persona_id = t.id WHERE p.codigo_carnet = %s"
        results = DatabaseManager.execute_query(query, (codigo,))
        return results[0] if results else None
    
    @staticmethod
    def get_all_encodings():
        """Get all facial encodings for recognition"""
        query = """
            SELECT id, nombre, apellido, encoding_facial, restriccion_ingreso 
            FROM personas 
            WHERE encoding_facial IS NOT NULL AND activo = 1
        """
        results = DatabaseManager.execute_query(query)
        
        # Convert JSON encodings back to lists
        for person in results:
            if person['encoding_facial']:
                person['encoding_facial'] = json.loads(person['encoding_facial'])
        
        return results
    
    @staticmethod
    def get_by_type(tipo_persona_id):
        """Get all persons of a specific type"""
        query = "SELECT p.*, t.nombre as tipo_persona_nombre FROM personas p LEFT JOIN tipos_persona t ON p.tipo_persona_id = t.id WHERE p.tipo_persona_id = %s ORDER BY p.apellido, p.nombre"
        return DatabaseManager.execute_query(query, (tipo_persona_id,))
    
    @staticmethod
    def update_password(persona_id, password_hash):
        """Update person's password"""
        query = "UPDATE personas SET password_hash = %s WHERE id = %s"
        return DatabaseManager.execute_query(query, (password_hash, persona_id), fetch=False)
    
    @staticmethod
    def get_all():
        """Get all persons"""
        query = "SELECT p.*, t.nombre as tipo_persona_nombre FROM personas p LEFT JOIN tipos_persona t ON p.tipo_persona_id = t.id ORDER BY t.nombre, p.apellido, p.nombre"
        return DatabaseManager.execute_query(query)


class CursoDAO:
    """Data access for cursos table"""
    
    @staticmethod
    def create(nombre, codigo, descripcion=None):
        """Create a new course"""
        query = """
            INSERT INTO cursos (nombre, codigo, descripcion)
            VALUES (%s, %s, %s)
        """
        params = (nombre, codigo, descripcion)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_by_id(curso_id):
        """Get basic course info by ID"""
        query = "SELECT * FROM cursos WHERE id = %s"
        results = DatabaseManager.execute_query(query, (curso_id,))
        return results[0] if results else None

    @staticmethod
    def get_assignment_by_id(assignment_id):
        """Get complete assignment info (course + schedule + room)"""
        query = """
            SELECT a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   p.nombre as catedratico_nombre, p.apellido as catedratico_apellido
            FROM asignaciones_catedratico a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN personas p ON a.catedratico_id = p.id
            WHERE a.id = %s
        """
        results = DatabaseManager.execute_query(query, (assignment_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_catedratico(catedratico_id):
        """Get all assigned classes for a professor"""
        query = """
            SELECT a.id as assignment_id, a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   CONCAT(a.dia_semana, ' ', DATE_FORMAT(a.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(a.hora_fin, '%H:%i')) as horario_full
            FROM asignaciones_catedratico a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            WHERE a.catedratico_id = %s
            ORDER BY FIELD(a.dia_semana, 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'), a.hora_inicio
        """
        return DatabaseManager.execute_query(query, (catedratico_id,))
    
    @staticmethod
    def get_all():
        """Get all materias in catalog"""
        query = "SELECT * FROM cursos ORDER BY nombre"
        return DatabaseManager.execute_query(query)

    @staticmethod
    def get_all_assignments():
        """Get all assigned classes with details"""
        query = """
            SELECT a.id as assignment_id, a.curso_id, a.seccion_id, a.catedratico_id, a.salon_id,
                   a.dia_semana, a.hora_inicio, a.hora_fin, c.nombre, c.codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   p.nombre as catedratico_nombre, p.apellido as catedratico_apellido,
                   CONCAT(a.dia_semana, ' ', DATE_FORMAT(a.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(a.hora_fin, '%H:%i')) as horario_full
            FROM asignaciones_catedratico a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN personas p ON a.catedratico_id = p.id
            ORDER BY c.nombre, s.nombre
        """
        return DatabaseManager.execute_query(query)


class AsignacionCursoDAO:
    """Data access for asignaciones_curso table"""
    
    @staticmethod
    def create(persona_id, curso_id):
        """Enroll a person in a course"""
        query = "INSERT INTO asignaciones_curso (persona_id, curso_id) VALUES (%s, %s)"
        return DatabaseManager.execute_insert(query, (persona_id, curso_id))
    
    @staticmethod
    def get_personas_by_curso(curso_id):
        """Get all persons enrolled in a course"""
        query = """
            SELECT p.*, t.nombre as tipo_persona_nombre 
            FROM personas p
            INNER JOIN asignaciones_curso a ON p.id = a.persona_id
            LEFT JOIN tipos_persona t ON p.tipo_persona_id = t.id
            WHERE a.curso_id = %s AND a.estado = 'ACTIVO'
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (curso_id,))
    
    @staticmethod
    def get_cursos_by_persona(persona_id):
        """Get all courses for a person"""
        query = """
            SELECT c.* 
            FROM cursos c
            INNER JOIN asignaciones_curso a ON c.id = a.curso_id
            WHERE a.persona_id = %s AND a.estado = 'ACTIVO'
            ORDER BY c.nombre
        """
        return DatabaseManager.execute_query(query, (persona_id,))
    
    @staticmethod
    def update_estado(persona_id, curso_id, estado):
        """Change state of assignment"""
        query = "UPDATE asignaciones_curso SET estado = %s WHERE persona_id = %s AND curso_id = %s"
        return DatabaseManager.execute_query(query, (estado, persona_id, curso_id), fetch=False)


class RegistroAccesoDAO:
    """Data access for registros_acceso table"""
    
    @staticmethod
    def create(persona_id, punto_acceso, metodo, observacion=None):
        """Create an access log entry"""
        query = """
            INSERT INTO registros_acceso (persona_id, punto_acceso, metodo, observacion)
            VALUES (%s, %s, %s, %s)
        """
        params = (persona_id, punto_acceso, metodo, observacion)
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
    def get_by_date(fecha, punto_acceso=None):
        """Get access logs for a specific date and location"""
        query = "SELECT * FROM registros_acceso WHERE DATE(fecha_hora) = %s"
        params = [fecha]
        
        if punto_acceso:
            query += " AND punto_acceso = %s"
            params.append(punto_acceso)
        
        query += " ORDER BY fecha_hora DESC"
        return DatabaseManager.execute_query(query, tuple(params))


class AsistenciaClaseDAO:
    """Data access for asistencias_clase table"""
    
    @staticmethod
    def create(persona_id, curso_id, salon_id, metodo, confirmado_por=None, observacion=None):
        """Create an attendance record"""
        query = """
            INSERT INTO asistencias_clase 
            (persona_id, curso_id, salon_id, metodo, confirmado_por, observacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (persona_id, curso_id, salon_id, metodo, confirmado_por, observacion)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def create_batch(attendance_records):
        """Create multiple attendance records at once
        Records should be tuples of (persona_id, curso_id, salon_id, fecha_hora, metodo, confirmado_por, observacion)
        """
        query = """
            INSERT INTO asistencias_clase 
            (persona_id, curso_id, salon_id, fecha_hora, metodo, confirmado_por, observacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return DatabaseManager.execute_many(query, attendance_records)
    
    @staticmethod
    def get_by_curso_and_fecha(curso_id, fecha):
        """Get attendance for a course on a specific date"""
        query = """
            SELECT a.*, p.nombre, p.apellido, p.email, p.foto_path
            FROM asistencias_clase a
            INNER JOIN personas p ON a.persona_id = p.id
            WHERE a.curso_id = %s AND DATE(a.fecha_hora) = %s
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (curso_id, fecha))
    
    @staticmethod
    def get_all_by_date(fecha):
        """Get all class attendance for a specific date across all courses/rooms"""
        query = """
            SELECT a.*, p.nombre, p.apellido, p.email
            FROM asistencias_clase a
            INNER JOIN personas p ON a.persona_id = p.id
            WHERE DATE(a.fecha_hora) = %s
            ORDER BY a.fecha_hora DESC
        """
        return DatabaseManager.execute_query(query, (fecha,))
    
    @staticmethod
    def exists(persona_id, curso_id, fecha):
        """Check if attendance record exists"""
        query = """
            SELECT COUNT(*) as count 
            FROM asistencias_clase 
            WHERE persona_id = %s AND curso_id = %s AND DATE(fecha_hora) = %s
        """
        result = DatabaseManager.execute_query(query, (persona_id, curso_id, fecha))
        return result[0]['count'] > 0 if result else False
    
    @staticmethod
    def get_by_persona(persona_id, curso_id=None):
        """Get attendance history for a person"""
        if curso_id:
            query = """
                SELECT * FROM asistencias_clase 
                WHERE persona_id = %s AND curso_id = %s
                ORDER BY fecha_hora DESC
            """
            params = (persona_id, curso_id)
        else:
            query = """
                SELECT a.*, c.nombre as curso_nombre
                FROM asistencias_clase a
                INNER JOIN cursos c ON a.curso_id = c.id
                WHERE a.persona_id = %s
                ORDER BY a.fecha_hora DESC
            """
            params = (persona_id,)
        
        return DatabaseManager.execute_query(query, params)
