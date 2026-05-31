"""
Script para insertar asistencias de prueba.
Marca a ALGUNOS estudiantes como presentes para que el monitor muestre variedad (verde/rojo).
"""
from database.db_manager import DatabaseManager
from datetime import datetime

def seed():
    from database.models import SesionClaseDAO
    # 1. Get all students assigned to salons via courses
    query = """
        SELECT DISTINCT acur.persona_id, acat.id as assignment_id, acat.salon_id, acat.hora_inicio, acat.hora_fin
        FROM programacion_academica acat
        INNER JOIN inscripciones_academicas acur ON acur.programacion_academica_id = acat.id AND acur.estado = 'ACTIVO'
        ORDER BY acat.salon_id, acur.persona_id
    """
    rows = DatabaseManager.execute_query(query)
    
    if not rows:
        print("No hay estudiantes asignados a salones. Verifica tus datos.")
        return
    
    print(f"Encontrados {len(rows)} registros de estudiantes en salones.")
    
    # 2. Mark roughly half as present (every other one)
    now = datetime.now()
    hoy = now.date()
    inserted = 0
    
    for i, r in enumerate(rows):
        if i % 2 == 0:  # Solo los pares -> presente
            try:
                # get or create sesion
                sesion = SesionClaseDAO.get_by_prog_and_fecha(r['assignment_id'], hoy)
                if not sesion:
                    sesion_id = SesionClaseDAO.create(r['assignment_id'], hoy, r['hora_inicio'], r['hora_fin'], 'FINALIZADA')
                else:
                    sesion_id = sesion['id']

                ins = """
                    INSERT INTO asistencias_clase 
                    (sesion_clase_id, persona_id, fecha_hora, metodo, observacion)
                    VALUES (%s, %s, %s, 'BIOMETRICO', 'Seed de prueba')
                """
                DatabaseManager.execute_query(ins, (sesion_id, r['persona_id'], now), fetch=False)
                inserted += 1
                print(f"  [+] persona_id={r['persona_id']}, assignment_id={r['assignment_id']}, salon_id={r['salon_id']}")
            except Exception as e:
                print(f"  [!] Error insertando persona_id={r['persona_id']}: {e}")
    
    print(f"\nListo! Se insertaron {inserted} asistencias de prueba.")
    print(f"De {len(rows)} estudiantes, {inserted} marcados como PRESENTES, {len(rows)-inserted} como AUSENTES.")

if __name__ == '__main__':
    seed()
