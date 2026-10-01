"""Strictly isolated local Code-corpus inspection and import."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from trainer.config import ProjectPaths
from trainer.corpus import QuarantinedSource, scan_for_secrets

CODE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html", ".java", ".js", ".json",
    ".jsx", ".kt", ".kts", ".m", ".mm", ".php", ".py", ".rb", ".rs", ".scala", ".sh", ".sql",
    ".swift", ".toml", ".ts", ".tsx", ".yaml", ".yml",
}
CODE_EXCLUDED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", ".build", "build", "checkouts", "coverage", "deriveddata", "dist", "node_modules", "pods",
    "target", "vendor", ".next", ".turbo", "__pycache__",
}
CODE_EXCLUDED_FILENAMES = {".env", ".env.local", ".env.production", "package-lock.json", "podfile.lock"}
CODE_TRAINING_LANGUAGES = {"c", "cc", "cpp", "cs", "go", "h", "hpp", "java", "js", "jsx", "kt", "kts", "py", "rs", "swift", "ts", "tsx"}


@dataclass(frozen=True)
class CodeDocument:
    id: str
    content_hash: str
    source_path: str
    storage_path: str
    imported_at: str
    language: str
    line_count: int
    quality: str = "unreviewed"


@dataclass(frozen=True)
class CodeInspection:
    accepted: tuple[Path, ...]
    ignored: tuple[Path, ...]
    quarantined: tuple[QuarantinedSource, ...]
    languages: dict[str, int]


@dataclass(frozen=True)
class CodeImportResult:
    imported: tuple[CodeDocument, ...]
    duplicates: tuple[str, ...]
    quarantined: tuple[QuarantinedSource, ...]
    ignored: tuple[str, ...]


@dataclass(frozen=True)
class WorkspaceInspection:
    projects: tuple[dict[str, object], ...]
    total_projects: int
    next_offset: int | None


def code_corpus_dir(paths: ProjectPaths) -> Path:
    return paths.root / "corpora" / "code"


def _manifest_path(paths: ProjectPaths) -> Path:
    return code_corpus_dir(paths) / "corpus-manifest.json"


def _language(path: Path) -> str:
    return path.suffix.lower().lstrip(".") or "unknown"


def _candidate_files(source: Path, excluded_directories: frozenset[str]) -> list[Path]:
    if not source.is_dir():
        raise ValueError("Code import source must be a repository directory.")
    excluded = CODE_EXCLUDED_DIRECTORIES | excluded_directories
    candidates: list[Path] = []
    for parent, directories, filenames in os.walk(source):
        directories[:] = sorted(name for name in directories if name.lower() not in excluded)
        for filename in sorted(filenames):
            path = Path(parent) / filename
            if not path.is_symlink() and path.name.lower() not in CODE_EXCLUDED_FILENAMES:
                candidates.append(path)
    return candidates


def inspect_code_repository(
    paths: ProjectPaths, source: Path, excluded_directories: frozenset[str] = frozenset()
) -> CodeInspection:
    """Inspect a repository without copying it; never accept the training project itself."""
    resolved = source.resolve()
    if resolved == paths.root.resolve():
        raise ValueError("Refusing to import the training project as a Code corpus.")
    accepted: list[Path] = []
    ignored: list[Path] = []
    quarantined: list[QuarantinedSource] = []
    languages: Counter[str] = Counter()
    normalized_exclusions = frozenset(name.lower() for name in excluded_directories)
    for candidate in sorted(_candidate_files(resolved, normalized_exclusions)):
        if candidate.suffix.lower() not in CODE_SUFFIXES:
            ignored.append(candidate)
            continue
        try:
            text = candidate.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            ignored.append(candidate)
            continue
        if findings := scan_for_secrets(text):
            quarantined.append(QuarantinedSource(str(candidate), findings))
            continue
        accepted.append(candidate)
        languages[_language(candidate)] += 1
    return CodeInspection(tuple(accepted), tuple(ignored), tuple(quarantined), dict(sorted(languages.items())))


def inspect_code_workspace(
    paths: ProjectPaths, workspace: Path, excluded_directories: frozenset[str] = frozenset(),
    offset: int = 0, limit: int = 10,
) -> WorkspaceInspection:
    """Inspect a bounded batch of top-level repositories without copying any code."""
    resolved = workspace.resolve()
    if not resolved.is_dir():
        raise ValueError("Code workspace must be a directory.")
    exclusions = frozenset(name.lower() for name in excluded_directories)
    projects = sorted(
        path for path in resolved.iterdir()
        if path.is_dir() and not path.is_symlink() and not path.name.startswith(".")
        and path.name.lower() not in exclusions
    )
    if offset < 0 or limit < 1:
        raise ValueError("Workspace offset must be non-negative and limit must be positive.")
    batch = projects[offset:offset + limit]
    rows: list[dict[str, object]] = []
    for project in batch:
        if project.resolve() == paths.root.resolve():
            rows.append({
                "project": project.name,
                "has_git": (project / ".git").exists(),
                "accepted": 0,
                "quarantined": 0,
                "ignored": 0,
                "languages": {},
                "skipped_reason": "training project isolation",
            })
            continue
        inspection = inspect_code_repository(paths, project, exclusions)
        rows.append({
            "project": project.name,
            "has_git": (project / ".git").exists(),
            "accepted": len(inspection.accepted),
            "quarantined": len(inspection.quarantined),
            "ignored": len(inspection.ignored),
            "languages": inspection.languages,
        })
    next_offset = offset + limit if offset + limit < len(projects) else None
    return WorkspaceInspection(tuple(rows), len(projects), next_offset)


def _list_documents(paths: ProjectPaths) -> list[CodeDocument]:
    manifest_path = _manifest_path(paths)
    if not manifest_path.is_file():
        return []
    return [CodeDocument(**record) for record in json.loads(manifest_path.read_text(encoding="utf-8"))["documents"]]


def import_code_corpus(
    paths: ProjectPaths, source: Path, excluded_directories: frozenset[str] = frozenset()
) -> CodeImportResult:
    """Copy only reviewed-safe source/config files into the isolated Code namespace."""
    inspection = inspect_code_repository(paths, source, excluded_directories)
    documents = _list_documents(paths)
    hashes = {document.content_hash for document in documents}
    imported: list[CodeDocument] = []
    duplicates: list[str] = []
    for candidate in inspection.accepted:
        normalized = candidate.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
        content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if content_hash in hashes:
            duplicates.append(str(candidate))
            continue
        storage_relative = Path("documents") / f"{content_hash}{candidate.suffix.lower()}"
        storage_path = code_corpus_dir(paths) / storage_relative
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(normalized, encoding="utf-8")
        document = CodeDocument(
            id=f"code-{content_hash[:16]}", content_hash=content_hash, source_path=str(candidate),
            storage_path=str(storage_relative), imported_at=datetime.now(UTC).isoformat(),
            language=_language(candidate), line_count=len(normalized.splitlines()),
        )
        documents.append(document)
        imported.append(document)
        hashes.add(content_hash)
    if imported or not _manifest_path(paths).exists():
        code_corpus_dir(paths).mkdir(parents=True, exist_ok=True)
        _manifest_path(paths).write_text(
            json.dumps({"schema_version": 1, "space": "code", "documents": [asdict(item) for item in documents]}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return CodeImportResult(tuple(imported), tuple(duplicates), inspection.quarantined, tuple(str(item) for item in inspection.ignored))


def _project_name(paths: ProjectPaths, document: CodeDocument) -> str:
    try:
        return Path(document.source_path).relative_to(paths.root.parent).parts[0]
    except ValueError:
        return Path(document.source_path).parent.name or "unknown"


def _is_training_document(document: CodeDocument) -> bool:
    """Exclude generated/dependency paths even if an older corpus imported them."""
    return not any(part.lower() in CODE_EXCLUDED_DIRECTORIES for part in Path(document.source_path).parts)


def code_dataset_dir(paths: ProjectPaths, name: str = "v1") -> Path:
    return paths.root / "datasets" / "code" / name


def _split_for_project(project: str) -> str:
    bucket = int(hashlib.sha256(project.encode()).hexdigest()[:8], 16) % 1000
    return "train" if bucket < 850 else "validation" if bucket < 925 else "test"


def _test_stem(path: Path) -> str | None:
    """Return the likely production stem for common Swift/TS/Python test names."""
    stem = path.stem
    if stem.endswith("Tests"):
        return stem.removesuffix("Tests").lower()
    if stem.endswith("Test"):
        return stem.removesuffix("Test").lower()
    if stem.endswith(".test") or stem.endswith(".spec"):
        return stem.rsplit(".", 1)[0].lower()
    if stem.startswith("test_"):
        return stem.removeprefix("test_").lower()
    return None


def _is_test_document(document: CodeDocument) -> bool:
    path = Path(document.source_path)
    return _test_stem(path) is not None or any(part.lower() in {"test", "tests", "__tests__"} for part in path.parts)


def _find_test_document(document: CodeDocument, project_documents: list[CodeDocument]) -> CodeDocument | None:
    """Find one same-language, same-project test contract without crossing projects."""
    source_path = Path(document.source_path)
    source_stem = source_path.stem.lower()
    candidates = [
        item for item in project_documents
        if item.language == document.language and _is_test_document(item)
        and _test_stem(Path(item.source_path)) == source_stem
    ]
    return sorted(candidates, key=lambda item: item.source_path)[0] if candidates else None


def build_code_dataset(
    paths: ProjectPaths, name: str = "v1", max_files_per_project: int = 80, max_characters: int = 6000,
    patch_oriented: bool = False, max_training_tokens: int = 1800, excluded_projects: frozenset[str] = frozenset(),
    minimum_test_contract_examples: int = 0,
) -> dict[str, int]:
    """Build a project-split Code dataset, optionally teaching constrained file replacement."""
    output = code_dataset_dir(paths, name)
    if output.exists():
        raise ValueError(f"Dataset output already exists: {output}")
    documents = [item for item in _list_documents(paths) if item.language in CODE_TRAINING_LANGUAGES and _is_training_document(item)]
    if not documents:
        raise ValueError("No primary-language Code documents are available.")
    grouped: dict[str, list[CodeDocument]] = {}
    for document in documents:
        grouped.setdefault(_project_name(paths, document), []).append(document)
    records: dict[str, list[dict[str, object]]] = {split: [] for split in ("train", "validation", "test")}
    metadata: list[dict[str, object]] = []
    skipped: list[str] = []
    language_counts: Counter[str] = Counter()
    project_counts: Counter[str] = Counter()
    corpus = code_corpus_dir(paths)
    if patch_oriented:
        from transformers import AutoTokenizer

        from trainer.models import code_model
        tokenizer = AutoTokenizer.from_pretrained(code_model(paths).path)
    held_out = frozenset(excluded_projects)
    for project, items in sorted(grouped.items()):
        if project in held_out:
            continue
        for document in sorted(items, key=lambda item: item.content_hash)[:max_files_per_project]:
            if _is_test_document(document):
                continue
            text = (corpus / document.storage_path).read_text(encoding="utf-8")
            if len(text) > max_characters:
                skipped.append(document.id)
                continue
            split = _split_for_project(project)
            filename = Path(document.source_path).name
            test_document = _find_test_document(document, items)
            test_text = ""
            if patch_oriented and test_document:
                test_text = (corpus / test_document.storage_path).read_text(encoding="utf-8")
            if patch_oriented and len(text) + len(test_text) > max_characters:
                skipped.append(document.id)
                continue
            if patch_oriented:
                contract = f"\n\nExisting test contract:\n{test_text}" if test_text else ""
                user_prompt = (
                    f"Return only the complete replacement contents of {filename}. Preserve public names and types. "
                    f"Keep the change narrow and maintainable. Use the supplied test contract when present.\n\n"
                    f"Existing {filename}:\n{text}{contract}"
                )
                example_kind = "patch-replacement-with-test" if test_text else "patch-replacement"
            else:
                user_prompt = f"Implement or complete a {document.language} source file consistent with project {project}. Return code only."
                example_kind = "completion"
            messages = [
                {"role": "system", "content": "You are SIXTWELVE Code. Return safe, maintainable code. Follow the requested output format exactly."},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": text},
            ]
            if patch_oriented:
                rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
                token_count = len(tokenizer.encode(rendered, add_special_tokens=False))
                if token_count > max_training_tokens:
                    skipped.append(document.id)
                    continue
            records[split].append({"messages": messages})
            metadata.append({"id": f"C2-{document.id}" if patch_oriented else f"C1-{document.id}", "source_id": document.id, "project": project, "language": document.language, "split": split, "kind": example_kind, "test_source_id": test_document.id if test_text else None})
            language_counts[document.language] += 1
            project_counts[project] += 1
    test_contract_examples = sum(1 for item in metadata if item["test_source_id"] is not None)
    if test_contract_examples < minimum_test_contract_examples:
        raise ValueError(
            f"Dataset has {test_contract_examples} test-contract examples; requires at least {minimum_test_contract_examples}."
        )
    output.mkdir(parents=True)
    for split, rows in records.items():
        (output / f"{split}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    manifest = {"schema_version": 4 if patch_oriented else 1, "space": "code", "dataset_name": name, "profile": "patch-oriented" if patch_oriented else "completion", "max_files_per_project": max_files_per_project, "max_characters": max_characters, "max_training_tokens": max_training_tokens if patch_oriented else None, "held_out_projects": sorted(held_out), "minimum_test_contract_examples": minimum_test_contract_examples, "test_contract_examples": test_contract_examples, "split_counts": {key: len(value) for key, value in records.items()}, "languages": dict(sorted(language_counts.items())), "projects": dict(sorted(project_counts.items())), "examples": metadata, "skipped_document_ids": skipped}
    (output / "dataset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_code_dataset(output)
    return manifest["split_counts"]


def validate_code_dataset(output: Path) -> dict[str, int]:
    manifest = json.loads((output / "dataset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("space") != "code":
        raise ValueError("Dataset is not namespaced as code.")
    projects: dict[str, str] = {}
    held_out = set(manifest.get("held_out_projects", []))
    counts: Counter[str] = Counter()
    for item in manifest["examples"]:
        if item["project"] in held_out:
            raise ValueError(f"Held-out evaluation project appears in dataset: {item['project']}")
        prior = projects.setdefault(item["project"], item["split"])
        if prior != item["split"]:
            raise ValueError(f"Project crosses dataset splits: {item['project']}")
        counts[item["split"]] += 1
    for split in ("train", "validation", "test"):
        lines = (output / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        if len(lines) != counts[split]:
            raise ValueError(f"{split} count does not match manifest.")
    return dict(counts)
