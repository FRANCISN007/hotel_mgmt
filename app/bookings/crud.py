from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.bookings import models as booking_models

def check_overlapping_check_in(
    db: Session,
    room_number: str,
    arrival_date,
    departure_date,
):
    """
    Check if there are overlapping check-ins for the given room and date range.
    
    Args:
        db (Session): The database session.
        room_number (str): The room number to check.
        arrival_date (date): The requested arrival date.
        departure_date (date): The requested departure date.

    Returns:
        guest_models.Check_in | None: The overlapping check-in if found, otherwise None.
    """
    overlapping_check_in = db.query(booking_models.Booking).filter(
        booking_models.Booking.room_number == room_number,
        booking_models.Booking.status == "checked-in",
        or_(
            booking_models.Booking.arrival_date <= departure_date,
            booking_models.Booking.departure_date >= arrival_date,
        )
    ).first()

    return overlapping_check_in


