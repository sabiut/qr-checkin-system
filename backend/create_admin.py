#!/usr/bin/env python
"""
Script to create a default admin user for the QR check-in system.
Run with: python create_admin.py
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qrcheckin.settings')
django.setup()

# Now import Django models
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

def create_admin_user():
    """Create admin user if one doesn't exist."""
    try:
        if User.objects.filter(username='admin').exists():
            print("Admin user already exists")
            # Set password for existing admin
            admin = User.objects.get(username='admin')
            admin.set_password('admin123')
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            print("Reset admin password to 'admin123'")
        else:
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print("Created admin user with password 'admin123'")
    except IntegrityError:
        print("Admin user already exists")
    except Exception as e:
        print(f"Error creating admin user: {e}")

if __name__ == '__main__':
    create_admin_user()