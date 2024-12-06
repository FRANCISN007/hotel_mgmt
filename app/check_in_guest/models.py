from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Check_in(Base):
    __tablename__ = "check_in"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, ForeignKey("rooms.room_number", ondelete="CASCADE"), nullable=False)
    guest_name = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=False)
    #status = Column(String(20))  # e.g., "checked-in", "checked-out"
    status = Column(String, default="checked-in")  # Ensure this defaults to "checked-in"
    room = relationship("Room", back_populates="check_in")
    is_checked_out = Column(Boolean, default=False)
    checkout_reason = Column(String, nullable=True)
