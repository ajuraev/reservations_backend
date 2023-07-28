from sqlalchemy.orm import Session, joinedload
from datetime import date
from typing import List

import models, schemas

def get_room_reservations(db: Session, room_id: int):
    return db.query(models.Reservation).join(models.Reservation.room).filter(models.Room.id == room_id).all()

def get_reservation_by_id(db: Session, reservation_id: int):
    return db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()

def get_reservations_by_room(db: Session, room_id: int, all: bool):
    if room_id is None:
        return db.query(models.Reservation).options(joinedload(models.Reservation.participants)).all()
    elif all:
        return db.query(models.Reservation).options(joinedload(models.Reservation.participants)).join(models.Reservation.room).filter(models.Room.id == room_id).all()
    else:
        return db.query(models.Reservation).options(joinedload(models.Reservation.participants)).join(models.Reservation.room).filter(models.Room.id == room_id, models.Reservation.date >= date.today()).all()
    
    
def get_reservations_by_date(db: Session, room_id: int, date: str):
    return db.query(models.Reservation).join(models.Reservation.room).filter(models.Room.id == room_id, models.Reservation.date == date).all()

def create_reservation(db: Session, room_id: int, from_time: str, to_time: str, title: str, description: str, reservation_date: date, participant_emails: List[str], created_by: str):
    reservation = models.Reservation(room_id=room_id, from_time=from_time, to_time=to_time, date=reservation_date, title=title, description=description, created_by=created_by)
    db.add(reservation)
    db.commit()

    participants = []
    for email in participant_emails:
        user = db.query(models.Participant).filter(models.Participant.email == email).first()
        if user is None:
            # User does not exist, so create a new User
            user = models.Participant(email=email)
            db.add(user)
        participants.append(user)

    db.commit()

    # Add participants to the reservation
    reservation.participants = participants

    db.commit()
    db.refresh(reservation)

    return reservation



def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Room).offset(skip).limit(limit)
