"""Shared fixtures. Scaffolding only — the suite itself is someone else's to fill in.

The point of these fixtures is that the app layer is testable **without an Anthropic API key**:
`stub_core` replaces the three `pipeline/` entry points with deterministic doubles, so tests exercise
retrieval, the bucket-E flow machine, persistence, and the HTTP surface rather than the model.
Test the Core itself against `pipeline/goldenset/golden.json` via `pipeline/eval_harness.py`.

Run from `backend/`:  python -m pytest
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
for path in (BACKEND_DIR, BACKEND_DIR / "pipeline"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture
def db_url(tmp_path) -> str:
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def stub_core(monkeypatch):
    """Stub the Assistant Core. Returns a dict you mutate to steer the doubles:

        core["intents"].append(IntentResult(bucket="a_where_i_stand"))  # queued, one per turn
        core["phrase"] = lambda facts, bucket, name, lang: "..."        # or raise, to test fallback
    """
    from pipeline import intent as intent_mod
    from pipeline import phrase as phrase_mod
    from pipeline.schema import IntentResult

    core: dict = {
        "intents": [],
        "phrase": lambda facts, bucket, name, lang: f"{name}: " + ", ".join(
            str(v) for v in facts.values()
        ),
    }

    def classify_intent(message: str, has_pending_flow: bool) -> IntentResult:
        return core["intents"].pop(0) if core["intents"] else IntentResult(bucket="unresolved")

    monkeypatch.setattr(intent_mod, "classify_intent", classify_intent)
    monkeypatch.setattr(
        phrase_mod, "phrase_reply", lambda *a, **kw: core["phrase"](*a, **kw)
    )
    return core


@pytest.fixture
def client(db_url, monkeypatch, stub_core):
    """A `TestClient` on a fresh seeded SQLite DB. Entering the context runs the lifespan
    (create_all + `seed_if_empty`), so Ana Souza and the three synthetic employees exist."""
    monkeypatch.setenv("WA_DATABASE_URL", db_url)
    from app.config import get_settings

    get_settings.cache_clear()

    # db.py binds its engine at import time, so it must be (re)imported after the env var is set.
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
