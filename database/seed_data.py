"""
Seed Data Script for UMG Biometric System
Populates the database with realistic test data for demos.
Run: python database/seed_data.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_cursos():
    """Insert additional courses"""
    cursos = [
        ('MAT201', 'Matemática 2'),
        ('MAT301', 'Matemática 3'),
        ('PROG201', 'Programación 2'),
        ('PROG301', 'Programación 3'),
        ('BD101', 'Bases de Datos 1'),
        ('BD201', 'Bases de Datos 2'),
        ('RED101', 'Redes de Computadoras'),
        ('SO101', 'Sistemas Operativos'),
        ('IA101', 'Inteligencia Artificial'),
        ('ING101', 'Ingeniería de Software'),
        ('EST101', 'Estadística 1'),
        ('EST201', 'Estadística 2'),
        ('ADM101', 'Administración 1'),
        ('ADM201', 'Administración 2'),
        ('CON101', 'Contabilidad 1'),
        ('CON201', 'Contabilidad 2'),
        ('DER101', 'Derecho Empresarial'),
        ('ECO101', 'Economía 1'),
        ('ECO201', 'Microeconomía'),
        ('PSI101', 'Psicología General'),
        ('PSI201', 'Psicología Social'),
        ('PSI301', 'Psicología Clínica'),
        ('AUD101', 'Auditoría 1'),
        ('AUD201', 'Auditoría 2'),
        ('FIL101', 'Filosofía'),
        ('SOC101', 'Sociología'),
        ('INV101', 'Investigación 1'),
        ('INV201', 'Investigación 2'),
        ('COM101', 'Comunicacion Oral y Escrita'),
        ('ETI101', 'Etica Profesional'),
        ('MER101', 'Mercadotecnia 1'),
        ('MER201', 'Mercadotecnia 2'),
        ('FIN101', 'Finanzas 1'),
        ('FIN201', 'Finanzas 2'),
        ('RRHH101', 'Administracion de Recursos Humanos'),
        ('LOG101', 'Logistica Empresarial'),
        ('WEB101', 'Desarrollo Web'),
        ('MOV101', 'Desarrollo de Aplicaciones Moviles'),
        ('SEC101', 'Seguridad Informatica'),
        ('ARQ101', 'Arquitectura de Computadoras'),
    ]
    count = 0
    for codigo, nombre in cursos:
        try:
            DatabaseManager.execute_insert(
                "INSERT IGNORE INTO cursos (codigo, nombre) VALUES (%s, %s)",
                (codigo, nombre)
            )
            count += 1
        except Exception as e:
            if '1062' not in str(e):
                logger.warning(f"  Skip curso {codigo}: {e}")
    logger.info(f"  Inserted {count} cursos")


def seed_salones():
    """Insert additional salones"""
    salones = [
        (1, 'BM-103', 'Salón 103', 'Primer Nivel'),
        (1, 'BM-202', 'Salón 202', 'Segundo Nivel'),
        (1, 'BM-203', 'Salón 203', 'Segundo Nivel'),
        (1, 'BM-302', 'Salón 302', 'Tercer Nivel'),
        (1, 'BM-303', 'Salón 303', 'Tercer Nivel'),
        (1, 'LAB-02', 'Laboratorio Redes', 'Edificio B'),
        (1, 'AUD-01', 'Auditorio Principal', 'Edificio C'),
    ]
    count = 0
    for sede_id, codigo, nombre, ubicacion in salones:
        try:
            DatabaseManager.execute_insert(
                "INSERT IGNORE INTO salones (sede_id, codigo, nombre, ubicacion) VALUES (%s, %s, %s, %s)",
                (sede_id, codigo, nombre, ubicacion)
            )
            count += 1
        except Exception as e:
            if '1062' not in str(e):
                logger.warning(f"  Skip salon {codigo}: {e}")
    logger.info(f"  Inserted {count} salones")


def seed_catedraticos():
    """Insert demo professors and assign the CATEDRATICO role."""
    DatabaseManager.execute_insert(
        """INSERT IGNORE INTO tipos_persona (nombre, descripcion)
           VALUES ('CATEDRATICO', 'Persona que imparte clases')"""
    )
    tipo_rows = DatabaseManager.execute_query("SELECT id FROM tipos_persona WHERE nombre = 'CATEDRATICO'")
    if not tipo_rows:
        logger.warning("  No se encontró el tipo CATEDRATICO.")
        return

    tipo_id = tipo_rows[0]['id']
    catedraticos = [
        ('Carlos', 'Docente', '55551111', 'carlos.docente@miumg.edu.gt', 'cat123'),
        ('María', 'González', '55552222', 'maria.gonzalez@miumg.edu.gt', 'cat123'),
        ('Luis', 'Ramírez', '55553333', 'luis.ramirez@miumg.edu.gt', 'cat123'),
    ]

    count = 0
    for nombre, apellido, telefono, email, password in catedraticos:
        try:
            DatabaseManager.execute_insert(
                """INSERT INTO personas (nombre, apellido, telefono, email, password_hash, activo)
                   VALUES (%s, %s, %s, %s, %s, 1)
                   ON DUPLICATE KEY UPDATE
                       nombre = VALUES(nombre),
                       apellido = VALUES(apellido),
                       telefono = VALUES(telefono),
                       password_hash = COALESCE(password_hash, VALUES(password_hash)),
                       activo = 1""",
                (nombre, apellido, telefono, email, password)
            )
            persona = DatabaseManager.execute_query("SELECT id FROM personas WHERE email = %s", (email,))
            if persona:
                DatabaseManager.execute_insert(
                    """INSERT INTO persona_roles (persona_id, tipo_persona_id, activo)
                       VALUES (%s, %s, 1)
                       ON DUPLICATE KEY UPDATE activo = 1""",
                    (persona[0]['id'], tipo_id)
                )
                count += 1
        except Exception as e:
            logger.warning(f"  Skip catedrático {email}: {e}")
    logger.info(f"  Inserted/updated {count} catedráticos")


def seed_programacion_academica():
    """Insert varied programacion_academica across jornadas and carreras"""
    jornadas_base = [
        ('Matutina', 'Jornada de la manana'),
        ('Vespertina', 'Jornada de la tarde'),
        ('Nocturna', 'Jornada de la noche'),
        ('Fin de semana', 'Sabados y domingos'),
    ]
    for nombre, descripcion in jornadas_base:
        try:
            DatabaseManager.execute_insert(
                "INSERT IGNORE INTO jornadas (nombre, descripcion) VALUES (%s, %s)",
                (nombre, descripcion)
            )
        except Exception as e:
            if '1062' not in str(e):
                logger.warning(f"  Skip jornada {nombre}: {e}")

    # First, get existing IDs
    catedraticos = DatabaseManager.execute_query(
        "SELECT p.id FROM personas p INNER JOIN persona_roles pr ON p.id = pr.persona_id "
        "INNER JOIN tipos_persona t ON pr.tipo_persona_id = t.id WHERE t.nombre = 'CATEDRATICO'"
    )
    if not catedraticos:
        logger.warning("  No catedráticos found. Skipping programacion_academica.")
        return

    cat_ids = [c['id'] for c in catedraticos]
    
    cursos = DatabaseManager.execute_query("SELECT id, codigo FROM cursos ORDER BY id")
    salones = DatabaseManager.execute_query("SELECT id, codigo FROM salones WHERE activo = 1 ORDER BY id")
    secciones = DatabaseManager.execute_query("SELECT id FROM secciones ORDER BY id")
    carreras = DatabaseManager.execute_query("SELECT id, nombre FROM carreras ORDER BY id")
    
    if not cursos or not salones or not secciones or not carreras:
        logger.warning("  Missing catalog data. Skipping programacion_academica.")
        return

    jornadas = DatabaseManager.execute_query("SELECT id, nombre FROM jornadas WHERE activo = 1")
    jornada_ids = {j['nombre']: j['id'] for j in jornadas}

    horarios_matutina = [('07:00:00', '08:30:00'), ('08:30:00', '10:00:00'), ('10:00:00', '11:30:00')]
    horarios_vespertina = [('13:00:00', '14:30:00'), ('14:30:00', '16:00:00'), ('16:00:00', '17:30:00')]
    horarios_nocturna = [('18:00:00', '19:30:00'), ('19:30:00', '21:00:00'), ('21:00:00', '22:00:00')]
    horarios_fds = [('07:00:00', '09:00:00'), ('09:00:00', '11:00:00'), ('11:00:00', '13:00:00'), ('14:00:00', '16:00:00')]

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    dias_fds = ['Sábado']

    jornada_config = [
        (jornada_ids.get('Matutina'), horarios_matutina, dias),
        (jornada_ids.get('Vespertina'), horarios_vespertina, dias),
        (jornada_ids.get('Nocturna'), horarios_nocturna, dias),
        (jornada_ids.get('Fin de semana'), horarios_fds, dias_fds),
    ]

    count = 0
    curso_idx = 0
    salon_idx = 0

    # Map cursos to carreras roughly
    # SISTEMAS=1, ECONOMIA=2, ADMINISTRACION=3, PSICOLOGIA=4, AUDITORIA=5
    curso_carrera_map = {
        'MAT101': 1, 'MAT201': 1, 'MAT301': 1,
        'PROG101': 1, 'PROG201': 1, 'PROG301': 1,
        'BD101': 1, 'BD201': 1,
        'RED101': 1, 'SO101': 1, 'IA101': 1, 'ING101': 1,
        'FIS101': 1,
        'EST101': 2, 'EST201': 2,
        'ECO101': 2, 'ECO201': 2,
        'ADM101': 3, 'ADM201': 3,
        'CON101': 3, 'CON201': 3,
        'DER101': 3,
        'PSI101': 4, 'PSI201': 4, 'PSI301': 4,
        'AUD101': 5, 'AUD201': 5,
        'FIL101': 1, 'SOC101': 4,
        'INV101': 1, 'INV201': 2,
        'COM101': 3, 'ETI101': 1,
        'MER101': 3, 'MER201': 3,
        'FIN101': 2, 'FIN201': 2,
        'RRHH101': 3, 'LOG101': 3,
        'WEB101': 1, 'MOV101': 1, 'SEC101': 1, 'ARQ101': 1,
    }

    for jornada_id, horarios, dias_list in jornada_config:
        if not jornada_id:
            continue
        for dia in dias_list:
            for horario_idx, (hora_ini, hora_fin) in enumerate(horarios):
                # Pick a course
                curso = cursos[curso_idx % len(cursos)]
                curso_idx += 1

                # Pick carrera based on course
                carrera_id = curso_carrera_map.get(curso['codigo'], carreras[0]['id'])

                # Pick section (rotate A, B)
                seccion_id = secciones[horario_idx % len(secciones)]['id']

                # Pick salon
                salon = salones[salon_idx % len(salones)]
                salon_idx += 1

                # Pick catedratico
                cat_id = cat_ids[curso_idx % len(cat_ids)]

                try:
                    DatabaseManager.execute_insert(
                        """INSERT IGNORE INTO programacion_academica 
                           (curso_id, seccion_id, carrera_id, sede_id, jornada_id, salon_id, 
                            catedratico_id, dia_semana, hora_inicio, hora_fin, ciclo, anio, activo)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)""",
                        (curso['id'], seccion_id, carrera_id, 1, jornada_id, salon['id'],
                         cat_id, dia, hora_ini, hora_fin, '1S', 2026)
                    )
                    count += 1
                except Exception as e:
                    if '1062' not in str(e):
                        logger.warning(f"  Skip prog {curso['codigo']} {dia} {hora_ini}: {e}")

    logger.info(f"  Inserted {count} programaciones académicas")


def _get_or_create_id(table, lookup_column, lookup_value, insert_values):
    row = DatabaseManager.execute_query(
        f"SELECT id FROM {table} WHERE {lookup_column} = %s LIMIT 1",
        (lookup_value,)
    )
    if row:
        return row[0]['id']

    columns = ', '.join(insert_values.keys())
    placeholders = ', '.join(['%s'] * len(insert_values))
    DatabaseManager.execute_insert(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(insert_values.values())
    )
    return DatabaseManager.execute_query(
        f"SELECT id FROM {table} WHERE {lookup_column} = %s LIMIT 1",
        (lookup_value,)
    )[0]['id']


def seed_sedes_y_programaciones_disponibles():
    """Create multi-campus academic schedules ready for professors to claim."""
    tipo_id = _get_or_create_id(
        'tipos_persona',
        'nombre',
        'CATEDRATICO',
        {'nombre': 'CATEDRATICO', 'descripcion': 'Persona que imparte clases'}
    )

    pending_email = 'pendiente.asignar@miumg.edu.gt'
    DatabaseManager.execute_insert(
        """INSERT INTO personas (nombre, apellido, telefono, email, password_hash, activo)
           VALUES ('Pendiente', 'Asignar', NULL, %s, 'pendiente', 1)
           ON DUPLICATE KEY UPDATE activo = 1""",
        (pending_email,)
    )
    pending_id = DatabaseManager.execute_query(
        "SELECT id FROM personas WHERE email = %s",
        (pending_email,)
    )[0]['id']
    DatabaseManager.execute_insert(
        """INSERT INTO persona_roles (persona_id, tipo_persona_id, activo)
           VALUES (%s, %s, 1)
           ON DUPLICATE KEY UPDATE activo = 1""",
        (pending_id, tipo_id)
    )

    sedes = [
        ('NORTE', 'Sede Norte', 'Guatemala', 'Zona Norte'),
        ('SUR', 'Sede Sur', 'Guatemala', 'Villa Nueva'),
        ('OCCIDENTE', 'Sede Occidente', 'Quetzaltenango', 'Quetzaltenango'),
        ('ORIENTE', 'Sede Oriente', 'Chiquimula', 'Chiquimula'),
        ('VIRTUAL', 'Campus Virtual', 'Virtual', 'Modalidad en linea'),
    ]
    sede_ids = {}
    for codigo, nombre, departamento, direccion in sedes:
        sede_ids[codigo] = _get_or_create_id(
            'sedes',
            'codigo',
            codigo,
            {
                'codigo': codigo,
                'nombre': nombre,
                'departamento': departamento,
                'direccion': direccion,
                'activo': 1,
            }
        )

    jornadas = [
        ('Matutina', 'Jornada de la manana'),
        ('Vespertina', 'Jornada de la tarde'),
        ('Nocturna', 'Jornada de la noche'),
        ('Fin de semana', 'Sabados y domingos'),
        ('Virtual', 'Clases en linea'),
    ]
    jornada_ids = {}
    for nombre, descripcion in jornadas:
        jornada_ids[nombre] = _get_or_create_id(
            'jornadas',
            'nombre',
            nombre,
            {'nombre': nombre, 'descripcion': descripcion, 'activo': 1}
        )

    carrera_names = ['SISTEMAS', 'ADMINISTRACION', 'ECONOMIA', 'DERECHO', 'PSICOLOGIA', 'AUDITORIA']
    carrera_ids = {
        nombre: _get_or_create_id('carreras', 'nombre', nombre, {'nombre': nombre})
        for nombre in carrera_names
    }

    seccion_names = ['A', 'B', 'C', 'D', 'E', 'F']
    seccion_ids = {
        nombre: _get_or_create_id('secciones', 'nombre', nombre, {'nombre': nombre})
        for nombre in seccion_names
    }

    cursos = [
        ('MAT201', 'Matematica 2', 'SISTEMAS'),
        ('PROG201', 'Programacion 2', 'SISTEMAS'),
        ('BD201', 'Bases de Datos 2', 'SISTEMAS'),
        ('WEB201', 'Desarrollo Web Avanzado', 'SISTEMAS'),
        ('ADM201', 'Administracion 2', 'ADMINISTRACION'),
        ('MER201', 'Mercadotecnia 2', 'ADMINISTRACION'),
        ('FIN201', 'Finanzas 2', 'ECONOMIA'),
        ('ECO201', 'Microeconomia', 'ECONOMIA'),
        ('DER101', 'Derecho Empresarial', 'DERECHO'),
        ('PSI101', 'Psicologia General', 'PSICOLOGIA'),
        ('AUD101', 'Auditoria 1', 'AUDITORIA'),
        ('CON201', 'Contabilidad 2', 'AUDITORIA'),
    ]
    curso_ids = {}
    curso_carrera = {}
    for codigo, nombre, carrera in cursos:
        curso_ids[codigo] = _get_or_create_id(
            'cursos',
            'codigo',
            codigo,
            {'codigo': codigo, 'nombre': nombre, 'descripcion': f'Curso de {carrera}', 'activo': 1}
        )
        curso_carrera[codigo] = carrera_ids[carrera]

    salon_ids = {}
    for sede_codigo, sede_id in sede_ids.items():
        if sede_codigo == 'VIRTUAL':
            salones = [('VIRT-01', 'Aula Virtual 1', 'Plataforma virtual')]
        else:
            salones = [
                ('A-101', 'Aula 101', 'Primer nivel'),
                ('A-202', 'Aula 202', 'Segundo nivel'),
                ('LAB-01', 'Laboratorio 1', 'Area tecnologica'),
            ]
        for codigo, nombre, ubicacion in salones:
            key = f'{sede_codigo}-{codigo}'
            row = DatabaseManager.execute_query(
                "SELECT id FROM salones WHERE sede_id = %s AND codigo = %s LIMIT 1",
                (sede_id, codigo)
            )
            if row:
                salon_ids[key] = row[0]['id']
                continue
            DatabaseManager.execute_insert(
                """INSERT INTO salones (sede_id, codigo, nombre, ubicacion, activo)
                   VALUES (%s, %s, %s, %s, 1)""",
                (sede_id, codigo, nombre, ubicacion)
            )
            salon_ids[key] = DatabaseManager.execute_query(
                "SELECT id FROM salones WHERE sede_id = %s AND codigo = %s LIMIT 1",
                (sede_id, codigo)
            )[0]['id']

    campus_jornadas = {
        'CENTRAL': ['Matutina', 'Nocturna', 'Vespertina', 'Fin de semana'],
        'NORTE': ['Matutina', 'Nocturna'],
        'SUR': ['Vespertina', 'Nocturna'],
        'OCCIDENTE': ['Matutina', 'Fin de semana'],
        'ORIENTE': ['Vespertina', 'Fin de semana'],
        'VIRTUAL': ['Virtual'],
    }
    horarios = {
        'Matutina': [('07:00:00', '08:30:00'), ('08:30:00', '10:00:00'), ('10:00:00', '11:30:00')],
        'Vespertina': [('13:00:00', '14:30:00'), ('14:30:00', '16:00:00'), ('16:00:00', '17:30:00')],
        'Nocturna': [('18:00:00', '19:30:00'), ('19:30:00', '21:00:00'), ('21:00:00', '22:00:00')],
        'Fin de semana': [('07:00:00', '09:00:00'), ('09:00:00', '11:00:00'), ('14:00:00', '16:00:00')],
        'Virtual': [('18:00:00', '19:30:00'), ('19:30:00', '21:00:00')],
    }
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    used_salon_slots = set()
    existing_slots = DatabaseManager.execute_query(
        """
        SELECT salon_id, dia_semana, TIME_FORMAT(hora_inicio, '%H:%i:%s') as hora_inicio,
               COALESCE(ciclo, '1S') as ciclo, COALESCE(anio, 2026) as anio
        FROM programacion_academica
        WHERE activo = 1
        """
    )
    for slot in existing_slots:
        used_salon_slots.add((
            slot['salon_id'],
            slot['dia_semana'],
            slot['hora_inicio'],
            slot['ciclo'],
            int(slot['anio'])
        ))

    def find_free_slot(salon_id, jornada_name, seed):
        candidates = []
        for day_offset, dia in enumerate(dias):
            for hour_offset, (inicio, fin) in enumerate(horarios[jornada_name]):
                candidates.append((seed + day_offset + hour_offset, dia, inicio, fin))
        for _, dia, inicio, fin in sorted(candidates, key=lambda item: item[0]):
            key = (salon_id, dia, inicio, '1S', 2026)
            if key not in used_salon_slots:
                used_salon_slots.add(key)
                return dia, inicio, fin
        return None, None, None

    count = 0
    curso_codes = list(curso_ids.keys())
    for sede_idx, (sede_codigo, jornada_names) in enumerate(campus_jornadas.items()):
        sede_id = sede_ids[sede_codigo]
        salon_keys = [key for key in salon_ids if key.startswith(f'{sede_codigo}-')]
        for jornada_idx, jornada_name in enumerate(jornada_names):
            for section_idx, section_name in enumerate(['A', 'B', 'C']):
                for offset in range(3):
                    curso_codigo = curso_codes[(sede_idx * 5 + jornada_idx * 3 + section_idx + offset) % len(curso_codes)]
                    salon_id = salon_ids[salon_keys[(section_idx + offset) % len(salon_keys)]]
                    dia, hora_inicio, hora_fin = find_free_slot(
                        salon_id,
                        jornada_name,
                        sede_idx + jornada_idx + section_idx + offset
                    )
                    if not dia:
                        logger.warning(f"  Sin horario libre para {sede_codigo} {jornada_name} salon {salon_id}")
                        continue
                    try:
                        DatabaseManager.execute_insert(
                            """INSERT IGNORE INTO programacion_academica
                               (curso_id, seccion_id, carrera_id, sede_id, jornada_id, salon_id,
                                 catedratico_id, dia_semana, hora_inicio, hora_fin, ciclo, anio, activo)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '1S', 2026, 1)""",
                            (
                                curso_ids[curso_codigo],
                                seccion_ids[section_name],
                                curso_carrera[curso_codigo],
                                sede_id,
                                jornada_ids[jornada_name],
                                salon_id,
                                pending_id,
                                dia,
                                hora_inicio,
                                hora_fin,
                            )
                        )
                        count += 1
                    except Exception as e:
                        if '1062' not in str(e):
                            logger.warning(f"  Skip disponible {sede_codigo} {curso_codigo} {section_name}: {e}")

    logger.info(f"  Inserted/updated {count} programaciones disponibles para tomar")


def run_seed():
    """Run all seed functions"""
    logger.info("=" * 50)
    logger.info("SEED DATA: Iniciando población de datos de prueba")
    logger.info("=" * 50)

    logger.info("\n[1/3] Insertando cursos adicionales...")
    seed_cursos()

    logger.info("\n[2/3] Insertando salones adicionales...")
    seed_salones()

    logger.info("\n[3/4] Insertando catedráticos de prueba...")
    seed_catedraticos()

    logger.info("\n[4/5] Insertando programación académica variada...")
    seed_programacion_academica()

    logger.info("\n[5/5] Insertando sedes y programaciones disponibles...")
    seed_sedes_y_programaciones_disponibles()

    # Summary
    cursos_count = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM cursos")[0]['c']
    salones_count = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM salones")[0]['c']
    prog_count = DatabaseManager.execute_query("SELECT COUNT(*) as c FROM programacion_academica")[0]['c']

    logger.info("\n" + "=" * 50)
    logger.info("SEED DATA COMPLETADO")
    logger.info(f"  Cursos totales:          {cursos_count}")
    logger.info(f"  Salones totales:         {salones_count}")
    logger.info(f"  Programaciones totales:  {prog_count}")
    logger.info("=" * 50)


if __name__ == '__main__':
    run_seed()
