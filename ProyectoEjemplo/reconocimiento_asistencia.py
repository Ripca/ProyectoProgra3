import cv2
import face_recognition
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database.models import PersonaDAO, RegistroAccesoDAO

def load_known_faces():
    """Carga los rostros conocidos desde la base de datos."""
    print("Cargando rostros conocidos...")
    personas = PersonaDAO.get_all_encodings()
    known_face_encodings = []
    known_face_names = []
    known_face_ids = []

    for persona in personas:
        if persona['encoding_facial']:
            encoding = np.array(persona['encoding_facial'])
            known_face_encodings.append(encoding)
            known_face_names.append(f"{persona['nombre']} {persona['apellido']}")
            known_face_ids.append(persona['id'])
    
    print(f"Total de rostros cargados: {len(known_face_encodings)}")
    return known_face_encodings, known_face_names, known_face_ids

def main():
    # 1. Start Database Connection & Load Faces
    known_face_encodings, known_face_names, known_face_ids = load_known_faces()

    # 2. Setup Camera (OpenCV)
    video_capture = cv2.VideoCapture(0) # Use 0 for default camera
    
    if not video_capture.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return

    print("Sistema de Reconocimiento Iniciado. Presione 'q' para salir.")

    # Variables for processing frame skipping (optimization)
    process_this_frame = True
    
    while True:
        # 3. Capture frame
        ret, frame = video_capture.read()
        if not ret:
            break

        # Optimization: Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # 4. Detect & Encode Faces
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                name = "Desconocido"
                persona_id = None

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        persona_id = known_face_ids[best_match_index]
                        
                        # 5. Log Attendance (with cooldown)
                        if persona_id:
                            # Check if recently logged
                            last_access = RegistroAccesoDAO.get_recent_by_person(persona_id, minutes=Config.COOLDOWN_MINUTES)
                            
                            if not last_access:
                                # Log new access
                                RegistroAccesoDAO.create(
                                    persona_id=persona_id,
                                    ubicacion="Entrada Principal", # Default location
                                    tipo_acceso="puerta_principal"
                                )
                                print(f"Acceso registrado: {name} a las {datetime.now().strftime('%H:%M:%S')}")
                                
                                # Visual feedback (could be added to frame, but print is safe)

                face_names.append(name)

        process_this_frame = not process_this_frame

        # 6. Display Results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            color = (0, 255, 0) if name != "Desconocido" else (0, 0, 255)
            cv2.rectangle(frame, (top, right), (bottom, left), color, 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Reconocimiento Facial UMG', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
