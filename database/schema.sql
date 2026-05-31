-- Create Database
CREATE DATABASE IF NOT EXISTS db_biometrico;
USE db_biometrico;

-- Table for People (Students, Teachers, Admin)
-- Optimized: Single table with strict 'role' ENUM.
CREATE TABLE IF NOT EXISTS personas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dpi VARCHAR(20) UNIQUE NOT NULL, -- National ID
    telefono VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    -- 'role' is the new standard field. 'tipo_persona' kept for compatibility if needed, but synced.
    role ENUM('admin', 'catedratico', 'estudiante') NOT NULL DEFAULT 'estudiante',
    tipo_persona VARCHAR(50), -- Kept for backward compatibility
    
    -- Biometrics
    foto_path VARCHAR(255),
    encoding_facial JSON, 
    
    -- Access Control
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restriccion_ingreso BOOLEAN DEFAULT FALSE,
    
    -- Auth
    password_hash VARCHAR(255) -- Nullable for students if they don't login
);

-- Relation tables (Normalized)
CREATE TABLE IF NOT EXISTS persona_carnets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL UNIQUE,
    codigo_carnet VARCHAR(50) NOT NULL UNIQUE,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS persona_secciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL UNIQUE,
    seccion_id INT NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS persona_carreras (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL UNIQUE,
    carrera_id INT NOT NULL,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
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
    FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
    UNIQUE(estudiante_id, curso_id) -- Prevent duplicate enrollment
);

-- Table for Raw Access Logs
CREATE TABLE IF NOT EXISTS registros_acceso (
    id INT PRIMARY KEY AUTO_INCREMENT,
    persona_id INT NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ubicacion VARCHAR(50), 
    tipo_acceso ENUM('puerta_principal', 'salon') NOT NULL,
    salon VARCHAR(20),
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
);

-- Table for Confirmed Attendance (Processed from logs or manual)
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
    FOREIGN KEY (confirmado_por) REFERENCES personas(id) ON DELETE SET NULL,
    UNIQUE(estudiante_id, curso_id, fecha) -- Prevent duplicate attendance per day
);
