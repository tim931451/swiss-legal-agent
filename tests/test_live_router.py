"""SW5 task 1: edge cases for the scope check against a real model. Skipped without LITELLM_API_KEY.

The expected areas are our own judgement of each case, not a source; adjust them if the team decides otherwise.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("LITELLM_API_KEY"), reason="needs LITELLM_API_KEY")

EDGE_CASES = [
    ("Ich bin im zweiten Lehrjahr. Wie viele Wochen Ferien stehen mir zu?", "arbeitsrecht"),
    ("Ich vermiete ein Zimmer meiner Mietwohnung unter. Muss mein Vermieter zustimmen?", "mietrecht"),
    ("Mein Vater ist gestorben. Wie wird das Erbe unter uns Geschwistern aufgeteilt?", "ausserhalb"),
    ("Welche Kündigungsfrist gilt in Deutschland nach dem BGB?", "ausserhalb"),
    ("Wie wird das Wetter morgen in Olten?", "ausserhalb"),
]


@pytest.mark.parametrize("question,expected", EDGE_CASES)
def test_router_edge_cases(question, expected):
    from lexgraph.agents.prompts import ROUTER_PROMPT
    from lexgraph.config import LLM_MODEL, make_llm

    verdict = make_llm(LLM_MODEL).invoke(ROUTER_PROMPT.format(question=question)).content.lower()
    area = "mietrecht" if "miet" in verdict else "arbeitsrecht" if "arbeit" in verdict else "ausserhalb"
    assert area == expected
