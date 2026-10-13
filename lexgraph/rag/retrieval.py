"""Hybrid retrieval (dense + BM25 with Reciprocal Rank Fusion), optional reranking and Hit@k.

Source: notebook 02, sections 4 to 7. Building block: `retrieve(query, k, mode)`.

Differences to the notebook: there the index is built at module level. Here it is built lazily on first use
(`build_index` and `_vectorstore` are repository glue), so that importing this module needs no key, no
network and no model download.
"""

import os
import re

from rank_bm25 import BM25Okapi

from lexgraph.config import EMBED_MODEL, LLM_BASE_URL
from lexgraph.rag.ingest import load_articles, to_documents

EMBEDDING_BACKEND = "proxy"  # "proxy" or "local" (sentence-transformers, no key needed)
USE_RERANKER = False  # cross-encoder reranking, notebook 02 section 6

# Retrieval test cases from notebook 02, section 7. The final test set lives in data/testset.jsonl.
RETRIEVAL_CASES = [
    ("Wie lange ist die Kündigungsfrist im dritten Dienstjahr?", "OR-335c"),
    ("Darf der Arbeitgeber kündigen, während ich krank bin?", "OR-336c"),
    ("Fristlose Entlassung nach Diebstahl im Betrieb", "OR-337"),
    ("Mieter zahlt die Miete nicht, was kann der Vermieter tun?", "OR-257d"),
    ("Schimmel in der Wohnung, darf ich weniger Miete zahlen?", "OR-259a"),
    ("Mit welcher Frist kann ich meine Wohnung kündigen?", "OR-266c"),
]

_index = {}  # docs, bm25, doc_by_id, doc_ids, vectorstore (filled lazily)
_cross_encoder = None


def tokenize(text):
    return re.findall(r"\w+", text.lower())


def build_index(records):
    """Repository glue: (re)build the in-memory BM25 index from article records. The dense index follows lazily."""
    docs = to_documents(records)
    _index.clear()
    _index.update(
        docs=docs,
        bm25=BM25Okapi([tokenize(d.page_content) for d in docs]),
        doc_by_id={d.metadata["id"]: d for d in docs},
        doc_ids=[d.metadata["id"] for d in docs],
    )


def _ensure_index():
    if not _index:
        build_index(load_articles())
    return _index


def _vectorstore():
    """Repository glue: build the FAISS index on first dense query (notebook 02, section 4)."""
    index = _ensure_index()
    if "vectorstore" not in index:
        from langchain_community.vectorstores import FAISS

        if EMBEDDING_BACKEND == "proxy":
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings(
                model=EMBED_MODEL,
                base_url=LLM_BASE_URL,
                api_key=os.environ["LITELLM_API_KEY"],
                check_embedding_ctx_length=False,  # needed for non-OpenAI models
            )
        else:
            from langchain_huggingface import HuggingFaceEmbeddings

            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        # TODO (T12): load the saved index from index/faiss_or (vectorstore.save_local in notebook 02, section 8)
        # instead of rebuilding it on every start.
        index["vectorstore"] = FAISS.from_documents(index["docs"], embeddings)
    return index["vectorstore"]


def bm25_ids(query, k=10):
    index = _ensure_index()
    scores = index["bm25"].get_scores(tokenize(query))
    ranked = sorted(range(len(index["docs"])), key=lambda i: scores[i], reverse=True)
    return [index["doc_ids"][i] for i in ranked[:k] if scores[i] > 0]


def rrf(rankings, k=60):
    """Reciprocal Rank Fusion of several ranked id lists."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


def dense_ids(query, k=10):
    return [d.metadata["id"] for d in _vectorstore().similarity_search(query, k=k)]


def retrieve(query, k=4, mode="hybrid"):
    """Return the top-k articles as Documents. mode: 'dense', 'bm25' or 'hybrid'."""
    if mode == "dense":
        ids = dense_ids(query)
    elif mode == "bm25":
        ids = bm25_ids(query)
    else:
        ids = rrf([dense_ids(query), bm25_ids(query)])
    hits = [_ensure_index()["doc_by_id"][i] for i in ids]
    if USE_RERANKER:
        hits = rerank(query, hits)
    return hits[:k]


def rerank(query, hits):
    """Cross-encoder reranking of the top candidates (notebook 02, section 6). The model loads on first use."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        _cross_encoder = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    scores = _cross_encoder.predict([(query, d.page_content) for d in hits])
    return [d for _, d in sorted(zip(scores, hits), key=lambda pair: pair[0], reverse=True)]


def hit_at_k(ranked_ids, gold_id, k):
    return gold_id in ranked_ids[:k]


def evaluate_retrieval(search, k=3, cases=RETRIEVAL_CASES):
    hits = [hit_at_k(search(q), gold, k) for q, gold in cases]
    return sum(hits) / len(hits)
