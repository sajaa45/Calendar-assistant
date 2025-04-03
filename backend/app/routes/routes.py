from fastapi import APIRouter, HTTPException, Request, Depends
from app.services.openai_service import generate_schedule
from sqlalchemy.orm import Session
from app.models.schemas import ScheduleRequest, ScheduleResponse
from app.services.google_calendar import parse_ai_schedule, add_to_calendar
from app.oauth.google_auth import CLIENT_SECRETS_FILE, SCOPES
from google_auth_oauthlib.flow import Flow
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from app.models.schemas import GoogleOAuthToken
from google.oauth2.credentials import Credentials
from ..database.db import get_db
from urllib.parse import quote_plus
import uuid
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
import re
router = APIRouter()

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#ise HTTPException(status_code=500, detail=str(e))


#@router.post("/generate_and_sync")
#async def generate_and_sync(
#    request: Request,
#    schedule_request: ScheduleRequest
#):  
#    # 1. Get AI schedule
#    ai_response = generate_schedule(schedule_request.user_events, schedule_request.free_time)
#    print(ai_response)
#    if not isinstance(ai_response, dict) or "schedule" not in ai_response:
#            raise ValueError("Invalid response format from AI model")
#
#    schedule_text = ai_response["schedule"]
#    #print("Parsed events:", ai_response)
#    # 2. Parse to calendar events
#    #try:
#    #    events = parse_schedule_text(ai_response["schedule"])
#    #    
#    #except Exception as e:
#    #    raise HTTPException(status_code=400, detail=f"Failed to parse schedule: {str(e)}")
#    #
#    # 3. Add to Google Calendar
#    #creds = request.session.get("google_creds")
#    #if not creds:
#    #    raise HTTPException(status_code=401, detail="Not authenticated with Google")
#    #
#    #try:
#    #    add_to_calendar(creds, events)
#    #except Exception as e:
#    #    raise HTTPException(status_code=500, detail=f"Failed to add to calendar: {str(e)}")
#    #
#    return {
#        "message": "Schedule generated successfully",
#        "schedule": schedule_text
#    #    #"events": events,
#    #    #"count": len(events)
#    }

from fastapi import Body, HTTPException

# Store the latest schedule as a string
latest_schedule: str = ""  

@router.post("/generate_schedule",  response_model=ScheduleResponse)
def schedule(request: ScheduleRequest):

    if not request.user_events:
        raise HTTPException(status_code=400, detail="At least one event is required")
    
    if not request.free_time:
        raise HTTPException(status_code=400, detail="At least one free time slot is required")
    
    try:
        generated_schedule  = generate_schedule(request.user_events, request.free_time)  
        
        if not isinstance(latest_schedule, str):
            raise ValueError("AI response should be a string")
        
        return ScheduleResponse(schedule=generated_schedule)  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_and_sync")
async def generate_and_sync(request: ScheduleResponse,
            db: Session = Depends(get_db)):  
    if not request.schedule:
        raise HTTPException(status_code=400, detail="Schedule cannot be empty.")

    try:
        events = parse_schedule_text(request.schedule.get("schedule"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse schedule: {str(e)}")
    token = db.query(GoogleOAuthToken).first()
    if not token or not token.access_token:
        print("[ERROR] Google Authentication Token Missing!")
        raise HTTPException(status_code=401, detail="Not authenticated with Google")
    
    # 4. Prepare credentials dictionary
    creds = {
        "token": token.access_token,
        "refresh_token": token.refresh_token if token.refresh_token else None,
        "token_uri": token.token_uri,
        "client_id": token.client_id,
        "client_secret": token.client_secret,
        "scopes": token.scopes.split(",") if token.scopes else []
    }
    print("[4/6] Google Credentials Retrieved Successfully")
    try:
        print("[5/6] Adding events to Google Calendar...")
        add_to_calendar(creds, events)
        print("[6/6] Successfully added events to Google Calendar")
    except Exception as e:
        print("[ERROR] Failed to add events to Google Calendar:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add to calendar: {str(e)}")
    
    return {
        "message": "Schedule generated successfully",
        "schedule": events
    }
import re
from datetime import datetime, timedelta

import re
from datetime import datetime, timedelta
def parse_schedule_text(schedule_text):
    """Parses the schedule text into structured Google Calendar events."""
    events = []
    current_day = None
    
    # Find the upcoming Monday to start assigning dates
    today = datetime.now()
    next_monday = today + timedelta(days=(0 - today.weekday()) % 7)
    
    date_mapping = {  
        "Monday": next_monday,  
        "Tuesday": next_monday + timedelta(days=1),  
        "Wednesday": next_monday + timedelta(days=2),  
        "Thursday": next_monday + timedelta(days=3),  
        "Friday": next_monday + timedelta(days=4),  
        "Saturday": next_monday + timedelta(days=5),  
        "Sunday": next_monday + timedelta(days=6),  
    }

    # Regular expressions for both formats
    day_pattern = re.compile(r"^[*•]\s+(?:\*\*)?(\w+)(?:\*\*)?$")  # Matches both "* **Monday**" and "*   Monday"
    event_pattern = re.compile(r"^\s*[*•]\s+(?:\*\*)?(\d{1,2}:\d{2}\s[AP]M)(?:\*\*)?-(?:\*\*)?(\d{1,2}:\d{2}\s[AP]M)(?:\*\*)?\s*:\s*(.+)$")

    # Process each line
    for line in schedule_text.split("\n"):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
        
        # Match day headers in both formats
        day_match = day_pattern.match(line)
        if day_match:
            day_name = day_match.group(1)
            if day_name in date_mapping:
                current_day = day_name
            continue
            
        # Match event times and descriptions in both formats
        if current_day:
            event_match = event_pattern.match(line)
            if event_match:
                start_time, end_time, activity = event_match.groups()

                # Clean time strings (remove ** if present)
                start_time = start_time.replace("**", "").strip()
                end_time = end_time.replace("**", "").strip()

                try:
                    # Convert to datetime objects
                    start_dt = datetime.strptime(f"{date_mapping[current_day].date()} {start_time}", "%Y-%m-%d %I:%M %p")
                    end_dt = datetime.strptime(f"{date_mapping[current_day].date()} {end_time}", "%Y-%m-%d %I:%M %p")
                    
                    # Append event data
                    events.append({
                        "date": date_mapping[current_day].strftime("%Y-%m-%d"),
                        "start_time": start_dt.strftime("%I:%M %p"),
                        "end_time": end_dt.strftime("%I:%M %p"),
                        "activity": activity.strip()
                    })
                except ValueError as e:
                    print(f"Skipping event due to time format error: {e}")
                    continue

    return events
@router.get("/auth/check")
async def check_google_auth(db: Session = Depends(get_db)):
    """
    Check if the user is authenticated with Google.
    """
    token = db.query(GoogleOAuthToken).order_by(GoogleOAuthToken.expiry.desc()).first()
    
    if token and token.access_token:
        return JSONResponse(content={"authenticated": True})
    
    return JSONResponse(content={"authenticated": False})

@router.get("/auth/google")
async def auth_google(request: Request):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/callback"
    )
    
    # 👇 THIS IS THE MAGIC COMBO THAT FORCES REFRESH TOKENS
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="false"
    )
    
    # Store state for security
    request.session["oauth_state"] = state
    print("🔥 Generated auth URL:", authorization_url)  # Debug
    return RedirectResponse(authorization_url)
@router.get("/test-cors")
async def test_cors():
    return {"message": "CORS test"}
@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    try:
        # State verification
        if state != request.session.get("oauth_state"):
            raise HTTPException(status_code=400, detail="Invalid state")
            
        # Initialize flow
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri="http://localhost:8000/auth/callback"
        )
        
        # Exchange code for tokens
        flow.fetch_token(
            code=code,
            client_secret=flow.client_config["client_secret"],
            # 👇 Keep consistent with auth endpoint
            access_type="offline",
            prompt="consent"  
        )
        
        # DEBUG: Print token details
        print("🔑 Token Details:", {
            "access_token": bool(flow.credentials.token),
            "refresh_token": bool(flow.credentials.refresh_token),
            "expiry": flow.credentials.expiry
        })
        
        # Enforce refresh token requirement
        if not flow.credentials.refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Google didn't provide refresh token. Try in incognito mode."
            )
            
        # Store token
        db.query(GoogleOAuthToken).delete()
        db.add(GoogleOAuthToken(
            id=str(uuid.uuid4()),
            access_token=flow.credentials.token,
            refresh_token=flow.credentials.refresh_token,
            token_uri=flow.credentials.token_uri,
            client_id=flow.credentials.client_id,
            client_secret=flow.client_config["client_secret"],
            scopes=",".join(flow.credentials.scopes),
            expiry=flow.credentials.expiry
        ))
        db.commit()
        
        return RedirectResponse("http://localhost:4200?auth_success=true")
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(f"http://localhost:4200/error?message={str(e)}")
@router.get("/debug/tokens")
async def debug_tokens(db: Session = Depends(get_db)):
    try:
        tokens = db.query(GoogleOAuthToken).all()
        
        token_list = []
        for token in tokens:
            # Safely handle all fields
            token_data = {
                "token": token.access_token,
                "refresh_token": token.refresh_token if token.refresh_token else None,  
                "token_uri": token.token_uri,
                "client_id": token.client_id,
                "client_secret": token.client_secret,
                "scopes": token.scopes.split(",") if token.scopes else [],
                "expiry": token.expiry.isoformat() if token.expiry else None
            }
            token_list.append(token_data)
        
        return {"count": len(token_list), "tokens": token_list}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving tokens: {str(e)}"
        )
@router.get("/auth/verify")
async def verify_token(db: Session = Depends(get_db)):
    token = db.query(GoogleOAuthToken).first()
    if not token:
        raise HTTPException(status_code=404, detail="No token found")
    
    return {
        "has_refresh": bool(token.refresh_token),
        "expires_in": (token.expiry - datetime.utcnow()).total_seconds() if token.expiry else None,
        "scopes": token.scopes.split(",") if token.scopes else []
    }