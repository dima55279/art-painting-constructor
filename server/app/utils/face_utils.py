import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import face_recognition
from PIL import Image, ImageEnhance

def preprocess_image(
    image_path: str,
    output_size: Tuple[int, int] = (800, 800),
    enhance_quality: bool = True
) -> np.ndarray:
    """
    Предобработка изображения для улучшения качества распознавания лиц
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Не удалось загрузить изображение")
    
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w = rgb_image.shape[:2]
    if h > output_size[1] or w > output_size[0]:
        scale = min(output_size[0] / w, output_size[1] / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        rgb_image = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    if enhance_quality:
        pil_image = Image.fromarray(rgb_image)

        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.2)

        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        brightness = np.mean(pil_image)
        if brightness < 100:
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(1.1)
        
        rgb_image = np.array(pil_image)
    
    return rgb_image

def calculate_face_quality(
    face_image: np.ndarray,
    face_location: Tuple[int, int, int, int]
) -> Dict[str, Any]:
    """
    Расчет качества лица по различным параметрам
    """
    top, right, bottom, left = face_location
    face_region = face_image[top:bottom, left:right]
    
    if face_region.size == 0:
        return {
            "quality_score": 0,
            "issues": ["Пустая область лица"],
            "brightness": 0,
            "sharpness": 0,
            "symmetry": 0
        }

    gray_face = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)

    quality_score = 1.0
    issues = []

    brightness = np.mean(gray_face)
    if brightness < 50:
        issues.append("Слишком темное")
        quality_score *= 0.7
    elif brightness > 200:
        issues.append("Слишком яркое/пересвеченное")
        quality_score *= 0.8

    sharpness = cv2.Laplacian(gray_face, cv2.CV_64F).var()
    if sharpness < 50:
        issues.append("Низкая резкость")
        quality_score *= 0.6
    elif sharpness < 100:
        issues.append("Средняя резкость")
        quality_score *= 0.8

    contrast = np.std(gray_face)
    if contrast < 30:
        issues.append("Низкая контрастность")
        quality_score *= 0.7
    
    face_width = right - left
    face_height = bottom - top
    face_area = face_width * face_height
    
    if face_area < 10000: 
        issues.append("Маленькое лицо")
        quality_score *= 0.6
    
    symmetry_score = calculate_face_symmetry(face_region)
    if symmetry_score < 0.8:
        issues.append("Низкая симметрия")
        quality_score *= 0.9
    
    return {
        "quality_score": round(quality_score, 3),
        "issues": issues,
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "contrast": round(contrast, 2),
        "symmetry": round(symmetry_score, 3),
        "face_size": (face_width, face_height)
    }

def calculate_face_symmetry(face_image: np.ndarray) -> float:
    """
    Расчет симметрии лица
    """
    try:
        height, width = face_image.shape[:2]

        mid_x = width // 2
        left_half = face_image[:, :mid_x]
        right_half = face_image[:, mid_x:]
        
        right_half_flipped = cv2.flip(right_half, 1)
        
        if left_half.shape != right_half_flipped.shape:
            right_half_flipped = cv2.resize(
                right_half_flipped, 
                (left_half.shape[1], left_half.shape[0])
            )

        difference = cv2.absdiff(left_half, right_half_flipped)
        mse = np.mean(difference ** 2)

        max_mse = 255 ** 2  
        symmetry = 1 - (mse / max_mse)
        
        return max(0, symmetry)
        
    except Exception:
        return 0.5  

def extract_face_embeddings(
    image_path: str,
    model: str = "large"
) -> List[Dict[str, Any]]:
    """
    Извлечение энкодингов и характеристик лиц
    """
    try:
        image = preprocess_image(image_path)

        face_locations = face_recognition.face_locations(image, model="hog")
        face_encodings = face_recognition.face_encodings(image, face_locations)
        face_landmarks = face_recognition.face_landmarks(image, face_locations)
        
        results = []
        for i, (location, encoding, landmarks) in enumerate(
            zip(face_locations, face_encodings, face_landmarks)
        ):
            quality = calculate_face_quality(image, location)

            characteristics = extract_face_characteristics(landmarks)
            
            results.append({
                "face_id": i,
                "location": location,
                "encoding": encoding.tolist(),  
                "quality": quality,
                "landmarks": landmarks,
                "characteristics": characteristics
            })
        
        return results
        
    except Exception as e:
        print(f"Error extracting face embeddings: {str(e)}")
        return []

def extract_face_characteristics(landmarks: Dict[str, List[Tuple[int, int]]]) -> Dict[str, Any]:
    """
    Извлечение характеристик лица на основе landmarks
    """
    characteristics = {}
    
    try:
        if "left_eye" in landmarks and "right_eye" in landmarks:
            left_eye_size = calculate_eye_size(landmarks["left_eye"])
            right_eye_size = calculate_eye_size(landmarks["right_eye"])
            characteristics["eye_sizes"] = {
                "left": left_eye_size,
                "right": right_eye_size,
                "ratio": left_eye_size / right_eye_size if right_eye_size > 0 else 1.0
            }
        
        if "left_eyebrow" in landmarks and "right_eyebrow" in landmarks:
            left_brow_shape = calculate_eyebrow_shape(landmarks["left_eyebrow"])
            right_brow_shape = calculate_eyebrow_shape(landmarks["right_eyebrow"])
            characteristics["eyebrow_shapes"] = {
                "left": left_brow_shape,
                "right": right_brow_shape
            }

        if "top_lip" in landmarks and "bottom_lip" in landmarks:
            lip_shape = calculate_lip_shape(
                landmarks["top_lip"], 
                landmarks["bottom_lip"]
            )
            characteristics["lip_shape"] = lip_shape

        if "nose_bridge" in landmarks and "nose_tip" in landmarks:
            nose_shape = calculate_nose_shape(
                landmarks["nose_bridge"],
                landmarks["nose_tip"]
            )
            characteristics["nose_shape"] = nose_shape

        if all(key in landmarks for key in ["chin", "left_eye", "right_eye", "nose_tip"]):
            face_proportions = calculate_face_proportions(landmarks)
            characteristics["face_proportions"] = face_proportions
            
    except Exception as e:
        print(f"Error extracting face characteristics: {str(e)}")
    
    return characteristics

def calculate_eye_size(eye_points: List[Tuple[int, int]]) -> float:
    """Расчет размера глаза"""
    if len(eye_points) < 6:
        return 0.0
    
    width = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
    height = (np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5])) + 
              np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))) / 2
    
    return width * height  

def calculate_eyebrow_shape(eyebrow_points: List[Tuple[int, int]]) -> str:
    """Определение формы брови"""
    if len(eyebrow_points) < 3:
        return "unknown"

    start_point = np.array(eyebrow_points[0])
    end_point = np.array(eyebrow_points[-1])
    
    angle = np.degrees(np.arctan2(
        end_point[1] - start_point[1],
        end_point[0] - start_point[0]
    ))
    
    if angle < -10:
        return "arched"
    elif angle > 10:
        return "raised"
    else:
        return "straight"

def calculate_lip_shape(
    top_lip: List[Tuple[int, int]], 
    bottom_lip: List[Tuple[int, int]]
) -> Dict[str, Any]:
    """Расчет характеристик губ"""
    if len(top_lip) < 6 or len(bottom_lip) < 6:
        return {"type": "unknown", "fullness": 0}
    
    lip_height = np.mean([
        np.linalg.norm(np.array(top_lip[i]) - np.array(bottom_lip[i]))
        for i in range(min(len(top_lip), len(bottom_lip)))
    ])
    
    lip_width = np.linalg.norm(np.array(top_lip[0]) - np.array(top_lip[-1]))
    
    fullness = lip_height / lip_width if lip_width > 0 else 0
    
    if fullness > 0.3:
        lip_type = "full"
    elif fullness < 0.15:
        lip_type = "thin"
    else:
        lip_type = "medium"
    
    return {
        "type": lip_type,
        "fullness": round(fullness, 3),
        "width": lip_width,
        "height": lip_height
    }

def calculate_nose_shape(
    nose_bridge: List[Tuple[int, int]],
    nose_tip: List[Tuple[int, int]]
) -> Dict[str, Any]:
    """Расчет характеристик носа"""
    if len(nose_bridge) < 2 or len(nose_tip) < 3:
        return {"type": "unknown", "length": 0, "width": 0}
    
    nose_length = np.linalg.norm(
        np.array(nose_bridge[0]) - np.array(nose_tip[2])
    )
    
    nose_width = np.linalg.norm(
        np.array(nose_tip[0]) - np.array(nose_tip[-1])
    )
    
    return {
        "type": "standard",
        "length": round(nose_length, 2),
        "width": round(nose_width, 2),
        "ratio": round(nose_length / nose_width, 2) if nose_width > 0 else 0
    }

def calculate_face_proportions(landmarks: Dict[str, List[Tuple[int, int]]]) -> Dict[str, float]:
    """Расчет пропорций лица"""
    proportions = {}
    
    try:
        chin = landmarks["chin"]
        left_eye = landmarks["left_eye"]
        right_eye = landmarks["right_eye"]
        nose_tip = landmarks["nose_tip"]
        
        face_width = np.linalg.norm(np.array(chin[0]) - np.array(chin[-1]))
        
        face_height = np.linalg.norm(np.array(chin[8]) - np.array(nose_tip[2]))
        
        left_eye_center = np.mean(left_eye, axis=0)
        right_eye_center = np.mean(right_eye, axis=0)
        eye_distance = np.linalg.norm(left_eye_center - right_eye_center)
        
        proportions = {
            "face_width": round(face_width, 2),
            "face_height": round(face_height, 2),
            "eye_distance": round(eye_distance, 2),
            "face_ratio": round(face_height / face_width, 2) if face_width > 0 else 0,
            "golden_ratio_deviation": calculate_golden_ratio_deviation(face_width, face_height)
        }
        
    except Exception as e:
        print(f"Error calculating face proportions: {str(e)}")
    
    return proportions

def calculate_golden_ratio_deviation(width: float, height: float) -> float:
    """Расчет отклонения от золотого сечения"""
    golden_ratio = 1.618
    actual_ratio = height / width if width > 0 else 0
    deviation = abs(actual_ratio - golden_ratio) / golden_ratio
    return round(deviation, 3)