"""Hybrid retrieval (dense + BM25 with Reciprocal Rank Fusion), optional reranking and Hit@k.

Source: notebook 02, sections 4 to 7. Building block: `retrieve(query, k, mode)`.

Differences to the notebook: there the index is built at module level. Here it is built lazily on first use
(`build_index` and `_vectorstore` are repository glue), so that importing this module needs no key, no
network and no model download.

T12 (4 Nov 2026):
- Embeddings from the FHNW proxy get the query and document prompts of their model cards (`EMBED_PROFILES`).
- Every vector is cached in index/ (gitignored), keyed by model and text. Rebuilding the index or repeating a Hit@k
  run sends no embedding request for texts that were embedded before.
- The proxy offers no reranker model (/v1/model/info lists chat, embedding and evaluation models only), so
  reranking is listwise by a chat model (`RERANKER = "llm"`). The local cross-encoder of notebook 02 stays an option.
- BM25 stays the fallback: the MCP server falls back to it when the dense search fails, and a failed rerank call
  keeps the order of the first stage.
"""

import hashlib
import logging
import os
import re
from pathlib import Path

import numpy as np
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25Okapi

from lexgraph.config import (
    EMBED_MODEL,
    HARRIER_EMBED_MODEL,
    LLM_BASE_URL,
    RERANK_MODEL,
    SWISS_EMBED_MODEL,
    make_llm,
)
from lexgraph.rag.ingest import REPO_ROOT, load_articles, to_documents

log = logging.getLogger(__name__)

EMBEDDING_BACKEND = "proxy"  # "proxy" or "local" (sentence-transformers, no key needed)
USE_RERANKER = False  # rerank the first-stage candidates before cutting to k (notebook 02, section 6)
RERANKER = "llm"  # "llm": listwise by RERANK_MODEL on the proxy (T12); "cross-encoder": local model of notebook 02
RERANK_CANDIDATES = 10  # first-stage hits the reranker sees
RERANK_MAX_CHARS = 1500  # article text per candidate in the rerank prompt (208 of 216 articles are shorter)
CACHE_DIR = REPO_ROOT / "index"  # gitignored; embedding cache, one file per model
EMBED_BATCH = 32  # texts per embedding request

EMBED_PROFILES = {  # prompts the model cards prescribe for retrieval, put in front of the text before embedding
    # andreasmartin/apertus-v1.1-swiss-embed-0.4b-bidir, config_sentence_transformers.json: "query: ", "passage: ".
    SWISS_EMBED_MODEL: {"query": "query: ", "document": "passage: "},
    # Ollama build of microsoft/harrier-oss-v1-0.6b (name and dimension 1024): an instruction for queries only, the
    # prompt "web_search_query" of the model card.
    HARRIER_EMBED_MODEL: {"query": "Instruct: Given a web search query, retrieve relevant passages that answer the "
                                   "query\nQuery: ", "document": ""},
}

# Retrieval test cases from notebook 02, section 7. The final test set lives in data/testset.jsonl.
RETRIEVAL_CASES = [
    ("Wie lange ist die Kündigungsfrist im dritten Dienstjahr?", "OR-335c"),
    ("Darf der Arbeitgeber kündigen, während ich krank bin?", "OR-336c"),
    ("Fristlose Entlassung nach Diebstahl im Betrieb", "OR-337"),
    ("Mieter zahlt die Miete nicht, was kann der Vermieter tun?", "OR-257d"),
    ("Schimmel in der Wohnung, darf ich weniger Miete zahlen?", "OR-259a"),
    ("Mit welcher Frist kann ich meine Wohnung kündigen?", "OR-266c"),
]

_index = {}  # docs, bm25, doc_by_id, doc_ids, vectorstores per embedding model (filled lazily)
_cross_encoder = None


def tokenize(text):
    return re.findall(r"\w+", text.lower())


# --- Embeddings with model-card prompts and a disk cache (T12) ---------------------------------------------------


def _cache_key(model, text):
    return hashlib.sha256(f"{model}\n{text}".encode()).hexdigest()


def _proxy_client(model):
    """OpenAI-compatible embeddings from the FHNW proxy (notebook 02, section 4)."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=model,
        base_url=LLM_BASE_URL,
        api_key=os.environ["LITELLM_API_KEY"],
        check_embedding_ctx_length=False,  # needed for non-OpenAI models
        # The openai client always sends encoding_format; the Ollama backend of the Harrier model rejects it with
        # error 400 (checked 4 Nov 2026). drop_params tells LiteLLM to drop parameters the backend does not support.
        model_kwargs={"extra_body": {"drop_params": True}},
    )


class CachedEmbeddings(Embeddings):
    """Embeddings with the prompts of the model card and a disk cache (T12).

    The cache stores the vector of the backend per (model, prompt + text), in index/embeddings-<model>.npz. Only texts
    that are not in the cache go to the backend, in batches of EMBED_BATCH. `requests` counts the requests sent.
    """

    def __init__(self, model=EMBED_MODEL, client=None, cache_dir=None, profile=None):
        self.model = model
        self.profile = EMBED_PROFILES.get(model, {}) if profile is None else profile
        self.client = client  # anything with embed_documents(texts); the proxy client is created on the first miss
        slug = re.sub(r"[^A-Za-z0-9.-]+", "_", model)
        self.path = Path(cache_dir or CACHE_DIR) / f"embeddings-{slug}.npz"
        self.cache = self._load()
        self.requests = 0

    def _load(self):
        if not self.path.exists():
            return {}
        with np.load(self.path, allow_pickle=False) as data:
            return dict(zip(data["keys"].tolist(), data["vectors"]))

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = list(self.cache)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "wb") as f:  # a file object keeps np.savez from appending .npz to the name
            np.savez(f, keys=np.array(keys), vectors=np.stack([self.cache[k] for k in keys]))
        os.replace(tmp, self.path)

    def _raw(self, texts):
        missing = [t for t in dict.fromkeys(texts) if _cache_key(self.model, t) not in self.cache]
        if missing:
            self.client = self.client or _proxy_client(self.model)
            for start in range(0, len(missing), EMBED_BATCH):
                batch = missing[start:start + EMBED_BATCH]
                self.requests += 1
                for text, vector in zip(batch, self.client.embed_documents(batch), strict=True):
                    self.cache[_cache_key(self.model, text)] = np.asarray(vector, dtype=np.float32)
            self._save()
        return np.stack([self.cache[_cache_key(self.model, t)] for t in texts])

    def embed_documents(self, texts):
        prefix = self.profile.get("document", "")
        return self._raw([prefix + t for t in texts]).tolist()

    def embed_query(self, text):
        return self._raw([self.profile.get("query", "") + text])[0].tolist()


def make_embeddings(model=EMBED_MODEL):
    """Repository glue: the embedding object for the vector store. Tests replace this function."""
    if EMBEDDING_BACKEND == "local":
        from langchain_huggingface import HuggingFaceEmbeddings

        name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        return CachedEmbeddings(name, client=HuggingFaceEmbeddings(model_name=name), profile={})
    return CachedEmbeddings(model)


# --- Index and first-stage search ----------------------------------------------------------------------------------


def build_index(records):
    """Repository glue: (re)build the in-memory BM25 index from article records. The dense index follows lazily."""
    docs = to_documents(records)
    _index.clear()
    _index.update(
        docs=docs,
        bm25=BM25Okapi([tokenize(d.page_content) for d in docs]),
        doc_by_id={d.metadata["id"]: d for d in docs},
        doc_ids=[d.metadata["id"] for d in docs],
        vectorstores={},
    )


def _ensure_index():
    if not _index:
        build_index(load_articles())
    return _index


def _vectorstore(model=None):
    """Repository glue: FAISS index per embedding model (notebook 02, section 4), built on the first dense query.

    T12: the vectors come from the embedding cache, so a rebuild costs no embedding request once every article has
    been embedded. normalize_L2 makes the FAISS distance rank like cosine similarity, the metric of both model cards.
    """
    index = _ensure_index()
    model = model or EMBED_MODEL
    if model not in index["vectorstores"]:
        from langchain_community.vectorstores import FAISS

        index["vectorstores"][model] = FAISS.from_documents(index["docs"], make_embeddings(model), normalize_L2=True)
    return index["vectorstores"][model]


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


def dense_ids(query, k=10, model=None):
    return [d.metadata["id"] for d in _vectorstore(model).similarity_search(query, k=k)]


def first_stage_ids(query, mode="hybrid", k=10, area=None, model=None):
    """Ranked ids of the first stage: k per retriever, for 'hybrid' fused with RRF (up to 2k ids).

    With `area` each retriever ranks only the articles of that area, as a search within one area of law.
    """
    index = _ensure_index()
    depth = len(index["docs"]) if area else k

    def within(ids):
        return [i for i in ids if index["doc_by_id"][i].metadata["area"] == area][:k] if area else ids

    if mode == "dense":
        return within(dense_ids(query, depth, model))
    if mode == "bm25":
        return within(bm25_ids(query, depth))
    return rrf([within(dense_ids(query, depth, model)), within(bm25_ids(query, depth))])


def retrieve(query, k=4, mode="hybrid", rerank=None, area=None):
    """Return the top-k articles as Documents. mode: 'dense', 'bm25' or 'hybrid'.

    rerank: None follows USE_RERANKER; True or False switches the reranker (RERANKER) on or off for this call.
    area: 'arbeitsrecht' or 'mietrecht' restricts the search to one area (T12, as search_law in the MCP server).
    """
    hits = [_ensure_index()["doc_by_id"][i] for i in first_stage_ids(query, mode, area=area)]
    if USE_RERANKER if rerank is None else rerank:
        top = hits[:RERANK_CANDIDATES]
        hits = (rerank_llm(query, top) if RERANKER == "llm" else cross_encoder_rerank(query, top)) + hits[len(top):]
    return hits[:k]


# --- Reranking -----------------------------------------------------------------------------------------------------

RERANK_PROMPT = (
    "Du ordnest Artikel des Schweizer Obligationenrechts nach ihrer Relevanz für eine Rechtsfrage.\n"
    "Massgebend ist, welcher Artikel die Frage am direktesten beantwortet.\n\n"
    "Frage: {query}\n\nArtikel:\n{candidates}\n\n"
    "Gib alle IDs zurück, vom relevantesten zum am wenigsten relevanten Artikel. "
    "Antworte nur mit JSON im Format {{\"ranking\": [\"OR-...\", ...]}}."
)
_ID_PATTERN = re.compile(r"\bOR-\d+[a-z]*\b", re.IGNORECASE)


def parse_ranking(text, candidate_ids):
    """Ids in the order of the reply, robust to extra text: unknown ids are dropped, repeated ids count once and
    candidates missing in the reply keep their first-stage order at the end."""
    by_upper = {c.upper(): c for c in candidate_ids}
    ranked = [by_upper[m.upper()] for m in _ID_PATTERN.findall(text or "") if m.upper() in by_upper]
    ranked = list(dict.fromkeys(ranked))
    return ranked + [c for c in candidate_ids if c not in ranked]


def rerank_llm(query, hits, llm=None):
    """Listwise reranking by a chat model (T12). On any error the first-stage order is kept and a warning logged."""
    if len(hits) < 2:
        return list(hits)
    candidates = "\n\n".join(
        f"[{d.metadata['id']}] {d.page_content[:RERANK_MAX_CHARS]}" for d in hits
    )
    try:
        llm = llm or make_llm(RERANK_MODEL)
        reply = llm.invoke(RERANK_PROMPT.format(query=query, candidates=candidates))
    except Exception as exc:  # noqa: BLE001 - a failed rerank must not break the search
        log.warning("rerank_llm: %s: %s, keeping the first-stage order", type(exc).__name__, exc)
        return list(hits)
    by_id = {d.metadata["id"]: d for d in hits}
    return [by_id[i] for i in parse_ranking(reply.content, list(by_id))]


def cross_encoder_rerank(query, hits):
    """Cross-encoder reranking of the top candidates (notebook 02, section 6). The model loads on first use."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder

        _cross_encoder = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    scores = _cross_encoder.predict([(query, d.page_content) for d in hits])
    return [d for _, d in sorted(zip(scores, hits), key=lambda pair: pair[0], reverse=True)]


rerank = cross_encoder_rerank  # name used in notebook 02


# --- Hit@k (notebook 02, section 7) ---------------------------------------------------------------------------------


def hit_at_k(ranked_ids, gold, k):
    """True if a gold article is among the first k ids. gold: one id or a list (cases with several gold articles)."""
    gold = {gold} if isinstance(gold, str) else set(gold)
    return bool(gold & set(ranked_ids[:k]))


def evaluate_retrieval(search, k=3, cases=RETRIEVAL_CASES):
    hits = [hit_at_k(search(q), gold, k) for q, gold in cases]
    return sum(hits) / len(hits)
