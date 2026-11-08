"""T13: load a cited article by its id, so the reviewer can check citations the retriever did not fetch.

Two ways with the same contract, `lookup("OR-335b")` returns {id, title, text} or None:

- `make_article_lookup(articles)`: directly over the knowledge base (data/or_articles.jsonl), fast, for tests and
  evaluation runs.
- `make_mcp_lookup()`: through the fedlex-mcp server and its tool `get_article` (stdio, one session per call). This
  is the path where the graph actually calls the MCP tool; it starts the server once per lookup (about 1 s).

Background (T17 live run, 30 Oct): three correct answers went to a human only because the keyword retriever had
not fetched the cited article, so the citation check could not see it in the sources.
"""

import asyncio
import json
import pathlib
import sys

SERVER = pathlib.Path(__file__).resolve().parents[2] / "mcp_server" / "fedlex_server.py"


def _record(article):
    return {"id": article["id"], "title": article["title"], "text": article["text"]}


def make_article_lookup(articles):
    """Lookup over a list of article records (id, title, text), ids compared case-insensitively."""
    by_id = {a["id"].upper(): a for a in articles}

    def lookup(article_id):
        article = by_id.get(article_id.upper())
        return _record(article) if article else None

    return lookup


async def _get_article(law, number, command, server, env):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=command, args=[str(server)], env=env)
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("get_article", {"law": law, "article": number})
        return json.loads(result.content[0].text)


def make_mcp_lookup(command=sys.executable, server=SERVER, env=None):
    """Lookup through the MCP tool get_article. env defaults to BM25 mode, the lookup needs no search index."""
    env = env if env is not None else {"FEDLEX_SEARCH_MODE": "bm25"}

    def lookup(article_id):
        law, _, number = article_id.partition("-")
        result = asyncio.run(_get_article(law, number, command, server, env))
        return _record(result) if result.get("found") else None

    return lookup
