from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'))  # Add booking_id as a foreign key to the bookings table
    room_number = Column(String, index=True)
    guest_name = Column(String, index=True)
    amount_paid = Column(Float)
    balance_due = Column(Float, default=0.0)
    payment_method = Column(String)
    payment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

    # Foreign key relationship to the booking
    booking = relationship("Booking", back_populates="payments")
   
   
    
   
    # Foreign key relationship to Check_in
    #check_in_id = Column(Integer, ForeignKey('check_in.id'))

   # Many-to-one relationship: Each Payment belongs to one Check_in
    #check_in = relationship("Check_in", back_populates="payments", remote_side=[check_in_id])