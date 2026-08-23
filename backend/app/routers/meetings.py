import os
import json
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import io

from ..database import get_db
from ..models import Meeting, ActionItem
from ..schemas import (
    MeetingResponse,
    MeetingListItem,
    TextSummarizeRequest,
    ActionItemResponse,
    ActionItemUpdate,
)
from ..services.asr_service import asr_service
from ..services.llm_service import llm_service
from ..services.export_service import export_service
from ..config import settings

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])


def _format_meeting_dict(meeting: Meeting) -> dict:
    decisions = []
    points = []
    tags = []
    try:
        decisions = json.loads(meeting.key_decisions) if meeting.key_decisions else []
    except Exception:
        decisions = []

    try:
        points = json.loads(meeting.discussion_points) if meeting.discussion_points else []
    except Exception:
        points = []

    try:
        tags = json.loads(meeting.tags) if meeting.tags else []
    except Exception:
        tags = []

    return {
        "id": meeting.id,
        "title": meeting.title,
        "filename": meeting.filename,
        "audio_duration_seconds": meeting.audio_duration_seconds,
        "file_size_bytes": meeting.file_size_bytes,
        "asr_provider": meeting.asr_provider,
        "llm_provider": meeting.llm_provider,
        "transcript": meeting.transcript,
        "executive_summary": meeting.executive_summary,
        "key_decisions": decisions,
        "discussion_points": points,
        "tags": tags,
        "sentiment": meeting.sentiment,
        "created_at": meeting.created_at.strftime("%Y-%m-%d %H:%M:%S") if meeting.created_at else "",
        "action_items": [
            {
                "id": a.id,
                "meeting_id": a.meeting_id,
                "task": a.task,
                "assignee": a.assignee,
                "priority": a.priority,
                "due_date": a.due_date,
                "status": a.status,
                "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
            }
            for a in meeting.action_items
        ]
    }


@router.post("/upload-and-summarize", response_model=MeetingResponse)
async def upload_and_summarize(
    file: UploadFile = File(...),
    custom_prompt: Optional[str] = Form(None),
    asr_provider: Optional[str] = Form("auto"),
    llm_provider: Optional[str] = Form("auto"),
    db: Session = Depends(get_db)
):
    # Validate file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".mp4", ".flac"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )

    # Save audio file to storage
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    saved_path = settings.UPLOAD_DIR / unique_filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(saved_path)

    # Step 1: Automatic Speech Recognition (ASR)
    transcript, used_asr = await asr_service.transcribe(str(saved_path), provider=asr_provider)

    # Step 2: LLM Meeting Summarization & Action Item Extraction
    summary_data, used_llm = await llm_service.summarize(
        transcript=transcript,
        custom_prompt=custom_prompt,
        provider=llm_provider
    )

    # Step 3: Persist to SQLite Database
    meeting = Meeting(
        title=summary_data.title or file.filename,
        filename=file.filename,
        file_path=str(saved_path),
        audio_duration_seconds=0.0,
        file_size_bytes=file_size,
        asr_provider=used_asr,
        llm_provider=used_llm,
        transcript=transcript,
        executive_summary=summary_data.executive_summary,
        key_decisions=json.dumps(summary_data.key_decisions),
        discussion_points=json.dumps(summary_data.discussion_points),
        tags=json.dumps(summary_data.tags),
        sentiment=summary_data.sentiment,
    )
    db.add(meeting)
    db.flush()

    for item in summary_data.action_items:
        action_item = ActionItem(
            meeting_id=meeting.id,
            task=item.task,
            assignee=item.assignee or "Unassigned",
            priority=item.priority or "Medium",
            due_date=item.due_date or "TBD",
            status=item.status or "pending"
        )
        db.add(action_item)

    db.commit()
    db.refresh(meeting)

    formatted = _format_meeting_dict(meeting)
    return formatted


@router.post("/text-summarize", response_model=MeetingResponse)
async def summarize_text_transcript(
    payload: TextSummarizeRequest,
    db: Session = Depends(get_db)
):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Transcript text cannot be empty.")

    summary_data, used_llm = await llm_service.summarize(
        transcript=payload.text,
        custom_prompt=payload.custom_prompt,
        provider=payload.provider
    )

    meeting = Meeting(
        title=payload.title or summary_data.title or "Direct Transcript Summary",
        filename="manual_input.txt",
        file_path="",
        audio_duration_seconds=0.0,
        file_size_bytes=len(payload.text.encode("utf-8")),
        asr_provider="Direct Input",
        llm_provider=used_llm,
        transcript=payload.text,
        executive_summary=summary_data.executive_summary,
        key_decisions=json.dumps(summary_data.key_decisions),
        discussion_points=json.dumps(summary_data.discussion_points),
        tags=json.dumps(summary_data.tags),
        sentiment=summary_data.sentiment,
    )
    db.add(meeting)
    db.flush()

    for item in summary_data.action_items:
        action_item = ActionItem(
            meeting_id=meeting.id,
            task=item.task,
            assignee=item.assignee or "Unassigned",
            priority=item.priority or "Medium",
            due_date=item.due_date or "TBD",
            status=item.status or "pending"
        )
        db.add(action_item)

    db.commit()
    db.refresh(meeting)

    return _format_meeting_dict(meeting)


@router.get("", response_model=List[MeetingListItem])
def list_meetings(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Meeting)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Meeting.title.ilike(search_pattern)) | 
            (Meeting.executive_summary.ilike(search_pattern)) |
            (Meeting.transcript.ilike(search_pattern))
        )
    
    meetings = query.order_by(Meeting.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for m in meetings:
        tags = []
        try:
            tags = json.loads(m.tags) if m.tags else []
        except Exception:
            tags = []
            
        total_items = len(m.action_items)
        completed_items = sum(1 for a in m.action_items if a.status == "completed")
        
        result.append(MeetingListItem(
            id=m.id,
            title=m.title,
            filename=m.filename,
            audio_duration_seconds=m.audio_duration_seconds,
            executive_summary=m.executive_summary,
            tags=tags,
            sentiment=m.sentiment,
            created_at=m.created_at,
            action_items_count=total_items,
            completed_items_count=completed_items
        ))
    return result


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _format_meeting_dict(meeting)


@router.patch("/{meeting_id}/action-items/{item_id}", response_model=ActionItemResponse)
def update_action_item(
    meeting_id: int,
    item_id: int,
    payload: ActionItemUpdate,
    db: Session = Depends(get_db)
):
    item = db.query(ActionItem).filter(
        ActionItem.id == item_id,
        ActionItem.meeting_id == meeting_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")

    if payload.status is not None:
        item.status = payload.status
    if payload.task is not None:
        item.task = payload.task
    if payload.assignee is not None:
        item.assignee = payload.assignee
    if payload.priority is not None:
        item.priority = payload.priority
    if payload.due_date is not None:
        item.due_date = payload.due_date

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Clean up uploaded audio file if present
    if meeting.file_path and os.path.exists(meeting.file_path):
        try:
            os.remove(meeting.file_path)
        except Exception:
            pass

    db.delete(meeting)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{meeting_id}/export/{export_format}")
def export_meeting_summary(
    meeting_id: int,
    export_format: str,
    db: Session = Depends(get_db)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting_dict = _format_meeting_dict(meeting)
    safe_title = "".join(c for c in meeting.title if c.isalnum() or c in (" ", "_", "-")).rstrip()
    safe_title = safe_title.replace(" ", "_") or f"meeting_{meeting_id}"

    if export_format.lower() == "md":
        content = export_service.to_markdown(meeting_dict)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_summary.md"'}
        )

    elif export_format.lower() == "txt":
        content = export_service.to_txt(meeting_dict)
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_summary.txt"'}
        )

    elif export_format.lower() == "json":
        content = export_service.to_json(meeting_dict)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_summary.json"'}
        )

    elif export_format.lower() == "pdf":
        pdf_bytes = export_service.to_pdf_bytes(meeting_dict)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_summary.pdf"'}
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Choose from: md, txt, json, pdf")
