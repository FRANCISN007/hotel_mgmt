#Check_in models
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


"""
class Check_in(Base):
    __tablename__ = "check_in"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, ForeignKey("rooms.room_number", ondelete="CASCADE"), nullable=False)
    guest_name = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=False)
    status = Column(String, default="checked-in")
    payment_status = Column(String, default="not paid")
    #original_payment_status = Column(String, default="not paid")
    room = relationship("Room", back_populates="check_in")
    is_checked_out = Column(Boolean, default=False)
    checkout_reason = Column(String, nullable=True)

     # One-to-many relationship: A Check_in can have many Payments
    payments = relationship("Payment", back_populates="check_in")
    
    
""" 




class Booking(Base):
    """
    Unified model for both reservations and check-ins.
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, ForeignKey("rooms.room_number", ondelete="CASCADE"), nullable=False)
    guest_name = Column(String, nullable=False)
    arrival_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=False)
    booking_type = Column(String, nullable=False)  # "reservation" or "check-in"
    status = Column(String, default="reserved")  # reserved, checked-in, or checked-out
    payment_status = Column(String, default="pending")  # Optional for check-ins
    is_checked_out = Column(Boolean, default=False)  # Optional for check-ins
    cancellation_reason = Column(String, nullable=True)  # Optional for reservations

    # Relationships
    room = relationship("Room", back_populates="bookings")
   
   # Many-to-one relationship: One booking can have multiple payments
    payments = relationship("Payment", back_populates="booking")