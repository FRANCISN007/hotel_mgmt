from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.payments import schemas as payment_schemas, crud
from app.users.auth import get_current_user
from app.users import schemas
from loguru import logger
from app.check_in_guest import models as check_in_models  # Import check-in models to update the status

router = APIRouter()

# Create Payment Endpoint
@router.post("/create/")
def create_payment(
    payment_request: payment_schemas.PaymentCreateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Create a new payment for a guest and automatically update check-in payment status.
    """
    # Step 1: Check if the room exists
    room = crud.get_room_by_number(db, payment_request.room_number)
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room {payment_request.room_number} does not exist."
        )

    # Step 2: Check if the guest has already paid for the room
    try:
        existing_payment = crud.get_payment_by_guest_and_room(db, payment_request.guest_name, payment_request.room_number)
        logger.info(f"Existing payment: {existing_payment}")
    except Exception as e:
        logger.error(f"Error checking existing payment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error checking existing payment."
        )

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail=f"Payment for room {payment_request.room_number} by guest {payment_request.guest_name} already exists."
        )

    # Step 3: Compare the payment amount with the room price
    if payment_request.amount_paid < room.amount:
        # Calculate the balance remaining if payment is less than room price
        balance_due = room.amount - payment_request.amount_paid
        logger.info(f"Balance remaining: {balance_due}")
        
        # Create the payment and set it as incomplete
        try:
            # Update balance_due and set status to "payment incomplete"
            new_payment = crud.create_payment(db=db, payment=payment_request, balance_due=balance_due, status="payment incomplete")
            logger.info(f"Payment of {new_payment.amount_paid} for room {new_payment.room_number} created successfully.")

            # Step 4: Update the check-in status to 'payment incomplete'
            check_in_record = db.query(check_in_models.Check_in).filter(
                check_in_models.Check_in.room_number == payment_request.room_number,
                check_in_models.Check_in.guest_name == payment_request.guest_name,
                check_in_models.Check_in.status == "checked-in",  # Only update for guests currently checked-in
            ).first()

            if check_in_record:
                check_in_record.payment_status = "payment incomplete"
                db.commit()
                logger.info(f"Payment status updated to 'payment incomplete' for guest {payment_request.guest_name} in room {payment_request.room_number}.")
            else:
                logger.warning(f"No check-in record found for guest {payment_request.guest_name} in room {payment_request.room_number}, payment not reflected.")

            # Commit the incomplete payment
            db.commit()
            logger.info(f"Payment status updated to 'payment incomplete' for guest {payment_request.guest_name}.")

            return {
                "message": "Payment amount is lesser than the room price. Balance due.",
                "room_number": payment_request.room_number,
                "guest_name": payment_request.guest_name,
                "room_price": room.amount,
                "amount_paid": payment_request.amount_paid,
                "balance_due": balance_due,
                "status": "payment incomplete"
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing payment: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while processing the payment.")
    
    # Step 5: Create the new payment in the database if payment is complete
    try:
        balance_due = 0  # Full payment, no balance due
        new_payment = crud.create_payment(db=db, payment=payment_request, balance_due=balance_due, status="payment completed")
        logger.info(f"Payment of {new_payment.amount_paid} for room {new_payment.room_number} created successfully.")

        # Step 6: Update check-in status to 'payment completed' if the full amount is paid
        check_in_record = db.query(check_in_models.Check_in).filter(
            check_in_models.Check_in.room_number == payment_request.room_number,
            check_in_models.Check_in.guest_name == payment_request.guest_name,
            check_in_models.Check_in.status == "checked-in",  # Only update for guests currently checked-in
        ).first()

        if check_in_record:
            check_in_record.payment_status = "payment completed"
            db.commit()
            logger.info(f"Payment status updated to 'payment completed' for guest {payment_request.guest_name} in room {payment_request.room_number}.")
        else:
            logger.warning(f"No check-in record found for guest {payment_request.guest_name} in room {payment_request.room_number}, payment not reflected.")

        # Commit the completed payment
        db.commit()
        logger.info(f"Payment status updated to 'payment completed' for guest {payment_request.guest_name}.")

        return {
            "message": "Payment processed successfully.",
            "payment_details": {
                "room_number": new_payment.room_number,
                "guest_name": new_payment.guest_name,
                "amount_paid": new_payment.amount_paid,
                "payment_method": new_payment.payment_method,
                "payment_date": new_payment.payment_date.isoformat(),
                "status": new_payment.status,
                "balance_due": new_payment.balance_due  # Include balance_due in the response
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
                "amount": payment.amount_paid,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date.isoformat(),
                "status": payment.status,
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

# Delete Payment Endpoint
@router.delete("/delete/{payment_id}/")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Delete a payment record by its ID.
    """
    try:
        # Get the payment record to check if it exists
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=404,
                detail=f"Payment with ID {payment_id} not found."
            )

        # Delete the payment record
        crud.delete_payment(db, payment_id)
        logger.info(f"Payment with ID {payment_id} has been deleted.")
        return {"message": f"Payment with ID {payment_id} has been deleted successfully."}

    except Exception as e:
        logger.error(f"Error deleting payment: {str(e)}")
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
        if payment_update.amount is not None:
            payment.amount = payment_update.amount
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
                "amount": payment.amount,
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
