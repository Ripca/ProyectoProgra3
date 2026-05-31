import base64
import io
import json
import logging
from datetime import datetime

import face_recognition
import numpy as np
from PIL import Image

from config import Config
from database.models import (
    AsistenciaClaseDAO,
    CursoDAO,
    PersonaDAO,
    RegistroAccesoDAO,
    SesionClaseDAO,
    AsignacionCursoDAO,
    PersonaCarnetDAO,
)

logger = logging.getLogger(__name__)


class WebRecognitionService:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.loaded_at = None

    def load_known_faces(self):
        personas = PersonaDAO.get_all_encodings()
        encodings = []
        names = []
        ids = []

        for persona in personas:
            encoding_data = persona.get("encoding_facial")
            if not encoding_data:
                continue

            if isinstance(encoding_data, str):
                encoding_data = json.loads(encoding_data)

            encodings.append(np.array(encoding_data))
            names.append(f"{persona['nombre']} {persona['apellido']}")
            ids.append(persona["id"])

        self.known_face_encodings = encodings
        self.known_face_names = names
        self.known_face_ids = ids
        self.loaded_at = datetime.now()

        return len(encodings)

    def ensure_loaded(self):
        if not self.known_face_encodings:
            self.load_known_faces()

    def recognize_image(self, image_data, mode="general", assignment_id=None, sede_id=None):
        self.ensure_loaded()

        if not self.known_face_encodings:
            return {
                "success": True,
                "recognized": [],
                "message": "No hay rostros registrados para comparar.",
                "known_faces": 0,
            }

        image_np = self._decode_image(image_data)
        face_locations = face_recognition.face_locations(image_np)
        face_encodings = face_recognition.face_encodings(image_np, face_locations)

        recognized = []
        for location, face_encoding in zip(face_locations, face_encodings):
            result = self._match_face(face_encoding)
            if not result:
                recognized.append({
                    "name": "Desconocido",
                    "persona_id": None,
                    "status": "unknown",
                    "message": "Rostro no registrado",
                    "box": self._box(location),
                })
                continue

            log_result = self._log_detection(result["persona_id"], result["name"], mode, assignment_id, sede_id)
            recognized.append({
                "name": result["name"],
                "persona_id": result["persona_id"],
                "status": log_result["status"],
                "message": log_result["message"],
                "box": self._box(location),
            })

        return {
            "success": True,
            "recognized": recognized,
            "message": self._summary_message(recognized),
            "known_faces": len(self.known_face_encodings),
        }

    def _decode_image(self, image_data):
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        binary_data = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(binary_data)).convert("RGB")
        return np.array(image)

    def _match_face(self, face_encoding):
        matches = face_recognition.compare_faces(
            self.known_face_encodings,
            face_encoding,
            tolerance=Config.FACE_RECOGNITION_TOLERANCE,
        )
        distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
        if len(distances) == 0:
            return None

        best_match_index = int(np.argmin(distances))
        if not matches[best_match_index]:
            return None

        return {
            "persona_id": self.known_face_ids[best_match_index],
            "name": self.known_face_names[best_match_index],
        }

    def _log_detection(self, persona_id, name, mode, assignment_id, sede_id=None):
        if mode == "clase" and assignment_id:
            enrolled = AsignacionCursoDAO.get_personas_by_curso(assignment_id)
            if persona_id not in [p['id'] for p in enrolled]:
                return {
                    "status": "not_enrolled",
                    "message": f"{name} no pertenece a esta clase.",
                }
            return self._log_class_attendance(persona_id, name, assignment_id)

        if mode == "general" and sede_id:
            if not PersonaCarnetDAO.has_for_sede(persona_id, sede_id):
                return {
                    "status": "wrong_sede",
                    "message": f"{name} no pertenece a esta sede.",
                }

        recent = RegistroAccesoDAO.get_recent_by_person(
            persona_id,
            minutes=Config.COOLDOWN_MINUTES,
            sede_id=sede_id,
            punto_acceso="ENTRADA_PRINCIPAL",
        )
        if recent:
            return {
                "status": "recent",
                "message": f"{name} ya fue registrado recientemente.",
            }

        RegistroAccesoDAO.create(
            persona_id=persona_id,
            punto_acceso="ENTRADA_PRINCIPAL",
            metodo="BIOMETRICO",
            observacion="Reconocimiento desde portal web",
            sede_id=sede_id,
        )
        return {"status": "logged", "message": f"Acceso registrado para {name}."}

    def _log_class_attendance(self, persona_id, name, assignment_id):
        assignment = CursoDAO.get_assignment_by_id(assignment_id)
        if not assignment:
            return {"status": "error", "message": "No se encontró la clase seleccionada."}

        today = datetime.now().date()
        sesion = SesionClaseDAO.get_by_prog_and_fecha(assignment_id, today)
        if sesion and sesion.get("estado") == "FINALIZADA":
            return {
                "status": "closed",
                "message": "La asistencia de esta clase ya fue confirmada. No se pueden agregar mas registros.",
            }

        if AsistenciaClaseDAO.exists(persona_id, assignment_id, today):
            return {
                "status": "already_logged",
                "message": f"{name} ya tiene asistencia registrada en esta clase hoy.",
            }

        if not sesion:
            sesion_id = SesionClaseDAO.create(
                assignment_id,
                today,
                assignment["hora_inicio"],
                assignment["hora_fin"],
                "EN_CURSO",
            )
        else:
            sesion_id = sesion["id"]

        AsistenciaClaseDAO.create(
            sesion_clase_id=sesion_id,
            persona_id=persona_id,
            metodo="BIOMETRICO",
            observacion="Registrado por reconocimiento facial",
        )

        location_name = f"Salón {assignment['salon_codigo']} - {assignment['curso_nombre']}"
        RegistroAccesoDAO.create(
            persona_id=persona_id,
            punto_acceso="OTRO",
            metodo="BIOMETRICO",
            observacion=location_name,
            sede_id=assignment.get("sede_id"),
        )
        return {"status": "logged", "message": f"Asistencia registrada para {name}."}

    def _box(self, location):
        top, right, bottom, left = location
        return {"top": top, "right": right, "bottom": bottom, "left": left}

    def _summary_message(self, recognized):
        if not recognized:
            return "No se detectó ningún rostro."
        logged = [item for item in recognized if item["status"] == "logged"]
        if logged:
            return f"{len(logged)} registro(s) guardado(s)."
        return recognized[0]["message"]
