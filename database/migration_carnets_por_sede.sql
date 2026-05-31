-- Permite manejar un carnet distinto por persona y sede.

SET @default_sede_id := (
    SELECT id FROM sedes WHERE codigo = 'CENTRAL' LIMIT 1
);

SET @has_sede := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND column_name = 'sede_id'
);

SET @sql_add_sede := IF(
    @has_sede = 0,
    'ALTER TABLE persona_carnets ADD COLUMN sede_id INT NULL AFTER persona_id',
    'SELECT 1'
);
PREPARE stmt FROM @sql_add_sede;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE persona_carnets
SET sede_id = @default_sede_id
WHERE sede_id IS NULL;

SET @idx_persona := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND index_name = 'persona_id'
);

SET @fk_persona_old := (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND constraint_name = 'persona_carnets_ibfk_1'
      AND constraint_type = 'FOREIGN KEY'
);

SET @idx_persona_helper := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND index_name = 'idx_persona_carnets_persona'
);

SET @sql_add_helper := IF(
    @idx_persona_helper = 0,
    'ALTER TABLE persona_carnets ADD INDEX idx_persona_carnets_persona (persona_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql_add_helper;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql_drop_fk_old := IF(
    @fk_persona_old > 0,
    'ALTER TABLE persona_carnets DROP FOREIGN KEY persona_carnets_ibfk_1',
    'SELECT 1'
);
PREPARE stmt FROM @sql_drop_fk_old;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql_drop_persona := IF(
    @idx_persona > 0,
    'ALTER TABLE persona_carnets DROP INDEX persona_id',
    'SELECT 1'
);
PREPARE stmt FROM @sql_drop_persona;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_sede := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND index_name = 'uq_persona_carnet_sede'
);

SET @sql_add_idx := IF(
    @idx_sede = 0,
    'ALTER TABLE persona_carnets ADD UNIQUE KEY uq_persona_carnet_sede (persona_id, sede_id)',
    'SELECT 1'
);
PREPARE stmt FROM @sql_add_idx;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE persona_carnets MODIFY COLUMN sede_id INT NOT NULL;

SET @fk_persona := (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND constraint_name = 'fk_persona_carnets_persona'
      AND constraint_type = 'FOREIGN KEY'
);

SET @sql_fk_persona := IF(
    @fk_persona = 0,
    'ALTER TABLE persona_carnets ADD CONSTRAINT fk_persona_carnets_persona FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE',
    'SELECT 1'
);
PREPARE stmt FROM @sql_fk_persona;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @fk_sede := (
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE table_schema = DATABASE()
      AND table_name = 'persona_carnets'
      AND constraint_name = 'fk_persona_carnets_sede'
      AND constraint_type = 'FOREIGN KEY'
);

SET @sql_fk_sede := IF(
    @fk_sede = 0,
    'ALTER TABLE persona_carnets ADD CONSTRAINT fk_persona_carnets_sede FOREIGN KEY (sede_id) REFERENCES sedes(id) ON DELETE CASCADE',
    'SELECT 1'
);
PREPARE stmt FROM @sql_fk_sede;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
