-- ==========================================
-- SCRIPT DE DATOS INICIALES (LIMPIEZA Y PROFESORES)
-- ==========================================

USE db_biometrico;

-- 1. LIMPIAR TABLAS (Orden inverso para Foreign Keys)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE asistencias;
TRUNCATE TABLE registros_acceso;
TRUNCATE TABLE inscripciones;
TRUNCATE TABLE cursos;
TRUNCATE TABLE personas;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. INSERTAR ADMINISTRADOR
-- Password: 'admin' (Hash puede variar, usaremos uno genérico o texto plano si el auth lo permite en dev, pero pondremos hash real)
-- Hash para 'admin': $2b$12$brhgmd8Fq3ZwVDnqBn1.9ecYohYyZ1xy.4Lbryw6WHOlDxbeXSxSa (Reciclado del anterior)
INSERT INTO personas (nombre, apellido, dpi, telefono, email, role, tipo_persona, codigo_carnet, password_hash)
VALUES 
('Administrador', 'Sistemas', '1000000000001', '5555-0000', 'admin@umg.edu.gt', 'admin', 'administrativo', 'ADM-001', '$2b$12$brhgmd8Fq3ZwVDnqBn1.9ecYohYyZ1xy.4Lbryw6WHOlDxbeXSxSa');

-- 3. INSERTAR CATEDRÁTICOS (Para Login)
-- Hash para 'docente': $2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2
INSERT INTO personas (nombre, apellido, dpi, telefono, email, role, tipo_persona, codigo_carnet, password_hash)
VALUES 
('Juan', 'Pérez', '2000000000001', '5555-1001', 'jperez@umg.edu.gt', 'catedratico', 'catedrático', 'CAT-101', '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2'),
('Maria', 'González', '3000000000001', '5555-1002', 'mgonzalez@umg.edu.gt', 'catedratico', 'catedrático', 'CAT-102', '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2');

-- 4. INSERTAR CURSOS (Asignados a los catedráticos)
INSERT INTO cursos (nombre, codigo, horario, salon, catedratico_id)
VALUES 
('Programación I', 'PROG-101', 'Lunes 07:00-09:00', 'A-101', (SELECT id FROM personas WHERE email='jperez@umg.edu.gt')),
('Base de Datos I', 'BD-101', 'Miércoles 09:00-11:00', 'LAB-1', (SELECT id FROM personas WHERE email='jperez@umg.edu.gt')),
('Inteligencia Artificial', 'IA-501', 'Viernes 18:00-20:00', 'C-303', (SELECT id FROM personas WHERE email='mgonzalez@umg.edu.gt'));

-- NOTA: NO SE INSERTAN ESTUDIANTES. SE DEBEN REGISTRAR VÍA WEB.
