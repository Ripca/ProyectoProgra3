"""
Main Application Launcher for UMG Biometric System
Provides menu interface to access all system modules
"""
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config import Config
    Config.validate_config()
except Exception as e:
    print(f"ERROR: Configuration error: {e}")
    print("Please check your .env file and configuration settings")
    sys.exit(1)

# Import database manager
from database.db_manager import DatabaseManager


def print_header():
    """Print application header"""
    print("\n" + "="*60)
    print(" "*10 + "SISTEMA DE REGISTRO BIOMÉTRICO UMG")
    print(" "*8 + "Universidad Mariano Gálvez - Boca del Monte")
    print("="*60 + "\n")


def print_menu():
    """Print main menu"""
    print("\n--- MENÚ PRINCIPAL ---")
    print("1. Sistema de Registro de Personas")
    print("2. Control de Acceso - Puerta Principal")
    print("3. Control de Acceso - Salón de Clases")
    print("4. Plataforma Web (Catedráticos)")
    print("5. Utilidades de Base de Datos")
    print("6. Salir")
    print("-" * 30)


def launch_registration():
    """Launch registration GUI"""
    try:
        from modules.registro.registro_gui import launch_registration_gui
        logger.info("Launching registration system...")
        launch_registration_gui()
    except Exception as e:
        logger.error(f"Error launching registration system: {e}")
        print(f"\nError: {e}")
        input("\nPresione Enter para continuar...")


def launch_main_entrance_control():
    """Launch main entrance access control"""
    try:
        from modules.acceso.face_recognition_system import launch_access_control
        logger.info("Launching main entrance access control...")
        print("\nIniciando control de acceso en Puerta Principal...")
        print("Presione 'Q' o 'ESC' para salir")
        print("Presione 'R' para recargar rostros conocidos\n")
        launch_access_control("Puerta Principal", "puerta_principal")
    except Exception as e:
        logger.error(f"Error launching main entrance control: {e}")
        print(f"\nError: {e}")
        input("\nPresione Enter para continuar...")


def launch_classroom_control():
    """Launch classroom access control"""
    try:
        from modules.acceso.face_recognition_system import launch_access_control
        
        print("\nIngrese el número de salón (ej: Salón 101): ", end="")
        salon = input().strip()
        
        if not salon:
            print("Error: Debe ingresar un número de salón")
            input("\nPresione Enter para continuar...")
            return
        
        logger.info(f"Launching classroom access control for {salon}...")
        print(f"\nIniciando control de acceso en {salon}...")
        print("Presione 'Q' o 'ESC' para salir")
        print("Presione 'R' para recargar rostros conocidos\n")
        launch_access_control(salon, "salon", salon)
    except Exception as e:
        logger.error(f"Error launching classroom control: {e}")
        print(f"\nError: {e}")
        input("\nPresione Enter para continuar...")


def launch_web_platform():
    """Launch web platform"""
    try:
        from web.app import run_web_app
        logger.info("Launching web platform...")
        print("\n" + "="*60)
        print("PLATAFORMA WEB - SISTEMA DE ASISTENCIA")
        print("="*60)
        print("\nLa plataforma web se iniciará en: http://localhost:5000")
        print("\nAcceso solo para catedráticos y administrativos")
        print("Presione Ctrl+C para detener el servidor\n")
        print("="*60 + "\n")
        run_web_app(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n\nServidor web detenido")
        input("\nPresione Enter para continuar...")
    except Exception as e:
        logger.error(f"Error launching web platform: {e}")
        print(f"\nError: {e}")
        input("\nPresione Enter para continuar...")


def database_utilities():
    """Database utilities menu"""
    while True:
        print("\n--- UTILIDADES DE BASE DE DATOS ---")
        print("1. Probar Conexión")
        print("2. Ver Estadísticas")
        print("3. Crear Usuario de Prueba (Catedrático)")
        print("4. Volver al Menú Principal")
        print("-" * 35)
        
        choice = input("\nSeleccione una opción: ").strip()
        
        if choice == '1':
            test_database_connection()
        elif choice == '2':
            show_database_stats()
        elif choice == '3':
            create_test_user()
        elif choice == '4':
            break
        else:
            print("Opción inválida")


def test_database_connection():
    """Test database connection"""
    try:
        print("\nProbando conexión a la base de datos...")
        if DatabaseManager.test_connection():
            print("✓ Conexión exitosa!")
            print(f"  Host: {Config.DB_CONFIG['host']}")
            print(f"  Database: {Config.DB_CONFIG['database']}")
        else:
            print("✗ Error en la conexión")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    input("\nPresione Enter para continuar...")


def show_database_stats():
    """Show database statistics"""
    try:
        from database.models import PersonaDAO, CursoDAO, RegistroAccesoDAO, AsistenciaDAO
        
        print("\n--- ESTADÍSTICAS DE LA BASE DE DATOS ---")
        
        # Count persons by type
        personas = PersonaDAO.get_all()
        estudiantes = [p for p in personas if p['tipo_persona'] == 'estudiante']
        catedraticos = [p for p in personas if p['tipo_persona'] == 'catedrático']
        
        print(f"\nPersonas Registradas:")
        print(f"  Total: {len(personas)}")
        print(f"  Estudiantes: {len(estudiantes)}")
        print(f"  Catedráticos: {len(catedraticos)}")
        
        # Count courses
        cursos = CursoDAO.get_all()
        print(f"\nCursos: {len(cursos)}")
        
        # Count access logs today
        from datetime import date
        accesos_hoy = RegistroAccesoDAO.get_by_date_and_location(date.today())
        print(f"\nAccesos Hoy: {len(accesos_hoy)}")
        
        print("\n" + "-" * 40)
        
    except Exception as e:
        print(f"\nError obteniendo estadísticas: {e}")
    
    input("\nPresione Enter para continuar...")


def create_test_user():
    """Create a test professor user"""
    try:
        from database.models import PersonaDAO
        from utils.helpers import hash_password, generate_codigo_carnet
        
        print("\n--- CREAR USUARIO DE PRUEBA (CATEDRÁTICO) ---")
        
        nombre = input("Nombre: ").strip()
        apellido = input("Apellido: ").strip()
        email = input("Email (@umg.edu.gt): ").strip()
        password = input("Contraseña: ").strip()
        
        if not all([nombre, apellido, email, password]):
            print("\nError: Todos los campos son obligatorios")
            input("\nPresione Enter para continuar...")
            return
        
        if not email.endswith('@umg.edu.gt'):
            print("\nError: El email debe terminar en @umg.edu.gt")
            input("\nPresione Enter para continuar...")
            return
        
        # Check if email exists
        existing = PersonaDAO.get_by_email(email)
        if existing:
            print(f"\nError: El email {email} ya está registrado")
            input("\nPresione Enter para continuar...")
            return
        
        # Create user
        codigo_carnet = generate_codigo_carnet('catedrático')
        password_hash = hash_password(password)
        
        persona_id = PersonaDAO.create(
            nombre=nombre,
            apellido=apellido,
            telefono=None,
            email=email,
            tipo_persona='catedrático',
            carrera=None,
            seccion=None,
            foto_path=None,
            encoding_facial=None,
            codigo_carnet=codigo_carnet,
            password_hash=password_hash
        )
        
        print(f"\n✓ Usuario creado exitosamente!")
        print(f"  ID: {persona_id}")
        print(f"  Carnet: {codigo_carnet}")
        print(f"  Email: {email}")
        print(f"\nPuede usar este usuario para acceder a la plataforma web")
        
    except Exception as e:
        print(f"\nError creando usuario: {e}")
    
    input("\nPresione Enter para continuar...")


def main():
    """Main application loop"""
    print_header()
    
    # Test database connection on startup
    print("Verificando conexión a base de datos...")
    if not DatabaseManager.test_connection():
        print("\n✗ ERROR: No se pudo conectar a la base de datos")
        print("Por favor verifique:")
        print("  - MySQL está ejecutándose")
        print("  - Las credenciales en .env son correctas")
        print("  - La base de datos 'db_biometrico' existe")
        input("\nPresione Enter para salir...")
        sys.exit(1)
    
    print("✓ Conexión a base de datos exitosa\n")
    
    while True:
        print_menu()
        choice = input("Seleccione una opción: ").strip()
        
        if choice == '1':
            launch_registration()
        elif choice == '2':
            launch_main_entrance_control()
        elif choice == '3':
            launch_classroom_control()
        elif choice == '4':
            launch_web_platform()
        elif choice == '5':
            database_utilities()
        elif choice == '6':
            print("\n¡Hasta luego!")
            sys.exit(0)
        else:
            print("\nOpción inválida. Por favor seleccione 1-6")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"\nError fatal: {e}")
        input("\nPresione Enter para salir...")
        sys.exit(1)
