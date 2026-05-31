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
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM tipos_persona ORDER BY nombre")

    @staticmethod
    def get_by_id(tipo_id):
        query = "SELECT * FROM tipos_persona WHERE id = %s"
        results = DatabaseManager.execute_query(query, (tipo_id,))
        return results[0] if results else None

class SeccionDAO:
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM secciones ORDER BY nombre")

    @staticmethod
    def get_by_id(seccion_id):
        query = "SELECT * FROM secciones WHERE id = %s"
        results = DatabaseManager.execute_query(query, (seccion_id,))
        return results[0] if results else None

class CarreraDAO:
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM carreras ORDER BY nombre")

    @staticmethod
    def get_by_id(carrera_id):
        query = "SELECT * FROM carreras WHERE id = %s"
        results = DatabaseManager.execute_query(query, (carrera_id,))
        return results[0] if results else None

class SalonDAO:
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM salones WHERE activo = 1 ORDER BY codigo")

    @staticmethod
    def get_by_id(salon_id):
        query = "SELECT * FROM salones WHERE id = %s"
        results = DatabaseManager.execute_query(query, (salon_id,))
        return results[0] if results else None

class SedeDAO:
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM sedes WHERE activo = 1 ORDER BY nombre")

    @staticmethod
    def get_default_id():
        rows = DatabaseManager.execute_query("SELECT id FROM sedes WHERE codigo = 'CENTRAL' LIMIT 1")
        if rows:
            return rows[0]['id']
        rows = DatabaseManager.execute_query("SELECT id FROM sedes WHERE activo = 1 ORDER BY id LIMIT 1")
        return rows[0]['id'] if rows else None

class JornadaDAO:
    @staticmethod
    def get_all():
        return DatabaseManager.execute_query("SELECT * FROM jornadas WHERE activo = 1 ORDER BY nombre")

class ProgramacionAcademicaDAO:
    @staticmethod
    def get_all():
        query = """
            SELECT a.id as assignment_id, a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   c.nombre as nombre, c.codigo as codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   p.nombre as catedratico_nombre, p.apellido as catedratico_apellido,
                   sd.nombre as sede_nombre, j.nombre as jornada_nombre, cr.nombre as carrera_nombre,
                   CONCAT(a.dia_semana, ' ', DATE_FORMAT(a.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(a.hora_fin, '%H:%i')) as horario_full
            FROM programacion_academica a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN personas p ON a.catedratico_id = p.id
            JOIN sedes sd ON a.sede_id = sd.id
            JOIN jornadas j ON a.jornada_id = j.id
            JOIN carreras cr ON a.carrera_id = cr.id
            WHERE a.activo = 1
            ORDER BY c.nombre, s.nombre
        """
        return DatabaseManager.execute_query(query)

    @staticmethod
    def get_by_id(programacion_id):
        query = "SELECT * FROM programacion_academica WHERE id = %s"
        results = DatabaseManager.execute_query(query, (programacion_id,))
        return results[0] if results else None

    @staticmethod
    def assign_to_catedratico(catedratico_id, curso_id, seccion_id, carrera_id, sede_id,
                              jornada_id, salon_id, dia_semana, hora_inicio, hora_fin,
                              ciclo='1S', anio=None):
        anio = anio or datetime.now().year
        conflict_query = """
            SELECT COUNT(*) as total
            FROM programacion_academica
            WHERE activo = 1
              AND salon_id = %s
              AND dia_semana = %s
              AND hora_inicio = %s
              AND COALESCE(ciclo, '') = COALESCE(%s, '')
              AND COALESCE(anio, 0) = COALESCE(%s, 0)
        """
        conflict = DatabaseManager.execute_query(
            conflict_query,
            (salon_id, dia_semana, hora_inicio, ciclo, anio)
        )
        if conflict and conflict[0]['total'] > 0:
            raise ValueError("El salon ya tiene una clase programada en ese horario.")

        query = """
            INSERT INTO programacion_academica
                (curso_id, seccion_id, carrera_id, sede_id, jornada_id, salon_id,
                 catedratico_id, dia_semana, hora_inicio, hora_fin, ciclo, anio, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
        return DatabaseManager.execute_insert(
            query,
            (
                curso_id, seccion_id, carrera_id, sede_id, jornada_id,
                salon_id, catedratico_id, dia_semana, hora_inicio, hora_fin,
                ciclo, anio
            )
        )

    @staticmethod
    def get_disponibles_para_catedratico(catedratico_id):
        query = """
            SELECT a.id as assignment_id, a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   c.nombre as nombre, c.codigo as codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   p.nombre as catedratico_nombre, p.apellido as catedratico_apellido,
                   sd.nombre as sede_nombre, j.nombre as jornada_nombre, cr.nombre as carrera_nombre,
                   CONCAT(a.dia_semana, ' ', DATE_FORMAT(a.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(a.hora_fin, '%H:%i')) as horario_full,
                   CASE WHEN conflicto.id IS NULL THEN 0 ELSE 1 END as tiene_conflicto
            FROM programacion_academica a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN personas p ON a.catedratico_id = p.id
            JOIN sedes sd ON a.sede_id = sd.id
            JOIN jornadas j ON a.jornada_id = j.id
            JOIN carreras cr ON a.carrera_id = cr.id
            LEFT JOIN programacion_academica conflicto
                ON conflicto.catedratico_id = %s
               AND conflicto.activo = 1
               AND conflicto.id <> a.id
               AND conflicto.dia_semana = a.dia_semana
               AND COALESCE(conflicto.anio, 0) = COALESCE(a.anio, 0)
               AND COALESCE(conflicto.ciclo, '') = COALESCE(a.ciclo, '')
               AND conflicto.hora_inicio < a.hora_fin
               AND conflicto.hora_fin > a.hora_inicio
            WHERE a.activo = 1
              AND a.catedratico_id <> %s
            ORDER BY tiene_conflicto, FIELD(a.dia_semana, 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'), a.hora_inicio, c.nombre
        """
        return DatabaseManager.execute_query(query, (catedratico_id, catedratico_id))

    @staticmethod
    def asignar_existente_a_catedratico(programacion_id, catedratico_id):
        assignment = CursoDAO.get_assignment_by_id(programacion_id)
        if not assignment:
            return False, "La programación seleccionada no existe."

        conflict_query = """
            SELECT COUNT(*) as total
            FROM programacion_academica
            WHERE catedratico_id = %s
              AND activo = 1
              AND id <> %s
              AND dia_semana = %s
              AND COALESCE(anio, 0) = COALESCE(%s, 0)
              AND COALESCE(ciclo, '') = COALESCE(%s, '')
              AND hora_inicio < %s
              AND hora_fin > %s
        """
        conflict = DatabaseManager.execute_query(
            conflict_query,
            (
                catedratico_id,
                programacion_id,
                assignment['dia_semana'],
                assignment.get('anio'),
                assignment.get('ciclo'),
                assignment['hora_fin'],
                assignment['hora_inicio']
            )
        )
        if conflict and conflict[0]['total'] > 0:
            return False, "No se puede asignar: el catedrático ya tiene ocupado ese horario."

        DatabaseManager.execute_query(
            "UPDATE programacion_academica SET catedratico_id = %s WHERE id = %s",
            (catedratico_id, programacion_id),
            fetch=False
        )
        return True, "Curso asignado al catedrático exitosamente."

class PersonaRolesDAO:
    @staticmethod
    def add_role(persona_id, tipo_persona_id):
        query = "INSERT IGNORE INTO persona_roles (persona_id, tipo_persona_id) VALUES (%s, %s)"
        return DatabaseManager.execute_insert(query, (persona_id, tipo_persona_id))
        
    @staticmethod
    def get_roles(persona_id):
        query = """
            SELECT pr.*, t.nombre as tipo_persona_nombre 
            FROM persona_roles pr
            JOIN tipos_persona t ON pr.tipo_persona_id = t.id
            WHERE pr.persona_id = %s AND pr.activo = 1
        """
        return DatabaseManager.execute_query(query, (persona_id,))
        
    @staticmethod
    def remove_role(persona_id, tipo_persona_id):
        query = "UPDATE persona_roles SET activo = 0 WHERE persona_id = %s AND tipo_persona_id = %s"
        return DatabaseManager.execute_query(query, (persona_id, tipo_persona_id), fetch=False)

class PersonaCarnetDAO:
    @staticmethod
    def get_by_persona(persona_id):
        query = """
            SELECT pc.*, s.nombre as sede_nombre
            FROM persona_carnets pc
            LEFT JOIN sedes s ON pc.sede_id = s.id
            WHERE pc.persona_id = %s
            ORDER BY s.nombre, pc.id
        """
        return DatabaseManager.execute_query(query, (persona_id,))

    @staticmethod
    def upsert(persona_id, sede_id, codigo_carnet):
        existing = DatabaseManager.execute_query(
            """
            SELECT persona_id, sede_id
            FROM persona_carnets
            WHERE codigo_carnet = %s
              AND NOT (persona_id = %s AND sede_id = %s)
            """,
            (codigo_carnet, persona_id, sede_id)
        )
        if existing:
            raise ValueError("Ese codigo de carnet ya esta asignado a otra persona o sede.")

        query = """
            INSERT INTO persona_carnets (persona_id, sede_id, codigo_carnet)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE codigo_carnet = VALUES(codigo_carnet)
        """
        return DatabaseManager.execute_insert(query, (persona_id, sede_id, codigo_carnet))

    @staticmethod
    def has_for_sede(persona_id, sede_id):
        query = """
            SELECT COUNT(*) as total
            FROM persona_carnets
            WHERE persona_id = %s AND sede_id = %s AND codigo_carnet IS NOT NULL AND codigo_carnet <> ''
        """
        rows = DatabaseManager.execute_query(query, (persona_id, sede_id))
        return bool(rows and rows[0]['total'] > 0)

class PersonaDAO:
    @staticmethod
    def create(nombre, apellido, telefono, email, tipo_persona_id, 
               foto_path, firma_path, encoding_facial, codigo_carnet, password_hash=None, restriccion_ingreso=0):
        # Insert basic info (removed seccion_id, carrera_id, tipo_persona_id from personas table logic)
        query = """
            INSERT INTO personas 
            (nombre, apellido, telefono, email, 
             foto_path, firma_path, encoding_facial, password_hash, restriccion_ingreso)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        encoding_json = json.dumps(encoding_facial.tolist()) if encoding_facial is not None else None
        params = (nombre, apellido, telefono, email,
                 foto_path, firma_path, encoding_json, password_hash, restriccion_ingreso)
        
        persona_id = DatabaseManager.execute_insert(query, params)
        
        if persona_id:
            if codigo_carnet:
                default_sede_id = SedeDAO.get_default_id()
                if default_sede_id:
                    PersonaCarnetDAO.upsert(persona_id, default_sede_id, codigo_carnet)
            if tipo_persona_id:
                PersonaRolesDAO.add_role(persona_id, tipo_persona_id)
                
        return persona_id
    
    @staticmethod
    def _get_base_query():
        return """
            SELECT p.*, pc.codigo_carnet, ps.seccion_id, pr.carrera_id, t.tipo_persona_nombre 
            FROM personas p 
            LEFT JOIN (
                SELECT persona_id, MIN(codigo_carnet) as codigo_carnet
                FROM persona_carnets
                GROUP BY persona_id
            ) pc ON p.id = pc.persona_id 
            LEFT JOIN (
                SELECT persona_id, MIN(seccion_id) as seccion_id
                FROM persona_secciones
                GROUP BY persona_id
            ) ps ON p.id = ps.persona_id 
            LEFT JOIN (
                SELECT persona_id, MIN(carrera_id) as carrera_id
                FROM persona_carreras
                GROUP BY persona_id
            ) pr ON p.id = pr.persona_id 
            LEFT JOIN (
                SELECT pr2.persona_id, GROUP_CONCAT(tp.nombre SEPARATOR ', ') as tipo_persona_nombre 
                FROM persona_roles pr2 
                JOIN tipos_persona tp ON pr2.tipo_persona_id = tp.id 
                WHERE pr2.activo = 1 
                GROUP BY pr2.persona_id
            ) t ON p.id = t.persona_id
        """

    @staticmethod
    def get_by_id(persona_id):
        query = PersonaDAO._get_base_query() + " WHERE p.id = %s"
        results = DatabaseManager.execute_query(query, (persona_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_email(email):
        query = PersonaDAO._get_base_query() + " WHERE p.email = %s"
        results = DatabaseManager.execute_query(query, (email,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_codigo_carnet(codigo):
        query = """
            SELECT p.*, pc.codigo_carnet, ps.seccion_id, pr.carrera_id, t.tipo_persona_nombre
            FROM persona_carnets pc
            JOIN personas p ON p.id = pc.persona_id
            LEFT JOIN (
                SELECT persona_id, MIN(seccion_id) as seccion_id
                FROM persona_secciones
                GROUP BY persona_id
            ) ps ON p.id = ps.persona_id
            LEFT JOIN (
                SELECT persona_id, MIN(carrera_id) as carrera_id
                FROM persona_carreras
                GROUP BY persona_id
            ) pr ON p.id = pr.persona_id
            LEFT JOIN (
                SELECT pr2.persona_id, GROUP_CONCAT(tp.nombre SEPARATOR ', ') as tipo_persona_nombre
                FROM persona_roles pr2
                JOIN tipos_persona tp ON pr2.tipo_persona_id = tp.id
                WHERE pr2.activo = 1
                GROUP BY pr2.persona_id
            ) t ON p.id = t.persona_id
            WHERE pc.codigo_carnet = %s
            LIMIT 1
        """
        results = DatabaseManager.execute_query(query, (codigo,))
        return results[0] if results else None
    
    @staticmethod
    def get_all_encodings():
        query = """
            SELECT id, nombre, apellido, encoding_facial, restriccion_ingreso 
            FROM personas 
            WHERE encoding_facial IS NOT NULL
        """
        results = DatabaseManager.execute_query(query)
        for person in results:
            if person['encoding_facial']:
                person['encoding_facial'] = json.loads(person['encoding_facial'])
        return results
    
    @staticmethod
    def get_by_type(tipo_persona_id):
        query = """
            SELECT p.*, pc.codigo_carnet, ps.seccion_id, pr.carrera_id, tp.nombre as tipo_persona_nombre 
            FROM personas p 
            JOIN persona_roles proles ON p.id = proles.persona_id AND proles.activo = 1
            JOIN tipos_persona tp ON proles.tipo_persona_id = tp.id
            LEFT JOIN (
                SELECT persona_id, MIN(codigo_carnet) as codigo_carnet
                FROM persona_carnets
                GROUP BY persona_id
            ) pc ON p.id = pc.persona_id 
            LEFT JOIN (
                SELECT persona_id, MIN(seccion_id) as seccion_id
                FROM persona_secciones
                GROUP BY persona_id
            ) ps ON p.id = ps.persona_id 
            LEFT JOIN (
                SELECT persona_id, MIN(carrera_id) as carrera_id
                FROM persona_carreras
                GROUP BY persona_id
            ) pr ON p.id = pr.persona_id 
            WHERE proles.tipo_persona_id = %s 
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (tipo_persona_id,))
    
    @staticmethod
    def update_password(persona_id, password_hash):
        query = "UPDATE personas SET password_hash = %s WHERE id = %s"
        return DatabaseManager.execute_query(query, (password_hash, persona_id), fetch=False)
    
    @staticmethod
    def get_all():
        query = PersonaDAO._get_base_query() + " ORDER BY p.apellido, p.nombre"
        return DatabaseManager.execute_query(query)

    @staticmethod
    def get_assignable():
        query = PersonaDAO._get_base_query() + """
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query)

class CursoDAO:
    @staticmethod
    def create(nombre, codigo, descripcion=None):
        query = "INSERT INTO cursos (nombre, codigo, descripcion) VALUES (%s, %s, %s)"
        params = (nombre, codigo, descripcion)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_by_id(curso_id):
        query = "SELECT * FROM cursos WHERE id = %s"
        results = DatabaseManager.execute_query(query, (curso_id,))
        return results[0] if results else None

    @staticmethod
    def get_assignment_by_id(assignment_id):
        query = """
            SELECT a.id as assignment_id, a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   c.nombre as nombre, c.codigo as codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   p.nombre as catedratico_nombre, p.apellido as catedratico_apellido,
                   sd.nombre as sede_nombre, j.nombre as jornada_nombre, cr.nombre as carrera_nombre
            FROM programacion_academica a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN personas p ON a.catedratico_id = p.id
            JOIN sedes sd ON a.sede_id = sd.id
            JOIN jornadas j ON a.jornada_id = j.id
            JOIN carreras cr ON a.carrera_id = cr.id
            WHERE a.id = %s
        """
        results = DatabaseManager.execute_query(query, (assignment_id,))
        return results[0] if results else None
    
    @staticmethod
    def get_by_catedratico(catedratico_id):
        query = """
            SELECT a.id as assignment_id, a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   c.nombre as nombre, c.codigo as codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sl.nombre as salon_nombre, sl.ubicacion as salon_ubicacion,
                   sd.nombre as sede_nombre, j.nombre as jornada_nombre, cr.nombre as carrera_nombre,
                   CONCAT(a.dia_semana, ' ', DATE_FORMAT(a.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(a.hora_fin, '%H:%i')) as horario_full
            FROM programacion_academica a
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN sedes sd ON a.sede_id = sd.id
            JOIN jornadas j ON a.jornada_id = j.id
            JOIN carreras cr ON a.carrera_id = cr.id
            WHERE a.catedratico_id = %s AND a.activo = 1
            ORDER BY FIELD(a.dia_semana, 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'), a.hora_inicio
        """
        return DatabaseManager.execute_query(query, (catedratico_id,))
    
    @staticmethod
    def get_all():
        query = "SELECT * FROM cursos ORDER BY nombre"
        return DatabaseManager.execute_query(query)

    @staticmethod
    def get_all_assignments():
        return ProgramacionAcademicaDAO.get_all()

class AsignacionCursoDAO:
    @staticmethod
    def create(persona_id, programacion_academica_id):
        query = """
            INSERT INTO inscripciones_academicas (persona_id, programacion_academica_id, estado)
            VALUES (%s, %s, 'ACTIVO')
            ON DUPLICATE KEY UPDATE estado = 'ACTIVO'
        """
        return DatabaseManager.execute_insert(query, (persona_id, programacion_academica_id))
    
    @staticmethod
    def get_personas_by_curso(assignment_id):
        query = """
            SELECT p.*, pc.codigo_carnet, t.nombre as tipo_persona_nombre 
            FROM personas p
            INNER JOIN inscripciones_academicas i ON p.id = i.persona_id
            LEFT JOIN persona_carnets pc ON p.id = pc.persona_id
            LEFT JOIN persona_roles pr ON p.id = pr.persona_id AND pr.activo = 1
            LEFT JOIN tipos_persona t ON pr.tipo_persona_id = t.id
            WHERE i.programacion_academica_id = %s AND i.estado = 'ACTIVO'
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (assignment_id,))
    
    @staticmethod
    def get_cursos_by_persona(persona_id):
        query = """
            SELECT a.id as assignment_id, a.*, c.nombre as curso_nombre, c.codigo as curso_codigo,
                   c.nombre as nombre, c.codigo as codigo,
                   s.nombre as seccion_nombre,
                   sl.codigo as salon_codigo, sd.nombre as sede_nombre, j.nombre as jornada_nombre,
                   cr.nombre as carrera_nombre,
                   CONCAT(a.dia_semana, ' ', DATE_FORMAT(a.hora_inicio, '%H:%i'), ' - ', DATE_FORMAT(a.hora_fin, '%H:%i')) as horario_full
            FROM programacion_academica a
            INNER JOIN inscripciones_academicas i ON a.id = i.programacion_academica_id
            JOIN cursos c ON a.curso_id = c.id
            JOIN secciones s ON a.seccion_id = s.id
            JOIN salones sl ON a.salon_id = sl.id
            JOIN sedes sd ON a.sede_id = sd.id
            JOIN jornadas j ON a.jornada_id = j.id
            JOIN carreras cr ON a.carrera_id = cr.id
            WHERE i.persona_id = %s AND i.estado = 'ACTIVO' AND a.activo = 1
            ORDER BY FIELD(a.dia_semana, 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'), a.hora_inicio, c.nombre
        """
        return DatabaseManager.execute_query(query, (persona_id,))
    
    @staticmethod
    def update_estado(persona_id, programacion_academica_id, estado):
        query = "UPDATE inscripciones_academicas SET estado = %s WHERE persona_id = %s AND programacion_academica_id = %s"
        return DatabaseManager.execute_query(query, (estado, persona_id, programacion_academica_id), fetch=False)

class RegistroAccesoDAO:
    @staticmethod
    def _has_sede_id():
        rows = DatabaseManager.execute_query("SHOW COLUMNS FROM registros_acceso LIKE 'sede_id'")
        return bool(rows)

    @staticmethod
    def create(persona_id, punto_acceso, metodo, observacion=None, sede_id=None):
        if sede_id and RegistroAccesoDAO._has_sede_id():
            query = """
                INSERT INTO registros_acceso (persona_id, sede_id, punto_acceso, metodo, observacion)
                VALUES (%s, %s, %s, %s, %s)
            """
            params = (persona_id, sede_id, punto_acceso, metodo, observacion)
        else:
            query = """
                INSERT INTO registros_acceso (persona_id, punto_acceso, metodo, observacion)
                VALUES (%s, %s, %s, %s)
            """
            params = (persona_id, punto_acceso, metodo, observacion)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def get_recent_by_person(persona_id, minutes=5, sede_id=None, punto_acceso=None):
        query = """
            SELECT * FROM registros_acceso 
            WHERE persona_id = %s 
            AND fecha_hora >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
        """
        params = [persona_id, minutes]
        if sede_id and RegistroAccesoDAO._has_sede_id():
            query += " AND sede_id = %s"
            params.append(sede_id)
        if punto_acceso:
            query += " AND punto_acceso = %s"
            params.append(punto_acceso)
        query += " ORDER BY fecha_hora DESC LIMIT 1"
        results = DatabaseManager.execute_query(query, tuple(params))
        return results[0] if results else None
    
    @staticmethod
    def get_by_date(fecha, punto_acceso=None):
        query = "SELECT * FROM registros_acceso WHERE DATE(fecha_hora) = %s"
        params = [fecha]
        if punto_acceso:
            query += " AND punto_acceso = %s"
            params.append(punto_acceso)
        query += " ORDER BY fecha_hora DESC"
        return DatabaseManager.execute_query(query, tuple(params))

class SesionClaseDAO:
    @staticmethod
    def create(programacion_academica_id, fecha, hora_inicio, hora_fin, estado='PROGRAMADA'):
        query = """
            INSERT INTO sesiones_clase (programacion_academica_id, fecha, hora_inicio, hora_fin, estado)
            VALUES (%s, %s, %s, %s, %s)
        """
        return DatabaseManager.execute_insert(query, (programacion_academica_id, fecha, hora_inicio, hora_fin, estado))

    @staticmethod
    def get_by_prog_and_fecha(programacion_academica_id, fecha):
        query = "SELECT * FROM sesiones_clase WHERE programacion_academica_id = %s AND fecha = %s"
        results = DatabaseManager.execute_query(query, (programacion_academica_id, fecha))
        return results[0] if results else None

    @staticmethod
    def update_estado(sesion_id, estado, observacion=None):
        query = "UPDATE sesiones_clase SET estado = %s, observacion = %s WHERE id = %s"
        return DatabaseManager.execute_query(query, (estado, observacion, sesion_id), fetch=False)

class AsistenciaClaseDAO:
    @staticmethod
    def create(sesion_clase_id, persona_id, metodo, confirmado_por=None, observacion=None):
        query = """
            INSERT INTO asistencias_clase 
            (sesion_clase_id, persona_id, metodo, confirmado_por, observacion)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (sesion_clase_id, persona_id, metodo, confirmado_por, observacion)
        return DatabaseManager.execute_insert(query, params)
    
    @staticmethod
    def create_batch(attendance_records):
        """
        Records should be tuples of (sesion_clase_id, persona_id, fecha_hora, metodo, confirmado_por, observacion)
        """
        query = """
            INSERT IGNORE INTO asistencias_clase 
            (sesion_clase_id, persona_id, fecha_hora, metodo, confirmado_por, observacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return DatabaseManager.execute_many(query, attendance_records)
    
    @staticmethod
    def get_by_curso_and_fecha(assignment_id, fecha):
        query = """
            SELECT a.*, p.nombre, p.apellido, p.email, p.foto_path
            FROM asistencias_clase a
            INNER JOIN sesiones_clase sc ON a.sesion_clase_id = sc.id
            INNER JOIN personas p ON a.persona_id = p.id
            WHERE sc.programacion_academica_id = %s AND sc.fecha = %s
            ORDER BY p.apellido, p.nombre
        """
        return DatabaseManager.execute_query(query, (assignment_id, fecha))
    
    @staticmethod
    def get_all_by_date(fecha):
        query = """
            SELECT a.*, p.nombre, p.apellido, p.email, sc.programacion_academica_id
            FROM asistencias_clase a
            INNER JOIN sesiones_clase sc ON a.sesion_clase_id = sc.id
            INNER JOIN personas p ON a.persona_id = p.id
            WHERE sc.fecha = %s
            ORDER BY a.fecha_hora DESC
        """
        return DatabaseManager.execute_query(query, (fecha,))
    
    @staticmethod
    def exists(persona_id, assignment_id, fecha):
        query = """
            SELECT COUNT(*) as count 
            FROM asistencias_clase a
            INNER JOIN sesiones_clase sc ON a.sesion_clase_id = sc.id
            WHERE a.persona_id = %s AND sc.programacion_academica_id = %s AND sc.fecha = %s
        """
        result = DatabaseManager.execute_query(query, (persona_id, assignment_id, fecha))
        return result[0]['count'] > 0 if result else False

    @staticmethod
    def delete_by_curso_and_fecha(assignment_id, fecha):
        sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, fecha)
        if not sesion:
            return 0
        deleted = DatabaseManager.execute_query(
            "DELETE FROM asistencias_clase WHERE sesion_clase_id = %s",
            (sesion['id'],),
            fetch=False
        )
        SesionClaseDAO.update_estado(sesion['id'], 'EN_CURSO', 'Confirmacion eliminada para pruebas')
        return deleted
