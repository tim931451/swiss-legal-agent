# Notebooks

The notebooks were written in Deepnote and document, explain and demonstrate the code; the code itself lives in this
repository. This folder holds all eight notebooks (`00_project_overview.ipynb` to `07_demo_ui.ipynb`) as frozen copies
of the Deepnote export from 16 Nov 2026, including the cell outputs saved there; they are no longer maintained. The
Deepnote project was suspended on 9 Nov 2026 by Deepnote's automated abuse detection and released again on 16 Nov 2026.
As agreed with A. Martin on 10 Nov 2026, the runnable solution is this repository only: start the demo with `python -m
lexgraph.ui.app` (main README, section Run).

Notebook 07 still ends with `demo.launch(share=True)`. That share tunnel triggered the suspension, so do not run this
cell in Deepnote; locally, `python -m lexgraph.ui.app` starts the UI without a share link.

The table shows which module took over the code of each notebook.

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
`check_tool_calling` (01), the `create_agent` demo (03), the real-case runs (04). The F1 chart is in
`docs/eval/f1-v2/f1_chart.png`.
