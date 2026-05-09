"""
Script para insertar asistencias de prueba.
Marca a ALGUNOS estudiantes como presentes para que el monitor muestre variedad (verde/rojo).
"""
from database.db_manager import DatabaseManager
from datetime import datetime

def seed():
    # 1. Get all students assigned to salons via courses
    query = """
        SELECT DISTINCT acur.persona_id, acat.curso_id, acat.salon_id
        FROM asignaciones_catedratico acat
        INNER JOIN asignaciones_curso acur ON acur.curso_id = acat.curso_id AND acur.estado = 'ACTIVO'
        ORDER BY acat.salon_id, acur.persona_id
    """
    rows = DatabaseManager.execute_query(query)
    
    if not rows:
        print("No hay estudiantes asignados a salones. Verifica tus datos.")
        return
    
    print(f"Encontrados {len(rows)} registros de estudiantes en salones.")
    
    # 2. Mark roughly half as present (every other one)
    now = datetime.now()
    inserted = 0
    
    for i, r in enumerate(rows):
        if i % 2 == 0:  # Solo los pares -> presente
            try:
                ins = """
                    INSERT INTO asistencias_clase 
                    (persona_id, curso_id, salon_id, fecha_hora, metodo, observacion)
                    VALUES (%s, %s, %s, %s, 'BIOMETRICO', 'Seed de prueba')
                """
                DatabaseManager.execute_query(ins, (r['persona_id'], r['curso_id'], r['salon_id'], now), fetch=False)
                inserted += 1
                print(f"  [+] persona_id={r['persona_id']}, curso_id={r['curso_id']}, salon_id={r['salon_id']}")
            except Exception as e:
                print(f"  [!] Error insertando persona_id={r['persona_id']}: {e}")
    
    print(f"\nListo! Se insertaron {inserted} asistencias de prueba.")
    print(f"De {len(rows)} estudiantes, {inserted} marcados como PRESENTES, {len(rows)-inserted} como AUSENTES.")

if __name__ == '__main__':
    seed()
