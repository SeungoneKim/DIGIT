#!/bin/bash

# Example script to run the paper reviewer
# Make sure OpenHands API server is running before executing this script

echo "OpenHands Research Paper Reviewer - Example Run"
echo "=============================================="

# Check if OpenHands API is accessible
echo "Checking OpenHands API connectivity..."
curl -s http://localhost:3000/api/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ OpenHands API is accessible"
else
    echo "✗ OpenHands API is not accessible at http://localhost:3000"
    echo "Please ensure OpenHands API server is running"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the paper reviewer with example data
echo "Starting paper review..."
python paper_reviewer.py \
    --paper-file example_paper_data.json \
    --output-dir ./example_review_output

echo "Review completed! Check ./example_review_output for results."