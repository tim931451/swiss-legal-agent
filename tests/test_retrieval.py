"""Retrieval: Reciprocal Rank Fusion and Hit@k with BM25 on the placeholder records. Source: notebook 02.

The index is built from ingest.SAMPLE (the paraphrases), not from data/or_articles.jsonl, so these tests stay
stable once T11 replaces the data file with the real Fedlex text.
"""

import os

import pytest

from lexgraph.rag import retrieval
from lexgraph.rag.ingest import SAMPLE


@pytest.fixture(autouse=True)
def placeholder_index():
    retrieval.build_index(SAMPLE)


def test_rrf_fuses_rankings():
    # notebook 02, section 5: rrf([["A", "B", "C"], ["C", "A"]])
    # A: 1/61 + 1/62, C: 1/63 + 1/61, B: 1/62
    assert retrieval.rrf([["A", "B", "C"], ["C", "A"]]) == ["A", "C", "B"]


def test_hit_at_k():
    assert retrieval.hit_at_k(["OR-336c", "OR-337"], "OR-337", 2)
    assert not retrieval.hit_at_k(["OR-336c", "OR-337"], "OR-337", 1)


def test_bm25_hit_at_3_on_placeholders():
    # Baseline measured on the paraphrases: 5 of 6 cases. BM25 finds nothing for
    # "Mit welcher Frist kann ich meine Wohnung kündigen?" (OR-266c): no stemming (Wohnung vs. Wohnungen) and
    # the other terms occur in at least half of the six records, so their BM25 IDF is 0.
    assert retrieval.evaluate_retrieval(retrieval.bm25_ids, k=3) >= 5 / 6


@pytest.mark.skipif(not os.environ.get("LITELLM_API_KEY"), reason="needs LITELLM_API_KEY for proxy embeddings")
@pytest.mark.parametrize("mode", ["dense", "hybrid"])
def test_dense_and_hybrid_hit_at_k(mode):
    # notebook 02, section 7: Hit@1 and Hit@3 per mode. No threshold yet (decision log open).
    def search(q):
        return [d.metadata["id"] for d in retrieval.retrieve(q, 10, mode)]

    for k in (1, 3):
        assert 0.0 <= retrieval.evaluate_retrieval(search, k) <= 1.0
