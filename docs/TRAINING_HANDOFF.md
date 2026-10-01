# Training Handoff — Verified Checkpoint

**Date:** 2026-08-12

## What is safe to use

| Specialist | Safe runtime | Status |
| --- | --- | --- |
| Writer | Local Qwen Writer base plus Writer-only retrieval | Operational default |
| Writer voice trial | `writer-voice-001` at the documented short-context limits | Candidate only; never default |
| Code | Local Qwen2.5-Coder 7B base for reviewed interactive Ask/Explain/Plan and proposed edits | Preferred Keel chat base; no autonomous writes |
| Lightweight Code | Local Qwen2.5-Coder 3B base | Retained fallback for low-resource Ask/Explain/Plan |
| Code adapters | None | Do not use for repository edits |

## Writer evidence

- Corpus: 250 approved writing works across all approved libraries.
- Default: base model plus local retrieval.
- `writer-voice-001`: passed the intended short-context operating profile and won a 2–1 blind voice comparison, but failed a longer stress condition. It remains an explicit trial, not a promoted model.

## Code evidence

| Artifact | Outcome |
| --- | --- |
| v1 dataset | 1,940 project-split source-completion examples across 63 projects. |
| v4 dataset | 1,477 patch-oriented examples, each verified at ≤1,800 rendered Qwen chat tokens. |
| Code base | 2/2 executable checks, 2/2 bounded patch checks, 1/3 controlled real-project checks. |
| `code-smoke-001` | Rejected: no improvement on real-project maintenance (1/3). |
| `code-patch-001` | Aborted: oversized training sequences discovered before completion. |
| `code-patch-002` | Aborted: token verifier bug discovered before completion. |
| `code-patch-003` | Rejected: 2/2 executable, but regressed to 1/2 bounded patch checks and remained 1/3 on real-project checks. |
| `code-v5-001` | Rejected: 2/2 executable, but regressed to 1/2 bounded patch checks and scored 0/3 on controlled real-project checks. V5 held all nine approved evaluation projects out of its 1,081/59/51 train/validation/test dataset. |
| `code-v7-001` | Rejected: 2/2 executable, but regressed to 1/2 bounded patch checks and scored 0/3 real-project checks, despite 120 independent repair-only test contracts and a smaller two-layer adapter. |
| `code-v8-001` | Rejected: 2/2 executable and preserved 2/2 bounded patch, but scored 0/3 real tasks despite 118 real historical repair episodes. |
| `code-7b-v8-001` | Rejected: it degraded the stronger unmodified 7B base from 1/2 patch and 3/3 real to 0/2 patch and 2/3 real. |

## Non-negotiables for any future training

1. Keep Writer and Code data, models, adapters, indexes, evaluations, and promotion history separate.
2. Validate formatted token length before training; never accept runtime truncation as normal.
3. A run completion produces a candidate, never an active model.
4. Evaluate against the base on executable, bounded patch, and controlled real-project tasks.
5. Reject a candidate that regresses on any safety-critical test or fails to show enough real-project value.
6. Do not modify live user repositories during evaluation; use temporary copies and store metadata, not generated code.

## Resume condition

The approved 12-task suite remains the future evaluation contract. All twelve original source/test runners are proven locally. The unmodified local 7B base is the strongest demonstrated Code chat model (3/3 real tasks) and should be attached to Keel without an adapter. Keep it review-only for writes. Do not attach any Code adapter.

Current runner qualification is recorded separately in `CODE_TASK_QUALIFICATION.md`; it must be updated whenever a task moves from discovered to executable-qualified.

## Useful commands

```bash
# From model-training
.venv/bin/pytest -q
.venv/bin/sixai context chat writer "Your writing task"
.venv/bin/sixai code chat "Explain this code task" -n 300
.venv/bin/sixai code eval-smoke
.venv/bin/sixai code eval-patch
.venv/bin/sixai code eval-real
```
