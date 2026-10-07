"""Eval harness — score the Assistant Core against the golden fixture set.

The metric that matters is **groundedness**: did every number the assistant stated trace back to a
fact it was given. Spec §3 calls the eval harness a first-class permanent investment for exactly
this reason, so a single fabricated number is a hard failure (non-zero exit), not a score.

Runnable without an API key:
    python eval_harness.py                                          # self-test the guardrail
    python eval_harness.py --golden goldenset/golden.json --validate # check the fixture set
    python eval_harness.py --golden goldenset/golden.json --offline  # score templated fallbacks

Needs an API key (runs intent -> phrase -> guardrail end to end):
    python eval_harness.py --golden goldenset/golden.json --run [--out results.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # invoked as `python eval_harness.py`, not `-m pipeline.eval_harness`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from pipeline import guardrail, intent, phrase, taxonomy
else:
    from . import guardrail, intent, phrase, taxonomy

_VALID_BUCKETS = set(taxonomy.CLASSIFIABLE_BUCKETS)
_VALID_REQUEST_TYPES = {name for name, _ in taxonomy.REQUEST_TYPES}
_VALID_FLOW_ACTIONS = {"confirm", "cancel"}


# --- golden set ---------------------------------------------------------------------------------

def load_golden(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("golden file must be a JSON list of cases")
    for case in data:
        if "id" not in case or "message" not in case or "bucket" not in case:
            raise ValueError("each golden case needs 'id', 'message' and 'bucket'")
    return data


def validate_golden(golden: list[dict]) -> list[str]:
    """Return a list of problems with the fixture set (empty == valid)."""
    problems: list[str] = []
    seen: set[str] = set()
    for case in golden:
        name = case.get("id", "<unnamed>")
        if name in seen:
            problems.append(f"{name}: duplicate id")
        seen.add(name)

        if case["bucket"] not in _VALID_BUCKETS:
            problems.append(f"{name}: unknown bucket '{case['bucket']}'")

        request_type = case.get("request_type")
        if request_type is not None:
            if request_type not in _VALID_REQUEST_TYPES:
                problems.append(f"{name}: unknown request_type '{request_type}'")
            if case["bucket"] != "e_do_something":
                problems.append(f"{name}: request_type set on bucket {case['bucket']}")

        flow_action = case.get("flow_action")
        if flow_action is not None:
            if flow_action not in _VALID_FLOW_ACTIONS:
                problems.append(f"{name}: unknown flow_action '{flow_action}'")
            if not case.get("has_pending_flow"):
                problems.append(f"{name}: flow_action set but has_pending_flow is false")

        facts = case.get("facts", {})
        if not isinstance(facts, dict):
            problems.append(f"{name}: facts must be an object")
            continue

        # A fixture whose own expectation isn't traceable to its own facts is an unpassable test.
        for expected in case.get("expected_substrings", []):
            stray = guardrail.untraceable_numbers(expected, facts)
            if stray:
                problems.append(
                    f"{name}: expected_substring '{expected}' has values absent from facts: "
                    f"{', '.join(stray)}"
                )
    return problems


# --- scoring -----------------------------------------------------------------------------------

def _substrings_present(reply: str, expected: list[str]) -> bool:
    haystack = reply.lower()
    return all(item.lower() in haystack for item in expected)


def score_case(case: dict, *, offline: bool) -> dict:
    """Run one case through the Core (or, offline, only the guardrail) and score it."""
    facts = case.get("facts", {})
    language = case.get("language", "en")
    row: dict = {"id": case["id"], "expected_bucket": case["bucket"]}

    if offline:
        # No model in the loop: score the templated fallback, which must be grounded by
        # construction. This is the regression test for the fallback path itself.
        reply = guardrail.build_fallback(facts, language)
        row["bucket"] = None
        row["bucket_ok"] = None
    else:
        result = intent.classify_intent(case["message"], bool(case.get("has_pending_flow")))
        row["bucket"] = result.bucket
        row["bucket_ok"] = result.bucket == case["bucket"]
        if case.get("request_type") is not None:
            row["request_type_ok"] = result.request_type == case["request_type"]
        if case.get("flow_action") is not None:
            row["flow_action_ok"] = result.flow_action == case["flow_action"]
        reply = phrase.phrase_reply(
            facts, result.bucket, case.get("employee_first_name", "Ana"), language
        )

    check = guardrail.check_grounded(reply, facts, language)
    delivered = reply if check.is_grounded else check.fallback_reply

    row["grounded"] = check.is_grounded
    row["untraceable"] = guardrail.untraceable_numbers(reply, facts)
    row["substrings_ok"] = _substrings_present(delivered, case.get("expected_substrings", []))
    row["reply"] = delivered
    return row


def _rate(rows: list[dict], key: str) -> float | None:
    values = [row[key] for row in rows if row.get(key) is not None]
    return round(sum(values) / len(values), 3) if values else None


def score_set(golden: list[dict], *, offline: bool) -> dict:
    rows = [score_case(case, offline=offline) for case in golden]
    return {
        "cases": len(rows),
        "mode": "offline (templated fallback)" if offline else "live (intent -> phrase)",
        "bucket_accuracy": _rate(rows, "bucket_ok"),
        "request_type_accuracy": _rate(rows, "request_type_ok"),
        "flow_action_accuracy": _rate(rows, "flow_action_ok"),
        "groundedness_pass_rate": _rate(rows, "grounded"),
        "substring_pass_rate": _rate(rows, "substrings_ok"),
        "rows": rows,
    }


def print_summary(summary: dict) -> None:
    print(f"\nmode: {summary['mode']}   cases: {summary['cases']}")
    print(f"{'case':<32} {'bucket':<18} {'ok':<4} {'grnd':<5} {'subs':<5} untraceable")
    print("-" * 88)
    for row in summary["rows"]:
        ok = "-" if row["bucket_ok"] is None else ("PASS" if row["bucket_ok"] else "FAIL")
        print(
            f"{row['id']:<32} {str(row['bucket'] or '-'):<18} {ok:<4} "
            f"{('ok' if row['grounded'] else 'FAIL'):<5} "
            f"{('ok' if row['substrings_ok'] else 'FAIL'):<5} "
            f"{', '.join(row['untraceable']) or '-'}"
        )
    print("-" * 88)
    for label, key in (
        ("bucket accuracy       ", "bucket_accuracy"),
        ("request_type accuracy ", "request_type_accuracy"),
        ("flow_action accuracy  ", "flow_action_accuracy"),
        ("groundedness pass rate", "groundedness_pass_rate"),
        ("substring pass rate   ", "substring_pass_rate"),
    ):
        value = summary[key]
        print(f"{label}: {'n/a' if value is None else value}")


# --- guardrail self-test (no fixtures, no API key) ----------------------------------------------

_SELF_TEST_FACTS = {
    "bank_balance": "14h 30m",
    "bank_reset_date": "31 Jul 2026",
    "bank_cycle": "monthly",
    "pto_days_available": 12,
    "next_shift_time": "08:00–17:00",
    "pending_requests": [{"type": "Time off", "detail": "Fri 25 Jul 2026", "status": "pending"}],
}

_SELF_TEST_CASES: list[tuple[str, str, bool]] = [
    ("verbatim value", "You have *14h 30m* in your hours bank right now. ⏱️", True),
    ("reformatted spacing", "You have *14h30m* banked.", True),
    ("date from facts", "It resets on *31 Jul 2026*.", True),
    ("bare count from int", "You have *12 days* of paid time off available. 🏖️", True),
    ("nested list value", "Your *Time off* for *25 Jul 2026* is still pending.", True),
    ("en-dash vs hyphen", "Your shift runs *08:00-17:00*.", True),
    ("no numbers at all", "I'll check that with your manager.", True),
    ("derived from minutes", "You have *870 minutes* banked.", False),
    ("unit-converted value", "You have *14.5 hours* banked.", False),
    ("invented rate", "Those hours are paid at *+50%*.", False),
    ("invented date", "It resets on *31 Aug 2026*.", False),
    ("invented shift end", "Your shift runs *08:00-18:00*.", False),
]


def self_test() -> int:
    failures = 0
    print(f"{'case':<24} {'expected':<10} {'got':<10} untraceable")
    print("-" * 72)
    for label, reply, expected in _SELF_TEST_CASES:
        stray = guardrail.untraceable_numbers(reply, _SELF_TEST_FACTS)
        got = not stray
        if got != expected:
            failures += 1
        print(
            f"{label:<24} {str(expected):<10} {str(got):<10} {', '.join(stray) or '-'}"
            f"{'   <-- MISMATCH' if got != expected else ''}"
        )
    print("-" * 72)
    print(f"{len(_SELF_TEST_CASES) - failures}/{len(_SELF_TEST_CASES)} guardrail assertions held")
    print("\nfallback for the same facts:\n" + guardrail.build_fallback(_SELF_TEST_FACTS))
    return 1 if failures else 0


# --- CLI ---------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Employee Assistant Core eval harness.")
    ap.add_argument("--golden", help="Path to the golden JSON.")
    ap.add_argument("--validate", action="store_true",
                    help="Validate the golden set and report problems.")
    ap.add_argument("--run", action="store_true",
                    help="Run the real pipeline (intent -> phrase -> guardrail). Needs an API key.")
    ap.add_argument("--offline", action="store_true",
                    help="Score the templated fallbacks only — no API key, no model calls.")
    ap.add_argument("--out", help="Write the scored results to this JSON path.")
    args = ap.parse_args()

    if not args.golden:
        return self_test()

    golden = load_golden(args.golden)
    problems = validate_golden(golden)
    if problems:
        print(f"{len(problems)} problem(s) in the golden set:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}")
        return 1
    if args.validate or not (args.run or args.offline):
        buckets = sorted({case["bucket"] for case in golden})
        languages = sorted({case.get("language", "en") for case in golden})
        print(f"OK — {len(golden)} case(s), buckets: {', '.join(buckets)}; "
              f"languages: {', '.join(languages)}")
        return 0

    summary = score_set(golden, offline=args.offline)
    print_summary(summary)

    if args.out:
        Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
        print(f"\nwrote results -> {args.out}", file=sys.stderr)

    # Hallucination budget is zero: one fabricated number fails the run.
    if summary["groundedness_pass_rate"] != 1.0:
        print("\nFAIL: at least one reply stated a number that does not trace to its facts.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
