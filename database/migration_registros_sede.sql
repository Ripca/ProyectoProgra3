-- Add sede_id to access logs so entrance records can be separated by campus.
SET @exist_col := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'registros_acceso'
      AND column_name = 'sede_id'
);
SET @sql_add_col := IF(
    @exist_col = 0,
    'ALTER TABLE registros_acceso ADD COLUMN sede_id INT NULL AFTER persona_id',
    'SELECT 1'
);
PREPARE stmt FROM @sql_add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE registros_acceso
SET sede_id = (SELECT id FROM sedes WHERE codigo = 'CENTRAL' LIMIT 1)
WHERE sede_id IS NULL;

SET @exist_idx := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'registros_acceso'
      AND index_name = 'idx_registros_sede_fecha'
);
SET @sql_add_idx := IF(
    @exist_idx = 0,
    'ALTER TABLE registros_acceso ADD INDEX idx_registros_sede_fecha (sede_id, fecha_hora)',
    'SELECT 1'
);
PREPARE stmt FROM @sql_add_idx;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
