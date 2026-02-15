"""
Configuration management for UMG Biometric System
Loads settings from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Database Configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'admin'),
        'database': os.getenv('DB_NAME', 'db_biometrico'),
        'charset': 'utf8mb4',
        'autocommit': False
    }
    
    # Email Configuration
    SMTP_CONFIG = {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'user': os.getenv('SMTP_USER', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'from_email': os.getenv('EMAIL_FROM', 'noreply@umg.edu.gt')
    }
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # Directory Paths
    OUTPUT_DIR = BASE_DIR / os.getenv('OUTPUT_DIR', 'output')
    PHOTOS_DIR = BASE_DIR / os.getenv('PHOTOS_DIR', 'output/photos')
    IDS_DIR = BASE_DIR / os.getenv('IDS_DIR', 'output/ids')
    REPORTS_DIR = BASE_DIR / os.getenv('REPORTS_DIR', 'output/reports')
    TEMP_DIR = BASE_DIR / os.getenv('TEMP_DIR', 'output/temp')
    ASSETS_DIR = BASE_DIR / 'assets'
    
    # Recognition Settings
    FACE_RECOGNITION_TOLERANCE = float(os.getenv('FACE_RECOGNITION_TOLERANCE', 0.6))
    COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', 5))
    PROCESS_EVERY_N_FRAMES = int(os.getenv('PROCESS_EVERY_N_FRAMES', 3))
    
    # UMG Information
    UMG_NAME = "Universidad Mariano Gálvez"
    UMG_SEDE = "Sede Boca del Monte"
    UMG_EMAIL_DOMAIN = "@umg.edu.gt"
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.OUTPUT_DIR,
            cls.PHOTOS_DIR,
            cls.IDS_DIR,
            cls.REPORTS_DIR,
            cls.TEMP_DIR,
            cls.ASSETS_DIR
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        errors = []
        
        # Check database config
        if not cls.DB_CONFIG['password']:
            errors.append("Database password not configured")
        
        # Check email config (warning only)
        if not cls.SMTP_CONFIG['user'] or not cls.SMTP_CONFIG['password']:
            print("WARNING: Email not configured. Email features will be disabled.")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True

# Initialize directories on import
Config.create_directories()
