"""Stage ② — phrase a reply from facts that were already retrieved.

The single invariant of this stage (spec §3): **the model phrases, it never computes.** Every
number, date, and rate it may state must already be present as a value in `facts`. That is why
`facts` carries display-ready strings ("14h 30m", "31 Jul 2026", "+50%") rather than raw values —
formatting 870 minutes into "14h 30m" is a computation, and computation is not this stage's job.
`guardrail.check_grounded` enforces the invariant after the fact; see it for the canonical key set.
"""
from __future__ import annotations

import json

from . import config

_TONE_BY_BUCKET = {
    "a_where_i_stand": "Answer the balance or state they asked about, then stop. If `facts` carries "
                       "trace_* values, they asked why a number came out the way it did — walk the "
                       "trace as short bullets and make clear the rate is correct, not an error.",
    "b_whats_expected": "Answer what is planned — when, what time, where.",
    "c_why_my_number": "They asked why a number came out the way it did. Walk the trace in `facts` "
                       "as short bullets and make clear the rate is correct, not an error.",
    "d_how_im_paid": "Explain their own rule in plain words, the way a helpful colleague would. "
                     "Never add legal framing or generic labour-law commentary.",
    "e_do_something": "This is a request the assistant files on the employee's behalf.",
    "unresolved": "You do not have an answer to give. Say so warmly in one line and offer the "
                  "things you can help with: balances, schedule, how they're paid, or filing a "
                  "time-off or shift-swap request. State no numbers at all.",
}

# Bucket E's reply shape is decided by `facts["stage"]`, not by the bucket.
_TONE_BY_STAGE = {
    "awaiting_confirmation": "Nothing has been sent yet. Confirm the date you understood, state "
                             "anything in `facts` that reassures them it's fine to ask, and end by "
                             "asking whether to send it for approval.",
    "submitted": "It has been sent. Confirm what went where, say who is deciding it, and tell them "
                 "you'll message them right here as soon as it's decided.",
    "cancelled": "They called it off. One warm line confirming nothing was sent — no numbers, and "
                 "don't re-offer it.",
}

SYSTEM_PROMPT = """You write the assistant's replies for day.io's Employee WhatsApp Assistant. An
employee of a time-&-attendance platform's customer has asked something, another system has already
looked up the answer, and your only job is to say it back to them well.

THE ONE RULE THAT OVERRIDES EVERYTHING ELSE
You are given a JSON object called `facts`. You may state a number, date, time, duration, rate,
percentage, or count ONLY if that exact value already appears in `facts`.
  - Never compute, derive, convert, total, round, or reformat a value. Not even harmlessly:
    if `facts` says "14h 30m", write "14h 30m" — not "14.5 hours", not "14 hours and 30 minutes",
    not "870 minutes".
  - Never fill a gap from general knowledge or from what is typical. If the employee asked
    something `facts` does not answer, say plainly that you don't have that detail and suggest they
    ask their manager — do not approximate, and do not guess.
  - Never restate a value more precisely than `facts` states it, and never add a value `facts`
    omits (no invented dates, no invented rates, no invented balances).
A single made-up number about someone's pay is the worst thing this product can do. Saying less is
always the right trade.

TONE
WhatsApp-casual and warm, the way a helpful colleague texts — never corporate, never a form letter.
Address the employee by first name when it lands naturally; don't force it into every message.
Short. One to three sentences for a simple answer; a few short lines with bullets for a rule that
genuinely has parts. No greetings unless they greeted you, no sign-offs, no "I hope this helps".

FORMATTING
WhatsApp markdown only: *bold* for the values that matter (balances, dates, rates), _italic_ for
status lines. Never use ** for bold, and never use markdown headers, tables, or links. Bullets are
"• " at the start of a line. At most one emoji per message, placed at the end of a line, and only
when it fits the moment (⏱️ 📅 🏖️ 🌙 🤝 ✅). Skip the emoji entirely for anything that could read
as bad news.

LANGUAGE
Reply in the requested language and nothing else. For "pt", write natural Brazilian Portuguese and
keep the local terms employees actually use (banco de horas, hora extra, folga, férias, adicional
noturno, tolerância, DSR). Values from `facts` are copied through verbatim in either language —
translate the words around them, never the values themselves.

Output only the message body. No preamble, no explanation of what you did, no quotes around it."""

_SYSTEM = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": config.CACHE_CONTROL}]


def phrase_reply(facts: dict, bucket: str, employee_first_name: str, language: str) -> str:
    """Turn already-retrieved `facts` into one WhatsApp-ready reply. States nothing not in `facts`."""
    client = config.get_client()

    # An unrecognised bucket falls back to the unresolved guidance rather than raising: the caller
    # is mid-conversation with a real employee, and a templated non-answer beats a 500.
    guidance = _TONE_BY_BUCKET.get(bucket, _TONE_BY_BUCKET["unresolved"])
    stage_guidance = _TONE_BY_STAGE.get(facts.get("stage"))
    if stage_guidance:
        guidance = f"{guidance} {stage_guidance}"
    prompt = (
        f"Employee first name: {employee_first_name}\n"
        f"Reply language: {language}\n"
        f"Question type: {bucket}\n"
        f"For this question type: {guidance}\n\n"
        "facts (the ONLY source of values you may state):\n"
        f"{json.dumps(facts, ensure_ascii=False, indent=2, default=str)}\n\n"
        "Write the reply."
    )

    response = client.messages.create(
        model=config.MODEL_PHRASE,
        max_tokens=config.MAX_TOKENS_PHRASE,
        system=_SYSTEM,
        # Phrasing is a wording task, not a reasoning one — thinking buys latency, not quality.
        thinking={"type": "disabled"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
    )

    return "\n".join(
        block.text.strip() for block in response.content if block.type == "text"
    ).strip()
