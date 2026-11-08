import re

ESCALATION_RULES = [
    {
        "rule": "arrest_or_custody",
        "pattern": r"\barrest\w*|\bcustody\b|\bdetain\w*|picked (him|her|me|them|up)|took (my|him|her)\b.*\bpolice|police (took|picked|detained)|FIR against|\bbail\b|giraft\w*|pakad\w* (liya|le gaye|ke le)|thane le gaye|गिरफ्त\w*|हिरासत|जमानत|ধরে নিয়ে|গ্রেফতার|கைது|ଗିରଫ",
        "message": "Someone is in police custody or may be arrested. This needs a real lawyer now. Everyone has a right to a free lawyer: call NALSA 15100, or ask for the legal aid lawyer at the police station or court.",
    },
    {
        "rule": "court_paper_or_deadline",
        "pattern": r"\bsummons?\b|court notice|notice from (the )?court|hearing date|reply within|within \d+ days|legal notice (from|received|aaya|mila)|(got|received) a (legal )?notice|samman|सम्मन|समन|नोटिस",
        "message": "There is a court paper or a deadline. Do not miss it. Show the document to a lawyer before the deadline (free help: NALSA 15100). I can help you understand it, but a lawyer should check your reply.",
    },
    {
        "rule": "violence_or_safety",
        "pattern": r"\bbeat(s|ing)?\b|hits? me\b|\bviolen\w*|\babus\w*|\bmaar(ta|ti|te|a)\b|\bdhamki\b|dowry|dahej|मारपीट|मारता|मारती|दहेज|धमकी",
        "message": "If you are in danger right now, call 112. Women's helpline: 181. A lawyer or Protection Officer can get you a protection order; NALSA 15100 gives a free lawyer.",
    },
    {
        "rule": "self_harm",
        "pattern": r"suicid\w*|kill myself|end my life|khudkushi|aatmahatya|आत्महत्या",
        "message": "You don't have to face this alone. Please call Tele-MANAS 14416 (free, 24x7), or 112 if you are in immediate danger.",
    },
    {
        "rule": "complex_dispute",
        "pattern": r"\bdivorce\b|talaq|तलाक|child custody|\bland\b|zameen|ज़मीन|जमीन|property dispute|inheritance|\bsue\b|case (file )?karna|guarantee .*win|will i win",
        "message": "Disputes like this (court cases, property, divorce, inheritance) need a lawyer to read your documents, and no one can guarantee an outcome. Use my answer to prepare, then speak to a lawyer (free: NALSA 15100).",
    },
]

_AMOUNT = re.compile(
    r"(?:₹|rs\.?|inr|rupees?)\s*([\d,]+(?:\.\d+)?)\s*(lakh|lac|crore|cr)?|([\d.]+)\s*(lakh|lac|crore|cr)\b",
    re.IGNORECASE,
)
HIGH_VALUE = 10_00_000

STATUTE_WORDING = [
    (r"anticipatory bail|apprehend\w* arrest|fear\w* (of )?(being )?arrest", "direction for grant of bail to person apprehending arrest"),
    (r"arrest|custody|picked up|detain|giraftar|हिरासत|गिरफ्तार", "person arrested to be informed of grounds of arrest and of right to bail; person arrested not to be detained more than twenty-four hours"),
    (r"limitation|time limit|how long .*(file|complain|sue)|within how many|kitne (time|din)", "limitation period for filing complaint"),
    (r"deposit", "security deposit refund on vacating premises"),
    (r"salary|wages|not paid|unpaid|tankhwah", "time limit for payment of wages; claims under the Code"),
    (r"hack|password|impersonat|fake (profile|account)", "computer related offences; punishment for identity theft; punishment for cheating by personation by using computer resource"),
    (r"refund|defect|warranty|repair|deficien", "deficiency; defect; complaint to District Commission; unfair trade practice"),
    (r"domestic violence|beat|abuse|husband|in-laws", "protection orders; residence orders; application to Magistrate"),
]


def _amounts(text):
    found = []
    for m in _AMOUNT.finditer(text):
        num, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        try:
            value = float(num.replace(",", ""))
        except (TypeError, ValueError):
            continue
        unit = (unit or "").lower()
        if unit in ("lakh", "lac"):
            value *= 1_00_000
        elif unit in ("crore", "cr"):
            value *= 1_00_00_000
        found.append(value)
    return found


def statute_terms(text):
    terms = [words for pattern, words in STATUTE_WORDING if re.search(pattern, text, re.IGNORECASE)]
    return "; ".join(terms)


def escalation_flags(*texts):
    text = " ".join(t for t in texts if t)
    text = re.sub(r"digital\s+arrest|डिजिटल\s+अरेस्ट|डिजिटल\s+गिरफ्तारी", "digital-scam", text, flags=re.IGNORECASE)
    flags = []
    for r in ESCALATION_RULES:
        if re.search(r["pattern"], text, re.IGNORECASE):
            flags.append({"rule": r["rule"], "message": r["message"]})
    amounts = _amounts(text)
    if amounts and max(amounts) >= HIGH_VALUE:
        flags.append({
            "rule": "high_value",
            "message": f"The amount involved (about ₹{max(amounts) / 1_00_000:.1f} lakh) is large. Get a lawyer to review the papers before you file or sign anything.",
        })
    return flags


_SECTION = re.compile(
    r"(?<![/\w-])(?:sections?|secs?\.?|s\.|u/s|धारा|dhara)\s*((?:\d{1,3}(?!\d)[A-Z]{0,2}(?:\(\d+\))*(?:\s*(?:,|and|&|or|to|aur|और|/|-|–)\s*)?)+)",
    re.IGNORECASE,
)
_NUM = re.compile(r"\d{1,3}[A-Z]{0,2}", re.IGNORECASE)
_ACT = re.compile(r"\b((?:[A-Z][A-Za-z()'&-]*\s){1,7}(?:Act|Sanhita|Code|Rules|Adhiniyam))(?:,)?\s*(?:of\s*)?(\d{4})")
_PARTY = r"[A-Z][A-Za-z&]*(?:\s(?:of\s)?[A-Z][A-Za-z&]*){0,4}"
_CASE = re.compile(rf"\b({_PARTY})\s+(?:v\.|vs\.?|versus)\s+({_PARTY})")
_LEAD_WORDS = {"the", "under", "as", "per", "see", "refer", "according", "to", "of", "in", "and", "also", "this", "that"}

ACT_HINTS = {
    "Information Technology Act, 2000": r"\bIT Act\b|Information Technology",
    "Consumer Protection Act, 2019": r"Consumer Protection|\bCPA\b",
    "Bharatiya Nagarik Suraksha Sanhita, 2023": r"\bBNSS\b|Nagarik Suraksha",
    "Code on Wages, 2019": r"Code on Wages|Wage Code",
    "Model Tenancy Act, 2021": r"Tenancy Act",
    "Protection of Women from Domestic Violence Act, 2005": r"Domestic Violence|\bPWDVA\b|\bDV Act\b",
}


REPEALED = {
    "CrPC (replaced by the BNSS in 2024)": r"\bCr\.?P\.?C\b|Criminal Procedure",
    "IPC (replaced by the BNS in 2024)": r"\bIPC\b|Indian Penal Code|Penal Code",
    "Indian Evidence Act (replaced by the BSA in 2024)": r"Indian Evidence Act|Evidence Act, 1872",
}


def _section_in(num, text):
    n = re.escape(num)
    patterns = [
        rf"(?<![\w.(]){n}\.\s*[\(A-Z“\"\-—–]",
        rf"\bsections?\s+{n}\b",
        rf"\bsec\.?\s*{n}\b",
        rf"धारा\s*{n}\b",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _sentence_around(text, start, end):
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start))
    right = text.find("\n", end)
    return text[left + 1 : right if right != -1 else len(text)]


def extract_citations(answer):
    cites = []
    for m in _SECTION.finditer(answer):
        sentence = _sentence_around(answer, m.start(), m.end())
        near = answer[max(0, m.start() - 30) : m.end() + 30]
        act = next((name for name, pat in REPEALED.items() if re.search(pat, near, re.IGNORECASE)), None)
        if act is None:
            act = next((name for name, pat in ACT_HINTS.items() if re.search(pat, sentence, re.IGNORECASE)), None)
        for num in _NUM.findall(re.sub(r"\([^)]*\)", "", m.group(1))):
            cites.append({"type": "section", "value": num.upper(), "act": act})
    for m in _ACT.finditer(answer):
        words = m.group(1).split()
        while words and words[0].lower() in _LEAD_WORDS:
            words = words[1:]
        cites.append({"type": "act", "value": f"{' '.join(words)}, {m.group(2)}", "act": None})
    for m in _CASE.finditer(answer):
        first = m.group(1).split()
        while first and first[0].lower() in _LEAD_WORDS:
            first = first[1:]
        if first:
            second = m.group(2).rstrip(".")
            cites.append({"type": "case", "value": f"{' '.join(first)} v. {second}", "act": None})
    seen, unique = set(), []
    for c in cites:
        key = (c["type"], c["value"], c["act"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def verify_citations(answer, law_pages, web_text=""):
    by_act = {}
    for act, text in law_pages:
        by_act.setdefault(act, []).append(text)
    evidence = "\n".join(t for _, t in law_pages) + "\n" + (web_text or "")

    results = []
    for c in extract_citations(answer):
        status = "unverified"
        if c["type"] == "section" and c["act"] in REPEALED:
            status = "repealed"
        elif c["type"] == "section":
            if c["act"] and c["act"] in by_act:
                if _section_in(c["value"], "\n".join(by_act[c["act"]])):
                    status = "verified"
                elif _section_in(c["value"], evidence):
                    status = "wrong_act"
            elif _section_in(c["value"], evidence):
                status = "verified"
        elif c["type"] == "act":
            core = re.sub(r",?\s*\d{4}$", "", c["value"]).lower()
            alias = any(re.search(p, c["value"], re.IGNORECASE) and name in by_act for name, p in ACT_HINTS.items())
            if alias or any(core in a.lower() for a in by_act) or core in evidence.lower():
                status = "verified"
        elif c["type"] == "case":
            first, second = (part.split()[0] for part in c["value"].split(" v. "))
            if first.lower() in evidence.lower() and second.lower() in evidence.lower():
                status = "verified"
        results.append({**c, "status": status})
    return results


def describe(c):
    if c["type"] == "section":
        return f"Section {c['value']}" + (f" of the {c['act']}" if c.get("act") else "")
    return c["value"]


def warning_note(results):
    note = ""
    old = [r for r in results if r["status"] == "repealed"]
    bad = [r for r in results if r["status"] not in ("verified", "repealed")]
    if old:
        note += (
            "\n\nℹ️ Old law: " + "; ".join(describe(o) for o in old)
            + ". These laws were replaced on 1 July 2024, so this is history, not the current rule."
        )
    if bad:
        note += (
            "\n\n⚠️ Not verified: " + "; ".join(describe(b) for b in bad)
            + ". I could not find this in the sources I used, so please double-check it with a lawyer before relying on it."
        )
    return note


TENANCY_NOTE = (
    "\n\n⚠️ Important: the Model Tenancy Act, 2021 is a model law. It applies only in states that "
    "have passed their own version of it. In other states (for example Maharashtra, Delhi or Karnataka) "
    "your state's rent law and your rent agreement decide the deposit and notice rules. Check which "
    "law applies in your state before relying on this, for example with free legal aid (NALSA 15100)."
)


def tenancy_caveat(answer):
    if re.search(r"Tenancy Act|किरायेदारी", answer, re.IGNORECASE) and not re.search(r"adopt", answer, re.IGNORECASE):
        return TENANCY_NOTE
    return ""
