"""Token accounting for model calls (SW5 task 6: how many tokens does an answered and a rejected question cost?).

`CountingLLM` wraps any chat model with an `invoke` method. The graph only calls `invoke`, so the wrapper can be
passed to `build_graph` unchanged. Each call is recorded with the graph node it belongs to (read from the prompt)
and the token usage the provider reports. This replaces the LangSmith trace view until tracing is wired in (T19).
"""

from lexgraph.agents.prompts import REJECT_PROMPT, REVIEWER_PROMPT, ROUTER_PROMPT, SPECIALIST_PROMPT

# The first words of each prompt identify the node that sent it.
_NODE_BY_PREFIX = {
    ROUTER_PROMPT[:40]: "router",
    SPECIALIST_PROMPT[:20]: "specialist",
    REVIEWER_PROMPT[:40]: "reviewer",
    REJECT_PROMPT[:40]: "out_of_scope",
}


def node_of(prompt):
    text = prompt if isinstance(prompt, str) else str(prompt)
    for prefix, node in _NODE_BY_PREFIX.items():
        if text.startswith(prefix):
            return node
    return "other"


def usage_of(message):
    """Input and output tokens of one model reply, 0 if the provider reports none."""
    usage = getattr(message, "usage_metadata", None) or {}
    if not usage:
        raw = (getattr(message, "response_metadata", None) or {}).get("token_usage") or {}
        usage = {"input_tokens": raw.get("prompt_tokens", 0), "output_tokens": raw.get("completion_tokens", 0)}
    return int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)


class CountingLLM:
    def __init__(self, llm):
        self.llm = llm
        self.calls = []

    def invoke(self, prompt, *args, **kwargs):
        message = self.llm.invoke(prompt, *args, **kwargs)
        tokens_in, tokens_out = usage_of(message)
        self.calls.append({"node": node_of(prompt), "input_tokens": tokens_in, "output_tokens": tokens_out})
        return message

    def reset(self):
        self.calls = []

    def summary(self):
        tokens_in = sum(c["input_tokens"] for c in self.calls)
        tokens_out = sum(c["output_tokens"] for c in self.calls)
        return {"model_calls": len(self.calls), "input_tokens": tokens_in, "output_tokens": tokens_out,
                "total_tokens": tokens_in + tokens_out, "path": [c["node"] for c in self.calls]}
