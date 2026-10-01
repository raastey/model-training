"""Reproducible, local MLX-LM smoke-run preparation."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from trainer.code import code_dataset_dir, validate_code_dataset
from trainer.config import ProjectPaths
from trainer.dataset import validate_writer_dataset, writer_dataset_dir
from trainer.models import code_7b_model, code_model, writer_model


@dataclass(frozen=True)
class PreparedRun:
    run_id: str
    run_dir: Path
    config_path: Path


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_writer_run(
    paths: ProjectPaths, run_id: str, dataset_name: str, iters: int, num_layers: int, save_every: int,
    profile: str,
) -> PreparedRun:
    """Stage a validated immutable dataset for a local Writer QLoRA candidate run."""
    model = writer_model(paths)
    if not model.ready:
        raise ValueError("Writer model is not downloaded.")
    dataset_dir = writer_dataset_dir(paths, dataset_name)
    counts = validate_writer_dataset(dataset_dir)
    run_dir = paths.root / "runs" / "writer" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "writer" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text(
        "\n".join(
            (
                f"model: {model.path}",
                "train: true",
                f"data: {data_dir}",
                "fine_tune_type: lora",
                "mask_prompt: true",
                f"num_layers: {num_layers}",
                "batch_size: 1",
                f"iters: {iters}",
                "val_batches: 2",
                "learning_rate: 1e-5",
                "steps_per_report: 1",
                f"steps_per_eval: {max(5, iters // 4)}",
                f"save_every: {save_every}",
                "test: true",
                "test_batches: 2",
                "max_seq_length: 2048",
                "grad_checkpoint: true",
                "seed: 42",
                f"adapter_path: {adapter_dir}",
                "",
            )
        ),
        encoding="utf-8",
    )
    manifest = {
        "run_id": run_id,
        "space": "writer",
        "profile": profile,
        "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(),
        "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"),
        "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)),
        "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def prepare_writer_smoke_run(paths: ProjectPaths, run_id: str = "writer-smoke-001") -> PreparedRun:
    return _prepare_writer_run(paths, run_id, "v1", iters=10, num_layers=4, save_every=10, profile="smoke")


def prepare_writer_chunked_run(paths: ProjectPaths, run_id: str = "writer-chunked-001") -> PreparedRun:
    return _prepare_writer_run(paths, run_id, "v2", iters=100, num_layers=8, save_every=25, profile="chunked-initial")


def prepare_writer_context_run(paths: ProjectPaths, run_id: str = "writer-context-001") -> PreparedRun:
    return _prepare_writer_run(paths, run_id, "v3", iters=150, num_layers=8, save_every=25, profile="context-initial")


def prepare_writer_context_rebalanced_run(paths: ProjectPaths, run_id: str = "writer-context-002") -> PreparedRun:
    """Prepare the smaller, authenticity-first all-library context candidate."""
    return _prepare_writer_run(paths, run_id, "v5", iters=100, num_layers=8, save_every=25, profile="context-rebalanced")


def prepare_writer_voice_regularized_run(paths: ProjectPaths, run_id: str = "writer-voice-001") -> PreparedRun:
    """Prepare a small authentic-prose-only all-library voice candidate."""
    return _prepare_writer_run(paths, run_id, "v6", iters=50, num_layers=4, save_every=25, profile="voice-authentic-regularized")


def prepare_code_smoke_run(paths: ProjectPaths, run_id: str = "code-smoke-001") -> PreparedRun:
    """Stage one small, non-promoting Code LoRA candidate from the Code-only v1 dataset."""
    model = code_model(paths)
    if not model.ready:
        raise ValueError("Code model is not downloaded.")
    dataset_dir = code_dataset_dir(paths, "v1")
    counts = validate_code_dataset(dataset_dir)
    run_dir = paths.root / "runs" / "code" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "code" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text(
        "\n".join((
            f"model: {model.path}", "train: true", f"data: {data_dir}", "fine_tune_type: lora",
            "mask_prompt: true", "num_layers: 4", "batch_size: 1", "iters: 50", "val_batches: 2",
            "learning_rate: 1e-5", "steps_per_report: 1", "steps_per_eval: 12", "save_every: 25",
            "test: true", "test_batches: 2", "max_seq_length: 2048", "grad_checkpoint: true",
            "seed: 42", f"adapter_path: {adapter_dir}", "",
        )), encoding="utf-8",
    )
    manifest = {
        "run_id": run_id, "space": "code", "profile": "smoke-project-balanced", "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(), "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"), "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)), "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def prepare_code_patch_run(paths: ProjectPaths, run_id: str = "code-patch-001") -> PreparedRun:
    """Stage a bounded Code-only patch-behavior candidate from v2."""
    model = code_model(paths)
    if not model.ready:
        raise ValueError("Code model is not downloaded.")
    dataset_dir = code_dataset_dir(paths, "v4")
    counts = validate_code_dataset(dataset_dir)
    run_dir = paths.root / "runs" / "code" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "code" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text("\n".join((
        f"model: {model.path}", "train: true", f"data: {data_dir}", "fine_tune_type: lora", "mask_prompt: true",
        "num_layers: 4", "batch_size: 1", "iters: 75", "val_batches: 2", "learning_rate: 8e-6", "steps_per_report: 1",
        "steps_per_eval: 15", "save_every: 25", "test: true", "test_batches: 2", "max_seq_length: 2048",
        "grad_checkpoint: true", "seed: 42", f"adapter_path: {adapter_dir}", "",
    )), encoding="utf-8")
    manifest = {
        "run_id": run_id, "space": "code", "profile": "patch-oriented", "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(), "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"), "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)), "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def prepare_code_v5_run(paths: ProjectPaths, run_id: str = "code-v5-001") -> PreparedRun:
    """Stage the approved held-out Code v5 candidate; it is never promoted automatically."""
    model = code_model(paths)
    if not model.ready:
        raise ValueError("Code model is not downloaded.")
    dataset_dir = code_dataset_dir(paths, "v5")
    counts = validate_code_dataset(dataset_dir)
    run_dir = paths.root / "runs" / "code" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "code" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text("\n".join((
        f"model: {model.path}", "train: true", f"data: {data_dir}", "fine_tune_type: lora", "mask_prompt: true",
        "num_layers: 4", "batch_size: 1", "iters: 50", "val_batches: 2", "learning_rate: 8e-6", "steps_per_report: 1",
        "steps_per_eval: 12", "save_every: 25", "test: true", "test_batches: 2", "max_seq_length: 2048",
        "grad_checkpoint: true", "seed: 42", f"adapter_path: {adapter_dir}", "",
    )), encoding="utf-8")
    manifest = {
        "run_id": run_id, "space": "code", "profile": "v5-held-out-patch-oriented", "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(), "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"), "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)), "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def prepare_code_v7_run(paths: ProjectPaths, run_id: str = "code-v7-001") -> PreparedRun:
    """Stage a small repair-first candidate from the independent V7 curriculum."""
    model = code_model(paths)
    if not model.ready:
        raise ValueError("Code model is not downloaded.")
    dataset_dir = code_dataset_dir(paths, "v7")
    counts = validate_code_dataset(dataset_dir)
    manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("test_contract_examples") != sum(manifest.get("split_counts", {}).values()):
        raise ValueError("V7 must be entirely test-guided repair episodes.")
    run_dir = paths.root / "runs" / "code" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "code" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text("\n".join((
        f"model: {model.path}", "train: true", f"data: {data_dir}", "fine_tune_type: lora", "mask_prompt: true",
        "num_layers: 2", "batch_size: 1", "iters: 30", "val_batches: 2", "learning_rate: 5e-6", "steps_per_report: 1",
        "steps_per_eval: 10", "save_every: 15", "test: true", "test_batches: 2", "max_seq_length: 2048",
        "grad_checkpoint: true", "seed: 42", f"adapter_path: {adapter_dir}", "",
    )), encoding="utf-8")
    manifest = {
        "run_id": run_id, "space": "code", "profile": "v7-repair-first-minimal", "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(), "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"), "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)), "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def prepare_code_v8_run(paths: ProjectPaths, run_id: str = "code-v8-001") -> PreparedRun:
    """Stage a small candidate trained only on real local Git repair history."""
    model = code_model(paths)
    if not model.ready:
        raise ValueError("Code model is not downloaded.")
    dataset_dir = code_dataset_dir(paths, "v8")
    counts = validate_code_dataset(dataset_dir)
    dataset_manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
    if dataset_manifest.get("profile") != "real-git-history-repair":
        raise ValueError("V8 must contain only real Git repair episodes.")
    run_dir = paths.root / "runs" / "code" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "code" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text("\n".join((
        f"model: {model.path}", "train: true", f"data: {data_dir}", "fine_tune_type: lora", "mask_prompt: true",
        "num_layers: 2", "batch_size: 1", "iters: 35", "val_batches: 2", "learning_rate: 4e-6", "steps_per_report: 1",
        "steps_per_eval: 10", "save_every: 20", "test: true", "test_batches: 2", "max_seq_length: 2048",
        "grad_checkpoint: true", "seed: 42", f"adapter_path: {adapter_dir}", "",
    )), encoding="utf-8")
    manifest = {
        "run_id": run_id, "space": "code", "profile": "v8-real-history-repair", "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(), "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"), "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)), "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def prepare_code_7b_v8_run(paths: ProjectPaths, run_id: str = "code-7b-v8-001") -> PreparedRun:
    """Stage a minimal real-history adapter for the separately benchmarked 7B base."""
    model = code_7b_model(paths)
    if not model.ready:
        raise ValueError("Code 7B model is not downloaded.")
    dataset_dir = code_dataset_dir(paths, "v8")
    counts = validate_code_dataset(dataset_dir)
    run_dir = paths.root / "runs" / "code" / run_id
    if run_dir.exists():
        raise ValueError(f"Run directory already exists: {run_dir}")
    data_dir = run_dir / "data"
    adapter_dir = paths.root / "adapters" / "code" / run_id
    data_dir.mkdir(parents=True)
    adapter_dir.mkdir(parents=True)
    for source_name, target_name in (("train.jsonl", "train.jsonl"), ("validation.jsonl", "valid.jsonl"), ("test.jsonl", "test.jsonl")):
        shutil.copy2(dataset_dir / source_name, data_dir / target_name)
    config_path = run_dir / "config.yaml"
    config_path.write_text("\n".join((
        f"model: {model.path}", "train: true", f"data: {data_dir}", "fine_tune_type: lora", "mask_prompt: true",
        "num_layers: 2", "batch_size: 1", "iters: 20", "val_batches: 1", "learning_rate: 2e-6", "steps_per_report: 1",
        "steps_per_eval: 10", "save_every: 20", "test: true", "test_batches: 1", "max_seq_length: 2048",
        "grad_checkpoint: true", "seed: 42", f"adapter_path: {adapter_dir}", "",
    )), encoding="utf-8")
    manifest = {
        "run_id": run_id, "space": "code", "profile": "7b-v8-real-history-minimal", "status": "prepared",
        "prepared_at": datetime.now(UTC).isoformat(), "base_model": model.repository,
        "dataset_manifest_sha256": _hash_file(dataset_dir / "dataset-manifest.json"), "dataset_counts": counts,
        "config": str(config_path.relative_to(paths.root)), "adapter_path": str(adapter_dir.relative_to(paths.root)),
    }
    (run_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedRun(run_id, run_dir, config_path)


def execute_prepared_run(prepared: PreparedRun) -> None:
    """Execute exactly the prepared local config; never publishes or promotes an adapter."""
    subprocess.run(
        [str(Path(sys.executable).with_name("mlx_lm.lora")), "--config", str(prepared.config_path)],
        check=True,
    )
    mark_run_completed(prepared.run_dir)


def mark_run_completed(run_dir: Path) -> None:
    """Record successful local completion only after the adapter file exists."""
    manifest_path = run_dir / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project_root = run_dir.parents[2]
    adapter_path = project_root / manifest["adapter_path"] / "adapters.safetensors"
    if not adapter_path.is_file() or adapter_path.stat().st_size == 0:
        raise RuntimeError("Training completed without a non-empty adapter file.")
    manifest |= {
        "status": "candidate",
        "completed_at": datetime.now(UTC).isoformat(),
        "adapter_file": str(adapter_path.relative_to(project_root)),
        "adapter_bytes": adapter_path.stat().st_size,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mark_run_rejected(run_dir: Path, reason: str) -> None:
    """Retain a failed candidate and its evidence without allowing promotion."""
    manifest_path = run_dir / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "candidate":
        raise ValueError("Only completed candidate runs can be rejected.")
    manifest |= {
        "status": "rejected",
        "rejected_at": datetime.now(UTC).isoformat(),
        "rejection_reason": reason,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mark_run_aborted(run_dir: Path, reason: str) -> None:
    """Retain an intentionally stopped run and its reason without treating it as a candidate."""
    manifest_path = run_dir / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "prepared":
        raise ValueError("Only a prepared run may be marked aborted.")
    manifest |= {"status": "aborted", "aborted_at": datetime.now(UTC).isoformat(), "abort_reason": reason}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
