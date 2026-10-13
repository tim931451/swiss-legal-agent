"""Input guards: jailbreak patterns, redaction of personal data (nDSG), off-topic pre-filter.

Source: notebook 05, sections 2 to 4. Building block: `input_guard(text)`.
Cheap, deterministic rules first. Questions outside employment and tenancy law are caught by the router.
"""

import re

JAILBREAK_PATTERNS = [
    r"ignor\w* (all|alle|previous|vorherige|deine)",
    r"vergiss (alle|deine) (anweisungen|regeln)",
    r"system ?prompt",
    r"du bist jetzt",
    r"act as|pretend to be|tu so als",
]

PII_PATTERNS = {
    "AHV": r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b",
    "IBAN": r"\bCH\d{2}(?:\s?[0-9A-Z]{4}){4}\s?[0-9A-Z]\b",
    "EMAIL": r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    "PHONE": r"(?:\+41|\b0)\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b",
}

LEGAL_HINTS = ["kündig", "miete", "vermiet", "arbeit", "lohn", "ferien", "vertrag", "frist", "art.", "or ", "chef",
               "wohnung", "mängel", "kaution", "entlass", "krank"]


def is_jailbreak(text):
    return any(re.search(p, text.lower()) for p in JAILBREAK_PATTERNS)


def redact(text):
    """Replace personal data with placeholders. Returns the clean text and what was found."""
    # TODO (T16): person names need a named-entity model (open point in notebook 05, section 3).
    found = []
    for label, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            found.append(label)
            text = re.sub(pattern, f"[{label}]", text)
    return text, found


def looks_legal(text):
    return any(h in text.lower() for h in LEGAL_HINTS)


def input_guard(text):
    """Return (allowed, cleaned_text, reason)."""
    if is_jailbreak(text):
        return False, text, "jailbreak"
    if not looks_legal(text):
        return False, text, "off_topic"
    cleaned, found = redact(text)
    return True, cleaned, f"redacted: {', '.join(found)}" if found else "ok"
