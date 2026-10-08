"""Offline tests for src/core/database.py (SQLite user store).

Each test runs against a fresh temporary database file by monkeypatching
database.DB_PATH, so nothing here touches the real digest.db or the network.
"""

import json

import pytest

from src.core import database


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()
    return database


def test_init_db_creates_users_table(db):
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
    assert row is not None


def test_add_pending_user_returns_token_and_pending_status(db):
    token = db.add_pending_user("ada@example.com")
    assert isinstance(token, str) and len(token) > 20
    user = db.get_user_by_email("ada@example.com")
    assert user["status"] == "pending"
    assert user["token"] == token


def test_add_pending_user_duplicate_email_keeps_existing_token(db):
    first = db.add_pending_user("ada@example.com")
    second = db.add_pending_user("ada@example.com")
    assert first == second


def test_get_user_by_token_roundtrip(db):
    token = db.add_pending_user("grace@example.com")
    user = db.get_user_by_token(token)
    assert user["email"] == "grace@example.com"


def test_get_user_by_token_unknown_returns_none(db):
    assert db.get_user_by_token("no-such-token") is None


def test_activate_user_marks_active_and_stores_preferences(db):
    token = db.add_pending_user("hopper@example.com")
    db.activate_user(token, ["ai", "security"], "08:00", "Asia/Calcutta")
    user = db.get_user_by_token(token)
    assert user["status"] == "active"
    assert json.loads(user["topics"]) == ["ai", "security"]
    assert user["delivery_time"] == "08:00"
    assert user["timezone"] == "Asia/Calcutta"
    assert [u["email"] for u in db.get_all_active_users()] == ["hopper@example.com"]


def test_get_all_active_users_excludes_pending(db):
    db.add_pending_user("pending@example.com")
    assert db.get_all_active_users() == []
