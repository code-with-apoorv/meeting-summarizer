# 📹 Demo Video Recording Guide & Submission Script

This guide outlines a simple **2-3 minute presentation script** that covers every single evaluation criteria specified in the assignment rubric.

---

## 📋 Pre-Recording Checklist
- [ ] Backend server running (`run.bat` or `uvicorn backend.app.main:app --port 8000`).
- [ ] Browser open at `http://localhost:8000`.
- [ ] Screen recording software ready (e.g., OBS Studio, Loom, Windows Game Bar `Win + G`, or QuickTime).
- [ ] Sample audio file generated or ready in `backend/samples/sample_meeting_demo.wav`.

---

## ⏱️ Video Script & Timeline (2 to 3 Minutes)

### 0:00 – 0:30 | Introduction & Architecture
- **Voiceover**: 
  > *"Hello! This is my submission for the Meeting Summarizer assignment. The objective of this project is to transcribe meeting audio recordings and automatically extract action-oriented summaries, key decisions, and actionable task lists with assignees and deadlines."*
- **Visual**: Show the web interface at `http://localhost:8000` and briefly mention the tech stack (FastAPI backend, SQLite persistence, multi-engine ASR with Whisper / Gemini / Groq, and LLM structured prompt extraction).

### 0:30 – 1:15 | Audio Upload & Speech-to-Text (ASR) Demo
- **Voiceover**: 
  > *"First, let's test the audio ingestion. We can either record live audio using the in-browser microphone with real-time waveform visualization, or drag and drop an audio file."*
- **Visual**: 
  1. Click **Start Recording** on the microphone card, speak for 3 seconds, and show the animated waveform canvas.
  2. Or drag and drop `sample_meeting_demo.wav` into the upload zone.
  3. Click **"Transcribe & Summarize"**.
  4. Show the live progress step tracker (`Uploading` ➔ `Transcribing via ASR` ➔ `Extracting Decisions & Tasks via LLM`).

### 1:15 – 2:00 | Structured Output & Features Walkthrough
- **Voiceover**: 
  > *"Here are the generated results:*
  > *1. On the left, we have the full verbatim transcript with a built-in search tool to quickly highlight and find key terms.*
  > *2. On the right, we have an Executive Summary, clear bullet points of all Key Decisions Made, and Discussion Topics.*
  > *3. Most importantly, we have the Action Items checklist. Each task has an assigned owner, priority badge, and deadline. We can interactively toggle tasks as completed, which immediately syncs with the SQLite database."*
- **Visual**: 
  1. Type a word in the transcript search bar to demonstrate real-time keyword highlighting.
  2. Check off one or two action items.
  3. Show the priority badges (High, Medium, Low) and assignee tags.

### 2:00 – 2:30 | Multi-Format Export & History Tab
- **Voiceover**: 
  > *"Users can export the full meeting report in multiple formats: Markdown, PDF report, JSON, or Plain Text."*
- **Visual**: 
  1. Click **"Markdown (.md)"** or **"PDF Report"** to show instant file download.
  2. Navigate to the **"Meeting History"** tab to show all past stored meetings, search filters, and progress completion bars.

### 2:30 – 2:50 | Code Structure & GitHub Repository
- **Voiceover**: 
  > *"The project follows a clean, modular architecture: `asr_service.py` handles speech recognition, `llm_service.py` enforces structured JSON schema extraction, `export_service.py` generates reports, and automated unit tests verify end-to-end reliability. Thank you!"*
- **Visual**: Quickly show the project folder structure or `backend/tests/` in VS Code / IDE.

---

## 🏆 Evaluation Rubric Alignment Table

| Assignment Requirement | Where It Is Demonstrated in the App |
| :--- | :--- |
| **Input: Meeting audio files** | Drag-and-drop uploader + live microphone recording |
| **Output: Transcript + summary + action items** | 2-column dashboard with verbatim transcript, decisions, and task checklist |
| **ASR API Integration** | `asr_service.py` (Whisper, Gemini, Groq, local fallback) |
| **Backend to store & process data** | FastAPI + SQLite database + SQLAlchemy models |
| **LLM for summary generation** | `llm_service.py` with structured JSON schema prompt |
| **Frontend to upload & view summary** | Full responsive Web UI (`frontend/index.html`) |
| **Deliverables (GitHub + README)** | Clean modular GitHub repository with full docs |
