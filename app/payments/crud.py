from fastapi import  HTTPException
from sqlalchemy.orm import Session
from app.payments import models as payment_models, schemas
from datetime import datetime
from app.rooms import models 
from loguru import logger
from sqlalchemy import between


def create_payment(db: Session, payment: schemas.PaymentCreateSchema, balance_due: float, status: str):
    db_payment = payment_models.Payment(
        room_number=payment.room_number,
        guest_name=payment.guest_name,
        amount_paid=payment.amount_paid,
        balance_due=balance_due,
        payment_method=payment.payment_method,
        payment_date=payment.payment_date or datetime.utcnow(),
        status=status,
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_room_by_number(db: Session, room_number: str):
    # This function will check if the room exists in the database
    return db.query(models.Room).filter(models.Room.room_number == room_number).first()


def get_payment_by_guest_and_room(db: Session, guest_name: str, room_number: str):
    return db.query(payment_models.Payment).filter(
        payment_models.Payment.guest_name == guest_name,
        payment_models.Payment.room_number == room_number
    ).first()




def get_all_payments(db: Session):
    return db.query(payment_models.Payment).all()


# Get Payment by ID
def get_payment_by_id(db: Session, payment_id: int):
    """
    Retrieve a payment by its ID, handling errors properly.
    """
    try:
        payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
        return payment
    except Exception as e:
        logger.error(f"Error retrieving payment by ID: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving payment.")

  
  
def update_payment_with_new_amount(db: Session, payment_id: int, amount_paid: float, balance_due: float):
    payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
    if payment:
        payment.amount_paid += amount_paid
        payment.balance_due = balance_due
        if balance_due == 0:
            payment.status = "payment completed"
        db.commit()
        db.refresh(payment)
        return payment
    return None
   


def get_payments_by_date_range(db: Session, start_date: datetime, end_date: datetime):
    """
    Get payments made within a specific date range.
    """
    return db.query(payment_models.Payment).filter(
        payment_models.Payment.payment_date.between(start_date, end_date)
    ).all()


  
def delete_payment(db: Session, payment_id: int):
    payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
    if payment:
        db.delete(payment)
        db.commit()
  