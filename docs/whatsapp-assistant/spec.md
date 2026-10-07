# Employee Assistant — Capability Spec (#19)

> The build reference for **Idea #19, the Employee WhatsApp Assistant** — the employee's HR
> interface *inside their messaging channel*. Read-only Q&A **+ request transactions + proactive
> nudges**, every answer grounded in the employee's real computed data. Companion to the sizing in
> [`../strategy/ai-features-deep-dive.md`](../strategy/ai-features-deep-dive.md#19-employee-whatsapp-assistant) (effort: **L,
> ~12–18 eng-months; read-only v1 in one quarter**).
>
> **Status:** design decisions locked with Assaf, 2026-07-14. Scope below is **v1** unless marked
> _(phase 2)_.

---

## 1. Framing

The workforce day.io serves is **deskless** (~80% of the global workforce) and doesn't log into a
portal — it lives in a messaging app. The assistant meets employees there. Three modes:

- **Ask** — read-only questions about the employee's own computed state, schedule, pay derivation,
  and comp rules.
- **Do** — a narrow set of **requests** the assistant files on the employee's behalf, each routed to
  a human for approval.
- **Nudge** — proactive, opt-in pushes that pre-empt the question (and often the problem).

The un-DIY-able slice is that **every number is grounded in the engine and the calculation trace** —
a generic HR bot answers *policy*; ours answers *your data*. Wrong answers about pay are radioactive,
so the engineering bar is **grounded-only, hallucination budget ≈ 0** (see §3).

## 2. Channel strategy — WhatsApp first, channel-agnostic core

The channel is **not** globally settled; it's regional. Current penetration:

| Region | Dominant channel | WhatsApp penetration |
| :-- | :-- | :-- |
| **Brazil** | WhatsApp | ~98.9% of internet users — *WhatsApp is the phone* |
| **LATAM (MX etc.)** | WhatsApp | ~90%+ |
| **Europe (ES/DE/IT)** | WhatsApp | 85–92% |
| **India** | WhatsApp | ~536M users (largest single market) |
| **United States** | **SMS** | ~32% — secondary; strong only in immigrant + 18–34 cohorts |

The US is the outlier: **54% of US professionals rate SMS the most effective channel for deskless
workers**, and Workday's Frontline Agent shipped on SMS, not WhatsApp. Neither channel is "free" —
WhatsApp gates on Meta template review, SMS gates on US carrier A2P/10DLC registration. RCS (now that
Apple supports it) is the emerging US analog to WhatsApp, but business RCS is still immature.

**Decision.** The channel is the cheap, swappable part; the grounded reasoning + engine-query layer
is the expensive, durable part (~8 of the 12–18 eng-months). So:

- **Build the assistant channel-agnostic.** Ship **WhatsApp first** — it covers Brazil + LATAM + EU +
  India, i.e. the world minus the US.
- **SMS/RCS is a later US adapter, not a rebuild.** Slack/Teams for desk-adjacent tenants is the same
  story.

> Sources: [Infobip — WhatsApp statistics 2026](https://www.infobip.com/blog/whatsapp-statistics) ·
> [Business of Apps — WhatsApp usage](https://www.businessofapps.com/data/whatsapp-statistics/) ·
> [Mobile Text Alerts — 2025 workplace messaging trends](https://mobile-text-alerts.com/articles/workplace-messaging-trends) ·
> [Text-Em-All — SMS vs WhatsApp for business](https://www.text-em-all.com/blog/sms-vs-whatsapp-for-business).

## 3. Architecture principle

```
Channel Adapter  (WhatsApp → SMS / RCS / Slack / Teams)
        │   normalizes inbound message + identity, renders outbound
        ▼
Assistant Core   (channel-independent)
   intent → grounded retrieval → engine / trace query → phrase → guardrail
```

- **The LLM phrases; it never computes pay.** Every number comes from an engine or trace lookup.
- **Hallucination budget ≈ 0** makes the **eval harness + red-teaming a first-class, permanent
  investment**, not a launch task.
- The Channel Adapter is the only channel-aware code; adding SMS/RCS never touches the Core.

## 4. Capability map

Five buckets, cut by **data source + risk** (not by UI). Read buckets deflect HR load; the write
bucket is deliberately narrow.

| # | Bucket | Example questions / actions | R/W | Source | Risk / auth |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **A** | **Where I stand** | banked hours, PTO/days-off balance, OT accrued this period, **when the bank resets**, last absence, request status | Read | rollup + accrual state | Low |
| **B** | **What's expected of me** | next shift, am I working the holiday, week's expected hours, did my swap go through | Read | Expected-shift inputs | Low |
| **C** | **Why my number is X** *(the moat)* | "why was my OT only 30%?", "why is my bank lower than last month?", "why didn't Saturday count?" | Read | **trace service / WhyPay #6** | **High** — needs #6 |
| **D** | **How I'm compensated** | *my* daily/weekly OT threshold, night premium, DSR rules, tolerance window, my banking cycle | Read | **the employee's actual pay policy** | Med — must be employee-specific, never a generic legal blurb |
| **E** | **Do something** *(requests only)* | **time-off / absence request**, **shift-swap / cover request** | **Write → human approval** | request/approval pipeline | **Step-up auth (§6)** |

**Bucket E is scoped to two request types in v1: time-off and shift-swap.** Both are pure
*scheduling-intent* requests — they never assert "I was present at time X," so they never touch the
authoritative punch record. Time-off folds in Idea #20 (Conversational Time-Off).

## 5. The legal firebreak — requests, not punches

> **The assistant originates *requests*; a human approves them. It never writes an authoritative
> time record itself.**

This is what lets v1 include transactions **without** the Brazil Portaria 671 / REP-P workstream
(record integrity, comprovante issuance, electronic-registration compliance). The rule holds across
jurisdictions, not just Brazil.

Explicitly **deferred**:

- **Punch-by-chat** — writing a punch. Requires Portaria 671 clearance. _(phase 2)_
- **Punch-correction requests** — "I forgot to punch out." Even as a *request*, it's out of v1's
  catalog; the missing-punch case is handled as **detect-and-notify only** (see §6), routing the
  employee to the existing correction flow. _(phase 2 candidate)_
- **Overtime pre-authorization requests.** _(phase 2 candidate)_

## 6. Interaction model — reactive + proactive

v1 is **both** pull (employee asks) and push (assistant nudges, opt-in).

**Nudge catalog (opt-in):**

- **Bank reset / expiry warning** — "your bank resets Sunday; you'll lose 4h."
- **OT above usual** — "your OT this period is 40% higher than usual."
- **Pay-different heads-up** — pre-empt the pay-shock *before* payday (attacks the #1 problem).
- **Request status change** — approved / denied.
- **Schedule published / changed.**
- **Missing punch detected** — *notify only* in v1 ("no clock-out recorded yesterday — contact your
  manager"); does **not** file a correction request (see §5).

**The killer loop — proactive detection → one-tap request.** The nudge *creates* the transaction, a
motion the pull-only competitors (Deel, Workday's SMS agent) don't have:

- bank-expiry nudge → *"want to request time off to use these hours?"* → **time-off request** (in
  catalog ✓)
- coverage-gap / availability-conflict nudge → *"want to ask a coworker to cover?"* → **shift-swap
  request** (in catalog ✓)

This loop is both the daily-active habit *and* the pre-empt-the-pay-shock value, in one motion.

## 7. Identity & anti-abuse

WhatsApp/SMS numbers are **bound at onboarding** = baseline identity. On shared phones, filing a
request or reading exact pay in someone else's name is the real abuse vector, so auth is **tiered**:

| Tier | Gate | Covers |
| :-- | :-- | :-- |
| **0** | none (bound number) | schedule (B), policy Q&A (D), coarse balances |
| **1** | one-time PIN / step-up | exact pay figures, why-my-number (C), **submitting any request (E)** |

## 8. v1 scope boundary

**In:** buckets A, B, C, D + E limited to **time-off & shift-swap** requests · reactive Q&A +
proactive nudges · WhatsApp · multilingual · grounded-only Core + eval harness · tiered identity.

**Out / deferred:** punches (Portaria 671) · punch-correction requests · OT pre-auth requests · SMS /
RCS (US) · Slack / Teams (desk-adjacent) — all _(phase 2)_.

## 9. Dependencies

- **#6 WhyPay Copilot / trace service** — required for bucket C.
- **#20 Conversational Time-Off** — folded into bucket E.
- **Pay-policy configuration** (`context/pay-policy-configuration.md`) — bucket D must resolve the
  employee's *actual* policy, not a generic KB.
- **Expected-shift pipeline data** — bucket B.
- **Request / approval pipeline** — the write path for bucket E.
- **Rollup & accrual state** — buckets A.

## 10. Open questions (phase 2)

- Punch-correction requests — worth adding once the approval pipeline is proven?
- Punch-by-chat — the Portaria 671 legal/product workstream, per jurisdiction.
- OT pre-authorization requests.
- US channel: SMS vs RCS adapter — timing and carrier A2P/10DLC lead time.
- Desk-adjacent Slack/Teams adapter for hybrid tenants.
- Proactive-nudge opt-in model, per-conversation WhatsApp COGS, and template pre-approval.
