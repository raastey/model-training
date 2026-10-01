"""Local, review-first Writer corpus ingestion."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from trainer.config import ProjectPaths

SUPPORTED_WRITER_SUFFIXES = {".md", ".markdown", ".txt"}
EXCLUDED_DIRECTORY_NAMES = {".git", ".hg", ".svn", "node_modules", "build", "dist", ".venv"}
QUALITY_LABELS = {"unreviewed", "gold", "good", "reference_only", "exclude"}
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("huggingface_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("connection_string", re.compile(r"\b(?:postgres|mysql|mongodb(?:\+srv)?)://[^\s]+", re.I)),
)


@dataclass(frozen=True)
class CorpusDocument:
    id: str
    content_hash: str
    source_path: str
    storage_path: str
    imported_at: str
    title: str
    word_count: int
    quality: str = "unreviewed"


@dataclass(frozen=True)
class QuarantinedSource:
    source_path: str
    findings: tuple[str, ...]


@dataclass(frozen=True)
class ImportResult:
    imported: tuple[CorpusDocument, ...]
    duplicates: tuple[str, ...]
    quarantined: tuple[QuarantinedSource, ...]
    ignored: tuple[str, ...]


def scan_for_secrets(text: str) -> tuple[str, ...]:
    """Return finding categories only—never matched secret values or source text."""
    return tuple(name for name, pattern in _SECRET_PATTERNS if pattern.search(text))


def writer_corpus_dir(paths: ProjectPaths) -> Path:
    return paths.root / "corpora" / "writer"


def _manifest_path(paths: ProjectPaths) -> Path:
    return writer_corpus_dir(paths) / "corpus-manifest.json"


def list_documents(paths: ProjectPaths) -> list[CorpusDocument]:
    manifest_path = _manifest_path(paths)
    if not manifest_path.is_file():
        return []
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [CorpusDocument(**record) for record in raw["documents"]]


def _write_manifest(paths: ProjectPaths, documents: list[CorpusDocument]) -> None:
    corpus_dir = writer_corpus_dir(paths)
    corpus_dir.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "documents": [asdict(item) for item in documents]}
    manifest_path = _manifest_path(paths)
    temporary_path = manifest_path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_path.replace(manifest_path)


def _candidate_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise ValueError(f"Source does not exist: {source}")
    return [
        candidate for candidate in source.rglob("*")
        if candidate.is_file() and not candidate.is_symlink()
        and not any(part in EXCLUDED_DIRECTORY_NAMES for part in candidate.relative_to(source).parts)
    ]


def _title(source: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:200] or source.stem
    return source.stem[:200]


def import_writer_corpus(paths: ProjectPaths, source: Path) -> ImportResult:
    """Import Markdown/text files, refusing any file with a likely secret."""
    documents = list_documents(paths)
    hashes = {document.content_hash for document in documents}
    imported: list[CorpusDocument] = []
    duplicates: list[str] = []
    quarantined: list[QuarantinedSource] = []
    ignored: list[str] = []
    for candidate in sorted(_candidate_files(source)):
        if candidate.suffix.lower() not in SUPPORTED_WRITER_SUFFIXES:
            ignored.append(str(candidate))
            continue
        try:
            text = candidate.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            ignored.append(str(candidate))
            continue
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
        if findings := scan_for_secrets(normalized):
            quarantined.append(QuarantinedSource(str(candidate.resolve()), findings))
            continue
        content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if content_hash in hashes:
            duplicates.append(str(candidate.resolve()))
            continue
        storage_relative = Path("documents") / f"{content_hash}.txt"
        storage_path = writer_corpus_dir(paths) / storage_relative
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(normalized, encoding="utf-8")
        document = CorpusDocument(
            id=f"writer-{content_hash[:16]}", content_hash=content_hash,
            source_path=str(candidate.resolve()), storage_path=str(storage_relative),
            imported_at=datetime.now(UTC).isoformat(), title=_title(candidate, normalized),
            word_count=len(normalized.split()),
        )
        documents.append(document)
        imported.append(document)
        hashes.add(content_hash)
    if imported or (not _manifest_path(paths).exists() and documents):
        _write_manifest(paths, documents)
    return ImportResult(tuple(imported), tuple(duplicates), tuple(quarantined), tuple(ignored))


def set_quality(paths: ProjectPaths, document_id: str, quality: str) -> CorpusDocument:
    if quality not in QUALITY_LABELS:
        raise ValueError(f"Unknown quality label: {quality}")
    documents = list_documents(paths)
    for index, document in enumerate(documents):
        if document.id == document_id:
            updated = CorpusDocument(**(asdict(document) | {"quality": quality}))
            documents[index] = updated
            _write_manifest(paths, documents)
            return updated
    raise ValueError(f"Unknown Writer document ID: {document_id}")
