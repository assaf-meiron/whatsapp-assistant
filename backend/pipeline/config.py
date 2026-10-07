"""Client + model configuration for the Assistant Core.

Models per stage: Haiku 4.5 for intent classification (cheap, high-volume, a forced tool call),
Sonnet 5 for phrasing (the only stage a human reads verbatim). Pricing ($/1M in/out, current as of
the API reference this was written against): Haiku 4.5 $1/$5 · Sonnet 5 $3/$15.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# backend/pipeline/config.py -> pipeline -> backend
_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines from a gitignored .env into os.environ (never overriding existing vars).

    Mirrors app/config.py's loader: pipeline scripts run standalone (`eval_harness.py`, not the
    FastAPI app), so ANTHROPIC_API_KEY in backend/.env would otherwise never reach os.environ.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and val:
            os.environ.setdefault(key, val)


_load_env_file(_BACKEND_DIR / ".env")

MODEL_INTENT = "claude-haiku-4-5"   # ① intent — one forced tool call, latency- and cost-sensitive
MODEL_PHRASE = "claude-sonnet-5"    # ② phrase — prose quality is the whole job

MAX_TOKENS_INTENT = 1024   # a single record_intent tool call
MAX_TOKENS_PHRASE = 1024   # a WhatsApp bubble, not an essay

# Cached-prefix minimums differ per model: 4096 tokens on Haiku 4.5, 1024 on Sonnet 5. Our system
# blocks sit below both, so `cache_control` is a no-op today — it is set so caching starts working
# the moment the taxonomy or the phrasing rules grow, rather than needing to be remembered then.
CACHE_CONTROL = {"type": "ephemeral"}


def get_client():
    """Return an Anthropic client, or exit with a clear message if the SDK is missing."""
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic SDK not installed — run: pip install -r requirements.txt")
    # A bare client also works after `ant auth login`; only warn if nothing is configured.
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        print("note: no ANTHROPIC_API_KEY set — relying on an `ant auth login` profile if present.",
              file=sys.stderr)
    return anthropic.Anthropic()
