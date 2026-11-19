"""SW5 tasks on our own use case: scope prompt, second tool, answer style, schema field, rejection, tokens. Offline."""

import importlib.util
import json
from pathlib import Path

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from lexgraph.agents.graph import FIXED_REJECTION, build_graph
from lexgraph.agents.prompts import ANSWER_STYLE, REJECT_PROMPT, ROUTER_PROMPT, SPECIALIST_PROMPT, SYSTEM_PROMPT
from lexgraph.agents.schema import parse_answer, render_answer
from lexgraph.eval.tokens import CountingLLM

SERVER = Path(__file__).resolve().parent.parent / "mcp_server" / "fedlex_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("fedlex_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_router_prompt_names_scope_and_format():
    text = ROUTER_PROMPT.format(question="Darf mein Vermieter die Miete erhöhen?")
    assert "319 bis 362 OR" in text and "253 bis 273c OR" in text
    assert "'arbeitsrecht', 'mietrecht' oder 'ausserhalb'" in text


def test_router_reply_mietrecht_is_routed():
    llm = GenericFakeChatModel(messages=iter(["mietrecht", "Entwurf", "OK"]))
    run = build_graph(llm, lambda q, a, k=3: [{"id": "OR-259a", "title": "Mängel", "text": "..."}]).invoke(
        {"question": "Schimmel in der Wohnung"})
    assert run["area"] == "mietrecht"


def test_answer_style_in_both_prompts():
    assert ANSWER_STYLE in SYSTEM_PROMPT and ANSWER_STYLE in SPECIALIST_PROMPT


def test_notice_period_table():
    server = load_server()
    assert server.notice_period(1)["months"] == 1
    assert server.notice_period(2)["months"] == 2 and server.notice_period(9)["months"] == 2
    assert server.notice_period(10)["months"] == 3 and server.notice_period(25)["months"] == 3
    assert server.notice_period(0)["found"] is False
    assert server.notice_period(5)["source"] == "Art. 335c Abs. 1 OR"


ANSWER = {"sachverhalt": "Kündigung ohne Angabe zum Dienstjahr.", "rechtsfrage": "Welche Frist gilt?",
          "normen": ["Art. 335c OR"], "subsumtion": "Die Frist hängt vom Dienstjahr ab.",
          "ergebnis": "Ein bis drei Monate auf Ende eines Monats.", "quellen": ["OR-335c"]}


def test_schema_field_rueckfrage_is_optional_and_rendered():
    assert parse_answer(json.dumps(ANSWER))["rueckfrage"] is None
    asked = parse_answer(json.dumps({**ANSWER, "rueckfrage": "In welchem Dienstjahr sind Sie?"}))
    assert asked["rueckfrage"] == "In welchem Dienstjahr sind Sie?"
    assert "Rückfrage: In welchem Dienstjahr" in render_answer(asked)
    assert "Rückfrage" not in render_answer(parse_answer(json.dumps({**ANSWER, "rueckfrage": "  "})))


def test_field_description_reaches_the_prompt_and_can_be_left_out():
    seen = []

    class Spy(GenericFakeChatModel):
        def invoke(self, prompt, *args, **kwargs):
            seen.append(prompt)
            return super().invoke(prompt, *args, **kwargs)

    for descriptions in (None, ""):
        seen.clear()
        llm = Spy(messages=iter(["arbeitsrecht", json.dumps(ANSWER), "OK"]))
        kwargs = {} if descriptions is None else {"field_descriptions": descriptions}
        build_graph(llm, lambda q, a, k=3: [{"id": "OR-335c", "title": "t", "text": "..."}], **kwargs).invoke(
            {"question": "Welche Kündigungsfrist?"})
        assert ("Dienstjahr bei einer Kündigungsfrist" in seen[1]) is (descriptions is None)


def test_rejection_fixed_by_default_and_by_model_on_request():
    fixed = build_graph(GenericFakeChatModel(messages=iter(["ausserhalb"])), lambda q, a, k=3: []).invoke(
        {"question": "Erbrecht?"})
    assert fixed["answer"] == FIXED_REJECTION
    llm = GenericFakeChatModel(messages=iter(["ausserhalb", "Dafür bin ich nicht zuständig."]))
    model = build_graph(llm, lambda q, a, k=3: [], reject_with_model=True).invoke({"question": "Erbrecht?"})
    assert model["answer"] == "Dafür bin ich nicht zuständig."
    assert "nenne keine Gesetzesartikel" in REJECT_PROMPT


def test_counting_llm_records_path_and_tokens():
    from langchain_core.messages import AIMessage

    class Fake:
        def __init__(self, replies):
            self.replies = iter(replies)

        def invoke(self, prompt):
            return AIMessage(content=next(self.replies),
                             usage_metadata={"input_tokens": 100, "output_tokens": 10, "total_tokens": 110})

    llm = CountingLLM(Fake(["ausserhalb", "Abgelehnt."]))
    build_graph(llm, lambda q, a, k=3: [], reject_with_model=True).invoke({"question": "Erbrecht?"})
    assert llm.summary() == {"model_calls": 2, "input_tokens": 200, "output_tokens": 20, "total_tokens": 220,
                             "path": ["router", "out_of_scope"]}


def test_reviewer_prompt_limits_revise_to_errors():
    # Issue #32: no "strict" review; a missing follow-up question alone is no reason to revise.
    from lexgraph.agents.prompts import REVIEWER_PROMPT
    text = REVIEWER_PROMPT.format(sources="[OR-336c] ...", question="Fall", draft="Entwurf")
    assert "streng" not in text and "Fehlt etwas Wesentliches" not in text
    assert "fehlende Rückfrage" in text and "jede Frist, Zahl, Form" in text
    assert "'OK'" in text and "'REVISE: " in text
