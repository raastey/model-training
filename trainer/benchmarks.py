"""Inspectable relevance and repetition gates for Writer candidates."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from trainer.context import RetrievedChunk
from trainer.corpus import CorpusDocument


def relevance_recall_at_k(results: list[RetrievedChunk], expected_document_ids: set[str], k: int = 5) -> bool:
    """A task passes when at least one user-labeled relevant document is retrieved."""
    return any(item.chunk.document_id in expected_document_ids for item in results[:k])


def repeated_ngram_ratio(text: str, n: int = 5) -> float:
    """Fraction of n-grams that repeat; high values flag degenerate generation."""
    tokens = text.lower().split()
    ngrams = [tuple(tokens[index:index + n]) for index in range(max(0, len(tokens) - n + 1))]
    if not ngrams:
        return 0.0
    counts = Counter(ngrams)
    return sum(count - 1 for count in counts.values() if count > 1) / len(ngrams)


def runtime_output_issue(text: str, repetition_threshold: float = 0.10) -> str | None:
    """Return a promotion-blocking reason for empty or repetitive generated output."""
    if not text.strip():
        return "EMPTY"
    if repeated_ngram_ratio(text) > repetition_threshold:
        return "REPETITION"
    return None


@dataclass(frozen=True)
class SelfRetrievalCase:
    """A transparent smoke case: a document should be retrievable from its own title."""

    document_id: str
    query: str


@dataclass(frozen=True)
class RelevanceCase:
    """A human-labeled conceptual retrieval case."""

    id: str
    query: str
    expected_document_ids: frozenset[str]


def self_retrieval_cases(documents: list[CorpusDocument], limit: int = 10) -> list[SelfRetrievalCase]:
    """Make deterministic title-to-source checks, distinct from human relevance evaluation."""
    cases: list[SelfRetrievalCase] = []
    for document in sorted(documents, key=lambda item: item.id):
        if document.quality not in {"gold", "good", "reference_only"}:
            continue
        title = " ".join(document.title.split())
        if len(title) < 8:
            continue
        cases.append(SelfRetrievalCase(document.id, f"Find the writing about: {title}"))
        if len(cases) == limit:
            break
    return cases


def load_relevance_cases(path: Path) -> list[RelevanceCase]:
    """Load reviewed conceptual relevance cases without silently accepting empty labels."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Relevance review must be a JSON list.")
    cases: list[RelevanceCase] = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("query"), str):
            raise ValueError("Each relevance case needs string 'id' and 'query' fields.")
        expected = item.get("expected_document_ids")
        if not isinstance(expected, list) or not expected or not all(isinstance(value, str) for value in expected):
            raise ValueError(f"Relevance case {item['id']} needs at least one expected_document_id.")
        cases.append(RelevanceCase(item["id"], item["query"], frozenset(expected)))
    if not cases:
        raise ValueError("Relevance review has no cases.")
    return cases
