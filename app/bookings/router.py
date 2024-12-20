from fastapi import APIRouter, HTTPException, Depends
from fastapi import Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from app.database import get_db
from typing import Optional  # Import for optional parameters
#from app.guest import schemas, models  # Import guest-specific schemas and models
from app.users.auth import get_current_user
from sqlalchemy import or_
from sqlalchemy import and_
from app.rooms import models as room_models  # Import room models
#from app.bookings.crud import check_overlapping_check_in  # Import the function
from app.bookings import schemas, models as  booking_models
from app.payments import models as payment_models
from loguru import logger

router = APIRouter()


logger.add("app.log", rotation="500 MB", level="DEBUG")




@router.post("/create/")
def create_booking(
    booking_request: schemas.BookingSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Create a booking for either reservation (R) or check-in (C).
    Ensures room availability and prevents overlapping bookings.
    """
    room_number = booking_request.room_number
    today = date.today()

    # Step 1: Validate booking dates
    if booking_request.departure_date < booking_request.arrival_date:
        raise HTTPException(
            status_code=400,
            detail="Departure date must be later than the arrival date.",
        )

    # Step 2: Validate booking type and dates
    if booking_request.booking_type == "C":  # Check-in
        if booking_request.arrival_date != today:
            raise HTTPException(
                status_code=400,
                detail="Check-in bookings can only be made for today's date.",
            )
    elif booking_request.booking_type == "R":  # Reserved
        if booking_request.arrival_date <= today:
            raise HTTPException(
                status_code=400,
                detail="Reserved bookings must be for a future date. Use the check-in option for today's booking.",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid booking type. Use 'C' for check-in or 'R' for reserved.",
        )

    # Step 3: Prevent past dates
    if booking_request.arrival_date < today:
        raise HTTPException(
            status_code=400, detail="Bookings cannot start in the past."
        )

    # Step 4: Check room existence
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found.")

    # Step 5: Check for overlapping bookings
    overlapping_booking = db.query(booking_models.Booking).filter(
        booking_models.Booking.room_number == room_number,
        booking_models.Booking.status != "checked-out",  # Do not consider 'checked-out' rooms
        or_(
            # Check for overlap with existing bookings
            and_(
                booking_models.Booking.arrival_date < booking_request.departure_date,
                booking_models.Booking.departure_date > booking_request.arrival_date,
            )
        )
    ).first()

    if overlapping_booking:
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} is already booked for the requested dates.",
        )

    # Step 6: Create new booking
    try:
        new_booking = booking_models.Booking(
            room_number=room_number,
            guest_name=booking_request.guest_name,
            arrival_date=booking_request.arrival_date,
            departure_date=booking_request.departure_date,
            booking_type=booking_request.booking_type,
            status="reserved" if booking_request.booking_type == "R" else "checked-in",
            room_price=room.amount,  # Include room price
        )
        db.add(new_booking)

        # Update room status
        room.status = "reserved" if booking_request.booking_type == "R" else "checked-in"
        db.commit()
        db.refresh(new_booking)

        return {
            "message": f"Booking created successfully for room {room_number}.",
            "booking_details": {
                "id": new_booking.id,
                "room_number": new_booking.room_number,
                "guest_name": new_booking.guest_name,
                "arrival_date": new_booking.arrival_date,
                "departure_date": new_booking.departure_date,
                "booking_type": new_booking.booking_type,
                "status": new_booking.status,
                "room_price": new_booking.room_price,  # Include room price in response
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/list/")
def list_bookings(
    limit: int = Query(10, ge=1),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all active bookings with updated payment status:
    - Pending: No payment made
    - Incomplete Payment: Payment made but balance remains
    - Payment Completed: Full payment made
    - Voided: Payment was voided
    Supports pagination with limit and skip.
    """
    bookings = db.query(booking_models.Booking).filter(
        booking_models.Booking.status != "checked-out"
    ).offset(skip).limit(limit).all()

    formatted_bookings = []
    for booking in bookings:
        # Calculate total payments made for this booking
        total_paid = db.query(func.sum(payment_models.Payment.amount_paid)).filter(
            payment_models.Payment.booking_id == booking.id,
            payment_models.Payment.status != "voided",  # Exclude voided payments
        ).scalar() or 0

        # Determine payment status
        if total_paid == 0:
            payment_status = "pending"
        elif total_paid < booking.room_price:
            payment_status = "incomplete payment"
        else:
            payment_status = "payment completed"

        # Update booking payment status in the database if it has changed
        if payment_status != booking.payment_status:
            booking.payment_status = payment_status
            db.commit()

        formatted_bookings.append({
            "id": booking.id,
            "room_number": booking.room_number,
            "guest_name": booking.guest_name,
            "arrival_date": booking.arrival_date,
            "departure_date": booking.departure_date,
            "number_of_days": booking.number_of_days,
            "booking_type": booking.booking_type,
            "status": booking.status,
            "payment_status": booking.payment_status,  # Updated payment status
        })

    return {
        "total_bookings": len(formatted_bookings),
        "bookings": formatted_bookings,
    }


@router.get("/list_by_id/{booking_id}/")
def list_booking_by_id(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Retrieve a specific booking by booking ID with updated payment status:
    - Pending: No payment made
    - Incomplete Payment: Payment made but balance remains
    - Payment Completed: Full payment made
    - Voided: Payment was voided
    """
    # Fetch the booking by ID
    booking = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found.")

    # Calculate total payments made for this booking
    total_paid = db.query(func.sum(payment_models.Payment.amount_paid)).filter(
        payment_models.Payment.booking_id == booking.id,
        payment_models.Payment.status != "voided",  # Exclude voided payments
    ).scalar() or 0

    # Determine payment status
    if total_paid == 0:
        payment_status = "pending"
    elif total_paid < booking.room_price:
        payment_status = "incomplete payment"
    else:
        payment_status = "payment completed"

    # Update booking payment status in the database if it has changed
    if payment_status != booking.payment_status:
        booking.payment_status = payment_status
        db.commit()

    # Format the response
    formatted_booking = {
        "id": booking.id,
        "room_number": booking.room_number,
        "guest_name": booking.guest_name,
        "arrival_date": booking.arrival_date,
        "departure_date": booking.departure_date,
        "number_of_days": booking.number_of_days,
        "booking_type": booking.booking_type,
        "status": booking.status,
        "payment_status": booking.payment_status,  # Updated payment status
    }

    return {
        "message": f"Booking details for ID {booking_id} retrieved successfully.",
        "booking": formatted_booking,
    }



@router.get("/list_by_date/")
def list_bookings_by_date(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List bookings filtered by an optional date range (start_date and end_date),
    with updated payment status:
    - Pending: No payment made
    - Incomplete Payment: Payment made but balance remains
    - Payment Completed: Full payment made
    - Voided: Payment was voided
    """
    try:
        # Build the base query
        query = db.query(booking_models.Booking).filter(
            booking_models.Booking.status != "checked-out"
        )

        # Apply date filters if provided
        if start_date:
            query = query.filter(booking_models.Booking.arrival_date >= start_date)
        if end_date:
            query = query.filter(booking_models.Booking.departure_date <= end_date)

        bookings = query.all()

        formatted_bookings = []
        for booking in bookings:
            # Fetch payment details for the booking
            payment = db.query(payment_models.Payment).filter(
                payment_models.Payment.booking_id == booking.id
            ).first()

            # Determine payment status
            if not payment:
                payment_status = "pending"
            elif payment.status == "voided":  # Check if payment is voided
                payment_status = "pending"  # Revert to pending to allow further payments
            elif payment.balance_due > 0:
                payment_status = "incomplete payment"
            else:
                payment_status = "payment completed"

            # Update booking payment status in the database if it has changed
            if payment_status != booking.payment_status:
                booking.payment_status = payment_status
                db.commit()

            formatted_bookings.append({
                "id": booking.id,
                "room_number": booking.room_number,
                "guest_name": booking.guest_name,
                "arrival_date": booking.arrival_date,
                "departure_date": booking.departure_date,
                "booking_type": booking.booking_type,
                "status": booking.status,
                "payment_status": booking.payment_status,  # Updated payment status
            })

        return {
            "total_bookings": len(formatted_bookings),
            "bookings": formatted_bookings,
        }

    except Exception as e:
        logger.error(f"Error retrieving bookings by date: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving bookings: {str(e)}",
        )


@router.put("/update/")
def update_booking(
    booking_id: int,
    updated_data: schemas.BookingSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Update booking details (reservation or check-in) by booking ID.
    """
    booking = db.query(booking_models.Booking).filter(booking_models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found.")

    # Step 1: Update booking fields
    for field, value in updated_data.dict(exclude_unset=True).items():
        setattr(booking, field, value)

    try:
        db.commit()
        db.refresh(booking)
        return {"message": "Booking updated successfully.", "updated_booking": booking}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/check-out/")
def check_out_booking(
    booking_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Check out a guest from a room.
    Optionally, a reason for checkout can be provided.
    """
    booking = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id, booking_models.Booking.status == "checked-in"
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail=f"No active check-in found for booking ID {booking_id}.")

    try:
        booking.status = "checked-out"
        booking.is_checked_out = True
        booking.cancellation_reason = reason

        # Update room status
        room = db.query(room_models.Room).filter(room_models.Room.room_number == booking.room_number).first()
        if room:
            room.status = "available"

        db.commit()
        return {
            "message": f"Guest successfully checked out of room {booking.room_number}.",
            "room_status": "available",
            "reason": reason or "No reason provided",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
