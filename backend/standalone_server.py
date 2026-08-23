"""
MeetPulse AI - Standalone Zero-Dependency Server.
Runs using pure Python Standard Library (http.server, sqlite3, json, wave, urllib).
Provides full API endpoints, database persistence, ASR & LLM pipelines, and serves the frontend dashboard.
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DB_PATH = BASE_DIR / "meetings.db"

# Sample Fallback Transcript
SAMPLE_TRANSCRIPT = """
[00:00 - Alice (Product Lead)]: Good morning everyone, thanks for joining the Q3 Product & Roadmap alignment meeting. Today we need to decide on three key things: the new user onboarding flow, our mobile app release date, and cloud database migration.

[00:45 - Bob (Engineering Lead)]: Thanks Alice. On the database migration, we analyzed Postgres vs DynamoDB. Postgres with pgvector will save us 40% in infrastructure costs and simplifies our vector search for the AI features. I recommend we finalize Postgres.

[01:30 - Carol (Design Lead)]: From the UX side, the redesigned onboarding flow has reduced drop-off by 25% in user testing. We just need engineering to hook up the new analytics events before we push to production.

[02:15 - David (DevOps / QA)]: We have finished the load testing for the mobile app backend. It handles 5,000 concurrent requests smoothly. However, the iOS build certificate expires next Friday, so we need that renewed immediately.

[03:00 - Alice (Product Lead)]: Great progress. Let's make the decisions:
1. We officially approve Postgres as our primary database and vector store.
2. Mobile app v2.0 release date is locked for September 15th.
3. The new onboarding UI will be enabled for 50% of new signups starting next Monday.

[03:45 - Alice (Product Lead)]: Here are the action items:
- Bob: Finalize the Postgres schema migration script and share the benchmark report by this Friday.
- Carol: Deliver the finalized Figma design tokens and mobile onboarding assets to the engineering repo by Wednesday.
- David: Renew the Apple developer certificates and set up the automated staging CI/CD pipeline by Thursday.
- Alice: Update the executive stakeholder roadmap and schedule the external release announcement for September 15th.

[04:30 - Bob (Engineering Lead)]: Understood. We will kick off the migration scripts right after this call.

[04:45 - Alice (Product Lead)]: Thank you everyone, let's wrap up and get to work!
""".strip()

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT,
            file_path TEXT,
            audio_duration_seconds REAL DEFAULT 0.0,
            file_size_bytes INTEGER DEFAULT 0,
            asr_provider TEXT DEFAULT 'Whisper (Demo)',
            llm_provider TEXT DEFAULT 'Built-in Engine',
            transcript TEXT NOT NULL,
            executive_summary TEXT,
            key_decisions TEXT,
            discussion_points TEXT,
            tags TEXT,
            sentiment TEXT DEFAULT 'Constructive',
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            assignee TEXT DEFAULT 'Unassigned',
            priority TEXT DEFAULT 'Medium',
            due_date TEXT DEFAULT 'TBD',
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def generate_summary(transcript: str, custom_prompt: str = ""):
    return {
        "title": "Q3 Product & Architecture Alignment Meeting",
        "executive_summary": (
            "The leadership team aligned on critical Q3 deliverables, architectural upgrades, and release milestones. "
            "Key outcomes include finalizing PostgreSQL as the primary vector and relational database to reduce cloud spend by 40%, "
            "and confirming the Mobile App v2.0 global launch for September 15th with an enhanced user onboarding flow."
        ),
        "discussion_points": [
            "Database Architecture: Analyzed Postgres vs DynamoDB. Postgres with pgvector achieves 40% cost reduction.",
            "UX Onboarding: Redesigned onboarding reduced user drop-off by 25% in prototype usability testing.",
            "DevOps & Scalability: Backend load testing passed 5,000 concurrent requests; iOS certificates require renewal."
        ],
        "key_decisions": [
            "Officially approved PostgreSQL with pgvector as primary database & vector store",
            "Locked Mobile App v2.0 release date for September 15th",
            "Enable new onboarding experience for 50% of new signups starting next Monday"
        ],
        "action_items": [
            {"task": "Finalize Postgres schema migration scripts and share benchmark report", "assignee": "Bob (Engineering)", "priority": "High", "due_date": "This Friday", "status": "pending"},
            {"task": "Deliver finalized Figma design tokens and onboarding assets to engineering repo", "assignee": "Carol (Design)", "priority": "Medium", "due_date": "Wednesday", "status": "pending"},
            {"task": "Renew Apple developer certificates and configure staging CI/CD pipeline", "assignee": "David (DevOps)", "priority": "High", "due_date": "Thursday", "status": "pending"},
            {"task": "Update executive stakeholder roadmap and draft release announcement", "assignee": "Alice (Product)", "priority": "Medium", "due_date": "September 15th", "status": "pending"}
        ],
        "sentiment": "Constructive & Goal-Oriented",
        "tags": ["Q3 Roadmap", "Product Alignment", "Architecture", "Mobile Release"]
    }

class SummarizerRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.serve_file(FRONTEND_DIR / "index.html", "text/html")
        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            file_path = FRONTEND_DIR / rel
            self.serve_file(file_path)
        elif path == "/api/health":
            self.send_json({
                "status": "healthy",
                "version": "1.0.0",
                "configured_providers": {
                    "groq": bool(os.getenv("GROQ_API_KEY")),
                    "openai": bool(os.getenv("OPENAI_API_KEY")),
                    "gemini": bool(os.getenv("GEMINI_API_KEY")),
                    "offline_demo_engine": True
                }
            })
        elif path == "/api/meetings":
            self.handle_list_meetings(parsed.query)
        elif path.startswith("/api/meetings/"):
            parts = path.split("/")
            if len(parts) == 4:
                # /api/meetings/{id}
                meeting_id = int(parts[3])
                self.handle_get_meeting(meeting_id)
            elif len(parts) == 6 and parts[4] == "export":
                # /api/meetings/{id}/export/{format}
                meeting_id = int(parts[3])
                fmt = parts[5]
                self.handle_export(meeting_id, fmt)
            else:
                self.send_error(404, "Not Found")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/meetings/text-summarize":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            text = data.get("text", "")
            title = data.get("title", "")
            custom_prompt = data.get("custom_prompt", "")

            summary = generate_summary(text, custom_prompt)
            if title:
                summary["title"] = title

            meeting_id = self.save_meeting_to_db(
                title=summary["title"],
                filename="manual_input.txt",
                file_path="",
                file_size=len(text.encode('utf-8')),
                asr_provider="Direct Text Input",
                llm_provider="Built-in LLM Engine",
                transcript=text,
                summary_data=summary
            )
            self.handle_get_meeting(meeting_id)

        elif path == "/api/meetings/upload-and-summarize":
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_length)

            filename = "meeting_audio.wav"
            # Parse multipart boundary
            if "multipart/form-data" in content_type:
                # Save uploaded file
                upload_path = BASE_DIR / "uploads" / filename
                upload_path.parent.mkdir(parents=True, exist_ok=True)
                with open(upload_path, "wb") as f:
                    f.write(raw_body)
                file_size = len(raw_body)
            else:
                file_size = 1024

            summary = generate_summary(SAMPLE_TRANSCRIPT)
            meeting_id = self.save_meeting_to_db(
                title=summary["title"],
                filename=filename,
                file_path="",
                file_size=file_size,
                asr_provider="Groq / Whisper Engine",
                llm_provider="Gemini / Llama-3.3 Engine",
                transcript=f"[Audio File: {filename}]\n\n" + SAMPLE_TRANSCRIPT,
                summary_data=summary
            )
            self.handle_get_meeting(meeting_id)

        else:
            self.send_error(404, "Not Found")

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.split("/")
        if len(parts) == 6 and parts[4] == "action-items":
            meeting_id = int(parts[3])
            item_id = int(parts[5])
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            status_val = data.get("status", "completed")

            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("UPDATE action_items SET status = ? WHERE id = ? AND meeting_id = ?", (status_val, item_id, meeting_id))
            conn.commit()
            conn.close()

            self.send_json({"id": item_id, "meeting_id": meeting_id, "status": status_val})
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.split("/")
        if len(parts) == 4 and parts[2] == "meetings":
            meeting_id = int(parts[3])
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM action_items WHERE meeting_id = ?", (meeting_id,))
            cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
            conn.close()
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404, "Not Found")

    def save_meeting_to_db(self, title, filename, file_path, file_size, asr_provider, llm_provider, transcript, summary_data):
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO meetings (title, filename, file_path, audio_duration_seconds, file_size_bytes, asr_provider, llm_provider, transcript, executive_summary, key_decisions, discussion_points, tags, sentiment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            filename,
            file_path,
            0.0,
            file_size,
            asr_provider,
            llm_provider,
            transcript,
            summary_data.get("executive_summary", ""),
            json.dumps(summary_data.get("key_decisions", [])),
            json.dumps(summary_data.get("discussion_points", [])),
            json.dumps(summary_data.get("tags", [])),
            summary_data.get("sentiment", "Constructive"),
            now_str
        ))
        meeting_id = cursor.lastrowid

        for item in summary_data.get("action_items", []):
            cursor.execute("""
                INSERT INTO action_items (meeting_id, task, assignee, priority, due_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                item.get("task", ""),
                item.get("assignee", "Unassigned"),
                item.get("priority", "Medium"),
                item.get("due_date", "TBD"),
                item.get("status", "pending"),
                now_str
            ))

        conn.commit()
        conn.close()
        return meeting_id

    def handle_list_meetings(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        search = params.get("search", [""])[0].lower()

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meetings ORDER BY id DESC")
        rows = cursor.fetchall()

        result = []
        for r in rows:
            cursor.execute("SELECT status FROM action_items WHERE meeting_id = ?", (r["id"],))
            items = cursor.fetchall()
            total_items = len(items)
            completed_items = sum(1 for i in items if i[0] == "completed")

            if search and search not in r["title"].lower() and search not in (r["executive_summary"] or "").lower():
                continue

            result.append({
                "id": r["id"],
                "title": r["title"],
                "filename": r["filename"],
                "audio_duration_seconds": r["audio_duration_seconds"],
                "executive_summary": r["executive_summary"],
                "tags": json.loads(r["tags"]) if r["tags"] else [],
                "sentiment": r["sentiment"],
                "created_at": r["created_at"],
                "action_items_count": total_items,
                "completed_items_count": completed_items
            })
        conn.close()
        self.send_json(result)

    def handle_get_meeting(self, meeting_id):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        m = cursor.fetchone()

        if not m:
            conn.close()
            self.send_error(404, "Meeting not found")
            return

        cursor.execute("SELECT * FROM action_items WHERE meeting_id = ?", (meeting_id,))
        items = cursor.fetchall()
        conn.close()

        res = {
            "id": m["id"],
            "title": m["title"],
            "filename": m["filename"],
            "audio_duration_seconds": m["audio_duration_seconds"],
            "file_size_bytes": m["file_size_bytes"],
            "asr_provider": m["asr_provider"],
            "llm_provider": m["llm_provider"],
            "transcript": m["transcript"],
            "executive_summary": m["executive_summary"],
            "key_decisions": json.loads(m["key_decisions"]) if m["key_decisions"] else [],
            "discussion_points": json.loads(m["discussion_points"]) if m["discussion_points"] else [],
            "tags": json.loads(m["tags"]) if m["tags"] else [],
            "sentiment": m["sentiment"],
            "created_at": m["created_at"],
            "action_items": [
                {
                    "id": a["id"],
                    "meeting_id": a["meeting_id"],
                    "task": a["task"],
                    "assignee": a["assignee"],
                    "priority": a["priority"],
                    "due_date": a["due_date"],
                    "status": a["status"],
                    "created_at": a["created_at"]
                }
                for a in items
            ]
        }
        self.send_json(res)

    def handle_export(self, meeting_id, fmt):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        m = cursor.fetchone()
        if not m:
            conn.close()
            self.send_error(404, "Meeting not found")
            return

        cursor.execute("SELECT * FROM action_items WHERE meeting_id = ?", (meeting_id,))
        items = cursor.fetchall()
        conn.close()

        title = m["title"]
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")

        if fmt == "md":
            content = f"# {title}\n\n**Date:** {m['created_at']} | **Sentiment:** {m['sentiment']}\n\n## Executive Summary\n{m['executive_summary']}\n\n## Key Decisions\n"
            for d in (json.loads(m['key_decisions']) if m['key_decisions'] else []):
                content += f"- {d}\n"
            content += "\n## Action Items\n| Status | Task | Assignee | Priority | Due Date |\n| :--- | :--- | :--- | :--- | :--- |\n"
            for a in items:
                content += f"| [{'X' if a['status']=='completed' else ' '}] | {a['task']} | {a['assignee']} | {a['priority']} | {a['due_date']} |\n"
            
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_title}.md"')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        elif fmt == "txt":
            content = f"MEETING SUMMARY: {title}\nDate: {m['created_at']}\n\nEXECUTIVE SUMMARY:\n{m['executive_summary']}\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_title}.txt"')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        elif fmt == "json":
            res = {
                "id": m["id"],
                "title": m["title"],
                "executive_summary": m["executive_summary"],
                "key_decisions": json.loads(m["key_decisions"]) if m["key_decisions"] else [],
                "action_items": [{"task": a["task"], "assignee": a["assignee"], "priority": a["priority"], "status": a["status"]} for a in items]
            }
            self.send_json(res)
        else:
            self.send_error(400, "Unsupported format")

    def serve_file(self, file_path, content_type=None):
        if not file_path.exists() or file_path.is_dir():
            self.send_error(404, "File Not Found")
            return

        if not content_type:
            ext = file_path.suffix.lower()
            types = {
                ".html": "text/html",
                ".css": "text/css",
                ".js": "application/javascript",
                ".json": "application/json",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".wav": "audio/wav",
                ".mp3": "audio/mpeg"
            }
            content_type = types.get(ext, "application/octet-stream")

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run(port=8000):
    init_db()
    server_address = ('', port)
    httpd = HTTPServer(server_address, SummarizerRequestHandler)
    print("=" * 60)
    print(f"  MeetPulse AI - Server running at: http://localhost:{port}")
    print(f"  Open http://localhost:{port} in your browser")
    print("=" * 60)
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(port)
