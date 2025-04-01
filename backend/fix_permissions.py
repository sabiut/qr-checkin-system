#!/usr/bin/env python

import os
import stat

# Script to fix media directory permissions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')

# Create directories if they don't exist
print(f"Creating directories in {MEDIA_DIR}...")
os.makedirs(os.path.join(MEDIA_DIR, 'tickets', 'html'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, 'tickets', 'pdf'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, 'qrcodes'), exist_ok=True)

# Set permissions (mode 0777) to allow all users to read, write, and execute
for root, dirs, files in os.walk(MEDIA_DIR):
    print(f"Setting permissions for {root}...")
    try:
        os.chmod(root, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO) # This is 0777
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Setting permissions for file {file_path}...")
            os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except Exception as e:
        print(f"Error setting permissions: {str(e)}")

print("Done. Please run this with appropriate permissions if you see errors.")