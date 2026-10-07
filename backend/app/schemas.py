"""Request/response models for the HTTP surface. Kept separate from `models.py` so the API shape
can change without touching the DB shape (and so the frontend has one place to read it from)."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .models import Bucket, MessageRole, NudgeType, RequestStatus, RequestType


# --- auth ---------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    display_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    display_name: str | None = None
    is_active: bool


# --- employees ----------------------------------------------------------------

class PayPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    name: str
    jurisdiction: str
    ot_threshold: str
    ot_rate_bands: str
    saturday_ot_rate: str | None
    night_premium: str
    dsr_rule: str
    tolerance: str
    banking_cycle: str


class EmployeeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    first_name: str
    role: str
    site: str
    company: str
    manager_name: str
    language: str
    phone_number: str


class BankedHoursOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    balance_minutes: int
    expiring_minutes: int
    reset_date: date
    cycle: str


class OvertimeAccrualOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_minutes: int
    trace_day: str | None
    trace_extra_minutes: int | None
    trace_rate_applied: str | None
    trace_rule: str | None
    trace_weekday_rate: str | None


class LastAbsenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    absence_date: date
    absence_type: str


class ExpectedShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    next_shift_when: str
    next_shift_time: str
    next_shift_site: str
    week_hours_label: str
    next_holiday_name: str | None
    next_holiday_date: date | None
    working_the_holiday: bool


class EmployeeDetail(EmployeeSummary):
    pay_policy: PayPolicyOut
    banked_hours: BankedHoursOut | None
    pto_days_available: float | None
    overtime_accrual: OvertimeAccrualOut | None
    last_absence: LastAbsenceOut | None
    expected_shift: ExpectedShiftOut | None
    requests: list["RequestOut"]


# --- requests (bucket E) ------------------------------------------------------

class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str | None = None
    type: RequestType
    status: RequestStatus
    detail: str
    swap_candidates: list[Any] | None
    decided_by: str | None
    decided_at: datetime | None
    decision_note: str | None
    created_at: datetime


class DecideRequest(BaseModel):
    decision: Literal["approved", "denied"]
    note: str | None = None


def request_out(request) -> RequestOut:
    """`RequestOut` + the employee's name, which the manager queue always needs alongside it."""
    out = RequestOut.model_validate(request, from_attributes=True)
    return out.model_copy(update={"employee_name": request.employee.name})


# --- chat ---------------------------------------------------------------------

class ChatRequest(BaseModel):
    employee_id: uuid.UUID
    message: str
    flow_state: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    reply: str
    bucket: str
    facts_used: dict[str, Any]
    guardrail_fallback: bool
    flow_state: dict[str, Any] | None = None
    request_created: RequestOut | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    text: str
    bucket: Bucket | None
    facts_used: dict[str, Any] | None
    guardrail_fallback: bool
    created_at: datetime


# --- nudges -------------------------------------------------------------------

class NudgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    type: NudgeType
    message: str
    acted_on: bool
    resulting_request_id: uuid.UUID | None
    created_at: datetime


class TriggerNudgeRequest(BaseModel):
    employee_id: uuid.UUID
    nudge_type: NudgeType


EmployeeDetail.model_rebuild()
