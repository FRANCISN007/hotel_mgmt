from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import between
from app.database import get_db
from app.payments import schemas as payment_schemas, crud
from app.payments import models as payment_models
from app.users.auth import get_current_user
from app.users import schemas
from app.bookings import models as booking_models
from loguru import logger

router = APIRouter()


@router.post("/create/{booking_id}")
def create_payment(
    booking_id: int,
    payment_request: payment_schemas.PaymentCreateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Create a new payment for a booking and automatically update check-in payment status.
    Excludes voided payments from total paid calculations.
    """
    booking_record = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id
    ).first()

    if not booking_record:
        raise HTTPException(
            status_code=404, detail=f"Booking with ID {booking_id} does not exist."
        )

    room = crud.get_room_by_number(db, booking_record.room_number)
    if not room:
        raise HTTPException(
            status_code=404, detail=f"Room {booking_record.room_number} does not exist."
        )

    if booking_record.status not in ["checked-in", "reserved"]:
        raise HTTPException(
            status_code=400,
            detail=f"Booking ID {booking_id} must be checked-in or reserved to make a payment.",
        )

    try:
        # Fetch existing payments for the booking, excluding voided payments
        existing_payments = db.query(payment_models.Payment).filter(
            payment_models.Payment.booking_id == booking_id,
            payment_models.Payment.status != "voided"  # Exclude voided payments
        ).all()

        logger.info(f"Existing payments: {existing_payments}")
    except Exception as e:
        logger.error(f"Error checking existing payments: {e}")
        raise HTTPException(status_code=500, detail="Error checking existing payments.")

    if existing_payments:
        return handle_existing_payment(
            db, existing_payments, payment_request, booking_record, room
        )

    return handle_new_payment(db, payment_request, booking_id, room, booking_record)


def handle_existing_payment(db, existing_payments, payment_request, booking_record, room):
    # Sum up all non-voided payments
    total_payment = sum(
        payment.amount_paid + (payment.discount_allowed or 0) for payment in existing_payments
    )

    total_payment += payment_request.amount_paid

    if total_payment > room.amount:
        raise HTTPException(
            status_code=400,
            detail="Total payment (including discount) exceeds the room price.",
        )

    new_balance_due = room.amount - total_payment
    status = "payment incomplete" if new_balance_due > 0 else "payment completed"

    try:
        # Update existing payment record
        updated_payment = crud.update_payment_with_new_amount(
            db=db,
            payment_id=existing_payments[-1].id,  # Update the last payment in the list
            amount_paid=total_payment,
            discount_allowed=payment_request.discount_allowed,
            balance_due=new_balance_due,
            status=status,
        )

        logger.info(f"Updated payment: {updated_payment.amount_paid} for booking {booking_record.id}.")

        booking_record.payment_status = status
        db.commit()

        return {
            "message": "Additional payment made successfully.",
            "payment_details": {
                "payment_id": updated_payment.id,
                "amount_paid": updated_payment.amount_paid,
                "discount_allowed": payment_request.discount_allowed,
                "balance_due": updated_payment.balance_due,
                "status": updated_payment.status,
            },
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating existing payment: {e}")
        raise HTTPException(status_code=500, detail="Error updating existing payment.")


def handle_new_payment(db, payment_request, booking_id, room, booking_record):
    # Calculate the total payment and balance due, excluding voided payments
    total_payment = payment_request.amount_paid + (payment_request.discount_allowed or 0)
    balance_due = room.amount - total_payment
    status = "payment incomplete" if balance_due > 0 else "payment completed"

    try:
        # Create new payment record
        new_payment = crud.create_payment(
            db=db,
            payment=payment_request,
            booking_id=booking_id,
            balance_due=balance_due,
            status=status,
        )
        booking_record.payment_status = status
        db.commit()

        logger.info(f"New payment created for booking ID {booking_id}.")
        return {
            "message": "Payment processed successfully.",
            "payment_id": new_payment.id,
            "amount_paid": new_payment.amount_paid,
            "discount_allowed": payment_request.discount_allowed,
            "balance_due": balance_due,
            "status": status,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Error processing payment.")


# List Payments Endpoint
@router.get("/list/")
def list_payments(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all payments in the system.
    """
    try:
        payments = crud.get_all_payments(db)
        if not payments:
            return {"message": "No payments found."}
        
        payment_list = []
        for payment in payments:
            payment_list.append({
                "payment_id": payment.id,  # Include the payment ID in the response
                "guest_name": payment.guest_name,
                "room_number": payment.room_number,
                "amount_paid": payment.amount_paid,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "balance_due": payment.balance_due,
            })

        return {
            "total_payments": len(payment_list),
            "payments": payment_list,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving payments: {str(e)}",
        )





@router.get("/payment/{payment_id}/")
def get_payment_by_id(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Get payment details by payment ID.
    """
    try:
        # Log the request
        logger.info(f"Fetching payment with ID: {payment_id}")
        
        # Retrieve payment by ID using the CRUD function
        payment = crud.get_payment_by_id(db, payment_id)
        
        # Check if the payment exists
        if not payment:
            logger.warning(f"Payment with ID {payment_id} not found.")
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )
        
        # Log the retrieved payment
        logger.info(f"Retrieved payment details: {payment}")

        # Return the payment details
        return {
            "payment_id": payment.id,
            "guest_name": payment.guest_name,
            "room_number": payment.room_number,
            "amount_paid": payment.amount_paid,
            "payment_method": payment.payment_method,
            "payment_date": payment.payment_date.isoformat(),
            "status": payment.status,
            "balance_due": payment.balance_due,
        }

    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e  # Re-raise the HTTPException
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error fetching payment with ID {payment_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving the payment."
        )


@router.get("/list_by_date/")
def list_payments_by_date(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List payments made between the specified start and end date.
    If no dates are provided, returns all payments.
    """
    try:
        # Build the base query
        query = db.query(payment_models.Payment)

        # Apply date filters based on provided inputs
        if start_date and end_date:
            if start_date > end_date:
                raise HTTPException(
                    status_code=400,
                    detail="Start date cannot be after end date."
                )
            query = query.filter(
                payment_models.Payment.payment_date >= start_date,
                payment_models.Payment.payment_date <= end_date
            )
        elif start_date:
            query = query.filter(payment_models.Payment.payment_date >= start_date)
        elif end_date:
            query = query.filter(payment_models.Payment.payment_date <= end_date)

        # Retrieve payments
        payments = query.all()

        if not payments:
            logger.info("No payments found for the specified criteria.")
            return {"message": "No payments found for the specified criteria."}

        # Prepare the list of payment details to be returned
        payment_list = [
            {
                "payment_id": payment.id,
                "guest_name": payment.guest_name,
                "room_number": payment.room_number,
                "amount_paid": payment.amount_paid,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "balance_due": payment.balance_due,
            }
            for payment in payments
        ]

        logger.info(f"Retrieved {len(payment_list)} payments.")
        return {
            "total_payments": len(payment_list),
            "payments": payment_list,
        }

    except Exception as e:
        logger.error(f"Error retrieving payments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving payments: {str(e)}",
        )

@router.get("/list_void_payments/")
def list_void_payments(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all voided payments between the specified start and end date.
    If no dates are provided, returns all voided payments.
    """
    try:
        # Build the base query to get only voided payments
        query = db.query(payment_models.Payment).filter(
            payment_models.Payment.status == "voided"
        )

        # Apply date filters based on provided inputs
        if start_date and end_date:
            if start_date > end_date:
                raise HTTPException(
                    status_code=400,
                    detail="Start date cannot be after end date."
                )
            query = query.filter(
                payment_models.Payment.payment_date >= start_date,
                payment_models.Payment.payment_date <= end_date
            )
        elif start_date:
            query = query.filter(payment_models.Payment.payment_date >= start_date)
        elif end_date:
            query = query.filter(payment_models.Payment.payment_date <= end_date)

        # Retrieve voided payments
        voided_payments = query.all()

        if not voided_payments:
            logger.info("No voided payments found for the specified criteria.")
            return {"message": "No voided payments found for the specified criteria."}

        # Prepare the list of voided payment details to be returned
        voided_payment_list = [
            {
                "payment_id": payment.id,
                "guest_name": payment.guest_name,
                "room_number": payment.room_number,
                "amount_paid": payment.amount_paid,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "balance_due": payment.balance_due,
            }
            for payment in voided_payments
        ]

        logger.info(f"Retrieved {len(voided_payment_list)} voided payments.")
        return {
            "total_voided_payments": len(voided_payment_list),
            "voided_payments": voided_payment_list,
        }

    except Exception as e:
        logger.error(f"Error retrieving voided payments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving voided payments: {str(e)}",
        )



@router.get("/total_daily_payment/")
def total_payment(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Retrieve total daily sales and a list of payments for the current day, excluding void payments.
    """
    try:
        # Get the current date
        today = datetime.now().date()

        # Query payments made on the current day, excluding void payments
        payments = db.query(payment_models.Payment).filter(
            payment_models.Payment.payment_date >= today,
            payment_models.Payment.payment_date < today + timedelta(days=1),
            payment_models.Payment.status != "voided"
        ).all()

        if not payments:
            return {
                "message": "No payments found for today.",
                "total_payments": 0,
                "total_amount": 0,
                "payments": []
            }

        # Prepare the list of payment details
        payment_list = []
        total_amount = 0
        for payment in payments:
            total_amount += payment.amount_paid
            payment_list.append({
                "payment_id": payment.id,
                "room_number": payment.room_number,
                "guest_name": payment.guest_name,
                "amount_paid": payment.amount_paid,
                "balance_due": payment.balance_due,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
            })

        return {
            "message": "Today's payment data retrieved successfully.",
            "total_payments": len(payment_list),
            "total_amount": total_amount,
            "payments": payment_list,
        }

    except Exception as e:
        logger.error(f"Error retrieving daily sales: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving daily sales."
        )




# Delete Payment Endpoint
@router.put("/void/{payment_id}/")
def void_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Mark a payment as void by its ID. This action preserves the payment record for audit purposes.
    """
    try:
        # Retrieve the payment record by ID
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            logger.warning(f"Payment with ID {payment_id} does not exist.")
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )

        # Update payment status to void
        payment.status = "voided"
        db.commit()

        logger.info(f"Payment with ID {payment_id} marked as void.")

        return {
            "message": f"Payment with ID {payment_id} has been marked as void successfully.",
            "payment_details": {
                "payment_id": payment.id,
                "status": payment.status,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking payment as void: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while marking the payment as void."
        )


@router.put("/update/{payment_id}/")
def update_payment(
    payment_id: int,
    payment_update: payment_schemas.PaymentUpdateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Update payment details such as amount, room number, guest name, and other fields by payment ID.
    The status will be automatically calculated.
    """
    try:
        # Retrieve the existing payment
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )

        # Update the room number if provided
        if payment_update.room_number is not None:
            # Validate the new room number
            room = crud.get_room_by_number(db, payment_update.room_number)
            if not room:
                raise HTTPException(
                    status_code=404,
                    detail=f"Room {payment_update.room_number} not found."
                )
            payment.room_number = payment_update.room_number

        # Update the guest name if provided
        if payment_update.guest_name is not None:
            # Optionally, add validation for the guest if needed
            payment.guest_name = payment_update.guest_name

        # Update the amount paid if provided
        if payment_update.amount_paid is not None:
            new_total_paid = payment_update.amount_paid
            if new_total_paid > room.amount:
                raise HTTPException(
                    status_code=400,
                    detail="Updated payment exceeds the room price."
                )
            payment.amount_paid = new_total_paid

        # Apply the discount if provided
        if payment_update.discount_allowed is not None:
            payment.discount_allowed = payment_update.discount_allowed

        # Calculate the total after applying the discount
        total_after_discount = room.amount - payment.discount_allowed

        # Ensure the payment does not exceed the total amount after the discount
        if payment.amount_paid > total_after_discount:
            raise HTTPException(
                status_code=400,
                detail="Amount paid exceeds the room price after discount."
            )

        # Calculate the new balance due considering the discount
        payment.balance_due = total_after_discount - payment.amount_paid

        # Update other fields
        if payment_update.payment_method is not None:
            payment.payment_method = payment_update.payment_method

        if payment_update.payment_date is not None:
            payment.payment_date = payment_update.payment_date

        # Calculate status automatically based on balance_due
        if payment.balance_due == 0:
            payment.status = "payment completed"
        elif payment.balance_due > 0 and payment.amount_paid > 0:
            payment.status = "payment incomplete"
        else:
            payment.status = "pending"

        # Commit changes to the database
        db.commit()
        logger.info(f"Payment with ID {payment_id} updated successfully.")

        # Return updated payment details
        return {
            "message": f"Payment with ID {payment_id} updated successfully.",
            "payment_details": {
                "payment_id": payment.id,
                "room_number": payment.room_number,
                "guest_name": payment.guest_name,
                "amount_paid": payment.amount_paid,
                "discount_allowed": payment.discount_allowed,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "balance_due": payment.balance_due,
                "status": payment.status,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating payment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the payment."
        )
