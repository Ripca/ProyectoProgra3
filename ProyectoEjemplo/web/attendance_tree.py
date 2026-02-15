"""
Attendance Tree Module
Generates attendance tree structure from access logs
"""
from datetime import datetime, date
from database.models import InscripcionDAO, RegistroAccesoDAO, CursoDAO
import logging

logger = logging.getLogger(__name__)


class AttendanceTree:
    """Generates attendance tree for courses"""
    
    @staticmethod
    def get_course_attendance(curso_id, fecha=None):
        """
        Get attendance tree for a course
        
        Args:
            curso_id: Course ID
            fecha: Date (defaults to today)
        
        Returns:
            dict: Attendance data with students marked as present/absent
        """
        try:
            if fecha is None:
                fecha = date.today()
            
            # Get course info
            curso = CursoDAO.get_by_id(curso_id)
            if not curso:
                return None
            
            # Get enrolled students
            estudiantes = InscripcionDAO.get_estudiantes_by_curso(curso_id)
            
            # Get access logs for the classroom today
            salon = curso['salon']
            accesos = RegistroAccesoDAO.get_today_by_salon(salon) if salon else []
            
            # Create set of student IDs who accessed
            accessed_ids = {acceso['persona_id'] for acceso in accesos}
            
            # Build attendance list
            attendance_list = []
            for estudiante in estudiantes:
                presente = estudiante['id'] in accessed_ids
                
                # Find access time if present
                access_time = None
                if presente:
                    for acceso in accesos:
                        if acceso['persona_id'] == estudiante['id']:
                            access_time = acceso['fecha_hora']
                            break
                
                attendance_list.append({
                    'id': estudiante['id'],
                    'nombre': estudiante['nombre'],
                    'apellido': estudiante['apellido'],
                    'email': estudiante['email'],
                    'foto_path': estudiante['foto_path'],
                    'codigo_carnet': estudiante['codigo_carnet'],
                    'presente': presente,
                    'hora_acceso': access_time
                })
            
            # Sort: present first, then by apellido
            attendance_list.sort(key=lambda x: (not x['presente'], x['apellido']))
            
            # Calculate statistics
            total = len(attendance_list)
            presentes = sum(1 for a in attendance_list if a['presente'])
            ausentes = total - presentes
            
            return {
                'curso': curso,
                'fecha': fecha,
                'salon': salon,
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
        Get hierarchical tree of building/floors/classrooms with attendance
        
        Args:
            fecha: Date (defaults to today)
        
        Returns:
            dict: Hierarchical attendance tree
        """
        try:
            if fecha is None:
                fecha = date.today()
            
            # Get all access logs for today
            accesos = RegistroAccesoDAO.get_by_date_and_location(fecha, tipo_acceso='salon')
            
            # Group by salon
            salon_accesos = {}
            for acceso in accesos:
                salon = acceso.get('salon', 'Sin Salón')
                if salon not in salon_accesos:
                    salon_accesos[salon] = []
                salon_accesos[salon].append(acceso)
            
            # Build tree structure (simplified - could be enhanced with actual building data)
            tree = {
                'edificio': 'UMG Boca del Monte',
                'niveles': []
            }
            
            # Organize by floor (extract from salon number)
            niveles = {}
            for salon, accesos_list in salon_accesos.items():
                # Extract floor from salon (e.g., "Salón 201" -> floor 2)
                try:
                    if salon.startswith('Salón '):
                        salon_num = salon.split()[1]
                        nivel = int(salon_num[0]) if salon_num else 1
                    else:
                        nivel = 1
                except:
                    nivel = 1
                
                if nivel not in niveles:
                    niveles[nivel] = []
                
                niveles[nivel].append({
                    'salon': salon,
                    'accesos': len(accesos_list),
                    'personas': accesos_list
                })
            
            # Convert to list
            for nivel_num in sorted(niveles.keys()):
                tree['niveles'].append({
                    'numero': nivel_num,
                    'nombre': f"Nivel {nivel_num}",
                    'salones': niveles[nivel_num]
                })
            
            return tree
            
        except Exception as e:
            logger.error(f"Error getting building tree: {e}")
            return None
