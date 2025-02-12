from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database import get_db
from app.events import models as event_models
from app.eventpayment import models as eventpayment_models, schemas as eventpayment_schemas
from app.users import schemas as user_schemas
from app.users.auth import get_current_user
from typing import List



router = APIRouter()



@router.post("/", response_model=eventpayment_schemas.EventPaymentResponse)
def create_event_payment(
    payment_data: eventpayment_schemas.EventPaymentCreate,
    db: Session = Depends(get_db),
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    event = db.query(event_models.Event).filter(event_models.Event.id == payment_data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Fetch all previous payments for this event
    total_paid = db.query(func.coalesce(func.sum(eventpayment_models.EventPayment.amount_paid), 0)).filter(
        eventpayment_models.EventPayment.event_id == payment_data.event_id
    ).scalar()

    total_discount = db.query(func.coalesce(func.sum(eventpayment_models.EventPayment.discount_allowed), 0)).filter(
        eventpayment_models.EventPayment.event_id == payment_data.event_id
    ).scalar()

    # Compute new total payment and discount including the new payment
    new_total_paid = total_paid + payment_data.amount_paid
    new_total_discount = total_discount + payment_data.discount_allowed

    # Compute balance due (excluding caution fee)
    balance_due = event.event_amount - (new_total_paid + new_total_discount)

    # Determine payment status
    payment_status = "incomplete" if balance_due > 0 else "complete"

    new_payment = eventpayment_models.EventPayment(
        event_id=payment_data.event_id,
        organiser=payment_data.organiser,
        amount_paid=payment_data.amount_paid,
        discount_allowed=payment_data.discount_allowed,
        balance_due=balance_due,
        payment_method=payment_data.payment_method,
        status=payment_status,  # Automatically set status
        created_by=current_user.username
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment


# List all Event Payments
@router.get("/", response_model=list[eventpayment_schemas.EventPaymentResponse])
def list_event_payments(
    db: Session = Depends(get_db),
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),                       
):
    
    return db.query(eventpayment_models.EventPayment).all()



# List Payment by ID
@router.get("/{payment_id}", response_model=eventpayment_schemas.EventPaymentResponse)
def get_event_payment_by_id(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    payment = db.query(eventpayment_models.EventPayment).filter(eventpayment_models.EventPayment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment




# List Payments by Status (Active, Complete, Void)
@router.get("/status/{status}", response_model=List[eventpayment_schemas.EventPaymentResponse])
def list_event_payments_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    valid_statuses = {"pending", "complete", "void"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {valid_statuses}")

    payments = db.query(eventpayment_models.EventPayment).filter(eventpayment_models.EventPayment.payment_status == status).all()
    
    return payments





# Void a Payment
@router.put("/{payment_id}/void", response_model=dict)
def void_event_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    # Only admins can void payments
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can void payments")

    payment = db.query(eventpayment_models.EventPayment).filter(eventpayment_models.EventPayment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status == "void":
        raise HTTPException(status_code=400, detail="Payment has already been voided")

    payment.status = "void"
    db.commit()
    
    return {"message": "Payment voided successfully"}
