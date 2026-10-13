"""Deterministic evaluation metrics. Source: notebook 06, sections 3, 4 and 6."""

from lexgraph.eval.judge import parse_judge
from lexgraph.eval.metrics import citation_scores, cohens_kappa


def test_citation_scores_exact_match():
    assert citation_scores("Gemäss Art. 336c Abs. 1 OR ist sie nichtig.", ["OR-336c"]) == \
           {"citation_precision": 1.0, "citation_recall": 1.0}


def test_citation_scores_invented_article_halves_precision():
    assert citation_scores("Art. 336c OR und Art. 999 OR", ["OR-336c"])["citation_precision"] == 0.5


def test_parse_judge_with_text_around_json():
    example = parse_judge('Hier: {"criteria": {"correct_norm": true, "correct_result": true, '
                          '"no_invented_sources": true, "complete": false, "clear_structure": true}, '
                          '"comment": "Frist fehlt."}')
    assert example["score"] == 80


def test_cohens_kappa_perfect_agreement():
    assert cohens_kappa([True, False, True], [True, False, True]) == 1.0
