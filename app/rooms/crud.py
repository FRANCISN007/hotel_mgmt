from sqlalchemy.orm import Session
from app.rooms import models, schemas



def create_room(db: Session, room: schemas.RoomSchema):
    db_room = models.Room(
        room_number=room.room_number,
        room_type=room.room_type,
        amount=room.amount,
        status=room.status
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

