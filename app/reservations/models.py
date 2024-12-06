   
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

from sqlalchemy import Boolean

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, ForeignKey("rooms.room_number", ondelete="CASCADE"), nullable=False)
    guest_name = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=False)
    status = Column(String, default="reserved")  # Possible values: reserved, checked-in, checked-out
    is_deleted = Column(Boolean, default=False)  # Soft delete flag
    cancellation_reason = Column(String, nullable=True)  # Reason for cancellation

    room = relationship("Room", back_populates="reservations")

