# SIXTWELVE Local AI — Implementation Log

This is the chronological, source-controlled record of implementation work in this repository. Entries state what changed, why, verification performed, and any blocker. It must never include tokens, corpus text, absolute paths to private source material, or other secrets.

## 2026-08-11 — 001: Initial repository study

**Outcome:** Established that the repository began as specifications only: the local training/context specification, master README, and macOS product specification. No implementation code was present.

**Key decision confirmed:** separate Qwen 3B-class Writer and Code adapters; behavior lives in adapters while retrieval and structured state carry current facts.

## 2026-08-11 — 002: Local credential boundary

**Outcome:** Created a project-local `.env` template, excluded `.env` from source control, and restricted the actual `.env` file to its owner.

**Verification:** token presence and expected format were checked without displaying its value.

## 2026-08-11 — 003: Implementation specification and Phase 0A scaffold

**Outcome:** Added `SIXTWELVE_TRAINING_IMPLEMENTATION_SPEC.md`, `pyproject.toml`, a Python package skeleton, a secret-safe `sixai doctor` diagnostic, bootstrap script, and initial tests.

**Boundary:** the macOS app remains the future user-facing chat/workspace. This repository is the terminal-based local training lab until a runtime bridge exists.

## 2026-08-11 — 004: Reproducible Python environment

**Outcome:** Installed Python 3.12.13 through `pyenv`, created `.venv`, and installed the project’s development dependencies.

**Decision:** Homebrew's Python 3.12 bottle was not used because its XML extension was incompatible with the installed macOS system library. The `pyenv` build passed the XML import check.

**Verification:** `.venv/bin/python --version` reports 3.12.13; `pytest` passed (2 tests); `sixai doctor --json` reports an Apple Silicon environment, supported Python, token availability only, and MLX not yet installed.

## 2026-08-11 — 005: Phase 0B Writer corpus safeguards

**Outcome:** Added a Writer-only corpus pipeline for Markdown, Markdown variants, and plain-text files. It creates normalized local copies under ignored `corpora/` storage, records a JSON manifest, and deduplicates by SHA-256 content hash.

**Review control:** every imported document begins as `unreviewed`. The terminal CLI supports `sixai corpus list writer` and an explicit `sixai corpus label writer DOCUMENT_ID gold|good|reference_only|exclude` decision. No imported item is automatically accepted as voice supervision.

**Secret control:** likely private keys, AWS/GitHub/Hugging Face/OpenAI-style tokens, and common database connection strings are quarantined before source content is copied. Reports identify only a file path and finding category, never a matched value.

**Verification:** five tests passed, covering diagnostics, normalization, idempotent duplicate handling, no-copy secret quarantine, and quality labeling. The `sixai corpus` command group exposes `import`, `list`, and `label`.

**Private-corpus status:** no user writing has been read or imported.

## Current state

Phases 0A and 0B are complete. The corpus importer is ready for a deliberately selected writings repository or folder. No model has been downloaded and no MLX package has been installed.

## 2026-08-11 — 006: Writings repository structure inspection

**Outcome:** Inspected the supplied writings repository structure without reading, copying, or importing document content. The repository is clean. It contains a mixed corpus: 962 Markdown and 666 text files, plus image, PDF, source, configuration, and workflow material.

**Import decision:** do not import the repository root. The largest area (`ia-writer`, 1,243 candidate text/Markdown files) includes active drafts and clearly mixed material. Candidate authored-writing areas also include `US-War-Essays` (53 files), `budget` (16 files), and `posts` (1 file). The user must select the intended authored corpus before import.

**Private-corpus status:** no user writing has been copied into this training repository.

## 2026-08-11 — 007: First Writer corpus import — `MD-Files/Misc`

**Outcome:** Imported the user-selected `MD-Files/Misc` folder through the Writer corpus pipeline.

**Result:** 234 unique documents imported; 2 duplicate-content files identified without a second copy; 0 documents quarantined for likely secrets; 1 unsupported file ignored.

**Safety result:** no secret finding was reported. All imported documents remain `unreviewed`; none may be used for training until the user assigns an explicit quality label.

**Next step:** inspect the corpus listing and apply `gold`, `good`, `reference_only`, or `exclude` labels. Dataset building remains blocked until this review is complete.

## 2026-08-11 — 008: Writer corpus import — remaining `MD-Files`

**Outcome:** Imported the user-selected remainder of `MD-Files` through the same Writer pipeline.

**Result:** 21 new documents imported; 237 already-imported duplicate-content files safely skipped; 0 documents quarantined for likely secrets; 9 unsupported files ignored.

**Corpus state:** the Writer corpus now holds 255 unique, normalized documents from `MD-Files`. All remain `unreviewed`; no dataset has been built.

## 2026-08-11 — 009: Writer / Developer training isolation confirmed

**Outcome:** Confirmed and documented the two-model boundary. The current corpus and all Phase 0 work are for the Writer specialist only: how the user writes, reasons, manages source/context, revises, and continues long-form work.

**Isolation rule:** the future Developer specialist will use a separate Coder base engine, adapter namespace, code-only corpus, dataset manifests, retrieval/index/state, evaluation suite, and promotion history. No prose corpus will be used to train Code behavior; no repository code will be used to train Writer behavior. Only generic pipeline utilities and domain-neutral context-management mechanics may be shared.

## 2026-08-11 — 010: Conservative Writer corpus triage

**Outcome:** Ran a local structural/content-signal review over the 255 Writer documents. The review examined only document structure and clear provenance signals; it did not infer authorship or quality from topic alone.

**Applied labels:** 3 documents were marked `exclude` because they were empty, explicitly attributed to a guest writer, or contained an assistant-style disclaimer. 2 documents were marked `reference_only` because they are a correction manifest and tool instructions, not prose supervision targets.

**Deliberate restraint:** 250 documents remain `unreviewed`. Some documents contained weak assistant-style phrasing or editorial references, but those signals are insufficient to label them automatically. No documents were marked `gold` or `good`, and no dataset may be built yet.

**Verification:** the quality manifest was read back as 3 `exclude`, 2 `reference_only`, and 250 `unreviewed`; the test suite passed (5 tests).

## 2026-08-11 — 011: Phase 0C Writer dataset and test harness

**Outcome:** On user approval, labeled the 250 remaining selected documents as provisional `good`, preserving the earlier 3 `exclude` and 2 `reference_only` decisions. Implemented a deterministic Writer dataset builder and validator.

**Dataset result:** built `datasets/writer/v1` with 250 authentic W1 voice examples: 225 train, 11 validation, and 14 test. The split is assigned by whole document hash, so an article cannot cross partitions. W4 revision examples remain at zero because no verified draft/final pair mapping has been supplied; none were fabricated.

**Validation:** checks Writer namespace, manifest/file count agreement, exact chat roles, non-empty messages, likely-secret absence, and one-source/one-example isolation. The first test run caught a validator edge case involving an empty split; it was corrected before the real dataset build. The suite then passed (6 tests), and the generated `v1` dataset validated successfully.

**User test access:** added `scripts/test.sh` and `docs/TESTING.md`. The user can run the synthetic suite plus diagnostic after every code change and validate the real dataset independently.

## 2026-08-11 — 012: Phase 0D Writer MLX runtime and base-model smoke test

**Outcome:** Installed and verified MLX 0.32.0 and MLX-LM 0.31.3 on the Apple Silicon GPU. These versions are now pinned in project metadata.

**Writer base:** downloaded `mlx-community/Qwen2.5-3B-Instruct-4bit` locally (approximately 1.6 GB) into the isolated Writer base-model directory. This is the MLX 4-bit conversion of the planned Qwen2.5 3B instruction model. No Code base model was downloaded.

**Verification:** direct local GPU inference completed successfully. Added `sixai model status writer`, `sixai model download writer`, and `sixai chat writer PROMPT`; added tests for local-model readiness. The test suite passed (8 tests).

**Boundary:** this is the unmodified Writer base model, not a trained personal model. The next training step must first export MLX-compatible dataset filenames and create a smoke-run configuration/manifest.

## 2026-08-11 — 013: First local Writer QLoRA smoke candidate

**Outcome:** Prepared and completed `writer-smoke-001`: a 10-step, local-only QLoRA run over the validated Writer dataset. It trained 4 layers with prompt masking, batch size 1, 2,048-token cap, fixed seed 42, and gradient checkpointing.

**Result:** MLX reported 1.663M trainable parameters (0.054% of the 3.086B base model) and peak memory below 5 GB during observed steps. The run produced and successfully loaded a 6,657,883-byte adapter. The run manifest records it as a non-promoted `candidate`.

**Finding:** several full-article examples exceeded the smoke cap and were truncated. This does not invalidate the smoke run; it establishes that the standard training path must generate section-sized examples before a meaningful training run.

**Verification:** adapter-backed local generation succeeded; run-manifest completion checks were added; the full test suite passed (10 tests). The chat CLI now accepts `--adapter-run writer-smoke-001` for direct base-versus-candidate comparison.

## 2026-08-11 — 014: Terminal-safe adapter option

**Outcome:** Added the short `-a` alias for `--adapter-run` after terminal input wrapped the long option into two commands. This changes only CLI ergonomics; the model and adapter are unaffected.

## 2026-08-11 — 015: First section-sized Writer candidate

**Outcome:** Rebuilt the Writer dataset as `v2`, splitting approved prose at paragraph/sentence boundaries with a 5,000-character target. The resulting 1,187 W1 examples are split by source document: 1,054 train, 58 validation, 75 test. No document crosses a split and no example was skipped.

**Training result:** completed `writer-chunked-001`, a local 100-step QLoRA candidate over `v2` with 8 trainable layers. Checkpoints were saved at steps 25, 50, 75, and 100. The final 13,315,808-byte adapter was loaded successfully for local generation and its run manifest is marked `candidate`.

**Quality gate:** no promotion decision has been made. This candidate is structurally valid and no longer suffers the previous full-article truncation warning, but it must be evaluated against fixed Writer benchmarks and blind user preference before it can become the active personal model.

**Verification:** `v2` dataset validation passed; the candidate adapter loaded for a local response; the test suite passed (11 tests).

## 2026-08-11 — 016: Context-aware Writer curriculum and candidate

**Correction applied:** the prior Writer candidates trained voice/section behavior but did not explicitly train context skills. Added a separate Writer context curriculum while retaining the architectural rule that live retrieval/state—not adapter weights—supplies current facts at runtime.

**Dataset:** built and validated `v3` with 5,894 examples split by source document: 5,252 train, 279 validation, 363 test. It contains 1,966 authentic W1 voice targets; 1,716 W3 continuation and 1,716 W9 non-repetition derived targets; 248 W5 working-state compression examples; and 248 W7 synthetic supersession examples. Every example records authentic, derived, or synthetic provenance.

**Training result:** completed `writer-context-001`, a separate local 150-step, 8-layer QLoRA candidate. Checkpoints were saved every 25 steps. The final 13,315,808-byte adapter is recorded as a non-promoted `candidate`.

**Verification:** an adapter-backed supersession prompt selected the later explicit instruction and returned the expected JSON. The test suite passed (13 tests). A blinded base-versus-candidate review package was generated for human preference evaluation.

## 2026-08-11 — 017: Blind preference result — `writer-context-001`

**User evaluation:** the user selected B for evidence, B for accountability, and a tie for power without seeing the A/B mapping.

**Resolved result:** B mapped to `writer-context-001` for both evidence and accountability. The candidate therefore won 2 prompts, the base won 0, and 1 prompt was tied.

**Decision:** record this as encouraging initial preference evidence, not a promotion. The comparison is too small and does not yet cover source discipline, long-form coherence, or real working-state/retrieval behavior.

## 2026-08-11 — 018: Local Writer retrieval and working-context layer

**Outcome:** Added a Writer-only, local lexical retrieval index and inspectable context package. It indexes approved Writer corpus documents as section-sized chunks and keeps all artifacts under the Writer namespace.

**Verification:** built the real local index with 1,981 chunks. `sixai context inspect writer QUERY` displays selected source titles, sections, and relevance scores before inference. `sixai context chat writer QUERY -a writer-context-001` supplies the same inspectable working-context package to the local candidate.

**Boundary:** this is a first lexical retrieval implementation. It is intentionally transparent but not yet semantic/hybrid ranking; its selected material must be inspected before relying on it for source-critical writing. The test suite passed (14 tests).

## 2026-08-11 — 019: Context runtime evaluation and rejection

**Outcome:** Tested `writer-context-001` with an inspectable retrieved context package. The candidate showed severe repetition. The base model with the same package remained more coherent but still received politically adjacent material instead of evidence-specific sources.

**Diagnosis:** two distinct shortcomings were exposed: the first lexical retrieval implementation lacks semantic relevance/distraction handling, and the initial derived context curriculum caused a repetition regression under runtime context.

**Decision:** rejected `writer-context-001` and recorded the rejection reason in its immutable run manifest. The adapter/checkpoints and evaluation evidence are retained for diagnosis, but it cannot be promoted. Added a tested rejection lifecycle helper; the suite passed (15 tests).

**Next engineering work:** introduce a relevance benchmark and improved hybrid/semantic retrieval before retraining context behavior; rebalance the context curriculum and require a no-repetition runtime gate.

## 2026-08-11 — 020: Retrieval relevance gate

**Outcome:** Replaced raw word-count retrieval with BM25-style scoring, exposed matched terms in the Context Inspector, and added abstention when fewer than two substantive query terms overlap a source. Expanded filtering of generic question words after inspection showed they were incorrectly inflating relevance scores.

**Verification:** added retrieval/abstention tests; the suite passed (16 tests). The real index remains local and contains 1,981 Writer chunks.

**Limit:** the result is a safer lexical baseline, not semantic retrieval. It improves transparency and avoids unrelated injection in no-match cases, but cannot reliably identify conceptual relevance. Semantic/hybrid retrieval is required before retraining the rejected context candidate.

## 2026-08-11 — 021: Local hybrid retrieval foundation

**Outcome:** Installed a local MLX embedding runtime and downloaded `mlx-community/bge-small-en-v1.5-4bit` (approximately 19 MB). A local similarity smoke test confirmed related evidence/debate phrases scored substantially higher than unrelated text.

**Implementation:** rebuilt the Writer index with 384-dimensional local embeddings for all 1,981 Writer chunks, stored alongside lexical data in the ignored local index (approximately 21 MB). Context Inspector now shows hybrid score, matched lexical terms, and semantic similarity.

**Verification:** the suite passed (16 tests); the real hybrid index built successfully and returned inspectable results. The embedding runtime is pinned as an optional retrieval dependency.

**Quality gate:** semantic similarity alone is not assumed correct. No further context-adapter training will occur until a relevance benchmark demonstrates improved source selection and an abstention/no-repetition runtime evaluation passes.

## 2026-08-11 — 022: Explicit context-runtime gates

**Outcome:** Added an inspectable repeated-5-gram gate for model output. A score above 0.10 blocks promotion pending diagnosis. The known looping pattern scores 0.714 and is correctly flagged for review; the test suite passed (19 tests).

**Retrieval gate:** added a deterministic Writer self-retrieval smoke benchmark. It asks the index to find documents from their own titles and writes a local report. The actual local index passed 10/10 checks after the benchmark was corrected to omit excluded sources (which the index correctly omits). This verifies index plumbing only; it is deliberately not represented as proof of conceptual relevance.

**Decision:** `writer-context-001` remains rejected. Before a replacement context candidate can train, the system needs human-labeled conceptual relevance cases, a passing retrieval evaluation over those cases, and a passing no-repetition runtime evaluation.

## 2026-08-11 — 023: Human-labeled relevance evaluator

**Outcome:** Added `sixai eval relevance writer`, which evaluates hybrid retrieval against explicit user judgments at top five and saves a local, inspectable report. The evaluator refuses empty labels; it cannot accidentally treat an unlabeled template as a passing benchmark.

**Review materials:** created `docs/writer-relevance-cases.json` as the machine-readable counterpart to the human review guide. Its five cases deliberately start without source IDs because conceptual relevance is a user judgment, not something the system should fabricate.

## 2026-08-11 — 024: Provisional conceptual relevance labels

**Outcome:** At the user's direction, completed the five initial relevance labels by inspecting the retrieved Writer sources and selecting direct topical matches. The labels are explicitly marked provisional and each records its rationale in `docs/writer-relevance-cases.json`; they can be reviewed or replaced without changing training data.

**Transparency:** Context Inspector now prints the stable source ID beside each selected title, eliminating the need to infer IDs from a separate corpus listing.

## 2026-08-11 — 025: Rebalanced context curriculum design

**Diagnosis applied:** v3 contained 1,966 authentic W1 examples but 3,432 derived continuation/non-repetition examples. The rejected candidate's severe looping makes that instruction-heavy balance unsafe to repeat.

**Implementation:** added the `balanced` context profile for v4. It preserves every authentic W1 example, samples continuation tasks only at deterministic intervals, retains working-state and supersession tasks, and removes W9's repeated anti-repetition wording. The replacement run is a distinct 100-step `writer-context-002`; it cannot alter v3 or its rejected adapter.

## 2026-08-11 — 026: `writer-context-002` runtime evaluation and rejection

**Training result:** built and validated Writer dataset v4 with 2,852 examples: 1,966 authentic W1, 390 sparse W3 continuation, 248 W5 working-state, and 248 W7 supersession. The local 100-step QLoRA run completed and produced a 13,315,808-byte adapter as a non-promoted candidate.

**Runtime result:** direct adapter chat worked, but the context-runtime prompt about evidence returned an empty completion while the unmodified base responded with the same retrieved package. Other context prompts produced text, demonstrating an unreliable conditional failure rather than a successful context capability.

**Decision:** reject `writer-context-002`. The runtime gate now rejects both repeated output and empty completions, so an empty response cannot be counted as a clean result. v4 artifacts are retained for diagnosis; no adapter has been promoted.

**Verification:** the expanded automated suite passed (21 tests), and the rejected status/reason was written to the run manifest after the completed adapter was verified.

## 2026-08-11 — 027: Stable Writer context runtime baseline

**Evaluation:** added a five-case context-runtime evaluator that uses the human-labeled retrieval cases, captures generation locally, and blocks empty or repeated output. The base Writer model passed 5/5. `writer-chunked-001` failed 2/5 for repetition; `writer-context-001` had already failed for severe looping; `writer-context-002` failed for an empty completion.

**Operational decision:** the current default context runtime is the unmodified local Writer base plus the local hybrid Writer retrieval index. This is a stable operational baseline, not a claim that it is personally fine-tuned. Context chat now has an explicit, announced base fallback if a selected adapter fails its runtime gate.

**Boundary preserved:** no Writer adapter was promoted, no Code asset was created or touched, and all reports contain only evaluation metadata rather than generated prose.

## 2026-08-11 — 028: Context-runtime instruction and length control

**Live check:** the base runtime passed its quality gates but answered a concise request too expansively. This is an instruction-following/ergonomics issue, not a failed retrieval or runtime gate.

**Correction:** strengthened the answer-only prompt to require the objective's requested format and length, and added `context chat --max-tokens` with a 220-token default. Users can set a tighter local bound without changing model settings or artifacts.

## 2026-08-11 — 029: Terminal-safe response-length option

**Outcome:** Added `-n` as a short alias for `--max-tokens` on both direct chat and context chat. This prevents terminal line wrapping from splitting the long option into `--max-` and a mistaken `tokens` command.

## 2026-08-11 — 030: Generic-context request abstention

**Issue found:** a live request containing the placeholder `X` had no real topic, but semantic retrieval still injected unrelated mountaineering material.

**Correction:** generic task words (such as `write`, `concise`, `paragraph`, and `one`) are now excluded from retrieval terms. If no substantive topic remains, Writer context retrieval abstains rather than inventing relevance. A regression test covers this exact placeholder case and the real semantic index was checked after the correction.

## 2026-08-11 — 031: Complete-sentence terminal output

**Issue found:** a valid short-response request reached its explicit 120-token ceiling midway through its final sentence.

**Correction:** Context Chat now preserves complete generated sentences and removes only a trailing incomplete fragment when the local token limit cuts a response short. It announces this display-only adjustment in the terminal; runtime quality evaluation continues to use the original model output.

## 2026-08-11 — 032: Complete-sentence word budget

**Issue found:** a token cap avoids unlimited generation but does not reliably produce a concise final answer; the model may use all available tokens before a sentence boundary.

**Correction:** added `context chat -w WORDS` as an optional terminal-safe final display budget. It retains whole sentences only, so a short response is both bounded and readable. The raw local model output remains available to the runtime gate before display shortening.

## 2026-08-11 — 033: Broad-question editorial discipline

**Issue found:** although the short-response budget worked, a broad question about evidence led with named political examples instead of the general claim.

**Correction:** strengthened the local context instruction: broad conceptual responses must begin with the general claim and avoid named examples unless the objective specifically calls for them. This changes only runtime prompting, not corpus data, retrieval records, or model weights.

## 2026-08-11 — 034: Full `MD-Files` library inclusion audit

**Verification:** re-imported the complete `MD-Files` root. It reported 258 known duplicates, zero new files, zero quarantine findings, and nine unsupported files ignored. This proves the full folder was already imported, not only `Misc`.

**Coverage:** the Writer corpus contains all 7 `Christian-Zionism` works and 12 trainable `Capital-Wars-NWO` works. `claude-instructions.md` and `EDITORIAL-CORRECTIONS-MANIFEST.md` remain correctly `reference_only`, never training examples. The remaining corpus is 231 `Misc` works; 3 are excluded. In total, 250 approved Writer works are eligible for training.

**Implementation:** dataset manifests now report document and example counts by original source library. A new all-library dataset version will make the coverage inspectable at build time.

**Dataset result:** built and validated `datasets/writer/v5`: 2,852 examples (2,544 train / 134 validation / 174 test), no skips. Source-library composition is 2,580 examples from `Misc`, 187 from `Capital-Wars-NWO`, and 85 from `Christian-Zionism`; every original source remains assigned to exactly one split. The next rebalanced training preparation now requires v5.

## 2026-08-11 — 035: Context ablation and controlled all-library voice candidate

**Ablation:** evaluated rejected `writer-chunked-001` over all five reviewed context tasks at 3,000, 6,000, and 9,000 retrieved-context characters. It passed 3/5 at 3,000 and only 1/5 at both 6,000 and 9,000, confirming that larger context packages worsen its repetition but do not solely cause it. No adapter status changed as a result.

**Controlled dataset/training:** built and validated `v6`, which contains 1,966 authentic W1 section examples only, drawn from all 250 approved works across `Misc`, `Capital-Wars-NWO`, and `Christian-Zionism`. Trained separate `writer-voice-001` for 50 steps with 4 layers (1.663M trainable parameters, 0.054% of the base); its adapter is 6,657,883 bytes and remains a candidate.

**Runtime evidence:** `writer-voice-001` passed 5/5 reviewed context cases at the actual terminal operating profile: 3,000 context characters and 220 output tokens. It had one repetition failure in the longer 400-token stress test, so this is a conditional operating-profile pass, not a promotion.

**Human review:** created a blinded base-versus-candidate comparison at `evals/writer/writer-voice-001-vs-base/blind-review.md`. Its private mapping remains unopened. User preference is the sole remaining input for this evaluation round.

## 2026-08-11 — 036: Blind voice result and constrained trial

**User review:** the user selected B for evidence, accountability, and power without seeing the mapping. B resolved to `writer-voice-001` for evidence and accountability, and to the base model for power.

**Resolved result:** `writer-voice-001` won 2 prompts; the base won 1; there were no ties. The preference result is saved beside the blind review package.

**Decision:** this supports a constrained short-context trial only. The candidate may be explicitly used with the validated 3,000-character / 220-token limits and automatic base fallback, but it remains unpromoted because it failed a 400-token stress case. The base remains the default runtime.

## 2026-08-11 — 037: Isolated Code-model foundation

**Architecture:** implemented a separate Code pipeline with strict repository inspection, code/config-only suffix allow-list, generated/dependency-directory exclusions, likely-secret quarantine, language composition reporting, and an independent `corpora/code` manifest. It refuses to import the training project itself and cannot read or write Writer corpus artifacts.

**Verification:** added Code isolation tests; the full suite passed (28 tests). No user code repository has been inspected or copied.

**Base model:** downloaded and verified `mlx-community/Qwen2.5-Coder-3B-Instruct-4bit` in `models/bases/code` (approximately 1.6 GB). This is a distinct local base model, not an adapter and not trained on the user's code. Added a Code-only terminal chat command for temporary local use.

## 2026-08-11 — 038: Multi-project Code workspace staging

**Discovery:** the user identified `raastey-work` as the Code workspace, excluding `writings`. A top-level size inventory found 90 non-hidden project directories, from small utilities to multi-gigabyte applications. This is a multi-project workspace, not a single import unit.

**Decision:** do not blindly import all code at once. The Code inspector now supports a default `writings` exclusion and a checkpointed, read-only ten-project workspace inventory. Each batch reports accepted source files, secret quarantines, ignored files, language composition, and Git presence before any copy occurs.

**Safety correction:** the initial broad walker was stopped after it revealed post-walk directory filtering was too slow. The code walker now prunes excluded/dependency/generated directories before descent; this changes only inspection performance, never corpus data.

## 2026-08-11 — 039: Staged `raastey-work` Code corpus import

**Inventory result:** completed all nine read-only workspace batches: 90 top-level project directories, 14,090 accepted pre-deduplication source/config files, 10 likely-secret quarantines, and one intentionally skipped training-laboratory directory. The `writings` directory was excluded from every batch.

**Import result:** imported all inspected project directories except `writings` and `model-training` into the isolated `corpora/code` namespace. Content-hash deduplication reduced the corpus to 9,788 unique files. Quarantined files were never copied. The manifest records separate Code IDs and source paths; Writer corpus, dataset, adapter, index, and model namespaces remain unchanged.

**Composition:** the imported Code corpus includes 1,902 Swift files, 1,878 Python files, 977 TypeScript/TSX files, 674 JSON files, and smaller C/C++/web/configuration groups. This diversity reinforces the need for a project-balanced Code dataset rather than raw-file training.

## 2026-08-11 — 040: User-requested pause checkpoint

**Writer state at pause:** local Writer base is ready. The approved corpus contains 250 works across `Misc` (231), `Capital-Wars-NWO` (12), and `Christian-Zionism` (7). `writer-voice-001` is a non-promoted conditional trial: it won the blind voice review 2–1 and passed 5/5 reviewed context tasks at 3,000 characters / 220 tokens, but failed one longer 400-token stress case. The base Writer plus local retrieval remains the default runtime. `writer-smoke-001` remains smoke-only; `writer-chunked-001`, `writer-context-001`, and `writer-context-002` are rejected.

**Code state at pause:** local Code base is ready. The separate Code corpus contains 9,788 deduplicated files from `raastey-work`, excluding `writings` and `model-training`; ten likely-secret files were quarantined and never copied. No Code dataset, adapter, or training run exists yet.

**Verification:** automated suite passes (30 tests). Durable state is additionally summarized in `PROJECT.md`, `DECISIONS.md`, `TASK.md`, `WRITER_RUNTIME_POLICY.md`, and `CODE_TRAINING_BOUNDARY.md`.

**Resume point:** design and build a project-balanced Code dataset plus Code-specific evaluation suite. Separately, collect focused user trial feedback for `writer-voice-001` before any Writer promotion decision.

## 2026-08-11 — 041: Plain-language project README

**Outcome:** added a short root `README.md` that explains the Writer and Code specialists, base models, adapters, training versus retrieved context, current safety status, useful terminal commands, and the documents that track decisions and progress.

**Purpose:** this is a user-facing orientation document. The implementation log remains the detailed chronological source of truth.

## 2026-08-11 — 042: Project-balanced Code dataset v1

**Dataset:** built and validated `datasets/code/v1` from the isolated Code corpus. It contains 1,940 examples across 63 projects: 1,767 train, 107 validation, and 66 test. Every project is assigned to one split only, preventing one app's files from appearing in both training and evaluation.

**Balance/safety:** the builder accepts primary source languages only, caps each project at 80 files, and skips 867 overlong files rather than truncating code mid-file. Composition is Swift-led (1,280 examples) with Python, TypeScript/TSX, Rust, JavaScript, and C/C++ coverage.

**Decision:** Code adapter training remains blocked until Code-specific evaluation tasks exist. The next work creates compile/test-aware and patch-scope evaluation fixtures rather than treating raw code completion as sufficient proof.

## 2026-08-11 — 043: Executable Code baseline evaluation

**Evaluation:** added local executable smoke fixtures for Python and Swift. The evaluator asks the Code base to generate a small self-contained function, extracts the code, runs it in a temporary directory, and stores only pass/fail metadata.

**Result:** the unmodified Code base passed 2/2 fixtures. An initial Python failure was traced to the evaluator calling a system interpreter rather than the project interpreter; the generated code itself was correct. After the harness correction, both Python and Swift checks passed. The automated suite passes (31 tests).

**Decision:** the Code base and dataset are now ready for a first non-promoting adapter preparation. Before execution, that run should have a separate run ID, bounded steps/layers, and a base-versus-candidate repeat of these executable checks.

## 2026-08-11 — 044: First isolated Code adapter candidate

**Training:** added a Code-only `sixai code train-smoke` command and trained `code-smoke-001` from the project-balanced Code v1 dataset. The run used the separate Qwen2.5-Coder 3B base, 50 local MLX LoRA steps, four adapted layers (1.663M parameters / 0.054% of the base), and created a 6,657,883-byte adapter. No Writer model, corpus, dataset, retrieval index, or adapter was read or changed.

**Evaluation:** extended `sixai code eval-smoke` to accept a Code adapter run. Both the untouched Code base and `code-smoke-001` passed the two local executable fixtures (Python and Swift, 2/2). The automated suite passes (32 tests).

**Decision:** `code-smoke-001` is a candidate only, not a default or promoted model. Tiny self-contained function checks establish that the adapter runs safely, not that it improves repository maintenance. The next stage must compare base and candidate on deterministic repository patch and test-preservation fixtures.

## 2026-08-11 — 045: Bounded Code patch-regression comparison

**Evaluation:** added `sixai code eval-patch`, a local evaluator that creates temporary small Python repositories, asks for the complete replacement of one existing file, and runs regression tests. The fixtures cover whitespace-normalizing slug creation and a threshold discount boundary. Generated source is not retained; reports contain only run metadata and pass/fail results.

**Result:** both the untouched Code base and `code-smoke-001` passed 2/2 file-replacement fixtures. The full automated suite passes (33 tests).

**Decision:** this is a useful basic safety signal, not proof that the candidate is better. The fixtures are synthetic and small. `code-smoke-001` remains unpromoted; the next evaluation must use representative, testable maintenance tasks from real projects and compare patch scope plus test preservation.

## 2026-08-11 — 046: First controlled real-project Code evaluation

**Evaluation:** added `sixai code eval-real`. It reads NauticGrid's existing `lib/operator/entry-href.ts` and its real Vitest test without changing the repository, creates a temporary controlled mutation, asks for a constrained full-file replacement, and executes the copied original test with the repository's local dependencies. Only pass/fail metadata is retained.

**Result:** both the Code base and `code-smoke-001` failed 0/1. This was not a runner failure: the base invented a route that does not exist in the test contract, and the candidate later declined to provide a replacement even when the actual test was included. The automated suite remains 33/33 passing.

**Decision:** retain `code-smoke-001` as an unpromoted diagnostic candidate and do not use it for real repository maintenance. The next round must broaden real-project evaluation and use those failures to build a more instruction- and patch-oriented Code dataset before training a second candidate.

## 2026-08-11 — 047: Commercial cross-platform application design handoff

**Product decision:** the future consumer application is direct-sold desktop software, launching on macOS but built around a Rust core so it can later ship on Windows and Linux. This supersedes the earlier Swift-only application architecture direction; it does not change the local-first training/runtime principles.

**Design deliverable:** created `docs/SIXTWELVE_CONTEXT_CROSS_PLATFORM_DESIGN_SPEC.md`, a detailed Claude Design handoff. It defines the product promise, audiences, vocabulary, trust/safety rules, Rust-core architecture boundary, app map, screen-by-screen behavior, onboarding, Writer and Developer workspaces, Context Inspector, Training Center, Learning Inbox, candidate promotion, privacy, error states, design system, anti-requirements, and prototype deliverables.

**Decision:** preserve macOS-native quality at launch while keeping platform-specific distribution and UI behavior at the shell. The Rust core owns sensitive business rules, local data, context, training orchestration, model registry, and filesystem safety. The current Code candidate remains unpromoted; this product specification does not claim it is ready for repository writes.

## 2026-08-12 — 048: Patch-oriented Code curriculum and expanded real-project gate

**Curriculum:** added a patch-oriented Code dataset profile that teaches full-file replacement, output-format discipline, public-interface preservation, and use of adjacent test contracts where available. During the first attempt, MLX reported examples beyond its 2,048-token limit. The run was intentionally stopped and retained as `code-patch-001`, rather than accepted as a candidate. A second attempt exposed a verifier bug that measured a tokenizer batch dimension rather than rendered chat tokens; it was stopped and retained as `code-patch-002`.

**Correction:** Code v4 validates the rendered local Qwen chat format with the local tokenizer before data is accepted. It contains 1,477 patch-oriented examples (1,341 train / 85 validation / 51 test), and its longest formatted conversation is 1,797 tokens, under the 1,800-token policy limit.

**Evaluation:** expanded the controlled read-only NauticGrid suite from one to three real TypeScript mutations, each run in a temporary copy with its existing Vitest contract. The Code base and `code-smoke-001` both score 1/3: they pass the confidence freshness case but fail the entry route and priority-watch cases.

## 2026-08-12 — 049: Clean patch candidate outcome and final Code decision

**Training:** `code-patch-003` trained cleanly from Code v4 for 75 bounded local steps on the separate Code model (four LoRA layers; 1.663M trainable parameters / 0.054% of base; 6,657,883-byte adapter). No Writer artifact was read or changed.

**Result:** it passed executable smoke checks 2/2, but regressed on bounded patch checks to 1/2 (the base remains 2/2) and did not improve the controlled real-project suite (1/3). It was rejected. `code-smoke-001` was also formally rejected for failing the real-project gate. No Code adapter remains active or eligible for repository writes. The full automated suite passes (36 tests).

**Decision:** stop Code adapter training at this evidence-backed checkpoint. The safe Code runtime is the untouched local base for Ask, Explain, and Plan. Resume only after a user-approved representative task set produces a new, targeted curriculum proposal.

## 2026-08-12 — 050: Model-training handoff checkpoint

**Handoff:** added `docs/TRAINING_HANDOFF.md`, which states the safe Writer and Code runtimes, corpus/dataset facts, every candidate outcome, future-training non-negotiables, and resume condition. Updated the plain README, durable project/task/decision records, and specification index so the commercial application work can proceed without ambiguity about model readiness.

**Final state:** Writer base plus retrieval is operational; `writer-voice-001` remains a limited non-default trial. Code base is operational only for assisted Ask/Explain/Plan; all Code adapters are inactive. Training artifacts, manifests, datasets, eval results, and logs remain local and reproducible.

## 2026-08-12 — 051: Proposed representative Code task contract and v5 curriculum

**Proposal:** created `docs/CODE_MAINTENANCE_TASKSET_AND_CURRICULUM.md` for explicit user approval. It defines six narrow, read-only maintenance tasks: four real NauticGrid TypeScript behavior fixes and two Swift domain-policy fixes drawn from Kineto and Tanzaku. Each task requires a one-file replacement, its existing test contract, a temporary copy, and source/test pass-fail validation. Evaluation files and projects are held out of future training.

**Curriculum:** Code v5 is proposed as test-guided maintenance episodes rather than generic source completion: 40% one-file repair with tests, 20% narrow repair without a test, 15% test addition/correction, 15% scoped planning, and 10% safety/uncertainty behavior. All examples must be project-split, token-preflighted to 1,800 rendered tokens, and generated only from source/test pairs that pass before and fail after a controlled mutation.

**Promotion gate:** a candidate must preserve 2/2 executable and 2/2 synthetic checks, pass at least 3/4 real TypeScript tasks, complete eligible Swift tasks, beat the base by two real tasks overall, introduce no regression, and pass human review. The proposal does not authorize a new run, promotion, or source-code mutation until the user approves it.

## 2026-08-12 — 052: Cross-product task-set correction and documentation reconciliation

**Correction:** after user direction, expanded the pending Code v5 proposal beyond the earlier NauticGrid-heavy draft. The current proposal has 12 one-file, test-guided tasks across Camera App, Tanzaku, Kineto, SixTwelve PhotoLab, a photo-editing app, Lumen, Dictionary, Mishkat Quran, and NauticGrid. Discovery verified existing narrow source/test contracts for camera stacking, geometry, media-domain wrapping, document integrity, reversible editing commands, Dynamic Type/accessibility, Quran reference parsing, and TypeScript policy behavior.

**Documentation:** reconciled `README.md`, `PROJECT.md`, `TASK.md`, `DECISIONS.md`, `TRAINING_HANDOFF.md`, `SIXTWELVE_CONTEXT_MASTER_README.md`, and the task/curriculum specification. They now consistently state that the 12-task suite is pending approval, that all tasks run in temporary copies and are held out of training, and that no new adapter training has begun. Removed the obsolete six-task table from the proposal to prevent two competing approval targets.

**Status:** Writer and Code runtime decisions are unchanged. Code v5 remains unbuilt and no model promotion is authorized. Automated training-laboratory tests pass (36 tests).

## 2026-08-12 — 053: Cross-product runner qualification foundation

**Discovery:** verified concrete test/build entry points across the user-identified app portfolio: Camera App, Tanzaku, Kineto, Lumen, Dictionary, SixTwelve PhotoLab, photo-editing app, and Mishkat Quran. All inspected Xcode projects expose named schemes; Mishkat’s shared domain is a standalone Swift package. No source code was changed.

**Execution:** added `docs/CODE_TASK_QUALIFICATION.md` to separate source/test discovery from executable qualification. Confirmed safe local runner paths for five tasks: NauticGrid entry routing and priority policy (existing temporary-copy Vitest fixtures), Mishkat Quran verse parsing (9 tests passed through SwiftPM), Lumen command parsing (macOS Xcode test passed), and SixTwelve PhotoLab document checksum integrity (macOS Xcode test passed). Xcode build products were directed to dedicated `/tmp` Derived Data locations.

**Decision:** only executable-qualified tasks may contribute to a future base-versus-candidate gate. The other seven portfolio tasks remain valid discovered contracts but require one safe baseline run before admission. This work does not build Code v5, train an adapter, mutate a live repository, or promote any model.

## 2026-08-12 — 054: Swift/iOS cross-product runner qualification

**Qualification:** verified the local simulator fleet and tested the proposed Swift portfolio contracts with fixed simulator IDs and temporary Derived Data. Kineto `EraMatrixTests`, Tanzaku `PreviewGeometryTests`, and Dictionary `LemmaThemeTests` passed. Together with the prior Lumen macOS, SixTwelve PhotoLab macOS, Mishkat SwiftPM, and two NauticGrid Vitest paths, eight of the twelve proposed tasks are now executable-qualified.

**Runner limitations:** Camera App `basic` and photo-editing app `whistler` schemes currently report no supported platform for their buildables when targeted at the available simulator. They are recorded as runner-blocked, not failed model tasks and not promotion credits. The photo-editing task was narrowed to `RecipeLibrary.swift` / `RecipeParityTests.swift`; no source code was changed.

**Documentation:** updated the task qualification matrix, curriculum proposal, and current task record with executable-qualified versus runner-blocked status. No Code v5 dataset, adapter training, source mutation, or model promotion occurred.

## 2026-08-12 — 055: Ten-task executable qualification checkpoint

**Qualification:** selected and ran the remaining safe one-file contracts: Lumen `HistoryTimeline` undo/redo branch safety and Mishkat Quran `PlaybackState` repeat-count policy. Both passed in their real local test runners. The cross-product suite now has ten executable-qualified contracts spanning Tanzaku, Kineto, SixTwelve PhotoLab, Lumen, Dictionary, Mishkat Quran, and NauticGrid.

**Blocked scope:** Camera App `StackPolicyTests` and photo-editing app `RecipeParityTests` remain runner-blocked because their current shared Xcode schemes report no supported platform for their buildables on the available simulator. This is recorded as a test-configuration limitation, not a model result. They cannot be used for training, candidate scoring, or promotion until their runners are safely repairable.

**Status:** task/source/test paths, passed runner commands, and exact blocked state are updated in `CODE_TASK_QUALIFICATION.md`, the curriculum proposal, current task record, and implementation log. No Code v5 data, adapter, source mutation, or promotion was created.

## 2026-08-12 — 056: Full cross-product runner qualification

**Correction:** the Camera App and photo-editing Xcode commands emitted `IDERunDestination` platform warnings, but that warning was non-fatal. Inspection of their actual Xcode result bundles proves that the selected `StackPolicyTests` passed 2 tests and `RecipeParityTests` passed 1 test on the fixed iOS simulator. The warning therefore does not make either task runner-blocked.

**Qualification:** all 12 proposed task contracts now have demonstrated local executable paths. The matrix includes exact source/test pairs, safe commands, and the distinction between test-runner qualification and future controlled-mutation validation. No repository source file was changed; Xcode build products stayed under dedicated `/tmp` Derived Data paths.

**Status:** the Code v5 suite is fully executable-qualified but remains pending explicit user approval. The next permitted training action, after approval, is a temporary-copy task manifest and controlled-mutation validation—not adapter training directly.

## 2026-08-12 — 057: Approved task manifest foundation

**Authorization:** the user explicitly approved the cross-product 12-task Code v5 suite and curriculum. This authorizes local fixture construction and one bounded, unpromoted candidate after the safety gates are met. It does not authorize live repository changes, automatic model promotion, or autonomous code writes.

**Implementation:** added `trainer/code_tasks.py` and `sixai code task-manifest-build` / `task-manifest-validate`. Built `reports/code/task-manifests/v5-approved-001.json`, which validates 12 runner-qualified tasks across nine project directories. Each record contains task/runner metadata and SHA-256 fingerprints for its selected source and test only; source/test contents and model-generated code are deliberately absent.

**Verification:** corrected the photo-editing source path to `whistler/Processing/Recipes/RecipeLibrary.swift` in both task specifications. Automated training-laboratory tests pass 37/37. No user application source, dataset v5, adapter, or promotion changed.

## 2026-08-12 — 058: Disposable task-workspace runner

**Implementation:** added `temporary_task_workspace` in `trainer/code_tasks.py`. It copies exactly one approved project to a fresh system temporary directory, excludes build/dependency artifacts, optionally replaces exactly one uniquely matched line, and deletes the copy on exit. Task paths are checked to remain within their declared project.

**Safety verification:** a regression test creates a sample project, mutates only the temporary copy, and proves the original source remains byte-for-byte unchanged. The training-laboratory suite now passes 38/38. This is runner infrastructure only: no production source, controlled fixture result, dataset v5, adapter, or promotion has changed.

## 2026-08-12 — 059: Held-out Code v5 candidate and rejection

**Dataset:** built and validated `datasets/code/v5` as a Code-only, patch-oriented dataset with 1,081 train, 59 validation, and 51 test examples across 51 non-evaluation projects. Camera App, Tanzaku, Kineto, SixTwelve PhotoLab, photo editing, Lumen, Dictionary, Mishkat Quran, and NauticGrid were explicitly held out. No Writer artifact was read or changed.

**Candidate:** completed the approved bounded 50-step, four-layer local MLX LoRA run `code-v5-001`. Its adapter is 6,657,883 bytes and is retained locally as a rejected audit artifact only. It is neither selected by the CLI nor permitted for repository work.

**Evaluation and decision:** `code-v5-001` passed 2/2 self-contained smoke checks but only 1/2 bounded patch checks and 0/3 controlled NauticGrid real-project checks. Re-run base evidence was 2/2 smoke, 2/2 patch, and 1/3 real. The candidate therefore regressed and was formally rejected. The Code base remains the sole safe Ask/Explain/Plan runtime.

**Boundary:** the approved cross-product task manifest and disposable copy runner remain in place, but exact original-pass/mutation-fail fixtures are still required before any future training iteration. No user application source, Code promotion, or autonomous write occurred.

## 2026-08-12 — 060: Code v5 regression diagnosis and guardrail

**Verified diagnosis:** inspection of the V5 manifest found 5 discovered source/test-contract examples among 1,191 total examples. V5 safely held out all evaluation projects, but its training material was overwhelmingly generic full-file imitation rather than the approved test-guided repair curriculum. Its outcome—smoke preserved but bounded and real repairs worse than base—is consistent with that mismatch; the causal explanation remains a testable hypothesis, not an asserted fact.

**Guardrail:** `build_code_dataset` and `sixai code dataset-build` now accept `--minimum-test-contract-examples`. Dataset construction fails if its measured contract-bearing example count is below the requested floor, preventing another generic dataset from being relabeled as repair training. Regression coverage confirms the failure behavior.

**Decision:** `code-v5-001` remains rejected. No further adapter run is allowed until exact controlled mutations run in disposable copies and a new held-out dataset meets a meaningful, documented test-contract minimum.

## 2026-08-12 — 061: Clean-corpus and test-pairing correction

**Discovery:** the legacy Code corpus included SwiftPM dependency material under `.build/checkouts`; that directory was absent from the original Code exclusion list. This makes such material unsuitable for the user's Code specialist even when it is not a secret.

**Implementation:** excluded `.build` and `checkouts` during future imports and defensively at dataset-build time for existing corpora. Expanded test discovery to recognize Swift `FooTests.swift`, TypeScript `foo.test.ts`/`foo.spec.ts`, and Python `test_foo.py` conventions within the same project and language. Added regression coverage for both policies; laboratory tests pass 42/42.

**Result:** clean `datasets/code/v6` has 1,010 train, 59 validation, and 41 test examples (1,110 total), with all nine approved evaluation projects held out and 44 verified attached test contracts. This is a material improvement from V5's 5 contracts, but it is still not repair-first enough to justify another candidate; V6 remains untrained.

## 2026-08-12 — 062: Repair-first V7 experiment and final 3B decision

**Curriculum:** created `datasets/code/v7`, a separate repair-only curriculum with 120 independent, token-validated Python boundary-repair episodes. Every example contains a deliberately broken complete source file, its complete test contract, and the complete fixed replacement. It contains no source or test artifact from any approved held-out evaluation task. The dataset validates at 96 train, 12 validation, and 12 test examples; all 120 are test-contract examples.

**Candidate:** trained `code-v7-001` for 30 low-learning-rate steps with a deliberately smaller two-layer LoRA (3,328,949 bytes), reducing the chance that the general Code base behavior would be overwritten. It completed locally and remained unpromoted.

**Evaluation and decision:** V7 passed 2/2 smoke checks but scored 1/2 bounded patch checks and 0/3 controlled real-project tasks—again worse than the base's 2/2, 2/2, and 1/3. It was formally rejected. This independently tests the earlier V5 data-quality hypothesis: test-guided synthetic repair behavior alone did not transfer to the user's real Swift/TypeScript repairs at this model size.

**Final state:** Writer remains unchanged. For Code, the local Qwen2.5-Coder 3B base remains the only permitted Ask/Explain/Plan runtime. All adapters (`code-smoke-001`, `code-patch-003`, `code-v5-001`, and `code-v7-001`) are inactive/rejected. Further 3B adapter training is paused; the justified next path is a larger base-model benchmark or a substantial corpus of verified real-project repair episodes. No live user source or product app was changed.

## 2026-08-12 — 063: Real Git-history repair curriculum

**Extraction:** added a local Git-history repair extractor. It reads before/after source snapshots and changed test snapshots from the user's non-evaluation repositories, never alters a Git checkout, and excludes every approved evaluation project. The resulting V8 dataset has 118 token-safe, real repair episodes across 12 projects, with project-level splits (105 train, 1 validation, 12 test) to prevent leakage.

**3B result:** `code-v8-001` preserved 2/2 bounded patch checks—an improvement over V5/V7—but scored 0/3 real held-out repairs. It is rejected. Real history improved general patch discipline but could not make 3B solve the target TypeScript repairs.

## 2026-08-12 — 064: Larger Code-base benchmark and Keel selection

**Benchmark:** downloaded the separate local `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` base (about 4 GB) without replacing the 3B base. Under the identical evaluation functions, the unmodified 7B passed 2/2 smoke, 1/2 bounded patch, and all 3/3 real NauticGrid controlled repairs. The 3B base passes 2/2, 2/2, and 1/3 respectively.

**Adapter result:** a minimal 20-step, two-layer real-history adapter (`code-7b-v8-001`) degraded 7B to 0/2 patch and 2/3 real; it is rejected. This confirms Keel should load the stronger 7B base directly, without a Code adapter.

**Final Code runtime:** use the 7B base for reviewed interactive chat, explanations, plans, and proposed diffs. Keep all Code writes user-reviewed; the one missed bounded whitespace repair means it is not authorized for autonomous edits. All Code adapters remain inactive/rejected. Training-laboratory tests pass 48/48.

## Next entry

Attach the unmodified 7B Code base to Keel for reviewed interactive assistance. Keep Writer and Code separate, all Code adapters detached, and repository writes explicitly user-reviewed.

## 2026-08-12 — 065: Keel local-model product integration

Connected the separate `keel-app` Rust/Tauri product to this training laboratory through a new local SIXTWELVE MLX engine contract. Keel now discovers the lab automatically, provisions separate Writer and Code 7B engines, routes Writer projects through approved-corpus retrieval, routes Developer projects through the unmodified 7B Code base, and exposes read-only chat in both product spaces. The Code CLI now selects the preferred 7B base by default while retaining an explicit 3B fallback.

Verified the boundary with all 48 training tests, Keel formatting/lint/unit checks, and live local inference through both Writer retrieval and Code 7B. No adapter was activated, no model weights were copied into Keel, and repository writes remain gated by reviewed scope, file list, diff, apply choice, test command, and result summary.
