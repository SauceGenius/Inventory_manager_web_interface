# Use the official Python image as a base image
FROM python:3.11.4

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

# Copy the rest of the application code into the container
COPY . .

# Copy .env file
COPY .env .env

# Copy the certificates
COPY certs /app/certs

# Expose the port the app runs on
EXPOSE 80

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

# Run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]