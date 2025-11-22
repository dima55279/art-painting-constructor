from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    plan_type = Column(String(50), nullable=False) 
    plan_name = Column(String(100), nullable=False)

    billing_cycle = Column(String(20), default="monthly")  
    price_per_cycle = Column(Float, nullable=False)

    generation_limit = Column(Integer, nullable=True) 
    max_photo_size = Column(Integer, default=10485760)  
    premium_frames_access = Column(Boolean, default=False)
    priority_processing = Column(Boolean, default=False)
    
    status = Column(String(50), default="active") 
    auto_renew = Column(Boolean, default=True)

    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    renewed_at = Column(DateTime(timezone=True), nullable=True)

    payment_method = Column(String(50), nullable=True)
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    next_payment_date = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan_type}')>"
    
    @property
    def is_active(self) -> bool:
        """Активна ли подписка в данный момент"""
        from datetime import datetime
        return (self.status == "active" and 
                self.end_date.replace(tzinfo=None) > datetime.utcnow())
    
    @property
    def days_remaining(self) -> int:
        """Количество оставшихся дней подписки"""
        from datetime import datetime
        if self.end_date:
            remaining = self.end_date.replace(tzinfo=None) - datetime.utcnow()
            return max(0, remaining.days)
        return 0