"""Output schema of the specialist (T10). Offline, no key needed."""

import json

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from lexgraph.agents.graph import build_graph
from lexgraph.agents.schema import FIELDS, parse_answer, render_answer
from lexgraph.guardrails.citation_check import citation_check

ANSWER = {
    "sachverhalt": "Arbeitnehmerin im dritten Dienstjahr, kein Vertrag zur Frist.",
    "rechtsfrage": "Welche Kündigungsfrist gilt?",
    "normen": ["Art. 335c OR"],
    "subsumtion": "Im zweiten bis neunten Dienstjahr gilt eine Frist von zwei Monaten.",
    "ergebnis": "Zwei Monate auf Ende eines Monats.",
    "quellen": ["OR-335c"],
}


def test_parse_answer_reads_json_inside_text():
    parsed = parse_answer("Hier die Antwort:\n```json\n" + json.dumps(ANSWER, ensure_ascii=False) + "\n```")
    assert parsed == {**ANSWER, "rueckfrage": None}


def test_parse_answer_rejects_free_text_and_missing_fields():
    assert parse_answer("Entwurf 1") is None
    assert parse_answer(json.dumps({"ergebnis": "x"})) is None


def test_parse_answer_with_braces_and_two_objects_around_the_answer():
    """T39: the old greedy regex took everything from the first { to the last } and failed here."""
    text = ('Vorbemerkung {siehe unten}. ' + json.dumps({"hinweis": "kein Antwortobjekt"}) + "\n"
            + json.dumps(ANSWER, ensure_ascii=False) + "\nNachtrag {Ende}")
    assert parse_answer(text) == {**ANSWER, "rueckfrage": None}


def test_parse_answer_casts_types_and_catches_none():
    """T39: str cast for text fields, lists of str for normen and quellen, None becomes empty."""
    raw = {**ANSWER, "ergebnis": 2, "subsumtion": ["Satz 1.", "Satz 2."], "normen": None,
           "quellen": "OR-335c", "rueckfrage": "  "}
    parsed = parse_answer(json.dumps(raw))
    assert parsed["ergebnis"] == "2" and parsed["subsumtion"] == "Satz 1. Satz 2."
    assert parsed["normen"] == [] and parsed["quellen"] == ["OR-335c"] and parsed["rueckfrage"] is None
    assert render_answer(parsed)  # renders without a TypeError
    assert parse_answer(None) is None


def test_rendered_answer_passes_citation_check():
    text = render_answer(ANSWER)
    assert all(f.capitalize() in text or f == "normen" for f in FIELDS)
    assert citation_check(text, ["OR-335c"])["ok"]


def test_graph_keeps_structured_answer():
    llm = GenericFakeChatModel(messages=iter(["arbeitsrecht", json.dumps(ANSWER, ensure_ascii=False), "OK"]))
    sources = [{"id": "OR-335c", "title": "Kündigungsfristen", "text": "..."}]
    run = build_graph(llm, lambda q, a, k=3: sources).invoke({"question": "Kündigungsfrist im dritten Dienstjahr?"})
    assert run["structured"] == {**ANSWER, "rueckfrage": None} and "Normwahl: Art. 335c OR" in run["answer"]
