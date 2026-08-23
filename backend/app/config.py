import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Try loading .env if python-dotenv is present
try:
    from dotenv import load_dotenv
    env_path = WORKSPACE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

class Settings:
    APP_NAME: str = "AI Meeting Summarizer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Storage
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/meetings.db"
    UPLOAD_DIR: Path = UPLOAD_DIR
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Default Providers: "auto", "groq", "openai", "gemini", "mock"
    DEFAULT_ASR_PROVIDER: str = os.getenv("DEFAULT_ASR_PROVIDER", "auto")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "auto")
    
    MAX_FILE_SIZE_MB: int = 50

settings = Settings()
