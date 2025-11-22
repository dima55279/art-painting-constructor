import cv2
import face_recognition
import numpy as np
from typing import Dict, Any, List, Tuple
from pathlib import Path

class FaceDetectionService:
    def __init__(self):
        self.min_face_size = 100  
        self.quality_threshold = 0.7  

    async def detect_faces(self, image_path: str) -> bool:
        """
        Обнаружение лиц на изображении
        Возвращает True если найдено хотя бы одно лицо
        """
        try:
            image = face_recognition.load_image_file(image_path)

            face_locations = face_recognition.face_locations(image)
            
            return len(face_locations) > 0
            
        except Exception as e:
            print(f"Error in face detection: {str(e)}")
            return False

    async def validate_face_quality(self, image_path: str) -> Dict[str, Any]:
        """
        Проверка качества обнаруженных лиц
        Возвращает детальную информацию о качестве
        """
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_landmarks_list = face_recognition.face_landmarks(image)
            
            if not face_locations:
                return {
                    "is_acceptable": False,
                    "quality_score": 0,
                    "issues": ["Лицо не обнаружено"],
                    "faces_count": 0
                }

            quality_results = []
            all_issues = []
            
            for i, (face_location, face_landmarks) in enumerate(zip(face_locations, face_landmarks_list)):
                face_quality = await self._analyze_single_face(
                    image, face_location, face_landmarks
                )
                quality_results.append(face_quality)
                all_issues.extend(face_quality.get("issues", []))

            best_quality = max(quality_results, key=lambda x: x["quality_score"])
            
            return {
                "is_acceptable": best_quality["quality_score"] >= self.quality_threshold,
                "quality_score": best_quality["quality_score"],
                "issues": all_issues,
                "faces_count": len(face_locations),
                "face_details": quality_results
            }
            
        except Exception as e:
            print(f"Error in face quality validation: {str(e)}")
            return {
                "is_acceptable": False,
                "quality_score": 0,
                "issues": [f"Ошибка анализа: {str(e)}"],
                "faces_count": 0
            }

    async def _analyze_single_face(
        self, 
        image: np.ndarray, 
        face_location: Tuple[int, int, int, int], 
        face_landmarks: Dict[str, List[Tuple[int, int]]]
    ) -> Dict[str, Any]:
        """Анализ качества отдельного лица"""
        issues = []
        quality_score = 1.0
        
        top, right, bottom, left = face_location
        face_width = right - left
        face_height = bottom - top

        if face_width < self.min_face_size or face_height < self.min_face_size:
            issues.append("Лицо слишком маленькое")
            quality_score *= 0.5

        face_region = image[top:bottom, left:right]
        brightness = np.mean(face_region)
        if brightness < 50:
            issues.append("Слишком темное освещение")
            quality_score *= 0.7
        elif brightness > 200:
            issues.append("Слишком яркое освещение/пересвет")
            quality_score *= 0.8

        gray_face = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)
        blur_value = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        if blur_value < 100:
            issues.append("Изображение размыто")
            quality_score *= 0.6

        if "left_eye" in face_landmarks and "right_eye" in face_landmarks:
            left_eye_center = np.mean(face_landmarks["left_eye"], axis=0)
            right_eye_center = np.mean(face_landmarks["right_eye"], axis=0)

            eye_angle = np.degrees(np.arctan2(
                right_eye_center[1] - left_eye_center[1],
                right_eye_center[0] - left_eye_center[0]
            ))
            
            if abs(eye_angle) > 10:
                issues.append("Лицо повернуто")
                quality_score *= 0.8
        
        if await self._are_eyes_closed(face_landmarks):
            issues.append("Глаза закрыты")
            quality_score *= 0.7
        
        return {
            "quality_score": round(quality_score, 2),
            "issues": issues,
            "face_size": (face_width, face_height),
            "brightness": round(brightness, 2),
            "sharpness": round(blur_value, 2)
        }

    async def _are_eyes_closed(self, face_landmarks: Dict[str, List[Tuple[int, int]]]) -> bool:
        """Проверка закрыты ли глаза"""
        if "left_eye" not in face_landmarks or "right_eye" not in face_landmarks:
            return False
        
        def eye_aspect_ratio(eye_points):
            A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            return (A + B) / (2.0 * C)
        
        left_ear = eye_aspect_ratio(face_landmarks["left_eye"])
        right_ear = eye_aspect_ratio(face_landmarks["right_eye"])
        
        return left_ear < 0.2 or right_ear < 0.2

    async def extract_face_encoding(self, image_path: str) -> List[np.ndarray]:
        """Извлечение энкодингов лиц для последующего сравнения"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            return face_encodings
        except Exception as e:
            print(f"Error extracting face encoding: {str(e)}")
            return []

    async def compare_faces(
        self, 
        known_encoding: np.ndarray, 
        unknown_image_path: str
    ) -> bool:
        """Сравнение лица с известным энкодингом"""
        try:
            unknown_encodings = await self.extract_face_encoding(unknown_image_path)
            if not unknown_encodings:
                return False

            matches = face_recognition.compare_faces(
                [known_encoding], 
                unknown_encodings[0]
            )
            
            return matches[0] if matches else False
            
        except Exception as e:
            print(f"Error comparing faces: {str(e)}")
            return False