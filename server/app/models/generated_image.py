from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    frame_id = Column(Integer, ForeignKey("frames.id", ondelete="CASCADE"), nullable=False)

    generated_image_url = Column(String(500), nullable=False)
    numbered_image_url = Column(String(500), nullable=True) 
    preview_image_url = Column(String(500), nullable=True)   

    generation_parameters = Column(JSON, nullable=True) 
    questionnaire_answers = Column(JSON, nullable=True) 

    status = Column(String(50), default="pending") 
    progress = Column(Integer, default=0)  
    error_message = Column(Text, nullable=True)

    colors_used = Column(JSON, nullable=True) 
    complexity_score = Column(Integer, nullable=True)  
    generation_time_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="generated_images")
    original_photo = relationship("Photo", back_populates="generated_images")
    frame = relationship("Frame", back_populates="generated_images")
    order = relationship("Order", back_populates="generated_image", uselist=False)
    
    def __repr__(self):
        return f"<GeneratedImage(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Завершена ли генерация"""
        return self.status == "completed"
    
    @property
    def processing_time(self) -> float:
        """Время обработки в секундах"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0