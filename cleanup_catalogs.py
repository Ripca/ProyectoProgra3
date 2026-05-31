import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import DatabaseManager

def main():
    print("Iniciando limpieza de catálogos y tablas restantes...")
    
    try:
        # Cursos: keep 1, 2, 3
        DatabaseManager.execute_query("DELETE FROM cursos WHERE id NOT IN (1, 2, 3)", fetch=False)
        
        # Carreras: keep 1, 2, 3
        DatabaseManager.execute_query("DELETE FROM carreras WHERE id NOT IN (1, 2, 3)", fetch=False)
        
        # Salones: keep 1, 2, 3
        DatabaseManager.execute_query("DELETE FROM salones WHERE id NOT IN (1, 2, 3)", fetch=False)
        
        # Secciones: keep 1, 2, 3
        DatabaseManager.execute_query("DELETE FROM secciones WHERE id NOT IN (1, 2, 3)", fetch=False)
        
        # Jornadas: keep 1, 2, 3
        DatabaseManager.execute_query("DELETE FROM jornadas WHERE id NOT IN (1, 2, 3)", fetch=False)
        
        # Tablas legacy que no se usan o que tienen exceso
        try:
            DatabaseManager.execute_query("DELETE FROM asistencias_clase_legacy", fetch=False)
        except: pass
        try:
            DatabaseManager.execute_query("DELETE FROM asignaciones_catedratico", fetch=False)
        except: pass
        try:
            DatabaseManager.execute_query("DELETE FROM asignaciones_curso", fetch=False)
        except: pass
        
        print("Catálogos limpios. Se han dejado máximo 3 registros por cada tabla importante.")
        
    except Exception as e:
        print(f"Error durante la limpieza: {e}")

if __name__ == '__main__':
    main()
