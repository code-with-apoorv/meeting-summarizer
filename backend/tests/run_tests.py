"""
Self-contained automated test suite for MeetPulse AI Meeting Summarizer.
Runs with Python standard library (unittest, sqlite3, json, wave, urllib).
"""

import os
import sys
import json
import sqlite3
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.samples.generate_sample_audio import create_synthetic_wav
from backend.app.services.export_service import export_service

TEST_DB_PATH = Path(__file__).resolve().parent / "test_meetings.db"

class TestStandaloneEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
            
        conn = sqlite3.connect(str(TEST_DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT,
                file_path TEXT,
                audio_duration_seconds REAL DEFAULT 0.0,
                file_size_bytes INTEGER DEFAULT 0,
                asr_provider TEXT,
                llm_provider TEXT,
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
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def test_1_database_operations(self):
        conn = sqlite3.connect(str(TEST_DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO meetings (title, filename, transcript, executive_summary, key_decisions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Q3 Product Planning",
            "meeting.wav",
            "Alice: We decided on Postgres.",
            "Meeting focused on Postgres DB migration.",
            json.dumps(["Approved Postgres migration"]),
            "2026-08-23 16:00:00"
        ))
        meeting_id = cursor.lastrowid
        self.assertIsNotNone(meeting_id)

        # Insert Action Item
        cursor.execute("""
            INSERT INTO action_items (meeting_id, task, assignee, priority, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (meeting_id, "Write DB migration scripts", "Bob", "High", "Friday", "pending", "2026-08-23 16:00:00"))
        
        item_id = cursor.lastrowid
        self.assertIsNotNone(item_id)

        # Query & Verify
        cursor.execute("SELECT title, executive_summary FROM meetings WHERE id = ?", (meeting_id,))
        row = cursor.fetchone()
        self.assertEqual(row[0], "Q3 Product Planning")

        # Toggle Action Item status
        cursor.execute("UPDATE action_items SET status = 'completed' WHERE id = ?", (item_id,))
        conn.commit()

        cursor.execute("SELECT status FROM action_items WHERE id = ?", (item_id,))
        status_row = cursor.fetchone()
        self.assertEqual(status_row[0], "completed")

        conn.close()

    def test_2_sample_audio_generation(self):
        wav_path = create_synthetic_wav("test_run.wav", duration_sec=1)
        self.assertTrue(Path(wav_path).exists())
        self.assertTrue(os.path.getsize(wav_path) > 1000)
        if Path(wav_path).exists():
            os.remove(wav_path)

    def test_3_export_service_formatting(self):
        mock_data = {
            "title": "Executive Alignment",
            "created_at": "2026-08-23",
            "sentiment": "Constructive",
            "executive_summary": "High level strategy alignment.",
            "key_decisions": ["Approved budget"],
            "discussion_points": ["Cost optimization"],
            "action_items": [{"task": "Submit invoice", "assignee": "Carol", "priority": "High", "due_date": "Tomorrow", "status": "pending"}],
            "tags": ["Finance", "Strategy"],
            "transcript": "Verbatim meeting discussion."
        }

        md = export_service.to_markdown(mock_data)
        self.assertIn("# Executive Alignment", md)
        self.assertIn("## Key Decisions Made", md)
        self.assertIn("Submit invoice", md)

        txt = export_service.to_txt(mock_data)
        self.assertIn("MEETING SUMMARY: EXECUTIVE ALIGNMENT", txt)
        self.assertIn("[TODO] Submit invoice", txt)

        json_out = export_service.to_json(mock_data)
        parsed = json.loads(json_out)
        self.assertEqual(parsed["title"], "Executive Alignment")

if __name__ == "__main__":
    unittest.main(verbosity=2)
