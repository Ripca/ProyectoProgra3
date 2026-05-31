-- Script para resetear la confirmación de asistencia de un curso en una fecha específica
-- Útil para pruebas donde se requiere confirmar la asistencia múltiples veces.

DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_reset_asistencia(
    IN p_assignment_id INT,
    IN p_fecha DATE
)
BEGIN
    DECLARE v_sesion_id INT;
    
    -- Obtener la sesión finalizada
    SELECT id INTO v_sesion_id 
    FROM sesion_clase 
    WHERE assignment_id = p_assignment_id 
      AND fecha = p_fecha;
      
    IF v_sesion_id IS NOT NULL THEN
        -- Eliminar los registros de asistencia asociados a la sesión
        DELETE FROM asistencia_clase WHERE sesion_clase_id = v_sesion_id;
        
        -- Opcionalmente eliminar la sesión o regresarla a estado pendiente
        -- DELETE FROM sesion_clase WHERE id = v_sesion_id;
        -- O si se manejan estados:
        UPDATE sesion_clase SET estado = 'PENDIENTE' WHERE id = v_sesion_id;
        
        SELECT 'Confirmación de asistencia reseteada exitosamente' as Mensaje;
    ELSE
        SELECT 'No se encontró confirmación para esta fecha' as Mensaje;
    END IF;
END //

DELIMITER ;
