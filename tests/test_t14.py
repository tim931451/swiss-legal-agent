"""T14: router, two specialist agents, reviewer loop (at most 2 rounds) and human in the loop. Offline."""

import json

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from lexgraph.agents.graph import HUMAN_REJECTION, build_graph

SOURCES = [{"id": "OR-259a", "title": "Mängel", "text": "..."}]


class Spy(GenericFakeChatModel):
    prompts: list = []

    def invoke(self, prompt, *args, **kwargs):
        self.prompts.append(prompt)
        return super().invoke(prompt, *args, **kwargs)


def test_graph_has_two_specialists():
    graph = build_graph(GenericFakeChatModel(messages=iter([])), lambda q, a, k=3: SOURCES)
    assert {"specialist_arbeitsrecht", "specialist_mietrecht"} <= set(graph.get_graph().nodes)


def test_each_area_reaches_its_own_specialist_with_its_guidance():
    for area, expected, other in [("mietrecht", "Art. 266l OR", "Art. 335b OR"),
                                  ("arbeitsrecht", "Art. 335b OR", "Art. 266l OR")]:
        llm = Spy(messages=iter([area, "Entwurf", "OK"]), prompts=[])
        seen_area = []
        run = build_graph(llm, lambda q, a, k=3: seen_area.append(a) or SOURCES).invoke({"question": "Fall"})
        specialist_prompt = llm.prompts[1]
        assert run["area"] == area and seen_area == [area]
        assert expected in specialist_prompt and other not in specialist_prompt


def test_revision_goes_back_to_the_same_specialist():
    llm = Spy(messages=iter(["mietrecht", "E1", "REVISE: Frist fehlt", "E2", "OK"]), prompts=[])
    run = build_graph(llm, lambda q, a, k=3: SOURCES).invoke({"question": "Wohnung kündigen"})
    assert run["answer"] == "E2" and run["revisions"] == 1
    assert "Art. 266l OR" in llm.prompts[3] and "Kritik am letzten Entwurf: REVISE: Frist fehlt" in llm.prompts[3]


def rejected_three_times():
    return GenericFakeChatModel(messages=iter(["arbeitsrecht", "E1", "REVISE: a", "E2", "REVISE: b", "E3",
                                               "REVISE: c"]))


def test_human_in_the_loop_pauses_and_resumes_with_edit():
    graph = build_graph(rejected_three_times(), lambda q, a, k=3: SOURCES, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "case-1"}}
    paused = graph.invoke({"question": "Schwieriger Fall"}, config)
    payload = paused["__interrupt__"][0].value
    assert payload["draft"] == "E3" and payload["review"] == "REVISE: c" and "answer" not in paused
    done = graph.invoke(Command(resume={"action": "edit", "text": "Korrigierte Antwort"}), config)
    assert done["answer"] == "Korrigierte Antwort" and done["human_decision"] == "edited" and done["needs_human"]


def test_human_in_the_loop_approve_and_reject():
    for decision, answer in [({"action": "approve"}, "E3"), ({"action": "reject"}, HUMAN_REJECTION),
                             ({"action": "edit", "text": "  "}, HUMAN_REJECTION)]:
        graph = build_graph(rejected_three_times(), lambda q, a, k=3: SOURCES, checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": json.dumps(decision)}}
        graph.invoke({"question": "Schwieriger Fall"}, config)
        assert graph.invoke(Command(resume=decision), config)["answer"] == answer


def test_without_checkpointer_no_pause():
    run = build_graph(rejected_three_times(), lambda q, a, k=3: SOURCES).invoke({"question": "Schwieriger Fall"})
    assert run["needs_human"] and "An eine Fachperson übergeben" in run["answer"] and "__interrupt__" not in run
