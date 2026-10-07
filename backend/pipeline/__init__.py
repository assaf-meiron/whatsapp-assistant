"""The Assistant Core (spec §3): intent → [retrieval, elsewhere] → phrase → guardrail.

DB-agnostic by construction — nothing here imports SQLAlchemy or opens a session. Every module
takes and returns plain JSON-safe data (`schema.py`), so the whole Core can be eval'd offline
against `goldenset/golden.json`.
"""
