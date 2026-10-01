"""Blind local Writer evaluation against the unmodified base model."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from trainer.config import ProjectPaths
from trainer.models import writer_model

WRITER_PROMPTS = (
    ("evidence", "Write a concise opening paragraph about why evidence matters in public debate."),
    ("accountability", "Write a concise opening paragraph arguing why public institutions must be judged by outcomes, not promises."),
    ("power", "Write a concise opening paragraph about how power becomes hardest to see when it is treated as ordinary."),
)


@dataclass(frozen=True)
class BlindEvaluation:
    directory: Path
    review_path: Path


def _generate(model_path: Path, prompt: str, adapter_path: Path | None = None) -> str:
    command = [
        str(Path(sys.executable).with_name("mlx_lm.generate")), "--model", str(model_path),
        "--prompt", prompt, "--max-tokens", "180", "--temp", "0.3", "--seed", "2026", "--verbose", "false",
    ]
    if adapter_path:
        command.extend(["--adapter-path", str(adapter_path)])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _order(prompt_id: str) -> tuple[str, str]:
    return ("candidate", "base") if int(hashlib.sha256(prompt_id.encode()).hexdigest(), 16) % 2 else ("base", "candidate")


def create_blind_writer_evaluation(paths: ProjectPaths, candidate_run: str) -> BlindEvaluation:
    if "/" in candidate_run or candidate_run in {"", ".", ".."}:
        raise ValueError("Candidate run ID is invalid.")
    model = writer_model(paths)
    if not model.ready:
        raise ValueError("Writer model is not downloaded.")
    adapter_path = paths.root / "adapters" / "writer" / candidate_run
    if not (adapter_path / "adapters.safetensors").is_file():
        raise ValueError(f"No ready Writer adapter for run: {candidate_run}")
    directory = paths.root / "evals" / "writer" / f"{candidate_run}-vs-base"
    if directory.exists():
        raise ValueError(f"Evaluation directory already exists: {directory}")
    directory.mkdir(parents=True)
    mapping: dict[str, dict[str, str]] = {}
    sections = ["# Blind Writer comparison", "\nFor each prompt, choose **A** or **B** based only on which output better reflects the writing you want.\n"]
    for prompt_id, prompt in WRITER_PROMPTS:
        responses = {"base": _generate(model.path, prompt), "candidate": _generate(model.path, prompt, adapter_path)}
        first, second = _order(prompt_id)
        mapping[prompt_id] = {"A": first, "B": second}
        sections.extend((f"## {prompt_id}", f"**Prompt:** {prompt}", "", f"### A\n\n{responses[first]}", "", f"### B\n\n{responses[second]}", ""))
    review_path = directory / "blind-review.md"
    review_path.write_text("\n".join(sections), encoding="utf-8")
    (directory / "private-mapping.json").write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    (directory / "evaluation-manifest.json").write_text(
        json.dumps({"candidate_run": candidate_run, "created_at": datetime.now(UTC).isoformat(), "prompt_ids": [item[0] for item in WRITER_PROMPTS]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return BlindEvaluation(directory, review_path)
