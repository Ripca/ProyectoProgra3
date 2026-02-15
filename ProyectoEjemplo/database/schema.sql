-- Create Database
CREATE DATABASE IF NOT EXISTS db_biometrico;
USE db_biometrico;

-- Table for People (Students, Teachers, etc.)
CREATE TABLE IF NOT EXISTS personas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    tipo_persona ENUM('estudiante', 'catedrático', 'administrativo', 'operativo') NOT NULL,
    carrera VARCHAR(100),
    seccion VARCHAR(50),
    foto_path VARCHAR(255),
    encoding_facial JSON, -- Store the 128-d encoding as a JSON array
    codigo_carnet VARCHAR(50) UNIQUE NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restriccion_ingreso BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255) -- For teachers and admins
);

-- Table for Courses
CREATE TABLE IF NOT EXISTS cursos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    horario VARCHAR(100),
    salon VARCHAR(20),
    catedratico_id INT,
    FOREIGN KEY (catedratico_id) REFERENCES personas(id) ON DELETE SET NULL
);

-- Table for Course Enrollments
CREATE TABLE IF NOT EXISTS inscripciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    estudiante_id INT NOT NULL,
    curso_id INT NOT NULL,
    FOREIGN KEY (estudiante_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE
);

-- Table for Raw Access Logs (from cameras)
CREATE TABLE IF NOT EXISTS registros_acceso (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ubicacion VARCHAR(50), -- e.g., 'Puerta Principal', 'Salón 101'
    tipo_acceso ENUM('puerta_principal', 'salon') NOT NULL,
    salon VARCHAR(20),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
);

-- Table for Confirmed Attendance
CREATE TABLE IF NOT EXISTS asistencias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    estudiante_id INT NOT NULL,
    curso_id INT NOT NULL,
    fecha DATE NOT NULL,
    presente BOOLEAN DEFAULT FALSE,
    confirmado_por INT,
    fecha_confirmacion TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (estudiante_id) REFERENCES personas(id) ON DELETE CASCADE,
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmado_por) REFERENCES personas(id) ON DELETE SET NULL
);

-- Insert a default admin/teacher for testing if needed
-- INSERT INTO personas (nombre, apellido, email, tipo_persona, codigo_carnet, password_hash) 
-- VALUES ('Admin', 'UMG', 'admin@umg.edu.gt', 'administrativo', 'ADMIN001', 'pbkdf2:sha256:...');
