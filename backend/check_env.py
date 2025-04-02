#!/usr/bin/env python
"""
Script to check if environment variables from .env are loaded correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Define the current directory and parent directory
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = SCRIPT_DIR / '.env'

# Print current working directory for debugging
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {SCRIPT_DIR}")
print(f"Looking for .env file at: {ENV_FILE_PATH}")
print(f".env file exists: {ENV_FILE_PATH.exists()}")

# Try to load the .env file
load_dotenv(ENV_FILE_PATH)
print(f"Loaded .env file from {ENV_FILE_PATH}")

# Check critical email settings
email_settings = {
    'EMAIL_BACKEND': os.environ.get('EMAIL_BACKEND', ''),
    'EMAIL_HOST': os.environ.get('EMAIL_HOST', ''),
    'EMAIL_PORT': os.environ.get('EMAIL_PORT', ''),
    'EMAIL_USE_TLS': os.environ.get('EMAIL_USE_TLS', ''),
    'EMAIL_HOST_USER': os.environ.get('EMAIL_HOST_USER', ''),
    'EMAIL_HOST_PASSWORD': os.environ.get('EMAIL_HOST_PASSWORD', '***' if os.environ.get('EMAIL_HOST_PASSWORD') else ''),
    'DEFAULT_FROM_EMAIL': os.environ.get('DEFAULT_FROM_EMAIL', ''),
}

print("\nEmail Environment Variables:")
for key, value in email_settings.items():
    # Hide actual password but show if it's set
    if key == 'EMAIL_HOST_PASSWORD':
        if value:
            print(f"{key}: (password is set)")
        else:
            print(f"{key}: (not set)")
    else:
        print(f"{key}: {value}")

print("\n.env file exists and is loaded correctly!" if ENV_FILE_PATH.exists() else "\n.env file not found!")