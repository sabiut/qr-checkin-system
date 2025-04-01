#!/usr/bin/env python
"""
Test script for checking ticket model fields
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qrcheckin.settings')
django.setup()

from invitations.models import Invitation

def print_model_fields():
    """Print the Invitation model fields to verify the changes"""
    print("Invitation model fields:")
    for field in Invitation._meta.get_fields():
        print(f"- {field.name}: {field.__class__.__name__}")

if __name__ == "__main__":
    print_model_fields()