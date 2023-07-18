from pydantic import BaseModel
from datetime import date



        
class ReservationBase(BaseModel):
    id: int
    room_id: int
    


class ReservationCreate(ReservationBase):
    pass


class Reservation(ReservationBase):
    id: int
    room_id: int
    date: date
    from_time: str
    to_time: str
    title: str
    description: str

    class Config:
        orm_mode = True


class RoomBase(BaseModel):
    id: int


class RoomCreate(RoomBase):
    pass


class Room(RoomBase):
    

    class Config:
        orm_mode = True
