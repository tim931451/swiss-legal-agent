"""Retrieval: Reciprocal Rank Fusion and Hit@k with BM25 on the placeholder records. Source: notebook 02.

The index is built from ingest.SAMPLE (the paraphrases), not from data/or_articles.jsonl, so these tests stay
stable once T11 replaces the data file with the real Fedlex text.

T12: embeddings, cache and reranking are tested offline with a hashed bag-of-words backend and fake chat models.
"""

import logging
import os
import zlib

import numpy as np
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from lexgraph.rag import retrieval
from lexgraph.rag.ingest import SAMPLE


@pytest.fixture(autouse=True)
def placeholder_index():
    retrieval.build_index(SAMPLE)


class BagOfWords:
    """Fake embedding backend: hashed word counts, offline and deterministic. Records every batch it receives."""

    def __init__(self, dim=512):
        self.dim, self.batches = dim, []

    def embed_documents(self, texts):
        self.batches.append(list(texts))
        vectors = np.zeros((len(texts), self.dim))
        for row, text in enumerate(texts):
            for token in retrieval.tokenize(text):
                vectors[row, zlib.crc32(token.encode()) % self.dim] += 1
        return vectors.tolist()


@pytest.fixture
def fake_embeddings(monkeypatch, tmp_path):
    backend = BagOfWords()
    monkeypatch.setattr(retrieval, "make_embeddings", lambda model=None: retrieval.CachedEmbeddings(
        "fake", client=backend, cache_dir=tmp_path, profile={}))
    return backend


def ids(docs):
    return [d.metadata["id"] for d in docs]


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


# --- T12: offline tests for embeddings, cache, area filter and reranking -------------------------------------------


def test_hit_at_k_with_several_gold_articles():
    assert retrieval.hit_at_k(["OR-266c", "OR-266l"], ["OR-266l", "OR-266c"], 1)
    assert not retrieval.hit_at_k(["OR-253", "OR-266l"], ["OR-266c", "OR-266l"], 1)
    assert retrieval.hit_at_k(["OR-253", "OR-266l"], ["OR-266c", "OR-266l"], 2)


def test_embedding_cache_uses_prompts_and_sends_each_text_once(tmp_path, monkeypatch):
    backend = BagOfWords()
    profile = {"query": "query: ", "document": "passage: "}
    first = retrieval.CachedEmbeddings("fake", client=backend, cache_dir=tmp_path, profile=profile)
    docs = first.embed_documents(["Kündigung zur Unzeit", "Mängel der Mietsache"])
    first.embed_query("Kündigung bei Krankheit")
    assert backend.batches == [["passage: Kündigung zur Unzeit", "passage: Mängel der Mietsache"],
                               ["query: Kündigung bei Krankheit"]]
    assert first.requests == 2 and first.path.name == "embeddings-fake.npz"

    second = retrieval.CachedEmbeddings("fake", client=backend, cache_dir=tmp_path, profile=profile)
    assert second.embed_documents(["Mängel der Mietsache", "Kündigung zur Unzeit"]) == docs[::-1]
    second.embed_query("Kündigung bei Krankheit")
    assert second.requests == 0 and len(backend.batches) == 2  # everything came from the cache file

    monkeypatch.setattr(retrieval, "EMBED_BATCH", 2)
    second.embed_documents(["a", "b", "c", "a"])  # three new texts, a repeated text is sent once
    assert backend.batches[2:] == [["passage: a", "passage: b"], ["passage: c"]]


def test_both_proxy_embedding_models_have_model_card_prompts(tmp_path):
    from lexgraph.config import EMBED_MODEL, HARRIER_EMBED_MODEL, SWISS_EMBED_MODEL

    assert EMBED_MODEL in (SWISS_EMBED_MODEL, HARRIER_EMBED_MODEL)
    assert retrieval.EMBED_PROFILES[SWISS_EMBED_MODEL] == {"query": "query: ", "document": "passage: "}
    harrier = retrieval.CachedEmbeddings(HARRIER_EMBED_MODEL, client=BagOfWords(), cache_dir=tmp_path)
    assert harrier.profile["query"].startswith("Instruct: ") and harrier.profile["document"] == ""
    assert harrier.path.name == "embeddings-leoipulsar_harrier-0.6b_latest.npz"


def test_dense_and_hybrid_retrieval_offline(fake_embeddings):
    assert retrieval.dense_ids("Schimmel Mängel Herabsetzung des Mietzinses", k=1) == ["OR-259a"]
    assert ids(retrieval.retrieve("Schimmel in der Wohnung, Herabsetzung", k=2, mode="hybrid"))[0] == "OR-259a"
    requests = len(fake_embeddings.batches)
    retrieval.build_index(SAMPLE)  # rebuilt index: the article vectors come from the cache
    retrieval.dense_ids("Schimmel", k=1)
    assert [len(b) for b in fake_embeddings.batches[requests:]] == [1]  # only the new query


def test_area_filter_searches_within_one_area(fake_embeddings):
    for mode in ("bm25", "dense", "hybrid"):
        hits = retrieval.retrieve("Kündigung Frist Monat", k=6, mode=mode, area="mietrecht")
        assert hits and {d.metadata["area"] for d in hits} == {"mietrecht"}


def test_parse_ranking_is_robust():
    candidates = ["OR-335c", "OR-336c", "OR-337"]
    reply = 'Hier:\n```json\n{"ranking": ["or-337", "OR-999", "OR-337", "OR-335c"]}\n```'
    assert retrieval.parse_ranking(reply, candidates) == ["OR-337", "OR-335c", "OR-336c"]
    assert retrieval.parse_ranking("Keine Angabe.", candidates) == candidates
    assert retrieval.parse_ranking(None, candidates) == candidates


def test_rerank_llm_reorders_and_keeps_order_on_error(caplog):
    hits = [retrieval._ensure_index()["doc_by_id"][i] for i in ("OR-335c", "OR-336c", "OR-337")]
    llm = GenericFakeChatModel(messages=iter([AIMessage(content='{"ranking": ["OR-337", "OR-335c"]}')]))
    assert ids(retrieval.rerank_llm("Diebstahl im Betrieb", hits, llm=llm)) == ["OR-337", "OR-335c", "OR-336c"]

    class Down:
        def invoke(self, prompt):
            raise RuntimeError("proxy down")

    with caplog.at_level(logging.WARNING, logger="lexgraph.rag.retrieval"):
        assert retrieval.rerank_llm("Diebstahl", hits, llm=Down()) == hits
    assert "keeping the first-stage order" in caplog.text


def test_retrieve_reranks_only_when_switched_on(monkeypatch):
    monkeypatch.setattr(retrieval, "rerank_llm", lambda query, hits, llm=None: list(reversed(hits)))
    plain = ids(retrieval.retrieve("Kündigung Frist Monat", k=3, mode="bm25"))
    reranked = ids(retrieval.retrieve("Kündigung Frist Monat", k=3, mode="bm25", rerank=True))
    first_stage = retrieval.first_stage_ids("Kündigung Frist Monat", "bm25")[: retrieval.RERANK_CANDIDATES]
    assert plain == first_stage[:3] and reranked == list(reversed(first_stage))[:3]
