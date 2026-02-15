-- ==========================================
-- SCRIPT DE DATOS INICIALES (FINAL + CATALOGOS)
-- ==========================================

USE db_biometrico;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE asistencias;
TRUNCATE TABLE registros_acceso;
TRUNCATE TABLE inscripciones;
TRUNCATE TABLE cursos;
TRUNCATE TABLE personas;
TRUNCATE TABLE carreras;
TRUNCATE TABLE secciones;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. CATALOGOS
INSERT INTO carreras (nombre) VALUES 
('Ingeniería en Sistemas'),
('Arquitectura'),
('Derecho'),
('Psicología'),
('Administración de Empresas');

INSERT INTO secciones (nombre) VALUES ('A'), ('B'), ('C'), ('D');

-- 2. ADMINISTRADOR
INSERT INTO personas (nombre, apellido, dpi, telefono, email, role, tipo_persona, codigo_carnet, password_hash)
VALUES 
('Administrador', 'Sistemas', '1001', '5555-0000', 'admin@umg.edu.gt', 'admin', 'administrativo', 'ADM-001', '$2b$12$brhgmd8Fq3ZwVDnqBn1.9ecYohYyZ1xy.4Lbryw6WHOlDxbeXSxSa');

-- 3. CATEDRÁTICOS
INSERT INTO personas (nombre, apellido, dpi, telefono, email, role, tipo_persona, codigo_carnet, password_hash)
VALUES 
('Juan', 'Pérez', '2001', '5555-1001', 'jperez@umg.edu.gt', 'catedratico', 'catedrático', 'CAT-101', '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2'),
('Maria', 'González', '3001', '5555-1002', 'mgonzalez@umg.edu.gt', 'catedratico', 'catedrático', 'CAT-102', '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2');

-- 4. CURSOS
INSERT INTO cursos (nombre, codigo, horario, salon, catedratico_id)
VALUES 
('Programación I', 'PROG-101', 'Lunes 07:00-09:00', 'A-101', (SELECT id FROM personas WHERE email='jperez@umg.edu.gt')),
('Base de Datos I', 'BD-101', 'Miércoles 09:00-11:00', 'LAB-1', (SELECT id FROM personas WHERE email='jperez@umg.edu.gt')),
('Inteligencia Artificial', 'IA-501', 'Viernes 18:00-20:00', 'C-303', (SELECT id FROM personas WHERE email='mgonzalez@umg.edu.gt'));
