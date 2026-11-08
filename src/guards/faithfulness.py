import json
import re

MAX_SOURCE_CHARS = 10000

PROMPT = """You check whether an answer from a legal help app is grounded in its sources.

SOURCES
{sources}

ANSWER
{answer}

Step 1: List the factual claims in the ANSWER, one fact per claim. A factual claim says what the law says, a right or duty, a deadline or time limit, an amount or limit, a penalty, which authority, court or portal to use, or a helpline number.
If a sentence mixes advice with a fact (for example "send a complaint citing Section 84"), keep only the fact ("Section 84 covers defective products").
Skip pure advice (for example "keep your receipts", "send a written request", "take photos"), questions to the user, the "you need a lawyer" warning, and the "Based on" line.
Write each claim in short English, even if the answer is in another language.

Step 2: Give each claim a verdict:
SUPPORTED if the SOURCES say it, in any wording or language, or it follows directly from them. The CHECKED FACTS count as sources.
NOT_SUPPORTED if the SOURCES do not say it or say something different. Any specific number, deadline or amount must appear in the SOURCES to be SUPPORTED.

Return only JSON, nothing else:
{{"claims": [{{"claim": "...", "verdict": "SUPPORTED"}}]}}"""


def _parse(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    claims = []
    for c in data.get("claims", []):
        claim = str(c.get("claim", "")).strip()
        verdict = str(c.get("verdict", "")).upper().replace(" ", "_")
        if claim and verdict in ("SUPPORTED", "NOT_SUPPORTED"):
            claims.append({"claim": claim, "verdict": verdict})
    return claims


def check(llm, answer, sources):
    sources = sources.strip()[:MAX_SOURCE_CHARS]
    if not sources:
        return None
    claims = None
    for _ in range(2):
        try:
            reply = llm.invoke(PROMPT.format(sources=sources, answer=answer)).content or ""
        except Exception as e:
            print(f"Faithfulness check skipped: {e}")
            return None
        claims = _parse(reply)
        if claims is not None:
            break
    if claims is None:
        print(f"Faithfulness check skipped: could not read the checker's reply: {reply[:200]!r}")
        return None
    supported = sum(c["verdict"] == "SUPPORTED" for c in claims)
    total = len(claims)
    return {
        "score": round(supported / total, 2) if total else None,
        "supported": supported,
        "total": total,
        "unsupported": [c["claim"] for c in claims if c["verdict"] == "NOT_SUPPORTED"],
        "claims": claims,
    }


def note(result, limit=3):
    if not result or not result["unsupported"]:
        return ""
    shown = result["unsupported"][:limit]
    more = len(result["unsupported"]) - len(shown)
    text = "; ".join(shown) + (f" (and {more} more)" if more > 0 else "")
    return (
        f"\n\n⚠️ Not found in the sources: {text}. "
        "Please double-check these points before acting on them."
    )


def summary(result):
    if not result or result["score"] is None:
        return "not checked"
    return f"{result['supported']}/{result['total']} claims found in the sources ({round(result['score'] * 100)}%)"
