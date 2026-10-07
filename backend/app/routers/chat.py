"""Chat — one turn of the employee conversation, plus the persisted history.

Unauthenticated, like `employees.py`: in production the channel adapter has already established
identity from the bound phone number. `flow_state` is carried by the caller and echoed back, so the
Assistant Core stays stateless between turns (a WhatsApp webhook has no session either).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import pipeline_adapter
from ..db import get_db
from ..models import ConversationMessage
from ..schemas import ChatRequest, ChatResponse, MessageOut, request_out
from .employees import load_employee

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)):
    if not body.message.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "message may not be empty")
    employee = load_employee(body.employee_id, db)

    result = pipeline_adapter.handle_message(db, employee, body.message, body.flow_state)
    created = result["request_created"]

    return ChatResponse(
        reply=result["reply"],
        bucket=result["bucket"],
        facts_used=result["facts_used"],
        guardrail_fallback=result["guardrail_fallback"],
        flow_state=result["flow_state"],
        request_created=request_out(created) if created else None,
    )


@router.get("/history", response_model=list[MessageOut])
def history(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    """The conversation log — so switching employees in the demo doesn't lose the thread."""
    load_employee(employee_id, db)
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.employee_id == employee_id)
        .order_by(ConversationMessage.created_at)
        .all()
    )
