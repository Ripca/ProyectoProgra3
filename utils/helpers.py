"""
Helper utilities for UMG Biometric System
"""
import os
import re
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_email(email, require_umg=True):
    """
    Validate email format
    
    Args:
        email: Email address to validate
        require_umg: If True, require @umg.edu.gt domain
    
    Returns:
        bool: True if valid
    """
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    if require_umg and not email.endswith('@umg.edu.gt'):
        return False
    
    return True


def generate_codigo_carnet(tipo_persona):
    """
    Generate unique carnet code
    Format: UMG-TIPO-YYYY-XXXXX
    
    Args:
        tipo_persona: Type of person (estudiante, catedrático, etc.)
    
    Returns:
        str: Unique carnet code
    """
    from database.models import PersonaDAO
    import random
    
    year = datetime.now().year
    tipo_code = {
        'estudiante': 'EST',
        'catedrático': 'CAT',
        'administrativo': 'ADM',
        'operativo': 'OPE'
    }.get(tipo_persona, 'GEN')
    
    # Generate random 5-digit number
    while True:
        numero = random.randint(10000, 99999)
        codigo = f"UMG-{tipo_code}-{year}-{numero}"
        
        # Check if code already exists
        existing = PersonaDAO.get_by_codigo_carnet(codigo)
        if not existing:
            return codigo


def format_datetime(dt, format_str='%d/%m/%Y %H:%M:%S'):
    """Format datetime object to string"""
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    return str(dt)


def format_date(d, format_str='%d/%m/%Y'):
    """Format date object to string"""
    if isinstance(d, datetime):
        return d.strftime(format_str)
    return str(d)


def ensure_dir(directory):
    """Ensure directory exists, create if not"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory


def safe_filename(filename):
    """
    Convert string to safe filename
    Remove special characters and spaces
    """
    # Remove special characters
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()


def get_file_extension(filename):
    """Get file extension from filename"""
    return Path(filename).suffix


def file_exists(filepath):
    """Check if file exists"""
    return Path(filepath).exists()


def delete_file(filepath):
    """Safely delete a file"""
    try:
        if file_exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted file: {filepath}")
            return True
    except Exception as e:
        logger.error(f"Error deleting file {filepath}: {e}")
    return False


def get_timestamp():
    """Get current timestamp as string"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def parse_date(date_str, format_str='%Y-%m-%d'):
    """Parse date string to date object"""
    try:
        return datetime.strptime(date_str, format_str).date()
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")
        return None


def hash_password(password):
    """Return plain text password instead of hashing"""
    return password


def verify_password(password, hashed):
    """Verify password against plain text"""
    return password == hashed
