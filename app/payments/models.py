from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, index=True)
    guest_name = Column(String, index=True)
    amount_paid = Column(Float)  # Changed from 'amount' to 'amount_paid'
    balance_due = Column(Float, default=0.0)
    payment_method = Column(String)
    payment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # Payment status (pending, completed, failed)

    #Relationship with check-in guest model (optional if you want to link payments to check-ins)
    #check_in_id = Column(Integer, ForeignKey("check_in.id"))
    #check_in = relationship("Check_in", back_populates="payments")