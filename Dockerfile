# Use the latest Python 3.14-slim image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies needed for psycopg2 (PostgreSQL client)
# This is crucial for connecting to your database from Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]