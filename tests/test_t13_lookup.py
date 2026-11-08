"""T13: the reviewer loads cited articles the retriever did not fetch, directly or through the MCP tool get_article.

Offline with fake chat models; the MCP test starts the real server over stdio in BM25 mode (no key needed).
"""

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from lexgraph.agents.graph import MAX_REVISIONS, build_graph
from lexgraph.agents.lookup import make_article_lookup, make_mcp_lookup

RETRIEVED = [{"id": "OR-335c", "title": "Kündigungsfristen", "text": "..."}]
KB = [*RETRIEVED, {"id": "OR-335b", "title": "Probezeit", "text": "Während der Probezeit sieben Tage."}]
DRAFT = "Nach Art. 335b OR gilt in der Probezeit eine Kündigungsfrist von sieben Tagen."


class Spy(GenericFakeChatModel):
    prompts: list = []

    def invoke(self, prompt, *args, **kwargs):
        self.prompts.append(prompt)
        return super().invoke(prompt, *args, **kwargs)


def counting(lookup):
    calls = []

    def wrapped(article_id):
        calls.append(article_id)
        return lookup(article_id)

    return wrapped, calls


def test_article_lookup_is_case_insensitive():
    lookup = make_article_lookup(KB)
    assert lookup("or-335B")["title"] == "Probezeit" and lookup("OR-999") is None


def test_cited_article_is_loaded_and_the_reviewer_sees_it():
    llm = Spy(messages=iter(["arbeitsrecht", DRAFT, "OK"]), prompts=[])
    lookup, calls = counting(make_article_lookup(KB))
    run = build_graph(llm, lambda q, a, k=3: RETRIEVED, lookup=lookup).invoke({"question": "Probezeit, welche Frist?"})
    assert run["review"] == "OK" and run["needs_human"] is False and run["revisions"] == 0
    assert calls == ["OR-335b"] and run["looked_up"] == ["OR-335B"]
    assert [s["id"] for s in run["sources"]] == ["OR-335c", "OR-335b"]
    assert "Während der Probezeit sieben Tage." in llm.prompts[-1]  # reviewer prompt got the loaded text


def test_article_outside_the_knowledge_base_stays_unsupported():
    draft = "Nach Art. 999 OR ist das so."
    llm = Spy(messages=iter(["arbeitsrecht", *[draft] * (MAX_REVISIONS + 1)]), prompts=[])
    lookup, calls = counting(make_article_lookup(KB))
    run = build_graph(llm, lambda q, a, k=3: RETRIEVED, lookup=lookup).invoke({"question": "Frist?"})
    assert run["needs_human"] is True and run["citation_check"]["unsupported"] == ["OR-999"]
    assert calls == ["OR-999"]  # looked up once per case, not once per round


def test_without_lookup_the_check_stays_strict():
    llm = Spy(messages=iter(["arbeitsrecht", *[DRAFT] * (MAX_REVISIONS + 1)]), prompts=[])
    run = build_graph(llm, lambda q, a, k=3: RETRIEVED).invoke({"question": "Probezeit, welche Frist?"})
    assert run["needs_human"] is True and "looked_up" not in run


def test_mcp_lookup_calls_get_article_over_stdio():
    lookup = make_mcp_lookup()
    article = lookup("OR-335c")
    assert article["id"] == "OR-335c" and "Kündigungsfrist" in article["text"]
    assert lookup("OR-9999") is None
