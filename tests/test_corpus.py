from pathlib import Path

from trainer.config import ProjectPaths
from trainer.corpus import import_writer_corpus, list_documents, set_quality


def test_import_normalizes_and_deduplicates(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "essay.md").write_text("# A Small Essay\r\n\r\nHello world.\r\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "project")
    first = import_writer_corpus(paths, source)
    second = import_writer_corpus(paths, source)
    assert len(first.imported) == 1
    assert first.imported[0].title == "A Small Essay"
    stored = paths.root / "corpora/writer" / first.imported[0].storage_path
    assert stored.read_text() == "# A Small Essay\n\nHello world.\n"
    assert len(second.duplicates) == 1
    assert len(list_documents(paths)) == 1


def test_import_quarantines_secret_without_copying_source_text(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "unsafe.txt").write_text("HF_TOKEN=hf_abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "project")
    result = import_writer_corpus(paths, source)
    assert len(result.quarantined) == 1
    assert result.quarantined[0].findings == ("huggingface_token",)
    assert not (paths.root / "corpora").exists()


def test_quality_label_requires_explicit_human_decision(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "essay.txt").write_text("A carefully written sentence.\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    assert document.quality == "unreviewed"
    assert set_quality(paths, document.id, "gold").quality == "gold"
