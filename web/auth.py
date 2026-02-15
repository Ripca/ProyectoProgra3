"""
Authentication Module for Web Platform
"""
from functools import wraps
from flask import session, redirect, url_for, flash
from database.models import PersonaDAO
from utils.helpers import verify_password
import logging

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def catedratico_required(f):
    """Decorator to require catedrático role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión', 'warning')
            return redirect(url_for('login'))
        
        if session.get('tipo_persona') not in ['catedrático', 'administrativo']:
            flash('Acceso denegado. Solo para catedráticos', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def authenticate_user(email, password):
    """
    Authenticate user credentials
    
    Args:
        email: User email
        password: User password
    
    Returns:
        tuple: (success: bool, user_data: dict or None, message: str)
    """
    try:
        # Get user by email
        user = PersonaDAO.get_by_email(email)
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {email}")
            return False, None, "Email o contraseña incorrectos"
        
        # Check if user has password (only catedráticos and admin should have passwords)
        if not user.get('password_hash'):
            logger.warning(f"Login attempt for user without password: {email}")
            return False, None, "Esta cuenta no tiene acceso al sistema web"
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            logger.warning(f"Failed login attempt for user: {email}")
            return False, None, "Email o contraseña incorrectos"
        
        # Check if user is catedrático or admin
        if user['role'] not in ['catedratico', 'admin'] and user['tipo_persona'] not in ['catedrático', 'administrativo']:
            logger.warning(f"Login attempt by non-catedrático: {email}")
            return False, None, "Solo catedráticos y administrativos pueden acceder"
        
        logger.info(f"Successful login: {email}")
        return True, user, "Login exitoso"
        
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return False, None, "Error en el sistema de autenticación"


def create_session(user_data):
    """
    Create user session
    
    Args:
        user_data: User data dictionary
    """
    session['user_id'] = user_data['id']
    session['nombre'] = user_data['nombre']
    session['apellido'] = user_data['apellido']
    session['email'] = user_data['email']
    session['tipo_persona'] = user_data['tipo_persona']
    session['role'] = user_data.get('role', user_data['tipo_persona']) # Fallback
    session['codigo_carnet'] = user_data['codigo_carnet']
    
    logger.info(f"Session created for user: {user_data['email']}")


def destroy_session():
    """Destroy user session"""
    user_email = session.get('email', 'Unknown')
    session.clear()
    logger.info(f"Session destroyed for user: {user_email}")


def get_current_user():
    """
    Get current logged-in user data
    
    Returns:
        dict or None: User data if logged in
    """
    if 'user_id' not in session:
        return None
    
    try:
        user = PersonaDAO.get_by_id(session['user_id'])
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None
