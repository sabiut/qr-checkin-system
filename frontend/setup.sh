#!/bin/bash

# Create app directory if it doesn't exist
mkdir -p app

# Copy files from src/app to app
cp -r src/app/* app/

# Tell the user what happened
echo "Setup complete! Files copied from src/app to app directory."