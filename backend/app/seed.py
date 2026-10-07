"""Idempotent demo seed — transcribes the React prototype's hard-coded sample data
(`EMP` + `DATA` + `SEED_REQUESTS` in `prototype/src/app.jsx`) into database rows, so the
assistant answers Ana Souza's questions from real tables instead of a client-side constant.

Three more employees follow, on three other jurisdictions' pay policies (US · India · Germany), so
the demo can show that bucket D resolves the employee's *actual* policy rather than a generic KB —
including two employees whose policies have **no hours bank at all**.

"Today" across the whole dataset is **Tue 14 Jul 2026** (the prototype's frame of reference).
`seed_if_empty(db, log)` returns immediately if any `Employee` already exists and commits once.
"""
from __future__ import annotations

from datetime import date

from .models import (
    BankedHoursState,
    Employee,
    ExpectedShift,
    LastAbsence,
    OvertimeAccrual,
    PayPolicy,
    PTOBalance,
    Request,
    RequestStatus,
    RequestType,
    User,
)
from .security import hash_password

# --- pay policies -------------------------------------------------------------
# `br-retail-cashier` is DATA.policy from the prototype, verbatim. The other three are written in
# the same plain-English voice the assistant quotes back.

POLICIES = [
    {
        "key": "br-retail-cashier",
        "name": "Brazil — Retail Standard (Comércio SP)",
        "jurisdiction": "BR",
        "ot_threshold": "8 hours a day",
        "ot_rate_bands": "the first 2 extra hours at +50%, anything beyond that at +70%",
        "saturday_ot_rate": "+30%",
        "night_premium": (
            "+20% (adicional noturno) between 22:00 and 05:00, and each night hour counts as 52m30s"
        ),
        "dsr_rule": "one paid weekly rest day (DSR) — normally your Sunday",
        "tolerance": "10 minutes",
        "banking_cycle": "a monthly cycle, resetting on the last day of each month",
    },
    {
        "key": "us-retail-tx",
        "name": "United States — Retail Hourly (Texas)",
        "jurisdiction": "US",
        "ot_threshold": "40 hours in a workweek",
        "ot_rate_bands": "1.5x your regular rate for every hour past 40 in the week",
        "saturday_ot_rate": None,
        "night_premium": "no night premium — neither federal law nor your policy adds one",
        "dsr_rule": "no state-mandated weekly rest day in Texas; your schedule targets two days off",
        "tolerance": "7 minutes (quarter-hour rounding)",
        "banking_cycle": "no hours bank — overtime is paid out in the same pay period it's worked",
    },
    {
        "key": "in-warehouse-ka",
        "name": "India — Warehouse (Karnataka)",
        "jurisdiction": "IN",
        "ot_threshold": "9 hours a day or 48 hours a week",
        "ot_rate_bands": "twice your ordinary rate (2x) for every overtime hour",
        "saturday_ot_rate": None,
        "night_premium": (
            "no statutory night premium; night-shift work needs your consent and transport home"
        ),
        "dsr_rule": "one full paid rest day every week — normally your Sunday",
        "tolerance": "5 minutes",
        "banking_cycle": "no hours bank — overtime is paid with the same month's wages",
    },
    {
        "key": "de-einzelhandel-nrw",
        "name": "Germany — Einzelhandel NRW",
        "jurisdiction": "DE",
        "ot_threshold": "8 hours a day (up to 10 if your 6-month average stays at 8)",
        "ot_rate_bands": (
            "extra hours are credited to your working-time account (Arbeitszeitkonto) as time off "
            "in lieu, not paid at a premium"
        ),
        "saturday_ot_rate": None,
        "night_premium": "+25% for hours worked between 23:00 and 06:00",
        "dsr_rule": (
            "Sundays are work-free by default; a worked Sunday must be compensated with a "
            "replacement rest day"
        ),
        "tolerance": "5 minutes",
        "banking_cycle": "a 6-month Arbeitszeitkonto averaging window",
    },
]

# --- employees + their computed state ----------------------------------------
# Ana's block is the prototype's EMP/DATA/SEED_REQUESTS, transcribed 1:1 (minutes for durations,
# real dates for display strings). The rest is plausible synthetic state for demo variety.

EMPLOYEES = [
    {
        "policy": "br-retail-cashier",
        "name": "Ana Souza",
        "first_name": "Ana",
        "role": "Cashier",
        "site": "Loja Centro",
        "company": "Rede Verde Supermercados",
        "manager_name": "Marcos",
        "language": "en",
        "phone_number": "+5511987654321",
        "bank": {
            "balance_minutes": 870,      # 14h 30m
            "expiring_minutes": 270,     # 4h 30m
            "reset_date": date(2026, 7, 31),
            "cycle": "monthly",
        },
        "pto_days": 12,
        "ot": {
            "period_minutes": 495,       # 8h 15m
            "trace_day": "Sat 5 Jul 2026",
            "trace_extra_minutes": 120,
            "trace_rate_applied": "+30%",
            "trace_rule": "Saturday overtime band (from your CCT)",
            "trace_weekday_rate": "+50%",
        },
        "last_absence": (date(2026, 6, 19), "paid vacation day"),
        "shift": {
            "next_shift_when": "tomorrow, Wed 15 Jul",
            "next_shift_time": "08:00-17:00",
            "next_shift_site": "Loja Centro",
            "week_hours_label": "44h across 6 days",
            "next_holiday_name": "Independência do Brasil",
            "next_holiday_date": date(2026, 9, 7),
            "working_the_holiday": False,
        },
        "requests": [(RequestType.time_off, "Fri 25 Jul 2026")],
    },
    {
        "policy": "us-retail-tx",
        "name": "Jordan Miller",
        "first_name": "Jordan",
        "role": "Sales Associate",
        "site": "Store #214, Austin TX",
        "company": "Northline Retail",
        "manager_name": "Dana",
        "language": "en",
        "phone_number": "+14155550123",
        "bank": None,  # no hours bank on a US hourly policy — OT is paid out
        "pto_days": 8,
        "ot": {
            "period_minutes": 180,       # 3h 00m
            "trace_day": "Fri 10 Jul 2026",
            "trace_extra_minutes": 60,
            "trace_rate_applied": "1.5x",
            "trace_rule": "hours past 40 in the workweek",
            "trace_weekday_rate": None,
        },
        "last_absence": (date(2026, 6, 29), "unpaid personal day"),
        "shift": {
            "next_shift_when": "Thursday, Thu 16 Jul",
            "next_shift_time": "10:00-18:30",
            "next_shift_site": "Store #214, Austin TX",
            "week_hours_label": "38h across 5 days",
            "next_holiday_name": "Labor Day",
            "next_holiday_date": date(2026, 9, 7),
            "working_the_holiday": True,
        },
        "requests": [],
    },
    {
        "policy": "in-warehouse-ka",
        "name": "Priya Nair",
        "first_name": "Priya",
        "role": "Warehouse Associate",
        "site": "Bengaluru DC",
        "company": "Sunveda Logistics",
        "manager_name": "Rakesh",
        "language": "en",
        "phone_number": "+919876543210",
        "bank": None,  # no hours bank — OT is paid with the month's wages
        "pto_days": 14,
        "ot": {
            "period_minutes": 330,       # 5h 30m
            "trace_day": "Mon 6 Jul 2026",
            "trace_extra_minutes": 90,
            "trace_rate_applied": "2x",
            "trace_rule": "hours past 9 in the day",
            "trace_weekday_rate": None,
        },
        "last_absence": (date(2026, 7, 2), "casual leave"),
        "shift": {
            "next_shift_when": "tomorrow, Wed 15 Jul",
            "next_shift_time": "09:00-18:00",
            "next_shift_site": "Bengaluru DC",
            "week_hours_label": "48h across 6 days",
            "next_holiday_name": "Independence Day",
            "next_holiday_date": date(2026, 8, 15),
            "working_the_holiday": False,
        },
        "requests": [],
    },
    {
        "policy": "de-einzelhandel-nrw",
        "name": "Lena Brandt",
        "first_name": "Lena",
        "role": "Sales Associate",
        "site": "Filiale Köln-Süd",
        "company": "GrünMarkt",
        "manager_name": "Stefan",
        "language": "de",
        "phone_number": "+4915112345678",
        "bank": {
            "balance_minutes": 1275,     # 21h 15m
            "expiring_minutes": 0,
            "reset_date": date(2026, 12, 31),
            "cycle": "6-month",
        },
        "pto_days": 18,
        "ot": {
            "period_minutes": 240,       # 4h 00m
            "trace_day": "Tue 7 Jul 2026",
            "trace_extra_minutes": 60,
            "trace_rate_applied": "time off in lieu",
            "trace_rule": "credited to your Arbeitszeitkonto instead of paid",
            "trace_weekday_rate": None,
        },
        "last_absence": (date(2026, 6, 12), "paid vacation day"),
        "shift": {
            "next_shift_when": "tomorrow, Wed 15 Jul",
            "next_shift_time": "07:00-15:30",
            "next_shift_site": "Filiale Köln-Süd",
            "week_hours_label": "37.5h across 5 days",
            "next_holiday_name": "Tag der Deutschen Einheit",
            "next_holiday_date": date(2026, 10, 3),
            "working_the_holiday": False,
        },
        "requests": [],
    },
]

# Security note: the demo login below is deliberately weak so the app is usable straight after
# `docker compose up`. It is a demo credential, not a default — replace it before any real
# deployment (`python -m app.manage_users passwd demo`). Same for the employee PIN: every seeded
# employee gets the tier-1 step-up PIN "1234" (spec §7).
_DEMO_PIN = "1234"


def seed_if_empty(db, log) -> None:
    if db.query(Employee).first() is not None:
        return

    if db.query(User).first() is None:
        db.add(
            User(
                username="demo",
                password_hash=hash_password("demo"),
                display_name="Demo Manager",
            )
        )
        log.warning("Seeded a default demo/demo manager login — change it before any real deployment.")

    policies = {}
    for spec in POLICIES:
        policy = PayPolicy(**spec)
        db.add(policy)
        policies[spec["key"]] = policy
    db.flush()  # assign policy ids for the FK

    pin_hash = hash_password(_DEMO_PIN)
    for spec in EMPLOYEES:
        employee = Employee(
            name=spec["name"],
            first_name=spec["first_name"],
            role=spec["role"],
            site=spec["site"],
            company=spec["company"],
            manager_name=spec["manager_name"],
            language=spec["language"],
            phone_number=spec["phone_number"],
            pin_hash=pin_hash,
            pay_policy_id=policies[spec["policy"]].id,
        )
        db.add(employee)
        db.flush()

        if spec["bank"]:
            db.add(BankedHoursState(employee_id=employee.id, **spec["bank"]))
        db.add(PTOBalance(employee_id=employee.id, days_available=spec["pto_days"]))
        db.add(OvertimeAccrual(employee_id=employee.id, **spec["ot"]))
        absence_date, absence_type = spec["last_absence"]
        db.add(
            LastAbsence(
                employee_id=employee.id, absence_date=absence_date, absence_type=absence_type
            )
        )
        db.add(ExpectedShift(employee_id=employee.id, **spec["shift"]))
        for req_type, detail in spec["requests"]:
            db.add(
                Request(
                    employee_id=employee.id,
                    type=req_type,
                    status=RequestStatus.pending,
                    detail=detail,
                )
            )

    db.commit()
    log.info(
        "Seeded %d pay policies and %d employees (Ana Souza + 3 synthetic).",
        len(POLICIES),
        len(EMPLOYEES),
    )
