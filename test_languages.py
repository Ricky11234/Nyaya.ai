"""Quick local test of Nyaya.ai's language support.

    python test_languages.py            # all cases (about 3-4 minutes, pauses for rate limits)
    python test_languages.py 03 07      # only cases whose id starts with 03 or 07

Each answer is saved, unedited, to outputs/language_tests/<id>.md and a
summary table to outputs/language_tests/summary.md.

The automatic check only looks at the *script* of the answer (e.g. are there
Tamil letters in a Tamil answer, no Devanagari in a Hinglish answer). Whether
the answer is actually correct and well written still needs a human read.
"""

import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # so Hindi/Tamil print on Windows

from main import AgenticRAG, legal_pdfs  # noqa: E402
from src.language import languages  # noqa: E402

SOURCES = legal_pdfs()  # every PDF in data/legal_pdfs

# (id, turns, mode, dropdown choice, expected reply language)
CASES = [
    ("01_english", ["I ordered a mixer online for Rs 4,500, it arrived broken, I returned it and the refund hasn't come for 2 months. What can I do?"], "normal", languages.AUTO, "English"),
    ("02_hinglish", ["Online order ka refund 2 mahine se nahi aaya, seller reply bhi nahi kar raha. Kya karun?"], "normal", languages.AUTO, "Hinglish"),
    ("03_hindi", ["मेरे अकाउंट से UPI फ्रॉड में 35,000 रुपये कट गए। अब मुझे क्या करना चाहिए?"], "normal", languages.AUTO, "Hindi"),
    ("04_tamil_beta", ["நான் ஆன்லைனில் வாங்கிய காலணி தவறான அளவில் வந்தது. திருப்பி அனுப்பினேன், ஆனால் பணம் திரும்ப வரவில்லை. என்ன செய்யலாம்?"], "normal", languages.AUTO, "Tamil"),
    ("05_odia_beta", ["ମୋ ଫେସବୁକ୍ ଆକାଉଣ୍ଟ ହ୍ୟାକ୍ ହୋଇଯାଇଛି ଏବଂ କେହି ମୋ ନାଁରେ ଟଙ୍କା ମାଗୁଛି। ମୁଁ କ'ଣ କରିବି?"], "normal", languages.AUTO, "Odia"),
    ("06_bengali_beta", ["পুলিশ আমার ভাইকে গতকাল রাতে ধরে নিয়ে গেছে, কারণ বলেনি। আমরা কী করতে পারি?"], "normal", languages.AUTO, "Bengali"),
    ("07_hinglish_followup", ["Flipkart se AC liya tha, installation ke 3 din baad gas leak ho gaya.", "Kitne time ke andar complaint karni padegi?"], "normal", languages.AUTO, "Hinglish"),
    ("08_dropdown_override", ["My online order refund has not come for 2 months. What can I do?"], "normal", "Hindi", "Hindi"),
    ("09_professional_hinglish", ["BNSS mein anticipatory bail ki conditions kya hain?"], "professional", languages.AUTO, "Hinglish"),
]

# Characters we expect to see in an answer in each language.
SCRIPT = {
    "Hindi": r"[ऀ-ॿ]",
    "Bengali": r"[ঀ-৿]",
    "Tamil": r"[஀-௿]",
    "Odia": r"[଀-୿]",
}
NON_LATIN = r"[ऀ-౿]"


def script_ok(answer, lang):
    if lang in SCRIPT:
        return bool(re.search(SCRIPT[lang], answer))
    # English and Hinglish should be in Roman letters only.
    return not re.search(NON_LATIN, answer)


def main():
    only = sys.argv[1:]
    cases = [c for c in CASES if not only or any(c[0].startswith(o) for o in only)]
    out = Path("outputs/language_tests")
    out.mkdir(parents=True, exist_ok=True)

    rag = AgenticRAG(SOURCES)
    rows = []

    for i, (cid, turns, mode, choice, expected) in enumerate(cases):
        print(f"\n===== {cid} =====")
        history, log = [], [f"# {cid}", f"Mode: {mode} | Dropdown: {choice} | Expected reply language: {expected}", ""]
        start = time.time()
        for msg in turns:
            r = rag.ask(msg, history, mode, choice)
            history += [{"role": "user", "content": msg}, {"role": "assistant", "content": r["answer"]}]
            log += [f"## User\n{msg}", "",
                    f"_Reply language: {r['reply_language']} | Source: {r['source_type']} | Confidence: {r['confidence']}_", "",
                    f"## Nyaya.ai\n{r['answer']}", ""]
        seconds = round(time.time() - start, 1)

        lang_ok = r["reply_language"] == expected
        writing_ok = script_ok(r["answer"], expected)
        log += ["## Automatic checks",
                f"- Reply language = {expected}: {'PASS' if lang_ok else 'FAIL'} (got {r['reply_language']})",
                f"- Answer written in the right script: {'PASS' if writing_ok else 'FAIL'}"]
        (out / f"{cid}.md").write_text("\n".join(log), encoding="utf-8")

        rows.append(f"| {cid} | {expected} | {r['reply_language']} | {'PASS' if lang_ok else 'FAIL'} | "
                    f"{'PASS' if writing_ok else 'FAIL'} | {r['source_type']} | {r['confidence']} | {seconds}s |")
        print(rows[-1])

        if i < len(cases) - 1:
            time.sleep(12)  # stay under Groq free-tier rate limits

    summary = ["# Language test summary", time.strftime("%Y-%m-%d %H:%M"), "",
               "| Case | Expected | Got | Language | Script | Source | Confidence | Time |",
               "|---|---|---|---|---|---|---|---|"] + rows
    (out / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"\nSaved answers to {out}/  (open summary.md)")


if __name__ == "__main__":
    main()
