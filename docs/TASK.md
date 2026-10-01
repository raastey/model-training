# TASK

Task
Finalize the verified Code model selection for Keel and preserve the adapter investigation evidence.

Phase
Handoff — unmodified 7B Code base selected for reviewed interactive use

Scope

- In: evidence preservation and Keel-ready base-model selection.
- Out: live-source changes, Code adapter activation, autonomous repository writes, or commercial application implementation.

Constraints

- All evaluation remains local and stores only fixture metadata/results, not source-code artifacts.
- No Code adapter is active or promoted; all candidates through `code-7b-v8-001` are rejected.
- Writer and Code namespaces remain strictly separate.

Relevant sources

- `trainer/code.py`: isolated corpus and project-split dataset.
- `docs/CODE_MAINTENANCE_TASKSET_AND_CURRICULUM.md`: proposed task contract and v5 curriculum.
- `trainer/code_evaluation.py`: executable Code evaluation harness.
- `trainer/code_tasks.py`: approved metadata-only task manifest builder.
- `trainer/cli.py`: Code training and evaluation commands.

Verified state

- Writer default and Code base-only runtime remain unchanged.
- Twelve proposed tasks span Camera App, Tanzaku, Kineto, SixTwelve PhotoLab, a photo-editing app, Lumen, Dictionary, Mishkat Quran, and NauticGrid.
- The user approved the 12-task suite and Code v5 curriculum on 2026-08-12.
- All 12 tasks are executable-qualified. The Camera App and photo-editing schemes emit a non-fatal platform warning, but their selected tests passed in their Xcode result bundles.
- `reports/code/task-manifests/v5-approved-001.json` validates 12 task records across nine projects and contains only metadata/hashes.
- `temporary_task_workspace` copies one project to a disposable system directory and permits at most one exact-line controlled mutation; a regression test confirms the live project is unchanged.
- Code v5 contains 1,081/59/51 train/validation/test examples with all nine approved evaluation projects held out.
- `code-v5-001` completed but is rejected: 2/2 smoke, 1/2 patch, 0/3 existing real-project checks; base scored 2/2, 2/2, 1/3.
- Verified diagnosis: only 5 of V5's 1,191 examples carried a discovered test contract. This was insufficient for the approved test-guided repair curriculum.
- Verified corpus correction: the legacy corpus admitted SwiftPM `.build/checkouts` dependency code. It is now excluded at import and dataset-build time; clean V6 contains 44 test-contract examples in 1,110 total examples and is not authorized for training yet.
- `code-v7-001` used 120 independent repair-only contracts with a smaller 2-layer adapter and was also rejected: 2/2 smoke, 1/2 patch, 0/3 real.
- Unmodified Qwen2.5-Coder 7B passed 2/2 smoke, 1/2 patch, and 3/3 held-out real repairs; its real-history adapter regressed to 0/2 patch and 2/3 real and is rejected.

Open questions / hypotheses

- Hypothesis: test-guided maintenance episodes plus explicit output-mode/scope examples will improve contract-following more than generic source completion.

Acceptance criteria

- A future controlled mutation runs only in a disposable project copy and is proven to fail its original selected test before it can influence training or promotion.
- Evaluation source/test content and generated model code are never retained in reports.

Status / next action

Completed on 2026-08-12: Keel discovers this lab, provisions separate Writer-retrieval and Code 7B engines, routes by project space, and exposes read-only chat in both spaces. All Code adapters remain detached and all file writes remain behind user review.
