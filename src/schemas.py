from pydantic import BaseModel
from datetime import date
from typing import List


class ParticipantBase(BaseModel):
    email: str


class Participant(ParticipantBase):
    id: int

    class Config:
        orm_mode = True


class ReservationBase(BaseModel):
    room_id: int
    date: date
    from_time: str
    to_time: str
    title: str
    description: str
    participants: List[Participant] = []
    created_by: str


class Reservation(ReservationBase):
    id: int

    class Config:
        orm_mode = True


class RoomBase(BaseModel):
    pass  # You might want to add fields here if your Room has any


class RoomCreate(RoomBase):
    pass  # You might want to add fields here if your Room creation process requires any


class Room(RoomBase):
    id: int
    reservations: List[Reservation] = []

    class Config:
        orm_mode = True
