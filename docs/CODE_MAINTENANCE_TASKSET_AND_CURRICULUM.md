# Code Maintenance Task Set and Curriculum Proposal

**Status:** approved on 2026-08-12 — fixture construction and one bounded candidate are authorized; promotion remains unauthorized

**Checkpoint:** `code-v5-001` completed as the one authorized bounded candidate and was rejected on 2026-08-12. Although V5 held all nine evaluation projects out, it scored 2/2 smoke, 1/2 bounded patch, and 0/3 existing real-project checks (the base: 2/2, 2/2, 1/3). Do not train another candidate until the approved temporary-copy fixtures have exact original-pass/mutation-fail evidence.

**Final 3B checkpoint:** a subsequent narrower `code-v7-001` experiment used 120 independent, token-validated, test-guided repair episodes and a smaller two-layer LoRA. It also scored 2/2 smoke, 1/2 patch, and 0/3 real. Both candidates are rejected. The next improvement path is not another 3B iteration: it requires either a separately benchmarked larger Code base or a substantial body of verified real-project controlled-repair episodes.

**Purpose:** define the real work a future Code Personal Model must prove it can do, and define the curriculum required to teach that behavior.

## Outcome we want

The future Code model should help with small, testable maintenance changes in the user's existing projects. It must read the relevant source and tests, preserve public interfaces, make a narrow patch, and run or preserve tests. It is not being trained to autonomously redesign projects or deploy code.

## Boundaries

- All evaluation uses a temporary copy. Live repositories remain read-only.
- Generated model code is not stored in evaluation reports.
- Writer artifacts are not read or changed.
- Evaluation tasks are never used as training examples.
- Every task has a known-good source, controlled mutation, real existing test, expected scope, and explicit pass/fail result.
- A future adapter remains a candidate unless it beats the Code base under the promotion rule below.

## Revised representative evaluation suite

The earlier draft over-weighted one TypeScript web project. This revised suite deliberately represents the user's actual app portfolio: camera behavior, photography/editing, dictionary accessibility, Quran domain correctness, and TypeScript product logic.

The final suite uses **12 tasks in six product families**. Each is a narrow controlled mutation against an existing test contract. All 12 original test contracts now have a demonstrated local runner path; controlled mutations still must be proven individually before a task becomes a promotion gate.

| Family | Tasks | What the model must demonstrate |
| --- | --- | --- |
| Camera apps | 2 | Preserve exposure/capture thresholds, optical/camera geometry, and boundary conditions. |
| Photo/video apps | 3 | Preserve reversible editing, document integrity, and finite-domain media rules. |
| Lumen | 2 | Preserve local editing command parsing and non-destructive history behavior. |
| Dictionary | 1 | Preserve Dynamic Type/accessibility scale behavior without changing design tokens outside scope. |
| Mishkat Quran | 2 | Preserve exact canonical reference parsing and identifier boundaries. |
| NauticGrid | 2 | Preserve existing TypeScript behavioral contracts and test-guided one-file repairs. |

### Task matrix

| ID | Product/language | Existing source and contract | Controlled maintenance behavior | Allowed patch scope |
| --- | --- | --- | --- | --- |
| CAM-01 | Camera App / Swift | `basic/Models/Ladders.swift` · `basicTests/StackPolicyTests.swift` | Restore the underexposure threshold and reject invalid/non-negative readings. | `Ladders.swift` only |
| CAM-02 | Tanzaku / Swift | `Tanzaku/Domain/PreviewGeometry.swift` · `TanzakuTests/GeometryPolicyTests.swift` | Restore front-camera mirror behavior while preserving rear-camera behavior and safe geometry. | `PreviewGeometry.swift` only |
| PHOTO-01 | Kineto / Swift | `Kineto/Domain/EraMatrix.swift` · `KinetoTests/EraMatrixTests.swift` | Restore negative/overflow wrapping while preserving IDs, formats, and valid index bounds. | `EraMatrix.swift` only |
| PHOTO-02 | SixTwelve PhotoLab / Swift | `Sources/PLCore/PLDocument.swift` · `Tests/DocumentModelTests.swift` | Preserve deterministic document encoding/checksum or legacy migration behavior. | `PLDocument.swift` only |
| PHOTO-03 | Photo editing app / Swift | `whistler/Processing/Recipes/RecipeLibrary.swift` · `whistlerTests/RecipeParityTests.swift` | Preserve photo recipe/lookup behavior under its existing test contract. | `RecipeLibrary.swift` only |
| LUMEN-01 | Lumen / Swift | `Lumen/Services/CommandPlanner.swift` · `LumenTests/LumenTests.swift` | Restore signed numeric exposure/temperature/saturation command parsing. | `CommandPlanner.swift` only |
| LUMEN-02 | Lumen / Swift | `Lumen/Model/HistoryTimeline.swift` · `LumenTests/LumenTests.swift` | Preserve undo/redo branch dropping and reversible-edit state. | `HistoryTimeline.swift` only |
| DICT-01 | Dictionary / Swift | `DictionaryApp/Theme/LemmaTheme.swift` · `DictionaryAppTests/LemmaThemeTests.swift` | Restore Dynamic Type monotonic scaling or accessible token behavior without broad UI edits. | `LemmaTheme.swift` only |
| QURAN-01 | Mishkat Quran / Swift | `QuranDomain/Identifiers/VerseReference.swift` · `QuranDomainTests/VerseReferenceTests.swift` | Restore colon/dot/range parsing and reject malformed/reversed references. | `VerseReference.swift` only |
| QURAN-02 | Mishkat Quran / Swift | `QuranDomain/Audio/PlaybackState.swift` · `QuranDomainTests/RepeatSettingsTests.swift` | Preserve canonical value bounds/defaults from existing package tests. | `PlaybackState.swift` only |
| NG-01 | NauticGrid / TypeScript | `lib/operator/entry-href.ts` · `lib/operator/entry-href.test.ts` | Restore signed-out routing while preserving entitled and upgrade paths. | `entry-href.ts` only |
| NG-03 | NauticGrid / TypeScript | `lib/operator/priority.ts` · `lib/operator/priority.test.ts` | Restore commercial-watch priority behavior. | `priority.ts` only |

### Why this is representative

- It reflects the projects you actually highlighted: camera apps, Lumen, SixTwelve PhotoLab, Dictionary, Mishkat Quran, and photo apps—not just a web dashboard.
- It samples the maintenance behavior that recurs in these products: numerical thresholds, parser correctness, finite-state/index safety, reversible non-destructive editing, persistence compatibility, accessibility, and policy preservation.
- It remains deliberately one-file and test-guided. A small local model must reliably do this before it is trusted with multi-file features, UI redesigns, data migrations, or repository writes.
- It includes both Swift and TypeScript, but the portfolio is Swift-led because that is where the camera/photo/dictionary/Quran products live.

### Verified source evidence

- Camera App `StackPolicyTests` covers underexposure threshold, non-negative values, and `NaN` behavior.
- Tanzaku `GeometryPolicyTests` covers front/rear camera policy and focus geometry.
- Kineto `EraMatrixTests` covers wrapping, identity format, bounds, and domain policy.
- Lumen tests cover command-parser numeric amounts, crop/rotation dimensions, and history behavior.
- SixTwelve PhotoLab tests cover byte-stable document round trips, legacy migration, checksum stability, artifacts, and non-destructive behavior.
- Dictionary tests cover contrast and Dynamic Type scale behavior.
- Mishkat Quran package tests cover canonical verse parsing, range/order rejection, and identifier bounds.
- NauticGrid has existing controlled temporary-copy fixtures; the current Code base scores 1/3 across the first three narrow mutations.

Every task now has a one-time demonstrated local test-runner path. A future temporary-copy runner must still prove the original source/test passes and each controlled mutation fails before the task can contribute promotion credit. It is never represented as a simulated pass.

The live qualification state and exact safe runner commands are recorded in `docs/CODE_TASK_QUALIFICATION.md`. All twelve tasks are executable-qualified across Camera App, Tanzaku, Kineto, SixTwelve PhotoLab, photo editing, Lumen, Dictionary, Mishkat Quran, and NauticGrid. Only executable-qualified tasks may count toward a promotion gate.

## Task format

For every fixture, the model receives:

1. a plain-language maintenance objective;
2. the complete mutated source file;
3. the complete existing test file;
4. a scope contract: “return only the complete replacement contents of this file; preserve exported/public names and types”; and
5. no hidden extra files.

The evaluator checks:

1. output is a replacement file, not commentary or a plan;
2. patch does not introduce imports outside the original dependency boundary unless the test contract requires one;
3. the original test passes in a temporary copy;
4. the live project was not changed;
5. the response is within an output-size ceiling;
6. the model does not refuse, claim the broken file is correct, or invent product behavior contradicted by the supplied test.

## Promotion gate

No candidate is promoted unless all conditions are met:

| Gate | Required result |
| --- | --- |
| Executable basics | At least 2/2 Python/Swift smoke tasks; no regression from base. |
| Synthetic patch discipline | At least 2/2 bounded patch fixtures; no regression from base. |
| Real cross-product maintenance | At least 8/12 passed after runner qualification, with at least one passing task in Camera, Photo, Lumen, Quran/Dictionary, and TypeScript product logic. |
| Family coverage | No more than one family may be entirely deferred; a deferred family blocks promotion if it contains the user's current primary work. |
| Comparison | Candidate must exceed base by at least three real tasks overall and introduce no regression in any previously passing gate. |
| Human review | User reviews at least three real task outputs/diffs blindly or side by side and confirms the candidate is more useful. |

An adapter that ties the base is not useful enough to promote. An adapter that regresses on a safety-critical test is rejected.

## Targeted curriculum — Code v5

The current source-completion and generic replacement datasets were insufficient because they did not reliably teach the model to obey a concrete existing test contract. Code v5 will train **maintenance episodes**, not merely code completions.

### Training example categories

| Category | Target share | What it teaches |
| --- | ---: | --- |
| Test-guided one-file repair | 40% | Read failing/behavioral tests; return only a replacement file; preserve API. |
| Narrow bug repair without a test file | 20% | Obey an explicit behavioral objective and minimal patch scope. |
| Test addition or correction | 15% | Add a small test only when asked, with source and test paths explicit. |
| Plan and file-scope selection | 15% | Identify files to inspect/change, explain why, and state what must not change. These outputs are never applied automatically. |
| Refusal/safety and uncertainty | 10% | Say that supplied context is insufficient, avoid guessing routes/API, ask for the missing file/test, and never claim a broken implementation is correct. |

### Format discipline

Every repair example has this structure:

```text
System: You are SIXTWELVE Code. Follow the requested output format exactly.
User: Objective + patch contract + complete source + complete test(s).
Assistant: Complete replacement source file only.
```

Plan examples are explicitly labeled `Mode: Plan` and return structured text, never code. This prevents the model from mixing explanations into a required code-only replacement.

### Data construction rules

1. Build episodes from source/test pairs in the Code corpus, but hold every evaluation project/file out of training.
2. Create controlled mutations mechanically from known source lines only when the original test fails and the original source passes.
3. Keep a source-to-test mapping manifest with project, language, target path, test path, mutation type, and split.
4. Split by project, not by file. Hold out all of NauticGrid, Kineto, and Tanzaku from the v5 training set if they are evaluation projects.
5. Cap rendered local-Qwen chat length at 1,800 tokens before training. Store exact tokenizer/model revision and length metadata.
6. Exclude generated files, dependencies, secrets, test snapshots with private content, migrations, minified code, and files that cannot be validated.
7. Preserve original material and store only local, reviewed derived examples.
8. Balance languages by episode count: approximately 45% TypeScript/TSX, 35% Swift, 10% Python, 10% other supported languages, subject to sufficient valid pairs.

### Training configuration proposal

- Base: existing separate local Qwen2.5-Coder 3B 4-bit MLX model.
- Adapter: Code-only LoRA; four layers; separate v5 run ID.
- First candidate: 50 steps at low learning rate, then evaluate. Do not increase steps or layers until quality evidence says why.
- Sequence limit: 2,048 runtime maximum; 1,800 preflight maximum.
- All runs: immutable dataset manifest hash, source/test pair counts, token-length distribution, MLX config, adapter size, and exact evaluation report.

## Implementation sequence after approval

1. Run the baseline tests for all 12 tasks in read-only temporary workspaces.
2. Build the v5 pair manifest and hold out all evaluation projects.
3. Generate/validate controlled repair episodes; reject any episode whose original source does not pass its test or whose mutation does not fail it.
4. Build and validate Code v5 with token preflight and project-level splits.
5. Train one bounded candidate.
6. Compare base vs candidate on all gates.
7. Record candidate, reject, or (only if every gate passes) offer human review for promotion.

## Explicit non-goals for this round

- multi-file feature work;
- framework migrations;
- UI redesigns;
- database migrations;
- deployment/configuration changes;
- autonomous repository writes;
- training on evaluation tasks;
- promotion based only on loss, smoke tests, or style preference.

## Approval statement

Approval received on 2026-08-12: **use the cross-product 12-task suite and Code v5 curriculum above to create new local evaluation fixtures and one bounded, unpromoted Code candidate.**

It does not authorize changes to live repositories, promotion, deployment, or new external services.
