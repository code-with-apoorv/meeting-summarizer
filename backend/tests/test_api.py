import pytest
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.samples.generate_sample_audio import create_synthetic_wav

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "configured_providers" in data

def test_text_summarize_api():
    payload = {
        "text": "Alice: We approved the new design. Bob will implement it by Friday.",
        "title": "Design Review Meeting"
    }
    response = client.post("/api/meetings/text-summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Design Review Meeting"
    assert len(data["action_items"]) > 0
    return data["id"]

def test_list_and_get_meetings():
    # Ensure at least one meeting exists
    payload = {"text": "Team sync: Bob is writing tests."}
    client.post("/api/meetings/text-summarize", json=payload)

    # List
    response = client.get("/api/meetings")
    assert response.status_code == 200
    meetings = response.json()
    assert isinstance(meetings, list)
    assert len(meetings) > 0

    first_id = meetings[0]["id"]

    # Get Single
    get_res = client.get(f"/api/meetings/{first_id}")
    assert get_res.status_code == 200
    m = get_res.json()
    assert m["id"] == first_id

def test_action_item_toggle():
    payload = {"text": "Action items: David will renew SSL certs by Thursday."}
    res = client.post("/api/meetings/text-summarize", json=payload)
    m = res.json()
    assert len(m["action_items"]) > 0

    item_id = m["action_items"][0]["id"]
    patch_res = client.patch(
        f"/api/meetings/{m['id']}/action-items/{item_id}",
        json={"status": "completed"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

def test_export_formats():
    payload = {"text": "Decision: Launch product on Sept 15th."}
    res = client.post("/api/meetings/text-summarize", json=payload)
    meeting_id = res.json()["id"]

    # Markdown export
    md_res = client.get(f"/api/meetings/{meeting_id}/export/md")
    assert md_res.status_code == 200
    assert "# " in md_res.text

    # TXT export
    txt_res = client.get(f"/api/meetings/{meeting_id}/export/txt")
    assert txt_res.status_code == 200
    assert "MEETING SUMMARY" in txt_res.text

    # JSON export
    json_res = client.get(f"/api/meetings/{meeting_id}/export/json")
    assert json_res.status_code == 200
    assert json_res.json()["id"] == meeting_id

def test_audio_upload_flow():
    wav_path = create_synthetic_wav("test_upload.wav", duration_sec=1)
    
    with open(wav_path, "rb") as f:
        response = client.post(
            "/api/meetings/upload-and-summarize",
            files={"file": ("test_upload.wav", f, "audio/wav")},
            data={"asr_provider": "mock", "llm_provider": "fallback"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert "transcript" in data
    assert len(data["action_items"]) > 0
