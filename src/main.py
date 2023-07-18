from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import date
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine
import crud, models, schemas


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)       

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)


@app.get("/rooms/", response_model=list[schemas.Room])
def read_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rooms = crud.get_rooms(db, skip=skip, limit=limit)
    return rooms

@app.get("/reservations/{room_id}", response_model=list[schemas.Reservation])
def read_room_reservations(room_id: int, db: Session = Depends(get_db)):
    reservations = crud.get_room_reservations(db, room_id)
    return reservations

@app.get("/reservations/{room_id}/{date}", response_model=list[schemas.Reservation])
def read_room_reservations_by_date(room_id: int, date: date, db: Session = Depends(get_db)):
    reservations = crud.get_reservations_by_date(db, room_id, date)
    return reservations

@app.post("/reservations")
async def create_reservation_endpoint(request: Request, db: Session = Depends(get_db)):
    reservation_data = await request.json()
    room_id = reservation_data.get("room_id")
    from_time = reservation_data.get("from_time")
    to_time = reservation_data.get("to_time")
    title = reservation_data.get("title")
    description = reservation_data.get("description")

    reservation_date = reservation_data.get("reservation_date")

    reservation = crud.create_reservation(db, room_id, from_time, to_time, title, description, reservation_date)
    return {"message": "Reservation created successfully", "reservation": reservation}


# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user


# @app.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)


# @app.get("/items/", response_model=list[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items
