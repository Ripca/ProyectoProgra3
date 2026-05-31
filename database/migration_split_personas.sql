-- ==========================================
-- SCRIPT DE MIGRACIÓN: SEPARACIÓN DE DATOS DE PERSONAS
-- SISTEMA BIOMÉTRICO UMG - RECK2
-- ==========================================

USE db_biometrico;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Crear tabla persona_carnets
CREATE TABLE IF NOT EXISTS persona_carnets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL UNIQUE,
    codigo_carnet VARCHAR(50) NOT NULL UNIQUE,
    FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. Crear tabla persona_secciones
CREATE TABLE IF NOT EXISTS persona_secciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL UNIQUE,
    seccion_id INT NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE,
    FOREIGN KEY (seccion_id) REFERENCES secciones (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. Crear tabla persona_carreras
CREATE TABLE IF NOT EXISTS persona_carreras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL UNIQUE,
    carrera_id INT NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE,
    FOREIGN KEY (carrera_id) REFERENCES carreras (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 4. Migrar los datos actuales de personas a las nuevas tablas
INSERT IGNORE INTO persona_carnets (persona_id, codigo_carnet)
SELECT id, codigo_carnet FROM personas WHERE codigo_carnet IS NOT NULL AND codigo_carnet <> '';

INSERT IGNORE INTO persona_secciones (persona_id, seccion_id)
SELECT id, seccion_id FROM personas WHERE seccion_id IS NOT NULL;

INSERT IGNORE INTO persona_carreras (persona_id, carrera_id)
SELECT id, carrera_id FROM personas WHERE carrera_id IS NOT NULL;

-- 5. Eliminar restricciones de llave foránea de la tabla personas
ALTER TABLE personas DROP FOREIGN KEY personas_ibfk_1;
ALTER TABLE personas DROP FOREIGN KEY personas_ibfk_2;

-- 6. Eliminar las columnas obsoletas de la tabla personas
ALTER TABLE personas DROP COLUMN codigo_carnet;
ALTER TABLE personas DROP COLUMN seccion_id;
ALTER TABLE personas DROP COLUMN carrera_id;

SET FOREIGN_KEY_CHECKS = 1;
