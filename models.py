from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String(50))

    
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    room_number = Column(String, unique=True, nullable=False)
    room_type = Column(String(50))
    amount= Column(Integer)
    status = Column(String(50))

    reservations = relationship("Reservation", back_populates="room")




class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, ForeignKey("rooms.room_number"), nullable=False)
    guest_name = Column(String(100), nullable=False)
    arrival_date = Column(DateTime, nullable=False)
    departure_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)

    room = relationship("Room", back_populates="reservations")

