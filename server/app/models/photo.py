from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Изменено на nullable=True

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), unique=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  
    mime_type = Column(String(100), nullable=False)

    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    image_metadata = Column(JSON, nullable=True) 

    face_detected = Column(Boolean, default=False)
    face_quality_score = Column(Integer, nullable=True)  
    face_analysis_data = Column(JSON, nullable=True) 

    is_approved = Column(Boolean, default=False) 
    rejection_reason = Column(Text, nullable=True) 

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="photos")
    generated_images = relationship("GeneratedImage", back_populates="original_photo")
    
    def __repr__(self):
        return f"<Photo(id={self.id}, user_id={self.user_id}, filename='{self.original_filename}')>"
    
    @property
    def file_size_mb(self) -> float:
        """Размер файла в мегабайтах"""
        return round(self.file_size / (1024 * 1024), 2)