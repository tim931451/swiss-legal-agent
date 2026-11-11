"""T15: the demo UI on the real graph with fake models. Offline, no keys."""

import json

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.checkpoint.memory import InMemorySaver

from lexgraph.agents.graph import HUMAN_REJECTION, build_graph
from lexgraph.ui import app

SOURCES = [{"id": "OR-336c", "title": "Kündigung zur Unzeit", "text": "..."}]
DRAFT = json.dumps({"sachverhalt": "Krank seit zwei Wochen.", "rechtsfrage": "Darf gekündigt werden?",
                    "normen": ["Art. 336c OR"], "subsumtion": "Sperrfrist läuft.",
                    "ergebnis": "Die Kündigung ist nichtig.", "quellen": ["OR-336c"], "rueckfrage": None},
                   ensure_ascii=False)


@pytest.fixture
def use_graph(monkeypatch):
    def install(messages):
        llm = GenericFakeChatModel(messages=iter(messages))
        graph = build_graph(llm, lambda q, a, k=3: SOURCES, checkpointer=InMemorySaver())
        monkeypatch.setattr(app, "get_graph", lambda: graph)
    return install


def paused(use_graph):
    use_graph(["arbeitsrecht", DRAFT, "REVISE: a", DRAFT, "REVISE: b", DRAFT, "REVISE: Frist fehlt"])
    return app.answer_case("Schwieriger Fall")


def test_result_comes_first_and_misplaced_text_is_dropped():
    text = app.format_answer({"sachverhalt": "Ergebnis: steht im falschen Feld", "rechtsfrage": "Frage?",
                              "normen": ["Art. 335c OR"], "subsumtion": "Subsumtion: Weil.",
                              "ergebnis": "Ergebnis: Zwei Monate."})
    assert text.startswith("**Ergebnis.** Zwei Monate.")
    assert "**Subsumtion.** Weil." in text and "falschen Feld" not in text and "Sachverhalt" not in text


def test_case_shows_answer_linked_sources_and_status(use_graph):
    use_graph(["arbeitsrecht", DRAFT, "OK"])
    answer, sources, status, panel, _, _, thread = app.answer_case("Ich bin krank und erhalte die Kündigung.")
    assert answer.startswith("**Ergebnis.** Die Kündigung ist nichtig.")
    assert "[OR-336c: Kündigung zur Unzeit](https://www.fedlex.admin.ch/" in sources
    assert "Arbeitsrecht" in status and "**Prüfrunden:** 0" in status and "bestanden" in status
    assert panel["visible"] is False and thread is None


def test_guard_block_makes_no_model_call(use_graph):
    use_graph([])
    answer, sources, status, *_ = app.answer_case("")
    assert "Beschreiben Sie bitte" in answer and sources == "Keine Quellen abgerufen." and "gestoppt" in status


def test_out_of_scope_shows_the_fixed_text(use_graph):
    use_graph(["out_of_scope"])
    answer, _, status, *_ = app.answer_case("Wie wird das Erbe aufgeteilt?")
    assert "ausserhalb" in answer and "Ausserhalb des Umfangs" in status and "Prüfrunden" not in status


def test_uncertain_case_opens_review_and_can_be_approved(use_graph):
    answer, _, status, panel, note, draft, thread = paused(use_graph)
    assert panel["visible"] is True and thread and "Prüfers:** Frist fehlt" in note and "Rechtsfrage:" in draft
    assert "Fachperson" in status and answer == app.PAUSED_ANSWER
    answer, _, status, panel, _, _, thread = app.approve(thread)
    assert answer.startswith("**Ergebnis.**") and "freigegeben" in status
    assert panel["visible"] is False and thread is None


def test_uncertain_case_can_be_edited_or_rejected(use_graph):
    *_, thread = paused(use_graph)
    assert app.edit(thread, "Korrigiert")[0] == "Korrigiert"
    *_, thread = paused(use_graph)
    assert app.reject(thread)[0] == HUMAN_REJECTION


def test_edited_answer_shows_the_result_first(use_graph):
    *_, thread = paused(use_graph)
    text = ("Sachverhalt: Krank.\nRechtsfrage: Gültig?\nNormwahl: Art. 336c OR\nSubsumtion: Sperrfrist.\n"
            "Ergebnis: Nichtig.\nQuellen: OR-336c")
    answer, _, status, *_ = app.edit(thread, text)
    assert answer.startswith("**Ergebnis.** Nichtig.") and "**Normwahl.** Art. 336c OR" in answer
    assert "Quellen" not in answer and "bearbeitet und freigegeben" in status


def test_edited_free_text_stays_as_typed():
    assert app.parse_rendered("Hinweis vorab\nErgebnis: X") is None
    assert app.parse_rendered("Sachverhalt: ohne Ergebnis") is None


def test_failure_shows_a_message_not_a_stack_trace(monkeypatch):
    def boom():
        raise KeyError("LITELLM_API_KEY")
    monkeypatch.setattr(app, "get_graph", boom)
    answer, _, status, *_ = app.answer_case("Fall")
    assert "nicht bearbeiten" in answer and status == "Technischer Fehler: KeyError"


def test_decision_without_open_case():
    assert "Kein Entwurf" in app.approve(None)[0]


def test_graph_uses_the_demo_setup(monkeypatch):
    seen = {}
    monkeypatch.setattr(app, "_cache", {})
    monkeypatch.setattr(app, "make_llm", lambda model: seen.setdefault("model", model))
    monkeypatch.setattr(app, "make_embedding_retriever", lambda: "embedding-retriever")
    monkeypatch.setattr(app, "build_graph", lambda llm, retrieve, **kw: seen.update(retrieve=retrieve, **kw) or "graph")
    assert app.get_graph() == "graph"
    assert seen["model"] == app.DEMO_MODEL == app.APERTUS_MODEL and seen["retrieve"] == "embedding-retriever"
    assert isinstance(seen["checkpointer"], InMemorySaver) and "lookup" not in seen
