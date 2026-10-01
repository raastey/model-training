"""Configuration that never persists secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def local_artifact_dirs(self) -> tuple[Path, ...]:
        return tuple(self.root / name for name in (
            "corpora", "datasets", "models", "adapters", "evals", "reports", "runs", "logs"
        ))


def project_paths(root: Path | None = None) -> ProjectPaths:
    return ProjectPaths((root or Path.cwd()).resolve())


def huggingface_token(root: Path) -> str | None:
    """Read the token from environment or a project-local .env file, without logging it."""
    if token := os.environ.get("HF_TOKEN"):
        return token
    env_file = root / ".env"
    if not env_file.is_file():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("HF_TOKEN="):
            return line.removeprefix("HF_TOKEN=").strip() or None
    return None


def huggingface_token_present(root: Path) -> bool:
    """Return availability only; callers must never display the token."""
    return bool(huggingface_token(root))
