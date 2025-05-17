#!/bin/bash
# run.sh - Simple script to start the Track Results Display application

echo "Starting Track Results Display..."
echo "-------------------------------------"
echo "Make sure you have installed all requirements with:"
echo "pip install -r requirements.txt"
echo "-------------------------------------"

# Create necessary directories if they don't exist
mkdir -p templates
mkdir -p static

# Check if Python is installed
if command -v python3 &>/dev/null; then
    python3 app.py
elif command -v python &>/dev/null; then
    python app.py
else
    echo "Error: Python not found. Please install Python 3.7 or higher."
    exit 1
fi