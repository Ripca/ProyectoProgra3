# Sistema de Registro Biométrico UMG

Sistema completo de control de asistencia mediante reconocimiento facial para la Universidad Mariano Gálvez, Sede Boca del Monte.

## 📋 Características

### Proceso 1: Registro de Personas
- Interfaz gráfica (Tkinter) para registro de estudiantes y catedráticos
- Captura de fotografía con webcam
- Generación automática de encoding facial (128 dimensiones)
- Generación de carnets PDF con código QR
- Envío automático de carnets por email
- Validación de email UMG (@umg.edu.gt)

### Proceso 2 & 3: Control de Acceso
- Reconocimiento facial en tiempo real
- Control de acceso en puerta principal
- Control de acceso en salones de clase
- Sistema de cooldown (5 minutos) para evitar registros duplicados
- Optimización de rendimiento (procesa cada 3 frames)
- Detección de personas con restricción de ingreso

### Proceso 4: Plataforma Web
- Sistema de autenticación para catedráticos
- Visualización de árbol de asistencia
- Confirmación de asistencia por curso
- Generación automática de reportes PDF
- Envío de reportes por email
- Estadísticas de asistencia en tiempo real

## 🚀 Instalación

### 1. Requisitos Previos
- Python 3.9 o superior
- MySQL Server
- Webcam (para captura y reconocimiento)

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nota importante para dlib:**
Si tiene problemas instalando `dlib`, puede necesitar instalar CMake y Visual Studio Build Tools primero.

### 3. Configurar Base de Datos

1. Asegúrese de que MySQL esté ejecutándose
2. Cree la base de datos:

```bash
mysql -u root -p < database/schema.sql
```

O manualmente:
```sql
CREATE DATABASE db_biometrico;
USE db_biometrico;
-- Ejecutar el contenido de database/schema.sql
```

### 4. Configurar Variables de Entorno

Edite el archivo `.env` con sus credenciales:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=admin
DB_NAME=db_biometrico

# Email (opcional - para envío de carnets y reportes)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📖 Uso

### Iniciar el Sistema

```bash
python main.py
```

### Menú Principal

```
1. Sistema de Registro de Personas
   - Registrar nuevos estudiantes y catedráticos
   - Capturar foto y generar encoding facial
   - Generar carnet PDF con QR

2. Control de Acceso - Puerta Principal
   - Reconocimiento facial en entrada principal
   - Registro automático de accesos

3. Control de Acceso - Salón de Clases
   - Reconocimiento facial en salones
   - Registro de asistencia por salón

4. Plataforma Web (Catedráticos)
   - Acceso: http://localhost:5000
   - Login con credenciales UMG
   - Ver y confirmar asistencia

5. Utilidades de Base de Datos
   - Probar conexión
   - Ver estadísticas
   - Crear usuario de prueba
```

## 🎓 Flujo de Trabajo Completo

### 1. Registrar Estudiantes
1. Ejecutar `main.py` → Opción 1
2. Completar formulario de registro
3. Capturar foto con webcam (presionar ESPACIO)
4. Sistema genera carnet PDF y envía por email

### 2. Registrar Catedrático
1. Ejecutar `main.py` → Opción 5 → Opción 3
2. Ingresar datos del catedrático
3. Crear contraseña para acceso web

### 3. Crear Curso e Inscribir Estudiantes
Actualmente se hace directamente en la base de datos:

```sql
-- Crear curso
INSERT INTO cursos (nombre, codigo, horario, salon, catedratico_id)
VALUES ('Programación III', 'PROG3', 'Lunes 7:00-9:00', 'Salón 101', 1);

-- Inscribir estudiantes
INSERT INTO inscripciones (estudiante_id, curso_id)
VALUES (2, 1), (3, 1), (4, 1);
```

### 4. Control de Acceso
1. Ejecutar `main.py` → Opción 3
2. Ingresar número de salón (ej: Salón 101)
3. Los estudiantes se paran frente a la cámara
4. Sistema reconoce y registra automáticamente

### 5. Confirmar Asistencia (Catedrático)
1. Ejecutar `main.py` → Opción 4
2. Abrir navegador: http://localhost:5000
3. Login con email y contraseña
4. Seleccionar curso
5. Ver árbol de asistencia (verde=presente, rojo=ausente)
6. Clic en "Confirmar Asistencia"
7. Se genera PDF y se envía por email

## 📁 Estructura del Proyecto

```
Reckonition/
├── main.py                 # Launcher principal
├── config.py               # Configuración
├── .env                    # Variables de entorno
├── requirements.txt        # Dependencias
│
├── database/
│   ├── schema.sql         # Esquema de BD
│   ├── db_manager.py      # Gestor de conexiones
│   └── models.py          # DAOs (Data Access Objects)
│
├── modules/
│   ├── registro/
│   │   ├── registro_gui.py      # GUI de registro
│   │   ├── camera_capture.py   # Captura de webcam
│   │   ├── face_encoder.py     # Encoding facial
│   │   ├── id_generator.py     # Generación de carnets
│   │   └── email_sender.py     # Envío de emails
│   │
│   └── acceso/
│       ├── face_recognition_system.py  # Reconocimiento en tiempo real
│       └── access_logger.py            # Registro de accesos
│
├── web/
│   ├── app.py                # Aplicación Flask
│   ├── auth.py               # Autenticación
│   ├── attendance_tree.py    # Árbol de asistencia
│   ├── pdf_reports.py        # Generación de PDFs
│   └── templates/            # Plantillas HTML
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       └── asistencia.html
│
├── utils/
│   └── helpers.py           # Funciones auxiliares
│
├── assets/
│   └── logo_umg.png         # Logo UMG
│
└── output/                  # Archivos generados
    ├── photos/             # Fotos de personas
    ├── ids/                # Carnets PDF
    ├── reports/            # Reportes de asistencia
    └── temp/               # Archivos temporales
```

## 🔧 Configuración Avanzada

### Ajustar Tolerancia de Reconocimiento

En `.env`:
```env
FACE_RECOGNITION_TOLERANCE=0.6  # Menor = más estricto (0.4-0.7 recomendado)
```

### Ajustar Cooldown

```env
COOLDOWN_MINUTES=5  # Minutos entre registros de la misma persona
```

### Optimización de Rendimiento

```env
PROCESS_EVERY_N_FRAMES=3  # Procesar cada N frames (mayor = más rápido, menos preciso)
```

## ⚠️ Solución de Problemas

### Error: "No module named 'mysql'"
```bash
pip install mysql-connector-python
```

### Error: "Failed to install dlib"
1. Instalar CMake: https://cmake.org/download/
2. Instalar Visual Studio Build Tools
3. Reintentar: `pip install dlib`

### Error: "No se detectó ninguna cámara"
- Verificar que la webcam esté conectada
- Probar con otra aplicación (ej: Cámara de Windows)
- Cambiar índice de cámara en el código

### Error de conexión a base de datos
- Verificar que MySQL esté ejecutándose
- Verificar credenciales en `.env`
- Verificar que la base de datos `db_biometrico` exista

### Email no se envía
- Verificar credenciales SMTP en `.env`
- Para Gmail, usar "App Password" en lugar de contraseña normal
- El sistema funciona sin email, solo no enviará carnets/reportes

## 📊 Base de Datos

### Tablas Principales

- **personas**: Estudiantes, catedráticos, administrativos
- **cursos**: Información de cursos
- **inscripciones**: Relación estudiante-curso
- **registros_acceso**: Logs de acceso (raw data)
- **asistencias**: Asistencias confirmadas por catedrático

## 🎯 Características Técnicas

- **Reconocimiento Facial**: face_recognition (basado en dlib)
- **Encoding**: 128 dimensiones por rostro
- **Base de Datos**: MySQL con connection pooling
- **Web Framework**: Flask
- **GUI**: Tkinter
- **PDF**: ReportLab
- **QR Codes**: qrcode
- **Email**: SMTP

## 📝 Notas Importantes

1. **Iluminación**: El reconocimiento facial funciona mejor con buena iluminación
2. **Distancia**: La persona debe estar a 0.5-1.5 metros de la cámara
3. **Ángulo**: Mirar directamente a la cámara para mejor reconocimiento
4. **Fotos**: Usar fotos claras, de frente, sin lentes oscuros
5. **Email**: Configurar SMTP es opcional pero recomendado

## 👥 Créditos

Sistema desarrollado para la Universidad Mariano Gálvez, Sede Boca del Monte.
Proyecto Final de Programación III - Mayo 2025

## 📄 Licencia

Este proyecto es para uso académico en la Universidad Mariano Gálvez.
