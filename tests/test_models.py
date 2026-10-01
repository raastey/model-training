from pathlib import Path

from trainer.config import ProjectPaths
from trainer.models import (
    CODE_7B_MODEL_REPOSITORY,
    WRITER_MODEL_REPOSITORY,
    code_7b_model,
    code_model,
    writer_model,
)


def test_writer_model_is_not_ready_without_required_files(tmp_path: Path) -> None:
    model = writer_model(ProjectPaths(tmp_path))
    assert model.repository == WRITER_MODEL_REPOSITORY
    assert model.ready is False


def test_writer_model_requires_config_and_weights(tmp_path: Path) -> None:
    paths = ProjectPaths(tmp_path)
    model_path = writer_model(paths).path
    model_path.mkdir(parents=True)
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    assert writer_model(paths).ready is False
    (model_path / "model.safetensors").write_bytes(b"fixture")
    assert writer_model(paths).ready is True


def test_code_7b_candidate_is_separate_from_the_operational_code_base(tmp_path: Path) -> None:
    paths = ProjectPaths(tmp_path)
    assert code_7b_model(paths).path != code_model(paths).path
    assert code_7b_model(paths).repository == CODE_7B_MODEL_REPOSITORY
