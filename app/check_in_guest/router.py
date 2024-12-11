from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from app.database import get_db
from typing import Optional  # Import for optional parameters
#from app.guest import schemas, models  # Import guest-specific schemas and models
from app.users.auth import get_current_user
from sqlalchemy import or_
from app.rooms import models as room_models  # Import room models
from app.reservations import models as reservation_models  # Import reservation models
from app.check_in_guest.crud import check_overlapping_check_in  # Import the function
from app.check_in_guest import schemas, models as check_in_guest_models
from datetime import date
from loguru import logger

router = APIRouter()


logger.add("app.log", rotation="500 MB", level="DEBUG")

@router.post("/create/")
def check_in_guest(
    check_in_request: schemas.CheckInSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Check a guest into a room.
    Ensures the room is available, no overlapping reservations or check-ins exist, 
    and the transaction date is valid.
    """
    room_number = check_in_request.room_number

    # Step 1: Validate the transaction date
    today = date.today()
    if check_in_request.arrival_date > today:
        logger.error(f"Failed check-in attempt for future date: {check_in_request.arrival_date} for room {room_number}.")
        raise HTTPException(
            status_code=400,
            detail="Check-ins are only allowed for today's date. For future dates, please use the reservation endpoint."
        )
    
    if check_in_request.arrival_date < today:
        logger.error(f"Failed check-in attempt for past date: {check_in_request.arrival_date} for room {room_number}.")
        raise HTTPException(
            status_code=400,
            detail="Check-in cannot be performed for past dates."
        )

    # Step 2: Validate room existence
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        logger.error(f"Room {room_number} not found.")
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    # Step 3: Check for overlapping check-ins
    overlapping_check_in = check_overlapping_check_in(
        db=db,
        room_number=room_number,
        arrival_date=check_in_request.arrival_date,
        departure_date=check_in_request.departure_date,
    )
    if overlapping_check_in:
        logger.error(f"Room {room_number} has overlapping check-in for dates {check_in_request.arrival_date} to {check_in_request.departure_date}.")
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} is already checked-in by another guest during the requested dates."
        )

    # Step 4: Create new check-in record
    try:
        new_check_in = check_in_guest_models.Check_in(
            room_number=room_number,
            guest_name=check_in_request.guest_name,
            arrival_date=check_in_request.arrival_date,
            departure_date=check_in_request.departure_date,
            status="checked-in",
        )
        db.add(new_check_in)

        # Update room status to 'checked-in'
        room.status = "checked-in"
        db.commit()

        logger.info(f"Guest {check_in_request.guest_name} successfully checked into room {room_number}.")
        return {
            "message": f"Guest {check_in_request.guest_name} successfully checked into room {room_number}.",
            "check_in_details": {
                "guest_name": new_check_in.guest_name,
                "room_number": new_check_in.room_number,
                "arrival_date": new_check_in.arrival_date,
                "departure_date": new_check_in.departure_date,
                "status": new_check_in.status,
            },
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error during check-in process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/list/")
def list_checked_in_guests(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all guests currently checked into rooms, including their payment status.
    """
    try:
        checked_in_guests = (
            db.query(
                check_in_guest_models.Check_in.guest_name,
                check_in_guest_models.Check_in.room_number,
                func.date(check_in_guest_models.Check_in.arrival_date).label("check_in_date"),
                func.date(check_in_guest_models.Check_in.departure_date).label("departure_date"),
                check_in_guest_models.Check_in.payment_status,  # Include payment status
            )
            .filter(check_in_guest_models.Check_in.status == "checked-in")
            .all()
        )

        if not checked_in_guests:
            return {"message": "No guests are currently checked in."}

        formatted_guests = []
        for guest in checked_in_guests:
            formatted_guests.append({
                "guest_name": guest.guest_name,
                "room_number": guest.room_number,
                "check_in_date": guest.check_in_date.isoformat(),
                "departure_date": guest.departure_date.isoformat(),
                "payment_status": guest.payment_status,  # Include payment status in the response
            })

        return {
            "total_checked_in_guests": len(formatted_guests),
            "checked_in_guests": formatted_guests,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/update/")
def update_check_in(
    room_number: str,
    guest_name: str,
    updated_data: schemas.CheckInSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Update check-in details for a specific room number and guest name.
    """
    # Step 1: Fetch the check-in record
    check_in_record = db.query(check_in_guest_models.Check_in).filter(
        check_in_guest_models.Check_in.room_number == room_number,
        check_in_guest_models.Check_in.guest_name == guest_name,
    ).first()

    if not check_in_record:
        raise HTTPException(
            status_code=404,
            detail=f"No check-in record found for room {room_number} and guest {guest_name}.",
        )

    # Step 2: Validate the new arrival date
    if updated_data.arrival_date > date.today():
        raise HTTPException(
            status_code=400,
            detail="Check-in arrival date cannot be in the future.",
        )

    # Step 3: Update the fields with the new data
    check_in_record.room_number = updated_data.room_number
    check_in_record.guest_name = updated_data.guest_name
    check_in_record.arrival_date = updated_data.arrival_date
    check_in_record.departure_date = updated_data.departure_date

    # Step 4: Save the updated record
    try:
        db.commit()
        db.refresh(check_in_record)  # Refresh to reflect the updated record
        return {
            "message": "Check-in details updated successfully.",
            "updated_check_in": {
                "room_number": check_in_record.room_number,
                "guest_name": check_in_record.guest_name,
                "arrival_date": check_in_record.arrival_date,
                "departure_date": check_in_record.departure_date,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@router.post("/check-out/")
def check_out_guest(
    room_number: str,
    guest_name: Optional[str] = None,
    reason: Optional[str] = None,  # Optional parameter for checkout reason
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Check a guest out of a room.
    Optionally, a reason for checkout can be provided.
    """
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    query = db.query(check_in_guest_models.Check_in).filter(
        check_in_guest_models.Check_in.room_number == room_number,
        check_in_guest_models.Check_in.status == "checked-in",
    )

    if guest_name:
        query = query.filter(check_in_guest_models.Check_in.guest_name == guest_name)
    else:
        query = query.filter(func.date(check_in_guest_models.Check_in.departure_date) == func.current_date())

    check_ins = query.all()

    if not check_ins:
        raise HTTPException(
            status_code=404,
            detail=f"No active check-in found for room {room_number} and guest {guest_name or 'due for check-out today'}.",
        )

    try:
        for check_in in check_ins:
            check_in.status = "checked-out"
            check_in.is_checked_out = True  # Mark as checked out
            if reason:
                check_in.checkout_reason = reason  # Save the reason if provided

        active_check_ins = db.query(check_in_guest_models.Check_in).filter(
            check_in_guest_models.Check_in.room_number == room_number,
            check_in_guest_models.Check_in.status == "checked-in",
        ).count()

        if active_check_ins == 0:
            room.status = "available"

        db.commit()

        return {
            "message": f"Guest(s) successfully checked out of room {room_number}.",
            "checked_out_guests": [ci.guest_name for ci in check_ins],
            "room_status": room.status,
            "reason": reason if reason else "No reason provided",  # Include the reason in the response
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


