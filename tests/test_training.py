from pathlib import Path

import pytest

from trainer.config import ProjectPaths
from trainer.training import (
    mark_run_aborted,
    mark_run_completed,
    mark_run_rejected,
    prepare_code_7b_v8_run,
    prepare_code_patch_run,
    prepare_code_smoke_run,
    prepare_code_v7_run,
    prepare_code_v8_run,
    prepare_writer_smoke_run,
)


def test_smoke_run_requires_a_downloaded_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not downloaded"):
        prepare_writer_smoke_run(ProjectPaths(tmp_path))


def test_code_smoke_run_requires_a_downloaded_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not downloaded"):
        prepare_code_smoke_run(ProjectPaths(tmp_path))


def test_code_patch_run_requires_a_downloaded_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not downloaded"):
        prepare_code_patch_run(ProjectPaths(tmp_path))


def test_code_v7_run_requires_a_downloaded_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Code model"):
        prepare_code_v7_run(ProjectPaths(tmp_path))


def test_code_v8_run_requires_a_downloaded_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Code model"):
        prepare_code_v8_run(ProjectPaths(tmp_path))


def test_code_7b_v8_run_requires_a_downloaded_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Code 7B"):
        prepare_code_7b_v8_run(ProjectPaths(tmp_path))


def test_mark_run_completed_requires_an_adapter(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "writer" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "run-manifest.json").write_text(
        '{"adapter_path": "adapters/writer/fixture"}', encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="non-empty adapter"):
        mark_run_completed(run_dir)


def test_only_candidate_runs_can_be_rejected(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "writer" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "run-manifest.json").write_text('{"status": "candidate"}', encoding="utf-8")
    mark_run_rejected(run_dir, "repetition regression")
    assert '"rejected"' in (run_dir / "run-manifest.json").read_text(encoding="utf-8")


def test_prepared_run_can_be_marked_aborted(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "code" / "fixture"
    run_dir.mkdir(parents=True)
    (run_dir / "run-manifest.json").write_text('{"status": "prepared"}', encoding="utf-8")
    mark_run_aborted(run_dir, "token limit")
    assert '"aborted"' in (run_dir / "run-manifest.json").read_text(encoding="utf-8")
