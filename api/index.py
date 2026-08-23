import sys
from pathlib import Path

# Add project root to sys.path for Vercel Serverless runtime
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.main import app
