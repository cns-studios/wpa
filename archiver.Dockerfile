# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install cron
RUN apt-get update && apt-get -y install cron

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Add crontab file to the cron directory
ADD crontab /etc/cron.d/archiver-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/archiver-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
