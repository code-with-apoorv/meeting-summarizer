from fastapi import APIRouter
from ..config import settings
from ..schemas import HealthResponse

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        configured_providers={
            "groq": bool(settings.GROQ_API_KEY),
            "openai": bool(settings.OPENAI_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "offline_demo_engine": True
        }
    )
