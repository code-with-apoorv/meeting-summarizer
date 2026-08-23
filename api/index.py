import os
import sys
from pathlib import Path

# Add project root and backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

if "PYTHONPATH" in os.environ:
    os.environ["PYTHONPATH"] = f"{ROOT_DIR}:{ROOT_DIR / 'backend'}:{os.environ['PYTHONPATH']}"
else:
    os.environ["PYTHONPATH"] = f"{ROOT_DIR}:{ROOT_DIR / 'backend'}"

from backend.app.main import app
