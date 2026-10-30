"""Output schema of the specialist agent (task T10).

The specialist answers as JSON with fixed fields. `parse_answer` reads that JSON, `render_answer` turns it into the
text shown to the user. If a model does not return valid JSON, the graph keeps the raw text (`structured` is None),
so a run never breaks because of formatting. This is the same JSON fallback that notebook 01, section 9 names for
models without reliable tool calling.
"""

import json
import re

FIELDS = ("sachverhalt", "rechtsfrage", "normen", "subsumtion", "ergebnis", "quellen")

# SW5 task 4: own schema field. Optional, so older answers without it still parse. The model fills it only when a
# fact is missing that decides the result (for a notice period, the year of service), otherwise null.
OPTIONAL_FIELDS = ("rueckfrage",)

# Field descriptions that go into the specialist prompt. They play the role of the pydantic `description` in the
# notebook: without them the model sees only the field name (see scripts/schema_description.py).
FIELD_DESCRIPTIONS = (
    "rueckfrage: eine kurze Frage an die Person, wenn eine Angabe fehlt, die das Ergebnis ändert "
    "(zum Beispiel das Dienstjahr bei einer Kündigungsfrist); sonst null."
)

SCHEMA_HINT = (
    '{"sachverhalt": "...", "rechtsfrage": "...", "normen": ["Art. 335c OR"], '
    '"subsumtion": "...", "ergebnis": "...", "quellen": ["OR-335c"], "rueckfrage": null}'
)

TEXT_FIELDS = ("sachverhalt", "rechtsfrage", "subsumtion", "ergebnis")
LIST_FIELDS = ("normen", "quellen")
_DECODER = json.JSONDecoder()


def _json_objects(text):
    """Every JSON object in the text, in order. T39: raw_decode instead of a greedy regex, so prose with braces
    before or after the answer, or a second object, no longer breaks parsing."""
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = _DECODER.raw_decode(text, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            yield obj


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_as_text(v) for v in value if v is not None).strip()
    return str(value).strip()


def _as_list(value):
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    return [str(v).strip() for v in items if v is not None and str(v).strip()]


def parse_answer(text):
    """Return the answer as a dict with all FIELDS, or None if the text holds no valid answer object.

    T39: the first object with all fields wins; text fields are cast to str, normen and quellen to lists of str,
    None becomes "" or [].
    """
    for data in _json_objects(text if isinstance(text, str) else ""):
        if not all(field in data for field in FIELDS):
            continue
        answer = {field: _as_text(data[field]) for field in TEXT_FIELDS}
        answer.update({field: _as_list(data[field]) for field in LIST_FIELDS})
        answer = {field: answer[field] for field in FIELDS}
        for field in OPTIONAL_FIELDS:
            value = _as_text(data.get(field))
            answer[field] = value or None
        return answer
    return None


def render_answer(answer):
    """Readable text for the user. Citations stay in the form 'Art. X OR', so the citation check can read them."""
    return (
        f"Sachverhalt: {answer['sachverhalt']}\n"
        f"Rechtsfrage: {answer['rechtsfrage']}\n"
        f"Normwahl: {', '.join(answer['normen'])}\n"
        f"Subsumtion: {answer['subsumtion']}\n"
        f"Ergebnis: {answer['ergebnis']}\n"
        f"Quellen: {', '.join(answer['quellen'])}"
        + (f"\nRückfrage: {answer['rueckfrage']}" if answer.get("rueckfrage") else "")
    )
