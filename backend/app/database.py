import sqlite3
import json
from datetime import datetime
from pathlib import Path
from app.config import BACKEND_DIR

DB_PATH = BACKEND_DIR / "vani_ai.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # Assessments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        user_email TEXT NOT NULL,
        programming_language TEXT NOT NULL,
        assessment_language TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        answers_json TEXT NOT NULL,
        status TEXT NOT NULL, -- 'in_progress', 'submitted'
        created_at TEXT NOT NULL,
        submitted_at TEXT,
        baseline_audio_filename TEXT,
        baseline_transcript TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Safe column migrations for existing databases
    for col in ["baseline_audio_filename TEXT", "baseline_transcript TEXT"]:
        try:
            cursor.execute(f"ALTER TABLE assessments ADD COLUMN {col}")
        except Exception:
            pass
    
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()
