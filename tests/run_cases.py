"""Runs every test case in tests/cases.json and saves the unedited outputs.

    python tests/run_cases.py                 # all 15 cases (about 10-15 minutes)
    python tests/run_cases.py 03 09           # only cases whose id starts with 03 or 09
    python tests/run_cases.py --pause 25      # more seconds between cases if Groq rate-limits

Writes:
    outputs/raw/<id>.md      the conversation, answer, lawyer warnings, citation
                             check, case file and draft, exactly as produced
    outputs/raw/<id>.json    the same as data
    outputs/summary.md       one row per case with the automatic checks

The automatic checks are rough signals, not a grade. Every case still needs a
human read; the "review" column in summary.md is left empty for that.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")  # so Hindi/Tamil print on Windows

from main import AgenticRAG, legal_pdfs  # noqa: E402
from src.assist.case_tools import case_to_markdown  # noqa: E402
from src.guards import guards  # noqa: E402
from src.config.config import Config  # noqa: E402

RAW = ROOT / "outputs" / "raw"
class RateLimited(Exception):
    pass


NEGATION = r"\b(not|no|doesn't|does not|isn't|is not|cannot|couldn't|could not|unable|nahi|nahin)\b|नहीं|Not verified|❌"


def run_checks(case, result):
    exp = case["expect"]
    answer = result.get("answer", "")
    checks = {
        "language": result.get("reply_language") == exp["language"],
        "source": result.get("source_type") in exp["source"],
        "lawyer_warning": bool(result.get("escalations")) == exp["escalation"],
    }
    # Trap cases (fake sections, outside-the-corpus laws) pass when the check
    # flags what it can't verify, so only score this on ordinary cases.
    if not exp.get("not_assert") and not case.get("trap"):
        checks["all_citations_verified"] = all(c["status"] in ("verified", "repealed") for c in result.get("citations", []))
    if exp.get("mention_any"):
        checks["mentions"] = any(t.lower() in answer.lower() for t in exp["mention_any"])
    if exp.get("not_assert"):
        ok = True
        for term in exp["not_assert"]:
            for line in answer.splitlines():
                if term.lower() in line.lower() and not re.search(NEGATION, line, re.IGNORECASE):
                    ok = False
        checks["did_not_assert_fake"] = ok
    return checks


def to_markdown(case, turns, case_file, draft, checks):
    out = [f"# {case['id']}", f"_Tests: {case['what_it_tests']}_", f"_Mode: {case['mode']}_", ""]
    for t in turns:
        r = t["result"]
        out += ["## User", t["input"], "",
                f"**Reply language:** {r.get('reply_language')} · **Source:** {r.get('source_type')} · "
                f"**Confidence:** {r.get('confidence')} · **Time:** {t['seconds']}s"]
        for f in r.get("escalations", []):
            out.append(f"**Lawyer warning ({f['rule']}):** {f['message']}")
        out += ["", "## Nyaya.ai", r.get("answer", ""), "", "**Citation check:**"]
        out += [f"- {guards.describe(c)}: {c['status']}" for c in r.get("citations", [])] or ["- nothing cited"]
        out.append("")
    if case_file:
        out += ["## Case file", case_to_markdown(case_file), ""]
    if draft:
        out += [f"## Draft: {case['draft']}", f"_Law pages used: {', '.join(draft.get('law_pages', []))}_", "", draft["text"], ""]
    out += ["## Automatic checks"] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("only", nargs="*", help="case id prefixes to run")
    p.add_argument("--pause", type=int, default=15)
    a = p.parse_args()

    cases = json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))
    if a.only:
        cases = [c for c in cases if any(c["id"].startswith(o) for o in a.only)]
    RAW.mkdir(parents=True, exist_ok=True)

    rag = AgenticRAG(legal_pdfs())

    for i, case in enumerate(cases):
        print(f"\n===== {case['id']} =====")
        history, turns, case_file, draft, error = [], [], None, None, ""
        try:
            for msg in case["turns"]:
                start = time.time()
                r = rag.ask(msg, history, case["mode"])
                if "(RATE_LIMIT)" in r.get("answer", ""):
                    raise RateLimited()
                turns.append({"input": msg, "result": r, "seconds": round(time.time() - start, 1)})
                history += [{"role": "user", "content": msg}, {"role": "assistant", "content": r["answer"]}]
            lang = turns[-1]["result"].get("reply_language") or "English"
            case_file = rag.build_case(case["turns"], lang)
            if case.get("draft"):
                draft = rag.draft(case_file, case["draft"], lang)
            checks = run_checks(case, turns[-1]["result"])
        except Exception as e:
            if isinstance(e, RateLimited) or "rate_limit" in repr(e):
                # Don't overwrite an earlier good result with a rate-limit error.
                print(f"\nGroq's daily token limit reached at {case['id']}. Stopping; earlier "
                      "outputs are untouched. Rerun this case and the ones after it later.")
                break
            error, checks = repr(e), {"ran": False}
            print("ERROR:", error)

        record = {"case": case, "turns": turns, "case_file": case_file, "draft": draft, "checks": checks, "error": error}
        (RAW / f"{case['id']}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        if turns:
            (RAW / f"{case['id']}.md").write_text(to_markdown(case, turns, case_file, draft, checks), encoding="utf-8")

        print(" | ".join(str(v) for v in summary_row(record).values()))
        if i < len(cases) - 1:
            time.sleep(a.pause)  # stay under Groq free-tier rate limits

    write_summary()
    print("\nDone. Open outputs/summary.md, then read each file in outputs/raw/.")


def summary_row(record):
    case, turns, checks, error = record["case"], record["turns"], record["checks"], record["error"]
    last = turns[-1]["result"] if turns else {}
    cites = last.get("citations", [])
    return {
        "case": case["id"],
        "language": last.get("reply_language", ""),
        "source": last.get("source_type", ""),
        "confidence": last.get("confidence", ""),
        "lawyer_warnings": ", ".join(f["rule"] for f in last.get("escalations", [])) or "-",
        "citations (unverified)": f"{len(cites)} ({sum(c['status'] not in ('verified', 'repealed') for c in cites)})",
        "checks passed": f"{sum(checks.values())}/{len(checks)}",
        "failed": ", ".join(k for k, v in checks.items() if not v) or "-",
        "error": error or "-",
        "review": "",
    }


def write_summary():
    """One row per case from every saved result in outputs/raw, so running
    only some cases updates their rows and keeps the rest."""
    all_cases = [c["id"] for c in json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))]
    rows = []
    for cid in all_cases:
        f = RAW / f"{cid}.json"
        if f.exists():
            rows.append(summary_row(json.loads(f.read_text(encoding="utf-8"))))
    if not rows:
        return
    header = (
        f"# Nyaya.ai test run, {time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Models: {Config.LLM_MODEL} (answers), {Config.EVALUATOR_MODEL} (evaluator)\n\n"
    )
    table = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    table += ["| " + " | ".join(str(r[k]) for k in rows[0]) + " |" for r in rows]
    (ROOT / "outputs" / "summary.md").write_text(header + "\n".join(table) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
