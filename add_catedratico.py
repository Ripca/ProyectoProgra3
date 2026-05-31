import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import DatabaseManager

def main():
    print("Agregando nuevo catedratico...")
    
    # 1. Insert Persona
    DatabaseManager.execute_query("""
        INSERT INTO personas (nombre, apellido, telefono, email)
        VALUES ('Carlos', 'Docente', '55551111', 'cdocente@miumg.edu.gt')
    """, fetch=False)
    
    # 2. Get the new ID
    new_user = DatabaseManager.execute_query("SELECT id FROM personas WHERE email = 'cdocente@miumg.edu.gt'")
    cat_id = new_user[0]['id']
    
    # 3. Add to persona_roles
    DatabaseManager.execute_query(f"""
        INSERT INTO persona_roles (persona_id, tipo_persona_id)
        VALUES ({cat_id}, 2)
    """, fetch=False)
    
    # 4. Update programacion_academica from Juan (1) to Carlos (cat_id)
    DatabaseManager.execute_query(f"""
        UPDATE programacion_academica SET catedratico_id = {cat_id}
    """, fetch=False)
    
    print(f"Catedratico agregado con ID {cat_id} y clases asignadas.")

if __name__ == '__main__':
    main()
