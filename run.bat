@echo off
REM Quick start script for RCA Competitor Analysis App
REM This script sets up and runs the Streamlit application

echo ========================================
echo RCA Competitor Analysis - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and fill in your credentials.
    echo.
    echo Press any key to create .env from template...
    pause > nul
    copy .env.example .env
    echo.
    echo .env file created. Please edit it with your credentials before running again.
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
echo.

REM Run the app
echo ========================================
echo Starting Streamlit app...
echo The app will open in your browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo ========================================
echo.

streamlit run app.py

REM Deactivate virtual environment on exit
deactivate
