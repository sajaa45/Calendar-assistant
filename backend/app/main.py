from fastapi import FastAPI
from app.routes.routes import router
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import Base, engine  
import secrets
import os
from pathlib import Path

# Ensure instance directory exists
instance_path = Path("./instance")
os.makedirs(instance_path, exist_ok=True)

# Create tables before starting the app
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    session_cookie="session_cookie",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Your Angular URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "This is the updated FastAPI app with database support!"}
