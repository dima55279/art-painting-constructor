from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    frame_type = Column(String(50), nullable=False)  

    preview_image_url = Column(String(500), nullable=False)
    model_3d_url = Column(String(500), nullable=True) 

    camera_settings = Column(JSON, nullable=True)
    
    price = Column(Float, nullable=False, default=0.0) 
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    complexity_level = Column(Integer, default=1) 
    estimated_time_hours = Column(Float, default=2.0) 

    tags = Column(JSON, nullable=True)
    sort_order = Column(Integer, default=0)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    generated_images = relationship("GeneratedImage", back_populates="frame")
    
    def __repr__(self):
        return f"<Frame(id={self.id}, name='{self.name}', type='{self.frame_type}')>"
    
    @property
    def price_display(self) -> str:
        """Форматированная цена для отображения"""
        return f"${self.price:.2f}" if self.price > 0 else "Бесплатно"