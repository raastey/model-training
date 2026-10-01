import json

import pytest

from trainer.benchmarks import (
    load_relevance_cases,
    repeated_ngram_ratio,
    runtime_output_issue,
    self_retrieval_cases,
)
from trainer.corpus import CorpusDocument


def test_repetition_gate_identifies_repeated_phrase() -> None:
    repetitive = "the position has the most money behind it " * 8
    natural = "Evidence supports public claims, while clear sources let readers test those claims independently."
    assert repeated_ngram_ratio(repetitive) > 0.4
    assert repeated_ngram_ratio(natural) == 0.0
    assert runtime_output_issue(repetitive) == "REPETITION"
    assert runtime_output_issue(natural) is None
    assert runtime_output_issue("") == "EMPTY"


def test_self_retrieval_cases_are_title_grounded() -> None:
    document = CorpusDocument(
        id="writer-1", content_hash="hash", source_path="evidence.md", storage_path="evidence.md",
        imported_at="2026-08-11T00:00:00Z", title="Evidence in debate", word_count=10, quality="good",
    )
    cases = self_retrieval_cases([document])
    assert cases[0].document_id == "writer-1"
    assert "Evidence in debate" in cases[0].query


def test_self_retrieval_cases_skip_excluded_documents() -> None:
    excluded = CorpusDocument(
        id="writer-excluded", content_hash="hash", source_path="ignore.md", storage_path="ignore.md",
        imported_at="2026-08-11T00:00:00Z", title="Ignored source", word_count=10, quality="exclude",
    )
    assert self_retrieval_cases([excluded]) == []


def test_load_relevance_cases_requires_human_labels(tmp_path) -> None:
    review = tmp_path / "review.json"
    review.write_text(json.dumps([{"id": "R1", "query": "Why evidence?", "expected_document_ids": ["writer-1"]}]), encoding="utf-8")
    assert load_relevance_cases(review)[0].expected_document_ids == frozenset({"writer-1"})
    review.write_text(json.dumps([{"id": "R1", "query": "Why evidence?", "expected_document_ids": []}]), encoding="utf-8")
    with pytest.raises(ValueError, match="at least one"):
        load_relevance_cases(review)
