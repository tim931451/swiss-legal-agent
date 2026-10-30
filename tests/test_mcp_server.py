"""T13: the fedlex-mcp server, its four tools, and a real MCP round trip over stdio. Offline, no key needed."""

import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parent.parent / "mcp_server" / "fedlex_server.py"


@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("fedlex_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SEARCH_MODE = "bm25"
    return module


def test_get_article_found_and_not_found(server):
    hit = server.get_article("or", "335C")
    assert hit["found"] and hit["id"] == "OR-335c" and hit["url"].startswith("https://www.fedlex.admin.ch")
    assert server.get_article("OR", "999")["found"] is False


def test_search_law_ranks_and_filters_by_area(server):
    ids = [a["id"] for a in server.search_law("Kündigung während Krankheit Sperrfrist", k=2)]
    assert ids and ids[0] == "OR-336c"
    tenancy = server.search_law("Kündigung Frist", k=5, area="mietrecht")
    assert tenancy and all(server.BY_ID[a["id"]]["area"] == "mietrecht" for a in tenancy)


def test_search_law_falls_back_to_bm25_without_index(server, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("no embeddings")

    monkeypatch.setattr(server, "_shared_search", broken)
    # T11: words of the legal text. Lay words such as "Schimmel" are not in the OR, BM25 alone misses them (T12).
    assert server.search_law("Mangel beseitigen Mietzins herabsetzen", k=1)[0]["id"] == "OR-259a"


def test_search_decisions_says_not_connected(server):
    result = server.search_decisions("Kündigung zur Unzeit")
    assert result["found"] is False and result["results"] == []


def test_stdio_round_trip_lists_and_calls_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env={"FEDLEX_SEARCH_MODE": "bm25"})
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            result = await session.call_tool("get_article", {"law": "OR", "article": "335c"})
            return names, result.content[0].text

    names, text = asyncio.run(run())
    assert names == {"get_article", "search_law", "notice_period", "search_decisions"}
    assert "Kündigungsfristen" in text
