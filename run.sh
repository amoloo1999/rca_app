#!/bin/bash
# Quick start script for RCA Competitor Analysis App (Mac/Linux)
# This script sets up and runs the Streamlit application

echo "========================================"
echo "RCA Competitor Analysis - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials."
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo ".env file created. Please edit it with your credentials before running again."
    exit 1
fi

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet --disable-pip-version-check
echo ""

# Run the app
echo "========================================"
echo "Starting Streamlit app..."
echo "The app will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

streamlit run app.py

# Deactivate virtual environment on exit
deactivate
