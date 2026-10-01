from pathlib import Path

from trainer.config import ProjectPaths
from trainer.doctor import inspect


def test_doctor_does_not_expose_a_token(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_testtoken")

    report = inspect(ProjectPaths(tmp_path))

    assert report.hf_token_present is True
    assert "hf_testtoken" not in str(report)


def test_doctor_detects_project_local_token_without_exposing_it(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("HF_TOKEN=hf_localtesttoken\\n", encoding="utf-8")

    report = inspect(ProjectPaths(tmp_path))

    assert report.hf_token_present is True
    assert "hf_localtesttoken" not in str(report)
