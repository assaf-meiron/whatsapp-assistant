"""Adapter: bridge the DB (`app/`) and the channel-independent Assistant Core (`pipeline/`).

The split enforces the spec's architecture principle (§3): **the LLM phrases, it never computes.**
Retrieval below is plain SQLAlchemy — every number in a reply is read out of the employee's own
rows and handed to `phrase.py` as a pre-formatted `facts` dict, then `guardrail.py` checks the
phrased reply back against that same dict. `pipeline/` never sees a session.

`handle_message` also owns the bucket-E flow state machine (the prototype's `resolve()` + `ctx.flow`
moved server-side): a fresh "I need Friday off" only *proposes* a request; the `Request` row is
written on the confirming turn. Nothing is ever auto-applied — a manager decides it (spec §5).
"""
from __future__ import annotations

import logging
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from .models import (
    Bucket,
    ConversationMessage,
    Employee,
    MessageRole,
    Nudge,
    NudgeType,
    Request,
    RequestStatus,
    RequestType,
)

log = logging.getLogger("whatsapp_assistant")

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PIPELINE_DIR = _BACKEND_DIR / "pipeline"


def _pipeline():
    """Import the Assistant Core lazily — so app startup never needs an Anthropic API key.

    Both dirs go on `sys.path`: `backend/` makes `pipeline` importable as a package, and
    `backend/pipeline/` lets its modules import each other flat.
    """
    for p in (_BACKEND_DIR, _PIPELINE_DIR):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from pipeline import guardrail, intent, phrase  # noqa: PLC0415

    return intent, phrase, guardrail


# --- display formatting -------------------------------------------------------
# The engine stores minutes and dates; the assistant quotes the strings the prototype showed.
# Formatting happens here (not in `pipeline/`) so the guardrail compares like for like.

def _now() -> datetime:
    """Chat rows are timestamped in Python, not by the DB: `func.now()` is second-granular on
    SQLite and transaction-time on Postgres, either of which ties the two rows of a turn and loses
    the order the conversation actually happened in."""
    return datetime.now(timezone.utc)


def _hm(minutes: int) -> str:
    return f"{minutes // 60}h {minutes % 60:02d}m"


def _day(d: date) -> str:
    return f"{d.day} {d.strftime('%b')} {d.year}"


def _weekday(d: date) -> str:
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')} {d.year}"


def _days(n: float) -> int | float:
    return int(n) if float(n).is_integer() else n


def _request_status_label(request: Request) -> str:
    if request.status is RequestStatus.pending:
        return "Pending"
    return f"{request.status.value.capitalize()} by {request.decided_by}"


# --- retrieval: bucket -> the exact facts needed to answer --------------------

def _facts_a(employee: Employee) -> dict:
    """Bucket A — "where I stand": balances, accruals, last absence, request status, and the canned
    rate trace behind overtime already worked (bucket C is deferred, so "why was my OT only 30%"
    is answered from `OvertimeAccrual`'s stored trace — see `pipeline/taxonomy.py`)."""
    facts: dict = {"manager_name": employee.manager_name}

    bank = employee.banked_hours
    facts["has_hours_bank"] = bank is not None
    if bank:
        facts["bank_balance"] = _hm(bank.balance_minutes)
        facts["bank_cycle"] = bank.cycle
        facts["bank_reset_date"] = _day(bank.reset_date)
        if bank.expiring_minutes:
            facts["bank_expiring"] = _hm(bank.expiring_minutes)
    else:
        # Not every policy has an hours bank. Say so from the policy rather than implying a zero.
        facts["banking_cycle_policy"] = employee.pay_policy.banking_cycle

    if employee.pto_balance:
        facts["pto_days_available"] = _days(employee.pto_balance.days_available)

    ot = employee.overtime_accrual
    if ot:
        facts["overtime_this_period"] = _hm(ot.period_minutes)
        if ot.trace_day:
            facts["trace_day"] = ot.trace_day
            facts["trace_rate_applied"] = ot.trace_rate_applied
            facts["trace_rule"] = ot.trace_rule
            if ot.trace_extra_minutes is not None:
                facts["trace_extra"] = _hm(ot.trace_extra_minutes)
            if ot.trace_weekday_rate:
                facts["trace_weekday_rate"] = ot.trace_weekday_rate

    if employee.last_absence:
        facts["last_absence_date"] = _day(employee.last_absence.absence_date)
        facts["last_absence_type"] = employee.last_absence.absence_type

    facts["pending_requests"] = [
        {
            "type": "Time off" if r.type is RequestType.time_off else "Shift swap",
            "detail": r.detail,
            "status": _request_status_label(r),
            "awaiting": (
                f"awaiting {employee.manager_name}"
                if r.status is RequestStatus.pending
                else None
            ),
        }
        for r in employee.requests
    ]
    return facts


def _facts_b(employee: Employee) -> dict:
    """Bucket B — "what's expected of me": next shift, week, holiday."""
    shift = employee.expected_shift
    if not shift:
        return {}
    facts = {
        "next_shift_when": shift.next_shift_when,
        "next_shift_time": shift.next_shift_time,
        "next_shift_site": shift.next_shift_site,
        "week_hours": shift.week_hours_label,
    }
    if shift.next_holiday_name and shift.next_holiday_date:
        facts["next_holiday_name"] = shift.next_holiday_name
        facts["next_holiday_date"] = _weekday(shift.next_holiday_date)
        facts["working_the_holiday"] = shift.working_the_holiday
    return facts


def _facts_d(employee: Employee) -> dict:
    """Bucket D — "how I'm compensated": the employee's *actual* policy, never a generic blurb."""
    p = employee.pay_policy
    facts = {
        "ot_threshold": p.ot_threshold,
        "ot_rate_bands": p.ot_rate_bands,
        "night_premium": p.night_premium,
        "dsr_rule": p.dsr_rule,
        "tolerance": p.tolerance,
        "banking_cycle": p.banking_cycle,
    }
    if p.saturday_ot_rate:
        facts["saturday_ot_rate"] = p.saturday_ot_rate
    return facts


_RETRIEVE = {
    Bucket.a_where_i_stand: _facts_a,
    Bucket.b_whats_expected: _facts_b,
    Bucket.d_how_im_paid: _facts_d,
}


# --- bucket E: date labels + flow state ---------------------------------------
# Fixed demo dates (the prototype's DAY_DATE), so the story reads the same whenever it's shown.
# "Today" in the seeded dataset is Tue 14 Jul 2026.

_DAY_LABEL = {
    "tomorrow": "Wed 15 Jul",
    "amanha": "Wed 15 Jul",
    "amanhã": "Wed 15 Jul",
    "friday": "Fri 17 Jul",
    "sexta": "Fri 17 Jul",
    "saturday": "Sat 18 Jul",
    "sabado": "Sat 18 Jul",
    "sábado": "Sat 18 Jul",
    "sunday": "Sun 19 Jul",
    "domingo": "Sun 19 Jul",
    "monday": "Mon 20 Jul",
    "tuesday": "Tue 21 Jul",
    "wednesday": "Wed 22 Jul",
    "thursday": "Thu 23 Jul",
}
_DEFAULT_DAY_LABEL = "Fri 17 Jul"
_DISPLAY_DATE = re.compile(r"^[A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2}")

_SWAP_CANDIDATES = ["Bruno", "Carla", "Diego"]


def _resolve_day(label: str | None) -> str:
    """Map a free-text day phrase to a concrete display date. Demo-grade: a fixed lookup, no
    calendar math — the seeded dataset is pinned to one week."""
    if not label:
        return _DEFAULT_DAY_LABEL
    if _DISPLAY_DATE.match(label):
        return label
    lowered = label.lower()
    for word, display in _DAY_LABEL.items():
        if word in lowered:
            return display
    return _DEFAULT_DAY_LABEL


def _request_type(raw: str | None) -> RequestType:
    try:
        return RequestType(raw or "time_off")
    except ValueError:
        return RequestType.time_off


def _facts_e(employee: Employee, req_type: RequestType, detail: str, stage: str) -> dict:
    """`stage` drives the whole shape of the reply — `pipeline/phrase.py` branches on it, since the
    same bucket covers "shall I send this?", "it's sent", and "cancelled"."""
    facts = {
        "stage": stage,
        "request_type": req_type.value,
        "request_detail": detail,
        "manager_name": employee.manager_name,
    }
    if req_type is RequestType.shift_swap:
        facts["swap_candidates"] = list(_SWAP_CANDIDATES)
    elif employee.pto_balance:
        facts["pto_days_available"] = _days(employee.pto_balance.days_available)
    return facts


def _swap_detail(employee: Employee, day_label: str) -> str:
    shift = employee.expected_shift
    return f"{day_label}, {shift.next_shift_time}" if shift else day_label


# --- phrasing + guardrail -----------------------------------------------------

def _phrase_and_check(employee: Employee, facts: dict, bucket: str) -> tuple[str, bool]:
    """Phrase the facts, then check the phrasing against them. Returns (reply, used_fallback).

    An empty `facts` dict has nothing to ground against (the `unresolved` bucket), so the check is
    skipped. A phrasing failure — the Anthropic API is an external boundary — falls back to the
    same templated reply the guardrail would have used.
    """
    _, phrase, guardrail = _pipeline()

    try:
        reply = phrase.phrase_reply(facts, bucket, employee.first_name, employee.language)
    except Exception:
        log.exception("phrase_reply failed for bucket %s — serving the templated fallback", bucket)
        return guardrail.check_grounded("", facts, employee.language).fallback_reply, True

    if not facts:
        return reply, False

    check = guardrail.check_grounded(reply, facts, employee.language)
    return (reply, False) if check.is_grounded else (check.fallback_reply, True)


# --- persistence --------------------------------------------------------------

def _log_turn(
    db: Session,
    employee: Employee,
    message: str,
    reply: str,
    bucket: Bucket,
    facts: dict,
    fallback: bool,
) -> None:
    asked_at = _now()
    db.add(
        ConversationMessage(
            employee_id=employee.id,
            role=MessageRole.employee,
            text=message,
            created_at=asked_at,
        )
    )
    db.add(
        ConversationMessage(
            employee_id=employee.id,
            role=MessageRole.assistant,
            text=reply,
            bucket=bucket,
            facts_used=facts,
            guardrail_fallback=fallback,
            created_at=asked_at + timedelta(milliseconds=1),
        )
    )


# --- the entry point ----------------------------------------------------------

def handle_message(
    db: Session, employee: Employee, message: str, flow_state: dict | None
) -> dict:
    """One conversational turn. `flow_state` is the caller's echo of the previous turn's
    `flow_state` — the channel adapter (or, here, the frontend) carries it, so the Core stays
    stateless between turns."""
    intent, _, _ = _pipeline()
    result = intent.classify_intent(message, has_pending_flow=flow_state is not None)

    try:
        bucket = Bucket(result.bucket)
    except ValueError:
        bucket = Bucket.unresolved

    next_flow: dict | None = None
    created: Request | None = None

    if bucket is Bucket.e_do_something:
        action = result.flow_action
        if action == "cancel" and flow_state:
            req_type = _request_type(flow_state.get("type"))
            facts = _facts_e(employee, req_type, flow_state.get("detail", ""), "cancelled")
        elif action == "confirm" and flow_state:
            req_type = _request_type(flow_state.get("type"))
            detail = flow_state.get("detail", _DEFAULT_DAY_LABEL)
            created = Request(
                employee_id=employee.id,
                type=req_type,
                status=RequestStatus.pending,
                detail=detail,
                swap_candidates=(
                    list(_SWAP_CANDIDATES) if req_type is RequestType.shift_swap else None
                ),
            )
            db.add(created)
            facts = _facts_e(employee, req_type, detail, "submitted")
        else:
            # A fresh ask (or a confirm whose flow got lost): propose, don't write.
            req_type = _request_type(result.request_type)
            day = _resolve_day(result.detected_date_label)
            detail = _swap_detail(employee, day) if req_type is RequestType.shift_swap else day
            facts = _facts_e(employee, req_type, detail, "awaiting_confirmation")
            next_flow = {"type": req_type.value, "detail": detail}
    else:
        facts = _RETRIEVE.get(bucket, lambda _e: {})(employee)

    reply, fallback = _phrase_and_check(employee, facts, bucket.value)
    _log_turn(db, employee, message, reply, bucket, facts, fallback)
    db.commit()
    if created:
        db.refresh(created)

    return {
        "reply": reply,
        "bucket": bucket.value,
        "facts_used": facts,
        "guardrail_fallback": fallback,
        "flow_state": next_flow,
        "request_created": created,
    }


# --- nudges (spec §6) ---------------------------------------------------------
# Templated in plain code, not phrased by the model: a push the employee didn't ask for is the
# worst place for an invented number, and every value below comes straight off their own rows.

def _status_change_message(employee: Employee, request: Request) -> str:
    kind = request.type.value.replace("_", " ")
    if request.status is RequestStatus.pending:
        return (
            f"{employee.first_name}, your {kind} request for {request.detail} is still with "
            f"{employee.manager_name}."
        )
    return (
        f"{employee.first_name}, your {kind} request for {request.detail} was "
        f"{request.status.value} by {request.decided_by}."
        + (f" Note: {request.decision_note}" if request.decision_note else "")
    )


def _nudge_message(employee: Employee, nudge_type: NudgeType) -> str:
    name = employee.first_name
    bank = employee.banked_hours
    ot = employee.overtime_accrual
    shift = employee.expected_shift

    if nudge_type is NudgeType.bank_expiry:
        if not bank:
            return (
                f"Heads-up, {name} — your policy has no hours bank, so nothing expires: "
                f"{employee.pay_policy.banking_cycle}."
            )
        return (
            f"Heads-up, {name} — your hours bank resets on {_day(bank.reset_date)} and you'll "
            f"lose {_hm(bank.expiring_minutes)} if they go unused. Want to turn them into a day off?"
        )

    if nudge_type is NudgeType.ot_above_usual:
        if not ot:
            return f"Heads-up, {name} — no overtime is recorded for you this pay period."
        return (
            f"{name}, you're at {_hm(ot.period_minutes)} of overtime this pay period — higher "
            f"than your usual. Want to see how it's paid?"
        )

    if nudge_type is NudgeType.pay_different_heads_up:
        if not ot:
            return f"{name}, your next payslip should look like your usual one. Nothing's changed."
        return (
            f"{name}, your next payslip will look a bit higher than usual — it includes the "
            f"{_hm(ot.period_minutes)} of overtime you did this period. Nothing's wrong! "
            f"Want the breakdown?"
        )

    if nudge_type is NudgeType.request_status_change:
        latest = next(
            (r for r in employee.requests if r.decided_at),
            next((r for r in employee.requests if r.status is RequestStatus.pending), None),
        )
        if not latest:
            return f"{name}, you have no requests in flight right now."
        return _status_change_message(employee, latest)

    if nudge_type is NudgeType.schedule_changed:
        if not shift:
            return f"{name}, your schedule was updated — open the app for the new shifts."
        return (
            f"{name}, your schedule was updated. Your next shift is {shift.next_shift_when}, "
            f"{shift.next_shift_time} at {shift.next_shift_site}."
        )

    # missing_punch_detected — notify only, never files a correction (spec §5).
    return (
        f"{name}, no clock-out was recorded for your last shift. I can't fix a time record — "
        f"please contact {employee.manager_name} to have it corrected."
    )


def trigger_nudge(db: Session, employee: Employee, nudge_type: NudgeType) -> Nudge:
    pushed_at = _now()
    nudge = Nudge(
        employee_id=employee.id,
        type=nudge_type,
        message=_nudge_message(employee, nudge_type),
        created_at=pushed_at,
    )
    db.add(nudge)
    db.add(
        ConversationMessage(
            employee_id=employee.id,
            role=MessageRole.assistant,
            text=nudge.message,
            created_at=pushed_at,
        )
    )
    db.commit()
    db.refresh(nudge)
    return nudge


def decide_request(
    db: Session, request: Request, decision: RequestStatus, username: str, note: str | None
) -> Request:
    """The human half of the firebreak (spec §5) — plus the status-change nudge that closes the
    loop back to the employee."""
    decided_at = _now()
    request.status = decision
    request.decided_by = username
    request.decided_at = decided_at
    request.decision_note = note
    db.flush()

    employee = request.employee
    message = _status_change_message(employee, request)
    db.add(
        Nudge(
            employee_id=employee.id,
            type=NudgeType.request_status_change,
            message=message,
            created_at=decided_at,
        )
    )
    db.add(
        ConversationMessage(
            employee_id=employee.id,
            role=MessageRole.assistant,
            text=message,
            created_at=decided_at,
        )
    )
    db.commit()
    db.refresh(request)
    return request
