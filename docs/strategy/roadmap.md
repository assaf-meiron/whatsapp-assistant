# AI Features — Roadmap & Priority Decisions

> **Decision record.** Outcome of the VP Product review with **Liran** (2026-07-15), where the
> AI-feature catalog, its rationale, and the mockups were presented and a starting set was chosen.
> This is the durable home for *which* AI features we build and *in what order* — the "why these"
> layer above the catalog.
>
> **Source artifacts presented:** the 30-idea catalog ([`ai-feature-ideas.md`](ai-feature-ideas.md)),
> the shortlist [`ai-features-deep-dive.md`](ai-features-deep-dive.md), three capability specs
> ([`../specs/`](../specs/)), and nine runnable mockups ([`../prototypes/`](../prototypes/)).
>
> _Decisions below are Liran + Assaf's calls from the review. Idea-`#` mappings are to the catalog;
> where a decision has no clean catalog match it is flagged. Scope marked **TBD** is Assaf's to
> detail — not yet defined._

## What was presented

A strategy deck walking Liran through: the **two strategic lenses** (defend the calc-engine moat
against DIY-IT rebuilds; make HR's life better by moving from copilots to agents), the **30-idea
catalog** ranked by effort/impact/defensibility, a **deep-dive** sizing the shortlist, and **nine
interactive mockups** making the promising ideas concrete and demoable. The review's job was to pick
what we start with.

## The decision at a glance

| Priority | Feature | Catalog | Spec | Prototype | Gating next step |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **Start now** | **LawTrack AI** | #3 (absorbs #2) | ✅ (+ PM track) | ✅ `prototypes/lawtrack-ai/` | Run discovery; build Phase-1 digest loop |
| **Start now** | **Payroll Copilot** | #7 | ✅ (notes folded) | ✅ `payroll-close-copilot/` | PM track: pain points → research → PRD |
| **Start now** | **MCP** | #28 | — | — | Write capability spec; no mockup yet |
| **Second** | **DIA** (employee super-assistant) | #19 + #20 + #6 | partial (`whatsapp-assistant.md`) | ✅ `whatsapp-assistant/` (one surface) | **Payroll-system integration** (money Q&A) — launch blocker |
| **Explore** | **Software as a commodity** | ~#1 + #27 *(inferred)* | — | — | Assaf to define scope |
| **On build list** | **What-If Simulator** | #5, **broadened** | — | ✅ `what-if-simulator/` (pay-policy only) | Assaf to define the broadened scope (**TBD**) |

---

## Tier 1 — start with these three

### 1. LawTrack AI (#3)
Reads any labor-rule source (law, CBA/CCT), flags what changed per jurisdiction, and drafts the
pay-policy config update — closing the loop from *detected change* → *drafted policy*. Absorbs the
former CBA/CCT Reader (#2) as its manual-upload mode. **Now a committed-feature home**
([`../lawtrack-ai/`](../lawtrack-ai/)): spec + full PM track — pain points, document taxonomy, phased
agent plan (Phase 1 digest → Phase 2 scanner), and a **production Claude API technical design**.
Mockup at `../prototypes/lawtrack-ai/`. Next: run discovery + build the Phase-1 digest loop.

### 2. Payroll Copilot (#7 — Payroll Close Copilot)
The agent that owns the payroll-close checklist. **Mockup + spec exist.** The review sharpened what
this feature must do — fold these into the spec:

- **The pain it removes.** Today the **supervisor** closes the payroll period — it's slow: they must
  nudge people and make sure everyone closes correctly with no missing punches. Then **HR** runs
  validations and corrections on top. Two serial, manual gauntlets.
- **Core value — fix what a human or a job misses.** Catch and repair errors the supervisor or an
  automated job let through. Canonical example: a **missing punch that makes a day's total hours
  negative** — impossible on its face, so the copilot should catch and fix it.
- **The higher-order layer (the real win).** Beyond mechanical repair, run **reasoning to understand
  the time & attendance at a higher level** — so the copilot can fix the timesheet *intelligently*,
  not just patch obvious breaks.
- **Mobile close (a major win if we support it).** The supervisor should be able to **close the
  payroll period from mobile.** Most of these jobs are **not office jobs** — making a supervisor sit
  down at a computer is a real burden. Mobile close is a differentiator, not a nice-to-have.
- **Capture the close-checklist.** Explicitly **ask the user which tests/checks they run** when they
  close payroll, and make those part of what the copilot verifies.
- **Anomaly detection.** Run ML / statistical methods to surface anomalies pre-close.

### 3. MCP (#28 — day.io MCP Server / Agent Platform)
Expose the governed calc engine and tenant data as an agent-callable surface (remote MCP server +
APIs, OAuth, granular permissions, full audit logging) — the "judo" answer to the DIY-IT threat: the
customer's own agents build *on* day.io instead of trying to replace it. **No spec, no mockup yet.**

---

## Second priority

### 4. DIA — the employee super-assistant (#19 + #20 + employee-side #6)
DIA is **not just** the WhatsApp Q&A bot (#19). It's the broader employee assistant, bundling:

- **#19 Employee (WhatsApp) Assistant** — the conversational HR interface in the employee's channel.
- **#20 Conversational Time-Off** — request/manage leave in chat.
- **#6 WhyPay, employee surface** — "why is my pay X?" traced from punches → rules → result.
- **Money/pay data the employee can ask about** — a first-class capability, not an add-on.

Notes from the review:

- **The goal is adoption — employees actually *using* it.** That's the bar DIA is measured against.
- **Payroll-system integration is the launch blocker.** Employees will ask about **money**, which is
  **outside our current solution scope** — day.io holds hours, not salaries/pay. We will **not launch
  DIA until it's connected to the actual payroll system** so those questions can be answered
  correctly. *How* to integrate is an open design question.
- **But we can start now.** Begin **fetching data and building** DIA ahead of the integration; the
  integration gates *launch*, not *development*.
- The existing `whatsapp-assistant/` mockup is **one surface** of DIA, not its full scope.

---

## To explore

### 5. Software as a commodity
The ability for **each customer to customize day.io's solution to their own needs** — configurability
/ "build-your-own" as a product surface rather than bespoke services. Closest catalog analogues are
**#1 Calculation Studio** (prompt a new calculation into existence) and **#27 HR Workflow Agent
Studio** *(mapping inferred — to be confirmed)*. **Assaf to explain the intended scope; captured here
as a named bet, scope TBD.**

---

## Also on the build list

### 6. What-If Simulator (broadened beyond #5)
We will build a What-If Simulator, but it should do **more than pay-policy what-ifs.** The existing
`what-if-simulator/` mockup (#5) only re-prices under changed **pay-policy levers**; the intended
feature is broader. **Scope is TBD — Assaf to detail it later.** Do not treat the current mockup as
the target definition.

---

## Open questions / next steps

- **Payroll Copilot** — ✅ six review notes folded into the spec, now in its own feature home
  [`../payroll-copilot/`](../payroll-copilot/) (spec + PM track). Step 1 **pain points** drafted +
  interview guide ready; **market research → PRD** are scaffolded, pending research.
- **DIA** — design the **payroll-system integration** (the launch gate); broaden the
  `whatsapp-assistant.md` spec into a DIA spec covering all surfaces + money Q&A.
- **What-If Simulator** — Assaf to define the broadened scope before building past the #5 mockup.
- **Software as a commodity** — Assaf to define scope; confirm/replace the #1/#27 mapping.
- **Specs still to write:** MCP, DIA (broadened), What-If (broadened). *(LawTrack AI ✅ done.)*
