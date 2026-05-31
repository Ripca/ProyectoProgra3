"""
Attendance Tree Module
Generates attendance tree structure from access logs
"""
from datetime import datetime, date
from database.models import AsignacionCursoDAO, RegistroAccesoDAO, CursoDAO, AsistenciaClaseDAO, SalonDAO
import logging

logger = logging.getLogger(__name__)


def _table_has_column(table_name, column_name):
    from database.db_manager import DatabaseManager

    rows = DatabaseManager.execute_query(f"SHOW COLUMNS FROM {table_name} LIKE %s", (column_name,))
    return bool(rows)


class AttendanceTree:
    """Generates attendance tree for courses"""
    
    @staticmethod
    def get_course_attendance(assignment_id, fecha=None):
        """
        Get attendance tree for a specific class assignment
        
        Args:
            assignment_id: ID from programacion_academica
            fecha: Date (defaults to today)
        
        Returns:
            dict: Attendance data
        """
        try:
            if fecha is None:
                fecha = date.today()
            
            # Get assignment info (course + room + section)
            assignment = CursoDAO.get_assignment_by_id(assignment_id)
            if not assignment:
                return None
            
            # Get enrolled students in THIS course
            estudiantes = AsignacionCursoDAO.get_personas_by_curso(assignment_id)
            
            # Get existing confirmed attendance
            asistencias = AsistenciaClaseDAO.get_by_curso_and_fecha(assignment_id, fecha)
            from database.models import SesionClaseDAO
            sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, fecha)
            finalizada = bool(sesion and sesion.get('estado') == 'FINALIZADA')
            
            # Create set of student IDs who are confirmed
            accessed_ids = {a['persona_id'] for a in asistencias}
            access_times = {a['persona_id']: a['fecha_hora'] for a in asistencias}
            
            # If not confirmed, get from biometric access logs (registros_acceso)
            if not asistencias and not finalizada:
                from database.db_manager import DatabaseManager
                if _table_has_column('registros_acceso', 'salon_id'):
                    raw_logs = DatabaseManager.execute_query(
                        """
                        SELECT persona_id, MIN(fecha_hora) as min_hora
                        FROM registros_acceso
                        WHERE DATE(fecha_hora) = %s AND salon_id = %s
                        GROUP BY persona_id
                        """,
                        (fecha, assignment['salon_id'])
                    )
                else:
                    raw_logs = DatabaseManager.execute_query(
                        """
                        SELECT persona_id, MIN(fecha_hora) as min_hora
                        FROM registros_acceso
                        WHERE DATE(fecha_hora) = %s
                          AND observacion LIKE %s
                        GROUP BY persona_id
                        """,
                        (fecha, f"Salón {assignment['salon_codigo']}%")
                    )
                if raw_logs:
                    accessed_ids = {r['persona_id'] for r in raw_logs}
                    access_times = {r['persona_id']: r['min_hora'] for r in raw_logs}

            # Build attendance list
            attendance_list = []
            for estudiante in estudiantes:
                presente = estudiante['id'] in accessed_ids
                access_time = access_times.get(estudiante['id'])
                
                attendance_list.append({
                    'id': estudiante['id'],
                    'nombre': estudiante['nombre'],
                    'apellido': estudiante['apellido'],
                    'email': estudiante['email'],
                    'foto_path': estudiante['foto_path'],
                    'codigo_carnet': estudiante['codigo_carnet'],
                    'presente': presente,
                    'hora_acceso': access_time,
                    'restriccion_ingreso': bool(estudiante.get('restriccion_ingreso', 0))
                })
            
            # Sort: present first, then by apellido
            attendance_list.sort(key=lambda x: (not x['presente'], x['apellido']))
            
            # Calculate statistics
            total = len(attendance_list)
            presentes = sum(1 for a in attendance_list if a['presente'])
            ausentes = total - presentes
            
            return {
                'assignment': assignment,
                'curso': {
                    'id': assignment['curso_id'],
                    'nombre': assignment['curso_nombre'],
                    'codigo': assignment['curso_codigo'],
                    'catedratico_id': assignment['catedratico_id']
                },
                'fecha': fecha,
                'salon': assignment['salon_codigo'],
                'seccion': assignment['seccion_nombre'],
                'horario': f"{assignment['dia_semana']} {str(assignment['hora_inicio'])[:5]} - {str(assignment['hora_fin'])[:5]}",
                'estudiantes': attendance_list,
                'estadisticas': {
                    'total': total,
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'porcentaje_asistencia': (presentes / total * 100) if total > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting course attendance: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_building_tree(fecha=None, sede_id=None):
        """
        Get hierarchical tree of building/floors/classrooms with attendance.
        Shows ALL students assigned to each salon, marking present/absent.
        Also fetches general access logs from registros_acceso.
        
        Args:
            fecha: Date (defaults to today)
        
        Returns:
            dict: Flattened attendance tree with general access logs
        """
        try:
            if fecha is None:
                fecha = date.today()
            
            from database.db_manager import DatabaseManager
            
            # 1. Get General Access Logs (By Entrance)
            # This uses real data from registros_acceso table
            access_query = """
                SELECT r.*, p.nombre, p.apellido, pc.codigo_carnet, p.foto_path, p.email, p.restriccion_ingreso
                FROM registros_acceso r
                INNER JOIN personas p ON r.persona_id = p.id
                LEFT JOIN persona_carnets pc ON p.id = pc.persona_id
                WHERE DATE(r.fecha_hora) = %s
                  AND r.punto_acceso = 'ENTRADA_PRINCIPAL'
            """
            access_params = [fecha]
            if sede_id and _table_has_column('registros_acceso', 'sede_id'):
                access_query += " AND r.sede_id = %s"
                access_params.append(sede_id)
            access_query += " ORDER BY r.fecha_hora DESC"
            access_logs = DatabaseManager.execute_query(access_query, tuple(access_params))
            
            # 2. Get Classroom Attendance (Salones)
            # Get all active salons
            if sede_id:
                salones = DatabaseManager.execute_query(
                    "SELECT * FROM salones WHERE activo = 1 AND sede_id = %s ORDER BY codigo",
                    (sede_id,)
                )
            else:
                salones = SalonDAO.get_all()
            logger.info(f"Monitor: found {len(salones) if salones else 0} active salones")
            
            salon_list = []
            for s in salones:
                # Get all students assigned to courses taught in this salon
                # LEFT JOIN with attendance to get present/absent status
                query = """
                    SELECT p.id, p.nombre, p.apellido, p.foto_path, p.email, pc.codigo_carnet, p.restriccion_ingreso,
                           MAX(CASE WHEN ac_att.id IS NOT NULL THEN 1 ELSE 0 END) as presente
                    FROM programacion_academica acat
                    INNER JOIN inscripciones_academicas acur ON acur.programacion_academica_id = acat.id AND acur.estado = 'ACTIVO'
                    INNER JOIN personas p ON p.id = acur.persona_id
                    LEFT JOIN persona_carnets pc ON p.id = pc.persona_id
                    LEFT JOIN sesiones_clase sc ON sc.programacion_academica_id = acat.id AND sc.fecha = %s
                    LEFT JOIN asistencias_clase ac_att ON ac_att.persona_id = p.id AND ac_att.sesion_clase_id = sc.id
                    WHERE acat.salon_id = %s
                    GROUP BY p.id, p.nombre, p.apellido, p.foto_path, p.email, pc.codigo_carnet, p.restriccion_ingreso
                    ORDER BY p.apellido, p.nombre
                """
                students = DatabaseManager.execute_query(query, (fecha, s['id']))
                
                student_list = []
                if students:
                    for st in students:
                        student_list.append({
                            'id': st['id'],
                            'nombre_completo': f"{st['nombre']} {st['apellido']}",
                            'foto_path': st['foto_path'],
                            'email': st['email'],
                            'codigo_carnet': st['codigo_carnet'],
                            'presente': bool(st['presente']),
                            'alerta': not bool(st['presente']),
                            'restriccion_ingreso': bool(st.get('restriccion_ingreso', 0))
                        })
                
                salon_list.append({
                    'id': s['id'],
                    'codigo': s['codigo'],
                    'nombre': s['nombre'],
                    'ubicacion': s.get('ubicacion'),
                    'estudiantes': student_list
                })
            
            return {
                'campus': 'UMG Boca del Monte',
                'salones': salon_list,
                'accesos_generales': access_logs,
                'fecha': fecha
            }
            
        except Exception as e:
            logger.error(f"Error getting building tree: {e}", exc_info=True)
            return None
