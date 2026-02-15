"""
Access Logger Module
Handles logging of access events to database
"""
from datetime import datetime, timedelta
from database.models import RegistroAccesoDAO
import logging

logger = logging.getLogger(__name__)


class AccessLogger:
    """Manages access logging with cooldown mechanism"""
    
    def __init__(self, cooldown_minutes=5):
        """
        Initialize access logger
        
        Args:
            cooldown_minutes: Minutes to wait before logging same person again
        """
        self.cooldown_minutes = cooldown_minutes
        self.recent_accesses = {}  # In-memory cache for performance
    
    def can_log_access(self, persona_id):
        """
        Check if person can be logged (cooldown check)
        
        Args:
            persona_id: ID of person
        
        Returns:
            bool: True if can log, False if in cooldown period
        """
        # Check in-memory cache first
        if persona_id in self.recent_accesses:
            last_access = self.recent_accesses[persona_id]
            time_diff = datetime.now() - last_access
            
            if time_diff.total_seconds() < (self.cooldown_minutes * 60):
                logger.debug(f"Person {persona_id} in cooldown period")
                return False
        
        # Check database for recent access
        recent = RegistroAccesoDAO.get_recent_by_person(persona_id, self.cooldown_minutes)
        
        if recent:
            # Update cache
            self.recent_accesses[persona_id] = recent['fecha_hora']
            logger.debug(f"Person {persona_id} accessed recently at {recent['fecha_hora']}")
            return False
        
        return True
    
    def log_access(self, persona_id, ubicacion, tipo_acceso, salon=None):
        """
        Log an access event
        
        Args:
            persona_id: ID of person
            ubicacion: Location description
            tipo_acceso: Type of access ('puerta_principal' or 'salon')
            salon: Classroom number if applicable
        
        Returns:
            tuple: (success: bool, message: str, access_id: int or None)
        """
        try:
            # Check cooldown
            if not self.can_log_access(persona_id):
                return False, "Persona ya registrada recientemente", None
            
            # Log to database
            access_id = RegistroAccesoDAO.create(
                persona_id=persona_id,
                ubicacion=ubicacion,
                tipo_acceso=tipo_acceso,
                salon=salon
            )
            
            # Update cache
            self.recent_accesses[persona_id] = datetime.now()
            
            logger.info(f"Access logged: Person {persona_id} at {ubicacion}")
            return True, "Acceso registrado", access_id
            
        except Exception as e:
            logger.error(f"Error logging access: {e}")
            return False, f"Error: {str(e)}", None
    
    def get_today_accesses(self, ubicacion=None, tipo_acceso=None):
        """
        Get today's access logs
        
        Args:
            ubicacion: Filter by location
            tipo_acceso: Filter by access type
        
        Returns:
            list: Access records
        """
        try:
            today = datetime.now().date()
            return RegistroAccesoDAO.get_by_date_and_location(today, ubicacion, tipo_acceso)
        except Exception as e:
            logger.error(f"Error getting today's accesses: {e}")
            return []
    
    def get_salon_accesses(self, salon, fecha=None):
        """
        Get access logs for a specific classroom
        
        Args:
            salon: Classroom number
            fecha: Date (defaults to today)
        
        Returns:
            list: Access records with person information
        """
        try:
            if fecha is None:
                fecha = datetime.now().date()
            
            return RegistroAccesoDAO.get_by_salon_and_date(salon, fecha)
        except Exception as e:
            logger.error(f"Error getting salon accesses: {e}")
            return []
    
    def clear_cache(self):
        """Clear in-memory cache"""
        self.recent_accesses.clear()
        logger.info("Access cache cleared")
