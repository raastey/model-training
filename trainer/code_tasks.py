"""Approved, metadata-only task manifests for Code maintenance evaluation."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from trainer.config import ProjectPaths


@dataclass(frozen=True)
class CodeMaintenanceTask:
    """One held-out source/test contract. Paths are relative to a project root."""

    id: str
    project: str
    project_directory: str
    source_path: str
    test_path: str
    runner: str
    test_selector: str


@dataclass(frozen=True)
class TemporaryTaskWorkspace:
    """A disposable copy of exactly one evaluation project."""

    root: Path
    project_root: Path
    source: Path
    test: Path


@dataclass(frozen=True)
class ControlledMutation:
    task_id: str
    expected_line: str
    broken_line: str


CONTROLLED_MUTATIONS: tuple[ControlledMutation, ...] = (
    ControlledMutation("CAM-01", "meterEV.isFinite && meterEV <= underexposureThresholdEV", "meterEV.isFinite && meterEV < underexposureThresholdEV"),
    ControlledMutation("CAM-02", "mirrorsOutput: front", "mirrorsOutput: false"),
    ControlledMutation("PHOTO-01", "return m < 0 ? m + count : m", "return m"),
    ControlledMutation("PHOTO-02", "encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]", "encoder.outputFormatting = [.prettyPrinted, .withoutEscapingSlashes]"),
    ControlledMutation("LUMEN-01", "if query.contains(\"darker\") || query.contains(\"lower\") || query.contains(\"reduce\") { value = -abs(value) }", "if query.contains(\"darker\") || query.contains(\"lower\") || query.contains(\"reduce\") { value = abs(value) }"),
    ControlledMutation("LUMEN-02", "if index < entries.count - 1 { entries = Array(entries.prefix(index + 1)) }", "if index < entries.count - 1 { entries = entries }"),
    ControlledMutation("DICT-01", "case .accessibility5: return 2.0", "case .accessibility5: return 1.0"),
    ControlledMutation("QURAN-01", "lower <= upper,", "lower >= upper,"),
    ControlledMutation("NG-01", 'if (!access.signedIn) return "/operator";', 'if (!access.signedIn) return "/operator?upgrade=1";'),
    ControlledMutation("NG-03", 'if (options?.commercialWatch) return "watch";', 'if (options?.commercialWatch) return "high";'),
)


APPROVED_V5_TASKS: tuple[CodeMaintenanceTask, ...] = (
    CodeMaintenanceTask("CAM-01", "Camera App", "camera-app", "basic/Models/Ladders.swift", "basicTests/StackPolicyTests.swift", "xcodebuild-ios", "basicTests/StackPolicyTests"),
    CodeMaintenanceTask("CAM-02", "Tanzaku", "tanzaku-app", "Tanzaku/Domain/PreviewGeometry.swift", "TanzakuTests/GeometryPolicyTests.swift", "xcodebuild-ios", "TanzakuTests/PreviewGeometryTests"),
    CodeMaintenanceTask("PHOTO-01", "Kineto", "kineto-video-app", "Kineto/Domain/EraMatrix.swift", "KinetoTests/EraMatrixTests.swift", "xcodebuild-ios", "KinetoTests/EraMatrixTests"),
    CodeMaintenanceTask("PHOTO-02", "SixTwelve PhotoLab", "sixtwelve-photolab-app", "Sources/PLCore/PLDocument.swift", "Tests/DocumentModelTests.swift", "xcodebuild-macos", "SixTwelvePhotoLabTests/DocumentModelTests/testChecksumIsStableAndKnown"),
    CodeMaintenanceTask("PHOTO-03", "Photo editing app", "photo-editing-app", "whistler/Processing/Recipes/RecipeLibrary.swift", "whistlerTests/RecipeParityTests.swift", "xcodebuild-ios", "whistlerTests/RecipeParityTests"),
    CodeMaintenanceTask("LUMEN-01", "Lumen", "lumen-app", "Lumen/Services/CommandPlanner.swift", "LumenTests/LumenTests.swift", "xcodebuild-macos", "LumenTests/LumenTests/testCommandParserUsesTheRequestedAmount"),
    CodeMaintenanceTask("LUMEN-02", "Lumen", "lumen-app", "Lumen/Model/HistoryTimeline.swift", "LumenTests/LumenTests.swift", "xcodebuild-macos", "LumenTests/LumenTests/testHistoryTimelineDropsRedoBranch"),
    CodeMaintenanceTask("DICT-01", "Dictionary", "dictionary-app", "DictionaryApp/Theme/LemmaTheme.swift", "DictionaryAppTests/LemmaThemeTests.swift", "xcodebuild-ios", "DictionaryAppTests/LemmaThemeTests/testSerifScaleIsMonotonic"),
    CodeMaintenanceTask("QURAN-01", "Mishkat Quran", "mishkat-quran-app", "Packages/MishkatKit/Sources/QuranDomain/Identifiers/VerseReference.swift", "Packages/MishkatKit/Tests/QuranDomainTests/VerseReferenceTests.swift", "swiftpm", "VerseReferenceTests"),
    CodeMaintenanceTask("QURAN-02", "Mishkat Quran", "mishkat-quran-app", "Packages/MishkatKit/Sources/QuranDomain/Audio/PlaybackState.swift", "Packages/MishkatKit/Tests/QuranDomainTests/RepeatSettingsTests.swift", "swiftpm", "RepeatCountTests"),
    CodeMaintenanceTask("NG-01", "NauticGrid", "nauticgrid", "lib/operator/entry-href.ts", "lib/operator/entry-href.test.ts", "vitest", "lib/operator/entry-href.test.ts"),
    CodeMaintenanceTask("NG-03", "NauticGrid", "nauticgrid", "lib/operator/priority.ts", "lib/operator/priority.test.ts", "vitest", "lib/operator/priority.test.ts"),
)


def code_task_manifest_path(paths: ProjectPaths, name: str = "v5-approved-001") -> Path:
    return paths.root / "reports" / "code" / "task-manifests" / f"{name}.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _task_record(paths: ProjectPaths, task: CodeMaintenanceTask) -> dict[str, object]:
    project_root = paths.root.parent / task.project_directory
    source = project_root / task.source_path
    test = project_root / task.test_path
    if not source.is_file() or not test.is_file():
        missing = source if not source.is_file() else test
        raise ValueError(f"Approved task file is unavailable: {task.id} ({missing})")
    return {
        **asdict(task),
        "source_sha256": _sha256(source),
        "test_sha256": _sha256(test),
        "status": "runner-qualified",
    }


def _relative_task_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Task path must remain within its project: {value}")
    return path


@contextmanager
def temporary_task_workspace(
    paths: ProjectPaths, task: CodeMaintenanceTask, expected_line: str | None = None, broken_line: str | None = None,
) -> Iterator[TemporaryTaskWorkspace]:
    """Copy one project outside the repository, optionally applying one exact mutation.

    The project copy and all build products are deleted when this context closes. The
    optional mutation must replace exactly one source line, preventing broad or
    ambiguous changes from becoming evaluation fixtures.
    """
    source_project = paths.root.parent / task.project_directory
    source_relative = _relative_task_path(task.source_path)
    test_relative = _relative_task_path(task.test_path)
    if not (source_project / source_relative).is_file() or not (source_project / test_relative).is_file():
        raise ValueError(f"Approved task file is unavailable: {task.id}")
    if (expected_line is None) != (broken_line is None):
        raise ValueError("A controlled mutation requires both expected and broken lines.")
    with tempfile.TemporaryDirectory(prefix="sixtwelve-code-task-") as directory:
        root = Path(directory)
        project_root = root / task.project_directory
        shutil.copytree(
            source_project,
            project_root,
            ignore=shutil.ignore_patterns(".git", "DerivedData", "build", ".build", "node_modules", "Pods"),
        )
        target = project_root / source_relative
        if expected_line is not None and broken_line is not None:
            original = target.read_text(encoding="utf-8")
            if original.count(expected_line) != 1:
                raise ValueError(f"Controlled mutation line must occur exactly once: {task.id}")
            target.write_text(original.replace(expected_line, broken_line, 1), encoding="utf-8")
        yield TemporaryTaskWorkspace(root, project_root, target, project_root / test_relative)


def build_code_task_manifest(
    paths: ProjectPaths, name: str = "v5-approved-001", tasks: tuple[CodeMaintenanceTask, ...] = APPROVED_V5_TASKS,
) -> Path:
    """Write a metadata-only manifest; never copy evaluation source or test contents."""
    output = code_task_manifest_path(paths, name)
    if output.exists():
        raise ValueError(f"Task manifest already exists: {output}")
    if len({task.id for task in tasks}) != len(tasks):
        raise ValueError("Task manifest contains duplicate task IDs.")
    records = [_task_record(paths, task) for task in tasks]
    payload = {
        "schema_version": 1,
        "space": "code",
        "kind": "approved-maintenance-task-manifest",
        "name": name,
        "created_at": datetime.now(UTC).isoformat(),
        "task_count": len(records),
        "tasks": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_code_task_manifest(output)
    return output


def validate_code_task_manifest(path: Path) -> dict[str, int]:
    """Validate manifest structure and ensure source/test content was never persisted."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("space") != "code":
        raise ValueError("Unsupported Code task manifest.")
    if payload.get("kind") != "approved-maintenance-task-manifest":
        raise ValueError("Manifest is not an approved maintenance task manifest.")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or payload.get("task_count") != len(tasks):
        raise ValueError("Task count does not match task records.")
    ids = [task.get("id") for task in tasks]
    if len(ids) != len(set(ids)) or not all(isinstance(value, str) and value for value in ids):
        raise ValueError("Task IDs must be unique and non-empty.")
    required = {"project", "project_directory", "source_path", "test_path", "runner", "test_selector", "source_sha256", "test_sha256", "status"}
    for task in tasks:
        if not required.issubset(task):
            raise ValueError(f"Task record is incomplete: {task.get('id', 'unknown')}")
        if task["status"] != "runner-qualified":
            raise ValueError(f"Task is not runner-qualified: {task['id']}")
        if any(key in task for key in ("source", "test", "source_content", "test_content")):
            raise ValueError("Task manifest must not store source or test content.")
    return {"tasks": len(tasks), "projects": len({task["project_directory"] for task in tasks})}
