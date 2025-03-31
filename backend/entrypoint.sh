#!/bin/bash

# Wait for the database to be ready
sleep 5

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Make migrations if tables don't exist (backup plan)
echo "Checking if tables exist..."
python -c "
import os
import psycopg2
import time
from django.conf import settings

# Get database configuration from settings
db_settings = settings.DATABASES['default']
db_name = db_settings.get('NAME')
db_user = db_settings.get('USER')
db_password = db_settings.get('PASSWORD')
db_host = db_settings.get('HOST')
db_port = db_settings.get('PORT')

# Connect to the database
try:
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()
    
    # Check if the events_event table exists
    cursor.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'events_event'
        );
    \"\"\")
    
    events_table_exists = cursor.fetchone()[0]
    
    if not events_table_exists:
        print('Tables do not exist. Running migrations again with more verbosity...')
        exit(1)
    else:
        print('Tables exist. Migration successful.')
        exit(0)
        
except Exception as e:
    print(f'Error checking database: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Tables don't exist. Trying again with more explicit migrations..."
    python manage.py makemigrations events
    python manage.py makemigrations invitations
    python manage.py makemigrations attendance
    python manage.py migrate
fi

# Verify migrations were applied
echo "Verifying migrations..."
python manage.py showmigrations

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create a superuser if none exists
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

# Start gunicorn server
echo "Starting gunicorn server..."
exec gunicorn qrcheckin.wsgi:application --bind 0.0.0.0:8000 --workers 2