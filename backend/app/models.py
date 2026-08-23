import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, default="Untitled Meeting")
    filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    audio_duration_seconds = Column(Float, default=0.0)
    file_size_bytes = Column(Integer, default=0)
    asr_provider = Column(String(50), default="whisper")
    llm_provider = Column(String(50), default="gemini")
    transcript = Column(Text, nullable=False, default="")
    executive_summary = Column(Text, nullable=True)
    key_decisions = Column(Text, nullable=True)     # JSON string list
    discussion_points = Column(Text, nullable=True) # JSON string list
    tags = Column(Text, nullable=True)              # JSON string list
    sentiment = Column(String(50), default="Neutral")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    task = Column(String(500), nullable=False)
    assignee = Column(String(100), default="Unassigned")
    priority = Column(String(20), default="Medium") # High, Medium, Low
    due_date = Column(String(50), default="TBD")
    status = Column(String(20), default="pending")  # pending, completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    meeting = relationship("Meeting", back_populates="action_items")
