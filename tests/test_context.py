from pathlib import Path

from trainer.config import ProjectPaths
from trainer.context import build_writer_index, retrieve_writer_context
from trainer.corpus import import_writer_corpus, set_quality


def test_writer_context_retrieves_only_writer_chunks(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "evidence.md").write_text("# Evidence\n\nEvidence matters in public debate because it makes claims accountable.\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    set_quality(paths, document.id, "good")

    assert build_writer_index(paths) == 1
    results = retrieve_writer_context(paths, "Why does evidence matter in debate?")
    assert results[0].chunk.document_id == document.id
    assert "evidence" in results[0].matched_terms


def test_writer_context_abstains_when_no_two_terms_overlap(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "harbor.md").write_text("# Harbor\n\nShips arrive at the harbor.\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    set_quality(paths, document.id, "good")
    build_writer_index(paths)

    assert retrieve_writer_context(paths, "astronomy telescope galaxy") == []


def test_writer_context_abstains_for_a_generic_placeholder_request(tmp_path: Path) -> None:
    source = tmp_path / "writing"
    source.mkdir()
    (source / "mountain.md").write_text("# Mountain\n\nA mountain expedition has risks.\n", encoding="utf-8")
    paths = ProjectPaths(tmp_path / "project")
    document = import_writer_corpus(paths, source).imported[0]
    set_quality(paths, document.id, "good")
    build_writer_index(paths)

    assert retrieve_writer_context(paths, "Write one concise paragraph about X.") == []
