"""Requests — the manager side of the legal firebreak (spec §5).

Every route here is manager-authenticated: the assistant *originates* a request, a human decides it,
and nothing the employee says can approve their own. Deciding also queues a `request_status_change`
nudge back to the employee (spec §6).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import pipeline_adapter
from ..db import get_db
from ..models import Request, RequestStatus, User
from ..schemas import DecideRequest, RequestOut, request_out
from ..security import get_current_user

router = APIRouter(prefix="/api/requests", tags=["requests"])


@router.get("", response_model=list[RequestOut])
def list_requests(
    status_filter: RequestStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Request)
    if status_filter:
        query = query.filter(Request.status == status_filter)
    return [request_out(r) for r in query.order_by(Request.created_at.desc()).all()]


@router.post("/{request_id}/decide", response_model=RequestOut)
def decide(
    request_id: uuid.UUID,
    body: DecideRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    request = db.get(Request, request_id)
    if not request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such request")
    if request.status is not RequestStatus.pending:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"request was already {request.status.value}"
        )
    decided = pipeline_adapter.decide_request(
        db, request, RequestStatus(body.decision), user.username, body.note
    )
    return request_out(decided)
