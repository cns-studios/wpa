# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Make port 4444 available to the world outside this container
EXPOSE 4444

# Define environment variable
ENV FLASK_APP server.py

# Run the command to start the server
CMD ["flask", "run", "--host=0.0.0.0", "--port=4444"]
