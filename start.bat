@echo off
REM Micro Gallery Japan - Backend Start Script (Windows)

echo 🚀 Starting Micro Gallery Japan Backend...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Copying from .env.example...
    copy .env.example .env
    echo ⚠️  Please update .env with your Supabase credentials!
    pause
    exit /b 1
)

REM Run the application
echo ✅ Starting FastAPI server...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
