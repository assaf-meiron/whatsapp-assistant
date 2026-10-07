"""Employees — the roster and one employee's full computed state.

**Unauthenticated on purpose.** In production the employee's identity comes from the phone number
bound to the WhatsApp conversation (spec §7 tier 0); there's no WhatsApp integration in this build,
so the demo's employee switcher stands in for that binding. Add the channel adapter and this
becomes a lookup by `phone_number` instead of a list.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Employee
from ..schemas import EmployeeDetail, EmployeeSummary, request_out

router = APIRouter(prefix="/api/employees", tags=["employees"])


def load_employee(employee_id: uuid.UUID, db: Session) -> Employee:
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such employee")
    return employee


@router.get("", response_model=list[EmployeeSummary])
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).order_by(Employee.name).all()


@router.get("/{employee_id}", response_model=EmployeeDetail)
def get_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    employee = load_employee(employee_id, db)
    return EmployeeDetail(
        id=employee.id,
        name=employee.name,
        first_name=employee.first_name,
        role=employee.role,
        site=employee.site,
        company=employee.company,
        manager_name=employee.manager_name,
        language=employee.language,
        phone_number=employee.phone_number,
        pay_policy=employee.pay_policy,
        banked_hours=employee.banked_hours,
        pto_days_available=employee.pto_balance.days_available if employee.pto_balance else None,
        overtime_accrual=employee.overtime_accrual,
        last_absence=employee.last_absence,
        expected_shift=employee.expected_shift,
        requests=[request_out(r) for r in employee.requests],
    )
