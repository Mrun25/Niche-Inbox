"""
database.py — SQLite storage for user preferences and status.
"""

import sqlite3
import secrets
import json
from datetime import datetime

DB_PATH = "digest.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT    UNIQUE NOT NULL,
                token         TEXT    UNIQUE,
                status        TEXT    NOT NULL DEFAULT 'pending',
                topics        TEXT,
                delivery_time TEXT,
                timezone      TEXT,
                created_at    TEXT    NOT NULL
            )
        """)
        conn.commit()


def add_pending_user(email: str) -> str:
    """Insert a new pending user with a one-time token. Returns the token."""
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, token, status, created_at) VALUES (?, ?, 'pending', ?)",
            (email, token, now),
        )
        conn.commit()
    with get_connection() as conn:
        row = conn.execute("SELECT token FROM users WHERE email = ?", (email,)).fetchone()
        return row["token"]


def get_user_by_token(token: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_all_active_users():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM users WHERE status = 'active'").fetchall()
        return [dict(r) for r in rows]


def activate_user(token: str, topics: list, delivery_time: str, timezone: str):
    with get_connection() as conn:
        conn.execute(
            """UPDATE users
               SET status = 'active', topics = ?, delivery_time = ?, timezone = ?
               WHERE token = ?""",
            (json.dumps(topics), delivery_time, timezone, token),
        )
        conn.commit()
