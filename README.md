# Swiss Legal Agent

A LangGraph agent for Swiss employment and tenancy law (OR 319 ff. and 253 ff.) that answers only from public
sources and cites every article it uses.

> **University prototype, not legal advice.** Built by Team LexGraph in the module Generative AI & Agent Systems,
> FHNW BSc Business Artificial Intelligence, HS 2026. Not an official service.

Architecture, building blocks and ownership: [docs/architecture.md](docs/architecture.md).
Decisions with rejected alternatives: [docs/decisions.md](docs/decisions.md).

## Team

| Member | Role |
|---|---|
| Jack Ondoua | Product Lead & Knowledge Architect |
| Tim Rusch | Agent Orchestration & Safety Engineer |

## Setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest and ruff
pip install -r requirements-local.txt # optional: cross-encoder and local embeddings (pulls torch), not in CI
cp .env.example .env               # then fill in LITELLM_API_KEY and SWISSAI_API_KEY
```

`requirements.txt` is the pinned, tested set from the course notebooks. Do not bump single packages.
`LITELLM_API_KEY` belongs to the FHNW LiteLLM proxy, `SWISSAI_API_KEY` to the Swiss AI Platform (Apertus).
Secrets never go into code. In Deepnote the keys are set under Integrations > Environment variables.

The package `lexgraph` can also be installed in editable mode with `pip install -e .`.

## Tests

```bash
pytest
ruff check .
```

All tests run offline without any API key. Model calls are replaced by `GenericFakeChatModel`. Tests that need
the embedding endpoint are skipped when `LITELLM_API_KEY` is not set. CI runs the same on every push and pull
request (`.github/workflows/ci.yml`).

## Run

MCP server `fedlex-mcp` (stdio transport, tools `get_article`, `search_law`, `search_decisions`):

```bash
python mcp_server/fedlex_server.py
```

Demo UI (Gradio):

```bash
python -m lexgraph.ui.app
```

The UI runs the full graph with Apertus, Harrier dense retrieval with LLM reranking and the human review step (task T15). It needs `LITELLM_API_KEY` and `SWISSAI_API_KEY`.

## Notebooks

The Deepnote project with the notebooks was suspended on 9 Nov 2026 by Deepnote's automated abuse detection
(support request open), so the notebooks are not available. As agreed with A. Martin on 10 Nov 2026, this repository
is the runnable solution: start the demo with `python -m lexgraph.ui.app` (see [Run](#run)). Code, data and results
of all notebooks are in this repository; which notebook fed which module: [notebooks/README.md](notebooks/README.md).

## Known limitations

- **Router with gpt-5.6-luna (#31):** luna routes the rental case MR-08 as out of scope and answers with the fixed
  rejection, without sources and without hand-over to a person. Apertus, the project standard, routes it correctly.
  Not fixed before the feature freeze; with luna as generator a wrong rejection can pass unnoticed.
- **Reviewer misses wrong periods (#32):** after #32 the reviewer no longer rejects correct drafts for missing
  follow-up questions, but it still accepts some wrong periods (test: three months instead of two in the 8th service
  year passed with the old and the new prompt). The hand-over to a person is a safety net, not a guarantee.
- **Missing norm in retrieval passes the reviewer:** the reviewer checks the draft against the retrieved sources only.
  When the deciding article is not retrieved, a wrong answer usually passes without hand-over (AR-12: Art. 329 OR was
  not retrieved in 10 of 10 live runs; hand-over in 1 of 5 runs with the new and 2 of 5 with the old reviewer
  prompt). Chunks per paragraph would be the obvious next step and are out of scope after the feature freeze; see
  [docs/eval/retrieval/live-suche.md](docs/eval/retrieval/live-suche.md).
- **F1 v2 measured the old checks:** "Zitate belegt" uses the citation check before #30 (PR #37) and the hand-over
  rate the reviewer before #32. F1 is not run again; see [docs/eval/f1-v2/README.md](docs/eval/f1-v2/README.md).

## Way of working

- `main` is changed only through pull requests: 1 approving review, CI green, squash merge.
- Branches: `feature/T13-<short-name>`, `fix/T17-<short-name>` (task ID first).
- Commit messages start with the task ID, for example `T13: connect search_law to retrieve()`.
- Every PR fills in the template: task ID, what changed, decision and rejected alternative, how it was tested.
- Open work is marked in the code as `# TODO (Txx): ...` with its task ID.

## Data and licence

The knowledge base currently holds **paraphrased placeholder records, not the legal text** (replaced in task T11).
Official enactments and decisions of authorities are not protected by copyright under Art. 5 of the Swiss
Copyright Act (URG). Details on origin and licence of the data: [data/README.md](data/README.md).
