from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.users.auth import get_current_user
from app.database import get_db
from typing import Optional
from app.reservations import schemas, models  # Import reservation-specific schemas and models
from app.rooms import schemas, models
from app.reservations import schemas as reservation_schemas, models as reservation_models
from app.rooms import schemas as room_schemas, models as room_models
from sqlalchemy import and_
from app.reservations.crud import check_overlapping_check_in, check_overlapping_reservations
from app.users import schemas
from datetime import date
from app.users.schemas import UserDisplaySchema  # Ensure correct import
from app.check_in_guest import models as check_in_models  # Ensure this exists
from loguru import logger


router = APIRouter()


logger.add("app.log", rotation="500 MB", level="DEBUG")

@router.post("/")
def create_reservation(
    reservation: reservation_schemas.ReservationSchema,
    db: Session = Depends(get_db),
):
    # Validate mandatory fields
    if not reservation.room_number:
        raise HTTPException(status_code=400, detail="Room number is required.")
    
    if reservation.arrival_date > reservation.departure_date:
        raise HTTPException(
            status_code=400, 
            detail="Arrival date must be before or on the same day as the departure date."
        )
    
    # Ensure the reservation is for a future date
    if reservation.arrival_date <= date.today():
        raise HTTPException(
            status_code=400,
            detail="Reservations can only be used for future dates. Use the check-in functionality instead."
        )
    
    # Validate if the room exists
    room = db.query(room_models.Room).filter(room_models.Room.room_number == reservation.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    # Check if the room is already checked in
    checked_in_reservation = check_overlapping_check_in(
        db=db,
        room_number=reservation.room_number,
        arrival_date=reservation.arrival_date,
        departure_date=reservation.departure_date
    )
    if checked_in_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is already checked in by another guest "
                   f"from {checked_in_reservation.arrival_date} to {checked_in_reservation.departure_date}."
        )
    
    # Check for overlapping reservations or active check-ins for the same room
    overlapping_reservation = check_overlapping_reservations(
        db=db,
        room_number=reservation.room_number,
        arrival_date=reservation.arrival_date,
        departure_date=reservation.departure_date
    )
    if overlapping_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is already occupied or reserved from "
                   f"{overlapping_reservation.arrival_date} to {overlapping_reservation.departure_date}.",
        )

    # Check if the room is under maintenance
    if room.status == "maintenance":
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is under maintenance and cannot be reserved.",
        )
    
    try:
        # Create a new reservation
        new_reservation = reservation_models.Reservation(
            room_number=reservation.room_number,
            guest_name=reservation.guest_name,
            arrival_date=reservation.arrival_date,
            departure_date=reservation.departure_date,
            status="reserved",
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
        
        # Update room status to "reserved"
        room.status = "reserved"
        db.commit()

        return {"message": "Reservation created successfully.", "reservation": new_reservation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/list/", response_model=reservation_schemas.ReservedRoomsListSchema)
def list_reserved_rooms(
    db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Querying the reserved rooms, excluding canceled reservations
        reserved_rooms = (
            db.query(
                room_models.Room.room_number,
                room_models.Room.room_type,
                reservation_models.Reservation.guest_name,
                reservation_models.Reservation.arrival_date,
                reservation_models.Reservation.departure_date,
            )
            .join(
                reservation_models.Reservation,
                room_models.Room.room_number == reservation_models.Reservation.room_number
            )
            .filter(
                room_models.Room.status == "reserved",
                reservation_models.Reservation.is_deleted == False  # Exclude canceled reservations
            )
            .all()
        )

        # Structuring the response
        return {
            "total_reserved_rooms": len(reserved_rooms),
            "reserved_rooms": [
                {
                    "room_number": room.room_number,
                    "room_type": room.room_type,
                    "guest_name": room.guest_name,
                    "arrival_date": room.arrival_date,
                    "departure_date": room.departure_date,
                }
                for room in reserved_rooms
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/update/")
def update_reservation(
    room_number: str,
    guest_name: str,
    updated_data: reservation_schemas.ReservationSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Update reservation details for a specific room number and guest name.
    """
    # Step 1: Fetch the reservation record
    reservation_record = db.query(reservation_models.Reservation).filter(
        reservation_models.Reservation.room_number == room_number,
        reservation_models.Reservation.guest_name == guest_name,
    ).first()

    if not reservation_record:
        raise HTTPException(
            status_code=404,
            detail=f"No reservation record found for room {room_number} and guest {guest_name}.",
        )

    # Step 2: Validate the new arrival date
    if updated_data.arrival_date <= date.today():
        raise HTTPException(
            status_code=400,
            detail="Reservation arrival date must be a future date.",
        )

    # Step 3: Update the fields with the new data
    reservation_record.room_number = updated_data.room_number
    reservation_record.guest_name = updated_data.guest_name
    reservation_record.arrival_date = updated_data.arrival_date
    reservation_record.departure_date = updated_data.departure_date

    # Step 4: Save the updated record
    try:
        db.commit()
        db.refresh(reservation_record)  # Refresh to reflect the updated record
        return {
            "message": "Reservation details updated successfully.",
            "updated_reservation": {
                "room_number": reservation_record.room_number,
                "guest_name": reservation_record.guest_name,
                "arrival_date": reservation_record.arrival_date,
                "departure_date": reservation_record.departure_date,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.delete("/cancel/")
def cancel_reservation(
    room_number: str,
    guest_name: str,
    cancellation_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Cancel a reservation with a reason.
    """
    try:
        reservation = db.query(reservation_models.Reservation).filter(
            reservation_models.Reservation.room_number == room_number,
            reservation_models.Reservation.guest_name == guest_name,
            reservation_models.Reservation.is_deleted == False
        ).first()

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail=f"No reservation found for room {room_number} and guest {guest_name}."
            )

        if current_user.role != "admin" and reservation.guest_name != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to cancel this reservation."
            )

        reservation.is_deleted = True
        reservation.cancellation_reason = cancellation_reason
        db.commit()

        remaining_reservations = db.query(reservation_models.Reservation).filter(
            reservation_models.Reservation.room_number == room_number,
            reservation_models.Reservation.is_deleted == False
        ).count()

        if remaining_reservations == 0:
            room = db.query(room_models.Room).filter(
                room_models.Room.room_number == room_number
            ).first()
            if room:
                room.status = "available"
                db.commit()

        return {
            "message": f"Reservation for room {room_number} and guest {guest_name} canceled successfully.",
            "cancellation_reason": cancellation_reason,
            "room_status": "available" if remaining_reservations == 0 else "reserved",
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while canceling the reservation: {str(e)}",
        )




@router.get("/transaction-history/")
def transaction_history(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user: UserDisplaySchema = Depends(get_current_user),
):
    try:
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be earlier than or equal to end date."
            )

        checked_out_query = db.query(
            check_in_models.Check_in.room_number,
            check_in_models.Check_in.guest_name,
            check_in_models.Check_in.arrival_date,
            check_in_models.Check_in.departure_date,
            check_in_models.Check_in.checkout_reason,
        ).filter(check_in_models.Check_in.is_checked_out.is_(True))

        deleted_reservation_query = db.query(
            reservation_models.Reservation.room_number,
            reservation_models.Reservation.guest_name,
            reservation_models.Reservation.arrival_date,
            reservation_models.Reservation.departure_date,
            reservation_models.Reservation.cancellation_reason,
        ).filter(reservation_models.Reservation.is_deleted.is_(True))

        if start_date:
            checked_out_query = checked_out_query.filter(check_in_models.Check_in.departure_date >= start_date)
            deleted_reservation_query = deleted_reservation_query.filter(
                reservation_models.Reservation.departure_date >= start_date
            )
        if end_date:
            checked_out_query = checked_out_query.filter(check_in_models.Check_in.departure_date <= end_date)
            deleted_reservation_query = deleted_reservation_query.filter(
                reservation_models.Reservation.departure_date <= end_date
            )

        checked_out_records = checked_out_query.all()
        deleted_reservation_records = deleted_reservation_query.all()

        transaction_history = [
            {
                "transaction_type": "checked-out",
                "room_number": record.room_number,
                "guest_name": record.guest_name,
                "arrival_date": record.arrival_date,
                "departure_date": record.departure_date,
                "checkout_reason": record.checkout_reason,
            }
            for record in checked_out_records
        ] + [
            {
                "transaction_type": "deleted-reservation",
                "room_number": record.room_number,
                "guest_name": record.guest_name,
                "arrival_date": record.arrival_date,
                "departure_date": record.departure_date,
                "cancellation_reason": record.cancellation_reason,  # Include cancellation reason
            }
            for record in deleted_reservation_records
        ]

        return {
            "total_transactions": len(transaction_history),
            "transactions": transaction_history,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
