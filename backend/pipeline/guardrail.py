"""Stage ③ — the hallucination budget, enforced in code.

`check_grounded` is deliberately LLM-free: a model cannot be the last line of defence against a
model. It pulls every number-like token out of the drafted reply and requires each one to trace
back to a value in `facts`. When one doesn't, `fallback_reply` is a reply assembled by string
templating straight from `facts` — no generation anywhere in that path, so it cannot itself invent
a number. That fallback is what makes "hallucination budget ≈ 0" (spec §3) a property of the
system rather than a hope about the model.

`facts` keys the templates below know about — the contract with `app/pipeline_adapter.py`. Unknown
keys still render, just generically, so the adapter can add fields without breaking the fallback:

  A  bank_status · bank_balance · bank_cycle · bank_reset · bank_expiring · pto_days ·
     ot_this_period · ot_trace_day · ot_trace_extra · ot_trace_rate · ot_trace_rule ·
     ot_trace_weekday_rate · last_absence_date · last_absence_type ·
     requests[{type, detail, status}] · manager_name
  B  next_shift_when · next_shift_time · next_shift_site · week_hours · holiday_name ·
     holiday_date · holiday_working
  D  ot_threshold · ot_rate_bands · saturday_ot_rate · night_premium · dsr_rule · tolerance ·
     banking_cycle
  E  stage ("awaiting_confirmation" | "submitted" | "cancelled") · request_type · request_date ·
     request_status · manager_name · pto_days · swap_candidates[]

`bank_status` is the no-hours-bank case: on a policy that pays overtime out instead of banking it
the balance keys are absent, and this plain-English line is the whole answer. It must never be
phrased as a zero balance.

The ot_trace_* keys sit under bucket A, not C: `classify_intent` never emits `c_why_my_number` (no
retrieval path exists for it in v1), so "why was my OT only 30%" arrives as `a_where_i_stand` and
the canned trace has to travel with the rest of the accrual state.

Every value must arrive display-ready ("14h 30m", "31 Jul 2026", "+50%"). A raw 870 that the reply
is expected to render as "14h 30m" will fail the check — correctly, because that conversion is a
computation. Nested values are walked, so a date quoted out of `requests` traces fine.
"""
from __future__ import annotations

import re

from .schema import GroundednessCheck

_DASHES = str.maketrans({"–": "-", "—": "-", "−": "-", "‒": "-"})

# A digit run (allowing internal . , :) plus whatever unit-ish token immediately follows it.
_NUMBER_RE = re.compile(r"\d+(?:[.,:]\d+)*(?:\s*%|\s*[A-Za-z]{1,9})?")

_MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|fev|abr|mai|ago|set|out|dez"
# A day/month/year date carries a fabrication its digits alone don't reveal: "31 Aug 2026" reuses
# every digit of "31 Jul 2026". Matched dates are therefore checked whole.
_DATE_RE = re.compile(
    rf"\b(?:\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})[a-zç]*\.?(?:\s+\d{{2,4}})?"
    rf"|(?:{_MONTHS})[a-zç]*\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{2,4}})?)\b",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text.lower().translate(_DASHES))


def _fact_values(facts: dict) -> list[str]:
    """Every scalar in `facts`, flattened. Booleans and None carry no digits worth tracing."""
    out: list[str] = []

    def walk(value) -> None:
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                walk(item)
        elif isinstance(value, bool) or value is None:
            return
        else:
            out.append(str(value))

    walk(facts)
    return out


def untraceable_numbers(reply: str, facts: dict) -> list[str]:
    """Number-like tokens in `reply` that trace back to no value in `facts`."""
    haystack = [_norm(v) for v in _fact_values(facts)]
    missing: list[str] = []

    def traces(probe: str) -> bool:
        return any(probe in value for value in haystack)

    for match in _DATE_RE.finditer(reply):
        token = match.group(0)
        if not traces(_norm(token)):
            missing.append(token.strip())

    for match in _NUMBER_RE.finditer(reply):
        token = match.group(0)
        probe = _norm(token)
        if traces(probe):
            continue
        # A percentage must match with its "%" — a bare-digit match would let a fabricated "+30%"
        # ride along on an unrelated "30" elsewhere in facts, and rates are the costliest thing to
        # get wrong. Everything else may match on digits alone, so "12 days" traces to a plain 12.
        digits = _norm(re.match(r"\d+(?:[.,:]\d+)*", token).group(0))
        if "%" not in probe and traces(digits):
            continue
        missing.append(token.strip())

    return list(dict.fromkeys(missing))


def check_grounded(reply: str, facts: dict, language: str = "en") -> GroundednessCheck:
    """Verify every number in `reply` traces to `facts`. `fallback_reply` is always populated.

    `language` only picks the wording of the fallback; the check itself is language-independent.
    It defaults to "en" so `check_grounded(reply, facts)` keeps working, but pass the employee's
    language — otherwise a Portuguese-speaking employee gets an English reply exactly when
    something has gone wrong.
    """
    return GroundednessCheck(
        is_grounded=not untraceable_numbers(reply, facts),
        fallback_reply=build_fallback(facts, language),
    )


# --- the templated fallback: string formatting from facts, nothing else --------------------------

# Wording tables, one per supported language. The fallback fires exactly when something has already
# gone wrong, so it must speak the employee's language — an English apology to a Brazilian cashier
# is a second failure on top of the first. The pt strings want a native-speaker review.
_TEXT: dict[str, dict] = {
    "en": {
        "unresolved": "I'm not sure I got that one. I can help with your *balances*, your "
                      "*schedule*, *how you're paid*, or *filing a time-off or shift-swap "
                      "request*. Which one would you like?",
        # (fact key, one-slot template). Rendered in order, only for keys present in facts.
        "lines": [
            # A — where I stand. bank_status comes first and stands alone: on a policy with no
            # hours bank it is the whole answer, and the balance lines below are absent.
            ("banking_cycle_policy", "{}"),
            ("bank_balance", "You have *{}* in your hours bank."),
            ("bank_cycle", "It runs on a {} cycle."),
            ("bank_reset_date", "It resets on *{}*."),
            ("bank_expiring", "*{}* will expire if unused before then."),
            ("pto_days_available", "You have *{}* days of paid time off available."),
            ("overtime_this_period", "You've done *{}* of overtime this pay period."),
            ("trace_day", "On *{}*:"),
            ("trace_extra", "• overtime worked: *{}*"),
            ("trace_rate_applied", "• rate applied: *{}*"),
            ("trace_rule", "• rule: {}"),
            ("trace_weekday_rate", "• Monday-to-Friday overtime is *{}*"),
            ("last_absence_date", "Your last day off was *{}*."),
            ("last_absence_type", "Type: {}."),
            # B — what's expected of me
            ("next_shift_when", "Your next shift is *{}*."),
            ("next_shift_time", "It runs *{}*."),
            ("next_shift_site", "Location: {}."),
            ("week_hours", "You're scheduled for *{}* this week."),
            ("next_holiday_name", "The next holiday is *{}*."),
            ("next_holiday_date", "It falls on *{}*."),
            # D — how I'm paid
            ("ot_threshold", "You start earning overtime after *{}*."),
            ("ot_rate_bands", "Overtime rates: {}."),
            ("saturday_ot_rate", "Saturday overtime is paid at *{}*."),
            ("night_premium", "Night work earns *{}*."),
            ("dsr_rule", "Your weekly rest day: {}."),
            ("tolerance", "Your tolerance window is *{}*."),
            ("banking_cycle", "Your hours bank runs on {}."),
        ],
        "working_the_holiday": "You're scheduled to work it.",
        "holiday_off": "You're not scheduled to work it.",
        "manager": "Your manager is {}.",
        "labels": {"time_off": "time-off", "shift_swap": "shift-swap"},
        "asks": {
            "time_off": "Got it — you'd like *{}* off.",
            "shift_swap": "Got it — you'd like someone to cover your *{}* shift.",
        },
        "ask_generic": "Got it — *{}*.",
        "ask_no_date": "Got it — you'd like to file a {} request.",
        "days_available": "You have *{}* days available.",
        "can_ask": "I can ask {}.",
        "send_to": "Shall I send this to {} for approval?",
        "send": "Shall I send this for approval?",
        "cancelled": "No problem — nothing was sent. 🙂",
        "submitted_head": "Your {} request",
        "submitted_head_bare": "Your request",
        "submitted_for": " for *{}*",
        "submitted_with": " is with {} for approval.",
        "submitted_sent": " has been sent for approval.",
        "submitted_tail": "I'll message you right here the moment it's decided.",
    },
    "pt": {
        "unresolved": "Não entendi bem essa. Posso ajudar com seus *saldos*, sua *escala*, *como "
                      "você é pago* ou *abrir um pedido de folga ou troca de turno*. O que você "
                      "prefere?",
        "lines": [
            ("banking_cycle_policy", "{}"),
            ("bank_balance", "Você tem *{}* no seu banco de horas."),
            ("bank_cycle", "Ele funciona em ciclo {}."),
            ("bank_reset_date", "Ele zera em *{}*."),
            ("bank_expiring", "*{}* vão expirar se não forem usadas até lá."),
            ("pto_days_available", "Você tem *{}* dias de férias disponíveis."),
            ("overtime_this_period", "Você fez *{}* de hora extra neste período."),
            ("trace_day", "Em *{}*:"),
            ("trace_extra", "• hora extra trabalhada: *{}*"),
            ("trace_rate_applied", "• adicional aplicado: *{}*"),
            ("trace_rule", "• regra: {}"),
            ("trace_weekday_rate", "• de segunda a sexta, a hora extra é *{}*"),
            ("last_absence_date", "Sua última folga foi em *{}*."),
            ("last_absence_type", "Tipo: {}."),
            ("next_shift_when", "Seu próximo turno é *{}*."),
            ("next_shift_time", "Ele vai de *{}*."),
            ("next_shift_site", "Local: {}."),
            ("week_hours", "Você está escalado para *{}* nesta semana."),
            ("next_holiday_name", "O próximo feriado é *{}*."),
            ("next_holiday_date", "Cai em *{}*."),
            ("ot_threshold", "Você começa a receber hora extra depois de *{}*."),
            ("ot_rate_bands", "Adicionais de hora extra: {}."),
            ("saturday_ot_rate", "No sábado, a hora extra é paga a *{}*."),
            ("night_premium", "O trabalho noturno recebe *{}*."),
            ("dsr_rule", "Seu descanso semanal remunerado: {}."),
            ("tolerance", "Sua tolerância é de *{}*."),
            ("banking_cycle", "Seu banco de horas funciona em {}."),
        ],
        "working_the_holiday": "Você está escalado para trabalhar nesse dia.",
        "holiday_off": "Você não está escalado para trabalhar nesse dia.",
        "manager": "Seu gestor é {}.",
        "labels": {"time_off": "folga", "shift_swap": "troca de turno"},
        "asks": {
            "time_off": "Beleza — você quer folga em *{}*.",
            "shift_swap": "Beleza — você quer que alguém cubra seu turno de *{}*.",
        },
        "ask_generic": "Beleza — *{}*.",
        "ask_no_date": "Beleza — você quer abrir um pedido de {}.",
        "days_available": "Você tem *{}* dias disponíveis.",
        "can_ask": "Posso perguntar para {}.",
        "send_to": "Posso enviar para {} aprovar?",
        "send": "Posso enviar para aprovação?",
        "cancelled": "Sem problema — nada foi enviado. 🙂",
        "submitted_head": "Seu pedido de {}",
        "submitted_head_bare": "Seu pedido",
        "submitted_for": " para *{}*",
        "submitted_with": " está com {} para aprovação.",
        "submitted_sent": " foi enviado para aprovação.",
        "submitted_tail": "Te aviso aqui mesmo assim que for decidido.",
    },
}

# Keys the templates consume some other way, plus control flags that are context for the model
# rather than content for the employee. Everything else falls through to the generic dump.
_HANDLED = {key for key, _ in _TEXT["en"]["lines"]} | {
    "has_hours_bank", "working_the_holiday", "pending_requests", "manager_name",
    "policy_name", "jurisdiction", "stage", "request_type", "request_detail",
    "request_status", "swap_candidates",
}


def _text(language: str) -> dict:
    return _TEXT.get((language or "en").lower().split("-")[0], _TEXT["en"])


def build_fallback(facts: dict, language: str = "en") -> str:
    """Assemble a reply purely by templating `facts`. Cannot state anything not in `facts`."""
    text = _text(language)
    if not facts:
        return text["unresolved"]
    if "stage" in facts:
        return _fallback_for_request(facts, text)

    lines: list[str] = []
    for key, template in text["lines"]:
        value = facts.get(key)
        if value is None or value == "":
            continue
        lines.append(template.format(value))

    if "working_the_holiday" in facts:
        lines.append(text["working_the_holiday"] if facts["working_the_holiday"]
                     else text["holiday_off"])

    for request in facts.get("pending_requests") or []:
        if isinstance(request, dict):
            head = " — ".join(
                str(request[key]) for key in ("type", "detail") if request.get(key)
            )
            if head:
                lines.append(f"• {head}")
            if request.get("status"):
                lines.append(f"  _{request['status']}_")
        elif request:
            lines.append(f"• {request}")

    if facts.get("manager_name"):
        lines.append(text["manager"].format(facts["manager_name"]))

    # Anything the adapter sent that no template claims still gets surfaced rather than dropped —
    # a clumsy line beats silently withholding a value the employee asked for.
    for key, value in facts.items():
        if key in _HANDLED or value is None or value == "":
            continue
        if isinstance(value, (dict, list, tuple, set)):
            continue
        lines.append(f"{key.replace('_', ' ')}: {value}")

    return "\n".join(lines) if lines else text["unresolved"]


def _fallback_for_request(facts: dict, text: dict) -> str:
    """The bucket-E fallback. `stage` decides the whole shape of the reply, so it branches first."""
    stage = facts.get("stage")
    request_type = facts.get("request_type")
    label = text["labels"].get(request_type, str(request_type or "").replace("_", " ").strip())
    detail = facts.get("request_detail")
    manager = facts.get("manager_name")

    # request_status is the DB's own prose ("Pending — sent to Marcos for approval"), so it is the
    # authoritative status line wherever it applies. On a cancellation the one warm line is enough.
    status = facts.get("request_status")

    if stage == "cancelled":
        return text["cancelled"]

    if stage == "submitted":
        head = text["submitted_head"].format(label) if label else text["submitted_head_bare"]
        if detail:
            head += text["submitted_for"].format(detail)
        head += (text["submitted_with"].format(manager) if manager else text["submitted_sent"])
        lines = [head]
        if status:
            lines.append(f"_{status}_")
        lines.append(text["submitted_tail"])
        return "\n".join(lines)

    # awaiting_confirmation, and any stage this code hasn't been taught yet
    lines = []
    if detail:
        lines.append(text["asks"].get(request_type, text["ask_generic"]).format(detail))
    elif label:
        lines.append(text["ask_no_date"].format(label))

    if facts.get("pto_days_available") is not None:
        lines.append(text["days_available"].format(facts["pto_days_available"]))
    candidates = facts.get("swap_candidates") or []
    if candidates:
        lines.append(text["can_ask"].format(", ".join(f"*{c}*" for c in candidates)))
    if status:
        lines.append(f"_{status}_")

    lines.append(text["send_to"].format(manager) if manager else text["send"])
    return "\n".join(lines)
