-- Evita que un mismo salon tenga dos clases activas en el mismo periodo.
-- Ejecutar despues de resolver cualquier choque existente.

UPDATE programacion_academica
SET ciclo = '1S'
WHERE ciclo IS NULL OR ciclo = '';

UPDATE programacion_academica
SET anio = YEAR(CURRENT_DATE)
WHERE anio IS NULL;

SET @idx_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'programacion_academica'
      AND index_name = 'uq_prog_salon_periodo'
);

SET @sql := IF(
    @idx_exists = 0,
    'ALTER TABLE programacion_academica ADD UNIQUE KEY uq_prog_salon_periodo (salon_id, dia_semana, hora_inicio, ciclo, anio)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
