from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

# Event Model
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    organizer = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    event_amount = Column(Float, nullable=False)
    caution_fee = Column(Float, nullable=False)
    location = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)
    address = Column(String, nullable=False)
    status = Column(String, default="active")
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    cancellation_reason = Column(String, nullable=True)

    # Relationship with EventPayment
    payments = relationship("EventPayment", back_populates="event")
