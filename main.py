import cv2
import face_recognition
import numpy as np
import sys
import os
from datetime import datetime

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database.models import PersonaDAO, RegistroAccesoDAO, CursoDAO

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_known_faces():
    """Carga los rostros conocidos desde la base de datos."""
    print("⏳ Cargando rostros conocidos...")
    try:
        personas = PersonaDAO.get_all_encodings()
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        return [], [], []

    known_face_encodings = []
    known_face_names = []
    known_face_ids = []

    for persona in personas:
        if persona['encoding_facial']:
            try:
                # Handle both list and numpy array formats
                encoding = np.array(persona['encoding_facial'])
                known_face_encodings.append(encoding)
                known_face_names.append(f"{persona['nombre']} {persona['apellido']}")
                known_face_ids.append(persona['id'])
            except Exception as e:
                print(f"⚠️ Error procesando encoding para {persona.get('nombre')}: {e}")
    
    print(f"✅ Total de rostros cargados: {len(known_face_encodings)}")
    return known_face_encodings, known_face_names, known_face_ids

def show_menu():
    print("\n" + "="*40)
    print(" SISTEMA DE ASISTENCIA BIOMÉTRICO UMG ")
    print("="*40)
    print("1. Iniciar Control de Asistencia (General)")
    print("2. Iniciar Control de Clase (Por Curso)")
    print("3. Salir")
    print("="*40)
    return input("Seleccione una opción: ")

def select_course():
    print("\n--- Seleccionar Curso ---")
    cursos = CursoDAO.get_all()
    if not cursos:
        print("❌ No hay cursos registrados.")
        return None
    
    for i, curso in enumerate(cursos, 1):
        prof = f" ({curso['catedratico_nombre']} {curso['catedratico_apellido']})" if curso['catedratico_nombre'] else ""
        print(f"{i}. {curso['nombre']} [{curso['codigo']}]{prof}")
    
    try:
        idx = int(input("\nIngrese el número del curso: ")) - 1
        if 0 <= idx < len(cursos):
            return cursos[idx]
        else:
            print("❌ Opción inválida.")
            return None
    except ValueError:
        print("❌ Entrada inválida.")
        return None

def start_recognition(course_data=None):
    # 1. Start Database Connection & Load Faces
    known_face_encodings, known_face_names, known_face_ids = load_known_faces()

    location_name = "Entrada Principal"
    if course_data:
        location_name = f"Salón {course_data['salon']} - {course_data['nombre']}"
        print(f"\n🚀 Iniciando control para: {course_data['nombre']}")
    else:
        print(f"\n🚀 Iniciando control GENERAL")

    # 2. Setup Camera
    print("📷 Abriendo cámara...")
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    
    if not video_capture.isOpened():
        print("⚠️ Cámara 0 falló. Intentando cámara 1...")
        video_capture = cv2.VideoCapture(1)
        if not video_capture.isOpened():
             print("❌ Error: No se pudo abrir ninguna cámara.")
             input("Presione Enter para volver...")
             return

    # 3. Setup Haar Cascade
    cascade_path = 'haarcascade_frontalface_default.xml'
    if not os.path.exists(cascade_path):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    
    face_cascade = cv2.CascadeClassifier(cascade_path)
    use_haar = not face_cascade.empty()
    if use_haar:
        print(f"✅ Usando Haar Cascade para detección.")
    
    print("\n🟢 SISTEMA ACTIVO. Presione 'q' para detener y volver al menú.")

    process_this_frame = True
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("❌ Error de video.")
            break

        # Resize for speed
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        gray_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        if process_this_frame:
            face_locations = []
            
            if use_haar:
                faces = face_cascade.detectMultiScale(gray_small_frame, 1.1, 5, minSize=(30, 30))
                for (x, y, w, h) in faces:
                    face_locations.append((y, x + w, y + h, x))
            else:
                face_locations = face_recognition.face_locations(rgb_small_frame)

            if face_locations:
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            else:
                face_encodings = []

            face_names = []
            
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=Config.FACE_RECOGNITION_TOLERANCE)
                name = "Desconocido"
                persona_id = None

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                        persona_id = known_face_ids[best_match_index]
                        
                        # Log Attendance
                        if persona_id:
                            try:
                                last_access = RegistroAccesoDAO.get_recent_by_person(persona_id, minutes=Config.COOLDOWN_MINUTES)
                                if not last_access:
                                    # Determinar tipo y salón
                                    tipo = "salon" if course_data else "puerta_principal"
                                    salon = course_data['salon'] if course_data else None
                                    
                                    RegistroAccesoDAO.create(
                                        persona_id=persona_id,
                                        ubicacion=location_name,
                                        tipo_acceso=tipo,
                                        salon=salon
                                    )
                                    print(f"✅ ASISTENCIA: {name} -> {location_name}")
                            except Exception:
                                pass 

                face_names.append(name)

        process_this_frame = not process_this_frame

        # Display
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2
            color = (0, 255, 0) if name != "Desconocido" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

        # Overlay Info
        cv2.putText(frame, f"MODO: {location_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow('Sistema de Asistencia UMG', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

def main():
    while True:
        clear_screen()
        opcion = show_menu()
        
        if opcion == '1':
            start_recognition()
        elif opcion == '2':
            curso = select_course()
            if curso:
                start_recognition(curso)
            else:
                input("Presione Enter para continuar...")
        elif opcion == '3':
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")
            input("Presione Enter para continuar...")

if __name__ == '__main__':
    main()
