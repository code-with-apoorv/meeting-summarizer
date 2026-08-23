import pytest
import os
from pathlib import Path
from backend.app.services.asr_service import asr_service
from backend.samples.generate_sample_audio import create_synthetic_wav

@pytest.mark.asyncio
async def test_asr_fallback_transcription():
    # Generate a temporary test wav
    test_wav = create_synthetic_wav("test_temp.wav", duration_sec=1)
    
    transcript, provider = await asr_service.transcribe(str(test_wav), provider="mock")
    
    assert transcript is not None
    assert len(transcript) > 50
    assert "Alice" in transcript or "Meeting" in transcript
    assert provider is not None
    
    if os.path.exists(test_wav):
        os.remove(test_wav)

def test_detect_provider():
    provider = asr_service.detect_provider("auto")
    assert provider in ["groq", "openai", "gemini", "mock"]
