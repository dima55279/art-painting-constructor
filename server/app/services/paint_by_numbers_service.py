import cv2
import numpy as np
from PIL import Image
import io
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class PaintByNumbersService:
    """Сервис для создания изображений, разбитых по номерам"""
    
    def __init__(self, max_colors: int = 12, blur: int = 15, min_area: int = 150):
        self.max_colors = max_colors
        self.blur = blur
        self.min_area = min_area
    
    async def create_numbered_image(
        self, 
        image_bytes: bytes,
        add_watermark: bool = True
    ) -> Tuple[Optional[bytes], List[str]]:
        """
        Создание изображения, разбитого по номерам
        
        Args:
            image_bytes: Байты исходного изображения
            add_watermark: Добавлять ли водяной знак
            
        Returns:
            Tuple[Optional[bytes], List[str]]: Байты изображения и список используемых цветов
        """
        try:
            logger.info("Начинаем создание изображения по номерам")
            
            # Конвертируем байты в изображение OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Не удалось декодировать изображение")
            
            logger.info(f"Размер изображения: {img.shape}")
            
            # Создаем изображение в стиле paint-by-numbers
            numbered_img, colors_used = self._process_paint_by_numbers(img)
            
            # Конвертируем обратно в PIL Image
            numbered_pil = Image.fromarray(numbered_img)
            
            # Конвертируем в байты
            output_bytes = io.BytesIO()
            numbered_pil.save(output_bytes, format='PNG', quality=95)
            numbered_bytes = output_bytes.getvalue()
            
            logger.info(f"Создано изображение размером {len(numbered_bytes)} байт")
            logger.info(f"Использовано цветов: {len(colors_used)}")
            
            return numbered_bytes, colors_used
            
        except Exception as e:
            logger.error(f"Ошибка при создании изображения по номерам: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, []
    
    def _process_paint_by_numbers(self, img: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """
        Обработка изображения в стиле paint-by-numbers
        
        Args:
            img: Изображение OpenCV (BGR)
            
        Returns:
            Tuple[np.ndarray, List[str]]: Обработанное изображение и список цветов
        """
        # Конвертируем BGR в RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Уменьшаем количество цветов
        reduced_img, color_palette = self._reduce_colors(rgb_img)
        
        # Создаем контурное изображение с номерами
        numbered_img = self._create_numbered_image(reduced_img, color_palette)
        
        # Конвертируем обратно в RGB
        numbered_rgb = cv2.cvtColor(numbered_img, cv2.COLOR_BGR2RGB)
        
        # Преобразуем цвета в hex строки
        colors_hex = self._colors_to_hex(color_palette)
        
        return numbered_rgb, colors_hex
    
    def _reduce_colors(self, img: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Уменьшение количества цветов в изображении
        
        Args:
            img: Изображение RGB
            
        Returns:
            Tuple[np.ndarray, List[np.ndarray]]: Уменьшенное изображение и палитра цветов
        """
        # Изменяем размер для ускорения обработки
        h, w = img.shape[:2]
        max_dim = 800
        if h > max_dim or w > max_dim:
            scale = max_dim / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Преобразуем в формат для k-means
        Z = img.reshape((-1, 3))
        Z = np.float32(Z)
        
        # Определяем критерии для k-means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = min(self.max_colors, len(np.unique(Z, axis=0)))
        
        # Применяем k-means
        _, labels, centers = cv2.kmeans(
            Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Преобразуем центры обратно в uint8
        centers = np.uint8(centers)
        
        # Восстанавливаем изображение
        res = centers[labels.flatten()]
        reduced_img = res.reshape((img.shape))
        
        # Сортируем цвета по яркости
        color_palette = self._sort_colors_by_brightness(centers)
        
        return reduced_img, color_palette
    
    def _sort_colors_by_brightness(self, colors: np.ndarray) -> List[np.ndarray]:
        """
        Сортировка цветов по яркости
        
        Args:
            colors: Массив цветов (BGR)
            
        Returns:
            List[np.ndarray]: Отсортированный список цветов
        """
        # Конвертируем в HSV для сортировки по значению (яркости)
        hsv_colors = []
        for color in colors:
            color_bgr = color.reshape(1, 1, 3)
            color_hsv = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)
            hsv_colors.append((color_hsv[0, 0, 2], color))
        
        # Сортируем по яркости
        hsv_colors.sort(key=lambda x: x[0])
        
        return [color for _, color in hsv_colors]
    
    def _create_numbered_image(
        self, 
        img: np.ndarray, 
        color_palette: List[np.ndarray]
    ) -> np.ndarray:
        """
        Создание изображения с номерами цветов
        
        Args:
            img: Уменьшенное изображение
            color_palette: Палитра цветов
            
        Returns:
            np.ndarray: Изображение с номерами
        """
        h, w = img.shape[:2]
        
        # Создаем белый фон
        result = np.ones((h, w, 3), dtype=np.uint8) * 255
        
        # Для каждого цвета в палитре
        for idx, color in enumerate(color_palette):
            # Создаем маску для этого цвета
            mask = cv2.inRange(img, color, color)
            
            # Находим контуры областей этого цвета
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Отбираем только достаточно большие контуры
            large_contours = [
                cnt for cnt in contours 
                if cv2.contourArea(cnt) > self.min_area
            ]
            
            # Рисуем контуры
            cv2.drawContours(
                result, large_contours, -1, 
                (0, 0, 0), 2  # Черные контуры
            )
            
            # Добавляем номера в центр каждого контура
            for cnt in large_contours:
                # Вычисляем центр масс
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Добавляем номер
                    cv2.putText(
                        result, str(idx + 1),
                        (cx - 10, cy + 10),  # Смещение для центрирования
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,  # Размер шрифта
                        (0, 0, 0),  # Черный цвет
                        2  # Толщина
                    )
        
        return result
    
    def _colors_to_hex(self, colors: List[np.ndarray]) -> List[str]:
        """
        Преобразование цветов BGR в HEX строки
        
        Args:
            colors: Список цветов в формате BGR
            
        Returns:
            List[str]: Список HEX строк
        """
        hex_colors = []
        for color in colors:
            # BGR -> RGB
            r, g, b = color[2], color[1], color[0]
            # RGB -> HEX
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            hex_colors.append(hex_color.upper())
        
        return hex_colors

# Глобальный экземпляр сервиса
paint_by_numbers_service = PaintByNumbersService()