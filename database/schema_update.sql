-- ==========================================
-- SCRIPT DE ACTUALIZACIÓN DE ESTRUCTURA
-- SISTEMA BIOMÉTRICO UMG - MEJORA DE ASIGNACIONES
-- ==========================================

USE db_biometrico;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Crear tabla de Salones (si no existe o para formalizarla)
CREATE TABLE IF NOT EXISTS salones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(100),
    ubicacion VARCHAR(100), -- Edificio/Nivel
    activo BOOLEAN DEFAULT TRUE
);

-- 2. Insertar algunos salones de ejemplo
INSERT IGNORE INTO salones (codigo, nombre, ubicacion) VALUES 
('BM-101', 'Salón 101 - Nivel 1', 'Edificio A'),
('BM-102', 'Salón 102 - Nivel 1', 'Edificio A'),
('BM-201', 'Salón 201 - Nivel 2', 'Edificio A'),
('BM-202', 'Salón 202 - Nivel 2', 'Edificio A'),
('LAB-01', 'Laboratorio de Cómputo 1', 'Edificio B');

-- 3. Modificar tabla de Cursos para usar salon_id y mejorar horarios
-- Primero agregamos la columna si no existe
ALTER TABLE cursos ADD COLUMN IF NOT EXISTS salon_id INT AFTER salon;
ALTER TABLE cursos ADD COLUMN IF NOT EXISTS descripcion TEXT AFTER codigo;

-- 4. Actualizar cursos existentes para que apunten a un salón válido (opcional/limpieza)
UPDATE cursos SET salon_id = 1 WHERE salon_id IS NULL;

-- 5. Crear la llave foránea para salones
ALTER TABLE cursos ADD FOREIGN KEY (salon_id) REFERENCES salones(id) ON DELETE SET NULL;

-- 6. Limpieza: Si prefieres usar solo salon_id, podríamos eliminar la columna 'salon' (texto)
-- ALTER TABLE cursos DROP COLUMN salon;

SET FOREIGN_KEY_CHECKS = 1;

-- Ejemplo de consulta para verificar la nueva estructura:
-- SELECT c.nombre, c.horario, s.codigo as salon, p.nombre as catedratico 
-- FROM cursos c 
-- JOIN salones s ON c.salon_id = s.id 
-- JOIN personas p ON c.catedratico_id = p.id;
