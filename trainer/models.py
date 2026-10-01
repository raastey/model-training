"""Local model registry and safe Hugging Face downloads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from huggingface_hub import snapshot_download

from trainer.config import ProjectPaths, huggingface_token

WRITER_MODEL_REPOSITORY = "mlx-community/Qwen2.5-3B-Instruct-4bit"
CODE_MODEL_REPOSITORY = "mlx-community/Qwen2.5-Coder-3B-Instruct-4bit"
CODE_7B_MODEL_REPOSITORY = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"


@dataclass(frozen=True)
class LocalModel:
    space: str
    repository: str
    path: Path
    ready: bool


def writer_model_path(paths: ProjectPaths) -> Path:
    return paths.root / "models" / "bases" / "writer" / "qwen2.5-3b-instruct-4bit"


def writer_model(paths: ProjectPaths) -> LocalModel:
    path = writer_model_path(paths)
    return LocalModel(
        space="writer",
        repository=WRITER_MODEL_REPOSITORY,
        path=path,
        ready=(path / "config.json").is_file() and (path / "model.safetensors").is_file(),
    )


def code_model_path(paths: ProjectPaths) -> Path:
    return paths.root / "models" / "bases" / "code" / "qwen2.5-coder-3b-instruct-4bit"


def code_model(paths: ProjectPaths) -> LocalModel:
    path = code_model_path(paths)
    return LocalModel(
        space="code", repository=CODE_MODEL_REPOSITORY, path=path,
        ready=(path / "config.json").is_file() and (path / "model.safetensors").is_file(),
    )


def code_7b_model_path(paths: ProjectPaths) -> Path:
    return paths.root / "models" / "bases" / "code" / "qwen2.5-coder-7b-instruct-4bit"


def code_7b_model(paths: ProjectPaths) -> LocalModel:
    path = code_7b_model_path(paths)
    return LocalModel(
        space="code-7b", repository=CODE_7B_MODEL_REPOSITORY, path=path,
        ready=(path / "config.json").is_file() and (path / "model.safetensors").is_file(),
    )


def download_writer_model(paths: ProjectPaths) -> LocalModel:
    model = writer_model(paths)
    snapshot_download(repo_id=model.repository, local_dir=model.path, token=huggingface_token(paths.root))
    verified = writer_model(paths)
    if not verified.ready:
        raise RuntimeError("Writer model download finished without required model files.")
    manifest = {
        "space": verified.space,
        "repository": verified.repository,
        "path": str(verified.path.relative_to(paths.root)),
        "mlx_version": version("mlx"),
        "mlx_lm_version": version("mlx-lm"),
    }
    (verified.path / "sixtwelve-model-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return verified


def download_code_model(paths: ProjectPaths) -> LocalModel:
    model = code_model(paths)
    snapshot_download(repo_id=model.repository, local_dir=model.path, token=huggingface_token(paths.root))
    verified = code_model(paths)
    if not verified.ready:
        raise RuntimeError("Code model download finished without required model files.")
    manifest = {
        "space": verified.space, "repository": verified.repository,
        "path": str(verified.path.relative_to(paths.root)), "mlx_version": version("mlx"),
        "mlx_lm_version": version("mlx-lm"),
    }
    (verified.path / "sixtwelve-model-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return verified


def download_code_7b_model(paths: ProjectPaths) -> LocalModel:
    """Download a separately benchmarked Code-base candidate; never replaces the 3B base."""
    model = code_7b_model(paths)
    snapshot_download(repo_id=model.repository, local_dir=model.path, token=huggingface_token(paths.root))
    verified = code_7b_model(paths)
    if not verified.ready:
        raise RuntimeError("Code 7B model download finished without required model files.")
    manifest = {
        "space": verified.space, "repository": verified.repository,
        "path": str(verified.path.relative_to(paths.root)), "mlx_version": version("mlx"),
        "mlx_lm_version": version("mlx-lm"), "role": "unpromoted-code-base-candidate",
    }
    (verified.path / "sixtwelve-model-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return verified
