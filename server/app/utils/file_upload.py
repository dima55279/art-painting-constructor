import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import imghdr

from app.config import settings

SUPPORTED_IMAGE_FORMATS = {
    'jpeg', 'jpg', 'png', 'webp', 'bmp', 'tiff'
}

MAX_SIZES = {
    'avatar': 5 * 1024 * 1024,  # 5MB
    'photo': 10 * 1024 * 1024,  # 10MB
    'document': 20 * 1024 * 1024,  # 20MB
}

async def save_uploaded_file(
    file: UploadFile,
    upload_dir: str,
    file_type: str = "photo",
    max_size: Optional[int] = None
) -> Tuple[str, str]:
    """
    Сохранение загруженного файла с валидацией
    """
    if not max_size:
        max_size = MAX_SIZES.get(file_type, settings.MAX_FILE_SIZE)

    await validate_file_size(file, max_size)
    
    await validate_file_type(file, SUPPORTED_IMAGE_FORMATS)

    file_extension = Path(file.filename).suffix.lower()
    filename = generate_unique_filename(file_extension)
    file_path = os.path.join(upload_dir, filename)
    
    os.makedirs(upload_dir, exist_ok=True)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    if file_type == "photo":
        await validate_image_dimensions(file_path)
    
    return filename, file_path

async def validate_file_size(file: UploadFile, max_size: int) -> None:
    """
    Валидация размера файла
    """
    current_position = file.file.tell()

    file.file.seek(0, 2)
    file_size = file.file.tell()

    file.file.seek(current_position)
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Размер файла не должен превышать {max_size // 1024 // 1024}MB"
        )

async def validate_file_type(file: UploadFile, allowed_types: set) -> None:
    """
    Валидация типа файла
    """
    if file.content_type and not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением"
        )

    file_extension = Path(file.filename).suffix.lower().lstrip('.')
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_types)}"
        )

    content = await file.read(1024)  
    await file.seek(0)  
    
    detected_type = imghdr.what(None, h=content)
    if detected_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не является валидным изображением"
        )

async def validate_image_dimensions(file_path: str) -> None:
    """
    Валидация размеров изображения
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size

            if width < 100 or height < 100:
                os.remove(file_path) 
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Изображение должно быть не менее 100x100 пикселей"
                )

            if width > 10000 or height > 10000:
                os.remove(file_path)  
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Изображение слишком большое (максимум 10000x10000 пикселей)"
                )
                
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обработке изображения: {str(e)}"
        )

def generate_unique_filename(extension: str) -> str:
    """
    Генерация уникального имени файла
    """
    return f"{uuid.uuid4().hex}{extension}"

def delete_file(file_path: str) -> bool:
    """
    Удаление файла
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")
        return False

def get_file_metadata(file_path: str) -> dict:
    """
    Получение метаданных файла
    """
    try:
        with Image.open(file_path) as img:
            return {
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "info": img.info
            }
    except Exception:
        return {}

async def compress_image(
    input_path: str,
    output_path: str,
    quality: int = 85,
    max_size: Tuple[int, int] = (1920, 1080)
) -> bool:
    """
    Сжатие изображения
    """
    try:
        with Image.open(input_path) as img:
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            if img.format in ['JPEG', 'JPG']:
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            elif img.format == 'PNG':
                img.save(output_path, 'PNG', optimize=True)
            else:
                img.save(output_path, quality=quality)
            
            return True
    except Exception as e:
        print(f"Error compressing image: {str(e)}")
        return False

def get_file_size_mb(file_path: str) -> float:
    """
    Получение размера файла в мегабайтах
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except OSError:
        return 0.0

def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Очистка старых файлов в директории
    """
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
    except Exception as e:
        print(f"Error cleaning up old files: {str(e)}")
    
    return deleted_count