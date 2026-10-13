"""One real case end to end (T10). Skipped without LITELLM_API_KEY, so CI stays offline."""

import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("LITELLM_API_KEY"), reason="needs LITELLM_API_KEY")


def test_employment_case_runs_end_to_end():
    from lexgraph.agents.graph import build_graph, make_keyword_retriever
    from lexgraph.config import LLM_MODEL, make_llm
    from lexgraph.rag.ingest import load_articles
    from scripts.run_case import CASES, run

    result = run(CASES[0], build_graph(make_llm(LLM_MODEL), make_keyword_retriever(load_articles())))
    assert result["area"] == "arbeitsrecht"
    assert "OR-335c" in result["sources"]
    assert result["answer"]
