from sqlalchemy import Table, Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from database import Base



class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    reservations = relationship("Reservation", back_populates="room")


# Association Table
reservation_participant_table = Table('reservation_participant', Base.metadata,
    Column('reservation_id', ForeignKey('reservations.id'), primary_key=True),
    Column('participant_id', ForeignKey('participants.id'), primary_key=True)
)


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    reservations = relationship(
        "Reservation",
        secondary=reservation_participant_table,
        back_populates="participants",
    )


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
    participants = relationship(
        "Participant",
        secondary=reservation_participant_table,
        back_populates="reservations",
    )
