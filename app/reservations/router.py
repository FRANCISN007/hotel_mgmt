from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.users.auth import get_current_user
from app.database import get_db
from app.reservations import schemas, models  # Import reservation-specific schemas and models

router = APIRouter()


@router.get("/reserved")
def list_reserved_rooms(db: Session = Depends(get_db)):
    reserved_rooms = (
        db.query(
            models.Room.room_number,
            models.Room.room_type,
            models.Reservation.guest_name,
            models.Reservation.arrival_date,
            models.Reservation.departure_date,
        )
        .join(models.Reservation, models.Room.room_number == models.Reservation.room_number)
        .filter(models.Room.status == "reserved")
        .all()
    )

    total_reserved_rooms = len(reserved_rooms)
    return {
        "total_reserved_rooms": total_reserved_rooms,
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


@router.post("/")
def create_reservation(reservation: schemas.ReservationSchema, db: Session = Depends(get_db)):
    if not reservation.room_number or not reservation.guest_name:
        raise HTTPException(status_code=400, detail="Room number and guest name are required.")

    room = db.query(models.Room).filter(models.Room.room_number == reservation.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.status != "available":
        raise HTTPException(status_code=400, detail=f"Room {reservation.room_number} is not available for reservation.")

    existing_reservation = db.query(models.Reservation).filter(
        models.Reservation.room_number == reservation.room_number,
        models.Reservation.arrival_date <= reservation.departure_date,
        models.Reservation.departure_date >= reservation.arrival_date,
    ).first()

    if existing_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} is already reserved from "
                   f"{existing_reservation.arrival_date} to {existing_reservation.departure_date}.",
        )

    try:
        new_reservation = models.Reservation(
            room_number=reservation.room_number,
            guest_name=reservation.guest_name,
            arrival_date=reservation.arrival_date,
            departure_date=reservation.departure_date,
            status="reserved",
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)

        room.status = "reserved"
        db.commit()

        return {"message": "Reservation created successfully", "reservation": new_reservation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/check-out-group/")
def check_out_multiple_rooms(
    room_numbers: list[str],
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    results = []

    for room_number in room_numbers:
        room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
        if not room:
            results.append({"room_number": room_number, "status": "error", "message": "Room does not exist."})
            continue

        reservation = db.query(models.Reservation).filter(
            models.Reservation.room_number == room_number,
            models.Reservation.status == "booked",
        ).first()

        if not reservation:
            results.append({"room_number": room_number, "status": "error", "message": "Room is not currently booked."})
            continue

        try:
            reservation.status = "checked-out"
            db.commit()

            room.status = "available"
            db.commit()

            results.append({"room_number": room_number, "status": "success", "message": f"Room {room_number} successfully checked out."})
        except Exception as e:
            db.rollback()
            results.append({"room_number": room_number, "status": "error", "message": str(e)})

    return {"results": results}


@router.delete("/{room_number}")
def delete_reservation_or_check_in(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to delete reservations.")

    reservation = db.query(models.Reservation).filter(models.Reservation.room_number == room_number).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="No reservation found for the specified room number.")

    try:
        room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found for the specified room number.")

        db.delete(reservation)
        room.status = "available"
        db.commit()

        return {
            "message": f"Reservation or check-in for room {room_number} has been successfully deleted.",
            "room_status": room.status,
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the reservation: {str(e)}")
