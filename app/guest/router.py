from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import get_db
from app.guest import schemas, models  # Import guest-specific schemas and models
from app.users.auth import get_current_user
from sqlalchemy import or_
from app.rooms import models as room_models  # Import room models
from app.reservations import models as reservation_models  # Import reservation models

router = APIRouter()


@router.post("/check-in/")
def check_in_guest(
    check_in_request: schemas.CheckInSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Check a guest into a room.
    Ensures the room is available and no overlapping reservations exist.
    """
    room_number = check_in_request.room_number

    # Step 1: Validate room existence
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    # Step 2: Validate room status
    if room.status != "available":
        raise HTTPException(
            status_code=400, detail=f"Room {room_number} is not available for check-in."
        )

    # Step 3: Check for overlapping reservations
    overlapping_reservation = (
        db.query(reservation_models.Reservation)
        .filter(
            reservation_models.Reservation.room_number == room_number,
            or_(
                reservation_models.Reservation.arrival_date < check_in_request.departure_date,
                reservation_models.Reservation.departure_date > check_in_request.arrival_date,
            ),
        )
        .first()
    )
    if overlapping_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} is reserved or occupied during the requested dates.",
        )

    try:
        # Step 4: Create reservation and update room status
        new_reservation = reservation_models.Reservation(
            room_number=room_number,
            guest_name=check_in_request.guest_name,
            arrival_date=check_in_request.arrival_date,
            departure_date=check_in_request.departure_date,
            status="checked-in",
        )
        db.add(new_reservation)

        # Update room status to 'checked-in'
        room.status = "checked-in"
        db.commit()

        return {
            "message": f"Guest {check_in_request.guest_name} successfully checked into room {room_number}.",
            "reservation": {
                "guest_name": new_reservation.guest_name,
                "room_number": new_reservation.room_number,
                "arrival_date": new_reservation.arrival_date,
                "departure_date": new_reservation.departure_date,
                "status": new_reservation.status,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/checked-in/")
def list_checked_in_guests(db: Session = Depends(get_db)):
    """
    List all guests currently checked into rooms, along with their room numbers
    and check-in/check-out dates.
    """
    try:
        # Query for guests who are currently checked in
        checked_in_guests = (
            db.query(
                reservation_models.Reservation.guest_name,
                reservation_models.Reservation.room_number,
                func.date(reservation_models.Reservation.arrival_date).label("check_in_date"),
                func.date(reservation_models.Reservation.departure_date).label("departure_date"),
            )
            .filter(reservation_models.Reservation.status == "checked-in")
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
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Check a guest out of a room.
    Updates the reservation status to 'checked-out' and reverts the room status to 'available'.
    """
    # Step 1: Validate room existence
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    # Step 2: Validate current room status
    if room.status != "checked-in":
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} is not currently checked in.",
        )

    # Step 3: Find the active reservation for the room
    reservation = (
        db.query(reservation_models.Reservation)
        .filter(
            reservation_models.Reservation.room_number == room_number,
            reservation_models.Reservation.status == "checked-in",
        )
        .first()
    )
    if not reservation:
        raise HTTPException(
            status_code=400,
            detail=f"No active reservation found for room {room_number}.",
        )

    try:
        # Step 4: Update reservation status and room status
        reservation.status = "checked-out"
        room.status = "available"
        db.commit()

        return {
            "message": f"Guest {reservation.guest_name} successfully checked out of room {room_number}.",
            "reservation": {
                "guest_name": reservation.guest_name,
                "room_number": reservation.room_number,
                "check_in_date": reservation.arrival_date.isoformat(),
                "departure_date": reservation.departure_date.isoformat(),
                "status": reservation.status,
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
