"""
Camera Capture Module
Handles webcam integration for photo capture
"""
import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CameraCapture:
    """Handles webcam capture functionality"""
    
    def __init__(self, camera_index=0):
        """
        Initialize camera
        
        Args:
            camera_index: Camera device index (0 for default camera)
        """
        self.camera_index = camera_index
        self.cap = None
    
    def initialize(self):
        """
        Initialize camera connection
        
        Returns:
            bool: True if successful
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            logger.info(f"Camera {self.camera_index} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def capture_photo(self, output_path):
        """
        Capture a single photo and save to file
        
        Args:
            output_path: Path to save the captured photo
        
        Returns:
            tuple: (success: bool, message: str, frame: numpy.ndarray or None)
        """
        if self.cap is None or not self.cap.isOpened():
            if not self.initialize():
                return False, "No se pudo inicializar la cámara", None
        
        try:
            # Read frame
            ret, frame = self.cap.read()
            
            if not ret:
                return False, "No se pudo capturar la imagen", None
            
            # Save image
            cv2.imwrite(str(output_path), frame)
            logger.info(f"Photo saved to {output_path}")
            
            return True, "Foto capturada exitosamente", frame
            
        except Exception as e:
            logger.error(f"Error capturing photo: {e}")
            return False, f"Error al capturar foto: {str(e)}", None
    
    def capture_with_preview(self, output_path, window_name="Captura de Foto - Presione ESPACIO para capturar, ESC para cancelar"):
        """
        Show live preview and capture photo on spacebar press
        
        Args:
            output_path: Path to save the captured photo
            window_name: Name of preview window
        
        Returns:
            tuple: (success: bool, message: str, frame: numpy.ndarray or None)
        """
        if self.cap is None or not self.cap.isOpened():
            if not self.initialize():
                return False, "No se pudo inicializar la cámara", None
        
        try:
            logger.info("Starting camera preview. Press SPACE to capture, ESC to cancel")
            
            while True:
                ret, frame = self.cap.read()
                
                if not ret:
                    return False, "Error al leer de la cámara", None
                
                # Add text overlay
                display_frame = frame.copy()
                cv2.putText(display_frame, "ESPACIO: Capturar | ESC: Cancelar", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show preview
                cv2.imshow(window_name, display_frame)
                
                # Wait for key press
                key = cv2.waitKey(1) & 0xFF
                
                # Spacebar - capture
                if key == 32:  # Spacebar
                    cv2.imwrite(str(output_path), frame)
                    logger.info(f"Photo captured and saved to {output_path}")
                    cv2.destroyAllWindows()
                    return True, "Foto capturada exitosamente", frame
                
                # ESC - cancel
                elif key == 27:  # ESC
                    logger.info("Capture cancelled by user")
                    cv2.destroyAllWindows()
                    return False, "Captura cancelada", None
                    
        except Exception as e:
            logger.error(f"Error in camera preview: {e}")
            cv2.destroyAllWindows()
            return False, f"Error: {str(e)}", None
    
    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            cv2.destroyAllWindows()
            logger.info("Camera released")
    
    def __del__(self):
        """Destructor - ensure camera is released"""
        self.release()
    
    @staticmethod
    def is_camera_available(camera_index=0):
        """
        Check if camera is available
        
        Args:
            camera_index: Camera device index
        
        Returns:
            bool: True if camera is available
        """
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                cap.release()
                return True
            return False
        except:
            return False
    
    @staticmethod
    def list_available_cameras(max_test=5):
        """
        List all available cameras
        
        Args:
            max_test: Maximum number of camera indices to test
        
        Returns:
            list: List of available camera indices
        """
        available = []
        for i in range(max_test):
            if CameraCapture.is_camera_available(i):
                available.append(i)
                logger.info(f"Camera {i} is available")
        
        return available
