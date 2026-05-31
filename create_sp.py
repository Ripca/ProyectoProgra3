import mysql.connector

conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='admin', database='db_biometrico')
cursor = conn.cursor()

sql = """
CREATE PROCEDURE sp_reset_asistencia(
    IN p_assignment_id INT,
    IN p_fecha DATE
)
BEGIN
    DECLARE v_sesion_id INT;
    SELECT id INTO v_sesion_id 
    FROM sesiones_clase 
    WHERE programacion_academica_id = p_assignment_id 
      AND fecha = p_fecha;
    IF v_sesion_id IS NOT NULL THEN
        DELETE FROM asistencias_clase WHERE sesion_clase_id = v_sesion_id;
        UPDATE sesiones_clase SET estado = 'EN_CURSO' WHERE id = v_sesion_id;
        SELECT 'Confirmación de asistencia reseteada exitosamente' as Mensaje;
    ELSE
        SELECT 'No se encontró confirmación para esta fecha' as Mensaje;
    END IF;
END
"""

cursor.execute("DROP PROCEDURE IF EXISTS sp_reset_asistencia")
cursor.execute(sql)
conn.commit()
print("SP updated successfully.")
