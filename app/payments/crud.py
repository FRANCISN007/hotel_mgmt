from sqlalchemy.orm import Session
from app.payments import models as payment_models, schemas
from datetime import datetime
from app.rooms import models 
from loguru import logger


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
    Retrieve a payment by its ID.
    """
    try:
        return db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
    except Exception as e:
        logger.error(f"Error retrieving payment by ID: {str(e)}")
        raise Exception("Error retrieving payment by ID")
  
  
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
   
    
def delete_payment(db: Session, payment_id: int):
    payment = db.query(payment_models.Payment).filter(payment_models.Payment.id == payment_id).first()
    if payment:
        db.delete(payment)
        db.commit()
  