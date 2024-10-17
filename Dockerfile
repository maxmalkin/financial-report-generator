# Dockerfile

# Use the official Python image from Docker Hub
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Copy requirements file to the container
COPY requirements.txt /code/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the container
COPY . /code/

# Run migrations and collect static files at build time (optional)
RUN python manage.py collectstatic --noinput

# Expose port 8000 for Django app
EXPOSE 5432

# Command to run the Django server
CMD ["gunicorn", "mybackend.wsgi:application", "--bind", "0.0.0.0:8000"]
