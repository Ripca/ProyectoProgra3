"""
Attendance Tree Module
Generates attendance tree structure from access logs
"""
from datetime import datetime, date
from database.models import AsignacionCursoDAO, RegistroAccesoDAO, CursoDAO, AsistenciaClaseDAO, SalonDAO
import logging

logger = logging.getLogger(__name__)


class AttendanceTree:
    """Generates attendance tree for courses"""
    
    @staticmethod
    def get_course_attendance(assignment_id, fecha=None):
        """
        Get attendance tree for a specific class assignment
        
        Args:
            assignment_id: ID from asignaciones_catedratico
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
            # Note: For now, AsignacionCurso still uses curso_id, 
            # but ideally should filter by seccion_id if students belong to specific sections
            estudiantes = AsignacionCursoDAO.get_personas_by_curso(assignment['curso_id'])
            
            # Get access logs (biometric or manual) for the classroom today
            asistencias = AsistenciaClaseDAO.get_by_curso_and_fecha(assignment['curso_id'], fecha)
            
            # Create set of student IDs who accessed
            accessed_ids = {a['persona_id'] for a in asistencias}
            
            # Build attendance list
            attendance_list = []
            for estudiante in estudiantes:
                presente = estudiante['id'] in accessed_ids
                
                # Find access time if present
                access_time = None
                if presente:
                    for a in asistencias:
                        if a['persona_id'] == estudiante['id']:
                            access_time = a['fecha_hora']
                            break
                
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
            logger.error(f"Error getting course attendance: {e}")
            return None
    
    @staticmethod
    def get_building_tree(fecha=None):
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
                SELECT r.*, p.nombre, p.apellido, p.codigo_carnet, p.foto_path, p.email, p.restriccion_ingreso
                FROM registros_acceso r
                INNER JOIN personas p ON r.persona_id = p.id
                WHERE DATE(r.fecha_hora) = %s
                ORDER BY r.fecha_hora DESC
            """
            access_logs = DatabaseManager.execute_query(access_query, (fecha,))
            
            # 2. Get Classroom Attendance (Salones)
            # Get all active salons
            salones = SalonDAO.get_all()
            logger.info(f"Monitor: found {len(salones) if salones else 0} active salones")
            
            salon_list = []
            for s in salones:
                # Get all students assigned to courses taught in this salon
                # LEFT JOIN with attendance to get present/absent status
                query = """
                    SELECT DISTINCT p.id, p.nombre, p.apellido, p.foto_path, p.email, p.codigo_carnet, p.restriccion_ingreso,
                           CASE WHEN ac_att.id IS NOT NULL THEN 1 ELSE 0 END as presente
                    FROM asignaciones_catedratico acat
                    INNER JOIN asignaciones_curso acur ON acur.curso_id = acat.curso_id AND acur.estado = 'ACTIVO'
                    INNER JOIN personas p ON p.id = acur.persona_id
                    LEFT JOIN asistencias_clase ac_att ON ac_att.persona_id = p.id 
                        AND ac_att.salon_id = %s 
                        AND DATE(ac_att.fecha_hora) = %s
                    WHERE acat.salon_id = %s
                    ORDER BY p.apellido, p.nombre
                """
                students = DatabaseManager.execute_query(query, (s['id'], fecha, s['id']))
                
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
