#!/bin/bash

# Micro Gallery Japan - Backend Start Script

echo "🚀 Starting Micro Gallery Japan Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your Supabase credentials!"
    exit 1
fi

# Run the application
echo "✅ Starting FastAPI server..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
