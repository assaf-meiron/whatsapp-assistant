"""The system of record for the employee's computed state — what the Assistant Core's
`retrieve.py` reads and what `seed.py` populates from the prototype's fake data.

`Employee` is the bound identity (phone number + PIN step-up, spec §7); `PayPolicy` is the
employee's *actual* plain-English policy (bucket D never answers from a generic KB). The
per-employee state tables (`BankedHoursState`, `PTOBalance`, `OvertimeAccrual`, `LastAbsence`,
`ExpectedShift`) are bucket A/B's grounding source. `Request` is the bucket-E write path — always
`pending` until a `User` (manager) decides it, never auto-applied (spec §5's legal firebreak).
`Nudge` is the proactive catalog (spec §6); `ConversationMessage` is the chat log **and** the audit
trail the eval harness / guardrail check every reply against.
"""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# --- enums ---------------------------------------------------------------------

class Bucket(str, enum.Enum):
    """The capability buckets a message resolves to (spec §4). C is out of v1 scope — it depends
    on the unbuilt WhyPay trace service (spec §9) — but the code stays for future wiring."""
    a_where_i_stand = "a_where_i_stand"
    b_whats_expected = "b_whats_expected"
    c_why_my_number = "c_why_my_number"       # deferred — no retrieval/phrase path wired in v1
    d_how_im_paid = "d_how_im_paid"
    e_do_something = "e_do_something"
    unresolved = "unresolved"


class RequestType(str, enum.Enum):
    """v1 catalog is deliberately narrow (spec §5) — scheduling-intent only, never a punch."""
    time_off = "time_off"
    shift_swap = "shift_swap"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"


class NudgeType(str, enum.Enum):
    """The v1 nudge catalog (spec §6)."""
    bank_expiry = "bank_expiry"
    ot_above_usual = "ot_above_usual"
    pay_different_heads_up = "pay_different_heads_up"
    request_status_change = "request_status_change"
    schedule_changed = "schedule_changed"
    missing_punch_detected = "missing_punch_detected"  # notify-only — never files a correction (spec §5)


class MessageRole(str, enum.Enum):
    employee = "employee"
    assistant = "assistant"


class AuthTier(str, enum.Enum):
    """Identity tiers (spec §7): tier 0 covers schedule/policy-Q&A/coarse balances off the bound
    phone number alone; tier 1 (PIN step-up) gates exact pay figures and any request submission."""
    tier_0 = "tier_0"
    tier_1 = "tier_1"


# --- auth: manager/approver login (mirrors lawtrack-ai's User) -----------------

class User(Base):
    """A manager/approver login — backs the "a human approves every request" firebreak (spec §5).
    Employees never log in this way; they're identified by their bound phone number (`Employee`)."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- pay policy: the employee's actual policy, in plain fields -----------------

class PayPolicy(Base):
    """The comparison baseline for bucket D — the employee's *actual* pay policy, never a generic
    legal blurb. Mirrors the shape of `pay-policy-configuration.md`'s Paid Overtime / Hours
    Distribution / Tolerance / Special Rules tabs, flattened to the fields the assistant quotes."""
    __tablename__ = "pay_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # e.g. "br-retail-cashier"
    name: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(64))

    ot_threshold: Mapped[str] = mapped_column(String(255))          # "8 hours a day"
    ot_rate_bands: Mapped[str] = mapped_column(String(512))          # "first 2h +50%, beyond +70%"
    saturday_ot_rate: Mapped[str | None] = mapped_column(String(64), default=None)
    night_premium: Mapped[str] = mapped_column(String(255))          # "+20% between 22:00-05:00 ..."
    dsr_rule: Mapped[str] = mapped_column(String(255))                # weekly rest day rule
    tolerance: Mapped[str] = mapped_column(String(64))                # "10 minutes"
    banking_cycle: Mapped[str] = mapped_column(String(255))           # "monthly, resets last day of month"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employees: Mapped[list["Employee"]] = relationship(back_populates="pay_policy")


# --- employee: the bound identity -----------------------------------------------

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(128))
    site: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    manager_name: Mapped[str] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(16), default="en")   # phrase.py's reply language

    phone_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    pin_hash: Mapped[str | None] = mapped_column(String(255), default=None)  # tier-1 step-up (spec §7)

    pay_policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pay_policies.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pay_policy: Mapped["PayPolicy"] = relationship(back_populates="employees")
    banked_hours: Mapped["BankedHoursState | None"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    pto_balance: Mapped["PTOBalance | None"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    overtime_accrual: Mapped["OvertimeAccrual | None"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    last_absence: Mapped["LastAbsence | None"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    expected_shift: Mapped["ExpectedShift | None"] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    requests: Mapped[list["Request"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", order_by="Request.created_at.desc()"
    )
    nudges: Mapped[list["Nudge"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", order_by="Nudge.created_at.desc()"
    )
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", order_by="ConversationMessage.created_at"
    )


# --- bucket A: "where I stand" --------------------------------------------------

class BankedHoursState(Base):
    __tablename__ = "banked_hours_states"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), unique=True)

    balance_minutes: Mapped[int] = mapped_column(Integer)             # e.g. 14h30m -> 870
    expiring_minutes: Mapped[int] = mapped_column(Integer, default=0)  # amount that lapses at next reset
    reset_date: Mapped[date] = mapped_column(Date)
    cycle: Mapped[str] = mapped_column(String(64))                    # "monthly" / "2-month" / ...

    employee: Mapped["Employee"] = relationship(back_populates="banked_hours")


class PTOBalance(Base):
    __tablename__ = "pto_balances"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), unique=True)
    days_available: Mapped[float] = mapped_column(Integer)

    employee: Mapped["Employee"] = relationship(back_populates="pto_balance")


class OvertimeAccrual(Base):
    """This-period OT + the trace behind it (day/extra/rate/rule) — bucket A's "how much overtime"
    and the one bit of bucket-C-shaped detail v1 still answers literally (a canned trace, not a
    live query into the WhyPay trace service, which is deferred per spec §9)."""
    __tablename__ = "overtime_accruals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), unique=True)

    period_minutes: Mapped[int] = mapped_column(Integer)     # OT so far this pay period
    trace_day: Mapped[str | None] = mapped_column(String(64), default=None)
    trace_extra_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    trace_rate_applied: Mapped[str | None] = mapped_column(String(32), default=None)
    trace_rule: Mapped[str | None] = mapped_column(String(255), default=None)
    trace_weekday_rate: Mapped[str | None] = mapped_column(String(32), default=None)

    employee: Mapped["Employee"] = relationship(back_populates="overtime_accrual")


class LastAbsence(Base):
    __tablename__ = "last_absences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), unique=True)
    absence_date: Mapped[date] = mapped_column(Date)
    absence_type: Mapped[str] = mapped_column(String(128))  # "paid vacation day", ...

    employee: Mapped["Employee"] = relationship(back_populates="last_absence")


# --- bucket B: "what's expected of me" ------------------------------------------

class ExpectedShift(Base):
    __tablename__ = "expected_shifts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), unique=True)

    next_shift_when: Mapped[str] = mapped_column(String(128))   # "tomorrow, Wed 15 Jul"
    next_shift_time: Mapped[str] = mapped_column(String(64))    # "08:00-17:00"
    next_shift_site: Mapped[str] = mapped_column(String(255))
    week_hours_label: Mapped[str] = mapped_column(String(128))  # "44h across 6 days"
    next_holiday_name: Mapped[str | None] = mapped_column(String(255), default=None)
    next_holiday_date: Mapped[date | None] = mapped_column(Date, default=None)
    working_the_holiday: Mapped[bool] = mapped_column(Boolean, default=False)

    employee: Mapped["Employee"] = relationship(back_populates="expected_shift")


# --- bucket E: requests (write -> human approval) -------------------------------

class Request(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))

    type: Mapped[RequestType] = mapped_column(SAEnum(RequestType))
    status: Mapped[RequestStatus] = mapped_column(SAEnum(RequestStatus), default=RequestStatus.pending)
    detail: Mapped[str] = mapped_column(String(255))          # e.g. "Fri 25 Jul 2026"
    swap_candidates: Mapped[list | None] = mapped_column(JSON, default=None)  # shift_swap only

    decided_by: Mapped[str | None] = mapped_column(String(255), default=None)  # User.username
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    decision_note: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="requests")


# --- nudges: the proactive catalog (spec §6) ------------------------------------

class Nudge(Base):
    __tablename__ = "nudges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))

    type: Mapped[NudgeType] = mapped_column(SAEnum(NudgeType))
    message: Mapped[str] = mapped_column(Text)
    acted_on: Mapped[bool] = mapped_column(Boolean, default=False)
    resulting_request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("requests.id", ondelete="SET NULL"), default=None
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="nudges")


# --- conversation log: chat history + the audit trail ---------------------------

class ConversationMessage(Base):
    """One turn. `facts_used` is the exact structured payload `retrieve.py` handed to `phrase.py` —
    the audit trail `guardrail.py` checks the reply against and the eval harness scores."""
    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))

    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole))
    text: Mapped[str] = mapped_column(Text)
    bucket: Mapped[Bucket | None] = mapped_column(SAEnum(Bucket), default=None)
    facts_used: Mapped[dict | None] = mapped_column(JSON, default=None)
    guardrail_fallback: Mapped[bool] = mapped_column(Boolean, default=False)  # true if phrase.py's
    # output failed the number-grounding check and a templated fallback was used instead

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped["Employee"] = relationship(back_populates="messages")
