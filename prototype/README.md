# Employee WhatsApp Assistant — mockup (Idea #19)

A demoable, **live** prototype of the Employee Assistant: a WhatsApp-style chat inside a phone
frame. **Type a question, get a grounded answer** — or tap a suggestion. Built to show a CEO how the
assistant feels for a deskless employee.

Spec it implements: [`../../specs/whatsapp-assistant.md`](../../specs/whatsapp-assistant.md).

## Run

```
cd ai-features/whatsapp-assistant
npm install
npm run dev      # → http://localhost:3002
```

## How it works (and why it's built this way)

There is **no live LLM and no network call.** A small client-side *intent engine* (`src/app.jsx`)
matches the typed message to a grounded answer assembled from **hard-coded fake data** (employee
"Ana Souza"). That's deliberate:

- **Reliable in front of an audience** — works fully offline, no API key, nothing to rate-limit or
  time out mid-demo.
- **It mirrors the real architecture** — in the spec, the model *phrases*, it never *computes*; every
  number comes from an engine/trace lookup. Here the "engine" is the fake-data store, so the demo
  faithfully shows the grounded-only principle rather than papering over it.

## What to show — the demo script

The chat opens with a **welcome message enumerating everything possible (buckets A–E)** and tappable
suggestion chips. Good live questions:

| Bucket | Try typing / tapping |
| :-- | :-- |
| **A — Where I stand** | "how many banked hours do I have" · "when does my bank reset" · "how many days off do I have" · "how much overtime did I do" · "when was my last day off" · "what are my requests" |
| **B — What's expected** | "when's my next shift" · "am I working the holiday" · "how many hours this week" |
| **C — Why my number is X** | "why was my OT only 30%?" · "why is my bank lower than last month" |
| **D — How I'm paid** | "what's my overtime threshold" · "how does night pay work" · "what's my rest day" · "what's the tolerance" |
| **E — Make a request** | "I need Friday off" · "can someone cover my Saturday" → confirm → routed to the manager for approval |

**Proactive nudges (the killer loop).** The two buttons in the left panel push a proactive message
that turns into a one-tap request — e.g. *"your bank resets on 31 Jul, want to turn it into a day
off?"* → **Request time off** → the E flow. This is the reactive **+** proactive story from the spec.

Free typing is fuzzy-matched, so slightly different phrasings still work; anything unrecognized gets
a helpful fallback that re-lists the capabilities. A few Portuguese keywords are wired in as a nod to
the core market.

> **Design artifact — fake data, not a real implementation.** Sibling mockups: `../whypay-copilot/`
> (Idea #6, port 3001), `../lawtrack-ai/` (Idea #3, port 3000).
