# AI declaration (template)

Template for the declaration of AI tools in the submission. Every team member adds a row for each tool they used.
Fill in only what actually happened. Leave the table empty rather than estimating.

Note: the language models the agent itself calls at runtime (LiteLLM proxy, Swiss AI Platform) are part of the
system and are documented in `lexgraph/config.py` and `docs/architecture.md`. This declaration covers AI tools used
to produce code, text, data or slides for the project.

| Tool (name, version or model) | Purpose | Scope (which files, sections or slides) | Member | How the output was checked |
|---|---|---|---|---|
| Claude (Anthropic, Cowork) | Code and tests for T16, T17, T19 from Tim's task description; Tim decided scope and rules | `lexgraph/guardrails/`, `lexgraph/tracing.py`, guard node and reviewer in `lexgraph/agents/graph.py`, `tests/test_guardrails.py`, `tests/test_t16_t17.py`, `tests/test_tracing.py` | Tim | Offline tests and ruff, one live run with gpt-oss-120b (`scripts/run_case.py`), review by Tim before merge |
| Claude (Anthropic, Cowork) | T13: article lookup in the reviewer via the MCP tool `get_article`, tests, development smoke run | `lexgraph/agents/lookup.py`, reviewer in `lexgraph/agents/graph.py`, `tests/test_t13_lookup.py`, `scripts/run_case.py` | Tim | Offline tests (including a real stdio call to the MCP server), ruff, smoke run on 4 development cases; proposal and code by Claude on Tim's instruction, whether the lookup is on by default is decided by Tim and Jack |
| Claude (Anthropic, Cowork) | CI #62 fix (sentence-transformers optional) and graph retrieval switched to dense with LLM reranking, on Tim's instruction after Jack's request of 9 Nov 2026 | `requirements.txt`, `requirements-local.txt`, `README.md`, `lexgraph/eval/experiment.py`, `scripts/eval_f1.py`, `tests/test_t20_eval.py`, `docs/decisions.md`, `docs/eval/f1-v2/README.md` | Tim | Offline tests and ruff locally, CI run on the pull request, review by Jack |
| Claude (Anthropic, Claude Code) | T15: Gradio UI connected to the graph, human review step, tests, on Jack's instruction | `lexgraph/ui/app.py`, `tests/test_t15_ui.py`, `README.md`, `docs/decisions.md` | Jack | Offline tests with fake models, ruff, browser check of all UI states with a fake model, review by Tim; live run with the real models by Tim on 9 and 10 Nov 2026, locally without share (T41) |
| Claude (Anthropic, Claude Code) | T17: citation check reads short-form ids and the Quellen line, ignores articles only mentioned as missing (issue #30), tests, on Tim's instruction | `lexgraph/guardrails/citation_check.py`, `tests/test_guardrails.py`, `docs/decisions.md` | Tim | Offline tests and ruff, offline re-check of the stored F1 v2 answers, review by Jack |
| Claude (Anthropic, Claude Code) | T17 after review Jack on #37: markers only exclude directly concerned articles, Quellen line read in long form, Jack's three sentences and nine regression tests, on Tim's instruction (rule "in doubt cited" set by Tim) | `lexgraph/guardrails/citation_check.py`, `tests/test_guardrails.py`, `docs/decisions.md` | Tim | Offline tests and ruff, regression cases checked against the check on main, offline re-check of the F1 v2 answers, changed luna answers checked by Tim, review by Jack |
| | | | | |

## Statement

Use the wording the module requires for the submission (see Moodle). It is not copied here so that the template does
not contain text nobody checked.
