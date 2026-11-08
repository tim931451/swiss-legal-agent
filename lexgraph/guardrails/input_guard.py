"""Input guards (T16): jailbreak patterns, redaction of personal data (nDSG), off-topic pre-filter, length limit.

Source: notebook 05, sections 2 to 4. Building block: `input_guard(text)`.
Own deterministic rules instead of a guardrail framework (decision 12 Oct 2026). In the graph the guard is the first
node, so a blocked input costs no model call and personal data never reaches a model. Off-topic questions are not
blocked there: the router decides, because a keyword list also misses legal questions in everyday words.
Known gaps: names without a title or cue word, obfuscation beyond invisible characters (leetspeak, spaced letters).
"""

import re
import unicodedata

MAX_CHARS = 4000  # a case fits easily; very long inputs are a typical carrier for injected instructions

INVISIBLE = re.compile(r"[­​-‏⁠﻿]")  # used to split trigger words: "ig​noriere"

# Matched on normalised lower-case text. Each rule needs an instruction word, so that "mein Chef ignoriert die
# Kündigungsfrist" or "du bist jetzt entlassen" stay allowed (tests/test_guardrails.py).
JAILBREAK_PATTERNS = [
    r"\bignorier(?:e|en sie)?\s+(?:\w+\s+){0,3}(?:anweisungen|instruktionen|regeln|vorgaben)\b",
    r"\bvergiss\s+(?:alle|deine|die|sämtliche)\s+(?:\w+\s+){0,2}(?:anweisungen|instruktionen|regeln|vorgaben)\b",
    r"\bvergiss alles\b",
    r"\bneue (?:anweisung|anweisungen|rolle|systemregeln)\b",
    r"\bdu bist (?:jetzt|nun|ab sofort|ab jetzt) (?:ein|eine|der|die) (?:\w+ )?(?:ki|bot|chatbot|assistent|modell)\b",
    r"\btu so,? als ob du\b",
    r"\bantworte\w* (?:mir )?ohne (?:einschränkungen|filter|zensur)\b",
    r"\b(?:zeig|gib|nenn|verrat)\w* (?:mir )?(?:deine|die) (?:internen |geheimen )?(?:anweisungen|instruktionen)\b",
    r"\b(?:ignore|disregard|forget)\s+(?:\w+\s+){0,3}(?:instructions|rules|prompts?|guidelines)\b",
    r"\byou are now\b",
    r"\bpretend (?:to be|you are)\b",
    r"\b(?:developer|god) mode\b|\bjailbreak\b|\bdo anything now\b",
    r"\bsystem ?prompt\b",
]

ROLE_NOUNS = (r"(?:Vermieter(?:in)?|Mieter(?:in)?|Arbeitgeber(?:in)?|Arbeitnehmer(?:in)?|Chef(?:in)?|"
              r"Anwält(?:in)?|Anwalt|Rechtsanwält(?:in)?|Rechtsanwalt|Doktor|Kollegin|Kollege|Nachbar(?:in)?|"
              r"Verwalter(?:in)?|Vorgesetzte[rn]?|Präsident(?:in)?|Direktor(?:in)?)")

# Order matters: AHV and IBAN before the phone number, the address before the name rules.
PII_PATTERNS = [
    ("EMAIL", r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", None),
    ("AHV", r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b", None),
    ("IBAN", r"\bCH\d{2}(?:\s?[0-9A-Z]{4}){4}\s?[0-9A-Z]\b", None),
    ("PHONE", r"(?:\+41|\b0041|\b0)\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b", None),
    # Street and number, but not "Arbeitsweg 45 Minuten".
    ("ADRESSE", r"\b[A-ZÄÖÜ][a-zäöüé]*(?:strasse|straße|gasse|weg|platz|allee|ring)\s+\d{1,4}(?!\d)"
                r"(?:\s?[a-zA-Z](?![a-zA-Z]))?(?!\s*(?i:min|km|std|stunden|franken|chf|tage|wochen|monate|jahre|%))",
     None),
    ("GEBURTSDATUM", r"\b((?i:geb\.|geboren(?: am)?|geburtsdatum:?))\s*\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}",
     r"\1 [GEBURTSDATUM]"),
    # Review Jack (30.10.): role nouns after a title ("Frau Vermieterin") are not names and stay.
    ("NAME", r"\b(Herr|Frau|Hr\.|Fr\.)\s+(?:Dr\.\s+)?(?!" + ROLE_NOUNS + r"\b)[A-ZÄÖÜ][a-zäöüéèà]+"
             r"(?:[- ][A-ZÄÖÜ][a-zäöüéèà]+)?", r"\1 [NAME]"),
    ("NAME", r"\b((?i:ich heisse|ich heiße|mein name ist))\s+[A-ZÄÖÜ]\w+(?:\s+[A-ZÄÖÜ]\w+)?", r"\1 [NAME]"),
]

LEGAL_HINTS = [
    "kündig", "miete", "mieter", "vermiet", "wohnung", "nebenkosten", "kaution", "mängel", "schimmel",
    "arbeit", "lohn", "ferien", "überstunden", "zeugnis", "probezeit", "entlass", "krank", "vertrag", "frist",
    "chef", "art.", "landlord", "tenant", "rent", "employer", "employee", "salary", "notice", "dismiss",
]


def normalize(text):
    """Lower case, unified Unicode forms, invisible characters removed and whitespace collapsed."""
    text = INVISIBLE.sub("", unicodedata.normalize("NFKC", text))
    return " ".join(text.lower().split())


def is_jailbreak(text):
    norm = normalize(text)
    return any(re.search(p, norm) for p in JAILBREAK_PATTERNS)


def redact(text):
    """Replace personal data with placeholders. Returns the clean text and the labels found, in order."""
    found = []
    for label, pattern, replacement in PII_PATTERNS:
        if re.search(pattern, text):
            if label not in found:
                found.append(label)
            text = re.sub(pattern, replacement or f"[{label}]", text)
    return text, found


def looks_legal(text):
    norm = normalize(text)
    return any(h in norm for h in LEGAL_HINTS) or re.search(r"\b(?:OR|ZGB)\b", text) is not None


def input_guard(text):
    """Return (allowed, cleaned_text, reason). The cleaned text is redacted in every case, also when blocked.

    Reasons: ok, redacted: <labels>, empty, too_long, jailbreak, off_topic.
    """
    cleaned, found = redact(text or "")
    if not cleaned.strip():
        return False, cleaned, "empty"
    if len(cleaned) > MAX_CHARS:
        return False, cleaned, "too_long"
    if is_jailbreak(cleaned):
        return False, cleaned, "jailbreak"
    if not looks_legal(cleaned):
        return False, cleaned, "off_topic"
    return True, cleaned, f"redacted: {', '.join(found)}" if found else "ok"
