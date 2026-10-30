"""Deterministic metrics: citation precision and recall, Cohen's kappa.

Source: notebook 06, sections 3 and 6. No model needed, cheap and fully reproducible.
"""

from lexgraph.guardrails.citation_check import cited_articles as _cited_articles


def cited_articles(answer):
    """Cited articles as upper-case ids (OR-336C). Same parsing as the guardrail (T17), which keeps the case."""
    return {c.upper() for c in _cited_articles(answer)}


def citation_scores(answer, gold_articles):
    cited, gold = cited_articles(answer), {g.upper() for g in gold_articles}
    precision = len(cited & gold) / len(cited) if cited else 0.0
    recall = len(cited & gold) / len(gold) if gold else 0.0
    return {"citation_precision": round(precision, 2), "citation_recall": round(recall, 2)}


def cohens_kappa(a, b):
    """Cohen's kappa for two lists of booleans of equal length."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    p_a, p_b = sum(a) / n, sum(b) / n
    expected = p_a * p_b + (1 - p_a) * (1 - p_b)
    return 1.0 if expected == 1 else round((observed - expected) / (1 - expected), 3)
