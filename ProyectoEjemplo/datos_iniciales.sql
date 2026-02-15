-- ==========================================
-- SCRIPT DE DATOS INICIALES (Instrucciones INSERT)
-- ==========================================

USE db_biometrico;

-- 1. INSERTAR ADMINISTRADOR
-- Password: 'admin123'
INSERT INTO personas (nombre, apellido, telefono, email, tipo_persona, codigo_carnet, password_hash)
VALUES 
('Administrador', 'Principal', '5555-0001', 'admin@umg.edu.gt', 'administrativo', 'UMG-ADM-2025-00001', '$2b$12$brhgmd8Fq3ZwVDnqBn1.9ecYohYyZ1xy.4Lbryw6WHOlDxbeXSxSa');

-- 2. INSERTAR CATEDRÁTICOS
-- Password: 'docente123' for all teachers
INSERT INTO personas (nombre, apellido, telefono, email, tipo_persona, codigo_carnet, password_hash)
VALUES 
('Juan', 'Pérez', '5555-1001', 'jperez@umg.edu.gt', 'catedrático', 'UMG-CAT-2025-10001', '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2'),
('Maria', 'González', '5555-1002', 'mgonzalez@umg.edu.gt', 'catedrático', 'UMG-CAT-2025-10002', '$2b$12$W.SwEt/nZ/u1M63pqFKGYeWd3eVjYd.9d3sGGOF8lJdtvEw2Hy5N2');

-- 3. INSERTAR CURSOS
-- Asignados a los catedráticos creados arriba (IDs 2 y 3 asumidos por orden de inserción, ajustar si es necesario)
-- ID 2: Juan Pérez
-- ID 3: Maria González

INSERT INTO cursos (nombre, codigo, horario, salon, catedratico_id)
VALUES 
('Programación I', 'PROG-101', 'Lunes 07:00-09:00', 'A-101', (SELECT id FROM personas WHERE email='jperez@umg.edu.gt')),
('Base de Datos I', 'BD-101', 'Miércoles 09:00-11:00', 'LAB-1', (SELECT id FROM personas WHERE email='jperez@umg.edu.gt')),
('Matemática Discreta', 'MATE-201', 'Martes 07:00-09:00', 'B-202', (SELECT id FROM personas WHERE email='mgonzalez@umg.edu.gt')),
('Física Fundamental', 'FIS-101', 'Jueves 11:00-13:00', 'LAB-FIS', (SELECT id FROM personas WHERE email='mgonzalez@umg.edu.gt'));

-- 4. INSERTAR ESTUDIANTES (Sin datos biométricos aún, para pruebas de inscripción)
-- Estos estudiantes servirán para probar las listas y asistencias.
-- Nota: encoding_facial es NULL. El usuario debe registrarlos "bien" para que tengan rostro, 
-- pero estos sirven para ver datos en la web.

INSERT INTO personas (nombre, apellido, telefono, email, tipo_persona, carrera, seccion, codigo_carnet)
VALUES 
('Estudiante', 'Uno', '5555-2001', 'euno@umg.edu.gt', 'estudiante', 'Ingeniería en Sistemas', 'A', 'UMG-EST-2025-20001'),
('Estudiante', 'Dos', '5555-2002', 'edos@umg.edu.gt', 'estudiante', 'Ingeniería en Sistemas', 'A', 'UMG-EST-2025-20002'),
('Estudiante', 'Tres', '5555-2003', 'etres@umg.edu.gt', 'estudiante', 'Ingeniería en Sistemas', 'B', 'UMG-EST-2025-20003'),
('Estudiante', 'Cuatro', '5555-2004', 'ecuatro@umg.edu.gt', 'estudiante', 'Arquitectura', 'A', 'UMG-EST-2025-20004'),
('Estudiante', 'Cinco', '5555-2005', 'ecinco@umg.edu.gt', 'estudiante', 'Derecho', 'C', 'UMG-EST-2025-20005');

-- 5. INSERTAR INSCRIPCIONES
-- Inscribir estudiantes a cursos

-- Programación I (Juan Pérez)
INSERT INTO inscripciones (estudiante_id, curso_id) VALUES 
((SELECT id FROM personas WHERE email='euno@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='PROG-101')),
((SELECT id FROM personas WHERE email='edos@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='PROG-101')),
((SELECT id FROM personas WHERE email='etres@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='PROG-101'));

-- Base de Datos I (Juan Pérez)
INSERT INTO inscripciones (estudiante_id, curso_id) VALUES 
((SELECT id FROM personas WHERE email='euno@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='BD-101')),
((SELECT id FROM personas WHERE email='ecuatro@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='BD-101'));

-- Matemática Discreta (Maria González)
INSERT INTO inscripciones (estudiante_id, curso_id) VALUES 
((SELECT id FROM personas WHERE email='edos@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='MATE-201')),
((SELECT id FROM personas WHERE email='ecinco@umg.edu.gt'), (SELECT id FROM cursos WHERE codigo='MATE-201'));

-- 6. INSERTAR REGISTROS DE ACCESO (Simulados)
-- Para que se vea actividad en el dashboard

INSERT INTO registros_acceso (persona_id, ubicacion, tipo_acceso, salon) VALUES
((SELECT id FROM personas WHERE email='jperez@umg.edu.gt'), 'Entrada Principal', 'puerta_principal', NULL),
((SELECT id FROM personas WHERE email='euno@umg.edu.gt'), 'Entrada Principal', 'puerta_principal', NULL),
((SELECT id FROM personas WHERE email='euno@umg.edu.gt'), 'Laboratorio 1', 'salon', 'LAB-1');

