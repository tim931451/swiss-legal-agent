# Notebooks

The notebooks live in Deepnote. They document, explain and demonstrate the code; the code itself lives in this
repository.

Deepnote project: <https://deepnote.com/workspace/GenAI-2026-10d57e68-1744-4ea7-a868-3b3feb9acdc6/project/Swiss-Legal-Agent-9b9d17b7-b4fd-473b-beb2-f7ed180fbdd3/notebook/00projectoverview-92fbd5ace251461e8e69c436f794863b>

Run order: 01 checks the keys. 02 writes `data/or_articles.jsonl`, which 03 and 04 read.

| # | Notebook | Owner | Code in this repository |
|---|---|---|---|
| 00 | Project Overview | Jack | `docs/architecture.md`, `docs/decisions.md` (decision log) |
| 01 | Setup and First Model Call | Tim | `lexgraph/config.py`: `LLM_BASE_URL`, `SWISSAI_BASE_URL`, model names, `make_llm` |
| 02 | Knowledge Base and RAG | Jack | `lexgraph/rag/ingest.py`: `SAMPLE`, `load_articles`, `to_documents`; `lexgraph/rag/retrieval.py`: `tokenize`, `bm25_ids`, `rrf`, `dense_ids`, `retrieve`, `rerank`, `hit_at_k`, `evaluate_retrieval`, `RETRIEVAL_CASES`; `data/or_articles.jsonl`; `tests/test_retrieval.py` |
| 03 | Tools and MCP Server | Tim | `mcp_server/fedlex_server.py`: `get_article`, `search_law`, `search_decisions`; `lexgraph/agents/prompts.py`: `SYSTEM_PROMPT` |
| 04 | Agent Graph | Tim | `lexgraph/agents/state.py`: `LegalState`; `lexgraph/agents/prompts.py`; `lexgraph/agents/graph.py`: `build_graph`, `format_sources`, `make_keyword_retriever`, `MAX_REVISIONS`; `tests/test_graph.py` |
| 05 | Guardrails | Tim | `lexgraph/guardrails/input_guard.py`: `input_guard`, `is_jailbreak`, `redact`, `looks_legal`; `lexgraph/guardrails/citation_check.py`: `citation_check`, `cited_articles`; `tests/test_guardrails.py` |
| 06 | Evaluation | Jack | `lexgraph/eval/metrics.py`: `citation_scores`, `cohens_kappa`; `lexgraph/eval/judge.py`: `CRITERIA`, `JUDGE_PROMPT`, `parse_judge`, `judge_answer`; `lexgraph/eval/experiment.py`: `baseline_answer`, `cost`, `run_experiment`; `data/testset.jsonl`; `tests/test_metrics.py` |
| 07 | Demo UI | Jack | `lexgraph/ui/app.py`: `run_pipeline` (placeholder), `answer_case`, `demo` |

Not moved into the repository (demonstration code that stays in the notebooks): `list_models`, `ask` and
`check_tool_calling` (01), the `create_agent` demo (03), the real-case runs (04), the F1 chart (06).
