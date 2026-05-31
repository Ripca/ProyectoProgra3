-- ==========================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS (ESTRUCTURA FINAL REDISEÑADA)
-- SISTEMA BIOMÉTRICO UMG - RECK2
-- ==========================================

-- 1. Crear Base de Datos
CREATE DATABASE IF NOT EXISTS db_biometrico;
USE db_biometrico;

SET FOREIGN_KEY_CHECKS = 0;

-- 2. Tablas Catálogo (Sedes, Jornadas, Salones, Carreras, Secciones)
DROP TABLE IF EXISTS sedes;
CREATE TABLE sedes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    departamento VARCHAR(100),
    direccion VARCHAR(200),
    activo TINYINT(1) NOT NULL DEFAULT 1
);

DROP TABLE IF EXISTS jornadas;
CREATE TABLE jornadas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(150),
    activo TINYINT(1) NOT NULL DEFAULT 1
);

DROP TABLE IF EXISTS salones;
CREATE TABLE salones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sede_id INT NOT NULL,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(100),
    ubicacion VARCHAR(150),
    capacidad INT DEFAULT 30,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE KEY uq_salon_sede_codigo (sede_id, codigo),
    FOREIGN KEY (sede_id) REFERENCES sedes(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS carreras;
CREATE TABLE carreras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

DROP TABLE IF EXISTS secciones;
CREATE TABLE secciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(10) NOT NULL UNIQUE
);

-- 3. Tabla PERSONAS
DROP TABLE IF EXISTS personas;
CREATE TABLE personas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dpi VARCHAR(20) UNIQUE NOT NULL, 
    telefono VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    role ENUM('admin', 'catedratico', 'estudiante') NOT NULL DEFAULT 'estudiante',
    tipo_persona VARCHAR(50), 
    
    -- Datos Biométricos & Documentos
    foto_path VARCHAR(255),
    firma_path VARCHAR(255), -- Ruta de la firma digital
    encoding_facial JSON, 
    
    -- Control
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_hash VARCHAR(255),
    restriccion_ingreso BOOLEAN DEFAULT FALSE
);

-- 3b. Tablas de Relación de Personas (Normalizadas)
DROP TABLE IF EXISTS persona_carnets;
CREATE TABLE persona_carnets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    sede_id INT NOT NULL,
    codigo_carnet VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_persona_carnet_sede (persona_id, sede_id),
    UNIQUE KEY uq_persona_carnet_codigo (codigo_carnet),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (sede_id) REFERENCES sedes(id) ON DELETE CASCADE
);

-- Nota: Ya no son strictly "UNIQUE" para permitir múltiples carreras/secciones (opcional)
DROP TABLE IF EXISTS persona_secciones;
CREATE TABLE persona_secciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    seccion_id INT NOT NULL,
    UNIQUE KEY uq_persona_seccion (persona_id, seccion_id),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS persona_carreras;
CREATE TABLE persona_carreras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    carrera_id INT NOT NULL,
    UNIQUE KEY uq_persona_carrera (persona_id, carrera_id),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE CASCADE
);

-- 4. Tabla CURSOS (Solo catálogo de cursos)
DROP TABLE IF EXISTS cursos;
CREATE TABLE cursos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE NOT NULL
);

-- 5. Tabla Central: PROGRAMACION ACADEMICA (Horarios e Instancias de Clases)
DROP TABLE IF EXISTS programacion_academica;
CREATE TABLE programacion_academica (
    id INT PRIMARY KEY AUTO_INCREMENT,
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
    ciclo VARCHAR(20) DEFAULT '1S',
    anio INT NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uq_prog_curso_seccion_dia (curso_id, seccion_id, dia_semana, hora_inicio),
    UNIQUE KEY uq_prog_salon_periodo (salon_id, dia_semana, hora_inicio, ciclo, anio),
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
    FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE CASCADE,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE CASCADE,
    FOREIGN KEY (sede_id) REFERENCES sedes(id) ON DELETE CASCADE,
    FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE,
    FOREIGN KEY (salon_id) REFERENCES salones(id) ON DELETE CASCADE,
    FOREIGN KEY (catedratico_id) REFERENCES personas(id) ON DELETE CASCADE
);

-- 6. Tabla INSCRIPCIONES ACADEMICAS (Relación Estudiante <-> Programación)
DROP TABLE IF EXISTS inscripciones_academicas;
CREATE TABLE inscripciones_academicas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL, -- estudiante
    programacion_academica_id INT NOT NULL,
    fecha_inscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('ACTIVO','INACTIVO','RETIRADO') NOT NULL DEFAULT 'ACTIVO',
    
    UNIQUE KEY uq_inscripcion_persona_prog (persona_id, programacion_academica_id),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (programacion_academica_id) REFERENCES programacion_academica(id) ON DELETE CASCADE
);

-- 7. Tabla REGISTROS DE ACCESO (Entrada/Salida física)
DROP TABLE IF EXISTS registros_acceso;
CREATE TABLE registros_acceso (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ubicacion VARCHAR(50), 
    tipo_acceso ENUM('puerta_principal', 'salon') NOT NULL,
    salon_id INT, -- Referencia a salones si aplica
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (salon_id) REFERENCES salones(id) ON DELETE SET NULL
);

-- 8. Tabla SESIONES DE CLASE (Instancia de un día específico de clase)
DROP TABLE IF EXISTS sesiones_clase;
CREATE TABLE sesiones_clase (
    id INT PRIMARY KEY AUTO_INCREMENT,
    programacion_academica_id INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado ENUM('PROGRAMADA','EN_CURSO','FINALIZADA','CANCELADA') NOT NULL DEFAULT 'PROGRAMADA',
    observacion VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uq_sesion_prog_fecha (programacion_academica_id, fecha),
    FOREIGN KEY (programacion_academica_id) REFERENCES programacion_academica(id) ON DELETE CASCADE
);

-- 9. Tabla ASISTENCIAS CLASE (Confirmación de asistencia del estudiante)
DROP TABLE IF EXISTS asistencias_clase;
CREATE TABLE asistencias_clase (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sesion_clase_id INT NOT NULL,
    persona_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('PRESENTE','AUSENTE','TARDE','JUSTIFICADO') NOT NULL DEFAULT 'PRESENTE',
    metodo ENUM('BIOMETRICO','MANUAL') NOT NULL DEFAULT 'BIOMETRICO',
    confirmado_por INT,
    observacion VARCHAR(255),
    
    UNIQUE KEY uq_asistencia_sesion_persona (sesion_clase_id, persona_id),
    FOREIGN KEY (sesion_clase_id) REFERENCES sesiones_clase(id) ON DELETE CASCADE,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmado_por) REFERENCES personas(id) ON DELETE SET NULL
);

-- 10. Datos Iniciales Base
INSERT INTO sedes (codigo, nombre, departamento, direccion) VALUES ('CENTRAL', 'Sede Central', 'Guatemala', 'Ciudad de Guatemala');
INSERT INTO jornadas (nombre, descripcion) VALUES ('Matutina', 'Jornada de la mañana'), ('Vespertina', 'Jornada de la tarde'), ('Nocturna', 'Jornada de la noche');

SET FOREIGN_KEY_CHECKS = 1;
