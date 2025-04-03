from fastapi import APIRouter
import os
router = APIRouter()

# Configure your client secrets
CLIENT_SECRETS_FILE = r"C:\Users\LENOVO\Desktop\Junior\calendar-assistant\backend\app\client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
# Ensure the file exists before proceeding
if not os.path.exists(CLIENT_SECRETS_FILE):
    raise FileNotFoundError(f"Error: {CLIENT_SECRETS_FILE} not found. Please check the file path.")
