import cv2
import numpy as np
import face_recognition

class ImageValidator:
    @staticmethod
    def validate_quality(image_np, face_locations, blur_threshold=35.0):
        """
        Validates the quality of a facial image based on ICAO-like criteria.
        Returns (is_valid, error_message).
        """
        if not face_locations or len(face_locations) != 1:
            return False, "Debe haber exactamente un rostro en la imagen."

        # Convert to grayscale for illumination and blur checks
        # Assuming image_np is RGB (since it's loaded via PIL convert('RGB'))
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

        # 1. Blur detection (Laplacian variance)
        top, right, bottom, left = face_locations[0]
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        face_gray = gray[max(top, 0):max(bottom, 0), max(left, 0):max(right, 0)]
        face_variance = cv2.Laplacian(face_gray, cv2.CV_64F).var() if face_gray.size else 0
        blur_score = max(variance, face_variance)
        if blur_score < blur_threshold:
            return False, "La fotografía está borrosa o desenfocada. Por favor, mantenga la cámara estable y vuelva a intentarlo."

        # 2. Lighting check (Brightness)
        mean_brightness = np.mean(gray)
        if mean_brightness < 40:
            return False, "La fotografía está demasiado oscura. Por favor, mejore la iluminación."
        elif mean_brightness > 220:
            return False, "La fotografía está sobreexpuesta (muy brillante). Evite luces fuertes directas."

        # 3. Face proportion and position
        face_width = right - left
        face_height = bottom - top
        
        img_height, img_width = image_np.shape[:2]
        
        face_area = face_width * face_height
        img_area = img_width * img_height
        
        area_ratio = face_area / img_area
        
        if area_ratio < 0.03:
            return False, "El rostro está demasiado lejos. Acérquese a la cámara."
        elif area_ratio > 0.65:
            return False, "El rostro está demasiado cerca de la cámara. Aléjese un poco."

        # 4. Check if face is centered
        face_center_x = left + (face_width / 2)
        face_center_y = top + (face_height / 2)
        
        img_center_x = img_width / 2
        img_center_y = img_height / 2
        
        # Calculate offset from center relative to image dimensions
        offset_x = abs(face_center_x - img_center_x) / img_width
        offset_y = abs(face_center_y - img_center_y) / img_height
        
        if offset_x > 0.35 or offset_y > 0.35:
            return False, "El rostro no está centrado. Por favor, alinéese en el centro."

        # 5. Face orientation / landmarks visibility
        landmarks = face_recognition.face_landmarks(image_np, face_locations)
        if not landmarks:
            return False, "No se pudieron detectar claramente las facciones del rostro."
            
        marks = landmarks[0]
        # Check presence of essential features
        required_features = ['left_eye', 'right_eye', 'nose_bridge', 'top_lip', 'bottom_lip']
        for feature in required_features:
            if feature not in marks or len(marks[feature]) == 0:
                return False, "El rostro no es completamente visible. Asegúrese de mirar de frente y no tener obstrucciones."

        return True, "Validación exitosa"
