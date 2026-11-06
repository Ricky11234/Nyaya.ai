"""Helping people act on their problem, not just understand it.

build_case(): turns a messy story spread over several chat messages (in any
              supported language) into a structured case file: what happened,
              when, what proof they have, what is still missing.

draft():      drafts the paperwork from that case file: a legal notice, a
              consumer complaint, a cyber crime complaint, a reply to a notice,
              or a complaint email. Missing facts become [PLACEHOLDERS] instead
              of being made up, and every section cited is checked in code.
"""

import io
import json
import re
from pathlib import Path

from src.guards import guards
from src.language import languages

DOC_TYPES = {
    "Legal notice": "a legal notice from the person to the other party, setting out the facts and demanding a specific remedy within 15 days, failing which they will approach the appropriate forum",
    "Consumer complaint": "a complaint to the District Consumer Disputes Redressal Commission under the Consumer Protection Act, 2019, with sections: Parties, Facts, Cause of action, Jurisdiction, Relief sought, List of documents, Verification",
    "Cyber crime complaint": "a written complaint for cybercrime.gov.in or the local cyber cell: what happened, transaction details (time, amount, UTR/reference number, accounts), suspect details, and a request to register the complaint and freeze the funds",
    "Reply to a notice": "a polite, firm reply to a notice the person received, responding point by point, denying liability where the person's facts support it, and asking for supporting documents",
    "Complaint email to company": "a short, firm grievance email to the company's grievance officer or customer care, with order details, the problem, the remedy wanted, and a deadline",
}

EMPTY_CASE = {
    "problem_type": "",
    "summary": "",
    "other_party": "",
    "timeline": [],
    "amount_involved": "",
    "proof_you_have": [],
    "proof_to_collect": [],
    "what_you_want": "",
    "questions_to_ask_you": [],
}


def _friendly_source(raw):
    from src.nodes.node import Nodes  # local import avoids a circular import

    low = Path(str(raw)).stem.lower()
    for key, name in Nodes.SOURCE_NAMES.items():
        if key in low:
            return name
    return Path(str(raw)).stem.replace("_", " ")


def build_case(llm, user_messages, language="English"):
    story = "\n".join(f"- {m}" for m in user_messages)
    prompt = f"""You organise a person's legal problem into a case file. The person
may write in English, Hinglish, Hindi, Bengali, Tamil or Odia.

What the person has said so far:
{story}

Return ONLY a JSON object with exactly these keys:
{{
  "problem_type": "short label, e.g. 'Refund not given for defective product'",
  "summary": "2 sentences in English, facts only",
  "other_party": "who the dispute is with (name/company if given, else describe)",
  "timeline": [{{"date": "as the person said it, or 'not mentioned'", "event": "what happened"}}],
  "amount_involved": "amount with Rs, or 'not mentioned'",
  "proof_you_have": ["documents/screenshots/witnesses the person says they have"],
  "proof_to_collect": ["practical proof they should gather now"],
  "what_you_want": "the outcome the person wants, in English",
  "questions_to_ask_you": ["up to 4 short questions for missing facts needed to draft a notice or complaint"]
}}

Rules:
- Use ONLY facts the person stated. Never invent names, dates, amounts or documents. Unknown = "not mentioned".
- Put the timeline in order.
- Write "questions_to_ask_you" in this language: {languages.instruction(language)}
- Everything else in English (officials and companies read case files in English)."""
    text = llm.invoke(prompt).content
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        return {**EMPTY_CASE, "summary": "Could not build the case file automatically. Please describe what happened, when, and what proof you have."}
    return {**EMPTY_CASE, **{k: v for k, v in data.items() if k in EMPTY_CASE}}


def case_to_markdown(case):
    lines = [f"**Problem:** {case.get('problem_type') or 'not mentioned'}", "", case.get("summary", ""), ""]
    lines.append(f"**Other party:** {case.get('other_party') or 'not mentioned'}")
    lines.append(f"**Amount:** {case.get('amount_involved') or 'not mentioned'}")
    lines.append(f"**You want:** {case.get('what_you_want') or 'not mentioned'}")
    if case.get("timeline"):
        lines += ["", "**Timeline**"]
        for e in case["timeline"]:
            if isinstance(e, dict):
                lines.append(f"- {e.get('date', '?')}: {e.get('event', '')}")
    for key, title in (
        ("proof_you_have", "Proof you have"),
        ("proof_to_collect", "Proof to collect now"),
        ("questions_to_ask_you", "I still need to know"),
    ):
        if case.get(key):
            lines += ["", f"**{title}**"] + [f"- {x}" for x in case[key]]
    return "\n".join(lines)


def draft(llm, case, doc_type, law_docs, language="English"):
    pages = [(_friendly_source(d.metadata.get("source", "")), d.page_content, d.metadata.get("page")) for d in law_docs]
    sources = "\n\n".join(f"[{act}, page {page}]\n{text}" for act, text, page in pages)
    prompt = f"""Draft {DOC_TYPES[doc_type]}.

CASE FILE (the only facts you may use):
{json.dumps(case, indent=2, ensure_ascii=False)}

LAW SOURCES (the only legal provisions you may cite):
{sources or '(none)'}

RULES
- Use only facts from the case file. For anything missing (names, addresses, dates, order IDs, amounts), write a placeholder in square brackets and capitals, e.g. [YOUR FULL NAME], [ORDER ID].
- Cite a section only if that exact number appears in the LAW SOURCES, and only for what it says there. If no source fits, refer to the Act generally or leave it out. Never invent case law.
- If you rely on the Model Tenancy Act, 2021, note that it applies only if the person's state has adopted it.
- Formal, clear English. No threats beyond lawful remedies.

OUTPUT
1. First, a short note titled "How to use this draft" (3-4 lines) in this language: {languages.instruction(language)}
   Include: fill the [PLACEHOLDERS], attach proof, keep a copy, and that a lawyer should review it before anything is filed in court.
2. Then a line with only "---".
3. Then the document itself, in English."""
    text = llm.invoke(prompt).content
    citations = guards.verify_citations(text, [(a, t) for a, t, _ in pages])
    text += guards.tenancy_caveat(text)
    bad = [c for c in citations if c["status"] != "verified"]
    if bad:
        text += "\n\n[CHECK BEFORE SENDING: these references could not be verified in the law text: " + \
            "; ".join(guards.describe(b) for b in bad) + "]"
    text += "\n\n(Drafted with AI help by Nyaya.ai. Not legal advice. Please have a lawyer review it before filing.)"
    return {"text": text, "citations": citations, "law_pages": [f"{a}, p.{p}" for a, _, p in pages]}


def to_docx_bytes(text, title):
    from docx import Document

    doc = Document()
    doc.add_heading(title, level=1)
    for line in text.split("\n"):
        doc.add_paragraph(line.replace("**", ""))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
