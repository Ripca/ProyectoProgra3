"""
Face Recognition System Module
Real-time facial recognition for access control
"""
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import threading
import logging
from config import Config
from database.models import PersonaDAO
from modules.acceso.access_logger import AccessLogger

logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    """Real-time facial recognition system"""
    
    def __init__(self, ubicacion, tipo_acceso, salon=None):
        """
        Initialize recognition system
        
        Args:
            ubicacion: Location description (e.g., "Puerta Principal", "Salón 101")
            tipo_acceso: Type of access ('puerta_principal' or 'salon')
            salon: Classroom number if applicable
        """
        self.ubicacion = ubicacion
        self.tipo_acceso = tipo_acceso
        self.salon = salon
        
        self.known_encodings = []
        self.known_ids = []
        self.known_names = []
        self.restricted_persons = []
        
        self.access_logger = AccessLogger(cooldown_minutes=Config.COOLDOWN_MINUTES)
        
        self.cap = None
        self.running = False
        self.process_this_frame = True
        self.frame_count = 0
        
        # Statistics
        self.total_recognitions = 0
        self.successful_logs = 0
    
    def load_known_faces(self):
        """Load all known face encodings from database"""
        try:
            logger.info("Loading known faces from database...")
            personas = PersonaDAO.get_all_encodings()
            
            self.known_encodings = []
            self.known_ids = []
            self.known_names = []
            self.restricted_persons = []
            
            for persona in personas:
                if persona['encoding_facial']:
                    # Convert JSON list back to numpy array
                    encoding = np.array(persona['encoding_facial'])
                    
                    self.known_encodings.append(encoding)
                    self.known_ids.append(persona['id'])
                    self.known_names.append(f"{persona['nombre']} {persona['apellido']}")
                    
                    if persona['restriccion_ingreso']:
                        self.restricted_persons.append(persona['id'])
            
            logger.info(f"Loaded {len(self.known_encodings)} known faces")
            logger.info(f"Restricted persons: {len(self.restricted_persons)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
            return False
    
    def initialize_camera(self, camera_index=0):
        """
        Initialize camera
        
        Args:
            camera_index: Camera device index
        
        Returns:
            bool: True if successful
        """
        try:
            self.cap = cv2.VideoCapture(camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            logger.info(f"Camera {camera_index} initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def process_frame(self, frame):
        """
        Process a single frame for face recognition
        
        Args:
            frame: Video frame from camera
        
        Returns:
            tuple: (processed_frame, recognized_persons)
        """
        recognized_persons = []
        
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        # Process each detected face
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale back up face locations
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_encodings, 
                face_encoding,
                tolerance=Config.FACE_RECOGNITION_TOLERANCE
            )
            
            name = "Desconocido"
            persona_id = None
            is_restricted = False
            color = (0, 0, 255)  # Red for unknown
            
            # Find best match
            if True in matches:
                face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    persona_id = self.known_ids[best_match_index]
                    name = self.known_names[best_match_index]
                    is_restricted = persona_id in self.restricted_persons
                    
                    if is_restricted:
                        color = (0, 0, 255)  # Red for restricted
                    else:
                        color = (0, 255, 0)  # Green for authorized
                    
                    recognized_persons.append({
                        'id': persona_id,
                        'name': name,
                        'restricted': is_restricted
                    })
                    
                    self.total_recognitions += 1
            
            # Draw rectangle and label
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            font = cv2.FONT_HERSHEY_DUPLEX
            text = f"{name} {'[RESTRINGIDO]' if is_restricted else ''}"
            cv2.putText(frame, text, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
        
        return frame, recognized_persons
    
    def log_recognized_persons(self, recognized_persons):
        """
        Log recognized persons to database
        
        Args:
            recognized_persons: List of recognized person dictionaries
        """
        for person in recognized_persons:
            if person['restricted']:
                logger.warning(f"RESTRICTED PERSON DETECTED: {person['name']}")
                # Could trigger alarm or notification here
                continue
            
            # Log access
            success, message, access_id = self.access_logger.log_access(
                persona_id=person['id'],
                ubicacion=self.ubicacion,
                tipo_acceso=self.tipo_acceso,
                salon=self.salon
            )
            
            if success:
                self.successful_logs += 1
                logger.info(f"Access logged for {person['name']}")
    
    def run(self, window_name=None):
        """
        Run the recognition system
        
        Args:
            window_name: Name for display window (None for default)
        """
        if window_name is None:
            window_name = f"Control de Acceso - {self.ubicacion}"
        
        # Load known faces
        if not self.load_known_faces():
            logger.error("Failed to load known faces")
            return
        
        # Initialize camera
        if not self.initialize_camera():
            logger.error("Failed to initialize camera")
            return
        
        self.running = True
        logger.info(f"Recognition system started at {self.ubicacion}")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.error("Failed to read frame from camera")
                    break
                
                # Process every Nth frame for performance
                self.frame_count += 1
                if self.frame_count % Config.PROCESS_EVERY_N_FRAMES == 0:
                    processed_frame, recognized_persons = self.process_frame(frame)
                    
                    # Log recognized persons
                    if recognized_persons:
                        self.log_recognized_persons(recognized_persons)
                    
                    display_frame = processed_frame
                else:
                    display_frame = frame
                
                # Add info overlay
                self.add_info_overlay(display_frame)
                
                # Display frame
                cv2.imshow(window_name, display_frame)
                
                # Check for quit key
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    logger.info("Quit key pressed")
                    break
                elif key == ord('r'):  # 'r' to reload faces
                    logger.info("Reloading known faces...")
                    self.load_known_faces()
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        finally:
            self.stop()
    
    def add_info_overlay(self, frame):
        """Add information overlay to frame"""
        height, width = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Text information
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, f"Ubicacion: {self.ubicacion}", (10, 20), font, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Rostros conocidos: {len(self.known_encodings)}", (10, 40), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Reconocimientos: {self.total_recognitions} | Registros: {self.successful_logs}", 
                   (10, 60), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Q: Salir | R: Recargar rostros", (10, height - 10), font, 0.5, (255, 255, 0), 1)
    
    def stop(self):
        """Stop the recognition system"""
        self.running = False
        
        if self.cap is not None:
            self.cap.release()
        
        cv2.destroyAllWindows()
        logger.info(f"Recognition system stopped. Stats: {self.total_recognitions} recognitions, {self.successful_logs} logs")


def launch_access_control(ubicacion, tipo_acceso, salon=None):
    """
    Launch access control system
    
    Args:
        ubicacion: Location description
        tipo_acceso: 'puerta_principal' or 'salon'
        salon: Classroom number if applicable
    """
    system = FaceRecognitionSystem(ubicacion, tipo_acceso, salon)
    system.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example: Main entrance
    launch_access_control("Puerta Principal", "puerta_principal")
