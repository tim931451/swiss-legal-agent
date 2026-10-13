"""LLM-as-a-judge with yes/no criteria. The score is the share of criteria met, 0 to 100.

Source: notebook 06, section 4. The judge prompt stays in German.
"""

import json
import re

from lexgraph.config import JUDGE_MODEL, make_llm

CRITERIA = {
    "correct_norm": "Die Antwort stützt sich auf die richtige Gesetzesbestimmung.",
    "correct_result": "Das Ergebnis stimmt inhaltlich mit der Musterlösung überein.",
    "no_invented_sources": "Die Antwort nennt keine erfundenen Artikel oder Entscheide.",
    "complete": "Wesentliche Voraussetzungen und Fristen aus der Musterlösung sind erwähnt.",
    "clear_structure": "Die Antwort ist klar gegliedert (Norm, Subsumtion, Ergebnis).",
}

JUDGE_PROMPT = (
    "Du bewertest die Antwort eines juristischen Assistenten. Beurteile jedes Kriterium mit true oder false.\n"
    "Antworte nur mit JSON im Format {{\"criteria\": {{<name>: true|false}}, \"comment\": \"<ein Satz>\"}}.\n\n"
    "Kriterien:\n{criteria}\n\nFrage: {question}\n\nMusterlösung: {expected}\n\nAntwort: {answer}"
)


def parse_judge(text):
    """Extract the JSON object from the judge reply, robust to extra text around it."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    data = json.loads(match.group(0)) if match else {}
    criteria = {name: bool(data.get("criteria", {}).get(name, False)) for name in CRITERIA}
    return {"criteria": criteria, "score": round(100 * sum(criteria.values()) / len(criteria)),
            "comment": data.get("comment", "")}


def judge_answer(case, answer, judge=None):
    """Let the judge model rate one answer. In the notebook `judge` is a global; here it is created on first call."""
    judge = judge or make_llm(JUDGE_MODEL)
    criteria_text = "\n".join(f"- {name}: {text}" for name, text in CRITERIA.items())
    reply = judge.invoke(JUDGE_PROMPT.format(
        criteria=criteria_text, question=case["question"], expected=case["expected_answer"], answer=answer,
    )).content
    return parse_judge(reply)
