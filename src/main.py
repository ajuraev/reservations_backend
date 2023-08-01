from fastapi import Depends, FastAPI, HTTPException, Request, status, Query, Security
from sqlalchemy.orm import Session
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi_login import LoginManager
from fastapi.security import OAuth2PasswordBearer

from pydantic import BaseModel
from typing import List
from datetime import datetime
import pytz
import os
import requests

from googleapiclient.discovery import build
from google.auth.transport.requests import Request as RequestAuth
from google.oauth2.credentials import Credentials
from fastapi.middleware.cors import CORSMiddleware
from google_auth_oauthlib.flow import Flow
from starlette.responses import JSONResponse
from googleapiclient.discovery import build
from database import SessionLocal, engine
import crud, models, schemas
import re



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

class AuthCode(BaseModel):
    code: str

@app.get("/verify")
async def verify_token(token: str = None, refresh_token: str = None):
    os.environ["CLIENT_ID"] = "584370108370-gu51j6u432c3gdicmu723dnei97en9ai.apps.googleusercontent.com"
    os.environ["CLIENT_SECRET"] = "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"

    response = requests.get('https://oauth2.googleapis.com/tokeninfo', params={'access_token': token})
    if response.status_code == 200:
        users = get_user_emails({"token": token, "refresh_token": refresh_token})
        return {"users": users}
    else:
        raise HTTPException(status_code=400, detail="Token is invalid")
    
@app.post("/auth/google")
async def get_google_token(auth_code: AuthCode):
    try:
        # This creates the Flow using a client_secrets.json file
        flow = Flow.from_client_secrets_file(
            "client_secret.json",
            scopes=[
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/contacts",
                "https://www.googleapis.com/auth/contacts.other.readonly",
                "https://www.googleapis.com/auth/calendar.events",
                "openid"
            ],
            redirect_uri='https://booking.safiabakery.uz'
        )
        #https://reservations-front.vercel.app
        #http://localhost:3000
        flow.fetch_token(code=auth_code.code)


        

        credentials = flow.credentials
        return JSONResponse(content={
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
        })
    except Exception as e:
        print(e)

def is_valid_email(email):
    email_regex = r"[^@]+@[^@]+\.[^@]+"  # This is a simple email regex
    return re.match(email_regex, email) is not None

def get_user_emails(auth_info):
    # Initialize the Google API client with the access token
    
    try:
        
        creds = Credentials.from_authorized_user_info({
            'access_token': auth_info.get("token"),
            'client_id' : os.environ.get('CLIENT_ID'),
            'refresh_token' : auth_info.get("refresh_token"),
            'client_secret' : os.environ.get('CLIENT_SECRET')
            })
        service = build('people', 'v1', credentials=creds)

    
        #create_event(auth_info, None)
        users = []

        results = service.people().connections().list(
        resourceName='people/me',
        pageSize=2000,
        personFields='emailAddresses,names',
        ).execute()

        contacts = results.get('connections', [])
        for person in contacts:
            user = {}
            email_addresses = person.get('emailAddresses', [])
            if email_addresses:
                email = email_addresses[0].get('value')
                if is_valid_email(email):
                    user['Email'] = email
                    names = person.get('names', [])
                    if names:
                        user['Name'] = names[0].get('displayName')
                    users.append(user)

        results = service.otherContacts().list(
        pageSize=1000,
        readMask='emailAddresses,names',
        ).execute()

        other_contacts = results.get('otherContacts', [])
        for person in other_contacts:
            user = {}
            email_addresses = person.get('emailAddresses', [])
            if email_addresses:
                email = email_addresses[0].get('value')
                if is_valid_email(email):
                    user['Email'] = email
                    names = person.get('names', [])
                    if names:
                        user['Name'] = names[0].get('displayName')
                    users.append(user)
        
        return users
    except Exception as e:
        print(e)

def format_date(date_string):
    # parse the date string into a datetime object
    date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')

    # assuming the date_string is in UTC, convert it to a naive datetime object (removing timezone info)
    date = date.replace(tzinfo=pytz.UTC)

    # convert the datetime object to the desired timezone
    date = date.astimezone(pytz.timezone('Asia/Tashkent'))

    # format the datetime object as a string
    formatted_date = date.isoformat()

    return formatted_date

def create_event(auth_info, res_data):
    os.environ["CLIENT_ID"] = "584370108370-gu51j6u432c3gdicmu723dnei97en9ai.apps.googleusercontent.com"
    os.environ["CLIENT_SECRET"] = "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"
    try:
        creds = Credentials.from_authorized_user_info({
            'access_token': auth_info.token,
            'client_id' : os.environ.get('CLIENT_ID'),
            'refresh_token' : auth_info.refresh_token,
            'client_secret' : os.environ.get('CLIENT_SECRET')
        })
        service = build('calendar', 'v3', credentials=creds)

        event = {
        'summary': res_data.title,
        'location': 'Conference room #1',
        'description': res_data.description,
        'start': {
            'dateTime': format_date(res_data.from_time),
            'timeZone': 'Asia/Tashkent',
        },
        'end': {
            'dateTime': format_date(res_data.to_time),
            'timeZone': 'Asia/Tashkent',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        if res_data.participants:
            event['attendees'] = [{'email': attendee_email} for attendee_email in res_data.participants]


        event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        print(f'Event created: {event.get("htmlLink")}')
    except Exception as e:
        print(e)

# @app.post("/user/emails/")
# def get_emails_from_token(auth_info: AuthInfo):
#     try:
#         users = get_user_emails(auth_info)
#         return {"users": users}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/reservations/{reservation_id}", response_model=schemas.Reservation)
def read_reservation_by_id(reservation_id: int, db: Session = Depends(get_db)):
    reservation = crud.get_reservation_by_id(db, reservation_id)

    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return reservation

@app.get("/reservations")
def read_reservations_by_room(room_id: int = None, all: bool = Query(None), db: Session = Depends(get_db)):
    reservations = crud.get_reservations_by_room(db, room_id, all)

    return reservations



@app.get("/rooms/", response_model=list[schemas.Room])
def read_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rooms = crud.get_rooms(db, skip=skip, limit=limit)
    return rooms



# @app.get("/reservations/{room_id}/{date}", response_model=list[schemas.Reservation])
# def read_room_reservations_by_date(room_id: int, date: date, db: Session = Depends(get_db)):
#     reservations = crud.get_reservations_by_date(db, room_id, date)
#     return reservations


class AccessToken(BaseModel):
    token: str
    refresh_token: str

class Reservation_data(BaseModel):
    room_id: str
    from_time: str
    to_time: str
    title: str
    description: str
    participants: List[str]
    reservation_date: str
    access_token: AccessToken



@app.post("/reservations")
async def create_reservation_endpoint(reservation_data: Reservation_data,db: Session = Depends(get_db)):
    try:
        room_id = reservation_data.room_id
        from_time = reservation_data.from_time
        to_time = reservation_data.to_time
        title = reservation_data.title
        description = reservation_data.description
        participants = reservation_data.participants
        access_token = reservation_data.access_token
        reservation_date = reservation_data.reservation_date
 
        response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', 
                                headers={'Authorization': f'Bearer {access_token.token}'})
        userinfo = response.json()
        email = userinfo['email']


        reservation = crud.create_reservation(db, room_id, from_time, to_time, title, description, reservation_date, participants, email)
        create_event(access_token, reservation_data)
        return {"message": "Reservation created successfully", "reservation": reservation}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))




# Delete endpoint
@app.delete("/reservations/{reservation_id}")
async def delete_reservation(
    reservation_id: int, 
    token: str,
    db: Session = Depends(get_db), 
    ):    
    reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()

    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo?alt=json', 
                                headers={'Authorization': f'Bearer {token}'})
    if not response.ok:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    decoded_token = response.json()
    if 'email' in decoded_token:
        created_by = decoded_token['email']
    else:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    if reservation.created_by != created_by:
        raise HTTPException(status_code=403, detail="Not authorized to delete this reservation")

    db.delete(reservation)
    db.commit()

    return {"message": "Reservation deleted successfully"}