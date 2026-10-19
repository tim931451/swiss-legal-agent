"""Live check of task T08: every candidate model must return a tool call. Skipped without both keys."""

import os

import pytest
from langchain_core.tools import tool

from lexgraph.config import CANDIDATE_MODELS, make_llm

pytestmark = pytest.mark.skipif(
    not (os.environ.get("LITELLM_API_KEY") and os.environ.get("SWISSAI_API_KEY")), reason="needs both API keys"
)


@tool
def get_article(law: str, article: str) -> str:
    """Return the text of one article of Swiss federal law, for example law='OR', article='335c'."""
    return f"(stub) text of Art. {article} {law}"


@pytest.mark.parametrize("model", CANDIDATE_MODELS)
def test_tool_calling(model):
    msg = make_llm(model).bind_tools([get_article]).invoke("Was steht in Art. 335c OR? Benutze das Tool.")
    assert msg.tool_calls and msg.tool_calls[0]["args"] == {"law": "OR", "article": "335c"}
