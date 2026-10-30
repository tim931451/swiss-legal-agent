# AI declaration (template)

Template for the declaration of AI tools in the submission. Every team member adds a row for each tool they used.
Fill in only what actually happened. Leave the table empty rather than estimating.

Note: the language models the agent itself calls at runtime (LiteLLM proxy, Swiss AI Platform) are part of the
system and are documented in `lexgraph/config.py` and `docs/architecture.md`. This declaration covers AI tools used
to produce code, text, data or slides for the project.

| Tool (name, version or model) | Purpose | Scope (which files, sections or slides) | Member | How the output was checked |
|---|---|---|---|---|
| Claude (Anthropic, Cowork) | Code and tests for T16, T17, T19 from Tim's task description; Tim decided scope and rules | `lexgraph/guardrails/`, `lexgraph/tracing.py`, guard node and reviewer in `lexgraph/agents/graph.py`, `tests/test_guardrails.py`, `tests/test_t16_t17.py`, `tests/test_tracing.py` | Tim | Offline tests and ruff, one live run with gpt-oss-120b (`scripts/run_case.py`), review by Tim before merge |
| | | | | |
| | | | | |

## Statement

Use the wording the module requires for the submission (see Moodle). It is not copied here so that the template does
not contain text nobody checked.
