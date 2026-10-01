"""Executable local smoke evaluation for the Code base or a future adapter."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from trainer.runtime import generate_writer_output


@dataclass(frozen=True)
class CodeSmokeCase:
    id: str
    prompt: str
    extension: str
    command: tuple[str, ...]
    expected: str


CASES = (
    CodeSmokeCase("python-reverse", "Return only Python code. Define reverse_text(value: str) -> str, then print(reverse_text('abc')).", ".py", ("python",), "cba"),
    CodeSmokeCase("swift-reverse", "Return only Swift code. Define reverseText(_ value: String) -> String, then print(reverseText(\"abc\")).", ".swift", ("swift",), "cba"),
)


@dataclass(frozen=True)
class CodePatchCase:
    id: str
    filename: str
    existing_code: str
    test_code: str
    request: str


@dataclass(frozen=True)
class RealPatchCase:
    id: str
    relative_source: str
    relative_test: str
    expected_line: str
    broken_line: str


PATCH_CASES = (
    CodePatchCase(
        "python-slugify-whitespace", "text_tools.py",
        "def slugify(value: str) -> str:\n    return value.lower().replace(\" \", \"-\")\n",
        """import unittest
from text_tools import slugify

class SlugifyTests(unittest.TestCase):
    def test_normalizes_whitespace_and_outer_spaces(self):
        self.assertEqual(slugify(\"  Hello   World  \"), \"hello-world\")
    def test_keeps_existing_simple_behavior(self):
        self.assertEqual(slugify(\"Hello World\"), \"hello-world\")

if __name__ == \"__main__\":
    unittest.main()
""",
        "Fix the bug in this existing Python module. Preserve its public function name and type signature. Return only the complete replacement contents of text_tools.py. The function must lowercase input, trim outer whitespace, and turn every run of internal whitespace into one hyphen.\n\nExisting text_tools.py:\n",
    ),
    CodePatchCase(
        "python-discount-boundary", "pricing.py",
        "def discounted_total(subtotal: float) -> float:\n    return subtotal * 0.9\n",
        """import unittest
from pricing import discounted_total

class DiscountTests(unittest.TestCase):
    def test_discount_at_threshold(self):
        self.assertEqual(discounted_total(100), 90)
    def test_no_discount_below_threshold(self):
        self.assertEqual(discounted_total(99), 99)
    def test_preserves_fractional_values(self):
        self.assertEqual(discounted_total(12.5), 12.5)

if __name__ == \"__main__\":
    unittest.main()
""",
        "Fix the bug in this existing Python module. Preserve its public function name and type signature. Return only the complete replacement contents of pricing.py. Apply a 10 percent discount only when subtotal is at least 100; otherwise return the original subtotal.\n\nExisting pricing.py:\n",
    ),
)


REAL_PATCH_CASES = (
    RealPatchCase("nauticgrid-entry-href-mutation", "lib/operator/entry-href.ts", "lib/operator/entry-href.test.ts", 'if (!access.signedIn) return "/operator";', 'if (!access.signedIn) return "/operator?upgrade=1";'),
    RealPatchCase("nauticgrid-confidence-stale-mutation", "lib/operator/confidence.ts", "lib/operator/confidence.test.ts", 'if (stale) return "LOW";', "if (stale) return confidence;"),
    RealPatchCase("nauticgrid-priority-watch-mutation", "lib/operator/priority.ts", "lib/operator/priority.test.ts", 'if (options?.commercialWatch) return "watch";', 'if (options?.commercialWatch) return "high";'),
)


def extract_code(output: str) -> str:
    match = re.search(r"```(?:\w+)?\n(.*?)```", output, flags=re.S)
    return (match.group(1) if match else output).strip()


def evaluate_code_smoke(model_path: Path, adapter_path: Path | None = None) -> list[dict[str, object]]:
    results = []
    for case in CASES:
        output = generate_writer_output(model_path, case.prompt, adapter_path, max_tokens=180)
        code = extract_code(output)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / f"main{case.extension}"
            target.write_text(code + "\n", encoding="utf-8")
            try:
                command = [sys.executable] if case.command == ("python",) else list(case.command)
                result = subprocess.run([*command, str(target)], capture_output=True, text=True, timeout=20)
                passed = result.returncode == 0 and result.stdout.strip() == case.expected
            except (OSError, subprocess.TimeoutExpired):
                passed = False
        results.append({"id": case.id, "passed": passed, "output_characters": len(output)})
    return results


def evaluate_code_patch(model_path: Path, adapter_path: Path | None = None) -> list[dict[str, object]]:
    """Ask for bounded replacement files and execute their local regression tests."""
    results = []
    for case in PATCH_CASES:
        output = generate_writer_output(model_path, case.request + case.existing_code, adapter_path, max_tokens=300)
        code = extract_code(output)
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / case.filename).write_text(code + "\n", encoding="utf-8")
            (workspace / "test_target.py").write_text(case.test_code, encoding="utf-8")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "unittest", "-q", "test_target.py"], cwd=workspace,
                    capture_output=True, text=True, timeout=20,
                )
                passed = result.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                passed = False
        results.append({"id": case.id, "passed": passed, "output_characters": len(output)})
    return results


def evaluate_nauticgrid_entry_patch(
    model_path: Path, workspace_root: Path, adapter_path: Path | None = None,
) -> list[dict[str, object]]:
    """Evaluate a controlled mutation of a real NauticGrid unit using its real test file.

    The live repository is read only. A temporary copy contains a deliberately broken
    line, and its existing Vitest test must pass after the model supplies a replacement.
    """
    repository = workspace_root / "nauticgrid"
    modules = repository / "node_modules"
    if not modules.is_dir():
        raise ValueError("NauticGrid local node_modules is unavailable.")
    results = []
    for case in REAL_PATCH_CASES:
        source = repository / case.relative_source
        test = repository / case.relative_test
        if not source.is_file() or not test.is_file():
            raise ValueError(f"NauticGrid fixture source or test is unavailable: {case.id}")
        original = source.read_text(encoding="utf-8")
        if case.expected_line not in original:
            raise ValueError(f"NauticGrid fixture source no longer matches its verified baseline: {case.id}")
        broken = original.replace(case.expected_line, case.broken_line, 1)
        filename = source.name
        prompt = (
            f"Fix the bug in this existing TypeScript module. Preserve all exported names and types. "
            f"Return only the complete replacement contents of {filename}. Use the existing tests as the behavioral contract.\n\n"
            f"Existing {filename}:\n{broken}\n\nExisting {test.name}:\n{test.read_text(encoding='utf-8')}"
        )
        output = generate_writer_output(model_path, prompt, adapter_path, max_tokens=700)
        code = extract_code(output)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            target_dir = temporary / source.parent.relative_to(repository)
            target_dir.mkdir(parents=True)
            (target_dir / filename).write_text(code + "\n", encoding="utf-8")
            (target_dir / test.name).write_text(test.read_text(encoding="utf-8"), encoding="utf-8")
            os.symlink(modules, temporary / "node_modules")
            try:
                result = subprocess.run(
                    [str(modules / ".bin" / "vitest"), "run", case.relative_test], cwd=temporary,
                    capture_output=True, text=True, timeout=30,
                )
                passed = result.returncode == 0
                failure_kind = None if passed else "test_failed"
            except (OSError, subprocess.TimeoutExpired):
                passed = False
                failure_kind = "runner_unavailable"
        record: dict[str, object] = {"id": case.id, "passed": passed, "output_characters": len(output)}
        if failure_kind:
            record["failure_kind"] = failure_kind
        results.append(record)
    return results
