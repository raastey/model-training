from pathlib import Path

import pytest

from trainer.code import (
    CodeDocument,
    _find_test_document,
    _is_training_document,
    build_code_dataset,
    import_code_corpus,
    inspect_code_repository,
    inspect_code_workspace,
)
from trainer.code_curriculum import _episode
from trainer.code_history import EVALUATION_PROJECTS
from trainer.code_tasks import (
    CodeMaintenanceTask,
    build_code_task_manifest,
    temporary_task_workspace,
    validate_code_task_manifest,
)
from trainer.config import ProjectPaths


def test_code_inspection_excludes_generated_files_and_quarantines_secrets(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (repository / "secret.py").write_text("token = 'hf_abcdefghijklmnopqrstuvwxyz'\n", encoding="utf-8")
    (repository / "node_modules").mkdir()
    (repository / "node_modules" / "ignored.js").write_text("x", encoding="utf-8")
    inspection = inspect_code_repository(ProjectPaths(tmp_path / "training"), repository)
    assert [path.name for path in inspection.accepted] == ["app.py"]
    assert inspection.quarantined[0].findings == ("huggingface_token",)
    assert inspection.languages == {"py": 1}


def test_code_import_is_namespaced_and_refuses_training_project(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "main.swift").write_text("print(\"hello\")\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "training")
    imported = import_code_corpus(paths, repository)
    assert imported.imported[0].id.startswith("code-")
    assert (paths.root / "corpora" / "code" / "corpus-manifest.json").is_file()
    with pytest.raises(ValueError, match="training project"):
        inspect_code_repository(paths, paths.root)


def test_code_inspection_honors_user_excluded_library(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    (repository / "writings").mkdir(parents=True)
    (repository / "writings" / "example.py").write_text("print('do not import')\n", encoding="utf-8")
    (repository / "app.py").write_text("print('import me')\n", encoding="utf-8")
    inspection = inspect_code_repository(ProjectPaths(tmp_path / "training"), repository, frozenset({"writings"}))
    assert [path.name for path in inspection.accepted] == ["app.py"]


def test_workspace_inspection_is_batched_and_does_not_copy_code(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    for name in ("alpha", "beta", "writings"):
        (workspace / name).mkdir(parents=True)
    (workspace / "alpha" / "app.py").write_text("print('a')\n", encoding="utf-8")
    (workspace / "beta" / "app.swift").write_text("print(\"b\")\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "training")
    result = inspect_code_workspace(paths, workspace, frozenset({"writings"}), limit=1)
    assert result.total_projects == 2
    assert len(result.projects) == 1
    assert result.next_offset == 1
    assert not (paths.root / "corpora" / "code").exists()


def test_task_manifest_stores_only_metadata_and_hashes(tmp_path: Path) -> None:
    paths = ProjectPaths(tmp_path / "training")
    project = paths.root.parent / "sample-app"
    (project / "Sources").mkdir(parents=True)
    (project / "Tests").mkdir()
    (project / "Sources" / "Target.swift").write_text("let privateSource = 42\n", encoding="utf-8")
    (project / "Tests" / "TargetTests.swift").write_text("func testTarget() {}\n", encoding="utf-8")
    task = CodeMaintenanceTask("SAMPLE-01", "Sample", "sample-app", "Sources/Target.swift", "Tests/TargetTests.swift", "swiftpm", "TargetTests")
    manifest = build_code_task_manifest(paths, "sample", (task,))
    assert validate_code_task_manifest(manifest) == {"tasks": 1, "projects": 1}
    contents = manifest.read_text(encoding="utf-8")
    assert "privateSource" not in contents
    assert "func testTarget" not in contents


def test_temporary_task_workspace_never_mutates_the_source_project(tmp_path: Path) -> None:
    paths = ProjectPaths(tmp_path / "training")
    project = paths.root.parent / "sample-app"
    (project / "Sources").mkdir(parents=True)
    (project / "Tests").mkdir()
    source = project / "Sources" / "Target.swift"
    source.write_text("let answer = 42\n", encoding="utf-8")
    (project / "Tests" / "TargetTests.swift").write_text("func testTarget() {}\n", encoding="utf-8")
    task = CodeMaintenanceTask("SAMPLE-01", "Sample", "sample-app", "Sources/Target.swift", "Tests/TargetTests.swift", "swiftpm", "TargetTests")
    with temporary_task_workspace(paths, task, "let answer = 42", "let answer = 0") as workspace:
        assert workspace.source.read_text(encoding="utf-8") == "let answer = 0\n"
        assert workspace.test.is_file()
        assert workspace.project_root != project
    assert source.read_text(encoding="utf-8") == "let answer = 42\n"


def test_code_dataset_validation_rejects_held_out_project(tmp_path: Path) -> None:
    output = tmp_path / "dataset"
    output.mkdir()
    (output / "dataset-manifest.json").write_text('{"space":"code","held_out_projects":["evaluation-app"],"examples":[{"project":"evaluation-app","split":"train"}]}', encoding="utf-8")
    for split in ("train", "validation", "test"):
        (output / f"{split}.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Held-out"):
        from trainer.code import validate_code_dataset
        validate_code_dataset(output)


def test_code_dataset_requires_the_requested_number_of_test_contracts(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "app.py").write_text("print('ok')\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "training")
    import_code_corpus(paths, repository)
    with pytest.raises(ValueError, match="test-contract"):
        build_code_dataset(paths, "v-next", max_files_per_project=1, minimum_test_contract_examples=1)


def test_test_contract_discovery_matches_swift_typescript_and_python_conventions() -> None:
    def document(path: str, language: str) -> CodeDocument:
        return CodeDocument(path, "hash", path, "documents/hash", "now", language, 1)
    swift = document("/work/app/Sources/Palette.swift", "swift")
    swift_test = document("/work/app/Tests/PaletteTests.swift", "swift")
    typescript = document("/work/web/lib/route.ts", "ts")
    typescript_test = document("/work/web/lib/route.test.ts", "ts")
    python = document("/work/tools/slug.py", "py")
    python_test = document("/work/tools/test_slug.py", "py")
    assert _find_test_document(swift, [swift, swift_test]) == swift_test
    assert _find_test_document(typescript, [typescript, typescript_test]) == typescript_test
    assert _find_test_document(python, [python, python_test]) == python_test


def test_training_document_filter_rejects_prior_dependency_build_paths() -> None:
    external = CodeDocument("external", "hash", "/work/app/.build/checkouts/Package/Sources/Thing.swift", "documents/hash", "now", "swift", 1)
    owned = CodeDocument("owned", "hash", "/work/app/Sources/Thing.swift", "documents/hash", "now", "swift", 1)
    assert not _is_training_document(external)
    assert _is_training_document(owned)


def test_repair_curriculum_uses_a_broken_source_and_complete_fixed_answer() -> None:
    messages = _episode(0)["messages"]
    assert "> 10" in messages[1]["content"]
    assert ">= 10" in messages[2]["content"]
    assert "test_discount_at_threshold" in messages[1]["content"]


def test_history_repair_excludes_every_approved_evaluation_project() -> None:
    assert {"camera-app", "nauticgrid", "mishkat-quran-app", "lumen-app"}.issubset(EVALUATION_PROJECTS)
