from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from app.database import get_db
from app.guest import schemas, models  # Import guest-specific schemas and models
from app.users.auth import get_current_user
from sqlalchemy import or_
from app.rooms import models as room_models  # Import room models
from app.reservations import models as reservation_models  # Import reservation models
from app.guest.crud import check_overlapping_check_in  # Import the function
from app.guest import schemas, models as guest_models

router = APIRouter()



@router.post("/check-in/")
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
        raise HTTPException(
            status_code=400,
            detail=(
                "Check-ins are only allowed for today's date. "
                "For future dates, please use the reservation endpoint."
            ),
        )
    if check_in_request.arrival_date < today:
        raise HTTPException(
            status_code=400,
            detail="Check-in cannot be performed for past dates.",
        )

    # Step 2: Validate room existence
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    # Step 3: Check for overlapping check-ins
    overlapping_check_in = check_overlapping_check_in(
        db=db,
        room_number=room_number,
        arrival_date=check_in_request.arrival_date,
        departure_date=check_in_request.departure_date,
    )

    if overlapping_check_in:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Room {room_number} is already checked-in by another guest during the requested dates. "
                f"Existing check-in: {overlapping_check_in.arrival_date} to {overlapping_check_in.departure_date}."
            ),
        )

    # Step 4: Create new check-in record
    try:
        new_check_in = guest_models.Check_in(
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
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/checked-in/")
def list_checked_in_guests(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all guests currently checked into rooms, along with their room numbers
    and check-in/check-out dates.
    """
    try:
        # Query for guests who are currently checked in
        checked_in_guests = (
            db.query(
                guest_models.Check_in.guest_name,
                guest_models.Check_in.room_number,
                func.date(guest_models.Check_in.arrival_date).label("check_in_date"),
                func.date(guest_models.Check_in.departure_date).label("departure_date"),
            )
            .filter(guest_models.Check_in.status == "checked-in")
            .all()
        )

        # If no guests are checked in, return a message
        if not checked_in_guests:
            return {"message": "No guests are currently checked in."}

        # Format the response
        formatted_guests = []
        for guest in checked_in_guests:
            formatted_guests.append({
                "guest_name": guest.guest_name,
                "room_number": guest.room_number,
                "check_in_date": (
                    guest.check_in_date.isoformat() if hasattr(guest.check_in_date, "isoformat") else guest.check_in_date
                ),
                "departure_date": (
                    guest.departure_date.isoformat() if hasattr(guest.departure_date, "isoformat") else guest.departure_date
                ),
            })

        return {
            "total_checked_in_guests": len(formatted_guests),
            "checked_in_guests": formatted_guests,
        }

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving checked-in guests: {str(e)}",
        )

@router.post("/check-out/")
def check_out_guest(
    room_number: str,
    guest_name: str = None,  # Optional: Specific guest for backdated check-out
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Check out a guest from a room.
    - If `guest_name` is provided, targets a specific guest.
    - Without `guest_name`, checks out the guest(s) due today.
    """
    # Step 1: Validate room existence
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    # Step 2: Find active reservations/check-ins for the room
    query = db.query(guest_models.Check_in).filter(
        guest_models.Check_in.room_number == room_number,
        guest_models.Check_in.status == "checked-in",
    )

    if guest_name:
        # Target specific guest
        query = query.filter(guest_models.Check_in.guest_name == guest_name)
    else:
        # Target guests due for check-out today
        query = query.filter(func.date(guest_models.Check_in.departure_date) == func.current_date())

    check_ins = query.all()

    if not check_ins:
        raise HTTPException(
            status_code=404,
            detail=(f"No active check-in found for room {room_number} "
                    + (f"and guest {guest_name}." if guest_name else "due for check-out today.")),
        )

    try:
        # Step 3: Mark check-in records as 'checked-out'
        for check_in in check_ins:
            check_in.status = "checked-out"
            db.delete(check_in)  # Remove the record after checking out

        # Step 4: Update room status
        active_check_ins = db.query(guest_models.Check_in).filter(
            guest_models.Check_in.room_number == room_number,
            guest_models.Check_in.status == "checked-in",
        ).count()

        if active_check_ins == 0:
            room.status = "available"

        db.commit()

        return {
            "message": f"Guest(s) successfully checked out of room {room_number}.",
            "checked_out_guests": [ci.guest_name for ci in check_ins],
            "room_status": room.status,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
