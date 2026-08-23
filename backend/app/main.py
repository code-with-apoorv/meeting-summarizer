import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .database import init_db
from .routers import health, meetings

# Initialize Database tables
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent AI Meeting Summarizer with Multi-Provider ASR and LLM Action Items Extraction",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(meetings.router)

# Resolve Frontend Static Directory across local and cloud deployment environments
possible_frontend_paths = [
    Path(__file__).resolve().parent.parent.parent / "frontend",
    Path.cwd() / "frontend",
    Path(__file__).resolve().parent.parent / "frontend"
]

FRONTEND_DIR = None
for p in possible_frontend_paths:
    if p.exists() and (p / "index.html").exists():
        FRONTEND_DIR = p
        break

if FRONTEND_DIR:
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    async def serve_frontend_index():
        return FileResponse(FRONTEND_DIR / "index.html")
