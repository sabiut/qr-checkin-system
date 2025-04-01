#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create media subdirectories with proper permissions
echo "Setting up media directories..."
mkdir -p media/qrcodes media/tickets/html media/tickets/pdf
chmod -R 777 media  # This ensures write access for all users

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000