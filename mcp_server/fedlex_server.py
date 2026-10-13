"""fedlex-mcp: MCP server that exposes the Swiss Code of Obligations to our agents.

Source: notebook 03, section 3. Run with: python mcp_server/fedlex_server.py (stdio transport).

Client side (notebook 03, section 4):

    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient({
        "fedlex": {"command": sys.executable, "args": ["mcp_server/fedlex_server.py"], "transport": "stdio"}
    })
    tools = await client.get_tools()
"""
import json
import pathlib
import re

from mcp.server.fastmcp import FastMCP
from rank_bm25 import BM25Okapi

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "or_articles.jsonl"

mcp = FastMCP("fedlex-mcp")


def _tokenize(text):
    return re.findall(r"\w+", text.lower())


def _load():
    with open(DATA, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


ARTICLES = _load()
BY_ID = {a["id"]: a for a in ARTICLES}
BM25 = BM25Okapi([_tokenize(f"{a['title']} {a['text']}") for a in ARTICLES])


@mcp.tool()
def get_article(law: str, article: str) -> dict:
    """Return one article of Swiss federal law by its number, for example law='OR', article='335c'."""
    record = BY_ID.get(f"{law.upper()}-{article.lower()}")
    if record is None:
        return {"found": False, "message": f"Art. {article} {law} is not in the knowledge base."}
    return {"found": True, **record}


@mcp.tool()
def search_law(query: str, k: int = 4) -> list[dict]:
    """Search the knowledge base for the articles that best match a legal question (German)."""
    # TODO (T13): call retrieve() from lexgraph.rag.retrieval instead of BM25 (planned for W4).
    scores = BM25.get_scores(_tokenize(query))
    ranked = sorted(range(len(ARTICLES)), key=lambda i: scores[i], reverse=True)[:k]
    return [{"id": ARTICLES[i]["id"], "title": ARTICLES[i]["title"], "text": ARTICLES[i]["text"],
             "url": ARTICLES[i]["url"]} for i in ranked if scores[i] > 0]


@mcp.tool()
def search_decisions(query: str, k: int = 3) -> list[dict]:
    """Search published Federal Supreme Court decisions (BGE). Not connected yet: returns an empty list."""
    # TODO (T13): connect a BGE source (optional since 12 Oct 2026, decision log notebook 00).
    return []


if __name__ == "__main__":
    mcp.run()   # stdio transport
