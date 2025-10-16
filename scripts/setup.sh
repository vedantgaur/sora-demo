#!/bin/bash
# Setup script for Sora Director

set -e  # Exit on error

echo "========================================="
echo "  Sora Director - Setup Script"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data/generations
mkdir -p data/reconstructions
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << EOF
# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
HOST=0.0.0.0

# Mode Configuration
USE_MOCK=true

# Data Storage
DATA_ROOT=./data

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/sora_director.log
EOF
    echo ".env file created with default values"
else
    echo ""
    echo ".env file already exists, skipping..."
fi

# Done
echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     python src/main.py"
echo ""
echo "  3. Open your browser to:"
echo "     http://localhost:5000"
echo ""
echo "========================================="

