-- Procedimiento para eliminar una persona y todos sus datos dependientes.
-- Uso:
--   CALL sp_eliminar_persona_completa(123);

DELIMITER $$

DROP PROCEDURE IF EXISTS sp_eliminar_persona_completa $$

CREATE PROCEDURE sp_eliminar_persona_completa(IN p_persona_id INT)
BEGIN
    DECLARE v_existe INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT COUNT(*)
      INTO v_existe
      FROM personas
     WHERE id = p_persona_id;

    IF v_existe = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No existe una persona con el ID indicado.';
    END IF;

    UPDATE asistencias_clase
       SET confirmado_por = NULL
     WHERE confirmado_por = p_persona_id;

    DELETE ac
      FROM asistencias_clase ac
      JOIN sesiones_clase sc ON sc.id = ac.sesion_clase_id
      JOIN programacion_academica pa ON pa.id = sc.programacion_academica_id
     WHERE pa.catedratico_id = p_persona_id;

    DELETE sc
      FROM sesiones_clase sc
      JOIN programacion_academica pa ON pa.id = sc.programacion_academica_id
     WHERE pa.catedratico_id = p_persona_id;

    DELETE FROM asistencias_clase
     WHERE persona_id = p_persona_id;

    DELETE FROM inscripciones_academicas
     WHERE persona_id = p_persona_id;

    DELETE FROM registros_acceso
     WHERE persona_id = p_persona_id;

    DELETE FROM programacion_academica
     WHERE catedratico_id = p_persona_id;

    DELETE FROM persona_carnets
     WHERE persona_id = p_persona_id;

    DELETE FROM persona_secciones
     WHERE persona_id = p_persona_id;

    DELETE FROM persona_carreras
     WHERE persona_id = p_persona_id;

    DELETE FROM persona_roles
     WHERE persona_id = p_persona_id;

    DELETE FROM personas
     WHERE id = p_persona_id;

    COMMIT;
END $$

DELIMITER ;
