-- Rediseño de Base de Datos - Script de Migración

-- Fase 1: Nuevas Tablas Catálogo
CREATE TABLE IF NOT EXISTS sedes (
    id INT NOT NULL AUTO_INCREMENT,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    departamento VARCHAR(100),
    direccion VARCHAR(200),
    activo TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY uq_sedes_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jornadas (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(150),
    activo TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY uq_jornadas_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar datos iniciales
INSERT IGNORE INTO sedes (codigo, nombre, departamento, direccion) VALUES ('CENTRAL', 'Sede Central Boca del Monte', 'Guatemala', 'Boca del Monte');
INSERT IGNORE INTO jornadas (nombre, descripcion) VALUES ('Matutina', 'Jornada Matutina'), ('Vespertina', 'Jornada Vespertina'), ('Nocturna', 'Jornada Nocturna'), ('Fin de semana', 'Sábados y Domingos');

-- Fase 2: Modificar Tablas Existentes

-- salones
-- Agregar columna sede_id si no existe
SET @exist := (SELECT count(*) FROM information_schema.columns WHERE table_name = 'salones' AND column_name = 'sede_id' AND table_schema = DATABASE());
SET @sql := if(@exist = 0, 'ALTER TABLE salones ADD COLUMN sede_id INT NULL AFTER id', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Asignar sede por defecto a salones existentes
UPDATE salones SET sede_id = (SELECT id FROM sedes WHERE codigo = 'CENTRAL') WHERE sede_id IS NULL;

-- Hacer NOT NULL
ALTER TABLE salones MODIFY COLUMN sede_id INT NOT NULL;

-- Agregar FK si no existe
SET @exist_fk := (SELECT count(*) FROM information_schema.table_constraints WHERE table_name = 'salones' AND constraint_name = 'fk_salones_sede' AND constraint_schema = DATABASE());
SET @sql_fk := if(@exist_fk = 0, 'ALTER TABLE salones ADD CONSTRAINT fk_salones_sede FOREIGN KEY (sede_id) REFERENCES sedes(id)', 'SELECT 1');
PREPARE stmt FROM @sql_fk;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Cambiar UNIQUE de codigo global a codigo por sede
-- Primero intentamos borrar la restricción 'codigo' si existe
SET @exist_idx := (SELECT count(*) FROM information_schema.statistics WHERE table_name = 'salones' AND index_name = 'codigo' AND table_schema = DATABASE());
SET @sql_drop_idx := if(@exist_idx > 0, 'ALTER TABLE salones DROP INDEX codigo', 'SELECT 1');
PREPARE stmt FROM @sql_drop_idx;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @exist_idx2 := (SELECT count(*) FROM information_schema.statistics WHERE table_name = 'salones' AND index_name = 'uq_salon_sede_codigo' AND table_schema = DATABASE());
SET @sql_add_idx := if(@exist_idx2 = 0, 'ALTER TABLE salones ADD UNIQUE KEY uq_salon_sede_codigo (sede_id, codigo)', 'SELECT 1');
PREPARE stmt FROM @sql_add_idx;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- cursos
-- Quitar FK si existen (cursos_ibfk_1 y cursos_ibfk_2 o fk_cursos_salon, fk_cursos_catedratico)
SET @exist_fk_salon := (SELECT count(*) FROM information_schema.table_constraints WHERE table_name = 'cursos' AND constraint_name = 'fk_cursos_salon' AND constraint_schema = DATABASE());
SET @sql_drop_fk_salon := if(@exist_fk_salon > 0, 'ALTER TABLE cursos DROP FOREIGN KEY fk_cursos_salon', 'SELECT 1');
PREPARE stmt FROM @sql_drop_fk_salon; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist_fk_cat := (SELECT count(*) FROM information_schema.table_constraints WHERE table_name = 'cursos' AND constraint_name = 'fk_cursos_catedratico' AND constraint_schema = DATABASE());
SET @sql_drop_fk_cat := if(@exist_fk_cat > 0, 'ALTER TABLE cursos DROP FOREIGN KEY fk_cursos_catedratico', 'SELECT 1');
PREPARE stmt FROM @sql_drop_fk_cat; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist_col := (SELECT count(*) FROM information_schema.columns WHERE table_name = 'cursos' AND column_name = 'salon_id' AND table_schema = DATABASE());
SET @sql_drop_cols := if(@exist_col > 0, 'ALTER TABLE cursos DROP COLUMN salon_id, DROP COLUMN catedratico_id, DROP COLUMN horario', 'SELECT 1');
PREPARE stmt FROM @sql_drop_cols; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- persona_carreras
SET @exist_pc_idx := (SELECT count(*) FROM information_schema.statistics WHERE table_name = 'persona_carreras' AND index_name = 'persona_id' AND table_schema = DATABASE());
SET @sql_drop_pc_idx := if(@exist_pc_idx > 0, 'ALTER TABLE persona_carreras DROP INDEX persona_id', 'SELECT 1');
PREPARE stmt FROM @sql_drop_pc_idx; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist_pc_uq := (SELECT count(*) FROM information_schema.statistics WHERE table_name = 'persona_carreras' AND index_name = 'uq_persona_carrera' AND table_schema = DATABASE());
SET @sql_add_pc_uq := if(@exist_pc_uq = 0, 'ALTER TABLE persona_carreras ADD UNIQUE KEY uq_persona_carrera (persona_id, carrera_id)', 'SELECT 1');
PREPARE stmt FROM @sql_add_pc_uq; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- persona_secciones
SET @exist_ps_idx := (SELECT count(*) FROM information_schema.statistics WHERE table_name = 'persona_secciones' AND index_name = 'persona_id' AND table_schema = DATABASE());
SET @sql_drop_ps_idx := if(@exist_ps_idx > 0, 'ALTER TABLE persona_secciones DROP INDEX persona_id', 'SELECT 1');
PREPARE stmt FROM @sql_drop_ps_idx; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exist_ps_uq := (SELECT count(*) FROM information_schema.statistics WHERE table_name = 'persona_secciones' AND index_name = 'uq_persona_seccion' AND table_schema = DATABASE());
SET @sql_add_ps_uq := if(@exist_ps_uq = 0, 'ALTER TABLE persona_secciones ADD UNIQUE KEY uq_persona_seccion (persona_id, seccion_id)', 'SELECT 1');
PREPARE stmt FROM @sql_add_ps_uq; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Fase 3: Tabla Central
CREATE TABLE IF NOT EXISTS programacion_academica (
    id INT NOT NULL AUTO_INCREMENT,
    curso_id INT NOT NULL,
    seccion_id INT NOT NULL,
    carrera_id INT NOT NULL,
    sede_id INT NOT NULL,
    jornada_id INT NOT NULL,
    salon_id INT NOT NULL,
    catedratico_id INT NOT NULL,
    dia_semana ENUM('Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    ciclo VARCHAR(20) DEFAULT NULL,
    anio INT DEFAULT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_prog_curso_seccion_dia (curso_id, seccion_id, dia_semana, hora_inicio),
    UNIQUE KEY uq_prog_salon_periodo (salon_id, dia_semana, hora_inicio, ciclo, anio),
    
    CONSTRAINT fk_prog_curso FOREIGN KEY (curso_id) REFERENCES cursos(id),
    CONSTRAINT fk_prog_seccion FOREIGN KEY (seccion_id) REFERENCES secciones(id),
    CONSTRAINT fk_prog_carrera FOREIGN KEY (carrera_id) REFERENCES carreras(id),
    CONSTRAINT fk_prog_sede FOREIGN KEY (sede_id) REFERENCES sedes(id),
    CONSTRAINT fk_prog_jornada FOREIGN KEY (jornada_id) REFERENCES jornadas(id),
    CONSTRAINT fk_prog_salon FOREIGN KEY (salon_id) REFERENCES salones(id),
    CONSTRAINT fk_prog_catedratico FOREIGN KEY (catedratico_id) REFERENCES personas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Migrar asignaciones_catedratico a programacion_academica (asumiendo carrera=1, jornada=Nocturna)
-- Se asume carrera=1 (Sistemas), sede=1 (Central), jornada=3 (Nocturna) para datos existentes
INSERT IGNORE INTO programacion_academica (curso_id, seccion_id, carrera_id, sede_id, jornada_id, salon_id, catedratico_id, dia_semana, hora_inicio, hora_fin, anio)
SELECT ac.curso_id, ac.seccion_id, 1, (SELECT id FROM sedes WHERE codigo='CENTRAL'), (SELECT id FROM jornadas WHERE nombre='Nocturna'), ac.salon_id, ac.catedratico_id, ac.dia_semana, ac.hora_inicio, ac.hora_fin, YEAR(CURRENT_DATE)
FROM asignaciones_catedratico ac;

-- Fase 4: Inscripciones Académicas
CREATE TABLE IF NOT EXISTS inscripciones_academicas (
    id INT NOT NULL AUTO_INCREMENT,
    persona_id INT NOT NULL,
    programacion_academica_id INT NOT NULL,
    fecha_inscripcion TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('ACTIVO','INACTIVO','RETIRADO') NOT NULL DEFAULT 'ACTIVO',

    PRIMARY KEY (id),
    UNIQUE KEY uq_inscripcion_persona_prog (persona_id, programacion_academica_id),

    CONSTRAINT fk_inscripcion_persona 
        FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    CONSTRAINT fk_inscripcion_programacion 
        FOREIGN KEY (programacion_academica_id) REFERENCES programacion_academica(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Fase 5: Sesiones y Asistencias
CREATE TABLE IF NOT EXISTS sesiones_clase (
    id INT NOT NULL AUTO_INCREMENT,
    programacion_academica_id INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado ENUM('PROGRAMADA','EN_CURSO','FINALIZADA','CANCELADA') NOT NULL DEFAULT 'PROGRAMADA',
    observacion VARCHAR(255) DEFAULT NULL,
    fecha_creacion TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_sesion_prog_fecha (programacion_academica_id, fecha),

    CONSTRAINT fk_sesion_programacion
        FOREIGN KEY (programacion_academica_id) REFERENCES programacion_academica(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Renombrar asistencias_clase a asistencias_clase_legacy si no se ha hecho
SET @exist_ac := (SELECT count(*) FROM information_schema.tables WHERE table_name = 'asistencias_clase' AND table_schema = DATABASE());
SET @sql_rename_ac := if(@exist_ac > 0 AND (SELECT count(*) FROM information_schema.columns WHERE table_name = 'asistencias_clase' AND column_name = 'sesion_clase_id' AND table_schema = DATABASE()) = 0, 'RENAME TABLE asistencias_clase TO asistencias_clase_legacy', 'SELECT 1');
PREPARE stmt FROM @sql_rename_ac; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS asistencias_clase (
    id INT NOT NULL AUTO_INCREMENT,
    sesion_clase_id INT NOT NULL,
    persona_id INT NOT NULL,
    fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('PRESENTE','AUSENTE','TARDE','JUSTIFICADO') NOT NULL DEFAULT 'PRESENTE',
    metodo ENUM('BIOMETRICO','MANUAL') NOT NULL DEFAULT 'BIOMETRICO',
    confirmado_por INT DEFAULT NULL,
    observacion VARCHAR(255) DEFAULT NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_asistencia_sesion_persona (sesion_clase_id, persona_id),

    CONSTRAINT fk_asistencia_sesion 
        FOREIGN KEY (sesion_clase_id) REFERENCES sesiones_clase(id),
    CONSTRAINT fk_asistencia_persona 
        FOREIGN KEY (persona_id) REFERENCES personas(id),
    CONSTRAINT fk_asistencia_confirmador 
        FOREIGN KEY (confirmado_por) REFERENCES personas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
