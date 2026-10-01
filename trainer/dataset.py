"""Deterministic Writer dataset construction and validation."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from trainer.config import ProjectPaths
from trainer.corpus import CorpusDocument, list_documents, scan_for_secrets, writer_corpus_dir

DATASET_SCHEMA_VERSION = 1
BUILDER_VERSION = "0.2.0"
SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class DatasetBuildResult:
    output_dir: Path
    examples_by_split: dict[str, int]
    skipped_document_ids: tuple[str, ...]


def writer_dataset_dir(paths: ProjectPaths, name: str = "v1") -> Path:
    return paths.root / "datasets" / "writer" / name


def split_for_document(document: CorpusDocument) -> str:
    """Allocate whole documents deterministically: 85% / 7.5% / 7.5%."""
    bucket = int(document.content_hash[:8], 16) % 1000
    if bucket < 850:
        return "train"
    if bucket < 925:
        return "validation"
    return "test"


def source_library(document: CorpusDocument) -> str:
    """Name the immediate source folder for corpus-composition auditing."""
    return Path(document.source_path).parent.name or "unknown"


def _prompt(document: CorpusDocument, section_number: int = 1) -> str:
    return (
        "Write a rigorously argued, source-conscious analytical article in the user's established "
        f"voice on this subject: {document.title}. Write section {section_number}, preserving clarity, "
        "specificity, and a coherent thesis."
    )


def _example(document: CorpusDocument, text: str, section_number: int = 1) -> dict[str, object]:
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are SIXTWELVE Writer. Follow the user's editorial voice and preserve factual discipline.",
            },
            {"role": "user", "content": _prompt(document, section_number)},
            {"role": "assistant", "content": text},
        ]
    }


def _context_example(user_content: str, assistant_content: str) -> dict[str, object]:
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are SIXTWELVE Writer. Select, preserve, and update only the context needed for the task.",
            },
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def chunk_writer_text(text: str, max_characters: int) -> list[str]:
    """Split prose at paragraph/sentence boundaries before MLX sees it."""
    if max_characters <= 0 or len(text) <= max_characters:
        return [text]
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        parts = [paragraph]
        if len(paragraph) > max_characters:
            parts = re.split(r"(?<=[.!?])\s+", paragraph)
        for part in parts:
            if current and len(current) + len(part) + 2 > max_characters:
                chunks.append(current + "\n")
                current = ""
            if len(part) > max_characters:
                for start in range(0, len(part), max_characters):
                    piece = part[start:start + max_characters]
                    if current:
                        chunks.append(current + "\n")
                        current = ""
                    chunks.append(piece + "\n")
            else:
                current = f"{current}\n\n{part}".strip()
    if current:
        chunks.append(current + "\n")
    return chunks


def build_writer_dataset(
    paths: ProjectPaths, name: str = "v1", chunk_characters: int = 0, include_context_tasks: bool = False,
    context_task_profile: str = "full",
) -> DatasetBuildResult:
    """Build W1 examples from explicitly approved prose; W4 needs authored revision pairs."""
    output_dir = writer_dataset_dir(paths, name)
    if output_dir.exists():
        raise ValueError(f"Dataset output already exists: {output_dir}")
    if context_task_profile not in {"full", "balanced"}:
        raise ValueError("Context task profile must be 'full' or 'balanced'.")
    documents = [document for document in list_documents(paths) if document.quality in {"gold", "good"}]
    if not documents:
        raise ValueError("No Writer documents are labeled gold or good.")
    records: dict[str, list[dict[str, object]]] = {split: [] for split in SPLIT_NAMES}
    metadata: list[dict[str, object]] = []
    skipped: list[str] = []
    corpus_dir = writer_corpus_dir(paths)
    class_counts: Counter[str] = Counter()
    library_document_counts: Counter[str] = Counter(source_library(document) for document in documents)
    library_example_counts: Counter[str] = Counter()

    def add_example(
        split: str, example_id: str, task_class: str, document: CorpusDocument,
        record: dict[str, object], provenance: str, section_number: int | None = None,
    ) -> None:
        records[split].append(record)
        item: dict[str, object] = {
            "id": example_id,
            "class": task_class,
            "provenance": provenance,
            "source_ids": [document.id],
            "source_hashes": [document.content_hash],
            "quality": document.quality,
            "reviewed": True,
            "split": split,
            "generator_version": BUILDER_VERSION,
        }
        if section_number is not None:
            item["section_number"] = section_number
        metadata.append(item)
        class_counts[task_class] += 1
        library_example_counts[source_library(document)] += 1

    for document in documents:
        text = (corpus_dir / document.storage_path).read_text(encoding="utf-8")
        if not text.strip() or scan_for_secrets(text):
            skipped.append(document.id)
            continue
        split = split_for_document(document)
        chunks = chunk_writer_text(text, chunk_characters)
        for section_number, chunk in enumerate(chunks, start=1):
            example_id = f"W1-{document.id}-{section_number:03d}"
            add_example(split, example_id, "W1", document, _example(document, chunk, section_number), "authentic", section_number)
        if include_context_tasks and len(chunks) > 1:
            for section_number in range(2, len(chunks) + 1):
                previous = chunks[section_number - 2]
                current = chunks[section_number - 1]
                include_pair = context_task_profile == "full" or section_number % 4 == 0
                if include_pair:
                    add_example(
                        split, f"W3-{document.id}-{section_number:03d}", "W3", document,
                        _context_example(
                            f"Article: {document.title}\n\nPrevious section:\n{previous}\n\nWrite the next section by advancing the argument with the next necessary claim.",
                            current,
                        ), "derived", section_number,
                    )
                if context_task_profile == "full":
                    add_example(
                        split, f"W9-{document.id}-{section_number:03d}", "W9", document,
                        _context_example(
                            f"Article: {document.title}\n\nAlready completed:\n{previous[:1200]}\n\nNext-section objective: advance the argument with a new claim; do not repeat the completed material.",
                            current,
                        ), "derived", section_number,
                    )
            state = json.dumps(
                {
                    "objective": document.title,
                    "completed": [f"sections 1-{len(chunks) - 1}"],
                    "unresolved": ["draft the next section"],
                    "claims_already_made": [chunks[0][:300]],
                    "next_action": "continue with the next section without repetition",
                }, ensure_ascii=False,
            )
            add_example(
                split, f"W5-{document.id}", "W5", document,
                _context_example(
                    f"Compress this article state into the required working-state JSON.\n\nTitle: {document.title}\n\nCompleted material:\n{chunks[0][:1200]}\n\nCurrent material:\n{chunks[1][:1200]}",
                    state,
                ), "derived",
            )
            add_example(
                split, f"W7-{document.id}", "W7", document,
                _context_example(
                    f"Task: continue an article titled '{document.title}'.\n\nOlder instruction: write a broad introduction.\nLater explicit instruction: begin with the central accountability claim and avoid a broad overview.\n\nReturn the active instruction as JSON.",
                    json.dumps({"active_instruction": "begin with the central accountability claim and avoid a broad overview"}),
                ), "synthetic",
            )
    output_dir.mkdir(parents=True)
    for split, items in records.items():
        (output_dir / f"{split}.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8"
        )
    manifest = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "builder_version": BUILDER_VERSION,
        "space": "writer",
        "dataset_name": name,
        "chunk_characters": chunk_characters,
        "context_tasks": include_context_tasks,
        "context_task_profile": context_task_profile if include_context_tasks else None,
        "classes": dict(sorted(class_counts.items())) | {"W4": 0},
        "source_libraries": {
            "documents": dict(sorted(library_document_counts.items())),
            "examples": dict(sorted(library_example_counts.items())),
        },
        "examples": metadata,
        "skipped_document_ids": skipped,
        "split_counts": {split: len(items) for split, items in records.items()},
    }
    _write_json(output_dir / "dataset-manifest.json", manifest)
    validate_writer_dataset(output_dir)
    return DatasetBuildResult(output_dir, manifest["split_counts"], tuple(skipped))


def validate_writer_dataset(output_dir: Path) -> dict[str, int]:
    """Check chat records, secret absence, manifest integrity, and split isolation."""
    manifest_path = output_dir / "dataset-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Dataset manifest is missing.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("space") != "writer":
        raise ValueError("Dataset is not namespaced as writer.")
    metadata = manifest.get("examples", [])
    source_splits: dict[str, str] = {}
    split_counts: Counter[str] = Counter()
    for item in metadata:
        if item["class"] not in {"W1", "W3", "W4", "W5", "W7", "W9"} or item["split"] not in SPLIT_NAMES:
            raise ValueError(f"Invalid metadata entry: {item.get('id', '<unknown>')}")
        for source_id in item["source_ids"]:
            previous_split = source_splits.setdefault(source_id, item["split"])
            if previous_split != item["split"]:
                raise ValueError(f"Source crosses dataset splits: {source_id}")
        split_counts[item["split"]] += 1
    for split in SPLIT_NAMES:
        lines = (output_dir / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        if len(lines) != split_counts[split]:
            raise ValueError(f"{split} JSONL count does not match manifest.")
        for line in lines:
            record = json.loads(line)
            messages = record.get("messages")
            if not isinstance(messages, list) or [message.get("role") for message in messages] != ["system", "user", "assistant"]:
                raise ValueError(f"Invalid chat roles in {split}.")
            if any(not isinstance(message.get("content"), str) or not message["content"].strip() for message in messages):
                raise ValueError(f"Empty chat content in {split}.")
            if any(scan_for_secrets(message["content"]) for message in messages):
                raise ValueError(f"Possible secret found in {split} dataset output.")
    return {split: split_counts[split] for split in SPLIT_NAMES}
