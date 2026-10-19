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
    answer = {field: data[field] for field in FIELDS}
    for field in OPTIONAL_FIELDS:
        value = data.get(field)
        answer[field] = value.strip() if isinstance(value, str) and value.strip() else None
    return answer


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
