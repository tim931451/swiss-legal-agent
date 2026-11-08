"""T18: 100-point judge grid, robust parser, reproducibility check and the test set of 20 cases. Offline, no key."""

import json

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from lexgraph.eval.judge import CRITERIA, MAX_POINTS, judge_answer, judge_prompt, parse_judge, score
from lexgraph.eval.metrics import agreement
from lexgraph.rag.ingest import ARTICLES_FILE, load_articles
from scripts import eval_judge

CASE = {"id": "AR-02", "area": "arbeitsrecht", "question": "Krank und gekündigt, gültig?",
        "expected_answer": "Nein, Sperrfrist von 90 Tagen.", "gold_articles": ["OR-336c"]}
ALL_TRUE = {name: True for name in CRITERIA}


def test_grid_has_the_five_criteria_of_notebook_06_and_100_points():
    assert list(CRITERIA) == ["correct_norm", "correct_result", "no_invented_sources", "complete", "clear_structure"]
    assert MAX_POINTS == 100 and all(isinstance(p, int) and p > 0 for p, _ in CRITERIA.values())
    assert CRITERIA["correct_result"][0] == max(p for p, _ in CRITERIA.values())
    assert score(ALL_TRUE) == 100 and score({}) == 0
    assert score({**ALL_TRUE, "clear_structure": False}) == 100 - CRITERIA["clear_structure"][0]


def test_parse_judge_code_fence_and_text_around():
    reply = ('Bewertung:\n```json\n{"criteria": {"correct_norm": true, "correct_result": true, '
             '"no_invented_sources": true, "complete": false, "clear_structure": true}, "comment": "Frist fehlt."}\n'
             '```\nHinweis: {nicht relevant}')
    verdict = parse_judge(reply)
    assert verdict["score"] == 100 - CRITERIA["complete"][0] and verdict["comment"] == "Frist fehlt."
    assert verdict["missing"] == []


def test_parse_judge_words_flat_object_and_missing_criteria():
    verdict = parse_judge('{"correct_norm": "ja", "correct_result": "Nein", "no_invented_sources": 1, '
                          '"complete": "vielleicht"}')
    assert verdict["criteria"] == {"correct_norm": True, "correct_result": False, "no_invented_sources": True,
                                   "complete": False, "clear_structure": False}
    assert verdict["missing"] == ["complete", "clear_structure"]  # unreadable or absent: false, but listed
    assert verdict["score"] == CRITERIA["correct_norm"][0] + CRITERIA["no_invented_sources"][0]


def test_parse_judge_without_criteria_raises():
    with pytest.raises(ValueError):
        parse_judge("Die Antwort ist gut.")
    with pytest.raises(ValueError):
        parse_judge('{"comment": "kein Kriterium"}')


def test_judge_prompt_is_german_and_names_the_gold_articles():
    prompt = judge_prompt({**CASE, "gold_articles": ["OR-259a", "OR-259d"]}, "Antwort")
    assert "Massgebende Artikel: Art. 259a OR, Art. 259d OR" in prompt
    assert "Musterlösung: Nein, Sperrfrist von 90 Tagen." in prompt and "ß" not in prompt
    assert all(f"- {name}: " in prompt for name in CRITERIA)


def test_judge_answer_with_fake_model():
    llm = GenericFakeChatModel(messages=iter([AIMessage(content=json.dumps({"criteria": ALL_TRUE, "comment": "ok"}))]))
    assert judge_answer(CASE, "Art. 336c OR: nichtig.", judge=llm)["score"] == 100


def test_agreement_per_criterion():
    assert agreement([True, False, True, True], [True, False, True, True]) == {"agreement": 1.0, "kappa": 1.0}
    assert agreement([True, True, False, False], [True, False, False, True])["agreement"] == 0.5


class ReplayJudge:
    """Fake judge: full marks for the reference answer, wrong answers fail norm, result and completeness."""

    def __init__(self):
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        answer = prompt.split("Antwort: ")[-1]
        gold = prompt.split("Massgebende Artikel: ")[1].split("\n")[0]
        right = answer.startswith(f"Norm: {gold}.")
        criteria = {**ALL_TRUE, "correct_norm": right, "correct_result": right, "complete": right,
                    "no_invented_sources": "BGB" not in answer}
        return AIMessage(content=json.dumps({"criteria": criteria, "comment": "x"}))


def test_eval_judge_offline(tmp_path, monkeypatch):
    cases = load_articles(ARTICLES_FILE.parent / "testset.jsonl")[:4]
    answers = eval_judge.fixed_answers(cases)
    assert answers[("wrong", "AR-01")] == eval_judge.reference_answer(cases[1])  # next case of the same area
    assert answers[("foreign", "AR-01")].endswith("§ 622 BGB.")
    judge = ReplayJudge()
    results = eval_judge.run_judge(cases, answers, judge, runs=2)
    assert len(results) == 2 * 3 * 4 and len(judge.prompts) == 24
    by_variant = results[results["run"] == 1].groupby("variant")["score"].mean()
    assert by_variant["reference"] == 100 and by_variant["wrong"] == 30
    assert by_variant["foreign"] == 100 - CRITERIA["no_invented_sources"][0]
    agree = eval_judge.compare_runs(results).set_index("criterion")
    assert (agree["agreement"] == 1.0).all() and agree.loc["score", "max_abs_diff"] == 0
    assert "| no_invented_sources | 20 | 12 | 100% |" in eval_judge.to_markdown(agree.reset_index(), results, "n")


def test_testset_has_20_cases_with_the_distribution_of_the_first_10():
    """T18: 20 cases, areas and difficulty in the same proportions as the first ten (6:4 and 2:2:1)."""
    cases = load_articles(ARTICLES_FILE.parent / "testset.jsonl")
    ids = {a["id"] for a in load_articles(ARTICLES_FILE)}
    assert len(cases) == 20 and len({c["id"] for c in cases}) == 20
    assert [c["area"] for c in cases].count("arbeitsrecht") == 12
    assert {d: [c["difficulty"] for c in cases].count(d) for d in ("easy", "medium", "hard")} == \
           {"easy": 8, "medium": 8, "hard": 4}
    fields = {"id", "area", "difficulty", "source", "question", "expected_answer", "gold_articles"}
    for case in cases:
        assert set(case) == fields and set(case["gold_articles"]) <= ids
        assert case["source"].startswith("own wording") and case["id"][:2] == {"arbeitsrecht": "AR",
                                                                                "mietrecht": "MR"}[case["area"]]
        assert "ß" not in case["question"] + case["expected_answer"]
    for case in cases[10:]:  # the new cases name the articles they are based on
        assert all(g in case["source"] for g in case["gold_articles"])
