"""LLM-as-a-judge with a 100-point grid of weighted true/false criteria.

Source: notebook 06, section 4. The judge prompt stays in German.

T18 (4 Nov 2026): the five yes/no criteria of notebook 06 stay, but they carry points that add up to 100 instead of
counting equally. The judge only decides true or false per criterion; the points are added up here, so a verdict can
be re-weighted without a new model call. The judge sees the gold articles of the case and runs at temperature 0. The
parser accepts code fences, text around the JSON, "ja"/"nein" and criteria without the "criteria" wrapper; a missing
criterion counts as false and is listed in `missing`, a reply without any criterion raises ValueError.
"""

import json

from lexgraph.config import JUDGE_MODEL, make_llm

# name: (points, criterion). Reasons for the weights: docs/eval/judge/README.md.
CRITERIA = {
    "correct_norm": (20, "Die Antwort stützt sich auf mindestens einen der massgebenden Artikel."),
    "correct_result": (30, "Das Ergebnis stimmt inhaltlich mit der Musterlösung überein: gleiche Antwort auf die "
                           "gestellte Frage, gleiche Fristen, Zahlen und Rechtsfolgen."),
    "no_invented_sources": (20, "Jede genannte Quelle existiert: keine erfundenen Artikelnummern, keine erfundenen "
                                "Entscheide und kein ausländisches Recht (zum Beispiel BGB). Ob ein bestehender "
                                "Artikel des OR zur Frage passt, spielt hier keine Rolle; das prüft correct_norm."),
    "complete": (20, "Alle wesentlichen Voraussetzungen, Fristen und Formvorschriften aus der Musterlösung sind "
                     "erwähnt."),
    "clear_structure": (10, "Die Antwort ist klar gegliedert (Norm, Subsumtion, Ergebnis)."),
}
MAX_POINTS = sum(points for points, _ in CRITERIA.values())

JUDGE_PROMPT = (
    "Du bewertest die Antwort eines juristischen Assistenten zum Schweizer Arbeits- und Mietrecht.\n"
    "Vergleiche die Antwort mit der Musterlösung und den massgebenden Artikeln. Beurteile jedes Kriterium für sich "
    "mit true oder false. Ist ein Kriterium nur teilweise erfüllt, gilt false.\n"
    "Antworte nur mit JSON im Format {{\"criteria\": {{<name>: true|false}}, \"comment\": \"<ein Satz>\"}}.\n\n"
    "Kriterien:\n{criteria}\n\nFrage: {question}\n\nMassgebende Artikel: {gold}\n\n"
    "Musterlösung: {expected}\n\nAntwort: {answer}"
)

_TRUE = {"true", "ja", "yes", "wahr", "erfüllt", "1"}
_FALSE = {"false", "nein", "no", "falsch", "nicht erfüllt", "0"}


def score(criteria):
    """Points of the criteria that are met, 0 to 100."""
    return sum(points for name, (points, _) in CRITERIA.items() if criteria.get(name) is True)


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in _TRUE | _FALSE:
        return value.strip().lower() in _TRUE
    return None


def _json_objects(text):
    """Every JSON object in the text, outermost first, also inside code fences or between other text."""
    decoder, pos = json.JSONDecoder(), 0
    while (start := text.find("{", pos)) != -1:
        try:
            obj, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            pos = start + 1
            continue
        if isinstance(obj, dict):
            yield obj
        pos = end


def parse_judge(text):
    """Verdict from the judge reply: criteria (bool), score (0 to 100), comment and the criteria it left out."""
    for data in _json_objects(text or ""):
        raw = data["criteria"] if isinstance(data.get("criteria"), dict) else data
        if any(name in raw for name in CRITERIA):
            break
    else:
        raise ValueError(f"judge reply without criteria: {(text or '')[:200]!r}")
    values = {name: _as_bool(raw.get(name)) for name in CRITERIA}
    criteria = {name: value is True for name, value in values.items()}
    return {"criteria": criteria, "score": score(criteria), "comment": str(data.get("comment", "")),
            "missing": [name for name, value in values.items() if value is None]}


def cite(article_id):
    """OR-336c -> Art. 336c OR"""
    law, number = article_id.split("-", 1)
    return f"Art. {number} {law}"


def judge_prompt(case, answer):
    criteria_text = "\n".join(f"- {name}: {text}" for name, (_, text) in CRITERIA.items())
    return JUDGE_PROMPT.format(criteria=criteria_text, question=case["question"],
                               gold=", ".join(cite(g) for g in case["gold_articles"]),
                               expected=case["expected_answer"], answer=answer)


def judge_answer(case, answer, judge=None):
    """Let the judge model rate one answer. In the notebook `judge` is a global; here it is created on first call."""
    judge = judge or make_llm(JUDGE_MODEL, temperature=0)
    return parse_judge(judge.invoke(judge_prompt(case, answer)).content)
