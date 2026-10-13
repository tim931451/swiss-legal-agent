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

The UI still shows a fixed placeholder answer until the pipeline is connected (task T15).

## Notebooks

The notebooks in Deepnote document, explain and demonstrate the code in this repository:
[Deepnote project](https://deepnote.com/workspace/GenAI-2026-10d57e68-1744-4ea7-a868-3b3feb9acdc6/project/Swiss-Legal-Agent-9b9d17b7-b4fd-473b-beb2-f7ed180fbdd3/notebook/00projectoverview-92fbd5ace251461e8e69c436f794863b).
Which notebook feeds which module: [notebooks/README.md](notebooks/README.md).

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
