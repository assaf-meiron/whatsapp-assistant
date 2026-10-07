import React, { useEffect, useRef, useState } from "react";
import avatarUrl from "./assistant-avatar.png";

/* ============================================================================
   day.io Employee Assistant — live demo mockup (AI Feature #19)

   Everything below is a DESIGN ARTIFACT with hard-coded fake data. There is no
   real LLM and no network call — a small client-side "intent engine" matches the
   typed question to a grounded answer built from FAKE_DATA. That mirrors the real
   architecture principle from the spec: the model phrases, it NEVER computes — every
   number comes from a data lookup. It also means the demo runs fully offline, with
   zero API-key / network risk in front of an audience.
   ========================================================================== */

/* ---------------------------------------------------------------------------
   FAKE DATA — one employee, "today" = Tue 14 Jul 2026
   --------------------------------------------------------------------------- */
const EMP = {
  name: "Ana Souza",
  first: "Ana",
  role: "Cashier",
  site: "Loja Centro",
  company: "Rede Verde Supermercados",
  manager: "Marcos",
};

const DATA = {
  bank: { balance: "14h 30m", reset: "31 Jul 2026", cycle: "monthly", expiring: "4h 30m" },
  pto: { days: 12 },
  otThisPeriod: "8h 15m",
  lastAbsence: { date: "19 Jun 2026", type: "paid vacation day" },
  nextShift: { when: "tomorrow, Wed 15 Jul", time: "08:00–17:00", site: "Loja Centro" },
  weekHours: "44h across 6 days",
  holiday: { name: "Independência do Brasil", date: "Mon 7 Sep 2026", working: false },
  policy: {
    otThreshold: "8 hours a day",
    otRates: "the first 2 extra hours at +50%, anything beyond that at +70%",
    saturdayOt: "+30%",
    night: "+20% (adicional noturno) between 22:00 and 05:00, and each night hour counts as 52m30s",
    dsr: "one paid weekly rest day (DSR) — normally your Sunday",
    tolerance: "10 minutes",
    banking: "a monthly cycle, resetting on the last day of each month",
  },
  // The trace behind "why was my OT only 30%?"
  otTrace: {
    day: "Sat 5 Jul 2026",
    extra: "2h 00m",
    applied: "+30%",
    rule: "Saturday overtime band (from your CCT)",
    weekdayRate: "+50%",
  },
};

// A pending time-off request already in the system (for "request status" answers)
const SEED_REQUESTS = [
  { type: "Time off", detail: "Fri 25 Jul 2026", status: "Pending — awaiting Marcos" },
];

/* ---------------------------------------------------------------------------
   INTENT ENGINE
   Each intent: keyword groups scored against the normalized message.
   The highest-scoring intent wins; ties break by list order. No match → fallback.
   --------------------------------------------------------------------------- */
const norm = (s) =>
  s.toLowerCase().replace(/[¿?¡!.,;:()'"]/g, " ").replace(/\s+/g, " ").trim();

// A term can be a plain string (substring match) — multi-word terms allowed.
const has = (t, term) => t.includes(term);

const INTENTS = [
  // ---- greetings / help / smalltalk ----
  {
    id: "help",
    kw: ["what can you do", "help", "menu", "options", "hi", "hello", "hey", "oi", "olá", "ola", "bom dia"],
    reply: () => MENU_TEXT,
    chips: true,
  },
  {
    id: "thanks",
    kw: ["thank", "thanks", "obrigad", "valeu", "ty"],
    reply: () => `Anytime, ${EMP.first}! 😊  Anything else?`,
  },

  // ---- BUCKET A — Where I stand ----
  {
    id: "a_bank",
    kw: ["banked hour", "hours bank", "bank balance", "hour bank", "banco de horas", "how many banked", "in my bank", "banked"],
    reply: () =>
      `You have *${DATA.bank.balance}* in your hours bank right now. ⏱️\n\nIt runs on a ${DATA.bank.cycle} cycle and resets on *${DATA.bank.reset}*.`,
  },
  {
    id: "a_reset",
    kw: ["when does the bank reset", "bank reset", "reset", "expire", "expiring", "lose my hours", "when do my hours"],
    reply: () =>
      `Your hours bank resets on *${DATA.bank.reset}*. Heads-up: *${DATA.bank.expiring}* will expire if unused before then.`,
  },
  {
    id: "a_pto",
    kw: ["days off do i have", "time off balance", "days off", "vacation balance", "pto", "days of vacation", "how many days", "férias", "ferias saldo", "saldo"],
    reply: () =>
      `You have *${DATA.pto.days} days* of paid time off available. 🏖️  Want me to file a request? Just say when.`,
  },
  {
    id: "a_ot",
    kw: ["how much overtime", "how many overtime", "overtime did i", "overtime this", "my overtime", "overtime so far", "extra hours this", "hora extra que fiz", "quanto de hora extra"],
    reply: () =>
      `You've done *${DATA.otThisPeriod}* of overtime this pay period. Want to know how it's paid, or why? Just ask.`,
  },
  {
    id: "a_lastoff",
    kw: ["last time", "last day off", "last absence", "when did i last", "última folga", "ultima folga"],
    reply: () =>
      `Your last day off was *${DATA.lastAbsence.date}* — a ${DATA.lastAbsence.type}.`,
  },
  {
    id: "a_requests",
    kw: ["my requests", "request status", "pending request", "any requests", "status of my", "meus pedidos", "did my request"],
    reply: (ctx) => {
      const rs = ctx.requests;
      if (!rs.length) return "You have no pending requests right now.";
      const lines = rs.map((r) => `• *${r.type}* — ${r.detail}\n   _${r.status}_`).join("\n");
      return `Here are your requests:\n\n${lines}`;
    },
  },

  // ---- BUCKET B — What's expected of me ----
  {
    id: "b_shift",
    kw: ["next shift", "when do i work", "when's my shift", "when is my shift", "my schedule", "working tomorrow", "próximo turno", "proximo turno", "quando eu trabalho"],
    reply: () =>
      `Your next shift is *${DATA.nextShift.when}*, *${DATA.nextShift.time}* at ${DATA.nextShift.site}. 📅`,
  },
  {
    id: "b_holiday",
    kw: ["holiday", "feriado", "work the holiday", "working the holiday", "next holiday"],
    reply: () =>
      `The next holiday is *${DATA.holiday.name}* on *${DATA.holiday.date}*. You're *${DATA.holiday.working ? "scheduled to work it" : "not scheduled to work it"}* — enjoy the day off. 🎉`,
  },
  {
    id: "b_week",
    kw: ["this week", "hours this week", "week's hours", "scheduled this week", "how many hours this week"],
    reply: () => `You're scheduled for *${DATA.weekHours}* this week.`,
  },

  // ---- BUCKET C — Why my number is X (the moat / trace) ----
  {
    id: "c_whyot",
    kw: ["why was my ot", "why only 30", "why 30", "only 30", "why is my overtime", "why was my overtime", "ot only", "por que 30", "so low", "why so low"],
    reply: () => {
      const t = DATA.otTrace;
      return (
        `Good question — and the rate is correct. Here's the trace: 🔍\n\n` +
        `• *${t.day}* — you worked *${t.extra}* of overtime\n` +
        `• Rate applied: *${t.applied}*\n` +
        `• Rule: *${t.rule}*\n\n` +
        `Those hours fell on a *Saturday*. Your pay policy pays Saturday overtime at *${t.applied}*, while Monday–Friday overtime is *${t.weekdayRate}*. So it's the right rate — just the weekend band, not an error.`
      );
    },
  },
  {
    id: "c_whybank",
    kw: ["why is my bank lower", "bank lower", "why did my bank", "bank went down", "less than last month"],
    reply: () =>
      `Your bank is lower because *${DATA.bank.expiring}* expired at the last monthly reset, and you've banked fewer hours since. Nothing was removed by mistake — it's the cycle reset.`,
  },

  // ---- BUCKET D — How I'm compensated (pay policy in plain English) ----
  {
    id: "d_otrule",
    kw: ["overtime threshold", "ot threshold", "when do i earn overtime", "overtime rule", "overtime rate", "how is overtime paid", "how does overtime", "paid overtime", "overtime start", "when does overtime", "regra de hora extra"],
    reply: () =>
      `Here's how your overtime works, in plain terms:\n\n• You start earning overtime after *${DATA.policy.otThreshold}*.\n• Rates: ${DATA.policy.otRates}.\n• On Saturdays, overtime is paid at *${DATA.policy.saturdayOt}*.`,
  },
  {
    id: "d_night",
    kw: ["night", "adicional noturno", "night shift pay", "night premium", "noturno"],
    reply: () => `Night work earns *${DATA.policy.night}*. 🌙`,
  },
  {
    id: "d_dsr",
    kw: ["rest day", "dsr", "weekly rest", "descanso", "folga semanal"],
    reply: () => `You get *${DATA.policy.dsr}*.`,
  },
  {
    id: "d_tol",
    kw: ["tolerance", "grace", "late by", "few minutes late", "tolerância", "tolerancia"],
    reply: () =>
      `Punches within *${DATA.policy.tolerance}* of your scheduled time aren't counted as late or as overtime — that's your tolerance window.`,
  },
  {
    id: "d_cycle",
    kw: ["banking cycle", "bank cycle", "how does my bank work", "when does my cycle"],
    reply: () => `Your hours bank runs on *${DATA.policy.banking}*.`,
  },
];

const MENU_TEXT =
  `Here's what I can help you with, ${EMP.first} 👇\n\n` +
  `📊 *Where you stand* — banked hours, time-off balance, overtime, when your bank resets\n` +
  `📅 *Your schedule* — next shift, holidays, this week's hours\n` +
  `💡 *Why your pay is what it is* — e.g. "why was my OT only 30%?"\n` +
  `📖 *How you're paid* — your overtime rules, night premium, rest day, tolerance\n` +
  `✍️ *Make a request* — time off or a shift swap (I'll send it to ${EMP.manager} for approval)\n\n` +
  `Tap a suggestion below, or just type your question.`;

const FALLBACK =
  `I'm not sure I got that one. I can help with your *balances*, *schedule*, *why your pay looks the way it does*, *how you're paid*, or *filing a time-off or shift-swap request*.\n\nTry one of the suggestions below 👇`;

/* ---- request flows (Bucket E) — time-off & shift-swap ---- */
const WEEKDAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
// Fixed demo dates so the story is consistent regardless of when it's shown.
const DAY_DATE = {
  friday: "Fri 17 Jul",
  saturday: "Sat 18 Jul",
  sunday: "Sun 19 Jul",
  monday: "Mon 20 Jul",
  tuesday: "Tue 21 Jul",
  wednesday: "Wed 22 Jul",
  thursday: "Thu 23 Jul",
  tomorrow: "Wed 15 Jul",
};

const detectDay = (t) => {
  if (has(t, "tomorrow") || has(t, "amanhã") || has(t, "amanha")) return DAY_DATE.tomorrow;
  for (const d of WEEKDAYS) if (has(t, d)) return DAY_DATE[d];
  if (has(t, "sexta")) return DAY_DATE.friday;
  if (has(t, "sábado") || has(t, "sabado")) return DAY_DATE.saturday;
  return "Fri 17 Jul"; // sensible default for the demo
};

const isTimeOff = (t) =>
  ["day off", "time off", "off on", "take off", "vacation", "leave", "need friday", "want friday",
   "folga", "férias", "ferias", "atestado", "day of leave", "request off"].some((k) => has(t, k));

const isSwap = (t) =>
  ["swap", "cover", "trade shift", "someone to cover", "can't work", "cant work", "troca", "cobrir", "trocar turno"].some((k) => has(t, k));

const isYes = (t) => ["yes", "yep", "yeah", "sure", "send", "confirm", "ok", "okay", "sim", "manda", "pode"].some((k) => t === k || t.startsWith(k + " ") || has(t, "yes send") || has(t, "yes, send"));
const isNo = (t) => ["no", "cancel", "nope", "not now", "no thanks", "não", "nao", "deixa"].some((k) => t === k || t.startsWith(k));

/* ---------------------------------------------------------------------------
   Core resolver: given the typed text + conversation context, return replies.
   A reply = { text, buttons?: [{label,value}], nudge?: bool }
   --------------------------------------------------------------------------- */
function resolve(raw, ctx) {
  const t = norm(raw);

  // 1) Are we mid-flow (awaiting a yes/no on a pending request)?
  if (ctx.flow) {
    if (isYes(t)) {
      const f = ctx.flow;
      ctx.setFlow(null);
      if (f.type === "timeoff") {
        ctx.addRequest({ type: "Time off", detail: f.date, status: `Pending — sent to ${EMP.manager}` });
        return [{
          text: `✅ Done! Your time-off request for *${f.date}* is with ${EMP.manager} for approval. I'll message you right here the moment it's decided.`,
        }];
      }
      ctx.addRequest({ type: "Shift swap", detail: f.date, status: "Pending — awaiting a coworker" });
      return [{
        text: `✅ Sent! I've asked *Bruno, Carla and Diego* to cover your *${f.date}* shift and flagged it to ${EMP.manager}. First to accept gets it — I'll let you know. 🤝`,
      }];
    }
    if (isNo(t)) {
      ctx.setFlow(null);
      return [{ text: "No problem — nothing sent. 🙂" }];
    }
    // not a yes/no → drop the flow and treat as a fresh message
    ctx.setFlow(null);
  }

  // 2) Request intents (Bucket E) start a flow
  if (isTimeOff(t)) {
    const date = detectDay(t);
    ctx.setFlow({ type: "timeoff", date });
    return [{
      text: `Sure — you'd like *${date}* off. ✍️\nYou have *${DATA.pto.days} days* available and coverage looks fine that day.\n\nShall I send this to ${EMP.manager} for approval?`,
      buttons: [{ label: "✅ Yes, send it", value: "yes" }, { label: "Cancel", value: "cancel" }],
    }];
  }
  if (isSwap(t)) {
    const date = detectDay(t) === "Fri 17 Jul" ? "Sat 18 Jul, 08:00–17:00" : detectDay(t);
    ctx.setFlow({ type: "swap", date });
    return [{
      text: `Got it — you want someone to cover your *${date}* shift. 🔁\nI can ask *3 eligible coworkers* and notify ${EMP.manager}.\n\nSend the swap request?`,
      buttons: [{ label: "✅ Yes, send it", value: "yes" }, { label: "Cancel", value: "cancel" }],
    }];
  }

  // 3) Standalone no/cancel niceties
  if (isNo(t)) return [{ text: "No problem — I'm here whenever you need me. 🙂" }];

  // 4) Score the read-only intents
  let best = null, bestScore = 0;
  for (const intent of INTENTS) {
    let score = 0;
    for (const k of intent.kw) if (has(t, k)) score += k.length; // longer match = stronger signal
    if (score > bestScore) { bestScore = score; best = intent; }
  }
  if (best) {
    const text = best.reply(ctx);
    return [{ text, chips: best.chips }];
  }

  // 5) Fallback
  return [{ text: FALLBACK }];
}

/* ---------------------------------------------------------------------------
   Proactive nudges (opt-in pushes) — the "killer loop": a nudge that turns
   into a one-tap request.
   --------------------------------------------------------------------------- */
const NUDGES = {
  bank: {
    text:
      `🔔 Heads-up, ${EMP.first} — your hours bank resets on *${DATA.bank.reset}* and you'll lose *${DATA.bank.expiring}* if they go unused.\n\nWant to turn them into a day off?`,
    buttons: [{ label: "🏖️ Request time off", value: "I'd like to request a day off" }, { label: "Not now", value: "not now" }],
  },
  pay: {
    text:
      `🔔 ${EMP.first}, your next payslip will look a bit higher than usual — it includes the *${DATA.otThisPeriod}* of overtime you did this period. Nothing's wrong! 💚\n\nWant the breakdown?`,
    buttons: [{ label: "💡 Show me why", value: "why was my ot only 30%" }, { label: "No thanks", value: "no thanks" }],
  },
};

/* ---------------------------------------------------------------------------
   UI
   --------------------------------------------------------------------------- */
const SUGGESTIONS = [
  "💰 Banked hours",
  "📅 Next shift",
  "🏖️ Time-off balance",
  "💡 Why was my OT only 30%?",
  "📖 My overtime rules",
  "✍️ I need Friday off",
];

// Map the emoji chip label to the actual query text sent to the engine.
const CHIP_QUERY = {
  "💰 Banked hours": "how many banked hours do I have",
  "📅 Next shift": "when is my next shift",
  "🏖️ Time-off balance": "how many days off do I have",
  "💡 Why was my OT only 30%?": "why was my OT only 30%",
  "📖 My overtime rules": "what is my overtime threshold",
  "✍️ I need Friday off": "I need Friday off",
};

let _id = 0;
const uid = () => ++_id;
const now = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// Render *bold* and newlines from the plain reply strings.
function RichText({ text }) {
  return (
    <>
      {text.split("\n").map((line, i) => (
        <span key={i} style={{ display: "block" }}>
          {line.split(/(\*[^*]+\*)/g).map((part, j) =>
            part.startsWith("*") && part.endsWith("*") ? (
              <strong key={j}>{part.slice(1, -1)}</strong>
            ) : (
              <React.Fragment key={j}>{part}</React.Fragment>
            ),
          )}
        </span>
      ))}
    </>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [requests, setRequests] = useState(SEED_REQUESTS);
  const flowRef = useRef(null); // pending request flow (yes/no)
  const scrollRef = useRef(null);
  const [clock] = useState(now());

  // ctx passed to the resolver
  const ctx = {
    requests,
    addRequest: (r) => setRequests((rs) => [...rs, r]),
    get flow() { return flowRef.current; },
    setFlow: (f) => { flowRef.current = f; },
  };

  // Welcome message on load
  useEffect(() => {
    setMessages([{ id: uid(), from: "bot", text: MENU_TEXT, time: now(), chips: true }]);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, typing]);

  function pushBot(replies) {
    setTyping(true);
    window.setTimeout(() => {
      setTyping(false);
      setMessages((m) => [
        ...m,
        ...replies.map((r) => ({
          id: uid(), from: "bot", text: r.text, time: now(), buttons: r.buttons, nudge: r.nudge,
        })),
      ]);
    }, 650 + Math.min(replies[0]?.text.length ?? 0, 500));
  }

  function send(text) {
    const clean = (text ?? "").trim();
    if (!clean) return;
    setMessages((m) => [...m, { id: uid(), from: "me", text: clean, time: now() }]);
    setInput("");
    const replies = resolve(clean, ctx);
    pushBot(replies);
  }

  function fireNudge(key) {
    const n = NUDGES[key];
    setTyping(true);
    window.setTimeout(() => {
      setTyping(false);
      setMessages((m) => [
        ...m,
        { id: uid(), from: "bot", text: n.text, time: now(), buttons: n.buttons, nudge: true },
      ]);
    }, 500);
  }

  return (
    <div style={S.stage}>
      <style>{KEYFRAMES}</style>

      {/* -------- Presenter panel (context + cue cards) -------- */}
      <aside style={S.side}>
        <div style={S.brandRow}>
          <div style={S.brandDot}>d</div>
          <div>
            <div style={S.brandName}>day.io Employee Assistant</div>
            <div style={S.brandSub}>Live demo · AI Feature #19</div>
          </div>
        </div>

        <p style={S.sideLead}>
          The employee's HR interface <em>inside WhatsApp</em>. Every answer is grounded in {EMP.first}'s
          real computed data — the model phrases, it never invents a number.
        </p>

        <div style={S.legendTitle}>What you can ask (A–E)</div>
        <ul style={S.legend}>
          <li><b>A · Where I stand</b> — banked hours, PTO, overtime, bank reset</li>
          <li><b>B · What's expected</b> — next shift, holidays, week's hours</li>
          <li><b>C · Why my pay is X</b> — "why was my OT only 30%?"</li>
          <li><b>D · How I'm paid</b> — OT rules, night premium, rest day</li>
          <li><b>E · Make a request</b> — time off · shift swap → approval</li>
        </ul>

        <div style={S.legendTitle}>Proactive nudges (the killer loop)</div>
        <div style={S.nudgeRow}>
          <button style={S.nudgeBtn} onClick={() => fireNudge("bank")}>🔔 Bank-expiry nudge</button>
          <button style={S.nudgeBtn} onClick={() => fireNudge("pay")}>🔔 Pay heads-up nudge</button>
        </div>
        <div style={S.disclaimer}>
          Mockup — hard-coded fake data, offline intent engine (no live LLM). Employee: {EMP.name},
          {" "}{EMP.role} @ {EMP.company}.
        </div>
      </aside>

      {/* -------- Phone -------- */}
      <div style={S.phone}>
        <div style={S.notch} />
        <div style={S.screen}>
          {/* status bar */}
          <div style={S.statusBar}>
            <span>{clock}</span>
            <span style={{ letterSpacing: 1 }}>●●● ▂▄▆ 🔋</span>
          </div>
          {/* WhatsApp header */}
          <div style={S.waHeader}>
            <span style={S.back}>‹</span>
            <div style={S.avatar} />
            <div style={{ flex: 1 }}>
              <div style={S.waName}>day.io Assistant</div>
              <div style={S.waStatus}>online</div>
            </div>
            <span style={S.hIcon}>📞</span>
            <span style={S.hIcon}>⋮</span>
          </div>

          {/* chat */}
          <div style={S.chat} ref={scrollRef}>
            <div style={S.dayPill}>TODAY</div>
            {messages.map((m) => (
              <MsgRow key={m.id} m={m} onButton={(v) => send(v)} />
            ))}
            {typing && (
              <div style={{ ...S.row, justifyContent: "flex-start" }}>
                <div style={{ ...S.bubble, ...S.bot }}>
                  <div style={S.typing}>
                    <span style={S.dot} /><span style={{ ...S.dot, animationDelay: ".2s" }} />
                    <span style={{ ...S.dot, animationDelay: ".4s" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* suggestions */}
          <div style={S.chips}>
            {SUGGESTIONS.map((c) => (
              <button key={c} style={S.chip} onClick={() => send(CHIP_QUERY[c] || c)}>{c}</button>
            ))}
          </div>

          {/* input */}
          <form
            style={S.inputBar}
            onSubmit={(e) => { e.preventDefault(); send(input); }}
          >
            <span style={S.inIcon}>😊</span>
            <input
              style={S.input}
              placeholder="Type a message"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" style={S.sendBtn} aria-label="send">➤</button>
          </form>
        </div>
      </div>
    </div>
  );
}

function MsgRow({ m, onButton }) {
  const mine = m.from === "me";
  return (
    <div style={{ ...S.row, justifyContent: mine ? "flex-end" : "flex-start" }}>
      <div
        style={{
          ...S.bubble,
          ...(mine ? S.me : S.bot),
          ...(m.nudge ? S.nudgeBubble : null),
        }}
      >
        <div style={S.bubbleText}><RichText text={m.text} /></div>
        {m.buttons && (
          <div style={S.btnStack}>
            {m.buttons.map((b) => (
              <button key={b.label} style={S.replyBtn} onClick={() => onButton(b.value)}>
                {b.label}
              </button>
            ))}
          </div>
        )}
        <div style={{ ...S.time, textAlign: "right" }}>
          {m.time}{mine && <span style={S.ticks}> ✓✓</span>}
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   Styles
   --------------------------------------------------------------------------- */
const WA = { header: "#008069", out: "#d9fdd3", chatBg: "#e5ddd5", teal: "#027e6f" };

const KEYFRAMES = `
@keyframes blink { 0%,60%,100% { opacity:.25 } 30% { opacity:1 } }
* { box-sizing: border-box; }
button { font: inherit; cursor: pointer; }
`;

const S = {
  stage: {
    minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
    gap: 40, flexWrap: "wrap", padding: "36px 24px",
    background: "radial-gradient(1200px 600px at 20% 0%, #16323a, #0b141a 70%)",
  },

  // presenter panel
  side: { width: 360, maxWidth: "92vw", color: "#cfe3df" },
  brandRow: { display: "flex", alignItems: "center", gap: 12, marginBottom: 14 },
  brandDot: {
    width: 40, height: 40, borderRadius: 12, background: WA.header, color: "#fff",
    display: "grid", placeItems: "center", fontWeight: 800, fontSize: 22,
  },
  brandName: { color: "#fff", fontWeight: 700, fontSize: 17 },
  brandSub: { color: "#7ea8a0", fontSize: 12.5, marginTop: 2 },
  sideLead: { fontSize: 14, lineHeight: 1.5, color: "#a7c7c1" },
  legendTitle: { color: "#fff", fontWeight: 700, fontSize: 13, textTransform: "uppercase", letterSpacing: 0.6, margin: "22px 0 8px" },
  legend: { margin: 0, paddingLeft: 18, fontSize: 13.5, lineHeight: 1.75, color: "#bfdbd5" },
  nudgeRow: { display: "flex", gap: 10, flexWrap: "wrap" },
  nudgeBtn: {
    background: "rgba(255,255,255,.06)", color: "#eafff9", border: "1px solid rgba(255,255,255,.18)",
    borderRadius: 10, padding: "9px 12px", fontSize: 13, fontWeight: 600,
  },
  disclaimer: { marginTop: 22, fontSize: 11.5, color: "#6f938c", lineHeight: 1.5 },

  // phone
  phone: {
    width: 372, height: 760, background: "#050505", borderRadius: 46, padding: 12,
    boxShadow: "0 40px 90px rgba(0,0,0,.55), inset 0 0 0 2px #2a2a2a", position: "relative",
    flexShrink: 0,
  },
  notch: {
    position: "absolute", top: 20, left: "50%", transform: "translateX(-50%)",
    width: 120, height: 26, background: "#050505", borderRadius: 16, zIndex: 5,
  },
  screen: {
    width: "100%", height: "100%", background: WA.chatBg, borderRadius: 36, overflow: "hidden",
    display: "flex", flexDirection: "column",
  },
  statusBar: {
    background: WA.header, color: "#fff", fontSize: 12.5, fontWeight: 600,
    padding: "10px 22px 6px", display: "flex", justifyContent: "space-between", alignItems: "center",
  },

  waHeader: {
    background: WA.header, color: "#fff", display: "flex", alignItems: "center", gap: 10,
    padding: "6px 12px 10px",
  },
  back: { fontSize: 26, lineHeight: 1, marginRight: -2 },
  avatar: {
    width: 38, height: 38, borderRadius: "50%",
    backgroundImage: `url(${avatarUrl})`, backgroundSize: "cover", backgroundPosition: "center",
    border: "1.5px solid rgba(255,255,255,.6)", flexShrink: 0,
  },
  waName: { fontWeight: 700, fontSize: 16 },
  waStatus: { fontSize: 12, opacity: 0.85 },
  hIcon: { fontSize: 16, opacity: 0.95, marginLeft: 4 },

  chat: {
    flex: 1, overflowY: "auto", padding: "12px 10px",
    backgroundColor: WA.chatBg,
    backgroundImage:
      "radial-gradient(rgba(0,0,0,0.035) 1px, transparent 1px)",
    backgroundSize: "18px 18px",
  },
  dayPill: {
    alignSelf: "center", width: "fit-content", margin: "0 auto 10px", background: "#ffffffcc",
    color: "#54656f", fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 8,
    display: "block", textAlign: "center", letterSpacing: 0.5,
  },
  row: { display: "flex", margin: "6px 2px" },
  bubble: {
    maxWidth: "82%", padding: "7px 9px 5px", borderRadius: 10, fontSize: 14.2, lineHeight: 1.42,
    color: "#111b21", boxShadow: "0 1px 0.5px rgba(0,0,0,.13)", position: "relative",
  },
  bot: { background: "#fff", borderTopLeftRadius: 2 },
  me: { background: WA.out, borderTopRightRadius: 2 },
  nudgeBubble: { borderLeft: `4px solid ${WA.header}` },
  bubbleText: { whiteSpace: "normal", wordBreak: "break-word" },
  time: { fontSize: 10.5, color: "#667781", marginTop: 3, lineHeight: 1 },
  ticks: { color: "#53bdeb" },

  btnStack: { marginTop: 8, borderTop: "1px solid #e9edef", display: "flex", flexDirection: "column" },
  replyBtn: {
    background: "transparent", color: WA.teal, border: "none", borderTop: "1px solid #e9edef",
    padding: "9px 4px", fontSize: 14, fontWeight: 600, textAlign: "center",
  },

  typing: { display: "flex", gap: 4, padding: "4px 2px" },
  dot: {
    width: 7, height: 7, borderRadius: "50%", background: "#93a0a6", display: "inline-block",
    animation: "blink 1.2s infinite",
  },

  chips: {
    display: "flex", gap: 7, padding: "8px 10px", overflowX: "auto", background: WA.chatBg,
    borderTop: "1px solid rgba(0,0,0,.06)",
  },
  chip: {
    whiteSpace: "nowrap", background: "#fff", color: WA.teal, border: "1px solid #cfe0db",
    borderRadius: 16, padding: "7px 12px", fontSize: 12.5, fontWeight: 600, flexShrink: 0,
  },

  inputBar: {
    display: "flex", alignItems: "center", gap: 8, padding: "8px 10px 12px", background: "#f0f2f5",
  },
  inIcon: { fontSize: 20, opacity: 0.6 },
  input: {
    flex: 1, border: "none", outline: "none", background: "#fff", borderRadius: 20,
    padding: "10px 14px", fontSize: 14.5, color: "#111b21",
  },
  sendBtn: {
    width: 42, height: 42, borderRadius: "50%", background: WA.header, color: "#fff",
    border: "none", fontSize: 16, flexShrink: 0,
  },
};
