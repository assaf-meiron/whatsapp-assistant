# AI Feature Ideas — 30 Ways AI Makes day.io Indispensable

> **Strategy artifact** — the catalog for the `ai-features/` workspace (see
> [`../README.md`](../README.md)); not part of the context-base index. Promising ideas get an
> interactive mockup under [`../prototypes/`](../prototypes/) (e.g. `prototypes/lawtrack-ai/` =
> Idea #3). Drafted 2026-07-14 from the
> context base + a web scan of competitor AI features and the "build-vs-buy in the AI era" debate.
> Global-first lens; Brazil examples where they sharpen an idea.

## The two strategic lenses (and the thesis)

**Lens 1 — the IT-department threat.** Customers' IT teams increasingly believe they can rebuild
what we do with AI coding tools (Retool 2026: 35% of teams already replaced at least one purchased
SaaS tool with a custom AI-built one; 78% plan to build more). But every serious analysis puts
**compliance-heavy calculation engines on the "still buy" list**: what kills a DIY rebuild isn't
writing the code, it's the years of edge cases, the audit trail, the liability, and keeping the
rules current across jurisdictions forever. The answer is therefore **not** to hide from the threat
but to play it three ways:

1. **Deepen the moat** — make the engine's correctness *visible*: explainability, audit trails,
   always-current statutory rules. Switching away from the system that generates your compliance
   proof means taking the liability on yourself.
2. **Judo move** — become the platform IT builds **on**, not instead of: expose the governed calc
   engine to their agents (MCP/APIs), and give them a sanctioned "build your own calculation"
   studio. Their AI ambitions become our usage, not our churn.
3. **Outrun** — ship the AI features that need our cross-customer data and domain depth; those
   can't be cloned by one IT team no matter how good their coding agent is.

**Lens 2 — make HR's life better.** The market is moving from copilots (assist a human) to agents
(own the workflow). For HR that means: stop being a system HR *queries* and become a colleague that
*does the work* — answers the employees, runs the payroll close, drafts the documents, watches the
law change.

Every idea below is tagged with the lens it serves, an effort tier, and its defensibility angle.

**Effort tiers:** 🟢 **Quick win** — weeks; mostly LLM + data we already have. 🟡 **Medium** — a
quarter-ish; a new surface or integration. 🔴 **Big bet** — multi-quarter; a new subsystem.

---

## Summary table

| # | Idea | Category | Effort | Impact | Lens |
|--:|:--|:--|:--|:--|:--|
| 1 | Calculation Studio (prompt-to-calculation, productized) | Calc engine | 🔴 | ★★★ | IT-judo |
| 2 | CBA/CCT reading → merged into #3 LawTrack AI | Calc engine | 🟡 | ★★★ | Moat + HR |
| 3 | LawTrack AI (reads CBAs/laws + monitors changes) | Calc engine | 🟡 | ★★★ | Moat |
| 4 | Pay-Policy Configuration Copilot | Calc engine | 🟢 | ★★ | HR |
| 5 | Policy What-If Simulator | Calc engine | 🟡 | ★★ | Moat + HR |
| 6 | WhyPay Copilot (HR + employee surfaces) | Calc engine | 🟢 | ★★★ | Moat + HR |
| 7 | Payroll Close Copilot | Payroll ops | 🟡 | ★★★ | HR |
| 8 | Anomaly & Fraud Detective | Payroll ops | 🟢 | ★★ | HR |
| 9 | Timesheet Auto-Repair | Payroll ops | 🟢 | ★★ | HR |
| 10 | Labor-Claim Defense Pack | Payroll ops | 🟡 | ★★★ | Moat |
| 11 | Audit Simulator | Payroll ops | 🟡 | ★★ | Moat |
| 12 | Overtime Cost Forecaster | Payroll ops | 🟡 | ★★ | HR |
| 13 | Hours-Bank Advisor | Payroll ops | 🟢 | ★★ | HR |
| 14 | AI Schedule Builder | Scheduling | 🔴 | ★★★ | HR |
| 15 | Shift-Fill Agent | Scheduling | 🟡 | ★★★ | HR |
| 16 | Shift-Swap Marketplace | Scheduling | 🟡 | ★★ | HR |
| 17 | Fatigue & Burnout Sentinel | Scheduling | 🟡 | ★★ | Moat + HR |
| 18 | Workforce What-If Planner | Scheduling | 🔴 | ★★ | HR |
| 19 | Employee WhatsApp Assistant | Employee-facing | 🟡 | ★★★ | HR |
| 20 | Conversational Time-Off | Employee-facing | 🟢 | ★★ | HR |
| 21 | Onboarding Concierge | Employee-facing | 🟢 | ★ | HR |
| 22 | HR Inbox Copilot | HR beyond T&A | 🟡 | ★★ | HR |
| 23 | HR Document Generator | HR beyond T&A | 🟢 | ★★ | HR |
| 24 | Living Handbook Q&A | HR beyond T&A | 🟢 | ★★ | HR |
| 25 | Attrition Early-Warning | HR beyond T&A | 🟡 | ★★★ | Outrun |
| 26 | Contract-to-Record Ingestion | HR beyond T&A | 🟢 | ★ | HR |
| 27 | HR Workflow Agent Studio | HR beyond T&A | 🟡 | ★★ | IT-judo |
| 28 | day.io MCP Server / Agent Platform | Platform & data | 🟡 | ★★★ | IT-judo |
| 29 | Benchmark Insights | Platform & data | 🟡 | ★★ | Outrun |
| 30 | Embedded Earned-Wage Access | Platform & data | 🔴 | ★★ | Outrun |

---

## A. The calc engine as an AI product (moat-deepening + IT-judo)

### 1. Calculation Studio — prompt a new calculation into existence 🔴 ★★★
- **What:** Productize the internal `prompt-to-calculation` workbench: a customer describes a rule
  in plain language ("night hours past 3h reclassify the whole shift at +15%"), and the studio
  drafts the calculation, places it in the pipeline, simulates it on the customer's real data
  (before/after), and deploys it into their pay policy — verified, versioned, auditable.
- **Who:** HR managers + implementation teams; indirectly customer IT.
- **Why AI now:** This repo is already proving it works (workbench runs + the modular engine's
  intent-coding PoC). No competitor lets customers *create* calculations — they all configure
  preset ones.
- **Moat vs DIY-IT:** The direct answer to "we could build this ourselves": here's a sanctioned
  builder, on a verified engine, with the audit trail. Their creativity, our liability coverage.

### 2. CBA/CCT Reader → merged into #3 LawTrack AI 🟡 ★★★
- **Merged.** Reading a collective agreement (CCT/ACT, union contract, tariff agreement) and
  mapping it to a pay-policy config is now the **manual-upload mode** of #3 LawTrack AI — same
  ingestion + extraction + mapping engine, same review surface. See #3.

### 3. LawTrack AI — read any labor-rule source, flag what changed, draft the config 🟡 ★★★
- **What:** One ingestion → extraction → mapping → gap-map → draft-config engine over labor-rule
  sources, in **two modes.** *Auto-detect:* the agent monitors labor-law and CCT/ACT changes per
  jurisdiction (Brazil PEC 6x1, Mexico 40h 2026–2030, India Labour Codes, France/Germany 2026 —
  all tracked "time-sensitive" in our research), determines effective dates, and compares each
  **new/renewed version against the tenant's current configured policy** (the four-layer
  inheritance makes affected policies + customers enumerable), then drafts the config update for
  one-click review. *Manual upload:* drop a CBA/law PDF on demand — the user **picks which
  pay-policy template** it's compared against — for onboarding and pre-sales support-matrices.
  (Absorbs the former "CBA/CCT Reader," #2.)
- **Who:** HR + implementation + compliance; also an internal tool for our own ops.
- **Why AI now:** We already ran this classification manually across Grupo Boticário's 72
  instruments (`brazil-cct-support-matrix.md`) — the validation set. CollBar compresses CBA
  analysis 6 months → weeks; US state employment law alone changes ~600×/yr;
  Papaya/Ramco/Deel/isolved ship statutory monitors across 150+ countries — none close the loop
  from *detected change* to *drafted policy-config update*. That last mile is ours.
- **Moat vs DIY-IT:** Extraction is easy; *mapping to a verified engine that then runs the rules*,
  and enumerating *which tenants are affected*, is the product — an IT department has nothing to
  map onto. And rules don't stop changing: an internal rebuild is obsolete the day the next reform
  or CCT renewal lands. This feature makes that moat *visible*.

### 4. Pay-Policy Configuration Copilot 🟢 ★★
- **What:** A conversational layer over pay-policy setup: explains every setting in context
  ("what does this tolerance window do?"), answers "how do I configure X?", validates the draft
  policy against the jurisdiction's statutory floor, and flags contradictory settings.
- **Who:** HR admins + onboarding/implementation (cuts time-to-live and support tickets).
- **Why AI now:** `pay-policy-configuration.md` documents tab-by-tab what every setting does — the
  knowledge base already exists; this is RAG + guardrails.
- **Moat vs DIY-IT:** Low; this is table-stakes UX. Its value is adoption speed and fewer
  misconfigurations (which become *our* support cost and the customer's compliance risk).

### 5. Policy What-If Simulator 🟡 ★★
- **What:** "What happens if we adopt semana espanhola / move to a 4-day week / change the OT
  threshold?" → re-run past periods under the candidate policy on real data; show cost delta,
  affected employees, and compliance impact, narrated in plain language.
- **Who:** HR + finance.
- **Why AI now:** The engine can already recompute; AI's job is translating intent → candidate
  config → readable verdict.
- **Moat vs DIY-IT:** Simulation requires the verified engine — inherently un-DIY-able.

### 6. WhyPay Copilot — trace-to-English, two surfaces 🟢 ★★★
_(formerly "Explain My Hours")_
- **What:** For any computed day or period: a plain-language derivation from punches → rules
  applied → result, citing the exact policy settings ("your Saturday shows 2h at 60% because the
  CCT's Saturday band overrides the 50% default"). Surface 1: HR answering disputes. Surface 2:
  employee self-serve "why is my paycheck X?" — deflecting the tickets before they reach HR.
- **Who:** HR, payroll admins, employees.
- **Why AI now:** The engine already has the trace; LLMs make it readable. Oracle (Pay Analyst)
  and Dayforce (Pay Clarity Agent) already explain pay conversationally — but at payslip level;
  nobody traces down to the rule and the policy setting. Market pull: unions are bargaining
  explainability-of-algorithmic-decisions clauses into contracts — this feature turns a legal
  demand into a product strength.
- **Moat vs DIY-IT:** Explainability *is* the audit trail — the compliance-proof artifact analyses
  call the reason calc engines stay "buy." Probably the highest leverage-per-effort item on this list.

## B. Payroll close & T&A operations (payroll admin's month)

### 7. Payroll Close Copilot 🟡 ★★★
- **What:** An agent that owns the close checklist: finds missing punches and pending approvals,
  messages the right employees/managers (WhatsApp/Slack) to resolve them, surfaces anomalies,
  tracks readiness per department, and prepares the export — HR supervises a dashboard instead of
  chasing people.
- **Who:** Payroll admins (their single biggest recurring pain).
- **Why AI now:** Agentic payroll is the emerging category (Warp, Central run payroll ops with
  agents; Gartner: 40% of enterprise apps embed task-specific agents by end-2026).
- **Moat vs DIY-IT:** The agent is only as good as the engine + data under it — ours.

### 8. Anomaly & Fraud Detective 🟢 ★★
- **What:** Pre-close scan of computed results vs. each employee's history and peer group: OT
  spikes, impossible punch sequences, buddy-punching patterns, geofence anomalies, systematic
  rounding abuse — each finding explained with evidence and a suggested action.
- **Who:** Payroll admins + HR.
- **Why AI now:** The single most universally shipped AI feature in the category — ADP, Dayforce,
  UKG, Oracle, Workday, SAP, Sage, Deel ("Payroll Detective"), Papaya and isolved all run pre-close
  anomaly detection (typical claims: 30–40% fewer errors, 25–50% faster processing). Table stakes
  to not lose — and our calc-aware version can explain *why* something is anomalous, not just that
  it is. Notably, no Brazilian T&A vendor ships this yet.
- **Moat vs DIY-IT:** Modest alone; compounds with #6 and #7.

### 9. Timesheet Auto-Repair 🟢 ★★
- **What:** Missing/duplicate punch inference with confidence and evidence ("she badged the
  building at 07:58, schedule starts 08:00 → propose 08:00 in-punch"), one-click approval, optional
  auto-fix below a confidence threshold with full audit marking.
- **Who:** Managers + payroll admins.
- **Why AI now:** Highest-volume manual correction in any T&A product; pure quick win. Deputy has
  AI Timesheet Approval in beta (auto-approve on rules, flag exceptions) — the direction is
  validated, nobody has it GA with evidence-backed inference.
- **Moat vs DIY-IT:** Low alone, but it feeds the audit trail correctly — DIY fixes in spreadsheets
  don't.

### 10. Labor-Claim Defense Pack 🟡 ★★★
- **What:** One click on an employee + date range → a court-ready evidence dossier: punch records,
  computed results with full derivations (#6), the policy versions in force each day, tolerance
  and rest-rule compliance, exceptions and who approved them. Brazil first (reclamatórias
  trabalhistas are overwhelmingly about hours), then global.
- **Who:** HR + legal.
- **Why AI now:** Assembling this manually takes days per claim; the narrative layer is LLM work
  on data only we hold in verified form.
- **Moat vs DIY-IT:** The "system of consequence" argument made tangible: the platform that
  generates your legal defense is the platform you don't churn from — and never DIY.

### 11. Audit Simulator 🟡 ★★
- **What:** "Inspect me like a labor auditor": run a mock fiscalização across the tenant —
  rest-period violations, OT-limit breaches, hours-bank expiry exposure, missing records — findings
  ranked by legal exposure, before the real inspector arrives.
- **Who:** HR + compliance officers.
- **Why AI now:** The checks are engine queries; AI contributes the auditor's playbook per
  jurisdiction and the readable report.
- **Moat vs DIY-IT:** Same family as #10 — compliance-proof generation.

### 12. Overtime Cost Forecaster 🟡 ★★
- **What:** Mid-period projection of period-end OT cost and hours-bank liability per team, with
  drivers ("logistics is trending 18% over — driven by 6 people covering the open weekend shifts")
  and suggested schedule mitigations before the money is spent.
- **Who:** HR + operations managers + finance.
- **Why AI now:** WFM vendors claim 15–30% OT-cost reduction from AI scheduling; forecasting is the
  first honest step and we have every input.
- **Moat vs DIY-IT:** Needs the live calc engine to project accurately.

### 13. Hours-Bank Advisor 🟢 ★★
- **What:** Watches every hours bank (banco de horas cycles, comp-time lots): predicts expiries,
  recommends compensate-vs-payout per employee ("force these 12 people's rest days this month or
  pay R$34k at cycle end"), and drafts the schedule changes.
- **Who:** HR + payroll admins.
- **Why AI now:** Cyclical banked hours are already deep engine logic (`cyclical-banked-hours.md`);
  the advisor layer is projection + recommendation. Also covers statutory expiry rules (cf. the
  Swiss 5-year time-bank workbench run).
- **Moat vs DIY-IT:** Banked-hours math is exactly the edge-case swamp DIY drowns in.

## C. Scheduling & workforce (the biggest adjacent land-grab)

### 14. AI Schedule Builder 🔴 ★★★
- **What:** Demand-forecast-driven auto-rostering (sales history, foot traffic, weather, events,
  predicted absences) that is *compliance-native*: rest rules, interjornada, minor restrictions,
  CCT constraints, and employee preferences are hard constraints, not afterthoughts. Manager edits;
  AI explains every trade-off.
- **Who:** Operations managers + HR; employees get fairer schedules.
- **Why AI now:** The defining WFM battleground (Legion, Quinyx, UKG Bryte; AI-scheduling market
  ~$3.2B→$9.5B by 2030; 47% of large US retailers already use it somewhere). We differ by putting
  the *calculation engine* inside the loop — a schedule is priced (OT cost) and compliance-checked
  as it's built.
- **Moat vs DIY-IT:** Compliance-priced scheduling requires the engine; generic schedulers don't
  have it.

### 15. Shift-Fill Agent 🟡 ★★★
- **What:** A no-show or open shift triggers an agent that ranks qualified, *compliant* candidates
  (rest rules, OT cost, skills, fairness rotation), messages them on WhatsApp, negotiates
  acceptance, and updates the schedule — minutes instead of a manager's morning on the phone.
- **Who:** Frontline managers; employees get first-come access to extra hours.
- **Why AI now:** Sira (YC) is built on exactly this ("agents call workers to fill shifts");
  Legion reports 40% of managers still text/call manually.
- **Moat vs DIY-IT:** The compliance-and-cost ranking is engine work; the agent is the face.

### 16. Shift-Swap Marketplace 🟡 ★★
- **What:** Employees propose swaps in chat; AI validates both sides (rest, OT, skills,
  CCT limits) instantly, auto-approves safe swaps per policy, routes edge cases to the manager with
  a recommendation.
- **Who:** Employees + managers.
- **Why AI now:** Standard in modern WFM but almost never compliance-validated in real time.
- **Moat vs DIY-IT:** Same engine-in-the-loop story.

### 17. Fatigue & Burnout Sentinel 🟡 ★★
- **What:** Continuous per-employee risk scoring from sustained OT, shrinking rest gaps, night-share
  creep, and missed breaks; proactive alerts with concrete fixes ("Maria has worked 11 nights in 14
  days — swap her Thursday with João, both compliant"). Duty-of-care report for regulators/insurers.
- **Who:** HR + operations; employees benefit directly.
- **Why AI now:** Fatigue rules are statutory in several target jurisdictions; wellbeing analytics
  is a rising demand (and a genuinely good use of data we already hold). UKG shipped "Meals &
  Breaks AI" (real-time missed/short-break monitoring with corrective action) in 2025 — the
  compliance half; the predictive fatigue half is still open.
- **Moat vs DIY-IT:** Needs the full punch + schedule + rule history only we have per tenant.

### 18. Workforce What-If Planner 🔴 ★★
- **What:** Strategic scenarios on real data: "open a site in Mexico with 40 staff", "move the
  plant to 12x36", "absorb the new CCT" → projected labor cost, required headcount, compliance
  deltas, transition plan. The globalization research (`worldwide-calculations/`) becomes a
  customer-facing advisor.
- **Who:** HR leadership + finance + expansion teams.
- **Why AI now:** Deloitte-class "autonomous workforce planning" is arriving; ours is grounded in
  an engine that actually prices the scenario.
- **Moat vs DIY-IT:** Cross-jurisdiction statutory knowledge + engine simulation — the two things
  hardest to DIY.

## D. Employee-facing (deflect the work before it reaches HR)

### 19. Employee WhatsApp Assistant 🟡 ★★★
- **What:** The employee's HR interface *inside WhatsApp* (or Slack/Teams): "when's my shift?",
  "how many hours in my bank?", "why was my OT only 30%?" (powered by #6), "I forgot to punch out"
  (feeds #9), punch-by-chat where legally valid. Multilingual by default.
- **Who:** Deskless employees (80% of the global workforce); HR gets its inbox back.
- **Why AI now:** Frontline workers check WhatsApp 50+×/day — the channel is the app. Deel already
  ships WhatsApp HR tasks; XOR/Paradox proved chat-native frontline HR at scale; Workday just
  announced a Frontline Agent (SMS-based time tracking/scheduling/absence, Spring 2026) — the
  giants agree the channel-native frontline interface is the next battleground.
- **Moat vs DIY-IT:** Every answer is grounded in the employee's real computed data — an internal
  bot without the engine gives wrong answers, and wrong answers about pay are radioactive.

### 20. Conversational Time-Off 🟢 ★★
- **What:** "I need Friday off" in chat → AI checks balance, team coverage, blackout rules and CCT
  terms, files the request, and hands the manager an approve/deny recommendation with reasoning.
- **Who:** Employees + managers; HR stops brokering.
- **Why AI now:** Time-off requests already flow through the pipeline (Expected-shift inputs); this
  is a thin, high-visibility layer. Paycom's GONE (automated time-off decisioning vs.
  coverage/policy) is GA and Deel ships a "PTO Fairy" coverage-gap agent — validated demand.
- **Moat vs DIY-IT:** Low alone; belongs to the assistant bundle (#19).

### 21. Onboarding Concierge 🟢 ★
- **What:** A new hire's first-week guide in chat: how to punch, their schedule, their policy in
  plain words, who to ask — personalized, multilingual, zero HR effort.
- **Who:** New employees + HR.
- **Why AI now:** Pure RAG over data already in the tenant; days of effort, immediate warmth.
- **Moat vs DIY-IT:** None — it's a delight feature that raises daily-active usage of the platform.

## E. HR beyond T&A (the "full HR life" expansion)

### 22. HR Inbox Copilot 🟡 ★★
- **What:** Connect HR's shared inbox/ticket queue; AI triages, answers the recurring 70%
  (grounded in company policy + the employee's actual data), drafts the rest for review. Leena AI
  claims 70%+ auto-resolution of HR tickets — but ours knows the hours data.
- **Who:** HR teams.
- **Why AI now:** Proven category (Leena, Borderless "Alberni"); our differentiation is the data.
- **Moat vs DIY-IT:** Medium — the T&A-grounded answers are the differentiated slice.

### 23. HR Document Generator 🟢 ★★
- **What:** Jurisdiction-aware HR documents auto-filled with real data: a lateness warning with the
  actual punch history attached, employment verification letters, schedule-change notices, contract
  amendments — drafted, formatted, logged.
- **Who:** HR.
- **Why AI now:** Borderless generates compliant employment agreements in minutes across
  jurisdictions; documents grounded in *our* records write themselves.
- **Moat vs DIY-IT:** The evidence attachment (real punch/calc data) is what generic tools can't do.

### 24. Living Handbook Q&A 🟢 ★★
- **What:** Company policies + applicable CCT/statutes compiled into an always-current handbook
  with a Q&A interface for HR and employees ("can I refuse a Sunday shift?" answered per *this*
  company + *this* CCT + *this* jurisdiction).
- **Who:** HR + employees.
- **Why AI now:** RAG over documents we already require for configuration (and #2 ingests).
- **Moat vs DIY-IT:** Grows from the same CCT-ingestion asset as #2 — shared investment.

### 25. Attrition Early-Warning 🟡 ★★★
- **What:** Retention risk signals from behavioral T&A data — lateness creep, absence drift,
  shift-swap spikes, sustained OT then sudden decline — cohort risk scores with explainable drivers
  and suggested interventions, never individual surveillance framing.
- **Who:** HR leadership + line managers.
- **Why AI now:** IBM-class results (95% flight-risk accuracy, ~30% turnover cut) required
  behavioral data most HR suites don't have. **We hold the substrate**: punches are the highest
  frequency behavioral signal in any HR stack.
- **Moat vs DIY-IT:** Data-exhaust play — this is the "outrun" lens: nobody else has this signal
  density, including the customer's IT (they'd have to get the data from us anyway).

### 26. Contract-to-Record Ingestion 🟢 ★
- **What:** Parse an employment contract/offer PDF → pre-filled employee record, correct policy and
  schedule assignment, flagged special terms (a personal OT arrangement → an exception in the
  policy's Employees + Exceptions tab).
- **Who:** HR ops.
- **Why AI now:** Document extraction is commodity; the mapping onto our config model is the value.
- **Moat vs DIY-IT:** Low; onboarding-friction reducer.

### 27. HR Workflow Agent Studio 🟡 ★★
- **What:** No-code automations over day.io events and data: probation-end reminders, contract
  renewal alerts, certification expiries, "manager hasn't approved timesheets in 3 days" nudges,
  birthday messages. Built as sanctioned agents with permissions and logs.
- **Who:** HR ops; *also the customer's IT* — this is a second judo surface.
- **Why AI now:** This is precisely what shadow-IT builds first (Retool: workflow automation is the
  #1 internally-rebuilt category, 35%) — so sell them the builder inside the governed platform.
- **Moat vs DIY-IT:** Converts the DIY impulse into platform lock-in.

## F. Platform & data plays (the strategic layer)

### 28. day.io MCP Server / Agent Platform 🟡 ★★★
- **What:** Expose the governed calc engine and tenant data as an agent-callable surface — a remote
  MCP server + APIs with OAuth, granular permissions, and full audit logging. The customer's
  Copilot/Claude/internal agents query hours, run simulations, file corrections — every call
  logged, every write policy-checked.
- **Who:** Customer IT departments and their AI programs; indirectly every persona above.
- **Why AI now:** The emerging consensus play ("the MCP server is the product; the dashboard is the
  audit log"), and HCM is already moving: isolved ships a Connector for Claude, Gusto and Deel run
  apps inside ChatGPT (MCP-based), Dayforce connects via Microsoft Copilot Studio + MCP, and
  Workday built an Agent Gateway (MCP + A2A) with agent-governance as a product. MCP-connected
  customers drive *more* API usage, not less.
- **Moat vs DIY-IT:** **The** judo move. The IT department that wanted to replace us becomes our
  highest-engagement integrator — and the engine stays ours.

### 29. Benchmark Insights 🟡 ★★
- **What:** Anonymized cross-customer benchmarks, AI-narrated: "your OT rate is 2.1× the sector
  median for retail in your region; the gap is concentrated in weekend coverage." Optionally a
  quarterly "workforce health report" per tenant.
- **Who:** HR leadership; also a marketing/sales asset.
- **Why AI now:** Only aggregatable by the platform — a classic network-effect data product. ADP
  already sells workforce benchmarks off its 1.1M-company dataset; nobody offers hours/OT-behavior
  benchmarks at T&A granularity.
- **Moat vs DIY-IT:** Impossible to DIY by construction (one company has no benchmark).

### 30. Embedded Earned-Wage Access 🔴 ★★
- **What:** Let employees access wages already earned — computed from *verified* hours, the thing
  we uniquely certify — via an embedded-finance partner (the Clair model), with AI advising the
  employee on safe amounts.
- **Who:** Employees (EWA adoption heading toward ~42% of businesses; raises take-home ~11%/mo for
  users); employers get a retention lever at no cost.
- **Why AI now/us:** EWA lives or dies on trustworthy earned-hours data — which is our core output.
  Deel already ships "Anytime Pay" for its EOR base. Partner-led, so the 🔴 is mostly
  compliance/fintech integration, not ML.
- **Moat vs DIY-IT:** Verified-hours certification is the asset; a new monetization line riding it.

---

## My take — where I'd start

If I had to pick five to champion:

1. **#6 WhyPay Copilot** — the cheapest item with strategic weight: it makes the moat (audit
   trail, explainability) *visible* to every user every day, and it's the foundation for #10, #19,
   and the union-driven explainability requirements coming to algorithmic workforce tools.
2. **#3 LawTrack AI — reader mode** — we already validated the classification manually on 72 real
   instruments; the manual-upload CBA/CCT reader attacks the single most painful onboarding step,
   ships before the change-monitoring layer, and feeds #24 and the globalization roadmap.
3. **#7 Payroll Close Copilot** — the highest-empathy feature for the payroll admin persona; turns
   the platform from a system they check into a colleague that chases.
4. **#19 Employee WhatsApp Assistant** — the biggest HR-life improvement per real-world usage;
   deskless workers live in WhatsApp, and every deflected question is HR time returned.
5. **#28 MCP Server / Agent Platform** — the strategic answer to the IT threat; cheap relative to
   its positioning value, and it compounds every other feature by making them agent-reachable.

And one challenge to the premise: the IT-department risk is real but the response should never be
defensive opacity — it's to make day.io the *most* buildable-on platform in the category while
keeping the one thing that can't be vibe-coded (the verified, always-current, audit-trailed
calculation engine) at the center of every feature above.

**A timing note on Brazil.** The competitor scan's clearest structural finding: the agentic wave
sweeping US/EU suites (pre-run anomaly detection, conversational hours reporting, payroll-close
agents, MCP connectors) is **essentially absent among Brazilian T&A vendors** — local AI is
concentrated in recruitment (Gupy), behavioral profiling (Sólides), and punch capture
(Ahgora/TOTVS facial recognition; day.io's own punch classification). Whoever brings the agentic
T&A feature set to Brazil first defines the local bar — and day.io's calc engine is exactly the
substrate it lands on. The quick-win column of the table above is that opening.

---

## Appendix — competitor landscape (2026-07 web scan)

### Ten cross-cutting patterns

1. **Named, role-based agents are the default framing** — UKG Bryte, Workday Illuminate, SAP Joule
   Agents, Oracle's 13+, Dayforce agents, isolved's six, Deel AI Workforce, Rippling's multi-agent
   architecture, Factorial One.
2. **Pre-run payroll anomaly detection is the most universally shipped feature** (ADP, Dayforce,
   UKG, Oracle, Workday, SAP, Sage, Deel, Papaya, isolved) — squarely in day.io's punches→payroll
   lane; consistent pitch "catch it before the close."
3. **Conversational NL reporting over people data is table stakes** — UKG, ADP, Personio, HiBob,
   Paylocity, Dayforce, Gusto, Factorial, Deputy, Legion.
4. **Employee self-service HR helpdesk assistants are near-ubiquitous** — UKG People Assist, SAP HR
   Service Agent, isolved Helper, Rankmi Genius Chat, Quinyx Ava, Deel AI, Paylocity, Buk.
5. **2025's shift: from Q&A to action** — assistants now execute approved actions with
   human-in-the-loop confirmation (Paylocity, Rippling, Gusto "Gus", Deputy, Deel).
6. **AI frontline scheduling with compliance guardrails is the WFM battleground** — Legion (96%
   forecast match, 300k+ models), Quinyx, Deputy, Connecteam, Sona, Planday, UKG Self-Scheduling,
   Workday Frontline Agent, Verint.
7. **Compliance-monitoring agents are emerging** — Deel Compliance Monitor, isolved Watchdog, ADP
   140+-country monitoring, UKG Meals & Breaks AI, Legion's predictive-scheduling-law automation.
8. **The MCP/connector surface is a distinct 2025–26 wave** — isolved Connector for Claude, Gusto
   & Deel apps in ChatGPT, Dayforce × Copilot Studio (MCP), Workday Agent Gateway (MCP + A2A).
9. **Agent governance is becoming its own product** — Workday's Agent System of Record + Flex
   Credits (consumption pricing), Dayforce AI Workspace (audit trails), isolved's "Workforce
   Capital Management" category.
10. **Brazil/LatAm lags with a different center of gravity** — recruitment AI (Gupy Gaia),
    behavioral profiling (Sólides Profiler), punch capture (Ahgora/TOTVS, Pontomais, day.io's own
    punch classification + anti-fraud), conversational helpdesks (Rankmi, Sesame, Buk). The
    agentic-payroll wave has not arrived — open field.

### Vendor highlights (condensed)

| Vendor | Most relevant shipped/announced AI |
| :-- | :-- |
| **UKG** (Bryte) | People Assist helpdesk (GA), conversational reporting, self-scheduling agent, **Meals & Breaks AI**, touchless-payroll anomaly agent (EA), workforce-planning scenarios |
| **ADP** (Assist/Lyric) | Payroll anomaly detection + resolution (GA), NL reporting, 140+-country compliance monitoring, benchmarks off 1.1M companies |
| **Workday** (Illuminate) | Payroll Agent (GA FY26), **Frontline Agent** — SMS time/scheduling/absence (Spring 2026), Agent Gateway (MCP+A2A) + agent-governance + consumption pricing |
| **Dayforce** | Autonomous Pay anomaly resolution (GA), **Pay Clarity Agent** (employee pay explanations, GA), AI Workspace governance |
| **SAP / Oracle** | Joule payroll/HR-service agents rolling 2026; Oracle Pay Analyst + Payroll Run Analyst (explains pay-run anomalies) |
| **Rippling** | Multi-agent architecture across HR/payroll/IT/finance; prompt-driven payroll execution across 185+ countries |
| **Deel** | AI assistant on 150-country compliance KB (GA), Payroll Detective / PTO Fairy / Border Buddy (beta), Compliance Monitor (GA), Anytime Pay EWA, ChatGPT app (MCP) |
| **Gusto / Paycom / Paylocity** | Gus question-to-action assistant + ChatGPT app; Paycom **Beti** (employee-driven payroll, −90% processing time) + **GONE** (auto time-off decisions); Paylocity questions→actions |
| **isolved** | Six autonomous agents incl. **Guardian** (payroll-run monitoring) + **Watchdog** (regulatory change); **Connector for Claude** |
| **Papaya Global** | Payroll data-validation agent (99.7% claimed, 160+ countries), anomaly detection, Cycle Manager agent |
| **Legion / Quinyx / Deputy** | Compliance-native AI scheduling (GA); Ava assistant; Deputy AI (shift-fill, timesheet approval — beta, 2026 rollout) |
| **Connecteam / Sona / Planday / When I Work** | AI auto-schedulers (GA), knowledge-base agents, Sona "Raffy", Planday×Xero payroll sync |
| **Sira** (YC) | AI-native deskless T&A+payroll: agents **call workers to fill shifts**, auto clock-in, flag missed punches — the closest AI-native threat to day.io's lane |
| **Brazil/LatAm** | Gupy Gaia (recruiting), Sólides Profiler (+ Pontomais), Ahgora/TOTVS Consultor Digital + facial-recognition ponto, Rankmi WhatsApp agent, Buk AI, Sesame AI — **no agentic payroll/anomaly wave yet** |

*Caveats: vendor metrics are marketing claims, not independently verified; some items are
announced/beta (flagged inline). Strategy sources: Retool Build-vs-Buy 2026, Bain, Vendep
("system of consequence"), Symmetry (deterministic engine under agents), Josh Bersin's HR-agent
landscape.*
