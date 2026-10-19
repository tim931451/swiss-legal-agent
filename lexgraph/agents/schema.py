"""Output schema of the specialist agent (task T10).

The specialist answers as JSON with fixed fields. `parse_answer` reads that JSON, `render_answer` turns it into the
text shown to the user. If a model does not return valid JSON, the graph keeps the raw text (`structured` is None),
so a run never breaks because of formatting. This is the same JSON fallback that notebook 01, section 9 names for
models without reliable tool calling.
"""

import json
import re

FIELDS = ("sachverhalt", "rechtsfrage", "normen", "subsumtion", "ergebnis", "quellen")

SCHEMA_HINT = (
    '{"sachverhalt": "...", "rechtsfrage": "...", "normen": ["Art. 335c OR"], '
    '"subsumtion": "...", "ergebnis": "...", "quellen": ["OR-335c"]}'
)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_answer(text):
    """Return the answer as a dict with all FIELDS, or None if the text holds no valid answer object."""
    match = _JSON_BLOCK.search(text or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not all(field in data for field in FIELDS):
        return None
    for field in ("normen", "quellen"):
        if isinstance(data[field], str):
            data[field] = [data[field]]
    return {field: data[field] for field in FIELDS}


def render_answer(answer):
    """Readable text for the user. Citations stay in the form 'Art. X OR', so the citation check can read them."""
    return (
        f"Sachverhalt: {answer['sachverhalt']}\n"
        f"Rechtsfrage: {answer['rechtsfrage']}\n"
        f"Normwahl: {', '.join(answer['normen'])}\n"
        f"Subsumtion: {answer['subsumtion']}\n"
        f"Ergebnis: {answer['ergebnis']}\n"
        f"Quellen: {', '.join(answer['quellen'])}"
    )
