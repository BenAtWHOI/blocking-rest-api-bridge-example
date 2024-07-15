FROM python:3.11-slim

# Set the working directory in the container

WORKDIR /app/example

COPY requirements.txt .

# Install the dependencies

RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory

COPY . /app

EXPOSE 8000

# Apply migrations and start the Django app
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
