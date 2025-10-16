#!/bin/bash
# Test script for Sora Director

set -e  # Exit on error

echo "========================================="
echo "  Running Tests"
echo "========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
echo "Running pytest with coverage..."
pytest --cov=src --cov-report=html --cov-report=term tests/

echo ""
echo "========================================="
echo "  Test Complete!"
echo "========================================="
echo ""
echo "Coverage report generated in htmlcov/index.html"

