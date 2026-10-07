# Pay Policy — configuration reference (current state)

> **On-demand · single home.** The one document for **how a day.io pay policy is configured and what
> it contains TODAY** — every setting in the current product, at full spec. Derived from the live
> product UI captured **2026-07-08** (`pay-policy-screens/`) + the `List Business Rules Groups` API
> shape (§15), and cross-checked against `flow/configuration.md`, `flow/calculation-flow.md`,
> `flow/payroll-event-types.md`, `flow/cyclical-banked-hours.md`, `data-model/fields.md`,
> `data-model/enums.md`.
>
> **This is the current-state reference.** The main body (§1–§9, §15) describes what the product does
> **today**. Settings that are **designed/needed but not in today's UI** are kept out of the way in
> **§10 (target/future)** and tagged **`T`** inline, so they inform without framing the picture.
>
> **Supersedes** the pay-policy prose that used to live in `flow/configuration.md` §3 (merged here per
> Assaf, 2026-07-10). `flow/configuration.md` remains the **binding-level map of all configuration**
> (where the pay policy sits in the stack — §2.5) and the **target-flow** framing; the full pay-policy
> detail is **here**. Templates/versioning/governance are a **separate, future feature** —
> `Modular-calculation/requirements/pay-policy-templates-prd.md`, deliberately **not** in this
> current-state doc.

## Legend

**Status tag**

| Tag | Meaning |
| :-- | :-- |
| **`C`** | **Current** — configurable in the product UI today (confirmed from the 2026-07-08 screens). |
| **`T`** | **Target** — designed / needed for the worldwide flow; **not** in today's UI (see §10). |
| **`BR?`** | Brazil/CLT-specific; **presence in the UI unconfirmed** (Assaf unsure — do not assert). |
| **`?`** | A detail still to confirm. |

**Full-spec columns** — each entry carries: what you set (**Setting**) · its **Control & values** ·
**Default** · **What it does → payroll event(s)** (the calc effect + the event it produces) · **Tag**.

> - **Default** = the value shown in the 2026-07-08 *sample* policy ("Policy Learning"); indicative, may
>   be a system default or a prior config, not asserted as *the* default. `—` = unknown.
> - **Payroll events** are drawn from `flow/payroll-event-types.md` — ⚠ that catalog is labelled
>   **"legacy / no-longer-maintained"** by the reports-integration PRD, so treat event names as
>   indicative of *shape*, not a maintained contract.
> - **What it does** is sourced from `flow/calculation-flow.md` (pay-policy lens §4.2, threshold
>   precedence / premium composition §4.3, per-step mechanics §3.3–3.6).

---

## 1. The object at a glance

A pay policy is the **compensation bundle** assigned to employees — it defines **how a company
compensates its employees** (the configuration layer for time & attendance rules). It has **six tabs**:

**Paid Overtime · Hours Distribution · Tolerance · On Call · Special Rules · Employees**

> ⚠ **Tab-count note:** several context docs still say "five tabs" (`Modular-calculation/day-io-today.md`,
> the pay-policy-template requirement, `cba-ingestion-tool.md`, and the old `configuration.md` §3.2) —
> that predates **Special Rules**. The UI has **six**. Flagged for a later `dvartorah` sweep.

Alongside the Pay Policies list sits a separate **Exceptions** area (§9) — *not* a pay-policy tab.

**Lifecycle & list behaviour** `C`:

- **Assignment & locking.** The **default** policy auto-assigns to every new employee at creation
  (shown "(Default)" + 🔒). Once employees are assigned, the policy is **locked for editing** (🔒 in
  the list) → **reassign, don't edit**. Editing in place would create retroactive ambiguity (was an
  hour earned at 1.5× or 1.75×?) and Day.io does **not** version policies; the correct path is to
  **create a new policy and reassign** — a clean record of when the change took effect.
- **Deactivation, not deletion.** Policies can be **deactivated** (Active / Inactive) but **not
  deleted** — customers may still need to reference past configuration. Inactive policies are retained
  for reference, not assignable. *Open:* when deactivated, do assigned employees become unassigned or
  move to the default policy?
- **Jurisdiction / CBA.** Compensation differences driven by union (CBA) or state/province are carried
  by **a pay policy built for that arrangement** — one arrangement per policy, **not** jurisdiction
  conditionals inside one policy. The mapping is **not 1:1**: many policies can share the same
  jurisdiction + CBA (super-configurability). Jurisdiction/CBA **seeds and informs** setup and
  **supplies statutory rules**; it does **not** select the policy (`flow/configuration.md` §1).
- **No separate "business rules."** Every setting governing *how an employee is paid* lives in the pay
  policy; there is **no separate "business rules" object** in the target flow (a historical engine
  container). Engine settings carried under `SourceShift.businessRules.*` are pay-policy settings,
  re-homed by tab — except `alignWorkingHoursBasedOnExitPunch`, a worked-time **measurement** rule
  that belongs at **Reconcile**, not here. Nothing at shift or employee level overrides the policy
  (⚠ the locking + no-override model is unresolved — finding #22).
- **Reports naming.** Exported reports still label the assigned pay policy the **"Business Rules
  Group"** (legacy naming; the target flow eliminates the "business rules" category — finding #22).

> Screens: `pay-policy-screens/` — `03` (Paid Overtime, bank on) · `04` (rates+limits) · `05` (Hours
> Distribution) · `06` (Tolerance) · `07` (On Call) · `08` (Special Rules) · `09`/`10` (Exceptions).
> `01` (pay-policies list) + `02` (Paid Overtime, bank off) pending re-capture.
>
> **Where it sits in the binding stack:** the pay policy is one level of the configuration stack
> (jurisdiction → company → payroll group → planning space → **pay policy** → schedule → shift →
> employee → date). The stack + the pay policy's flow-coverage registry live in
> `flow/configuration.md` §1/§2.5.

---

## 2. Policy-level (header + list)

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Policy name | text | — | Identity in the Pay Policies list. | `C` |
| Start date | date | — | The **policy's** start date; also anchors the banked-hours cycle when the bank is on. Selects which policy version applies from that date. (API: `businessRules.startDate` — rules are effective-dated.) | `C` |
| Status | Active / Inactive | Active | Inactive policies are retained for reference, not assignable. | `C` |
| Default policy | flag (auto) | — | Auto-assigned to every new employee at creation; shown "(Default)" + 🔒. | `C` |
| External ID (for integration) | checkbox → id | off | Exposes an external identifier for integrations; no calc effect. Appears at the bottom of the Paid Overtime tab. | `C` |
| Entity scope (country / state / CBA / company) | — | — | The compensation arrangement the policy is built for; seeds statutory defaults. Not a visible control today. | `T` |

---

## 3. Tab 1 — Paid Overtime

> **What this tab is.** How overtime is compensated — rates, hours bank, calculation method. **OT is
> the surplus of actual worked time above the planned shift** (planned hours come from the schedule).
> *Confirmed: there is **no** regular-hours-target control in the pay policy today* —
> `regularHoursDuration` is a target concept (`T`, §10), not a UI control.

### 3.1 Banked Hours activation — the fundamental toggle

Whether the hours bank is activated is a **fundamental** pay-policy choice:

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Activate Banked Hours | toggle | off | **Off** → overtime pays as **Extra Hours (EH)** — cash on the next payroll run. **On** → overtime *can* accrue as **Banked Hours (BH)** — a time-credit taken later as PTO or paid at cycle end. Gates the whole §3.2 block. → *Extra Hours* vs *Banked Hours* families. | `C` |

> **EH and BH are not "mutually exclusive per policy."** The exclusivity is **per OT bucket**: a given
> overtime minute is *either* cashed (EH) *or* banked (BH). But a **BH-enabled policy produces both** —
> each row of the rates table (§3.4) sets a **BH↔EH split %**, so you can route everything to the bank,
> split per row, or still give specific rows as EH. Activating the bank doesn't force all OT into it.
> _(per Assaf, 2026-06-17 — corrects an earlier "mutually exclusive per policy" framing; calc §4.2 E3.)_

### 3.2 Banked Hours cycle *(shown when activated)*
| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Start date | date (= policy start, §2) | — | Anchors the cycle. | `C` |
| Choose the first due date | checkbox → date | off | Aligns the cycle to a payroll period rather than the calendar month. | `C` |
| Duration | dropdown, **1–18 months** | 2 Months | Cycle length; **Next End Date** = start + duration (shown, computed). | `C` |
| Reset hours bank cyclically | checkbox | off | Carry balances across cycles within a retention window (see `cyclical-banked-hours.md`) vs a single reset. | `C` |
| Cycles before reset | integer **N** *(cyclical only)* | — | Past cycles retained before the oldest expires. ⚠ UI counts one extra — enter **N−1** for N cycles. | `C` |
| Hide the Banked Hours summary from the employee's app | checkbox | off | Visibility only; no calc effect. | `C` |
| Missing Days | dropdown: **Reduce hours from the bank and set as a missing day** / **Set as a missing day without reducing the bank** / **Reduce hours from the bank only** | Reduce+set | What a missing day does to the balance — always does ≥1 of dock / mark. → *Total Missing Days*, *Missed days in hours*. | `C` |
| Banked Hours payment — **Positive bank** (at cycle close) | **Do nothing (keep as expired)** / Convert to Extra Hours (with multiplier) / Convert original hours to Extra Hours (before multiplication) | Do nothing | Disposition of a positive balance at expiry. → *Extra Hours Rates – End of Bank*, *Total extra hours from the end of the bank*. ⚠ calc-flow §3.4/§4.3 compresses this to "EH **with a multiplier**"; the three UI labels are canonical here. | `C` |
| Banked Hours payment — **Negative bank** (at cycle close) | **Do nothing (keep as expired)** / Convert to missing hours | Do nothing | Disposition of a negative balance. → *Missing hours from converted negative bank*. ⚠ calc-flow §4.3 frames negative as "carry-forward (cyclical) / configurable" — reconcile vocabulary. | `C` |

> **Cyclical vs non-cyclical expiry differ.** The per-sign expiry actions above are the **non-cyclical**
> options. In **cyclical** BH the disposition is **fixed** (positive → EH with multiplier; negative →
> carry forward) — not configurable. Full ledger mechanics: `cyclical-banked-hours.md`.

### 3.3 Extra hours settings (overtime onset)

> **OT onset baseline** — OT is the **surplus of actual worked time above the planned shift**.
> *Confirmed: no regular-hours-target control in the pay policy today* (§10, `regularHoursDuration`).
>
> **⚠ Weekly overtime — now in delivery (per Assaf, 2026-07-18).** A **weekly OT trigger** (OT on hours
> beyond a weekly threshold, accumulated over a configurable week window) is being **built as a
> first-class capability** — moving the daily/weekly statutory threshold from §10 (`T`, target) toward
> current. Treat weekly OT as **supported** for planning/compliance answers. **Status caveat:** it is
> **committed-in-delivery**, not yet observed in the 2026-07-08 UI screens or the 2024 API payload (§15) —
> so this is product-owner confirmation, not `C`-in-UI evidence. Track ship status.

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Consider only early arrivals and late leaves as overtime (regardless of total worked hours) | checkbox | off | **Checked** → OT is only the spill **outside** planned boundaries, pinned to the early-in / late-out moment; a boundary **shortfall becomes a debit** (not netted). **Unchecked** → total surplus above planned floats to the tail. (calc §3.4 option #1 / §4.2 E2). → *Total Debit Hours* when checked. | `C` |
| ↳ Include breaks in the calculation | checkbox | off | **Modifies the above** — includes breaks when applying the early/late-only rule. ⚠ **no counterpart in calc-flow** (finding #25). | `C` `?` |
| On non-planned days, start calculating overtime after X hours | checkbox + X hours | off | On non-planned days, hours up to X are regular; only the surplus is OT (off → all hours OT). → *Not planned work days 100%* bucket; *Non-planned hours* (Hours Distribution). | `C` |
| Split days by | **Split by calendar days** / **Split by shifts** | Split by shifts | Only matters when OT crosses midnight. Calendar → after-midnight portion takes the **next day's** rate; shifts → whole shift takes the **start-date** rate. (calc §3.4 option #3 / §4.2 E2). | `C` |

> *Worked example (early/late-only, checked vs unchecked):* planned 09:00–18:00, actual 10:00–19:00
> (9h). **Unchecked** → 0 OT (late in/out cancel). **Checked** → 1h debit (late arrival) + 1h OT (late
> departure), not netted. On cross-midnight shifts this changes which calendar day (and rate) the OT
> lands on.

### 3.4 Rates

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Split rates by | **Specific days** / **Planned & Non-planned days** | Specific days | Selects the OT-rate-window basis; **drives the Days-column options** below (calc §4.3 "OT rate window?"). When splitting **planned vs non-planned**, the rate is driven by the shift's working-day flag (`SourceShift.working` / `nonWorkingDayShift`); when splitting by **specific days**, the table must cover all windows with no gaps. | `C` |
| Calculate compensation rates by | **Percentage (%)** / **Multipliers (×)** | Percentage | *Crediting/labeling* axis: 2h @ 1.5× = 3h credited; 2h @ 50% = 2h credited labeled 150%. ⚠ **Not** the premium-**composition** mode (additive/multiplicative/winner-take-all, calc §4.3) — different axes. | `C` |

**The rates table** — one or more rows (**New row** to add). Each row:

| Column | What it holds | Notes |
| :-- | :-- | :-- |
| **Days** | day-group the rate applies to | options depend on *Split rates by* — see the two lists below | `C` |
| **Day/night split** (per-row ☀/🌙 button) | splits the row into a **Day** rate and a **Night** rate | night boundary from the Hours Distribution night window (§4); off = combined (no split, phase type `combined`). Night here **composes** onto the OT state (calc §4.3). | `C` |
| **Pay rate** | a **%** or **×** value (per *Calculate rates by*) | → *Extra Hours Phases* / *Extra Hours Rates – Worked Hours* (Standard-10 rate buckets) | `C` |
| **BH↔EH split** (per-rate option) | what portion of *this rate's* overtime goes to **Extra Hours** vs **Banked Hours** | only meaningful when the bank is on; a BH-enabled policy produces **both** (per-bucket exclusivity, calc §4.2 E3). → *Banked Hours Phases* (4 rates) + *Banked Hours* balances | `C` |
| **Name** | the payroll-event name for this rate (editable) | this **is** the rate's payroll-event label (calc §3.6; event-types "labels come from the pay policy") | `C` |
| **Limit** ("Add Limit") | the rate applies **up to N hours**, then **switches to the next rate** | rate-chaining by hours worked (e.g. 50% for the first 2:00, then 60%); multiple limits stack per row | `C` |

**Days options** — depend on *Split rates by*:

- **Specific days:** Monday–Friday · Monday–Saturday · Sunday–Thursday · All days · Holidays ·
  Friday–Saturday · Saturday · Sunday & Holidays · Monday · Tuesday · Wednesday · Thursday · Friday ·
  Saturday · Sunday · DSR & Rest days.
- **Planned & Non-planned days:** Planned work days · Not planned work days · DSR & Rest days.

> **Day/night split is opt-in — default is NO split.** By default the platform does **not** split a
> shift's hours into day vs. night. The split exists only when configured — via this tab (day/night
> rate rows) or the Hours Distribution night window (§4). An OT phase typed `combined` is the no-split
> mode. Night hours from Hours Distribution already carry a base premium; the rates here **compound**
> on top. _(per Assaf.)_

### 3.5 Limits section — overall period cap
A limits section **below** the rates table sets an **overall cap on total overtime / banked hours over a
period** (e.g. max 40h OT per month) — **independent** of the per-row `Add Limit` (which chains one rate
into the next after N hours). Label follows the bank toggle:

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Extra hours limits ("New extra hours limit") *(bank off)* | one or more overall caps, each over a period | — | Caps total extra hours; overflow handling per the limit rule. → *Extra Hours Rates – Over Limit*. | `C` |
| Hours Bank Limits and Payment ("New hours bank limit") *(bank on)* | overall banked-hours caps over a period | — | Caps the bank; over-limit converts to EH. → *Missing hours from crossing negative bank limit* / *Extra Hours Rates – Over Limit*. | `C` |
| ↳ Create custom hours bank rate for limit rules | checkbox | off | Attach a custom hours-bank rate to the limit rules. | `C` |

> **Hours-bank limits, in full.** A bank limit is defined by **scope** (period bank vs accumulated
> bank; optionally restricted to a specific rate), **cap** (positive / negative configured
> independently), **period** (weekly / monthly / yearly / custom — custom can trigger immediately on
> cap-crossing rather than at period end), and **conversion target** (the action at cap: convert to EH
> / convert at EH rate / convert to a customer-defined HB rate %). *(See `cyclical-banked-hours.md`.)*

### 3.6 Notifications and alerts
| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Banked Hours limit alert + Period | time (e.g. 05:00) + Weekly/… | 05:00 · Weekly | Supervisor alert when the bank balance crosses the threshold. **Alert only — no hours effect.** | `C` |
| Extra Hours defined limit + Period | time (e.g. 04:00) + Daily/… | 04:00 · Daily | "Supervisors notified when an employee exceeds the set hours." **Alert only.** | `C` |

### 3.7 Other
| Setting | Control & values | Default | What it does | Tag |
| :-- | :-- | :-- | :-- | :-- |
| External ID (for integration) | checkbox → id | off | Integration identifier for the policy; no calc effect. (`externalId`, nullable) | `C` |

### 3.8 Cross-shift interval *(confirmed in the API payload; UI tab not identified in the 2026 screens)*
| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Inter-shift interval | minutes (`crossShiftsInterval.interval`); **660 = 11h** | 11h | Minimum rest between one shift's end and the next shift's start; below it the next shift may be reshaped/flagged (finding #17). → *Cross Shifts* events (*Cross Shifts Interval*, *Total Cross Shifts Hours*). | `C` `?` |
| Interval phases | `crossShiftsInterval.phases[]` `{name, limit (-1=∞)}` | `unlimited` | How hours are classified when the interval is violated. | `C` `?` |

---

## 4. Tab 2 — Hours Distribution

> **What this tab is.** Night-shift properties + **labeling specific hours** for payroll records. The
> distribution rules (§4.2) classify worked time into reporting buckets — a *monitoring/labeling*
> surface, **not** an hours driver.

### 4.1 Night Shift
| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Activate Night shift | checkbox | on (sample) | Enables the night premium band. Default is **no split** unless configured (calc §3.2). | `C` |
| Start time / End Time | times | 22:00 / 05:00 | The night window. | `C` |
| Percentage % | number | 20 | Night premium on in-window worked hours, **independent of surplus**. → *Night Shift* family (*Night Shift (hours)*, *Night shift 20%*, …); *Weekdays night-hours* (Hours Distribution). *(How the % interacts with the Multipliers-vs-Percentage choice, §3.4, is an open question.)* | `C` |
| "Schedules started inside the above period must be considered entirely as night shift" | checkbox | on (sample) | A shift that *starts* in the window is paid **entirely** as night (`nightShiftExtendToFullRange`, calc §3.2). Brazil confirmed; general-case field open. | `C` |

### 4.2 Hours distribution rules
One or more rows (**New rule**). Labeling / monitoring — classifies worked time into reporting buckets;
not an hours driver.

| Column | What it holds | Notes | Tag |
| :-- | :-- | :-- | :-- |
| Period | day-group | **same option list as the Paid Overtime *Days* column (§3.4)** | `C` |
| Hours type | **Planned hours** / **Non-planned hours** | ⚠ `enums.md` also lists `every_hour` — possible third value | `C` `?` |
| Range | start–end time | the time window to bucket | `C` |
| Name | payroll-event name | | `C` |
| Include in calculations | multi-select: **Breaks · Overtime · Extended hours** | what counts into the bucket | `C` |

→ *Hours Distribution* events: *Weekdays 8-18*, *Weekdays night-hours*, *Saturday*, *Sunday*, *Non-planned hours*.

### 4.3 Brazil-adjacent night/DSR settings *(not seen in the 2026 screens)*
| Setting | What it does | Tag |
| :-- | :-- | :-- |
| Add non-working breaks to night duration | adds non-working break time to night-shift duration for the premium (`addNonWorkingBreaksToNightShift`) | `BR?` |
| Night reduced hours (duration compression) | a night hour pays 60′ though ~52½′ elapse (`hora noturna reduzida`, finding #19); **compresses worked-time duration before Reconcile/OT onset** — distinct from sleep time (a paid-but-non-OT category, §10) and from the night premium (a *rate*) | `BR?` |
| DSR report labeling; DSR hours-accounting | show DSR days in reports (`showDsrInReports`); count DSR in hours (`countDsrInHours`); DSR-day duration (`dsrDayDuration`) | `BR?` |
| DSR missing-minutes discount | dock DSR when worked minutes fall short, up to a limit — `discountDsrForMissingMinutes {limit: 30 min, active}`. **Confirmed in the API payload** (§15), so no longer scan-only. | `BR` |

---

## 5. Tab 3 — Tolerance

Tolerance allows **minor deviations** from scheduled times without triggering penalties.

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Deactivate Tolerance | toggle | tolerance on | Turns tolerance on/off for the policy. | `C` |
| Tolerance limit | single duration (e.g. 10m) | 10m (sample) | Deviation forgiven before it becomes missing/OT; if it **exceeds** the limit the **entire** deviation counts (all-or-nothing, calc §3.3). | `C` |
| Period | **Per Punch** / **Per Day** | Per Punch | Per Punch = each event independently; Per Day = deviations summed with end-of-day netting (a late arrival can offset a late departure — "negative tolerance"). | `C` |
| Consider the Break registers too | checkbox | off | Extends tolerance scope to break punches. | `C` |
| Consider early Entry and late Exit too | checkbox | off | Extends scope beyond the default (late arrivals / early departures) to early arrivals / late departures. | `C` |

→ affects *Late Arrivals* (*Total Late Arrivals*, *Total late entry hours*, *Late Arrivals w/o Breaks*)
and *Early Leaves* (*Total early leaves*, *Total early leave hours*, *Early Leaves w/o Breaks*).

> *Worked example (all-or-nothing):* tolerance 5 min → arrival 08:04 → the 4 min is ignored; arrival
> 08:07 → all 7 min deducted (the whole deviation, not just the excess). *Per-day netting:* a late
> arrival can be offset by working past a planned break start or planned exit — the closest thing to
> "negative tolerance."

> **Tolerance ≠ validity.** Validity (the acceptance window — how early/late a punch is accepted at all;
> outside → `invalid`) lives on the **schedule**, not here. The four separate `confines.*` tolerance
> thresholds (`data-model/fields.md`) are **schedule-level**, not this tab. Also distinct from the
> Paid-Overtime option "consider only early arrivals and late leaves as OT" (§3.3, which governs how
> *overtime* is determined). Two-tier validity↔tolerance model: `calculation-flow.md` §4.
>
> ⚠ **Data-layer note:** the API `tolerance` object is `{type, limit(min), scope(punch/day), active,
> includeBreaks}` — it has **no** "early Entry / late Exit" field. That 2026 checkbox is newer than the
> 2024 sample (§15).

---

## 6. Tab 4 — On Call

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Compensation | **No compensation** / **Follow pay policies** | Follow pay policies | Whether on-call time is compensated and how. Availability and activation are paid **separately** (calc §3.5). → *On Call*, *On Call Activation*, *Total On Call excluding activated hours*. | `C` |

---

## 7. Tab 5 — Special Rules

| Setting | Control & values | Default | What it does → payroll event | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Bonus hours | toggle + **Payroll event name** | off | Grant a set number of hours **per working day**; **the daily bonus amount is set on the employee profile.** ⚠ **No calc-flow mechanic and no dedicated payroll event** (finding #24); emits a custom-named event (closest catalog entry *Fixed hours*, uncertain). | `C` `?` |

> Currently the only Special Rule. This is the "escape valve" surface (cf. `SourceShift.specialRules`
> in `data-model/fields.md`, e.g. commute hours) — expect more rules here over time.
>
> ⚠ **Absent from the `List Business Rules Groups` payload** (2024 sample, §15) — Bonus hours is newer
> or stored outside `businessRules`, reinforcing flow-finding #24 (no clear calc home).

---

## 8. Tab 6 — Employees

| Setting | Control & values | Default | What it does | Tag |
| :-- | :-- | :-- | :-- | :-- |
| Assignment | which employees fall under this policy | — | The binding itself — selects the policy for those employees (→ all calc steps). Default policy auto-assigns; assignment **locks** the policy. Distinct from the payroll/business group. | `C` |

---

## 9. Exceptions *(sibling of Pay Policies — not a pay-policy tab)*

A tab beside "Pay Policies" listing **exceptions**: `NAME · DATE · EMPLOYEES · CREATED BY · STATUS`, with
**New exception**. An exception is a **date-range + employee override** that **always pays extra hours,
regardless of the assigned pay policy** (per the in-UI banner).

**Exception detail** — two tabs (Exception details · Employees):

| Setting | Control & values | What it does | Tag |
| :-- | :-- | :-- | :-- |
| Name | text | identity | `C` |
| Date | a date **range** | the days the exception covers | `C` |
| Rates table | same shape as §3.4 (Days · ☀/🌙 split · %/× rate · Name · Limit); Days include **DSR & Rest days** | the extra-hours rates for the covered days | `C` |
| Employees | which employees the exception applies to | binding | `C` |

> Exceptions have **no** Banked-Hours / Tolerance / On-Call / Special-Rules tabs — always Extra Hours.
>
> ⚠ **Naming collision:** a pay-policy **Exception** (here) is **distinct** from a **schedule exception**
> (`scheduleExceptionUuid` in `flow/calculation-flow.md` / `data-model/fields.md`) — the latter is a
> per-date *schedule* replacement, unrelated to compensation.

---

## 10. Target-design configurations *(not in today's UI — `T`)*

> **Not current state.** These belong in the pay policy in the **worldwide flow** (compensation routes
> through the policy — `flow/configuration.md` §1/§2.5, finding F-B) but are **not** configurable in
> the product today. Kept here so the design intent is visible without cluttering the current-state
> body. Sources in §12.

| Configuration | Note |
| :-- | :-- |
| Regular-hours target (`regularHoursDuration`) | explicit **daily regular-hours target** — hours up to it are regular, surplus is OT. Overlaps the statutory thresholds below; today OT onset is surplus-above-planned (no such control). |
| Statutory OT thresholds (daily / weekly) + daily double-time | jurisdiction-seeded; cascade country → state → CBA (calc §4.3). **⚠ The weekly OT trigger is now in delivery (per Assaf, 2026-07-18) — see §3.3; treat weekly OT as supported.** Daily thresholds + daily double-time remain target. |
| Premium composition mode | additive / multiplicative / winner-take-all for stacked premiums (calc §4.3; finding #2) |
| Additive vs multiplicative rate application | first-class rate-application axis (distinct from %/× and from composition mode) |
| Rate-base composition (`include_in_regular_rate`) | which habitual additions fold into the OT base rate (finding #5/#10) |
| Two working-hour types / sleep time | paid-but-not-OT-counting hours — only the OT-counting bucket drives OT onset (`subjectToOtThresholds` / `sleepTimeMinutes`) |
| Spread-of-hours premium | premium when actual spread (first-in to last-out, incl. unpaid gaps) > threshold (e.g. NY > 10h; `spreadOfHoursThreshold`). Mechanic designed; only the storage field is future. |
| Consecutive-working-days rule | earned day-off / manager alert / all-OT after N days (finding F-I) |
| Minimum guaranteed hours (+ rate basis) | reporting / call-in pay floor |
| Split-shift premium | premium for a split shift |
| Minimum inter-shift rest | e.g. EU/Swiss 11h (finding #17) |
| Holiday-compensation model + reference-period averaging | worked-holiday matrix / premium-or-substitute-day; trailing-window averaging (finding #6) |
| Meal-break obligation premium | premium if a required meal break isn't provided |
| OT averaging / reference period / redistribution | annualised-hours schemes (finding #1) |
| Banked-hours cycle expiry → cash OT payout at the cycle premium | (consistent with `cyclical-banked-hours.md`) |
| Unused / incomplete break disposition (`unusedBreak`) | no-comp / →EH / →EH-separate / follow-policy *(mechanic mapped; surfaced at Daily record)* |

---

## 11. Worked examples

**A. Rate table with a chained limit + day/night split** *(Split rates by = Specific days, Percentage)*
- Row **Monday–Saturday**: `50%` up to **02:00**, then a second limit → `60%` beyond. Name: "Extra Hours
  Mon–Sat 50% / 60%". BH↔EH split 50/50 (bank on) → half each row's OT banks, half cashes.
- Row **Sunday, Holiday**, ☀/🌙 split: ☀ Day `100%`, 🌙 Night `100%` (night also carries the +20% band
  from §4.1, composed). Names carry "(day)" / "(night)".
- Overall **Extra hours limit** (§3.5): max 40h/month across all rows.

**B. "Consider only early/late as OT" — checked vs unchecked** *(calc §4.2 E2)*
- Planned 08:00–17:00; actual 08:10–17:30.
- **Unchecked** → total worked surplus, net of the 10-min morning shortfall = **20 min OT**.
- **Checked** → only the boundary spill: **30 min OT** (late departure) + a **10-min debit** (late
  arrival), not netted. → *Total Debit Hours* carries the debit.

**C. Banked-hours cycle** *(bank on)*
- Start Jul 8, 2026 · Duration 2 months → **Next End Date 07/09/2026**. Cyclical reset on, **Cycles
  before reset** 3 (enter 2 in the UI). Missing day → "Reduce from bank and set missing". At close:
  Positive → "Convert to Extra Hours"; Negative → "Convert to missing hours". Full ledger mechanics in
  `flow/cyclical-banked-hours.md`.

**D. An Exception**
- Name "Carnival week"; Date 21/05/2026–23/05/2026; rate row **DSR & Rest days** `50%`, ☀/🌙 split with
  Night `50%`. Applies to the selected employees, **paying extra hours regardless** of each employee's
  assigned policy.

---

## 12. See also / provenance

- **Binding-level map / target flow** — `flow/configuration.md`: where the pay policy sits in the
  configuration stack (§1), its flow-coverage registry (§2.5), the all-config picture, and the
  target-flow framing. *(This doc is the current-state pay-policy detail; that doc is the binding map.)*
- **Mechanics home** — `flow/calculation-flow.md`: pay-policy lens §4.2 (E1→E3), threshold precedence /
  premium composition / OT→EH/BH tree §4.3, `SourceHistoricalState` §4.9, per-step mechanics §3.3–3.6.
- **Output vocabulary** — `flow/payroll-event-types.md` (Standard-10 vs BH-4 rate breakdown) ⚠ *legacy /
  no-longer-maintained*.
- **Banked hours** — `flow/cyclical-banked-hours.md`.
- **Reports surface** — `reports/reports-knowledge.md` (column↔config glossary; reports label the policy
  "Business Rules Group") + `Modular-calculation/requirements/Integration-to-reports-n-payroll-events-requirements.md`
  (multi-policy report-union rule; N/A ≠ 0).
- **Templates feature (future)** — `Modular-calculation/requirements/pay-policy-templates-prd.md`
  (scope, generate, governance, versioning). Not current-state config; excluded here by design.
- **Backlog / rationale** — `workbench/flow-findings.md` (params behind target behaviors) +
  `workbench/runs/*` (worked config examples: Colorado, India %/×, Dominican Republic, Switzerland,
  sleep-time, bonus-eligible).
- **Typed-config model** — `Modular-calculation/architecture.md` §5 (pay policy = set of Configurations)
  + the data-foundation `policy_keys` / `policy_values` / `policy_rate_tables` / `regimes` schema.
- **Config defaults source** — `worldwide-calculations/` (per-jurisdiction values, not surface).
- **Ground-truth fields / enums** — `data-model/fields.md`, `data-model/enums.md`.
- **Screens** — `pay-policy-screens/` (2026-07-08 snapshot).
- **Data-layer shape** — `List Business Rules Groups` GET (2024-era sample); full field map in §15.

---

## 13. Status flags / divergences

1. **Legacy event catalog** — `payroll-event-types.md` is labelled "legacy / no-longer-maintained"; event
   names here indicate shape, not a maintained contract.
2. **"Business Rules Group"** — reports still name the pay policy this way (legacy), though the target
   flow eliminates the "business rules" category (finding #22).
3. **Override-model tension** — `Modular-calculation/architecture.md` §5 ("override unrestricted;
   guardrails warn, never block") vs spine `todo.md` T4 / finding #22 ("no shift/employee override;
   policy locked once assigned"). Different layers (authoring a policy vs runtime per-employee override);
   noted, not resolved.
4. **Bank-expiry vocabulary** — UI labels (§3.2) vs calc-flow "EH with multiplier" / "carry-forward";
   UI labels canonical here, reconcile on merge.
5. **"Exceptions" naming collision** — §9 vs schedule exceptions.
6. **Composition mode ≠ "Calculate compensation rates by"** — different axes (§3.4).

---

## 14. Open items

1. `BR?` — whether the Brazil night/DSR settings (§4.3) surface in the UI for CLT-configured policies
   (Assaf unsure).
2. `?` — Hours-distribution "Hours type": is `every_hour` a third value (§4.2)?
3. `?` — Bonus-hours (§7) and Include-breaks (§3.3) calc semantics: no flow counterpart — logged as
   flow-findings #24 / #25.
4. Screens **01** (pay-policies list) + **02** (Paid Overtime, bank off) pending re-capture into
   `pay-policy-screens/`.
5. `?` — **Cross-shift interval** (§3.8): which UI tab exposes it (confirmed in data, not seen in the
   2026 screens).
6. `?` — `weekdayStage` / `holidayStage` / `ignoreOvertimeOnNonPlannedDays` (§15): likely the OT-onset
   "start after X" / non-planned controls, but the UI mapping is unconfirmed.
7. `?` — 2024-vs-2026 **version drift**: tolerance "early Entry / late Exit", the 3-option Missing-Days
   dropdown, and the editable rate **Name** appear in the 2026 UI but not the 2024 API sample.
8. Deactivation semantics: when a policy is deactivated, do assigned employees unassign or move to the
   default policy? (§1)

---

## 15. Data-layer field map — API `List Business Rules Groups`

> The pay policy's raw shape from the `List Business Rules Groups` GET — a **Business Rules Group** *is*
> the pay policy. **Sample is 2024-era** (UI screens are 2026-07-08); where a 2026 control is absent
> below, treat it as version drift. Conventions: **durations in minutes** · **`limit: -1` = unlimited** ·
> **`daysMask`** = an 8-bit string over **[Mon, Tue, Wed, Thu, Fri, Sat, Sun, Holiday]** (e.g.
> `11111100` = Monday–Saturday; `00000011` = Sunday & Holidays).

**Group (policy) level:** `uuid` · `name` · `companyUuid` · `isDefault` · `isLocked` (true once
`userProfilesCount` > 0 — lock-on-assignment) · `status` · `externalId` (nullable) · `userProfilesCount`
(the EMPLOYEES column) · created/updated. Rules are **effective-dated** — `businessRules[]` each carry
`startDate` / `endDate`; the UI "Start date" = `businessRules.startDate`.

**`rules.payedOvertime`**

| Reference / UI | API field | Value in sample |
| :-- | :-- | :-- |
| Activate Banked Hours | `hoursBankActive` | false |
| Duration | `hoursBankRecurrenceInterval` + `hoursBankRecurrencePeriod` | 2 + `month` |
| Reset type | `hoursBankResetType` | `full` / `cyclical` |
| Cycles before reset | `hoursBankCyclesCountUntilReset` | 0 |
| Hide from app | `hoursBankHideOnMobiles` | false |
| Positive / Negative expiry | `hoursBankExpiredPhasesPositiveAction` / `…NegativeAction` | `keepInExpiredPhases` |
| Bank start / first-due | `hoursBankStartDateNew` · `hoursBankStartDateOverride` | null |
| Bank limits · payment rules | `hoursBankLimits[]` · `hoursBankPayedRules{…}` | [] · nulls |
| Missing days | `hoursBankIgnoreMissingDays` (bool) | false — ⚠ 2026 UI is a 3-option dropdown |
| Consider only early/late as OT | `splitPositiveAndNegativeHours.active` | false |
| ↳ Include breaks | `splitPositiveAndNegativeHours.includeBreaks` | false |
| Split days by | `splitDaysBasedOn` | `schedule` (=by shifts) / `calendar` |
| Calculate rates by | `phasesType` + `multiplierType` | `percentage` + `disabled` |
| Rate rows | `phases[]` = `{name`(rate %)`, type`(combined/day/night)`, daysMask, extraHours`(%→EH)`, limit`(min; -1=∞)`, uuid}` | 50 / 100 |
| Deduction order | `phasesSubtractionOrder[]` + `customPhasesSubtractionOrder` | [] · false |
| BH limit alert | `hoursBankBalanceAlert{limit,active,limitType}` | 300 · true · week |
| EH defined limit | `extraHoursBalanceAlert{limit,active,limitType}` | 240 · true · day |
| OT-start alert | `overtimeStartAlert` | false |
| DSR missing-minutes discount *(Brazil)* | `discountDsrForMissingMinutes{limit,active}` | 30 · false |
| ⚠ unmapped | `weekdayStage` · `holidayStage` (0) · `ignoreOvertimeOnNonPlannedDays` (false) | likely OT-onset / non-planned controls |

**`rules.tolerance`** — `{type:"tolerance", limit`(min)`, scope`(`punch`/`day`)`, active, includeBreaks}`.
No "early Entry / late Exit" field in the 2024 sample.

**`rules.nightShift`** — `{name`(premium %)`, active, nightShiftStartTime, nightShiftEndTime, nightShiftApplyEntirePeriod}`.

**`rules.onCalls`** — `{compensation}` (`"no"` = No compensation).

**`rules.hoursDistribution`** — `{rules:[]}`.

**`rules.crossShiftsInterval`** — `{interval`(min; **660 = 11h**)`, phases:[{name, uuid, limit}]}` (§3.8).

**Absent from the payload:** Special Rules / **Bonus hours**; the rate row's editable **text Name**
(`phases[].name` is numeric — the label looks **generated** from rate + days).

---

_Single current-state home for pay-policy configuration. Derived from the 2026-07-08 product screens +
the 2024 API sample + the context base. Merges the former `pay-policy-reference.md` with the pay-policy
prose from `flow/configuration.md` §3 (per Assaf, 2026-07-10)._
