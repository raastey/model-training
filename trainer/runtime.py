"""Local, inspectable Writer generation and context-runtime quality checks."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from trainer.benchmarks import runtime_output_issue
from trainer.context import RetrievedChunk, format_working_context


@dataclass(frozen=True)
class ContextRuntimeResult:
    output: str
    issue: str | None
    retrieved: tuple[RetrievedChunk, ...]


def writer_context_prompt(query: str, retrieved: list[RetrievedChunk]) -> str:
    """Give the model a bounded source package and an answer-only instruction."""
    return (
        format_working_context(query, retrieved)
        + "\n\nWrite a direct answer to the objective. Do not mention this working context, source labels, or these instructions. "
        "Follow the objective's requested format and length exactly. Use only claims supported by the supplied material; "
        "if it is insufficient, say so plainly. For a broad conceptual question, begin with the general claim and avoid named people, organizations, places, or cases unless the objective specifically needs them."
    )


def generate_writer_output(model_path: Path, prompt: str, adapter_path: Path | None = None, max_tokens: int = 400) -> str:
    command = [
        str(Path(sys.executable).with_name("mlx_lm.generate")), "--model", str(model_path),
        "--prompt", prompt, "--max-tokens", str(max_tokens), "--temp", "0.3", "--seed", "2026", "--verbose", "false",
    ]
    if adapter_path:
        command.extend(["--adapter-path", str(adapter_path)])
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def evaluate_context_output(output: str, retrieved: list[RetrievedChunk]) -> ContextRuntimeResult:
    return ContextRuntimeResult(output, runtime_output_issue(output), tuple(retrieved))


def complete_sentences_for_display(output: str) -> str:
    """Avoid showing a cut-off final fragment when a local token ceiling is reached."""
    stripped = output.strip()
    if not stripped or re.search(r"[.!?][\]\"')]*$", stripped):
        return stripped
    endings = list(re.finditer(r"[.!?][\]\"')]*", stripped))
    if not endings:
        return stripped
    return stripped[:endings[-1].end()].rstrip()


def fit_complete_sentences_to_words(output: str, max_words: int | None) -> str:
    """Apply an optional display word budget without returning a broken sentence."""
    if max_words is None:
        return output
    sentences = re.findall(r".+?[.!?](?:[\]\"')]+)?(?=\s|$)", output, flags=re.S)
    kept: list[str] = []
    used = 0
    for sentence in sentences:
        words = len(sentence.split())
        if used + words > max_words:
            break
        kept.append(sentence.strip())
        used += words
    return " ".join(kept) or output
