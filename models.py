from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base


class WhatsAppCustomer(Base):
    __tablename__ = "whatsapp_customers"

    id = Column(Integer, primary_key=True, index=True)
    waba_id = Column(String, unique=True, index=True, nullable=False)
    phone_number_id = Column(String, nullable=False)
    pin_code = Column(String, nullable=False)
    business_name = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())