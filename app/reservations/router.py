from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.users.auth import get_current_user
from app.database import get_db
from app.reservations import schemas, models  # Import reservation-specific schemas and models
from app.rooms import schemas, models
from app.reservations import schemas as reservation_schemas, models as reservation_models
from app.rooms import schemas as room_schemas, models as room_models
from sqlalchemy import and_


router = APIRouter()



def check_overlapping_reservations(db: Session, room_number: str, arrival_date, departure_date):
    """
    Checks if a given room has overlapping reservations within the specified date range.
    """
    overlapping_reservation = db.query(reservation_models.Reservation).filter(
        reservation_models.Reservation.room_number == room_number,
        and_(
            reservation_models.Reservation.arrival_date <= departure_date,
            reservation_models.Reservation.departure_date >= arrival_date
        )
    ).first()
    return overlapping_reservation

@router.post("/")
def create_reservation(reservation: reservation_schemas.ReservationSchema, db: Session = Depends(get_db)):
    if not reservation.room_number or not reservation.guest_name:
        raise HTTPException(status_code=400, detail="Room number and guest name are required.")
    
    if reservation.arrival_date > reservation.departure_date:
        raise HTTPException(status_code=400, detail="Arrival date must be before or on the same day as the departure date.")
    
    room = db.query(room_models.Room).filter(room_models.Room.room_number == reservation.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check for overlapping reservations
    overlapping_reservation = check_overlapping_reservations(
        db=db,
        room_number=reservation.room_number,
        arrival_date=reservation.arrival_date,
        departure_date=reservation.departure_date
    )
    
    if room.status == "reserved" and overlapping_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is already reserved from "
                   f"{overlapping_reservation.arrival_date} to {overlapping_reservation.departure_date}.",
        )
    
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
        
        # Update room status to reserved
        room.status = "reserved"
        db.commit()

        return {"message": "Reservation created successfully", "reservation": new_reservation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@router.get("/reserved", response_model=reservation_schemas.ReservedRoomsListSchema)
def list_reserved_rooms(db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Querying the reserved rooms
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
            .filter(room_models.Room.status == "reserved")
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




@router.delete("/{room_number}")
def delete_or_cancel_reservation(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: reservation_schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Deletes or cancels a reservation for a given room number. 
    Admins can delete any reservation, while users can only cancel their own reservations.
    """
    try:
        # Fetch the reservation
        reservation = db.query(reservation_models.Reservation).filter(
            reservation_models.Reservation.room_number == room_number
        ).first()

        if not reservation:
            raise HTTPException(
                status_code=404, detail=f"No reservation found for room number {room_number}."
            )

        # Admins can delete any reservation; regular users can cancel their own
        if current_user.role != "admin" and reservation.guest_name != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this reservation.",
            )

        # Fetch the associated room
        room = db.query(room_models.Room).filter(
            room_models.Room.room_number == room_number
        ).first()

        if not room:
            raise HTTPException(
                status_code=404, detail=f"No room found for room number {room_number}."
            )

        # Delete the reservation and update the room's status
        db.delete(reservation)
        room.status = "available"  # Assumes room is now free; adjust if needed
        db.commit()

        return {
            "message": f"Reservation for room {room_number} successfully deleted/canceled.",
            "room_status": room.status,
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the reservation: {str(e)}",
        )
