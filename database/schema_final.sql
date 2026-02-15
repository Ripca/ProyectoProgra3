-- ==========================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS (ESTRUCTURA FINAL)
-- SISTEMA BIOMÉTRICO UMG - RECK2
-- ==========================================

-- 1. Crear Base de Datos
CREATE DATABASE IF NOT EXISTS db_biometrico;
USE db_biometrico;

SET FOREIGN_KEY_CHECKS = 0;

-- 2. Tablas Catalogo (Carreras, Secciones)
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
    
    -- Datos de Estudiante (FKs)
    carrera_id INT,
    seccion_id INT,
    codigo_carnet VARCHAR(50) UNIQUE, 
    
    -- Datos Biométricos & Documentos
    foto_path VARCHAR(255),
    firma_path VARCHAR(255), -- Ruta de la firma digital
    encoding_facial JSON, 
    
    -- Control
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    password_hash VARCHAR(255),
    restriccion_ingreso BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE SET NULL,
    FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE SET NULL
);

-- 4. Tabla CURSOS
DROP TABLE IF EXISTS cursos;
CREATE TABLE cursos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    horario VARCHAR(100),
    salon VARCHAR(20),
    catedratico_id INT,
    FOREIGN KEY (catedratico_id) REFERENCES personas(id) ON DELETE SET NULL
);

-- 5. Tabla INSCRIPCIONES
DROP TABLE IF EXISTS inscripciones;
CREATE TABLE inscripciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    estudiante_id INT NOT NULL,
    curso_id INT NOT NULL,
    FOREIGN KEY (estudiante_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
    UNIQUE(estudiante_id, curso_id) 
);

-- 6. Tabla REGISTROS DE ACCESO
DROP TABLE IF EXISTS registros_acceso;
CREATE TABLE registros_acceso (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ubicacion VARCHAR(50), 
    tipo_acceso ENUM('puerta_principal', 'salon') NOT NULL,
    salon VARCHAR(20),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
);

-- 7. Tabla ASISTENCIAS (Confirmadas)
DROP TABLE IF EXISTS asistencias;
CREATE TABLE asistencias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    estudiante_id INT NOT NULL,
    curso_id INT NOT NULL,
    fecha DATE NOT NULL,
    presente BOOLEAN DEFAULT FALSE,
    confirmado_por INT,
    fecha_confirmacion TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (estudiante_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmado_por) REFERENCES personas(id) ON DELETE SET NULL,
    UNIQUE(estudiante_id, curso_id, fecha) 
);

SET FOREIGN_KEY_CHECKS = 1;
