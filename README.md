# SIXTWELVE local model training

**Results:** [STUDY.md](STUDY.md) measures prompt engineering, retrieval, and LoRA fine-tuning on the same 3B model, and an agentic test-feedback loop on 3B and 7B code models.

This folder trains and tests two private local AI specialists:

| Specialist | Purpose | Current state |
| --- | --- | --- |
| Writer | Learn your writing voice; use your writing as optional local context. | Base model works. `writer-voice-001` is a limited trial, not promoted. |
| Code | Learn patterns from your code projects. | Base model works; two experimental adapters are rejected and inactive. |

## The simple mental model

The **base model** is the large general-purpose AI.

An **adapter** is a small add-on trained locally to adjust how that base model behaves. It does not replace the base model.

Your files play two different roles:

- **Training data** teaches longer-term style and behavior.
- **Retrieved context** gives the model relevant local material for one answer. It is inspectable and can change without retraining.

Nothing in this project sends your writing or code to a remote model.

## Where we stand

### Writer

- Local base: Qwen2.5 3B Instruct.
- Approved writing: 250 works from `Misc`, `Capital-Wars-NWO`, and `Christian-Zionism`.
- Default safe use: base model plus local Writer retrieval.
- Trial adapter: `writer-voice-001` won the blind voice review 2–1 and works at short limits, but it still has one long-response failure. It is deliberately **not promoted**.

Safe default Writer command:

```bash
.venv/bin/sixai context chat writer "Your specific writing task"
```

Optional limited trial:

```bash
.venv/bin/sixai context chat writer "Your specific writing task" -a writer-voice-001 --context-budget 3000 -n 220
```

If the trial adapter fails, the command automatically uses the stable base model instead.

### Code

- Local base: Qwen2.5-Coder 3B Instruct.
- Private Code corpus: 9,788 deduplicated files from `raastey-work`.
- Excluded: `writings`, the `model-training` laboratory, generated/dependency folders, and ten likely-secret files.
- Balanced dataset v1: 1,940 examples from 63 projects, with project-level train/validation/test splits.
- `code-smoke-001` and `code-patch-003` are both rejected and inactive. They remain stored only as reproducible evidence.
- The base passes Python/Swift executable checks (2/2), bounded file-replacement checks (2/2), and the expanded real-project suite at 1/3.
- `code-patch-003` passed executable checks (2/2) but regressed on bounded file replacement (1/2) and did not improve real-project maintenance (1/3). It is not fit for repository use.
- Safe Code use today: base Engine for Ask, Explain, and Plan. Do not use a Code adapter to apply repository changes.

Try the untouched Code base:

```bash
.venv/bin/sixai code chat "Write a Swift function that reverses a string." -n 120
```

Run the base executable check:

```bash
.venv/bin/sixai code eval-smoke
```

Run the local file-replacement regression fixtures:

```bash
.venv/bin/sixai code eval-patch
```

Run the controlled real-project test (it reads NauticGrid but never edits it):

```bash
.venv/bin/sixai code eval-real
```

## Safety rules

- Writer and Code never share corpora, datasets, adapters, models, or evaluations.
- Secret-looking files are quarantined instead of copied.
- No candidate becomes active just because training completed.
- Tests and human review decide whether a candidate advances.

## Important files

- `docs/IMPLEMENTATION_LOG.md` — chronological record of every material step.
- `docs/PROJECT.md` — permanent project rules.
- `docs/DECISIONS.md` — major choices and why they were made.
- `docs/TASK.md` — current next task.
- `docs/WRITER_RUNTIME_POLICY.md` — which Writer model is safe to use now.
- `docs/CODE_TRAINING_BOUNDARY.md` — Code isolation and import rules.

## Testing

From this folder:

```bash
bash scripts/test.sh
```

Or run only the automated suite:

```bash
.venv/bin/pytest -q
```

At the current checkpoint, the suite has 36 passing tests.
