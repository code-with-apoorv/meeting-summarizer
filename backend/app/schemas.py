from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ActionItemBase(BaseModel):
    task: str
    assignee: Optional[str] = "Unassigned"
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = "TBD"
    status: Optional[str] = "pending"

class ActionItemCreate(ActionItemBase):
    pass

class ActionItemUpdate(BaseModel):
    task: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None

class ActionItemResponse(ActionItemBase):
    id: int
    meeting_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SummaryStructured(BaseModel):
    title: str = Field(description="Crisp and descriptive title for the meeting")
    executive_summary: str = Field(description="1-2 paragraph high-level overview of the meeting")
    discussion_points: List[str] = Field(default_factory=list, description="Key topics and arguments discussed")
    key_decisions: List[str] = Field(default_factory=list, description="Explicit decisions reached during the meeting")
    action_items: List[ActionItemCreate] = Field(default_factory=list, description="Extracted tasks with assignees and deadlines")
    sentiment: Optional[str] = Field(default="Constructive", description="Overall tone/sentiment of the meeting")
    tags: List[str] = Field(default_factory=list, description="Relevant category tags (e.g. Engineering, Product, Sprint)")

class MeetingCreate(BaseModel):
    title: Optional[str] = "Untitled Meeting"
    transcript: str
    asr_provider: Optional[str] = "manual"
    llm_provider: Optional[str] = "gemini"

class MeetingResponse(BaseModel):
    id: int
    title: str
    filename: Optional[str]
    audio_duration_seconds: float
    file_size_bytes: int
    asr_provider: str
    llm_provider: str
    transcript: str
    executive_summary: Optional[str]
    key_decisions: List[str] = []
    discussion_points: List[str] = []
    tags: List[str] = []
    sentiment: Optional[str]
    created_at: datetime
    action_items: List[ActionItemResponse] = []

    class Config:
        from_attributes = True

class MeetingListItem(BaseModel):
    id: int
    title: str
    filename: Optional[str]
    audio_duration_seconds: float
    executive_summary: Optional[str]
    tags: List[str] = []
    sentiment: Optional[str]
    created_at: datetime
    action_items_count: int = 0
    completed_items_count: int = 0

    class Config:
        from_attributes = True

class TextSummarizeRequest(BaseModel):
    text: str
    title: Optional[str] = None
    custom_prompt: Optional[str] = None
    provider: Optional[str] = "auto"

class HealthResponse(BaseModel):
    status: str
    version: str
    configured_providers: dict
