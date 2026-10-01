"""Agentic code evaluation: the model edits a file, the real tests run, failures are fed back.

Three harness conditions isolate what context and feedback add on top of the same model:
the request alone, the request plus the test file, and a test-feedback loop.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from trainer.code_evaluation import extract_code

ChatGenerator = Callable[[list[dict[str, str]]], str]

SYSTEM = "You are a careful software engineer. Reply with only the complete replacement file in one fenced code block."


@dataclass(frozen=True)
class CodeTask:
    id: str
    filename: str
    request: str
    source: str
    tests: str


@dataclass(frozen=True)
class Harness:
    id: str
    label: str
    show_tests: bool
    attempts: int


HARNESSES = (
    Harness("request", "Request only, one attempt", False, 1),
    Harness("tests", "Request + test file, one attempt", True, 1),
    Harness("agent", "Request + tests + failure feedback, up to 3 attempts", True, 3),
)


def load_code_tasks(path: Path) -> list[CodeTask]:
    return [CodeTask(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def run_tests(task: CodeTask, source: str, timeout: int = 20) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        (workspace / task.filename).write_text(source, encoding="utf-8")
        (workspace / "test_task.py").write_text(task.tests, encoding="utf-8")
        try:
            result = subprocess.run([sys.executable, "-m", "unittest", "-q", "test_task.py"], cwd=workspace,
                                    capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, "Tests timed out."
        return result.returncode == 0, (result.stdout + result.stderr)[-1500:]


def first_prompt(task: CodeTask, show_tests: bool) -> str:
    prompt = f"{task.request}\n\nCurrent {task.filename}:\n```python\n{task.source}```"
    if show_tests:
        prompt += f"\n\nThe file must pass these tests:\n```python\n{task.tests}```"
    return prompt + f"\n\nReturn the complete corrected {task.filename}."


def run_task(task: CodeTask, harness: Harness, generate: ChatGenerator) -> dict[str, object]:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": first_prompt(task, harness.show_tests)}]
    started = time.monotonic()
    passed, attempts, log = False, 0, ""
    while attempts < harness.attempts and not passed:
        attempts += 1
        reply = generate(messages)
        passed, log = run_tests(task, extract_code(reply) + "\n")
        messages += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": f"The tests failed:\n```\n{log}\n```\nFix the file. Return the complete corrected {task.filename}."}]
    return {"id": task.id, "passed": passed, "attempts": attempts, "seconds": round(time.monotonic() - started, 1),
            "failure_tail": None if passed else log[-400:]}


def run_code_study(tasks: list[CodeTask], models: dict[str, ChatGenerator]) -> dict[str, object]:
    rows = []
    for model_id, generate in models.items():
        for harness in HARNESSES:
            results = [run_task(task, harness, generate) for task in tasks]
            passed = sum(bool(item["passed"]) for item in results)
            rows.append({"model": model_id, "harness": harness.id, "label": harness.label, "passed": passed,
                         "total": len(results), "seconds": round(sum(float(r["seconds"]) for r in results), 1),
                         "results": results})
    return {"kind": "agentic_code_study", "tasks": [task.id for task in tasks], "rows": rows}


def mlx_chat_generator(model_path: Path, max_tokens: int = 700) -> ChatGenerator:
    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(str(model_path))

    def run(messages: list[dict[str, str]]) -> str:
        prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        mx.random.seed(2026)
        return generate(model, tokenizer, prompt, max_tokens=max_tokens, sampler=make_sampler(temp=0.2))

    return run


def code_markdown_table(report: dict[str, object]) -> str:
    lines = ["| Model | Harness | Tasks passed | Total time (s) |", "|---|---|---|---|"]
    for row in report["rows"]:
        lines.append(f"| {row['model']} | {row['label']} | {row['passed']}/{row['total']} | {row['seconds']:.0f} |")
    return "\n".join(lines) + "\n"
