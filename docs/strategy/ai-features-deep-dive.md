# AI Features Deep Dive — Problem Size, Solution Fit, Build Effort

Companion to *"30 Ways AI Makes day.io Indispensable"* (2026-07-14). Covers the shortlisted ideas (#2+#3 now merged as **LawTrack AI**, #5, #6, #7, #12, #13, #14, #15, #19, #20, #25) plus one addition (#31 Recruiting Agent). Numbers sourced from a 2026-07 web scan (EY, TST/CNJ, BLS, Circadian, Gallup, Mercer, McKinsey, Legion, HDI, Paradox/Chipotle case data, et al.); internal anchors from the Roseman/context-base work where they sharpen the estimate.

## How to read the effort estimates

Calibration assumptions (adjust if squad shapes differ):

- **Squad** = 3 engineers + PM + part-time design. **1 quarter ≈ 9 eng-months.**
- **S** = 1–3 eng-months · **M** = 4–9 eng-months (≤1 quarter) · **L** = 10–24 eng-months (1–2 quarters, full squad) · **XL** = 25+ eng-months (multi-quarter, dedicated squad / new subsystem)
- Estimates separate **v1** (design-partner-ready, narrow scope) from **full vision**, and flag **ongoing ops** where the feature carries a permanent content/curation/COGS cost — several do, and that cost is often the moat.
- Five pieces of infrastructure are shared across features (trace service, projection service, WhatsApp channel, document-ingestion pipeline, versioned policy templates). Per-feature  numbers assume the shared piece is paid for once; see **Shared Infrastructure** at the end.

## Summary scorecard

| # | Feature | Problem headline | How much it solves | v1 effort | Full effort | Hard dependency |
|---|---------|------------------|--------------------|-----------|-------------|-----------------|
| 6 | WhyPay Copilot | T&A errors = #1 payroll error, >1/employee/yr, ~$250k per 1,000 employees (EY); horas extras = #1 BR lawsuit subject (~633k claims in 2025) | 50–70% deflection of pay-explanation tickets; minutes-not-hours dispute resolution | **S–M** (3–6 em) | 8–10 em (both surfaces) | Calculation trace coverage |
| 13 | Hours-Bank Advisor | Statutory expiry windows (1/6/12-month) force payouts at 50%+ premium; banco de horas among top jornada claim themes (2.9M claims 2015–25) | Near-fully removes the expiry surprise; converts payout-vs-compensate into a priced decision | **S–M** (4–7 em) | +2–3 em (draft schedule fixes) | Projection service |
| 5 | What-If Simulator | Labor = 50–70% of opex in service industries; PEC 6x1 / Mexico 40h make "what will it cost" a board question | Ground-truth mechanical cost delta (vs consultant guesswork); can't model behavior change | **M** (4–8 em) | +4–6 em if shadow-run infra missing | Policy versioning + batch re-run |
| 12 | OT Cost Forecaster | OT = 5–12% of hours in frontline ops (peaks 20%); ~20% of workforce drives ~80% of OT | High-accuracy projection; saves money only when paired with mitigation hand-off | **M** (6–9 em) | shared w/ #13 | Schedule-ahead data quality |
| 2·3 | LawTrack AI (reader + monitor) | 72 CBA instruments for one account (Boticário); ~600 US state law changes/yr; live reforms in every target market — one missed change misconfigures every affected tenant at once | Cuts CCT-analysis 50–70%; kills "we didn't know" + "who's affected" for covered jurisdictions; human review stays (and should) | **M–L** reader (8–10 em) | +L monitor (12–15 em) + 0.5–1 FTE/cluster ops | Reader: rules taxonomy + eval set (exist). Monitor: versioned 4-layer templates (in flight) |
| 19 | WhatsApp Assistant | Up to 60% of HR support time on repeat questions; ~9 hrs/wk per HR pro; $22 live vs $2 self-serve (HDI) | 50–70% deflection of informational load; transactions phased (Portaria 671 for punch) | **L** (12–18 em) | + WhatsApp COGS + eval ops | Grounding architecture; hallucination budget ≈ 0 |
| 20 | Conversational Time-Off | Highest-frequency HR transaction (5–15 requests/employee/yr); 67% of employees struggle to get timely HR answers | Removes HR brokering for standard cases end-to-end | **S–M** (3–5 em on #19) | — | #19 channel |
| 7 | Payroll Close Copilot | 29 workweeks/yr per 1,000 employees fixing errors; 15 corrections/pay period; 80% avg payroll accuracy (EY) | Agent owns 60–80% of the chase volume; judgment calls stay human | **L** (12–18 em; 1-quarter narrow v1) | — | #19 channel for deskless reach |
| 15 | Shift-Fill Agent | 5–10% unscheduled absence in hourly workplaces; $3,600/hourly worker/yr (Circadian); fills done by phone (40% of managers) | Converts a 1–2 hr scramble into minutes, compliance-checked and cost-priced; can't conjure willing workers | **M–L** (8–12 em on #19) | L standalone | #19 + schedules live in day.io |
| 14 | AI Schedule Builder | 56% of managers spend 3–10+ hrs/wk scheduling (Legion); Chipotle paid $20M+$1M for NYC Fair Workweek violations | v1 (compliance-priced assisted rostering) ≈ 60% of value at 35% of cost; demand forecasting needs external data | **L** (15–24 em, v1) | **XL** (+2–3 quarters) | Tenants actually scheduling in day.io |
| 25 | Attrition Early-Warning | Retail turnover ~60%/yr (BLS), c-stores 100–130%; frontline exit costs ~40% of salary / $2k–10k each | Catches the 40–60% of quits that telegraph; value gated on manager intervention workflow | **M–L** (9–12 em) | 2–3 quarters calendar (label lag) | Exit labels + privacy/legal review |
| 31 | Recruiting Agent (reframed 2026-07) | Hourly hiring runs ~12 days application→start and most of it is coordination latency (phone-tag, no-shows, dropped debriefs), carried by HR/managers hiring as one of five hats | Personal hiring chief-of-staff: agent owns outreach/scheduling/debrief/next-step, human keeps every verdict ("coordination, not judgment"); screening demoted to phase 2+ | **M–L** (8–12 em on #19) | Screening phase gated on design partners | #19 channel + calendar integration |

*(em = engineer-months)*

---

# A. Calc-engine features

## #2 · #3 LawTrack AI — read any labor-rule source, flag what changed, draft the config

> **Merged feature.** The former "#2 CBA/CCT Reader" and "#3 LawTrack AI" are one product: a single
> ingestion → extraction → mapping → gap-map → draft-diff engine with **two ingestion modes** —
> *manual upload* (drop a CBA/law PDF on demand) and *auto-detect* (the agent monitors statutes and
> CCT/ACT renewals). Both land on the same review surface and compare the source against a pay
> policy. The mockup (`lawtrack-ai/`) already reflects the merge.

### 1. How big is the problem

- **CBA/CCT reading is a recurring implementation tax.** One enterprise account — Grupo Boticário — required manual classification of **72 collective instruments** (`brazil-cct-support-matrix.md`). At a realistic 2–5 expert-days per instrument to read, extract T&A rules, and map to configuration, that single account is **30–70 person-weeks** of pre-revenue implementation labor — and it recurs, because Brazilian CCTs renegotiate **annually**. In France roughly **98% of employees** are covered by branch collective agreements; Germany's tariff system and most of Western Europe run 60–80%+ sectoral coverage. Retail and logistics — day.io's core verticals — are exactly the multi-instrument segments.
- **Statutory churn is structural, not episodic.** In the US alone: **~150 state posting changes/yr** (Poster Guard), **200+ mandatory federal/state/local posting changes/yr** (ComplyRight), and the original scan's **~600 state employment-law changes/yr**; minimum wage moves across dozens of jurisdictions every January 1 and July 1. **Every day.io target market has a reform in flight right now** — Brazil 6x1/40h, Mexico 48→40h (2026–2030), India's Labour Codes, France/Germany 2026 — all already flagged "time-sensitive" in the worldwide-calculations research, which *is* a manual compliance radar today.
- **The failure mode is correlated and high-severity.** For a calculation vendor, one missed change — a renewed CCT band or a statutory reform — silently propagates wrong results across **every affected tenant simultaneously**; today its mitigation is "someone noticed." Cost anchor: horas extras is the **#1 subject of Brazilian labor litigation — 25.7% of all claims in 2025, ~633,000 lawsuits** (TST), and a large share are precisely CCT-premium disputes (which band, which base, which stacking rule). A misread instrument becomes tenant-wide, systematic underpayment.
- **The benchmark for what's possible:** CollBar compresses CBA analysis from **~6 months to weeks**; Deel/Papaya/isolved ship statutory-change monitors across 150+ countries — none close the loop from *detected change* to *drafted config update*. That last mile is ours.

### 2. How much does the solution solve it

**Two modes, one engine.** The pipeline is identical whichever way a document arrives — extract the T&A rules, map each to the engine capability taxonomy (✅ supported / ⚠ needs config / ❌ gap), render the source with clauses marked in place, and draft the pay-policy config diff for clause-by-clause review. What differs is the trigger and the comparison baseline:

- **Auto-detect mode** — the agent monitors statutes/gazettes and auto-renewing CBAs/ACTs per jurisdiction. When it finds a change it compares the **new/renewed version against the tenant's current configured policy** — it already knows which policy applies, because the four-layer inheritance (country → state/workplace → company → policy) makes affected descendants enumerable by construction. This "which tenants, which policies" answer is the part no generic compliance-news service can give. Output: a flagged config diff, one-click into review.
- **Manual upload mode** — the user drops a CBA/law PDF. Because there is no monitored context, the user **must choose which pay-policy template** the document is compared against (the mockup gates the Analyze action on that selection). This is the pre-sales/onboarding path: run a prospect's instruments through it during the sales cycle and produce a support-matrix in a day.
- **Extraction vs mapping have opposite difficulty and value.** Extraction (pull OT bands, rest rules, premiums, hours-bank terms out of the PDF) is near-commodity LLM work — **80–90%** clause-level accuracy, residual failures on ambiguous drafting, cross-references, side letters; any competitor or IT department can do it. **Mapping** is the product: it lands each rule against the taxonomy and drafts the actual config, converting "months of consultant reading" into "days of reviewing a cited draft." It's un-DIY-able because there is nothing to map onto without the engine — our premium-stacking taxonomy and worldwide-calculations research are the structural advantage.
- **Realistic effect:** cut the CCT-analysis portion of implementation **50–70%**, and kill the "we didn't know" and "who's affected" failure modes ~completely for covered jurisdictions — converting the moat from a claim into a weekly-experienced product behavior. **Full automation is the wrong bar** — human-in-loop legal review must remain (a liability feature, not a weakness), and effective-date/transition-rule interpretation stays human. What it surfaces but doesn't solve: genuine legal-interpretation calls, and engine capability gaps (those become a live, customer-driven roadmap registry — itself valuable).
- **Trust dynamic to design for:** false positives kill this feature. Tune alerts for precision; sweep recall into a periodic digest.
- **Compounding:** the same ingestion asset powers a future living-handbook, and — underrated — **pre-sales**: the support-matrix demo closes enterprise deals.

### 3. Effort estimate

**Two phases: the reader ships first and cheap; the monitor is the heavy, ops-carrying add-on.**

- **Phase 1 — reader mode (manual upload). ~8–10 eng-months, one squad-quarter to design-partner-ready, no ops tail.**
  - Document pipeline (OCR, chunking, versioning): 2 em
  - Extraction schema + prompts + confidence scoring: 2 em — the rules taxonomy largely exists from the research corpus
  - Mapping layer to capability matrix + config drafting: 2–3 em
  - Review UI (clause-by-clause evidence citation, accept/edit/reject, **required policy-template selection**): 2 em
  - Eval harness: **~free** — the 72 manually classified Boticário instruments are a ready-made golden set, a rare luxury
  - Global expansion: +1–2 em per jurisdiction family (France CCN, Germany TV) — mostly taxonomy and eval work, not new infrastructure
- **Phase 2 — auto-detect mode (the monitor). +L of product, plus a permanent ops line that is also the moat.**
  - Source ingestion + change detection + dedup (4–5 em), mapping onto versioned country-layer templates (3–4 em), internal legal-review workflow (2 em), tenant-facing flags + draft diffs + audit trail (3–4 em) — ~**12–15 em / ~1.5 quarters** for the top-5 jurisdictions (less of it net-new, since Phase 1 already built the extract→map→draft engine).
  - **Ongoing ops: 0.5–1 FTE legal-curation per major jurisdiction cluster.** This is the real cost line — and precisely the recurring cost that makes "never DIY" true: an internal rebuild is obsolete the day the next reform lands.
  - **Hard dependency:** structured, versioned four-layer policy templates must land first. Sequence Phase 2 accordingly.
- **Main risk (both phases):** accuracy expectations. Mitigation is positioning — ship as "cited draft for expert review," never "auto-configuration." **Calendar:** reader mode 1 quarter to design partner, 2 to GA; monitor mode follows the templates.

---

## #5 Policy What-If Simulator

### 1. How big is the problem

- **Labor is the largest controllable cost line** in day.io's verticals: ~**50–70% of operating cost** in service industries broadly, ~**41% of revenue** in healthcare, 10–20% in retail. Policy parameters (OT thresholds, tolerance windows, schedules, bank rules) are levers directly on that line — and today customers pull them blind.
- **Reform pressure makes it a board-level question:** every Brazilian customer watching the 6x1/40h debate, and every Mexican customer inside the 40h phase-in, is asking finance "what will this cost us?" The current answer comes from consultant spreadsheets with invented assumptions.
- **The everyday version is constant:** adopting semana espanhola, moving a plant to 12x36, changing an OT threshold or a rounding tolerance — changes are made, and the cost is discovered at the next close. Worked example of the stakes: a 1-percentage-point misjudgment in OT policy on a 10,000-employee, R$500M annual payroll is **~R$5M/year**, invisible until spent.

### 2. How much does the solution solve it

- **For mechanical cost delta, it solves the problem about as well as it can be solved** — re-running real historical periods through the real engine under the candidate policy is *ground truth*, not a model. No consultant, no DIY spreadsheet, and no competitor without an engine-in-the-loop can produce a comparable number. Compliance impact (violations under candidate config) comes free from the same run.
- **Honest boundary:** it computes the counterfactual *holding behavior constant*. Employees and managers adapt to new rules (punch behavior shifts, scheduling shifts), so label outputs explicitly as "mechanical delta on historical behavior" — that's still 10x better than the status quo, and the labeling protects credibility.
- **Adoption risk is low** because the buyer is finance/HR leadership with a live question; during reform seasons this doubles as a **sales weapon** ("bring us last year's data, we'll price the reform for you in a demo").

### 3. Effort estimate

**M — if the engine's shadow-run capability exists; the deterministic design makes this its natural first product payoff.**

- Core dependency: batch re-runs of historical inputs under an alternate **policy version**. Roseman's deterministic engine + versioned config is exactly this shape; if recalculation infra exists, ~70% of the plumbing exists.
- Build: scenario builder as a **draft policy in the existing config UI** (reuse the settings-page work directly, 1–2 em), batch orchestration + cost/compliance diff service (2–3 em), LLM narration of the verdict (1 em), compute guardrails — re-running 10k employees × 12 months is real compute; sampling strategies (1 em).
- **Total: 4–8 eng-months** with shadow-run infra; **+4–6** if that infra must be built (in which case build it — #12 and #13 ride the same service).

---

## #6 WhyPay Copilot — trace-to-English, two surfaces

### 1. How big is the problem

- **Time & attendance errors are the single largest payroll-error category.** EY's payroll-error study: T&A errors occur **more than once per employee per year**, costing **~$250,000 per 1,000 employees annually**; missing/incorrect punches alone carry the highest direct cost of any error type (**$71,700 per 1,000 employees**); organizations spend **29 forty-hour workweeks per 1,000 employees per year** fixing the common errors; average payroll accuracy is **80%**, with **15 corrections per pay period**. Every one of those corrections begins with a human reconstructing *why the number is what it is*.
- **The question volume is constant:** payroll/HR fields **~30 questions per pay period per 1,000 employees** (EY) — dominated by "why is my pay X."
- **In Brazil the question escalates into court:** horas extras is the **#1 lawsuit subject — 25.7% of all labor claims, ~633,000 suits in 2025**; jornada-related themes (OT, intrajornada, ponto, banco de horas, DSR) generated **~2.9M claims from 2015–2025** (TST). Every one of those cases is, at its core, a dispute over a derivation.
- **The regulatory tailwind:** unions are negotiating explainability-of-algorithmic-decisions clauses into agreements (original scan) — explainability is becoming a legal requirement, not a nice-to-have.

### 2. How much does the solution solve it

- **Ticket deflection (employee surface):** for the "why" class — balance and derivation questions — grounded self-serve answers realistically deflect **50–70%** before they reach HR. Benchmarks: self-service resolution costs **$2 vs $22** for live support (HDI); HR-copilot vendors claim 70%+ auto-resolution. Ours is differentiated because the answer is computed from the tenant's actual trace, not a policy FAQ.
- **Dispute resolution (HR surface):** an HR admin answers a challenge in minutes with policy-setting citations ("Saturday shows 2h at 60% because the CCT Saturday band overrides the 50% default") instead of manually re-deriving. This is also the seed of the future court-ready evidence pack.
- **What it doesn't fix — by design:** wrong data or wrong configuration. It *exposes* them faster, moving discovery upstream of payday — which converts a $291-per-error post-hoc correction (EY average) into a pre-close fix. That's a feature.
- **Strategic weight beyond the tickets:** this is the cheapest way to make the moat *visible daily* — the audit trail stops being an architecture slide and becomes a thing every employee touches. Foundation for the labor-claim defense pack, the WhatsApp assistant's pay answers, and the union-driven explainability requirements. Highest leverage-per-effort on the list; the original doc's #1 pick holds up under the numbers.

### 3. Effort estimate

**S–M, with one honest dependency that defines coverage.**

- The entire feature is a **rendering layer over the calculation trace**. Roseman's deterministic engine is designed to emit it; the legacy calc path almost certainly isn't. v1 coverage = Roseman-computed tenants — accept that openly (it's also a healthy migration forcing-function), and budget for the gap.
- Build: trace → canonical explanation schema (1–2 em), LLM narration with hard guardrails — **numbers come verbatim from the trace, the LLM only phrases; it never computes** (1 em), HR surface (1–2 em), employee surface — tone, multilingual, rollout care (2–3 em).
- **Estimate: 3–6 eng-months for the HR surface; 8–10 total for both surfaces.** If the trace has gaps, add ~a quarter of engine work — work the engine needs anyway.

---

# B. Payroll close & T&A operations

## #7 Payroll Close Copilot

### 1. How big is the problem

- **The close is a monthly chase, and the chase is quantified.** EY: an average 1,000-employee organization spends **29 forty-hour workweeks per year** fixing the most common payroll errors — more than half a full-time year of pure correction labor; **26 minutes per employee per year** goes to fixing time punches alone; the average org makes **15 corrections per pay period** and runs **80% payroll accuracy**. Behind each correction is a message: chase the employee for the justification, chase the manager for the approval, repeat across every department, every cycle.
- **The cost of a leaky close compounds downstream:** manual-heavy 1,000-employee companies can spend **$900k+/year** on error correction (EY-derived analyses); the IRS penalizes roughly **1 in 4 businesses** for payroll mistakes; and on the employee side, ~**1 in 5 Americans** hit by a payroll error took drastic financial action (Morning Consult) — pay errors are a retention event, not a bookkeeping event.
- **Persona weight:** this is the payroll admin's single biggest recurring pain, and the monthly moment when day.io's value is actually judged. Agentic payroll ops is also the category the market is coalescing around (Warp, Central; Gartner projecting 40% of enterprise apps embedding task-specific agents by end-2026 — original scan).

### 2. How much does the solution solve it

- **The chase is highly automatable because every part of it is legible to the system:** what's missing is an engine query, who owes it is org data, chasing is messaging, readiness is state. An agent can plausibly own **60–80% of chase volume** — finding gaps, messaging the right person on the right channel, tracking per-department readiness, escalating stalls, preparing the export.
- **What correctly stays human:** exception judgment and final approval. The product frames HR as supervising a readiness dashboard rather than working a phone list.
- **The honest bottleneck is reach, not reasoning:** for deskless workforces, an agent that chases via email doesn't chase — it queues. Resolution rates hinge on the WhatsApp channel (#19). Ship v1 on Slack/email for desk-adjacent tenants, but treat #19 as the unlock for the core market.
- **Compounding:** pairs naturally with punch auto-repair (agent finds the gap, repair proposes the fix, human approves) — together they attack the $250k-per-1,000-employees T&A error line from both ends. **Measurable:** close cycle time (target 30–50% reduction), % periods closed on time, share of corrections caught pre-close vs post-payday.

### 3. Effort estimate

**L. ~12–18 eng-months over ~2 quarters for the real thing; a narrow v1 in one quarter.**

- Agent task-graph per close (detect → assign → message → track → escalate): 4–5 em
- Comms integrations (Slack/email first; WhatsApp via #19): 2–3 em
- Readiness dashboard + escalation policies: 3–4 em
- **Agent auditability** — an agent touching payroll data must itself produce an audit trail (who was messaged, what was claimed, what changed): 2–3 em. Non-negotiable for this domain; budget it explicitly.
- Narrow v1 (missing punches + pending approvals only, one channel): ~8–9 em, one squad-quarter.

---

## #12 Overtime Cost Forecaster

### 1. How big is the problem

- **OT is one of the largest discretionary cost lines in frontline operations:** typical OT share of hours runs **5–12% in frontline ops**, **6–12% in manufacturing/logistics with seasonal peaks of 12–20%**, **3–8% in healthcare with surges to 15%** (industry benchmarks, Umbrex). Every OT hour carries the premium multiplier — and in day.io's jurisdictions, stacked premiums well beyond 1.5x.
- **It's concentrated, therefore addressable:** roughly **20% of the workforce generates ~80% of OT cost** — drivers are findable, which is what makes forecasting actionable rather than decorative.
- **Today the cost is discovered after it's spent:** OT materializes at close; mid-period visibility is spreadsheets. WFM vendors claim **15–30% OT-cost reduction** from AI-driven scheduling (original scan) — forecasting is the honest, low-regret first step toward that number, and we hold every input.

### 2. How much does the solution solve it

- **Projection accuracy is structurally high** because the inputs are known: actuals-to-date plus the published schedule ahead, priced through the *real* engine — capturing threshold effects (weekly OT triggers, bank overflows, premium stacking) that naive run-rate extrapolation misses entirely. That engine-priced forward run is the differentiator; a BI tool can't do it.
- **A forecast saves nothing by itself** — the save happens when a manager changes the remaining schedule. The feature must ship with driver attribution ("logistics is trending 18% over, driven by 6 people covering the open weekend shifts") and a hand-off to schedule mitigation. Alone it's a report; wired to action it's money.
- **Realistic impact:** the addressable slice is the schedule-driven, still-avoidable OT visible mid-period — plausibly **20–40% of period OT** in ops-heavy tenants. A tenant running 8% OT who shaves 1–2 points has a self-funding ROI story, which also makes this an easy expansion-revenue conversation.
- Secondary win: finance gets accurate period accruals instead of surprises.

### 3. Effort estimate

**M. ~6–9 eng-months, one quarter — and it buys shared infrastructure.**

- **Period projection service** (engine-priced forward runs over actuals + schedule): 4–5 em — shared with #13 and structurally sibling to #5's shadow runs; pay for it once
- Driver attribution (deterministic decomposition; LLM narrates): 1–2 em
- Alerts + team dashboard: 1–2 em
- **Dependency to respect:** schedule-ahead data quality per tenant. Garbage schedules produce garbage forecasts — gate the feature per-tenant on a schedule-coverage threshold rather than shipping wrong numbers.

---

## #13 Hours-Bank Advisor

### 1. How big is the problem

- **Banked hours are a liability with a statutory fuse.** Brazil post-2017: tacit individual banco de horas must be compensated **within the month**, written individual agreements within **6 months**, CCT/ACT banks within **12 months** (CLT art. 59) — and hours not compensated in the window convert to payout at the **50%+ OT premium**. The same pattern generalizes: Swiss long-horizon time banks (our 5-year workbench run), comp-time lots in the US, Zeitkonten in Germany.
- **It's mainstream, not niche:** banco de horas has been standard practice across Brazilian mid-market and enterprise since the reform, and bank disputes sit among the leading themes in the **2.9M jornada-related lawsuits filed 2015–2025** (TST) — expired-and-uncompensated balances are claims waiting to be filed.
- **The pain shape is a cycle-end ambush:** HR discovers N employees with expiring balances and faces forced payout — the original doc's example ("force these 12 people's rest days this month or pay R$34k") is typical. Worked scale: 500 employees averaging 20 expiring hours at R$25/h × 1.5 = **~R$375k of exposure in a single cycle**, most of it avoidable with 60–90 days of notice.

### 2. How much does the solution solve it

- **This is the rare AI feature where the hard part is already built.** Balances, accrual run-rates, and cycle rules are fully known to the engine (the cyclical-banked-hours logic) — expiry prediction is essentially **deterministic**, not ML. Confidence in the core promise is therefore high, and the "AI" layer is projection + recommendation + narration.
- **It removes the surprise ~completely** and converts compensate-vs-payout into an explicit per-employee economic decision with a deadline ("schedule these 12 rest days by the 20th or pay R$34k"). The share of forced payouts converted into scheduled compensation depends on schedule flexibility and coverage constraints — start recommend-only, add drafted schedule changes when schedule-edit APIs are ready.
- **Compliance dividend:** zero expired-uncompensated balances = one fewer claim category. This pairs with #6's derivations as tangible "system of consequence" proof.

### 3. Effort estimate

**S–M. ~4–7 eng-months — arguably the fastest real-money win on the list.**

- Expiry projection over existing cyclical-BH engine logic: 2–3 em (rides the #12 projection service)
- Compensate-vs-payout recommendation economics: 1–2 em
- Alerts + advisor UI: 1–2 em
- Drafted schedule changes: later, +2–3 em, gated on schedule-edit APIs
- Low risk, high certainty, direct currency-denominated value — a strong candidate to ship *first* and set the pattern for the projection-service features.

---

# C. Scheduling & workforce

## #14 AI Schedule Builder

### 1. How big is the problem

- **Manager time:** **56% of managers spend 3–10+ hours per week** on scheduling and time-attendance tasks (Legion, 2024 State of the Hourly Workforce); shift-industry benchmarks put scheduling plus related admin at **6–11 hrs/week — up to ~25% of a manager's workweek** (When I Work, 2026); spreadsheet-based scheduling carries a **10–30% error rate**.
- **Compliance is priced in real money:** Chipotle paid **$20M to ~13,000 NYC workers plus $1M in civil penalties** for Fair Workweek violations — 14-day schedule notice, change premiums, clopening rules (largest fair-workweek settlement in the US). Day.io's jurisdictions stack interjornada, rest rules, minor restrictions, and CCT constraints on top; every manually built schedule is a compliance document written freehand.
- **Schedule quality drives the turnover line:** **34% of retail leavers cite schedule inflexibility** as a reason for leaving; the most-engaged teams show **78% lower absenteeism** than the least engaged (Gallup meta-analysis). The schedule is the single biggest lever a frontline employer has on both.
- **Market context:** AI scheduling ~$3.2B→$9.5B by 2030, 47% of large US retailers already deploying, vendors claiming 15–30% OT reduction (original scan). This is the defining WFM battleground — which cuts both ways: biggest prize, most competition.

### 2. How much does the solution solve it

Be honest about the three layers, because they have very different feasibility:

- **(a) Constraint-compliant roster generation** — solved-ish technology (CP/OR solvers). Our differentiation is the *depth of the constraints*: statutory + CCT rules as hard constraints, compiled from the pay-policy config. Generic schedulers bolt compliance on; ours would inherit it.
- **(b) Cost-pricing while building** — unique to an engine-in-the-loop vendor: every draft schedule is priced (OT, premiums, bank effects) *as it's edited*. No competitor without a real calc engine can show a manager the payroll cost of a drag-and-drop in real time.
- **(c) Demand forecasting** (sales history, foot traffic, weather) — requires external data day.io doesn't hold; this is where the headline 15–30% OT-reduction claims live, and it needs POS/traffic integrations or partners.
- **v1 = (a)+(b):** manager states demand (headcount per slot), AI produces a compliant, cost-priced roster and explains trade-offs. That attacks the manager-hours, the compliance exposure, and part of the OT — roughly **60% of the value at ~35% of the cost**. Layer (c) is a follow-on strategic decision, not a v1 requirement.
- **What it can't fix:** tenant adoption inertia (schedules are habits, and the feature only matters where tenants actually build schedules in day.io — a discovery question to answer *before* committing the squad), and preference/fairness politics without a preference-capture surface.

### 3. Effort estimate

**L for v1; XL for the full vision. This is a new subsystem and a land-grab decision, not a feature.**

- v1 (~**15–24 eng-months, 2 quarters, dedicated squad**): solver integration (OR-tools class) 3–4 em; **policy-config → solver-constraint compiler** — the genuinely novel engineering, turning the four-layer config into hard constraints — 4–6 em; engine pricing loop 2–3 em; schedule build/edit UI 4–6 em; preference capture 2–3 em
- Full vision (+demand forecasting, integrations, auto-rostering): **+2–3 quarters**
- Recommended gate: validate that ≥N design-partner tenants schedule natively in day.io before funding; otherwise #15 and #12 deliver the scheduling-adjacent value sooner.

---

## #15 Shift-Fill Agent

### 1. How big is the problem

- **Absence is constant and expensive:** unscheduled absenteeism runs **5–10% of the hourly workforce at any given time** (Circadian); the US all-worker absence rate is **3.2%** (BLS 2024), manufacturing ~3.4%. Cost: **~$3,600 per hourly employee per year** (Circadian, *Absenteeism: The Bottom-Line Killer*); a single no-show costs **~$150–300** in coverage scramble, replacement OT, and management time; absenteeism and no-shows drain an estimated **$225B/year** from the US workforce.
- **The fill process is pre-industrial:** **~40% of managers still fill shifts by texting and calling** down a list (Legion) — a no-show consumes a manager's morning. Sira (YC) exists solely to make agents do this calling (original scan), validating the category.
- **Bad fills create new liabilities:** a panicked fill that violates rest rules or triggers clopening premiums is exactly the violation class behind the Chipotle $20M settlement; an accidental-OT fill silently costs the premium.

### 2. How much does the solution solve it

- **It's a well-bounded agent loop — the best kind:** open shift → rank qualified candidates by **compliance (rest rules, interjornada), projected cost (engine-priced, including OT it would trigger), skills, and fairness rotation** → message candidates on WhatsApp → confirm acceptance → write back to the schedule. The compliance-and-cost ranking is the un-DIY-able part; the agent is just the face.
- **Time cost: near-fully solved** — a 1–2 hour scramble becomes minutes, and the fill is pre-checked and pre-priced rather than panicked. **What it can't do:** conjure willing workers. Acceptance rates depend on incentives and workforce liquidity, not on AI — set expectations accordingly, and log fairness rotation (legal + morale protection).
- Employee-side benefit is real and sellable: first-come access to extra hours, transparently offered.

### 3. Effort estimate

**M–L riding #19; L standalone.**

- On top of the #19 channel and live schedule data: engine-backed ranking service 3–4 em; outreach state machine (offer, expiry, cascade, acceptance) 3–4 em; schedule write-back + audit 1–2 em; manager console 1–2 em → **~8–12 eng-months, 1–1.5 quarters**
- Standalone (building its own channel): add 4–6 em and lose the shared-infra logic — don't.
- Dependencies: schedules must live in day.io (same discovery gate as #14 v1 — but note #15 needs only schedule *data*, not schedule *building*, so it can precede #14).

---

# D. Employee-facing

## #19 Employee WhatsApp Assistant

> **Capability spec:** [`../specs/whatsapp-assistant.md`](../specs/whatsapp-assistant.md) — channel strategy,
> the 5 buckets, the requests-not-punches firebreak, reactive + proactive model, identity tiers, v1 scope.

### 1. How big is the problem

- **The workforce lives on a channel HR doesn't operate on:** ~**80% of the global workforce is deskless** (~2.7B people); frontline workers check WhatsApp **50+ times a day** (original scan) — and in day.io's core markets (Brazil, LATAM), WhatsApp *is* the phone. Deel already ships HR tasks over WhatsApp; the channel question is settled.
- **The HR load it can absorb is measured:** repetitive questions consume **up to 60% of HR support time**; HR professionals average **~9 hours/week** fielding routine questions (HealthJoy benchmark); payroll/HR fields **~30 questions per pay period per 1,000 employees** (EY); a live-agent interaction costs **~$22 vs ~$2 self-serve** (HDI) — a 91% unit-cost difference. Deflection benchmark: HR-copilot vendors (Leena AI) claim **70%+ auto-resolution**.
- **The differentiated slice:** generic HR bots answer *policy* questions. The questions that actually burn T&A-adjacent HR time are *data* questions — "why was my OT only 30%?", "how many hours in my bank?", "when's my shift?" — which require the engine and the trace. An internal bot without the engine gives wrong answers, and wrong answers about pay are radioactive.

### 2. How much does the solution solve it

- **Informational tier (v1): 50–70% deflection is realistic** for schedule, balance, derivation (#6-powered), and policy questions — the direct HR-hours-back value, multilingual by default.
- **Transactional tier (phased): higher value, real legal weight.** "I forgot to punch out" intake feeds correction flows safely. But **punch-by-chat in Brazil must clear Portaria 671** (REP-P electronic registration requirements: record integrity, comprovante issuance) — that's a legal/product workstream, not a toggle. Phase it explicitly; don't let it block v1.
- **The engineering bar that defines success:** grounded-only architecture — every number comes from an engine/trace lookup; **the LLM phrases, it never computes pay.** Hallucination budget ≈ 0, which makes the eval harness a first-class, permanent investment, not a launch task. Identity binding (which employee is this number?) must be designed against proxy abuse.
- **Strategic frame — this is channel infrastructure, not a feature:** #7 chases through it, #15 offers shifts through it, #20 lives in it, #31 screens candidates through it. Evaluate its cost as a platform amortized over five features.

### 3. Effort estimate

**L. ~12–18 eng-months over ~2 quarters; read-only v1 in one quarter.**

- WhatsApp Business Platform integration (Meta review, template management, number strategy): 2–3 em
- Identity/auth binding + anti-abuse: 2 em
- Grounded retrieval + engine-query layer + guardrails: 3–4 em
- **Eval harness + red-teaming for pay answers:** 2–3 em (and ongoing)
- Multilingual + tone + admin console + tenant rollout tooling: 3–4 em
- v1 = read-only Q&A (schedule, balances, WhyPay Copilot): ~8–9 em, one squad-quarter
- **Ongoing costs to price into packaging:** WhatsApp per-conversation COGS + permanent eval maintenance.

---

## #20 Conversational Time-Off

### 1. How big is the problem

- **Highest-frequency employee↔HR transaction there is:** on the order of **5–15 requests per employee per year** across vacation/sick/comp types — each touching employee, manager, and coverage, most flowing through email or corridor conversations today.
- **The cost is latency and coverage errors, plus brokering:** approvals sit in inboxes; leave gets approved that breaks coverage, blackout rules, or CCT terms; and HR relays status. **67% of employees report difficulty getting timely HR responses** (Unthread benchmark) — time-off status is a top offender in that bucket, which itself sits inside the 60%-of-HR-time repetitive load.
- Standalone, this problem doesn't headline; as the flagship *transaction* inside #19, it's what converts the assistant from a Q&A novelty into a daily-active habit.

### 2. How much does the solution solve it

- **For standard cases, end-to-end:** request in chat → balance + coverage + blackout + CCT checks (all data the pipeline already holds — time-off flows already exist as Expected-shift inputs) → filed → manager receives approve/deny **with a reasoned recommendation** → status self-served. HR exits the brokering loop entirely for the standard 80%.
- **Edge cases route to humans, correctly:** negative balances, statutory leave types, medical certificates. The recommendation-with-reasoning to the manager is the quiet differentiator — approvals get faster *and* better-informed (coverage impact visible at decision time).

### 3. Effort estimate

**S–M as a #19 skill — not worth building standalone.**

- Request intake + validation orchestration (checks largely exist): 2–3 em
- Manager approval UX with reasoning + coverage view: 1–2 em
- Notifications + status self-serve: ~1 em
- **Total: ~3–5 eng-months** riding the channel. Bundle it into the #19 roadmap as the first transaction.

---

# E. HR beyond T&A

## #25 Attrition Early-Warning

### 1. How big is the problem

- **Frontline turnover is an economic constant:** retail runs **~60% annual turnover** (BLS), general-merchandise/clothing subsectors up to **81%**, convenience stores **100–130%**; Mercer's 2025 survey puts Retail & Wholesale voluntary turnover at **26.7% — the highest of any sector**. Replacing a frontline worker costs **~40% of annual salary** (Gallup) — **$2,000–$10,000 per retail exit** (McKinsey, State of Fashion 2025). Worked scale: a 5,000-employee retail tenant at 60% turnover and $4k/exit carries a **~$12M/year turnover line**.
- **A meaningful share is preventable — and schedule-driven:** **~42% of leavers say the organization could have retained them**; **34% of retail leavers cite schedule inflexibility** specifically. The single biggest named driver is one whose data day.io *already holds*.
- **The signal advantage is the whole thesis:** punches are the **highest-frequency behavioral stream in any HR stack** — lateness creep, absence drift, shrinking rest gaps, swap spikes, sustained-OT-then-decline. IBM-class results (95% flight-risk accuracy, ~30% turnover reduction, per the original scan) required exactly this signal density, which most HR suites — and every customer IT department — lack. This is the purest "outrun" play on the list.

### 2. How much does the solution solve it

- **Prediction is the easy 40%; intervention is the value.** A risk score that isn't attached to a manager workflow changes nothing. The shippable unit is: cohort risk + **explainable drivers** + concrete suggested actions (schedule fixes first — the driver we control) + measurement of retained-cohort deltas against matched controls. Sell outcomes, not scores.
- **Honest ceiling:** behavioral signals catch the quits that *telegraph* — disengagement-driven exits, plausibly **40–60% of voluntary turnover**. Market-driven and life-event quits won't show up in punches. Even capturing a fraction of the preventable-42% slice on a $12M line clears any reasonable ROI bar.
- **Ethics and legality are product requirements, not footnotes:** cohort-level framing (never individual-surveillance UX), LGPD/GDPR legal bases, works-council review in EU tenants. Getting this wrong makes the feature itself a churn and reputation risk; getting it right is a differentiator with unions increasingly scrutinizing algorithmic workforce tools.
- **Cold-start reality:** requires historical exit labels (termination events exist in the T&A data) plus enough tenure history per tenant; model claims must be validated against labels that arrive with a lag.

### 3. Effort estimate

**M–L in eng-months, but calendar-bound — plan 2–3 quarters wall-clock.**

- Feature store over punch/schedule/exit history: 3–4 em
- Model + explainability layer (data-science-heavy): 3–4 em
- Cohort UI + manager intervention workflow: 2–3 em
- Privacy/legal workstream in parallel (LGPD/GDPR/works councils): not eng-months, but real
- **Build: ~9–12 eng-months. Calendar: 2–3 quarters**, because label lag gates validation. Run as a design-partner beta with 2–3 high-turnover tenants (retail/logistics — the Boticário profile is ideal).

---

# F. New addition

## #31 Recruiting Agent — the HR person's hiring chief-of-staff

> **Reframed 2026-07-14 (with Assaf).** The original take here was a Paradox-style candidate
> *screening* funnel — and it was flagged as the highest-strategic-risk item on the shortlist. The
> reframe keeps the proven mechanics but changes what we agent: **the person, not the process.** A
> personal agent for one HR person that owns everything *around* the interview — outreach,
> conversational scheduling, debrief capture, next-step coordination — and **never evaluates a
> candidate** ("coordination, not judgment," the #19 firebreak pattern). The tenant's ATS stays the
> system of record. Screening is demoted to a phase-2+ option behind the design-partner gate. Build
> reference: [`../specs/recruiting-agent.md`](../specs/recruiting-agent.md).

### 1. How big is the problem

- **Hourly hiring is a speed game, and the baseline is slow:** pre-AI, Chipotle ran **~12 days from application to start**; hourly candidates overwhelmingly take the first offer that lands, so days of latency = lost candidates. Most of that latency is *coordination*, not evaluation — phone-tag to book a screen, no-shows, dropped debriefs, chasing a manager for round-2 availability.
- **The scale is structural:** at 60–130% frontline turnover, hiring is a permanent operation — a 5,000-employee retail tenant makes on the order of **3,000 hires/year**. Average US cost-per-hire is **~$4,700** (SHRM), with frontline replacement all-in at $2k–10k. And the humans running the loops are HR generalists and managers who hire as one of five hats — the same managers already losing 3–10+ hrs/week to scheduling.
- **Proof the AI mechanism works — at category-defining scale:** Chipotle × Paradox ("Ava Cado," 3,500+ restaurants): **time-to-hire down 75% (12 → 4 days)**, multilingual, with managers reclaiming weekly admin hours (CNBC, company case data). Paradox's biggest wins are precisely the coordination mechanics (scheduling, reminders, no-show recovery) this scope keeps.

### 2. How much does the solution solve it — the reframed fit

The original question — *should day.io enter the recruiting category?* — dissolves under the reframe: we don't. No sourcing, no job boards, no screening, no ATS. The agent runs the loop the human already owns:

- **The loop (see spec §3):** ① outreach & conversational scheduling in the HR person's name over WhatsApp (not a booking link — this demographic doesn't click Calendly links), against their live calendar; ② **debrief capture at call-end** — "How was Maria?", answered by voice note, structured into a scorecard while the memory is fresh; ③ verdict-driven next-step orchestration — round 2 proposals that *ask permission* before pulling a colleague in, approval-gated rejection/keep-warm sends, interviewer-debrief chasing; ④ per-req pipeline memory + full audit trail.
- **The differentiated assets:**
  1. **The channel (#19):** candidates and employees are the same demographic on the same WhatsApp — outreach reuses the assistant infrastructure nearly wholesale.
  2. **Interviewer availability from the shift roster:** when round 2 is with a store manager, their availability is the day.io roster, not an Outlook calendar. GoodTime/ModernLoop/Calendly read office calendars; no recruiting tool can see shifts and floor coverage.
  3. **The demand signal nobody else has (phase 2/3):** #25 attrition risk + schedule gaps → **predictive headcount** ("Store 12 will be 4 heads short by March — open the req now"). ATSs react to reqs; we could *originate* them.
  4. **Hire-to-first-punch continuity:** verdict "hire" → employee record, policy assignment, schedule — day-1 ready. Nobody closes the loop from predicted vacancy to first punch.
- **What the firebreak buys:** no automated employment decisions → no NYC Local Law 144 bias-audit obligation and no EU AI Act high-risk classification for v1. The compliance workstream shrinks to candidate-PII handling (LGPD/GDPR — a new data-subject class) + AI disclosure in first contact.
- **Honest risks:** scheduling alone is table stakes — if tenants don't adopt the debrief-at-call-end habit, this is a charming Calendly; capability ② is the retention hook and must be designed and measured as such. And the who-runs-the-loop question (central HR vs. location manager) decides where the agent lands first.

### 3. Effort estimate

**M–L — meaningfully lighter than the screening version, and most of the strategic risk is gone.**

- Candidate/req data model: 1–2 em · Scheduling conversation flows (reusing #19's channel): 2–3 em · Calendar integrations (Google/Microsoft): 1–2 em · Debrief capture + pipeline surface: 2 em · Orchestration, approvals, audit trail: 1–2 em · Candidate-PII compliance workstream: 1 em
- **Total: ~8–12 eng-months, ~1–1.5 quarters** (vs. 13–17 em for the screening framing — the job-board integrations and bias-audit workstream drop out). Screening as phase 2+ re-adds ~5–8 em plus the compliance load.
- **The design-partner gate stays, with a sharper question:** not "does the buyer want hiring from their T&A vendor?" (softened — this isn't hiring infrastructure and the ATS stays) but *who runs the candidate call at our tenants — central HR or the location manager? And will they debrief to an agent at call-end?* If the manager: even better — they're already a day.io user and their availability is already the roster.

---

# Shared infrastructure — the real build plan

The 12 features above are closer to **5 platform investments + thin feature layers** than a dozen independent builds. Sequencing should buy the platforms early:

| Platform investment | Bought by | Then powers | Approx cost |
|---|---|---|---|
| **Calculation trace service** (canonical, complete, queryable derivations) | #6 | #7 answers, #19 pay-Q&A, future claim-defense pack | 3–6 em (Roseman-native; legacy path is the gap) |
| **Period projection service** (engine-priced forward/shadow runs) | #12 or #5 | #5, #12, #13 | 4–6 em, paid once |
| **WhatsApp channel + identity** | #19 | #7 chase, #15 offers, #20 transactions, #31 candidate outreach | 5–7 em of #19's total |
| **Document ingestion + rules taxonomy** | LawTrack reader mode (#2·3) | LawTrack monitor mode (CCT/statute change detection), future living handbook | 4–5 em of the reader's total |
| **Versioned 4-layer policy templates** | already in flight | #3 mapping, #5 candidate configs, #2 drafting target | prerequisite — protect it |

## A sequencing sketch (one opinionated pass — argue with it)

- **Q1:** #6 HR surface (trace) + #13 (fastest money, sets the projection pattern) + start #19 (Meta review lead-times are real)
- **Q2:** #19 read-only GA + #20 · #12 (completes projection service) · start **LawTrack reader mode** (#2·3, Brazil)
- **Q3:** **LawTrack reader** GA + pre-sales motion · #7 v1 riding the channel · #5 (reform-season timing) · #25 design-partner kickoff
- **Q4+:** **LawTrack monitor mode** (after templates land) · #14 v1 → #15 · #31 coordination v1 if the design-partner gate clears

Total shortlist, v1 scopes, shared infra deduped: roughly **95–125 eng-months** — about **3–4 squads for a year**. The scorecard's job is to make the cut lines explicit; the sequencing above front-loads the items where problem size, solve-confidence, and effort all agree (#6, #13, #19), and pushes the two genuine bets (#14 full vision, #31's screening phase) behind explicit validation gates.
