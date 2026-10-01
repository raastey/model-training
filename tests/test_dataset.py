import json
from pathlib import Path

from trainer.config import ProjectPaths
from trainer.corpus import import_writer_corpus, set_quality
from trainer.dataset import build_writer_dataset, validate_writer_dataset


def test_build_writer_dataset_from_reviewed_documents(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    for number in range(12):
        (source / f"essay-{number}.md").write_text(
            f"# Essay {number}\n\nA complete analytical paragraph number {number}.\n", encoding="utf-8"
        )
    paths = ProjectPaths(tmp_path / "project")
    imported = import_writer_corpus(paths, source).imported
    for document in imported:
        set_quality(paths, document.id, "good")

    result = build_writer_dataset(paths, "fixture")

    assert sum(result.examples_by_split.values()) == 12
    assert validate_writer_dataset(result.output_dir) == result.examples_by_split
    assert (result.output_dir / "dataset-manifest.json").is_file()


def test_chunked_examples_keep_one_document_in_one_split(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "essay.md").write_text(
        "# Essay\n\n" + "First sentence. " * 100 + "\n\n" + "Second sentence. " * 100,
        encoding="utf-8",
    )
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    set_quality(paths, document.id, "good")

    result = build_writer_dataset(paths, "chunked", chunk_characters=500)

    assert sum(result.examples_by_split.values()) > 1
    assert validate_writer_dataset(result.output_dir) == result.examples_by_split


def test_context_tasks_are_labeled_by_provenance(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "essay.md").write_text(
        "# Essay\n\n" + "First sentence. " * 80 + "\n\n" + "Second sentence. " * 80,
        encoding="utf-8",
    )
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    set_quality(paths, document.id, "good")

    result = build_writer_dataset(paths, "context", chunk_characters=500, include_context_tasks=True)
    manifest = (result.output_dir / "dataset-manifest.json").read_text(encoding="utf-8")

    assert '"W3"' in manifest
    assert '"synthetic"' in manifest


def test_balanced_context_profile_omits_w9_and_reduces_derived_pairs(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "long.md").write_text(
        "# Long\n\n" + "\n\n".join(f"Paragraph {number}. " + "x" * 100 for number in range(12)),
        encoding="utf-8",
    )
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    set_quality(paths, document.id, "good")
    build_writer_dataset(paths, "balanced", chunk_characters=120, include_context_tasks=True, context_task_profile="balanced")
    manifest = json.loads((paths.root / "datasets" / "writer" / "balanced" / "dataset-manifest.json").read_text(encoding="utf-8"))
    assert manifest["context_task_profile"] == "balanced"
    assert manifest["classes"].get("W9", 0) == 0
    assert manifest["classes"]["W3"] < manifest["classes"]["W1"]
    assert manifest["source_libraries"]["documents"] == {"writing": 1}
