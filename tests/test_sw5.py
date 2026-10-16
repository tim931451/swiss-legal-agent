"""SW5 tasks on our own use case: scope prompt, second tool, answer style. Offline, no key needed."""

import importlib.util
from pathlib import Path

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from lexgraph.agents.graph import build_graph
from lexgraph.agents.prompts import ANSWER_STYLE, ROUTER_PROMPT, SPECIALIST_PROMPT, SYSTEM_PROMPT

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
