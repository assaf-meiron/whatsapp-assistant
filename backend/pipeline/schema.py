"""The shared contract between `pipeline/` (Claude-API logic, DB-agnostic) and
`app/pipeline_adapter.py` (DB-facing orchestration — retrieval, Request creation, persistence).

Mirrors lawtrack-ai's split: `pipeline/` never imports SQLAlchemy or touches a session; it only
sees plain JSON-safe data in and out, so it can be eval'd/red-teamed offline against a fixture set.
"""
from __future__ import annotations

from pydantic import BaseModel


class IntentResult(BaseModel):
    """`classify_intent`'s return. `bucket` is one of the `app.models.Bucket` enum values."""

    bucket: str
    request_type: str | None = None        # "time_off" | "shift_swap" — set only when bucket == e_do_something
    flow_action: str | None = None         # "confirm" | "cancel" | None — set when continuing a pending flow
    detected_date_label: str | None = None  # free-text date phrase for a new request ask, e.g. "Fri 25 Jul"


class GroundednessCheck(BaseModel):
    """`check_grounded`'s return. `fallback_reply` is always populated (built directly from
    `facts`, no LLM) so the caller can use it unconditionally when `is_grounded` is False."""

    is_grounded: bool
    fallback_reply: str
