# Use the official Python 3.9 Alpine base image
FROM python:3.9-alpine

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed to build and run the Python application
RUN apk add --no-cache gcc musl-dev libffi-dev

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app.py file to the working directory
COPY app.py .

# Command to run the server when the container starts
CMD ["gunicorn", "-w 1", "-b 0.0.0.0:5454", "app:app"]
