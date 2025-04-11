# Use an official Python runtime (slim image for smaller size)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy only requirements first (caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app (respects .dockerignore)
COPY . .

# Run the app (fixed CMD syntax)
CMD ["python", "app/main.py"]  