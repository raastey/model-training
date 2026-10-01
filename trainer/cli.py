"""Development CLI for the local training pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from trainer.agentic import code_markdown_table, load_code_tasks, mlx_chat_generator, run_code_study
from trainer.benchmarks import (
    load_relevance_cases,
    relevance_recall_at_k,
    repeated_ngram_ratio,
    runtime_output_issue,
    self_retrieval_cases,
)
from trainer.code import (
    build_code_dataset,
    import_code_corpus,
    inspect_code_repository,
    inspect_code_workspace,
    validate_code_dataset,
)
from trainer.code_curriculum import build_repair_curriculum
from trainer.code_evaluation import (
    evaluate_code_patch,
    evaluate_code_smoke,
    evaluate_nauticgrid_entry_patch,
)
from trainer.code_history import build_historical_repair_dataset
from trainer.code_tasks import build_code_task_manifest, validate_code_task_manifest
from trainer.config import project_paths
from trainer.context import build_writer_index, embed_texts, retrieve_writer_context
from trainer.corpus import import_writer_corpus, list_documents, set_quality
from trainer.dataset import build_writer_dataset, validate_writer_dataset
from trainer.doctor import as_dict, inspect
from trainer.evaluation import create_blind_writer_evaluation
from trainer.models import (
    code_7b_model,
    code_model,
    download_code_7b_model,
    download_code_model,
    download_writer_model,
    writer_model,
)
from trainer.runtime import (
    complete_sentences_for_display,
    evaluate_context_output,
    fit_complete_sentences_to_words,
    generate_writer_output,
    writer_context_prompt,
)
from trainer.study import (
    build_blind_review,
    load_tasks,
    markdown_table,
    mlx_generator,
    run_writer_study,
    score_blind_review,
)
from trainer.training import (
    execute_prepared_run,
    prepare_code_7b_v8_run,
    prepare_code_patch_run,
    prepare_code_smoke_run,
    prepare_code_v5_run,
    prepare_code_v7_run,
    prepare_code_v8_run,
    prepare_writer_chunked_run,
    prepare_writer_context_rebalanced_run,
    prepare_writer_context_run,
    prepare_writer_smoke_run,
    prepare_writer_voice_regularized_run,
)

app = typer.Typer(no_args_is_help=True, help="SIXTWELVE local AI training tools.")
corpus_app = typer.Typer(no_args_is_help=True, help="Private local corpus management.")
dataset_app = typer.Typer(no_args_is_help=True, help="Dataset build and validation.")
model_app = typer.Typer(no_args_is_help=True, help="Local base model management.")
train_app = typer.Typer(no_args_is_help=True, help="Local, non-promoting training runs.")
eval_app = typer.Typer(no_args_is_help=True, help="Local candidate evaluation.")
context_app = typer.Typer(no_args_is_help=True, help="Local Writer working-context retrieval.")
code_app = typer.Typer(no_args_is_help=True, help="Strictly isolated Code corpus preparation.")
study_app = typer.Typer(no_args_is_help=True, help="Reproducible context-versus-weights studies.")
app.add_typer(corpus_app, name="corpus")
app.add_typer(dataset_app, name="dataset")
app.add_typer(model_app, name="model")
app.add_typer(train_app, name="train")
app.add_typer(eval_app, name="eval")
app.add_typer(context_app, name="context")
app.add_typer(code_app, name="code")
app.add_typer(study_app, name="study")
console = Console()


@app.callback()
def main() -> None:
    """Developer commands for the local training laboratory."""


@app.command()
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable diagnostics."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory to inspect."),
) -> None:
    """Check the local environment without downloading or modifying anything."""
    report = as_dict(inspect(project_paths(root)))
    if json_output:
        console.print_json(json.dumps(report))
        return
    table = Table(title="SIXTWELVE training diagnostics")
    table.add_column("Check")
    table.add_column("Result")
    for key, value in report.items():
        table.add_row(key.replace("_", " "), str(value))
    console.print(table)


@corpus_app.command("import")
def corpus_import(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0B."),
    source: Path = typer.Argument(..., exists=True, readable=True),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Import Markdown and text files, quarantining likely secrets."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0B.", param_hint="space")
    result = import_writer_corpus(project_paths(root), source)
    console.print(
        f"Imported {len(result.imported)}; duplicates {len(result.duplicates)}; "
        f"quarantined {len(result.quarantined)}; ignored {len(result.ignored)}."
    )
    for item in result.quarantined:
        console.print(f"[yellow]Quarantined[/yellow] {item.source_path} ({', '.join(item.findings)})")


@corpus_app.command("list")
def corpus_list(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0B."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """List imported documents and their review state."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0B.", param_hint="space")
    table = Table(title="Writer corpus")
    table.add_column("ID")
    table.add_column("Quality")
    table.add_column("Words")
    table.add_column("Title")
    for document in list_documents(project_paths(root)):
        table.add_row(document.id, document.quality, str(document.word_count), document.title)
    console.print(table)


@corpus_app.command("label")
def corpus_label(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0B."),
    document_id: str = typer.Argument(...),
    quality: str = typer.Argument(..., help="gold, good, reference_only, or exclude"),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Record a human quality decision for an imported document."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0B.", param_hint="space")
    document = set_quality(project_paths(root), document_id, quality)
    console.print(f"{document.id} → {document.quality}")


@dataset_app.command("build")
def dataset_build(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0C."),
    name: str = typer.Option("v1", "--name", help="New dataset output name."),
    chunk_characters: int = typer.Option(0, "--chunk-characters", min=0, help="Target chunk size; 0 keeps full documents."),
    context_tasks: bool = typer.Option(False, "--context-tasks", help="Add derived Writer context-management tasks."),
    context_profile: str = typer.Option("full", "--context-profile", help="Context profile: full or balanced."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Build a validated Writer dataset from gold/good documents."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0C.", param_hint="space")
    try:
        result = build_writer_dataset(project_paths(root), name, chunk_characters, context_tasks, context_profile)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Built {result.output_dir}: {result.examples_by_split}; skipped {len(result.skipped_document_ids)}.")


@dataset_app.command("validate")
def dataset_validate(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0C."),
    name: str = typer.Option("v1", "--name", help="Dataset output name."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Validate a previously generated Writer dataset."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0C.", param_hint="space")
    try:
        counts = validate_writer_dataset(project_paths(root).root / "datasets" / "writer" / name)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Valid Writer dataset: {counts}")


@model_app.command("status")
def model_status(
    space: str = typer.Argument(..., help="writer or code."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Show whether the local Writer base model is ready."""
    if space not in {"writer", "code", "code-7b"}:
        raise typer.BadParameter("Only 'writer', 'code', or 'code-7b' is available.", param_hint="space")
    model = writer_model(project_paths(root)) if space == "writer" else code_model(project_paths(root)) if space == "code" else code_7b_model(project_paths(root))
    console.print(f"{model.space}: {'ready' if model.ready else 'not downloaded'} ({model.repository})")


@model_app.command("download")
def model_download(
    space: str = typer.Argument(..., help="writer or code."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Explicitly download the local Writer base model."""
    if space not in {"writer", "code", "code-7b"}:
        raise typer.BadParameter("Only 'writer', 'code', or 'code-7b' is available.", param_hint="space")
    model = download_writer_model(project_paths(root)) if space == "writer" else download_code_model(project_paths(root)) if space == "code" else download_code_7b_model(project_paths(root))
    console.print(f"Downloaded and verified {model.repository}.")


@code_app.command("inspect")
def code_inspect(
    source: Path = typer.Argument(..., exists=True, readable=True),
    exclude_dir: list[str] = typer.Option(["writings"], "--exclude-dir", help="Directory name to exclude; repeatable."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Training project directory."),
) -> None:
    """Inspect a code repository without copying a file or downloading a model."""
    try:
        result = inspect_code_repository(project_paths(root), source, frozenset(exclude_dir))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Accepted {len(result.accepted)}; quarantined {len(result.quarantined)}; ignored {len(result.ignored)}; languages {result.languages}.")
    for item in result.quarantined:
        console.print(f"[yellow]Quarantined[/yellow] {item.source_path} ({', '.join(item.findings)})")


@code_app.command("import")
def code_import(
    source: Path = typer.Argument(..., exists=True, readable=True),
    exclude_dir: list[str] = typer.Option(["writings"], "--exclude-dir", help="Directory name to exclude; repeatable."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Training project directory."),
) -> None:
    """Import source/config files into the separate Code corpus after inspection."""
    try:
        result = import_code_corpus(project_paths(root), source, frozenset(exclude_dir))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Imported {len(result.imported)}; duplicates {len(result.duplicates)}; quarantined {len(result.quarantined)}; ignored {len(result.ignored)}.")


@code_app.command("workspace-inspect")
def code_workspace_inspect(
    workspace: Path = typer.Argument(..., exists=True, readable=True),
    exclude_dir: list[str] = typer.Option(["writings"], "--exclude-dir", help="Top-level directory name to exclude; repeatable."),
    offset: int = typer.Option(0, "--offset", min=0, help="Zero-based top-level project batch offset."),
    limit: int = typer.Option(10, "--limit", min=1, max=25, help="Projects to inspect in this read-only batch."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Training project directory."),
) -> None:
    """Inspect a bounded batch of a multi-project workspace without importing it."""
    try:
        result = inspect_code_workspace(project_paths(root), workspace, frozenset(exclude_dir), offset, limit)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    report_path = project_paths(root).root / "reports" / "code" / f"workspace-inventory-{offset}-{limit}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"total_projects": result.total_projects, "offset": offset, "next_offset": result.next_offset, "projects": result.projects}, indent=2) + "\n", encoding="utf-8")
    console.print(f"Inspected {len(result.projects)}/{result.total_projects} projects; next offset: {result.next_offset}; report: {report_path}")
    for project in result.projects:
        console.print(f"{project['project']}: accepted {project['accepted']}; quarantined {project['quarantined']}; languages {project['languages']}")


@code_app.command("dataset-build")
def code_dataset_build(
    name: str = typer.Option("v1", "--name"),
    max_files_per_project: int = typer.Option(80, "--max-files-per-project", min=1),
    max_characters: int = typer.Option(6000, "--max-characters", min=100),
    patch_oriented: bool = typer.Option(False, "--patch-oriented", help="Build constrained full-file replacement examples."),
    max_training_tokens: int = typer.Option(1800, "--max-training-tokens", min=100, max=2048),
    exclude_project: list[str] = typer.Option([], "--exclude-project", help="Project name to hold out; repeatable."),
    minimum_test_contract_examples: int = typer.Option(0, "--minimum-test-contract-examples", min=0),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Build a balanced, project-split Code dataset without training a model."""
    try:
        counts = build_code_dataset(project_paths(root), name, max_files_per_project, max_characters, patch_oriented, max_training_tokens, frozenset(exclude_project), minimum_test_contract_examples)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Built Code dataset {name}: {counts}")


@code_app.command("dataset-validate")
def code_dataset_validate(name: str = typer.Option("v1", "--name"), root: Path = typer.Option(Path.cwd(), "--root")) -> None:
    """Validate a previously built Code dataset."""
    try:
        counts = validate_code_dataset(project_paths(root).root / "datasets" / "code" / name)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Valid Code dataset: {counts}")


@code_app.command("repair-curriculum-build")
def code_repair_curriculum_build(
    name: str = typer.Option("v7", "--name"),
    episodes: int = typer.Option(120, "--episodes", min=30),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Build a test-guided repair-only curriculum independent of held-out evaluations."""
    try:
        counts = build_repair_curriculum(project_paths(root), name, episodes)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Built repair-first Code curriculum {name}: {counts}")


@code_app.command("history-repair-build")
def code_history_repair_build(
    name: str = typer.Option("v8", "--name"),
    limit: int = typer.Option(300, "--limit", min=30, max=1000),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Build repair-only episodes from local user-project Git history."""
    try:
        counts = build_historical_repair_dataset(project_paths(root), name, limit)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Built real-history Code repair dataset {name}: {counts}")


@code_app.command("task-manifest-build")
def code_task_manifest_build(
    name: str = typer.Option("v5-approved-001", "--name", help="New approved task-manifest name."),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Record hashes and runner metadata for the approved held-out task set."""
    try:
        output = build_code_task_manifest(project_paths(root), name)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Built metadata-only Code task manifest: {output}")


@code_app.command("task-manifest-validate")
def code_task_manifest_validate(
    name: str = typer.Option("v5-approved-001", "--name"),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Validate an approved task manifest without reading project source into reports."""
    try:
        counts = validate_code_task_manifest(project_paths(root).root / "reports" / "code" / "task-manifests" / f"{name}.json")
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Valid Code task manifest: {counts}")


@code_app.command("chat")
def code_chat(
    prompt: str = typer.Argument(..., help="Coding task for the local Code base model."),
    base: str = typer.Option("7b", "--base", help="Local Code base to use: 7b (preferred) or 3b."),
    max_tokens: int = typer.Option(300, "--max-tokens", "-n", min=1, max=4096),
    root: Path = typer.Option(Path.cwd(), "--root", help="Training project directory."),
) -> None:
    """Run the unmodified local Code base without importing or storing code."""
    if base not in {"3b", "7b"}:
        raise typer.BadParameter("Base must be '7b' or '3b'.", param_hint="base")
    model = code_7b_model(project_paths(root)) if base == "7b" else code_model(project_paths(root))
    if not model.ready:
        raise typer.BadParameter(f"Code {base} model is not downloaded. Run: sixai model download code{'-7b' if base == '7b' else ''}")
    console.print(generate_writer_output(model.path, prompt, max_tokens=max_tokens))


@code_app.command("train-smoke")
def code_train_smoke(
    run_id: str = typer.Option("code-smoke-001", "--run-id"),
    execute: bool = typer.Option(True, "--execute/--prepare-only", help="Run the bounded local candidate after staging it."),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Train one small Code-only candidate; it is never promoted automatically."""
    try:
        prepared = prepare_code_smoke_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; Code-only candidate remains unpromoted.")
        if execute:
            execute_prepared_run(prepared)
            console.print(f"Completed candidate {prepared.run_id}; evaluate it before any use.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@code_app.command("train-patch")
def code_train_patch(
    run_id: str = typer.Option("code-patch-001", "--run-id"),
    execute: bool = typer.Option(True, "--execute/--prepare-only"),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Train one bounded Code-only patch candidate; it is never promoted automatically."""
    try:
        prepared = prepare_code_patch_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; Code-only candidate remains unpromoted.")
        if execute:
            execute_prepared_run(prepared)
            console.print(f"Completed candidate {prepared.run_id}; evaluate it before any use.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@code_app.command("train-v5")
def code_train_v5(
    run_id: str = typer.Option("code-v5-001", "--run-id"),
    execute: bool = typer.Option(True, "--execute/--prepare-only"),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Train the approved held-out Code v5 candidate; it is never promoted automatically."""
    try:
        prepared = prepare_code_v5_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; Code-only candidate remains unpromoted.")
        if execute:
            execute_prepared_run(prepared)
            console.print(f"Completed candidate {prepared.run_id}; evaluate it before any use.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@code_app.command("train-v7")
def code_train_v7(
    run_id: str = typer.Option("code-v7-001", "--run-id"),
    execute: bool = typer.Option(True, "--execute/--prepare-only"),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Train a small repair-first candidate; it is never promoted automatically."""
    try:
        prepared = prepare_code_v7_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; Code-only candidate remains unpromoted.")
        if execute:
            execute_prepared_run(prepared)
            console.print(f"Completed candidate {prepared.run_id}; evaluate it before any use.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@code_app.command("train-v8")
def code_train_v8(
    run_id: str = typer.Option("code-v8-001", "--run-id"),
    execute: bool = typer.Option(True, "--execute/--prepare-only"),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Train a real-history repair candidate; it is never promoted automatically."""
    try:
        prepared = prepare_code_v8_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; Code-only candidate remains unpromoted.")
        if execute:
            execute_prepared_run(prepared)
            console.print(f"Completed candidate {prepared.run_id}; evaluate it before any use.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@code_app.command("train-7b-v8")
def code_train_7b_v8(
    run_id: str = typer.Option("code-7b-v8-001", "--run-id"),
    execute: bool = typer.Option(True, "--execute/--prepare-only"),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Train a minimal 7B real-history candidate; it is never promoted automatically."""
    try:
        prepared = prepare_code_7b_v8_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; 7B Code candidate remains unpromoted.")
        if execute:
            execute_prepared_run(prepared)
            console.print(f"Completed candidate {prepared.run_id}; evaluate it before any use.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@code_app.command("eval-smoke")
def code_eval_smoke(
    adapter_run: str | None = typer.Option(None, "--adapter-run", "-a", help="Candidate Code run ID to evaluate."),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Generate and execute two self-contained Code checks for base or candidate."""
    paths = project_paths(root)
    model = code_model(paths)
    if not model.ready:
        raise typer.BadParameter("Code model is not downloaded.")
    adapter_path = None
    label = "base"
    if adapter_run:
        candidate = paths.root / "adapters" / "code" / adapter_run / "adapters.safetensors"
        if not candidate.is_file():
            raise typer.BadParameter(f"No completed Code adapter: {adapter_run}")
        adapter_path = candidate.parent
        label = adapter_run
    results = evaluate_code_smoke(model.path, adapter_path)
    report = paths.root / "evals" / "code" / f"{label}-smoke.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"model": model.repository, "adapter_run": adapter_run, "results": results}, indent=2) + "\n", encoding="utf-8")
    passed = sum(item["passed"] for item in results)
    console.print(f"code_smoke={passed}/{len(results)}; report: {report}")


@code_app.command("eval-patch")
def code_eval_patch(
    adapter_run: str | None = typer.Option(None, "--adapter-run", "-a", help="Candidate Code run ID to evaluate."),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Evaluate base or candidate with bounded file-replacement regression fixtures."""
    paths = project_paths(root)
    model = code_model(paths)
    if not model.ready:
        raise typer.BadParameter("Code model is not downloaded.")
    adapter_path = None
    label = "base"
    if adapter_run:
        candidate = paths.root / "adapters" / "code" / adapter_run / "adapters.safetensors"
        if not candidate.is_file():
            raise typer.BadParameter(f"No completed Code adapter: {adapter_run}")
        adapter_path = candidate.parent
        label = adapter_run
    results = evaluate_code_patch(model.path, adapter_path)
    report = paths.root / "evals" / "code" / f"{label}-patch.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"model": model.repository, "adapter_run": adapter_run, "results": results}, indent=2) + "\n", encoding="utf-8")
    passed = sum(item["passed"] for item in results)
    console.print(f"code_patch={passed}/{len(results)}; report: {report}")


@code_app.command("eval-real")
def code_eval_real(
    adapter_run: str | None = typer.Option(None, "--adapter-run", "-a", help="Candidate Code run ID to evaluate."),
    root: Path = typer.Option(Path.cwd(), "--root"),
) -> None:
    """Run a controlled mutation of real local source in a temporary workspace."""
    paths = project_paths(root)
    model = code_model(paths)
    if not model.ready:
        raise typer.BadParameter("Code model is not downloaded.")
    adapter_path = None
    label = "base"
    if adapter_run:
        candidate = paths.root / "adapters" / "code" / adapter_run / "adapters.safetensors"
        if not candidate.is_file():
            raise typer.BadParameter(f"No completed Code adapter: {adapter_run}")
        adapter_path = candidate.parent
        label = adapter_run
    try:
        results = evaluate_nauticgrid_entry_patch(model.path, paths.root.parent, adapter_path)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    report = paths.root / "evals" / "code" / f"{label}-real.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"model": model.repository, "adapter_run": adapter_run, "results": results}, indent=2) + "\n", encoding="utf-8")
    passed = sum(item["passed"] for item in results)
    console.print(f"code_real={passed}/{len(results)}; report: {report}")


@app.command()
def chat(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0D."),
    prompt: str = typer.Argument(..., help="Prompt for the local base model."),
    max_tokens: int = typer.Option(300, "--max-tokens", "-n", min=1, max=4096),
    adapter_run: str | None = typer.Option(
        None, "--adapter-run", "-a", help="Candidate Writer run ID to load."
    ),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run a direct local smoke-test conversation with the selected base model."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0D.", param_hint="space")
    model = writer_model(project_paths(root))
    if not model.ready:
        raise typer.BadParameter("Writer model is not downloaded. Run: sixai model download writer")
    command = [
        str(Path(sys.executable).with_name("mlx_lm.generate")), "--model", str(model.path),
    ]
    if adapter_run:
        adapter_path = project_paths(root).root / "adapters" / "writer" / adapter_run
        if not (adapter_path / "adapters.safetensors").is_file():
            raise typer.BadParameter(f"No ready adapter for Writer run: {adapter_run}")
        command.extend(["--adapter-path", str(adapter_path)])
    command.extend([
        "--prompt", prompt, "--max-tokens", str(max_tokens), "--temp", "0.3", "--verbose", "false",
    ])
    subprocess.run(
        command,
        check=True,
    )


@train_app.command("smoke")
def train_smoke(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 0D."),
    run_id: str = typer.Option("writer-smoke-001", "--run-id", help="New immutable run ID."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Prepare and execute a 10-step local Writer QLoRA smoke run."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in Phase 0D.", param_hint="space")
    try:
        prepared = prepare_writer_smoke_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; starting local smoke training.")
        execute_prepared_run(prepared)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@train_app.command("chunked")
def train_chunked(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 1."),
    run_id: str = typer.Option("writer-chunked-001", "--run-id", help="New immutable run ID."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run the first 100-step section-sized Writer QLoRA candidate."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    try:
        prepared = prepare_writer_chunked_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; starting local chunked training.")
        execute_prepared_run(prepared)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@train_app.command("context")
def train_context(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 1."),
    run_id: str = typer.Option("writer-context-002", "--run-id", help="New immutable run ID."),
    profile: str = typer.Option("rebalanced", "--profile", help="rebalanced for v4; initial for the retained v3 profile."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run a separate context-aware Writer QLoRA candidate."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    try:
        prepared = prepare_writer_context_rebalanced_run(project_paths(root), run_id) if profile == "rebalanced" else prepare_writer_context_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; starting local context-aware training.")
        execute_prepared_run(prepared)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@train_app.command("voice")
def train_voice(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    run_id: str = typer.Option("writer-voice-001", "--run-id", help="New immutable run ID."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Train a small authentic-prose-only Writer voice candidate over v6."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    try:
        prepared = prepare_writer_voice_regularized_run(project_paths(root), run_id)
        console.print(f"Prepared {prepared.run_id}; starting local voice training.")
        execute_prepared_run(prepared)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error


@eval_app.command("blind")
def eval_blind(
    space: str = typer.Argument(..., help="Only 'writer' is available in Phase 1."),
    candidate_run: str = typer.Option(..., "--candidate", help="Writer candidate run ID."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Generate a blinded base-versus-candidate Writer comparison."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    try:
        evaluation = create_blind_writer_evaluation(project_paths(root), candidate_run)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(f"Blind review ready: {evaluation.review_path}")


@context_app.command("build-index")
def context_build_index(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Build a local, inspectable Writer retrieval index."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    console.print(f"Indexed {build_writer_index(project_paths(root), use_semantic=True)} Writer chunks with hybrid retrieval.")


@context_app.command("inspect")
def context_inspect(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    query: str = typer.Argument(..., help="Current writing objective or question."),
    sources: int = typer.Option(5, "--sources", "-k", min=1, max=5, help="Maximum retrieved Writer sections."),
    context_budget: int = typer.Option(9000, "--context-budget", min=500, max=12000, help="Maximum characters supplied as context."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Show why local Writer context would be selected, without running a model."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    try:
        retrieved = retrieve_writer_context(project_paths(root), query, limit=sources, budget_characters=context_budget)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    table = Table(title="Selected Writer context")
    table.add_column("Score")
    table.add_column("Matched terms")
    table.add_column("Semantic")
    table.add_column("Source ID")
    table.add_column("Source")
    table.add_column("Section")
    for item in retrieved:
        table.add_row(f"{item.score:.2f}", ", ".join(item.matched_terms), f"{item.semantic_score:.2f}", item.chunk.document_id, item.chunk.title, str(item.chunk.section_number))
    console.print(table)


@context_app.command("chat")
def context_chat(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    query: str = typer.Argument(..., help="Writing task to answer using local context."),
    adapter_run: str | None = typer.Option(None, "--adapter-run", "-a", help="Candidate Writer run ID to load."),
    fallback_base: bool = typer.Option(True, "--fallback-base/--no-fallback-base", help="Use the stable base model if an adapter output fails the runtime gate."),
    max_tokens: int = typer.Option(220, "--max-tokens", "-n", min=1, max=4096, help="Maximum local response length."),
    max_words: int | None = typer.Option(None, "--max-words", "-w", min=1, help="Optional display budget that keeps complete sentences."),
    sources: int = typer.Option(5, "--sources", "-k", min=1, max=5, help="Maximum retrieved Writer sections."),
    context_budget: int = typer.Option(9000, "--context-budget", min=500, max=12000, help="Maximum characters supplied as context."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run the local Writer model with an inspectable retrieved context package."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    paths = project_paths(root)
    model = writer_model(paths)
    if not model.ready:
        raise typer.BadParameter("Writer model is not downloaded.")
    try:
        retrieved = retrieve_writer_context(paths, query, limit=sources, budget_characters=context_budget)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    if not retrieved:
        raise typer.BadParameter("No relevant Writer context was found; refine the query or import relevant sources.")
    adapter_path: Path | None = None
    if adapter_run:
        adapter_path = paths.root / "adapters" / "writer" / adapter_run
        if not (adapter_path / "adapters.safetensors").is_file():
            raise typer.BadParameter(f"No ready adapter for Writer run: {adapter_run}")
    prompt = writer_context_prompt(query, retrieved)
    output = generate_writer_output(model.path, prompt, adapter_path, max_tokens)
    result = evaluate_context_output(output, retrieved)
    if result.issue and adapter_path and fallback_base:
        console.print(f"[yellow]Adapter runtime gate: {result.issue}. Returning the stable base-model response.[/yellow]")
        output = generate_writer_output(model.path, prompt, max_tokens=max_tokens)
        result = evaluate_context_output(output, retrieved)
    if result.issue:
        raise typer.BadParameter(f"Context runtime gate failed: {result.issue}")
    display_output = fit_complete_sentences_to_words(complete_sentences_for_display(output), max_words)
    if display_output != output:
        console.print("[dim]Response was shortened to complete sentences for the requested limit.[/dim]")
    console.print(display_output)


@eval_app.command("repetition")
def eval_repetition(
    text: str = typer.Argument(..., help="Model output to evaluate for repeated n-grams."),
) -> None:
    """Report a transparent repetition score; scores above 0.10 require review."""
    score = repeated_ngram_ratio(text)
    issue = runtime_output_issue(text)
    console.print(f"repeated_5gram_ratio={score:.3f}; {issue or 'PASS'}")


@eval_app.command("retrieval-smoke")
def eval_retrieval_smoke(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    cases: int = typer.Option(10, "--cases", min=1, max=50, help="Number of deterministic title-to-source checks."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Check whether Writer documents can be retrieved from their own titles.

    This is an infrastructure smoke test, not a substitute for human relevance labels.
    """
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    paths = project_paths(root)
    results = []
    for case in self_retrieval_cases(list_documents(paths), cases):
        retrieved = retrieve_writer_context(paths, case.query)
        passed = relevance_recall_at_k(retrieved, {case.document_id})
        results.append({"document_id": case.document_id, "query": case.query, "passed_at_5": passed})
    passed_count = sum(result["passed_at_5"] for result in results)
    report_path = paths.root / "evals" / "writer" / "retrieval-smoke.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"kind": "self_retrieval_smoke", "results": results}, indent=2) + "\n", encoding="utf-8")
    outcome = "PASS" if passed_count == len(results) and results else "REVIEW"
    console.print(f"self_retrieval_at_5={passed_count}/{len(results)}; {outcome}; report: {report_path}")


@eval_app.command("relevance")
def eval_relevance(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    review: Path = typer.Option(Path("docs/writer-relevance-cases.json"), "--review", help="Human-labeled JSON review file."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Evaluate hybrid retrieval against explicit human relevance labels."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    paths = project_paths(root)
    review_path = review if review.is_absolute() else paths.root / review
    try:
        cases = load_relevance_cases(review_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error), param_hint="--review") from error
    results = []
    for case in cases:
        retrieved = retrieve_writer_context(paths, case.query)
        results.append({
            "id": case.id,
            "query": case.query,
            "expected_document_ids": sorted(case.expected_document_ids),
            "retrieved_document_ids": [item.chunk.document_id for item in retrieved],
            "passed_at_5": relevance_recall_at_k(retrieved, set(case.expected_document_ids)),
        })
    passed_count = sum(result["passed_at_5"] for result in results)
    report_path = paths.root / "evals" / "writer" / "relevance-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"kind": "human_labeled_relevance", "results": results}, indent=2) + "\n", encoding="utf-8")
    outcome = "PASS" if passed_count == len(results) else "REVIEW"
    console.print(f"human_relevance_at_5={passed_count}/{len(results)}; {outcome}; report: {report_path}")


@eval_app.command("context-runtime")
def eval_context_runtime(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    candidate_run: str | None = typer.Option(None, "--candidate", help="Optional Writer adapter to evaluate against context tasks."),
    review: Path = typer.Option(Path("docs/writer-relevance-cases.json"), "--review", help="Human-labeled JSON review file."),
    sources: int = typer.Option(5, "--sources", "-k", min=1, max=5, help="Maximum retrieved Writer sections."),
    context_budget: int = typer.Option(9000, "--context-budget", min=500, max=12000, help="Maximum characters supplied as context."),
    max_tokens: int = typer.Option(400, "--max-tokens", "-n", min=1, max=4096, help="Generation length to evaluate."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run every reviewed context task and reject empty/repetitive answers in the report."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    paths = project_paths(root)
    model = writer_model(paths)
    if not model.ready:
        raise typer.BadParameter("Writer model is not downloaded.")
    review_path = review if review.is_absolute() else paths.root / review
    try:
        cases = load_relevance_cases(review_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error), param_hint="--review") from error
    adapter_path = None
    label = "base"
    if candidate_run:
        adapter_path = paths.root / "adapters" / "writer" / candidate_run
        if not (adapter_path / "adapters.safetensors").is_file():
            raise typer.BadParameter(f"No ready adapter for Writer run: {candidate_run}")
        label = candidate_run
    results = []
    for case in cases:
        retrieved = retrieve_writer_context(paths, case.query, limit=sources, budget_characters=context_budget)
        output = generate_writer_output(model.path, writer_context_prompt(case.query, retrieved), adapter_path, max_tokens)
        runtime = evaluate_context_output(output, retrieved)
        results.append({"id": case.id, "issue": runtime.issue, "output_characters": len(runtime.output), "retrieved_document_ids": [item.chunk.document_id for item in retrieved]})
    passed_count = sum(item["issue"] is None for item in results)
    report_path = paths.root / "evals" / "writer" / f"context-runtime-{label}-{context_budget}-{max_tokens}.json"
    report_path.write_text(json.dumps({"candidate": label, "sources": sources, "context_budget": context_budget, "max_tokens": max_tokens, "results": results}, indent=2) + "\n", encoding="utf-8")
    outcome = "PASS" if passed_count == len(results) else "REVIEW"
    console.print(f"context_runtime={passed_count}/{len(results)}; {outcome}; report: {report_path}")


@eval_app.command("context-ablation")
def eval_context_ablation(
    space: str = typer.Argument(..., help="Only 'writer' is available in this phase."),
    candidate_run: str = typer.Option(..., "--candidate", help="Writer adapter to diagnose."),
    review: Path = typer.Option(Path("docs/writer-relevance-cases.json"), "--review", help="Human-labeled JSON review file."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Compare one adapter across 3k, 6k, and 9k local context budgets."""
    if space != "writer":
        raise typer.BadParameter("Only 'writer' is available in this phase.", param_hint="space")
    paths = project_paths(root)
    model = writer_model(paths)
    if not model.ready:
        raise typer.BadParameter("Writer model is not downloaded.")
    adapter_path = paths.root / "adapters" / "writer" / candidate_run
    if not (adapter_path / "adapters.safetensors").is_file():
        raise typer.BadParameter(f"No ready adapter for Writer run: {candidate_run}")
    review_path = review if review.is_absolute() else paths.root / review
    try:
        cases = load_relevance_cases(review_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise typer.BadParameter(str(error), param_hint="--review") from error
    variants = []
    for budget in (3000, 6000, 9000):
        results = []
        for case in cases:
            retrieved = retrieve_writer_context(paths, case.query, limit=5, budget_characters=budget)
            output = generate_writer_output(model.path, writer_context_prompt(case.query, retrieved), adapter_path)
            runtime = evaluate_context_output(output, retrieved)
            results.append({"id": case.id, "issue": runtime.issue, "output_characters": len(runtime.output), "retrieved_count": len(retrieved)})
        variants.append({"context_budget": budget, "passed": sum(item["issue"] is None for item in results), "total": len(results), "results": results})
    report_path = paths.root / "evals" / "writer" / f"context-ablation-{candidate_run}.json"
    report_path.write_text(json.dumps({"candidate": candidate_run, "variants": variants}, indent=2) + "\n", encoding="utf-8")
    summary = ", ".join(f"{item['context_budget']}={item['passed']}/{item['total']}" for item in variants)
    console.print(f"context_ablation {summary}; report: {report_path}")


@study_app.command("writer")
def study_writer(
    adapter_run: str = typer.Option("writer-voice-001", "--adapter", help="Writer adapter for the weights conditions."),
    tasks: Path = typer.Option(Path("evals/study/writer-tasks.json"), "--tasks", help="Held-out study tasks."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run every Writer task under six steering conditions and write the report and blind review."""
    paths = project_paths(root)
    model = writer_model(paths)
    adapter_path = paths.root / "adapters" / "writer" / adapter_run
    if not model.ready or not (adapter_path / "adapters.safetensors").is_file():
        raise typer.BadParameter("Writer base model or adapter is not ready.")
    task_list = load_tasks(tasks if tasks.is_absolute() else paths.root / tasks)
    report = run_writer_study(paths, task_list, mlx_generator(model.path, adapter_path), lambda texts: embed_texts(paths, texts))
    report["adapter"] = adapter_run
    out = paths.root / "evals" / "study"
    (out / "writer-study.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "writer-study.md").write_text(markdown_table(report), encoding="utf-8")
    page, key = build_blind_review(report)
    (out / "blind-review.html").write_text(page, encoding="utf-8")
    key_path = paths.root / "runs" / "study" / "blind-key.json"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    console.print(markdown_table(report))


@study_app.command("blind-score")
def study_blind_score(
    choices: Path = typer.Argument(..., help="blind-choices.json downloaded from the review page."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Unblind a completed human review and record win rates."""
    paths = project_paths(root)
    key = json.loads((paths.root / "runs" / "study" / "blind-key.json").read_text(encoding="utf-8"))
    result = score_blind_review(json.loads(choices.read_text(encoding="utf-8")), key)
    (paths.root / "evals" / "study" / "blind-review-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    console.print(result)


@study_app.command("code")
def study_code(
    tasks: Path = typer.Option(Path("evals/study/code-tasks.json"), "--tasks", help="Agentic code tasks."),
    root: Path = typer.Option(Path.cwd(), "--root", help="Project directory."),
) -> None:
    """Run the agentic code study on the local 3B and 7B Coder models."""
    paths = project_paths(root)
    task_list = load_code_tasks(tasks if tasks.is_absolute() else paths.root / tasks)
    models = {}
    for name, local in (("Qwen2.5-Coder-3B", code_model(paths)), ("Qwen2.5-Coder-7B", code_7b_model(paths))):
        if not local.ready:
            raise typer.BadParameter(f"{name} is not downloaded.")
        models[name] = mlx_chat_generator(local.path)
    report = run_code_study(task_list, models)
    out = paths.root / "evals" / "study"
    (out / "code-study.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "code-study.md").write_text(code_markdown_table(report), encoding="utf-8")
    console.print(code_markdown_table(report))
