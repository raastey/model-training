import json
from pathlib import Path

from trainer.agentic import HARNESSES, CodeTask, load_code_tasks, run_task, run_tests
from trainer.study import (
    BLIND_CONDITIONS,
    build_blind_review,
    build_style_profile,
    register_violations,
    score_blind_review,
    score_output,
)

AUTHOR = [
    "The ministry spoke of order and the courts spoke of law, and yet the prisons filled all the same.",
    "The bank lent the money and the state signed the terms, and yet the debt was never only about money.",
    "The port was sold and the navy arrived, and yet officials insisted that nothing had changed at all.",
]


def test_style_delta_prefers_author_text_over_unrelated_text():
    profile = build_style_profile(AUTHOR, vocabulary_size=10)
    near = "The court spoke of law and the state signed the order, and yet the prisons filled."
    far = "Click here to buy now! Best deals online today, limited offer, free shipping included."
    assert profile.delta(near) < profile.delta(far)


def test_copy_rate_detects_verbatim_reuse():
    profile = build_style_profile(AUTHOR)
    assert profile.copy_rate(AUTHOR[0]) == 1.0
    assert profile.copy_rate("An entirely different sentence about weather patterns over the northern sea today.") == 0.0
    assert profile.copy_rate("") == 0.0


def test_register_violations_count_dashes_banned_words_and_scaffolding():
    assert register_violations("A stark choice — this is not policy, it is theatre.") == 3
    assert register_violations("The state signed the terms, and yet the debt grew.") == 0


def test_score_output_flags_empty_output():
    profile = build_style_profile(AUTHOR)
    assert score_output(profile, "")["issue"] == "EMPTY"


def test_blind_review_hides_conditions_and_scores_choices():
    report = {
        "tasks": [{"id": "W01", "task": "Task one"}, {"id": "W02", "task": "Task two"}],
        "conditions": [{"id": c, "results": [{"id": "W01", "output": f"{c} one"}, {"id": "W02", "output": f"{c} two"}]}
                       for c in BLIND_CONDITIONS],
    }
    page, key = build_blind_review(report)
    assert '"prompt_retrieval"' not in page and "</script></body>" in page
    adapter_slot = next(slot for slot, condition in key["W01"].items() if condition == "adapter")
    result = score_blind_review({"W01": adapter_slot, "W02": "Z"}, key)
    assert result["judged"] == 1 and result["wins"]["adapter"] == 1


def test_published_code_tasks_fail_before_repair():
    tasks = load_code_tasks(Path(__file__).parents[1] / "evals" / "study" / "code-tasks.json")
    assert len(tasks) == 8
    for task in tasks:
        assert run_tests(task, task.source)[0] is False


TASK = CodeTask("double", "double.py", "double is wrong. Fix it.", "def double(x):\n    return x + 1\n",
                "import unittest\nfrom double import double\n\nclass T(unittest.TestCase):\n    def test(self):\n        self.assertEqual(double(4), 8)\n")


def test_agent_loop_feeds_failures_back_and_stops_on_success():
    replies = iter(["```python\ndef double(x):\n    return x * 3\n```", "```python\ndef double(x):\n    return x * 2\n```"])
    seen: list[list[dict[str, str]]] = []

    def generate(messages):
        seen.append(list(messages))
        return next(replies)

    agent = next(h for h in HARNESSES if h.id == "agent")
    result = run_task(TASK, agent, generate)
    assert result["passed"] is True and result["attempts"] == 2
    assert "The tests failed" in seen[1][-1]["content"]


def test_single_attempt_harness_does_not_retry():
    single = next(h for h in HARNESSES if h.id == "tests")
    result = run_task(TASK, single, lambda messages: "def double(x):\n    return x\n")
    assert result["passed"] is False and result["attempts"] == 1
    assert json.dumps(result)
