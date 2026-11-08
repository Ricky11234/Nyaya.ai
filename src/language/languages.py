import re

AUTO = "Auto (reply in my language)"

LANGUAGES = {
    "English": {
        "status": "full",
        "instruction": "Write the answer in simple, plain English.",
    },
    "Hinglish": {
        "status": "full",
        "instruction": (
            "Write the answer in Hinglish: Hindi written in Roman (English) letters, "
            "mixed naturally with English words, the way people chat on WhatsApp. "
            "Do NOT use Devanagari script. Keep Act names and section numbers in English."
        ),
    },
    "Hindi": {
        "status": "full",
        "instruction": (
            "Write the answer in simple Hindi in Devanagari script. "
            "Keep Act names and section numbers in English."
        ),
    },
    "Bengali": {"status": "beta", "instruction": "Write the answer in simple Bengali (Bangla script). Keep Act names and section numbers in English."},
    "Tamil": {"status": "beta", "instruction": "Write the answer in simple Tamil (Tamil script). Keep Act names and section numbers in English."},
    "Odia": {"status": "beta", "instruction": "Write the answer in simple Odia (Odia script). Keep Act names and section numbers in English."},
}

UI_CHOICES = [AUTO] + [
    name if info["status"] == "full" else f"{name} (beta)"
    for name, info in LANGUAGES.items()
]

_SCRIPTS = [
    (r"[஀-௿]", "Tamil"),
    (r"[ঀ-৿]", "Bengali"),
    (r"[଀-୿]", "Odia"),
    (r"[ऀ-ॿ]", "Devanagari"),
]


def detect_script(text):
    for pattern, name in _SCRIPTS:
        if re.search(pattern, text or ""):
            return name
    return "Latin"


_HINGLISH_WORDS = {
    "hai", "hain", "nahi", "nahin", "kya", "kyu", "kyun", "kaise", "kaisa",
    "karun", "karu", "karna", "karni", "karo", "kar", "kare", "karein",
    "raha", "rahi", "rahe", "tha", "thi", "hoga", "hogi", "hua", "hui",
    "ka", "ki", "ke", "ko", "se", "mein", "mai", "mujhe", "mera", "meri",
    "mere", "hum", "humein", "aap", "aapko", "unka", "uska", "usne", "maine",
    "aaya", "aayi", "gaya", "gayi", "diya", "liya", "wapas", "paisa", "paise",
    "chahiye", "kitne", "kitna", "kab", "kahan", "kaun", "bhi", "abhi",
    "lekin", "par", "aur", "bhai", "yaar", "ghar", "mahine", "saal", "din",
}


def looks_like_hinglish(text):
    words = re.findall(r"[a-z]+", (text or "").lower())
    hits = sum(w in _HINGLISH_WORDS for w in words)
    return hits >= 2 or (words and hits / len(words) >= 0.3)


def detect_language(text, model_guess):
    script = detect_script(text)
    if script == "Devanagari":
        return "Hindi"
    if script != "Latin":
        return script
    if model_guess == "Hinglish" or looks_like_hinglish(text):
        return "Hinglish"
    return "English"


def resolve(choice, detected):
    choice = (choice or AUTO).replace(" (beta)", "")
    if choice in LANGUAGES:
        return choice
    return detected if detected in LANGUAGES else "English"


def instruction(language):
    return LANGUAGES.get(language, LANGUAGES["English"])["instruction"]
