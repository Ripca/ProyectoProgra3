"""
Facial Encoding Module
Generates 128-dimensional facial encodings using face_recognition library
"""
import face_recognition
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class FaceEncoder:
    """Handles facial encoding generation and validation"""
    
    @staticmethod
    def generate_encoding(image_path):
        """
        Generate facial encoding from image file
        
        Args:
            image_path: Path to image file
        
        Returns:
            numpy.ndarray: 128-dimensional encoding, or None if no face detected
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Detect faces and generate encodings
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                logger.warning(f"No face detected in {image_path}")
                return None
            
            if len(face_locations) > 1:
                logger.warning(f"Multiple faces detected in {image_path}, using first face")
            
            # Generate encoding for first face
            encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(encodings) > 0:
                logger.info(f"Successfully generated encoding from {image_path}")
                return encodings[0]
            else:
                logger.error(f"Failed to generate encoding from {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating encoding: {e}")
            return None
    
    @staticmethod
    def generate_encoding_from_array(image_array):
        """
        Generate facial encoding from numpy array (from OpenCV)
        
        Args:
            image_array: Numpy array of image (BGR format from OpenCV)
        
        Returns:
            numpy.ndarray: 128-dimensional encoding, or None if no face detected
        """
        try:
            # Convert BGR to RGB (OpenCV uses BGR, face_recognition uses RGB)
            import cv2
            rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_image)
            
            if len(face_locations) == 0:
                logger.warning("No face detected in image")
                return None
            
            # Generate encoding
            encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if len(encodings) > 0:
                logger.info("Successfully generated encoding from image array")
                return encodings[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error generating encoding from array: {e}")
            return None
    
    @staticmethod
    def validate_encoding(encoding):
        """
        Validate that encoding is in correct format
        
        Args:
            encoding: Encoding to validate
        
        Returns:
            bool: True if valid
        """
        if encoding is None:
            return False
        
        if not isinstance(encoding, np.ndarray):
            return False
        
        if encoding.shape != (128,):
            logger.error(f"Invalid encoding shape: {encoding.shape}, expected (128,)")
            return False
        
        return True
    
    @staticmethod
    def compare_faces(known_encoding, unknown_encoding, tolerance=0.6):
        """
        Compare two facial encodings
        
        Args:
            known_encoding: Known face encoding
            unknown_encoding: Unknown face encoding to compare
            tolerance: How much distance between faces to consider a match (lower is more strict)
        
        Returns:
            bool: True if faces match
        """
        if not FaceEncoder.validate_encoding(known_encoding) or \
           not FaceEncoder.validate_encoding(unknown_encoding):
            return False
        
        # Calculate face distance
        distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        
        logger.debug(f"Face distance: {distance} (tolerance: {tolerance})")
        
        return distance <= tolerance
    
    @staticmethod
    def detect_face_in_image(image_path):
        """
        Check if image contains exactly one face
        
        Args:
            image_path: Path to image file
        
        Returns:
            tuple: (success: bool, message: str, face_location: tuple or None)
        """
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                return False, "No se detectó ningún rostro en la imagen", None
            
            if len(face_locations) > 1:
                return False, f"Se detectaron {len(face_locations)} rostros. Por favor, capture una foto con solo una persona", None
            
            return True, "Rostro detectado correctamente", face_locations[0]
            
        except Exception as e:
            logger.error(f"Error detecting face: {e}")
            return False, f"Error al procesar la imagen: {str(e)}", None
