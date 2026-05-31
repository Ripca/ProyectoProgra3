import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import DatabaseManager

def main():
    print("Iniciando limpieza de la base de datos...")
    
    # 1. Encontrar 1 Administrador
    admin = DatabaseManager.execute_query("""
        SELECT p.id FROM personas p 
        JOIN persona_roles pr ON p.id = pr.persona_id 
        JOIN tipos_persona tp ON pr.tipo_persona_id = tp.id 
        WHERE tp.nombre LIKE '%Admin%' LIMIT 1
    """)
    if not admin:
        # Fallback si no hay admin por rol, usar el ID 1 o buscar por email
        admin = DatabaseManager.execute_query("SELECT id FROM personas WHERE email LIKE '%admin%' LIMIT 1")
    
    # 2. Encontrar 1 Catedrático que tenga una programación académica
    catedratico = DatabaseManager.execute_query("""
        SELECT p.id FROM personas p 
        JOIN programacion_academica pa ON p.id = pa.catedratico_id 
        LIMIT 1
    """)
    
    # 3. Encontrar 1 Estudiante que esté inscrito en la clase del catedrático anterior
    estudiante = None
    if catedratico:
        cat_id = catedratico[0]['id']
        estudiante = DatabaseManager.execute_query(f"""
            SELECT p.id 
            FROM personas p 
            JOIN inscripciones_academicas ia ON p.id = ia.persona_id 
            JOIN programacion_academica pa ON ia.programacion_academica_id = pa.id 
            WHERE pa.catedratico_id = {cat_id} LIMIT 1
        """)
    else:
        # Fallback si no hay relaciones completas
        estudiante = DatabaseManager.execute_query("SELECT id FROM personas WHERE role = 'estudiante' LIMIT 1")

    ids_to_keep = []
    if admin and admin[0]: ids_to_keep.append(str(admin[0]['id']))
    if catedratico and catedratico[0]: ids_to_keep.append(str(catedratico[0]['id']))
    if estudiante and estudiante[0]: ids_to_keep.append(str(estudiante[0]['id']))
    
    # Eliminar duplicados si una persona cumple múltiples roles
    ids_to_keep = list(set(ids_to_keep))
    
    if not ids_to_keep:
        print("No se encontraron registros clave para preservar. Abortando limpieza para evitar base de datos vacía.")
        return
        
    ids_str = ",".join(ids_to_keep)
    print(f"IDs de Personas que se conservarán: {ids_str}")
    
    try:
        # Contar antes
        total_before = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM personas")[0]['c']
        prog_before = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM programacion_academica")[0]['c']
        print(f"Total de personas antes: {total_before}")
        print(f"Total de programaciones antes: {prog_before}")
        
        # Manual cascade deletes to avoid constraint errors
        DatabaseManager.execute_query(f"DELETE FROM asistencias_clase WHERE persona_id NOT IN ({ids_str})", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM registros_acceso WHERE persona_id NOT IN ({ids_str})", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM inscripciones_academicas WHERE persona_id NOT IN ({ids_str})", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM persona_carnets WHERE persona_id NOT IN ({ids_str})", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM persona_roles WHERE persona_id NOT IN ({ids_str})", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM persona_secciones WHERE persona_id NOT IN ({ids_str})", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM persona_carreras WHERE persona_id NOT IN ({ids_str})", fetch=False)
        
        # Delete related to programacion_academica that we drop
        DatabaseManager.execute_query(f"DELETE FROM asistencias_clase WHERE sesion_clase_id IN (SELECT id FROM sesiones_clase WHERE programacion_academica_id IN (SELECT id FROM programacion_academica WHERE catedratico_id NOT IN ({ids_str})))", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM sesiones_clase WHERE programacion_academica_id IN (SELECT id FROM programacion_academica WHERE catedratico_id NOT IN ({ids_str}))", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM inscripciones_academicas WHERE programacion_academica_id IN (SELECT id FROM programacion_academica WHERE catedratico_id NOT IN ({ids_str}))", fetch=False)
        DatabaseManager.execute_query(f"DELETE FROM programacion_academica WHERE catedratico_id NOT IN ({ids_str})", fetch=False)
        
        # Ejecutar borrado masivo
        DatabaseManager.execute_query(f"DELETE FROM personas WHERE id NOT IN ({ids_str})", fetch=False)
        
        # Contar después
        total_after = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM personas")[0]['c']
        prog_after = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM programacion_academica")[0]['c']
        print(f"Total de personas después: {total_after}")
        print(f"Total de programaciones después: {prog_after}")
        print("Limpieza completada exitosamente.")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")

if __name__ == '__main__':
    main()
