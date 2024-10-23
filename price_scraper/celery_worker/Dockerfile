# Base Image
FROM python:3.9

# Set the working directory
WORKDIR /usr/src/app

# Install dependencies
COPY ../requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .
