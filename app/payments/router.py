from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.payments import schemas as payment_schemas, crud
from app.users.auth import get_current_user
from app.users import schemas
from loguru import logger
from app.bookings import models as booking_models  # Import check-in models to update the status
from sqlalchemy import between
from datetime import datetime
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/create/{booking_id}")
def create_payment(
    booking_id: int,
    payment_request: payment_schemas.PaymentCreateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Create a new payment for a guest and automatically update check-in payment status.
    """
    # Step 1: Check if the booking exists based on the booking ID
    booking_record = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id
    ).first()

    if not booking_record:
        raise HTTPException(
            status_code=404,
            detail=f"Booking with ID {booking_id} does not exist."
        )

    room = crud.get_room_by_number(db, booking_record.room_number)
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room {booking_record.room_number} does not exist."
        )

    # Step 2: Validate guest's booking status
    if booking_record.status not in ["checked-in", "reserved"]:
        raise HTTPException(
            status_code=400,
            detail=f"Guest with booking ID {booking_id} must be checked in or have a reserved status before making a payment."
        )
    
    # Step 3: Check if the guest has already paid for the room
    try:
        existing_payment = crud.get_payment_by_guest_and_room(db, booking_record.guest_name, booking_record.room_number)
        logger.info(f"Existing payment: {existing_payment}")
    except Exception as e:
        logger.error(f"Error checking existing payment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error checking existing payment."
        )

    if existing_payment:
        if existing_payment.status == "payment completed":
            raise HTTPException(
                status_code=400,
                detail=f"Payment for room {booking_record.room_number} by guest {booking_record.guest_name} already exists and is completed."
            )
        elif existing_payment.status == "payment incomplete":
            # If the payment is incomplete, we allow another payment.
            balance_due = existing_payment.balance_due
            if payment_request.amount_paid + existing_payment.amount_paid > room.amount:
                raise HTTPException(
                    status_code=400,
                    detail="Payment amount exceeds the room price."
                )
            else:
                # Add the new payment and update the balance.
                new_balance_due = balance_due - payment_request.amount_paid
                updated_payment = crud.update_payment_with_new_amount(
                    db=db,
                    payment_id=existing_payment.id,
                    amount_paid=payment_request.amount_paid,
                    balance_due=new_balance_due
                )
                logger.info(f"Updated payment of {updated_payment.amount_paid} for room {updated_payment.room_number}.")

                # Step 4: Update the check-in status to 'payment incomplete' if still incomplete
                check_in_record = db.query(booking_models.Booking).filter(
                    booking_models.Booking.id == booking_id,
                    booking_models.Booking.status == "checked-in",
                ).first()

                if check_in_record:
                    check_in_record.payment_status = "payment incomplete"
                    db.commit()
                    logger.info(f"Payment status updated to 'payment incomplete' for guest {booking_record.guest_name} in room {booking_record.room_number}.")
                else:
                    logger.warning(f"No check-in record found for guest {booking_record.guest_name} in room {booking_record.room_number}, payment not reflected.")

                db.commit()
                return {
                    "message": "Additional payment made successfully, balance updated.",
                    "payment_details": {
                        "payment_id": updated_payment.id,
                        "payment_id": updated_payment.id,
                        "room_number": updated_payment.room_number,
                        "guest_name": updated_payment.guest_name,
                        "amount_paid": updated_payment.amount_paid,
                        "payment_method": updated_payment.payment_method,
                        "payment_date": updated_payment.payment_date.isoformat(),
                        "status": updated_payment.status,
                        "balance_due": updated_payment.balance_due
                    }
                }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown payment status for guest {booking_record.guest_name} in room {booking_record.room_number}."
            )
    else:
        # Step 3: Compare the payment amount with the room price for a first-time payment
        if payment_request.amount_paid < room.amount:
            balance_due = room.amount - payment_request.amount_paid
            logger.info(f"Balance remaining: {balance_due}")

            try:
                # Create the payment and set it as incomplete
                new_payment = crud.create_payment(db=db, payment=payment_request, balance_due=balance_due, status="payment incomplete")
                logger.info(f"Payment of {new_payment.amount_paid} for room {new_payment.room_number} created successfully.")

                # Step 4: Update the check-in status to 'payment incomplete'
                check_in_record = db.query(booking_models.Booking).filter(
                    booking_models.Booking.id == booking_id,
                    booking_models.Booking.status == "checked-in",
                ).first()

                if check_in_record:
                    check_in_record.payment_status = "payment incomplete"
                    db.commit()
                    logger.info(f"Payment status updated to 'payment incomplete' for guest {booking_record.guest_name} in room {booking_record.room_number}.")
                else:
                    logger.warning(f"No check-in record found for guest {booking_record.guest_name} in room {booking_record.room_number}, payment not reflected.")

                db.commit()
                return {
                    "message": "Payment amount is lesser than the room price. Balance due.",
                    "payment_id": new_payment.id,
                    "room_number": booking_record.room_number,
                    "guest_name": booking_record.guest_name,
                    "room_price": room.amount,
                    "amount_paid": payment_request.amount_paid,
                    "balance_due": balance_due,
                    "status": "payment incomplete"
                }

            except Exception as e:
                db.rollback()
                logger.error(f"Error processing payment: {str(e)}")
                raise HTTPException(status_code=500, detail="An error occurred while processing the payment.")
    
        else:
            # Full payment received
            balance_due = 0  # Full payment, no balance due
            try:
                new_payment = crud.create_payment(db=db, payment=payment_request, balance_due=balance_due, status="payment completed")
                logger.info(f"Payment of {new_payment.amount_paid} for room {new_payment.room_number} created successfully.")

                # Step 6: Update check-in status to 'payment completed' if the full amount is paid
                check_in_record = db.query(booking_models.Booking).filter(
                    booking_models.Booking.id == booking_id,
                    booking_models.Booking.status == "checked-in",
                ).first()

                if check_in_record:
                    check_in_record.payment_status = "payment completed"
                    db.commit()
                    logger.info(f"Payment status updated to 'payment completed' for guest {booking_record.guest_name} in room {booking_record.room_number}.")
                else:
                    logger.warning(f"No check-in record found for guest {booking_record.guest_name} in room {booking_record.room_number}, payment not reflected.")

                db.commit()
                return {
                    "message": "Payment processed successfully.",
                    "payment_id": new_payment.id,
                    "payment_details": {
                        "booking_id": new_payment.booking_id,
                        "room_number": new_payment.room_number,
                        "guest_name": new_payment.guest_name,
                        "amount_paid": new_payment.amount_paid,
                        "payment_method": new_payment.payment_method,
                        "payment_date": new_payment.payment_date.isoformat(),
                        "status": new_payment.status,
                        "balance_due": new_payment.balance_due
                    }
                }
            except Exception as e:
                db.rollback()
                logger.error(f"Error processing payment: {str(e)}")
                raise HTTPException(status_code=500, detail="An error occurred while processing the payment.")


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
        # Retrieve payment by ID
        payment = crud.get_payment_by_id(db, payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )
        
        # If the payment exists, return its details
        return {
            "payment_id": payment.id,
            "guest_name": payment.guest_name,
            "room_number": payment.room_number,
            "amount_paid": payment.amount_paid,
            "payment_method": payment.payment_method,
            "payment_date": payment.payment_date.isoformat(),
            "status": payment.status,
            "balance_due": payment.balance_due
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving the payment: {str(e)}",
        )

# List Payments by Date Range Endpoint
from datetime import datetime, timedelta

@router.get("/list_by_date/")
def list_payments_by_date(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List payments made between the specified start and end date.
    """
    try:
        # Ensure that the start_date is before or equal to end_date
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date cannot be after end date."
            )

        # Adjust the end date to include the entire day (23:59:59.999999)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Retrieve payments within the specified date range
        payments = crud.get_payments_by_date_range(db, start_date, end_date)

        if not payments:
            logger.info(f"No payments found between {start_date} and {end_date}.")
            return {"message": "No payments found for the specified date range."}

        # Prepare the list of payment details to be returned
        payment_list = []
        for payment in payments:
            payment_list.append({
                "payment_id": payment.id,
                "guest_name": payment.guest_name,
                "room_number": payment.room_number,
                "amount_paid": payment.amount_paid,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
                "balance_due": payment.balance_due,
            })

        logger.info(f"Retrieved {len(payment_list)} payments between {start_date} and {end_date}.")
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

# Delete Payment Endpoint
# Delete Payment Endpoint
@router.delete("/delete/{payment_id}/")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Delete a payment record by its ID and revert the check-in status to 'payment incomplete' if applicable.
    """
    try:
        # Step 1: Check if the payment exists
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            logger.warning(f"Payment with ID {payment_id} does not exist.")
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )

        logger.info(f"Found payment record to delete: {payment}")

        # Step 2: Revert check-in payment status if associated check-in record exists
        check_in_record = db.query(booking_models.Booking).filter(
            booking_models.Booking.room_number == payment.room_number,
            booking_models.Booking.guest_name == payment.guest_name
        ).first()

        if check_in_record:
            check_in_record.payment_status = "payment incomplete"
            db.commit()  # Commit the reverted status immediately
            logger.info(f"Reverted payment status for guest {payment.guest_name} in room {payment.room_number} to 'payment incomplete'.")

        # Step 3: Delete the payment
        crud.delete_payment(db, payment_id)
        db.commit()
        logger.info(f"Payment with ID {payment_id} successfully deleted.")

        return {"message": f"Payment with ID {payment_id} has been deleted successfully."}

    except HTTPException as e:
        # Raise HTTPExceptions gracefully
        raise e
    except Exception as e:
        db.rollback()  # Rollback the transaction on error
        logger.error(f"Error deleting payment with ID {payment_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the payment."
        )

# Update Payment Endpoint
@router.put("/update/{payment_id}/")
def update_payment(
    payment_id: int,
    payment_update: payment_schemas.PaymentUpdateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Update payment details such as amount, status, or other fields by payment ID.
    """
    try:
        # Get the existing payment
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )

        # Update the fields based on the input
        if payment_update.amount_paid is not None:
            payment.amount_paid = payment_update.amount_paid
        if payment_update.status is not None:
            payment.status = payment_update.status

        # Commit the changes to the database
        db.commit()
        logger.info(f"Payment with ID {payment_id} updated successfully.")

        return {
            "message": f"Payment with ID {payment_id} updated successfully.",
            "payment_details": {
                "room_number": payment.room_number,
                "guest_name": payment.guest_name,
                "amount": payment.amount_paid,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating payment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the payment."
        )