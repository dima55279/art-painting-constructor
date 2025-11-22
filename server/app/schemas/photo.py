from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl

class PhotoBase(BaseModel):
    original_filename: str
    description: Optional[str] = None

class PhotoUpload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class PhotoResponse(PhotoBase):
    id: int
    user_id: Optional[int] = None
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    face_detected: bool
    face_quality_score: Optional[int] = None
    is_approved: bool
    rejection_reason: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    file_size_mb: float
    image_metadata: Optional[Dict[str, Any]] = None
    face_analysis_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        # Создаем словарь с данными, обрабатывая None значения
        data = {
            "id": obj.id,
            "user_id": obj.user_id,  # Может быть None
            "original_filename": obj.original_filename,
            "stored_filename": obj.stored_filename,
            "file_path": obj.file_path,
            "file_size": obj.file_size,
            "mime_type": obj.mime_type,
            "width": obj.width,
            "height": obj.height,
            "face_detected": obj.face_detected,
            "face_quality_score": obj.face_quality_score,
            "is_approved": obj.is_approved,
            "rejection_reason": obj.rejection_reason,
            "uploaded_at": obj.uploaded_at,
            "processed_at": obj.processed_at,
            "file_size_mb": round(obj.file_size / (1024 * 1024), 2),
            "image_metadata": obj.image_metadata,
            "face_analysis_data": obj.face_analysis_data,
        }
        return cls(**data)

class PhotoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_approved: Optional[bool] = None
    rejection_reason: Optional[str] = None

class PhotoInDB(PhotoResponse):
    pass

class FaceDetectionResult(BaseModel):
    face_detected: bool
    faces_count: int
    quality_score: Optional[int] = None
    message: Optional[str] = None
    issues: Optional[list] = None

class PhotoValidationRequest(BaseModel):
    photo_id: int
    validate_face: bool = True
    validate_quality: bool = True