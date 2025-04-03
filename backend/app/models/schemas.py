from pydantic import BaseModel
from typing import List
from sqlalchemy import Column, String, Integer, DateTime
from ..database.db import Base
from typing import List, Dict
class UserEvent(BaseModel):
    event_name: str

class FreeTimeSlot(BaseModel):
    start: str  # Again, `datetime` is recommended
    end: str

class ScheduleRequest(BaseModel):
    user_events: List[UserEvent]
    free_time: List[FreeTimeSlot]
class ScheduleResponse(BaseModel):
    schedule: dict  
class GoogleOAuthToken(Base):
    __tablename__ = "google_oauth_tokens"
    
    id = Column(String, primary_key=True)  # Changed from Integer to String
    user_id = Column(String)  
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)  # Explicitly nullable
    token_uri = Column(String)
    client_id = Column(String)
    client_secret = Column(String)
    scopes = Column(String) 
    expiry = Column(DateTime, nullable=True)
