import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pytz
def parse_ai_schedule(schedule_text):
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

    # Regular expressions
    day_pattern = re.compile(r"[*•]\s*\*\*(\w+)\*\*")  # Match "**Monday**"
    event_pattern = re.compile(r"[*•]\s*(\d{1,2}:\d{2}(?:\s?[AP]M)?)-(\d{1,2}:\d{2}(?:\s?[AP]M)?)\s*:\s*(.+)")

    # Process each line
    for line in schedule_text.split("\n"):
        line = line.strip()
        
        # Match day headers like "**Monday**"
        day_match = day_pattern.match(line)
        if day_match:
            current_day = day_match.group(1)
            continue
            
        # Match event times and descriptions
        event_match = event_pattern.match(line)
        if event_match and current_day:
            start_time, end_time, activity = event_match.groups()

            # Convert time format to AM/PM
            def convert_time_format(time_str):
                try:
                    return datetime.strptime(time_str.strip(), "%I:%M %p").strftime("%I:%M %p")
                except ValueError:
                    return datetime.strptime(time_str.strip(), "%H:%M").strftime("%I:%M %p")

            start_time = convert_time_format(start_time)
            end_time = convert_time_format(end_time)

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

    return events

def add_to_calendar(creds_dict, parsed_data):
    try:
        # 1. Validate and prepare credentials
        if creds_dict["refresh_token"] == "null":
            creds_dict["refresh_token"] = None
            
        creds = Credentials(
            token=creds_dict["token"],
            refresh_token=creds_dict["refresh_token"],
            token_uri=creds_dict["token_uri"],
            client_id=creds_dict["client_id"],
            client_secret=creds_dict["client_secret"],
            scopes=creds_dict["scopes"]
        )
        
        # 2. Refresh token if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        # 3. Build service
        service = build("calendar", "v3", credentials=creds)
        timezone = pytz.timezone('Europe/Paris')
        
        # 4. Process events
        for event in parsed_data:
            try:
                # Parse datetimes
                start_naive = datetime.strptime(
                    f"{event['date']} {event['start_time']}", 
                    "%Y-%m-%d %I:%M %p"
                )
                end_naive = datetime.strptime(
                    f"{event['date']} {event['end_time']}", 
                    "%Y-%m-%d %I:%M %p"
                )
                
                # Localize and handle timezones
                start_dt = timezone.localize(start_naive)
                end_dt = timezone.localize(end_naive)
                
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                
                # Create event payload
                google_event = {
                    "summary": event["activity"],
                    "start": {
                        "dateTime": start_dt.isoformat(),
                        "timeZone": "Europe/Paris"
                    },
                    "end": {
                        "dateTime": end_dt.isoformat(),
                        "timeZone": "Europe/Paris"
                    }
                }
                
                # Insert and verify
                result = service.events().insert(
                    calendarId="primary",
                    body=google_event
                ).execute()
                
                print(f"✅ Event created: {result.get('htmlLink')}")
                print(f"Event ID: {result['id']}")
                
            except Exception as e:
                print(f"❌ Failed to add event {event}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"🔥 Critical error: {str(e)}")
        raise