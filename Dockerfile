# Use an official lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file from the backend directory
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend AND frontend directories into the container
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Set the working directory to the backend folder
WORKDIR /app/backend

# Expose the port Cloud Run expects
ENV PORT=8080
EXPOSE 8080

# Command to run the application using the $PORT environment variable
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}