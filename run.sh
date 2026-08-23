#!/bin/bash
set -e

echo "==================================================="
echo "  MeetPulse AI - Meeting Summarizer Starting Up"
echo "==================================================="
echo ""

if ! command -v python3 &> /dev/null
then
    echo "[ERROR] python3 could not be found. Please install Python 3.9+"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[2/3] Activating virtual environment & installing dependencies..."
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

echo "[3/3] Generating sample test audio..."
python backend/samples/generate_sample_audio.py

echo ""
echo "==================================================="
echo "  Server is running at: http://localhost:8000"
echo "  API Docs available at: http://localhost:8000/docs"
echo "==================================================="
echo ""

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
