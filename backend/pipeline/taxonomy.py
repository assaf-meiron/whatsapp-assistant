"""The classification target — the five capability buckets (spec §4) and the two identity tiers
(spec §7), rendered as one stable block of system context for the intent stage.

Source of truth: `../../docs/whatsapp-assistant/spec.md`. Bucket keys match `app.models.Bucket`.
"""
from __future__ import annotations

# (key, label, what it covers, example asks). `key` matches the app.models.Bucket enum values.
BUCKETS: list[tuple[str, str, str, str]] = [
    (
        "a_where_i_stand",
        "Where I stand",
        "the employee's own accrued state: hours-bank balance, when the bank resets or expires, "
        "PTO / days-off balance, overtime accrued this pay period, last absence, status of a "
        "request they already filed. Also the canned rate trace behind overtime already worked.",
        '"how many banked hours do I have", "when does my bank reset", "how much overtime did I '
        'do", "when was my last day off", "did my request go through", "why was my OT only 30%"',
    ),
    (
        "b_whats_expected",
        "What's expected of me",
        "the plan: next shift (when / time / site), this week's scheduled hours, the next holiday "
        "and whether they work it, whether a swap went through.",
        '"when is my next shift", "am I working the holiday", "how many hours this week", '
        '"what is my schedule tomorrow"',
    ),
    (
        "c_why_my_number",
        "Why my number is X  — DEFERRED, NOT IN USE IN v1",
        "live pay-derivation traces from the WhyPay trace service. That service is not built "
        "(spec §9), so there is no retrieval or phrasing path for this bucket and it is NOT a "
        "selectable answer. Route why-questions about already-accrued overtime or bank movement "
        "to a_where_i_stand (a canned trace ships with the accrual record); route why-questions "
        "that are really about a rule to d_how_im_paid.",
        "(none — never select this bucket)",
    ),
    (
        "d_how_im_paid",
        "How I'm compensated",
        "the rules in THIS employee's own pay policy, stated in plain language: their overtime "
        "threshold and rate bands, Saturday rate, night premium, weekly rest day (DSR), tolerance "
        "window, hours-bank cycle. Rules, not amounts.",
        '"when do I start earning overtime", "what is my night premium", "how does my tolerance '
        'window work", "how does my hours bank work", "what is my rest day"',
    ),
    (
        "e_do_something",
        "Do something (requests only)",
        "the employee wants the assistant to FILE something on their behalf. Exactly two request "
        "types exist in v1 — time_off and shift_swap — and both are scheduling intent routed to a "
        "human for approval. Asking about an existing request is a_where_i_stand, not this.",
        '"I need Friday off", "can someone cover my Saturday shift", "quero folga na sexta", '
        '"preciso trocar meu turno"',
    ),
]

BUCKET_KEYS: list[str] = [key for key, _, _, _ in BUCKETS]

# Bucket C is deliberately excluded from what the classifier may emit: it has no retrieval path in
# v1, so a message routed there would produce an ungrounded reply. It stays in BUCKETS (and in
# app.models.Bucket) so the wiring is ready when the trace service lands.
CLASSIFIABLE_BUCKETS: list[str] = [k for k in BUCKET_KEYS if k != "c_why_my_number"] + ["unresolved"]

REQUEST_TYPES: list[tuple[str, str]] = [
    ("time_off", "a day off, vacation, leave, folga, férias — any absence the employee wants "
                 "approved in advance"),
    ("shift_swap", "asking a coworker to cover a shift, or trading shifts — cover, swap, troca, "
                   "cobrir"),
]

IDENTITY_TIERS: list[tuple[str, str]] = [
    ("tier_0", "bound phone number only — schedule (B), policy Q&A (D), coarse balances"),
    ("tier_1", "one-time PIN step-up — exact pay figures and submitting ANY request (E)"),
]

CLASSIFICATION_RUBRIC = """
Classify ONE inbound employee message. Decide in this exact order:

1. IS A FLOW PENDING? You are told whether the employee has an unanswered yes/no confirmation
   sitting in front of them (a request the assistant offered to send). If a flow IS pending:
     • the message agrees / approves / says go ahead ("yes", "yep", "send it", "sure", "ok",
       "please do", "sim", "manda", "pode mandar") -> set flow_action="confirm"
     • the message declines / stops it ("no", "cancel", "not now", "no thanks", "nope", "não",
       "nao", "deixa", "esquece") -> set flow_action="cancel"
     • the message is neither — it is a fresh question or a fresh request -> leave flow_action
       unset and classify the message on its own merits per steps 2-3.
   Whenever you set flow_action, also set bucket="e_do_something": the message is a turn in a
   request flow, not a new question. Leave request_type and detected_date_label unset — the
   pending request already carries both.
   If NO flow is pending, never set flow_action, even for a bare "yes" or "no".

2. IS THIS A NEW REQUEST TO FILE? If the employee is asking the assistant to DO something —
   file an absence, or get a shift covered — set bucket="e_do_something", set request_type, and
   set detected_date_label to the date phrase EXACTLY as the employee said it ("friday",
   "tomorrow", "next monday", "the 25th", "sexta", "amanhã", "sábado"). Do NOT resolve it to a
   calendar date, do NOT reformat it, do NOT invent one: if the message names no day at all,
   leave detected_date_label unset. Downstream code resolves the phrase to a real date.
   Careful: "did my time-off request go through?" is a QUESTION about existing state
   (a_where_i_stand), not a new request.

3. OTHERWISE IT IS A QUESTION. Pick the single bucket whose data source answers it:
     • about MY accrued numbers or a request I already filed -> a_where_i_stand
     • about MY plan / schedule / holidays -> b_whats_expected
     • about the RULES that govern my pay -> d_how_im_paid
   The distinguishing test between a_where_i_stand and d_how_im_paid is amount vs rule:
   "how much overtime did I do" is an amount (A); "when do I start earning overtime" is a
   rule (D). "How many hours are in my bank" is an amount (A); "how does my bank cycle work"
   is a rule (D).

4. UNRESOLVED. Set bucket="unresolved" for greetings, thanks, small talk, menu/help requests,
   anything you cannot confidently place, and anything outside the four live buckets — notably
   punch corrections, "I forgot to clock out", overtime pre-authorisation, payslip disputes, and
   anything asking the assistant to record time worked. Those are deliberately out of scope
   (spec §5); do NOT force them into a live bucket. Guessing wrong is worse than unresolved,
   because a wrong bucket retrieves the wrong facts.

Messages arrive in English or Portuguese (Brazilian), often mixed with local terms — "banco de
horas" (hours bank), "hora extra" (overtime), "folga" (day off / rest day), "férias" (vacation),
"feriado" (public holiday), "atestado" (medical certificate), "adicional noturno" (night premium),
"tolerância" (tolerance window), "DSR"/"descanso semanal" (weekly rest day), "turno" (shift),
"escala" (roster). Classify on meaning, not on language.

Emit exactly one record_intent call. Never explain yourself in text.
"""


def render_taxonomy() -> str:
    """The stable, cacheable system block the intent stage classifies against."""
    lines = [
        "You are the intent stage of day.io's Employee WhatsApp Assistant — the employee-facing "
        "chat interface of a time-&-attendance platform. Employees message it about their own "
        "hours, schedule, pay rules, and requests.",
        "",
        "CAPABILITY BUCKETS (pick exactly one):",
    ]
    for key, label, covers, examples in BUCKETS:
        lines.append(f"  {key}  — {label}")
        lines.append(f"      covers: {covers}")
        lines.append(f"      e.g.:   {examples}")
    lines.append("  unresolved  — Nothing above fits, or you are not confident.")
    lines.append("")
    lines.append("REQUEST TYPES (only when bucket = e_do_something):")
    for name, covers in REQUEST_TYPES:
        lines.append(f"  {name}  — {covers}")
    lines.append("")
    lines.append("IDENTITY TIERS (context only — you do not gate anything):")
    for name, covers in IDENTITY_TIERS:
        lines.append(f"  {name}  — {covers}")
    lines.append("")
    lines.append(
        "Set `bucket` to EXACTLY ONE of: " + ", ".join(CLASSIFIABLE_BUCKETS) + "."
    )
    return "\n".join(lines)
