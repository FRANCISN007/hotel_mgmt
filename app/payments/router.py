from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import between
from app.database import get_db
from app.payments import schemas as payment_schemas, crud
from app.payments import models as payment_models
from app.users.auth import get_current_user
from app.users import schemas
from app.rooms import models as room_models  # Ensure Room model is imported
from app.bookings import models as booking_models
from sqlalchemy.sql import func
from loguru import logger

router = APIRouter()


# Set up logging
logger.add("app.log", rotation="500 MB", level="DEBUG")

@router.post("/{booking_id}")
def create_payment(
    booking_id: int,
    payment_request: payment_schemas.PaymentCreateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Create a new payment for a booking, considering discounts and payment history.
    """

    # Get the current system time as a timezone-aware datetime
    transaction_time = datetime.now(timezone.utc)

    # Ensure payment_date in the request is timezone-aware
    if payment_request.payment_date.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="The provided payment_date must include timezone information."
        )

    # Validate that the transaction time is not in the future
    if payment_request.payment_date > transaction_time:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction time {payment_request.payment_date} cannot be in the future."
        )

    # Fetch the booking record
    booking_record = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id
    ).first()

    if not booking_record:
        raise HTTPException(
            status_code=404, detail=f"Booking with ID {booking_id} does not exist."
        )

    # Fetch the room associated with the booking
    room = crud.get_room_by_number(db, booking_record.room_number)
    if not room:
        raise HTTPException(
            status_code=404, detail=f"Room {booking_record.room_number} does not exist."
        )
    
    # Ensure the booking status allows payments
    if booking_record.status not in ["checked-in", "reserved"]:
        raise HTTPException(
            status_code=400,
            detail=f"Booking ID {booking_id} must be checked-in or reserved to make a payment.",
        )

    # Calculate the total due based on the number of days and room price (exclude booking cost)
    num_days = booking_record.number_of_days
    total_due = (num_days * room.amount)  # Exclude booking cost if not needed

    # Fetch all previous payments for this booking
    existing_payments = db.query(payment_models.Payment).filter(
        payment_models.Payment.booking_id == booking_id,
        payment_models.Payment.status != "voided",
    ).all()

    # Calculate the total amount already paid, considering any previous discount allowed
    total_existing_payment = sum(
        payment.amount_paid + (payment.discount_allowed or 0) for payment in existing_payments
    )

    # Add the new payment to the total existing payments
    new_total_payment = total_existing_payment + payment_request.amount_paid + (payment_request.discount_allowed or 0)

    # Check if you want to apply a discount to the total due here (not booking cost)
    effective_total_due = total_due  # Adjust if a discount is applied to the room amount

    # Check for overpayment
    #if new_total_payment > effective_total_due:
        #raise HTTPException(
            #status_code=400,
            #detail=f"Payment exceeds the total due amount of {effective_total_due}. Please verify the payment amount."
        #)

    # Calculate balance due
    balance_due = max(effective_total_due - new_total_payment, 0)

    # Determine payment status based on balance due
    status = "payment incomplete" if balance_due > 0 else "payment completed"

    try:
        # Create the new payment with system-generated payment_date
        new_payment = crud.create_payment(
            db=db,
            payment=payment_schemas.PaymentCreateSchema(
                amount_paid=payment_request.amount_paid,
                discount_allowed=payment_request.discount_allowed,
                payment_method=payment_request.payment_method,
                payment_date=payment_request.payment_date.isoformat(),  # System-generated payment_date in UTC
            ),
            booking_id=booking_id,
            balance_due=balance_due,
            status=status,
        )

        # Update the booking payment status
        booking_record.payment_status = status
        db.commit()

        return {
            "message": "Payment processed successfully.",
            "payment_details": {
                "payment_id": new_payment.id,
                "amount_paid": new_payment.amount_paid,
                "discount_allowed": payment_request.discount_allowed,
                "payment_date": new_payment.payment_date,
                "balance_due": new_payment.balance_due,
                "status": new_payment.status,
            },
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail="Error creating payment.")
    
    


@router.get("/list")
def list_payments(
    start_date: Optional[date] = Query(None, description="date format-yyyy-mm-dd"),
    end_date: Optional[date] = Query(None, description="date format-yyyy-mm-dd"),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all payments made between the specified start and end date,
    including the total payment amount for the range, excluding voided and cancelled payments from the total calculation.
    """
    try:
        # Set the end date to the end of the day if only the date is provided
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())

        # Build the base query for payments
        query = db.query(payment_models.Payment)

        # Apply date filters based on provided inputs
        if start_date and end_date:
            if start_date > end_date:
                raise HTTPException(
                    status_code=400,
                    detail="Start date cannot be after end date."
                )
            query = query.filter(
                payment_models.Payment.payment_date >= start_datetime,
                payment_models.Payment.payment_date <= end_datetime
            )
        elif start_date:
            query = query.filter(payment_models.Payment.payment_date >= start_datetime)
        elif end_date:
            query = query.filter(payment_models.Payment.payment_date <= end_datetime)

        # Retrieve all payments within the date range, ordered by payment_date in descending order
        payments = query.order_by(payment_models.Payment.payment_date.desc()).all()

        if not payments:
            logger.info("No payments found for the specified criteria.")
            return {"message": "No payments found for the specified criteria."}

        # Prepare the list of payment details
        payment_list = []
        total_payment_amount = 0
        for payment in payments:
            payment_list.append({
                "payment_id": payment.id,
                "guest_name": payment.guest_name,
                "room_number": payment.room_number,
                "amount_paid": payment.amount_paid,
                #"booking_cost": payment.booking_cost,
                "discount_allowed": payment.discount_allowed,
                "balance_due": payment.balance_due,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "booking_id": payment.booking_id,
            })

            # Add to total_payment_amount if payment status is not "voided" or "cancelled"
            if payment.status not in ["voided", "cancelled"]:
                total_payment_amount += payment.amount_paid

        logger.info(f"Retrieved {len(payment_list)} payments.")
        return {
            "total_payments": len(payment_list),
            "total_amount": total_payment_amount,
            "payments": payment_list,
        }

    except HTTPException as e:
        # Re-raise the HTTP exception
        raise e
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving payments: {str(e)}"
        )


@router.get("/by-status")
def list_payments_by_status(
    status: Optional[str] = Query(None, description="Payment status to filter by (payment completed, payment incomplete, voided)"),
    start_date: Optional[date] = Query(None, description="Filter by payment date (start) in format yyyy-mm-dd"),
    end_date: Optional[date] = Query(None, description="Filter by payment date (end) in format yyyy-mm-dd"),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Build the base query
        query = db.query(payment_models.Payment)

        # Filter by status
        if status:
            query = query.filter(payment_models.Payment.status == status.lower())

        # Apply date filters based on payment_date
        if start_date:
            query = query.filter(payment_models.Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(payment_models.Payment.payment_date <= end_date)

        # Execute the query
        payments = query.all()

        # If no payments found, return an informative message
        if not payments:
            return {"message": "No payments found for the given criteria."}

        # Format the payments response
        formatted_payments = [
            {
                "payment_id": payment.id,
                "guest_name": payment.guest_name,
                "room_number": payment.room_number,
                "amount_paid": payment.amount_paid,
                "discount_allowed": payment.discount_allowed,
                "balance_due": payment.balance_due,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "booking_id": payment.booking_id,
            }
            for payment in payments
        ]

        # Return formatted response
        return {
            "total_payments": len(formatted_payments),
            "payments": formatted_payments if formatted_payments else []
        }

    except Exception as e:
        logger.error(f"Error retrieving payments by status and date: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        ) 


@router.get("/total_daily_payment")
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
                #"booking_cost": payment.booking_cost,
                "amount_paid": payment.amount_paid,
                "discount allowed": payment.discount_allowed,
                "balance_due": payment.balance_due,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "booking_id": payment.booking_id,
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


@router.get("/debtor_list")
def get_debtor_list(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Query all bookings that are not canceled and not complimentary
        bookings = db.query(booking_models.Booking).filter(
            booking_models.Booking.status != "cancelled",
            booking_models.Booking.payment_status != "complimentary"  # Exclude complimentary bookings
        ).all()

        if not bookings:
            raise HTTPException(status_code=404, detail="No debtor bookings found.")

        debtor_list = []
        total_debt_amount = 0  # Initialize total debt amount

        # Iterate through each booking
        for booking in bookings:
            # Fetch the room associated with the booking
            room = db.query(room_models.Room).filter(
                room_models.Room.room_number == booking.room_number
            ).first()

            if not room:
                continue

            # Calculate total amount due based on number_of_days and room price
            total_due = booking.number_of_days * room.amount

            # Query all payments for this booking, ignoring voided payments
            all_payments = db.query(payment_models.Payment).filter(
                payment_models.Payment.booking_id == booking.id,
                payment_models.Payment.status != "voided"
            ).all()

            # Calculate the total amount paid for this booking
            total_paid = sum(
                payment.amount_paid + (payment.discount_allowed or 0)
                for payment in all_payments
            )

            # Get the most recent payment date (if available)
            last_payment_date = (
                max(payment.payment_date for payment in all_payments)
                if all_payments else None
            )

            # Calculate the balance due
            balance_due = total_due - total_paid

            # Only include bookings where balance_due > 0
            if balance_due > 0:
                debtor_list.append({
                    "guest_name": booking.guest_name,
                    "room_number": booking.room_number,
                    "booking_id": booking.id,
                    "room_price": room.amount,
                    "number_of_days": booking.number_of_days,
                    "total_due": total_due,
                    "total_paid": total_paid,
                    "amount_due": balance_due,
                    "last_payment_date": last_payment_date,  # Include last payment date for sorting
                })
                total_debt_amount += balance_due

        # Raise an exception if no debtors are found
        if not debtor_list:
            raise HTTPException(status_code=404, detail="No debtors found.")

        # Sort debtor list in descending order based on the last payment date
        debtor_list.sort(
            key=lambda x: x["last_payment_date"] if x["last_payment_date"] else datetime.min,
            reverse=True
        )

        return {
            "total_debtors": len(debtor_list),
            "total_debt_amount": total_debt_amount,
            "debtors": debtor_list,
        }

    except Exception as e:
        logger.error(f"Error retrieving debtor list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the debtor list.",
        )


@router.get("/{payment_id}")
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
            #"booking_cost": payment.booking_cost,
            "amount_paid": payment.amount_paid,
            "discount_allowed": payment.discount_allowed,
            "balance_due": payment.balance_due,
            "payment_method": payment.payment_method,
            "payment_date": payment.payment_date.isoformat(),
            "status": payment.status,
            "booking_id": payment.booking_id,
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






# Delete Payment Endpoint
@router.put("/void/{payment_id}/")
def void_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    
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



