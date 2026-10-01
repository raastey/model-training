# SIXTWELVE Local AI — Training Implementation Specification

**Status:** implementation plan v0.1  
**Scope:** local Writer training path first, then a shared foundation for Developer training  
**Reference hardware:** Apple Silicon, 32 GB unified memory  
**Training backend:** MLX + MLX-LM, isolated behind project interfaces

## Product boundary

This repository is the local AI laboratory: it prepares corpora, trains/evaluates adapters, manages local model artifacts, and exposes a developer-oriented terminal CLI. It is **not** the end-user chat product.

The separate SIXTWELVE macOS app specified in `SIXTWELVE_CONTEXT_MAC_PRODUCT_SPEC.md` is the eventual chat and workspace interface. Until its runtime bridge exists, model download, training, evaluation, and direct model interaction happen through `sixai` terminal commands in this repository. The future app should call a stable local runtime API/daemon rather than replicate training logic in Swift.

## 1. Outcome and boundaries

The first working vertical slice must take a small, user-selected Writer corpus through:

```text
import → normalize → inspect → curate → build JSONL → validate → split → smoke train → evaluate → register candidate
```

The first slice proves the pipeline; it must not claim that a candidate is ready for promotion. All original user material stays local. A LoRA adapter teaches behavior and voice; searchable source material and a later context engine supply current facts.

The initial base engine is `Qwen/Qwen2.5-3B-Instruct`, accessed only after the user explicitly starts the download. The Developer engine will later use `Qwen/Qwen2.5-Coder-3B-Instruct` through the same interfaces.

### Writer / Developer isolation rule

The product trains two distinct specialists, never a blended personal adapter:

| Boundary | Writer | Developer |
| --- | --- | --- |
| Base engine | Qwen2.5 3B Instruct-class | Qwen2.5 Coder 3B Instruct-class |
| Adapter | `sixtwelve-writer-*` only | `sixtwelve-code-*` only |
| Corpus | User-authored prose, revisions, outlines, and explicitly permitted research context | User-selected repositories, commits, tests, architecture records, and locally exported issue/PR material |
| Behavioral targets | Voice, argument construction, editorial judgment, source discipline, context continuation | Architecture/style fit, file selection, patch scope, tests, technical-decision continuation |
| Retrieval/state | Writer documents and article state | Repository symbols/files and project state |
| Evaluation | Voice, revision, long-form/context benchmarks | Build/tests, patch correctness, scope/style/context benchmarks |

Shared utilities may implement generic concepts such as content hashing, provenance, secret scanning, manifests, retrieval interfaces, and structured working-state schemas. They must retain a `space` namespace and cannot mix Writer and Developer examples, artifacts, scores, or promotion decisions. A future Code import command is a separate Phase 2 deliverable, with stricter repository exclusions and its own secret scan.

## 2. Implementation decisions

| Concern | V0.1 decision |
| --- | --- |
| Python | 3.12, in a project-local `.venv`; do not use the installed Python 3.14 until MLX compatibility is verified. |
| Packages | `mlx`, `mlx-lm`, `pydantic`, `typer`, `rich`, `pytest`; exact versions are frozen after the smoke run. |
| Source storage | Read-only input paths are copied into a content-addressed local corpus only when import is explicitly requested. |
| Dataset format | JSONL chat records plus per-record provenance metadata in a separate manifest. |
| Splits | Whole-document allocation: 85% train, 7.5% validation, 7.5% test. Related draft/revision variants never cross splits. |
| Evaluation | Fixed Gold set is separate from all train/validation/test data and is never passed to MLX-LM training. |
| Secrets | Hugging Face token is read from `.env` at runtime and never written to manifests, logs, reports, commands, or source control. |
| Adapter lifecycle | A run produces a candidate only. Promotion needs recorded automated checks and a blind human comparison. |

## 3. Repository layout

```text
model-training/
├── docs/                         # Product and implementation specifications
├── trainer/                      # Python package: pure pipeline logic
│   ├── cli.py                    # `sixai` command entry point
│   ├── config.py                 # Paths and environment configuration
│   ├── domain.py                 # Typed records/manifests
│   ├── corpus.py                 # Writer import and normalization
│   ├── dataset.py                # Example building/split/validation
│   ├── runs.py                   # Immutable run manifests
│   └── training.py               # MLX-LM command boundary (Phase 0 stub)
├── scripts/                      # Safe local setup and diagnostics
├── tests/                        # Unit tests with synthetic fixtures only
├── datasets/                     # Generated, ignored local artifacts
├── corpora/                      # Imported private material, ignored
├── models/                       # Downloaded bases, ignored
├── adapters/                     # Candidate/promoted adapters, ignored
├── evals/                        # Local evaluation fixtures/results, ignored
├── reports/                      # Run reports, ignored
└── runs/                         # Immutable manifests/logs, ignored
```

Only code, test fixtures with invented text, configuration templates, and documentation belong in version control. Every other directory is local/private.

## 4. Data contracts

### 4.1 Corpus document

Each accepted source becomes a `CorpusDocument` with `id`, `source_path`, SHA-256 `content_hash`, title, timestamps when known, type, status, quality label, relationships, and normalized UTF-8 body. Imports are idempotent by hash.

Quality labels are `gold`, `good`, `reference_only`, and `exclude`. Only `gold` and `good` may become voice-supervision targets. Import never changes the source file.

### 4.2 Training example

Examples are chat-template records with a stable identifier and separate metadata:

```json
{"messages":[{"role":"system","content":"…"},{"role":"user","content":"…"},{"role":"assistant","content":"…"}]}
```

The paired metadata contains `id`, class (`W1`–`W10`), provenance (`authentic`, `derived`, or `synthetic`), source IDs, quality, review status, split, and generator version. The model-specific template is applied only at train time, after validation.

### 4.3 Manifests

`dataset-manifest.json` records source hashes, example IDs/hashes, split assignment, builder version, and validation output. `run-manifest.json` records base model/revision, dataset manifest hash, adapter configuration, environment, MLX versions, metrics, status, and parent run. Manifests are append-only after a run begins.

## 5. Writer vertical slice

1. **Environment diagnostic:** detect Apple Silicon, disk space, Python version, MLX importability, and free memory. No model download.
2. **Corpus import:** accept a deliberately chosen small folder of Markdown/plain-text writing; record metadata and hash. DOCX/PDF support comes only after their parsers have tests.
3. **Curation:** user marks representative pieces `gold` or `good`; no automatic voice claim from unreviewed prose.
4. **Example builder:** first implement W1 voice generation and W4 draft→revision pairs. W5 compression, W6 relevance, and W7 supersession follow before any standard run.
5. **Validator:** check JSON schema, roles, no empty targets, source provenance, duplicate hash, split integrity, and forbidden secret patterns.
6. **Baseline evaluation:** run the fixed prompts against the base engine and store outputs for blind comparison.
7. **Smoke training:** run only a tiny reviewed dataset against a verified local model. Capture command, versions, config, logs, checkpoint, and candidate manifest.
8. **Candidate evaluation:** compare base and adapter using W1/W4 and context tasks; reject on degradation or leakage concerns.

## 6. CLI contract

The CLI is deliberately thin; business logic remains importable and testable.

```bash
sixai doctor
sixai corpus import writer PATH
sixai corpus list writer
sixai dataset build writer
sixai dataset validate writer
sixai model download writer             # explicit network action
sixai chat writer                       # direct local model interaction during development
sixai train writer --profile smoke      # refuses if validation fails
sixai eval writer --candidate RUN_ID
sixai run show RUN_ID
```

Every command supports `--json` for automation. Mutating commands require explicit paths/IDs and print artifacts produced. Training and download commands never print `HF_TOKEN`.

## 7. Safety gates

- Refuse an import path containing an obvious excluded directory (`.git`, `node_modules`, build outputs) until code-space support exists.
- Scan normalized material and generated examples for likely secrets before writing a dataset; quarantine flagged records and report only paths/record IDs.
- Refuse training if split leakage, unreviewed target prose, invalid chat structure, or a missing Gold-set declaration is found.
- Refuse promotion unless required benchmark results and blind review are recorded.
- Preserve raw inputs; regeneration deletes only a user-selected generated output directory.

## 8. Evaluation design

The first Gold set contains hand-curated prompts that have no source overlap with training: voice continuation, revision preference, source-grounded paragraph, compression with constraints, superseded-instruction selection, and no-repeat continuation. Score each candidate with structured rubrics and blind preference labels. For every task, retain prompt ID, source IDs, output, model/adaptor ID, latency, token count where available, and evaluator decision.

## 9. Phased implementation order

| Phase | Deliverable | Completion evidence |
| --- | --- | --- |
| 0A | Scaffold, private artifact boundaries, diagnostics | `sixai doctor` and unit tests pass without MLX/model. |
| 0B | Corpus manifest/import, quality labeling, secret scan | Synthetic import tests and idempotency tests pass. |
| 0C | W1/W4 builder, validator, whole-document splitter | Valid JSONL and manifest generated from fixtures. |
| 0D | Verified Qwen download and MLX-LM smoke run | Reproducible candidate manifest and checkpoint exist. |
| 1 | Writer context curriculum and evaluation suite | Candidate exceeds base on predeclared evaluation criteria. |
| 2 | Code corpus/indexing/dataset path | Repo filtering and patch evaluation work independently. |
| 3 | Shared retrieval/state/context budgeter | Context Inspector explains every selected item. |

## 10. Immediate work

Phase 0A creates the package skeleton, private artifact rules, project metadata, environment template, a safe `doctor` command, and tests. Phase 0B adds a Writer-only Markdown/plain-text importer: it normalizes a private corpus copy, deduplicates by content hash, defaults every document to `unreviewed`, supports explicit human quality labels, and quarantines likely secrets before any content is stored. It intentionally does not download a model or ingest private writing until the user selects a source repository.
