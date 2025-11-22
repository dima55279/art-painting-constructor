from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)  # Для неавторизованных пользователей
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Опционально
    
    # Данные анкеты
    setting = Column(String(200), nullable=False)
    clothing = Column(String(200), nullable=False)
    pose = Column(String(200), nullable=False)
    additional_notes = Column(Text, nullable=True)
    
    # Анализ анкеты
    mood = Column(String(50), nullable=True)
    style_preferences = Column(JSON, nullable=True)
    color_palette = Column(JSON, nullable=True)
    complexity_level = Column(Integer, default=1)
    artistic_style = Column(String(100), nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Для временных анкет
    
    user = relationship("User", back_populates="questionnaires")
    
    def __repr__(self):
        return f"<Questionnaire(id={self.id}, session_id='{self.session_id}')>"