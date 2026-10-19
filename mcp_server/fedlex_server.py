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
import os
import pathlib
import re
import sys

from mcp.server.fastmcp import FastMCP
from rank_bm25 import BM25Okapi

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "or_articles.jsonl"
sys.path.insert(0, str(ROOT))  # the server runs as a script (stdio), so make the lexgraph package importable

# T13: search_law uses the shared retrieval from lexgraph.rag.retrieval (notebook 02). Hybrid search needs the
# embedding proxy and therefore LITELLM_API_KEY; without a key the server falls back to BM25, so it always starts.
SEARCH_MODE = os.environ.get("FEDLEX_SEARCH_MODE") or ("hybrid" if os.environ.get("LITELLM_API_KEY") else "bm25")

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


def _bm25_search(query, k):
    scores = BM25.get_scores(_tokenize(query))
    ranked = sorted(range(len(ARTICLES)), key=lambda i: scores[i], reverse=True)[:k]
    return [ARTICLES[i] for i in ranked if scores[i] > 0]


def _shared_search(query, k, mode):
    from lexgraph.rag import retrieval

    return [BY_ID[d.metadata["id"]] for d in retrieval.retrieve(query, k=k, mode=mode) if d.metadata["id"] in BY_ID]


@mcp.tool()
def search_law(query: str, k: int = 4, area: str = "") -> list[dict]:
    """Search the knowledge base for the articles that best match a legal question (German).

    area: optional filter, 'arbeitsrecht' or 'mietrecht'. Empty means both.
    """
    k = max(1, min(int(k), 10))
    try:
        hits = _shared_search(query, k * 2, SEARCH_MODE)
    except Exception:  # noqa: BLE001 - no key, no network or no index: the server must still answer
        hits = _bm25_search(query, k * 2)
    if area:
        hits = [a for a in hits if a.get("area") == area.lower()]
    return [{"id": a["id"], "title": a["title"], "text": a["text"], "url": a["url"]} for a in hits[:k]]


# SW5 task 2: a second tool with its own small table. Notice periods for employees after the probation
# period, from Art. 335c para. 1 OR. Para. 2 allows other periods by written agreement, see the note.
NOTICE_PERIODS = [  # (first service year, last service year or None, months)
    (1, 1, 1),
    (2, 9, 2),
    (10, None, 3),
]


@mcp.tool()
def notice_period(service_year: int) -> dict:
    """Statutory notice period in months for an employment contract after the probation period.

    service_year: the year of service the employee is in at the time of notice (1 = first year).
    """
    if service_year < 1:
        return {"found": False, "message": "service_year must be 1 or higher."}
    for first, last, months in NOTICE_PERIODS:
        if service_year >= first and (last is None or service_year <= last):
            return {
                "found": True,
                "service_year": service_year,
                "months": months,
                "to": "end of a month",
                "source": "Art. 335c Abs. 1 OR",
                "note": "Different periods are possible by written agreement (Art. 335c Abs. 2 OR); "
                        "check the contract and Art. 335c before answering.",
            }
    return {"found": False, "message": "No entry for this service year."}


@mcp.tool()
def search_decisions(query: str, k: int = 3) -> dict:
    """Search published Federal Supreme Court decisions (BGE). Not connected: BGE is optional since 12 Oct 2026.

    Returns found=False with a message, so an agent does not mistake an empty list for "no relevant decisions".
    """
    # BGE stays out of scope unless the team decides otherwise in T23 (Inspect & Adapt, 09.11.).
    return {"found": False, "results": [],
            "message": "Bundesgerichtsentscheide sind nicht angebunden. Nur Gesetzesartikel zitieren."}


if __name__ == "__main__":
    mcp.run()   # stdio transport
