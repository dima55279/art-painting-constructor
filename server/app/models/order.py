from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    generated_image_id = Column(Integer, ForeignKey("generated_images.id", ondelete="CASCADE"), nullable=False)
    
    painting_name = Column(String(200), nullable=False)
    painting_size = Column(String(50), nullable=False) 
    materials_included = Column(Boolean, default=True) 

    shipping_address = Column(JSON, nullable=False)  
    shipping_method = Column(String(50), default="standard") 
    tracking_number = Column(String(100), nullable=True)

    status = Column(String(50), default="pending")
    payment_status = Column(String(50), default="pending")  

    base_price = Column(Float, nullable=False)
    frame_price = Column(Float, default=0.0)
    shipping_price = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)

    promo_code = Column(String(50), nullable=True)
    discount_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="orders")
    generated_image = relationship("GeneratedImage", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"
    
    @property
    def can_be_cancelled(self) -> bool:
        """Можно ли отменить заказ"""
        return self.status in ["pending", "confirmed"]
    
    @property
    def estimated_delivery_date(self):
        """Расчетная дата доставки"""
        return None