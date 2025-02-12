from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class EventPayment(Base):
    __tablename__ = "event_payments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)  # Foreign key to Event table
    
    organiser = Column(String, index=True, nullable=False)
    amount_paid = Column(Float, nullable=False)
    discount_allowed = Column(Float, default=0.0)  # Discount allowed on the payment
    balance_due = Column(Float, default=0.0)  # Computed: event_amount - (amount_paid + discount_allowed)
    payment_method = Column(String, nullable=False)
    payment_date = Column(DateTime, default=func.now())
    payment_status = Column(String, default="pending")
    created_by = Column(String, nullable=False)  # Track who created the payment

    # Relationship with Event
    event = relationship("Event", back_populates="payments")

    def compute_balance_due(self):
        """Computes the balance due for the event payment."""
        if self.event:
            self.balance_due = self.event.event_amount - (self.amount_paid + self.discount_allowed)
