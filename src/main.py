from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi_login import LoginManager
from pydantic import BaseModel
from typing import List
from datetime import datetime
import pytz
import os
import requests

from googleapiclient.discovery import build
from google.auth.transport.requests import Request as RequestAuth
from google.oauth2.credentials import Credentials
from starlette.responses import JSONResponse
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

class AuthInfo(BaseModel):
    access_token: str
    client_id: str
    refresh_token: str
    client_secret: str

@app.get("/verify/")
def verify_token(token):
    try:
        response = requests.get('https://oauth2.googleapis.com/tokeninfo', params={'access_token': token})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Token is invalid')
    except Exception as e:
        print(e)
    
@app.post("/auth/google")
async def get_google_token(auth_code: AuthCode):
    # This creates the Flow using a client_secrets.json file
    flow = Flow.from_client_secrets_file(
        "/etc/secrets/client_secret.json",
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/contacts",
            "https://www.googleapis.com/auth/contacts.other.readonly",
            "https://www.googleapis.com/auth/calendar.events",
            "openid"
        ],
        redirect_uri='https://reservations-front.vercel.app/'
    )

    flow.fetch_token(code=auth_code.code)

    credentials = flow.credentials

    return JSONResponse(content={
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    })

def is_valid_email(email):
    email_regex = r"[^@]+@[^@]+\.[^@]+"  # This is a simple email regex
    return re.match(email_regex, email) is not None

def get_user_emails(auth_info):
    # Initialize the Google API client with the access token
    creds = Credentials.from_authorized_user_info({
        'access_token': auth_info.access_token,
        'client_id' : auth_info.client_id,
        'refresh_token' : auth_info.refresh_token,
        'client_secret' : auth_info.client_secret
        })
    service = build('people', 'v1', credentials=creds)

    
    try:
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
        # your date string
    #date_string = 'Wed Jul 26 2023 17:00:00 GMT+0300 (GMT+03:00)'

    # strip off the '(GMT+03:00)' part
    date_string = date_string.split(' (')[0]

    # parse the date string into a datetime object
    date = datetime.strptime(date_string, '%a %b %d %Y %H:%M:%S %Z%z')

    # convert the datetime object to the desired timezone
    date = date.astimezone(pytz.timezone('Asia/Tashkent'))

    # format the datetime object as a string
    formatted_date = date.strftime('%Y-%m-%dT%H:%M:%S%z')

    # insert the colon for the timezone offset
    formatted_date = formatted_date[:-2] + ':' + formatted_date[-2:]

    return formatted_date

def create_event(auth_info, res_data):
    try:
        creds = Credentials.from_authorized_user_info({
            'access_token': auth_info.get('token'),
            'client_id' : auth_info.get('client_id'),
            'refresh_token' : auth_info.get('refresh_token'),
            'client_secret' : auth_info.get('client_secret')
        })

        service = build('calendar', 'v3', credentials=creds)

        event = {
        'summary': res_data.get('title'),
        'location': 'Conference room #1',
        'description': res_data.get('description'),
        'start': {
            'dateTime': format_date(res_data.get('from_time')),
            'timeZone': 'Asia/Tashkent',
        },
        'end': {
            'dateTime': format_date(res_data.get('to_time')),
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

        if res_data.get('participants'):
            event['attendees'] = [{'email': attendee_email} for attendee_email in res_data.get('participants')]


        event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        print(f'Event created: {event.get("htmlLink")}')
    except Exception as e:
        print(e)

@app.post("/user/emails/")
def get_emails_from_token(auth_info: AuthInfo):
    try:
        users = get_user_emails(auth_info)
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

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
    participants = reservation_data.get("participants")

    token = reservation_data.get("access_token")

    reservation_date = reservation_data.get("reservation_date")

    reservation = crud.create_reservation(db, room_id, from_time, to_time, title, description, reservation_date, participants)
    create_event(token, reservation_data)
    return {"message": "Reservation created successfully", "reservation": reservation}