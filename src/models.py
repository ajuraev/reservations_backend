from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    reservations = relationship("Reservation", back_populates="room")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    title = Column(String)
    description = Column(String)
    from_time = Column(String)
    to_time = Column(String)
    room_id = Column(Integer, ForeignKey("rooms.id"))

    room = relationship("Room", back_populates="reservations")
