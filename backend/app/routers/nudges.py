"""Nudges — the proactive half of the interaction model (spec §6).

Real nudges fire from engine events (a bank approaching reset, a published schedule). There's no
scheduler in this build, so `POST /trigger` is the demo's stand-in: it builds the nudge from the
employee's current rows, exactly as the event-driven version would.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import pipeline_adapter
from ..db import get_db
from ..models import Nudge
from ..schemas import NudgeOut, TriggerNudgeRequest
from .employees import load_employee

router = APIRouter(prefix="/api/nudges", tags=["nudges"])


@router.get("", response_model=list[NudgeOut])
def list_nudges(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    load_employee(employee_id, db)
    return (
        db.query(Nudge)
        .filter(Nudge.employee_id == employee_id)
        .order_by(Nudge.created_at.desc())
        .all()
    )


@router.post("/trigger", response_model=NudgeOut)
def trigger(body: TriggerNudgeRequest, db: Session = Depends(get_db)):
    employee = load_employee(body.employee_id, db)
    return pipeline_adapter.trigger_nudge(db, employee, body.nudge_type)
