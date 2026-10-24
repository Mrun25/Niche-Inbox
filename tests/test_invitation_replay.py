"""Activation consumes a pending invitation exactly once, without network access."""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.core import database


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "activation.db"))
    database.init_db()
    return database


def test_repeated_activation_preserves_first_preferences(db):
    token = db.add_pending_user("reader@example.com")
    assert db.activate_user(token, ["Technology"], "08:00", "UTC") is True
    assert db.activate_user(token, ["Sports"], "12:00", "Asia/Kolkata") is False
    user = db.get_user_by_token(token)
    assert json.loads(user["topics"]) == ["Technology"]
    assert user["delivery_time"] == "08:00"
    assert user["timezone"] == "UTC"


def test_unknown_token_does_not_activate_anyone(db):
    db.add_pending_user("reader@example.com")
    assert db.activate_user("unknown", ["Technology"], "08:00", "UTC") is False
    assert db.get_all_active_users() == []


def test_concurrent_submissions_have_only_one_winner(db):
    token = db.add_pending_user("reader@example.com")
    def activate(hour):
        return db.activate_user(token, ["Technology"], hour, "UTC")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(activate, ["08:00", "09:00", "10:00", "11:00"]))
    assert results.count(True) == 1
    assert results.count(False) == 3
    assert len(db.get_all_active_users()) == 1
"""Flask tests isolate persistence and replace every external effect."""
import importlib
import json
import sys
from types import SimpleNamespace

import pytest

from src.core import database


@pytest.fixture()
def web(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "web.db"))
    database.init_db()
    # API clients are outside the request lifecycle being tested.
    monkeypatch.setitem(sys.modules, "src.core.news_fetcher", SimpleNamespace(fetch_articles=lambda *a: []))
    monkeypatch.setitem(sys.modules, "src.core.email_sender", SimpleNamespace(send_email=lambda *a: None))
    monkeypatch.setitem(sys.modules, "src.core.summarizer", SimpleNamespace(build_newsletter=lambda *a: "stub"))
    monkeypatch.setitem(sys.modules, "src.core.scheduler", SimpleNamespace(schedule_all_users=lambda *a: None))
    monkeypatch.setitem(sys.modules, "src.main", SimpleNamespace(scheduler_instance=object()))
    sys.modules.pop("src.api.preferences", None)
    module = importlib.import_module("src.api.preferences")
    effects = []
    monkeypatch.setattr(module, "schedule_all_users", lambda *a: effects.append("schedule"))
    class FakeThread:
        def __init__(self, **kwargs):
            pass
        def start(self):
            effects.append("send")
    monkeypatch.setattr(module.threading, "Thread", FakeThread)
    module.app.config.update(TESTING=True)
    yield module.app.test_client(), module, effects
    sys.modules.pop("src.api.preferences", None)


def form(token, **changes):
    return dict(token=token, topics="Technology", delivery_time="08:00", timezone="UTC", **changes)


def test_successful_submission_then_replay_does_not_send_or_reschedule(web):
    client, _, effects = web
    token = database.add_pending_user("reader@example.com")
    assert client.post("/submit", data=form(token)).status_code == 200
    assert effects == ["schedule", "send"]
    replay = dict(token=token, topics="Sports", delivery_time="12:00", timezone="Asia/Kolkata")
    assert client.post("/submit", data=replay).status_code == 200
    assert effects == ["schedule", "send"]
    user = database.get_user_by_token(token)
    assert json.loads(user["topics"]) == ["Technology"]
    assert user["delivery_time"] == "08:00"


def test_stale_pending_read_loses_atomic_activation_without_side_effects(web, monkeypatch):
    client, module, effects = web
    token = database.add_pending_user("reader@example.com")
    pending = database.get_user_by_token(token)
    database.activate_user(token, ["Sports"], "12:00", "UTC")
    monkeypatch.setattr(module, "get_user_by_token", lambda _: pending)
    assert client.post("/submit", data=form(token)).status_code == 200
    assert effects == []
    assert json.loads(database.get_user_by_token(token)["topics"]) == ["Sports"]


def test_unknown_invitation_has_no_side_effects(web):
    client, _, effects = web
    assert client.post("/submit", data=form("unknown")).status_code == 404
    assert effects == []


def test_missing_topics_keeps_invitation_pending(web):
    client, _, effects = web
    token = database.add_pending_user("reader@example.com")
    assert client.post("/submit", data={"token": token}).status_code == 200
    assert database.get_user_by_token(token)["status"] == "pending"
    assert effects == []
