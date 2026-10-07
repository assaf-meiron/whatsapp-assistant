"""Stage ① — classify one inbound message into a capability bucket.

One forced tool call on the cheap model. No DB, no retrieval: this stage decides *what kind of
question was asked*, and `app/pipeline_adapter.py` decides what to fetch for it.
"""
from __future__ import annotations

from . import config, taxonomy
from .schema import IntentResult

_FLOW_ACTIONS = ("confirm", "cancel")
_REQUEST_TYPES = tuple(name for name, _ in taxonomy.REQUEST_TYPES)

INTENT_TOOL = {
    "name": "record_intent",
    "description": "Record the classification of one inbound employee message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "bucket": {
                "type": "string",
                "enum": taxonomy.CLASSIFIABLE_BUCKETS,
                "description": "The capability bucket that answers this message.",
            },
            "request_type": {
                "type": "string",
                "enum": list(_REQUEST_TYPES),
                "description": "Only when bucket is e_do_something: which of the two v1 request "
                               "types the employee wants filed.",
            },
            "flow_action": {
                "type": "string",
                "enum": list(_FLOW_ACTIONS),
                "description": "Only when a confirmation is pending and this message answers it: "
                               "confirm to send the request, cancel to drop it.",
            },
            "detected_date_label": {
                "type": "string",
                "description": "Only for a NEW request: the date phrase verbatim as the employee "
                               "wrote it (e.g. 'friday', 'tomorrow', 'sexta'). Never resolved, "
                               "reformatted, or invented.",
            },
        },
        "required": ["bucket"],
    },
}

_SYSTEM = [
    {
        "type": "text",
        "text": taxonomy.render_taxonomy() + "\n\n" + taxonomy.CLASSIFICATION_RUBRIC,
        "cache_control": config.CACHE_CONTROL,
    }
]


def classify_intent(message: str, has_pending_flow: bool) -> IntentResult:
    """Classify `message`; `has_pending_flow` is True when an unanswered yes/no is outstanding."""
    client = config.get_client()

    flow_state = (
        "A confirmation IS pending: the assistant has offered to file a request and is waiting "
        "for the employee's yes or no."
        if has_pending_flow
        else "No confirmation is pending."
    )

    response = client.messages.create(
        model=config.MODEL_INTENT,
        max_tokens=config.MAX_TOKENS_INTENT,
        system=_SYSTEM,
        tools=[INTENT_TOOL],
        tool_choice={"type": "tool", "name": INTENT_TOOL["name"]},
        messages=[
            {
                "role": "user",
                "content": f"{flow_state}\n\nEmployee message:\n{message}",
            }
        ],
    )

    payload = next(
        (block.input for block in response.content if block.type == "tool_use"),
        None,
    )
    if not isinstance(payload, dict):
        return IntentResult(bucket="unresolved")
    return _coerce(payload, has_pending_flow=has_pending_flow)


def _coerce(payload: dict, *, has_pending_flow: bool) -> IntentResult:
    """Clamp the tool payload to the contract — the model may still emit a stray field."""
    bucket = payload.get("bucket")
    if bucket not in taxonomy.CLASSIFIABLE_BUCKETS:
        bucket = "unresolved"

    request_type = payload.get("request_type")
    if bucket != "e_do_something" or request_type not in _REQUEST_TYPES:
        request_type = None

    flow_action = payload.get("flow_action")
    if not has_pending_flow or flow_action not in _FLOW_ACTIONS:
        flow_action = None

    date_label = payload.get("detected_date_label")
    if not isinstance(date_label, str) or not date_label.strip():
        date_label = None
    else:
        date_label = date_label.strip()

    # A confirm/cancel is a turn in the pending request flow: it always belongs to bucket E, and it
    # never carries a fresh request of its own.
    if flow_action is not None:
        bucket = "e_do_something"
        request_type, date_label = None, None

    return IntentResult(
        bucket=bucket,
        request_type=request_type,
        flow_action=flow_action,
        detected_date_label=date_label,
    )
