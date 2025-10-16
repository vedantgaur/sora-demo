#!/bin/bash
# Run script for Sora Director

set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using default configuration."
fi

# Run the application
echo "Starting Sora Director..."
echo "========================================="
python src/main.py

