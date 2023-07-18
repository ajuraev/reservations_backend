from sqlalchemy.orm import Session
from datetime import date

import models, schemas


# def get_room_reservations(db: Session, room_id: int):
#     return db.query(models.Room).filter(models.Room.id == room_id).all()


def get_room_reservations(db: Session, room_id: int):
    return db.query(models.Reservation).join(models.Reservation.room).filter(models.Room.id == room_id).all()

def get_reservations_by_date(db: Session, room_id: int, date: str):
    return db.query(models.Reservation).join(models.Reservation.room).filter(models.Room.id == room_id, models.Reservation.date == date).all()

def create_reservation(db: Session, room_id: int, start_hour: int, end_hour: int):
    return db.query

def create_reservation(db: Session, room_id: int, from_time: str, to_time: str, title: str, description: str, reservation_date: date):
    reservation = models.Reservation(room_id=room_id, from_time=from_time, to_time=to_time, date=reservation_date, title=title, description=description)
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Room).offset(skip).limit(limit)

# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item
