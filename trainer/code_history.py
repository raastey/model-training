"""Derive real, test-guided repair episodes from local Git history."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from trainer.code import (
    CODE_TRAINING_LANGUAGES,
    _is_test_document,
    _language,
    code_dataset_dir,
    validate_code_dataset,
)
from trainer.code_tasks import APPROVED_V5_TASKS
from trainer.config import ProjectPaths

EVALUATION_PROJECTS = frozenset(task.project_directory for task in APPROVED_V5_TASKS)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)
    return result.stdout if result.returncode == 0 else ""


def _git_file(repo: Path, revision: str, path: str) -> str | None:
    result = subprocess.run(["git", "-C", str(repo), "show", f"{revision}:{path}"], capture_output=True, text=True, timeout=30)
    return result.stdout if result.returncode == 0 else None


def _is_test_path(path: str) -> bool:
    from trainer.code import CodeDocument
    candidate = CodeDocument("history", "history", path, "", "", _language(Path(path)), 0)
    return _is_test_document(candidate)


def historical_repair_episodes(paths: ProjectPaths, limit: int = 300) -> list[dict[str, object]]:
    """Return deduplicated old-source/test/new-source episodes from user-project commits."""
    episodes: list[dict[str, object]] = []
    seen: set[str] = set()
    workspace = paths.root.parent
    repositories = sorted(path for path in workspace.iterdir() if (path / ".git").is_dir() and path.name not in EVALUATION_PROJECTS and path.name not in {"writings", "model-training"})
    for repo in repositories:
        commits = _git(repo, "rev-list", "--max-count=80", "HEAD").splitlines()
        for commit in commits:
            parent = _git(repo, "rev-parse", f"{commit}^").strip()
            if not parent:
                continue
            changed = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", parent, commit).splitlines()
            tests = [path for path in changed if _is_test_path(path) and Path(path).suffix.lstrip(".") in CODE_TRAINING_LANGUAGES]
            sources = [path for path in changed if not _is_test_path(path) and Path(path).suffix.lstrip(".") in CODE_TRAINING_LANGUAGES]
            if not tests or not sources:
                continue
            for source_path in sources:
                old = _git_file(repo, parent, source_path)
                new = _git_file(repo, commit, source_path)
                if not old or not new or old == new or len(old) + len(new) > 10000:
                    continue
                stem = Path(source_path).stem.lower()
                matching = [path for path in tests if stem in Path(path).stem.lower()]
                test_path = (matching or tests)[0]
                test = _git_file(repo, commit, test_path)
                if not test or len(test) > 6000:
                    continue
                fingerprint = hashlib.sha256((old + "\0" + new + "\0" + test).encode()).hexdigest()
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                episodes.append({"project": repo.name, "commit": commit, "source_path": source_path, "test_path": test_path, "language": _language(Path(source_path)), "old": old, "new": new, "test": test})
                if len(episodes) >= limit:
                    return episodes
    return episodes


def build_historical_repair_dataset(paths: ProjectPaths, name: str = "v8", limit: int = 300) -> dict[str, int]:
    """Build a real-history repair dataset; evaluation projects are always excluded."""
    output = code_dataset_dir(paths, name)
    if output.exists():
        raise ValueError(f"Dataset output already exists: {output}")
    from transformers import AutoTokenizer

    from trainer.models import code_model
    tokenizer = AutoTokenizer.from_pretrained(code_model(paths).path)
    rows = {"train": [], "validation": [], "test": []}
    metadata = []
    episodes = historical_repair_episodes(paths, limit)
    projects = sorted({str(episode["project"]) for episode in episodes})
    project_splits = {
        project: "test" if index == 0 else "validation" if index == 1 else "train"
        for index, project in enumerate(projects)
    }
    for episode in episodes:
        filename = Path(str(episode["source_path"])).name
        messages = [
            {"role": "system", "content": "You are SIXTWELVE Code. Return only the complete requested replacement file. Preserve public names and types."},
            {"role": "user", "content": f"Fix the regression in {filename}. Return only the complete replacement contents of {filename}. Use the changed test as the behavioral contract.\n\nExisting {filename}:\n{episode['old']}\n\nExisting test {Path(str(episode['test_path'])).name}:\n{episode['test']}"},
            {"role": "assistant", "content": episode["new"]},
        ]
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        tokens = len(tokenizer.encode(rendered, add_special_tokens=False))
        if tokens > 1800:
            continue
        split = project_splits[str(episode["project"])]
        rows[split].append({"messages": messages})
        metadata.append({"id": f"git-{str(episode['commit'])[:12]}-{len(metadata):03d}", "project": episode["project"], "language": episode["language"], "split": split, "kind": "verified-git-repair", "test_source_id": episode["test_path"], "source_path": episode["source_path"], "commit": episode["commit"], "tokens": tokens})
    if len(metadata) < 30:
        raise ValueError(f"Only {len(metadata)} token-safe historical repair episodes found; requires 30.")
    output.mkdir(parents=True)
    for split, values in rows.items():
        (output / f"{split}.jsonl").write_text("".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values), encoding="utf-8")
    manifest = {"schema_version": 6, "space": "code", "dataset_name": name, "profile": "real-git-history-repair", "split_counts": {key: len(value) for key, value in rows.items()}, "languages": dict(Counter(item["language"] for item in metadata)), "projects": dict(Counter(item["project"] for item in metadata)), "examples": metadata, "held_out_projects": sorted(EVALUATION_PROJECTS), "minimum_test_contract_examples": len(metadata), "test_contract_examples": len(metadata), "source_artifacts_retained": False}
    (output / "dataset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_code_dataset(output)
    return manifest["split_counts"]
