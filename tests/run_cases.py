import argparse
import json
import re
import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("FALLBACK_MODEL", "none")

_p = argparse.ArgumentParser()
_p.add_argument("only", nargs="*", help="case id prefixes to run")
_p.add_argument("--pause", type=int, default=30)
_p.add_argument("--out", default="outputs", help="folder for results (default: outputs)")
ARGS = _p.parse_args()
OUT = ROOT / ARGS.out

from main import AgenticRAG, legal_pdfs
from src.assist.case_tools import case_to_markdown
from src.guards import guards, faithfulness
from src.config.config import Config

RAW = OUT / "raw"
class RateLimited(Exception):
    def __init__(self, daily):
        super().__init__("daily" if daily else "per minute")
        self.daily = daily


def is_daily(text):
    return "RATE_LIMIT_DAY" in text or "per day" in text or "TPD" in text


NEGATION = r"\b(not|no|doesn't|does not|isn't|is not|cannot|couldn't|could not|unable|nahi|nahin)\b|नहीं|Not verified|❌"


def run_checks(case, result):
    exp = case["expect"]
    answer = result.get("answer", "")
    checks = {
        "language": result.get("reply_language") == exp["language"],
        "source": result.get("source_type") in exp["source"],
        "lawyer_warning": bool(result.get("escalations")) == exp["escalation"],
    }
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
        faith = r.get("faithfulness")
        out += ["", f"**Grounded:** {faithfulness.summary(faith)}"]
        out += [f"- {c['verdict']}: {c['claim']}" for c in (faith or {}).get("claims", [])]
        out.append("")
    if case_file:
        out += ["## Case file", case_to_markdown(case_file), ""]
    if draft:
        out += [f"## Draft: {case['draft']}", f"_Law pages used: {', '.join(draft.get('law_pages', []))}_", "", draft["text"], ""]
    out += ["## Automatic checks"] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    return "\n".join(out)


def main():
    a = ARGS

    cases = json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))
    if a.only:
        cases = [c for c in cases if any(c["id"].startswith(o) for o in a.only)]
    RAW.mkdir(parents=True, exist_ok=True)

    rag = AgenticRAG(legal_pdfs())

    for i, case in enumerate(cases):
        print(f"\n===== {case['id']} =====")
        limit = None
        for attempt in range(3):
            try:
                turns, case_file, draft, checks, error = run_case(rag, case)
                limit = None
                break
            except RateLimited as hit:
                limit = hit
                if hit.daily or attempt == 2:
                    break
                print("Per-minute token limit hit. Waiting 65 seconds, then retrying this case...")
                time.sleep(65)
        if limit:
            print(f"\nGroq's {limit} token limit reached at {case['id']}. Stopping; earlier "
                  "outputs are untouched. Rerun this case and the ones after it later.")
            break

        record = {"case": case, "turns": turns, "case_file": case_file, "draft": draft, "checks": checks, "error": error}
        (RAW / f"{case['id']}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        if turns:
            (RAW / f"{case['id']}.md").write_text(to_markdown(case, turns, case_file, draft, checks), encoding="utf-8")

        print(" | ".join(str(v) for v in summary_row(record).values()))
        if i < len(cases) - 1:
            time.sleep(a.pause)

    write_summary()
    print(f"\nDone. Open {ARGS.out}/summary.md, then read each file in {ARGS.out}/raw/.")


def run_case(rag, case):
    turns, case_file, draft, error = [], None, None, ""
    try:
        history = []
        for msg in case["turns"]:
            start = time.time()
            r = rag.ask(msg, history, case["mode"])
            if "(RATE_LIMIT" in r.get("answer", ""):
                raise RateLimited(is_daily(r["answer"]))
            turns.append({"input": msg, "result": r, "seconds": round(time.time() - start, 1)})
            history += [{"role": "user", "content": msg}, {"role": "assistant", "content": r["answer"]}]
        lang = turns[-1]["result"].get("reply_language") or "English"
        case_file = rag.build_case(case["turns"], lang)
        if case.get("draft"):
            draft = rag.draft(case_file, case["draft"], lang)
        checks = run_checks(case, turns[-1]["result"])
    except RateLimited:
        raise
    except Exception as e:
        if "rate_limit" in repr(e):
            raise RateLimited(is_daily(repr(e)))
        error, checks = repr(e), {"ran": False}
        print("ERROR:", error)
    return turns, case_file, draft, checks, error


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
        "grounded": faithfulness.summary(last.get("faithfulness")).split(" claims")[0],
        "checks passed": f"{sum(checks.values())}/{len(checks)}",
        "failed": ", ".join(k for k, v in checks.items() if not v) or "-",
        "error": error or "-",
        "review": "",
    }


def write_summary():
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
        f"Models: {Config.LLM_MODEL} (answers), {Config.EVALUATOR_MODEL} (evaluator), {Config.FACT_CHECK_MODEL} (fact check)\n\n"
    )
    table = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    table += ["| " + " | ".join(str(r[k]) for k in rows[0]) + " |" for r in rows]
    (OUT / "summary.md").write_text(header + "\n".join(table) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
