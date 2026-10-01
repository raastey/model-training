# SIXTWELVE Local AI — Training & Context Model Specification

**Status:** v1.0 implementation specification  
**Target machine:** Apple Silicon Mac, initial reference hardware M1 Pro / 32 GB unified memory  
**Initial model family:** Qwen  
**Primary runtime/training stack:** MLX + MLX-LM  
**Distribution of this component:** Local/private; no user corpus is required to leave the Mac  
**Primary models:** `sixtwelve-writer-3b` and `sixtwelve-code-3b`

---

## 1. Executive Summary

This project creates two small, local specialist language models that learn both **domain behavior** and **context-management behavior**:

1. **SIXTWELVE Writer** — learns the user's writing voice, editorial preferences, long-form argument construction, source discipline, revision behavior, and how to manage large bodies of research and prior draft context.
2. **SIXTWELVE Code** — learns the user's coding conventions, architectural preferences, implementation style, testing behavior, repo-navigation habits, and how to determine which code/project context matters for a requested change.

The product must not treat model weights as a database. The trained adapters teach **how to behave**. A separate local context system supplies **what is currently true**.

The core formula is:

```text
BASE MODEL
+ PERSONAL LoRA ADAPTER
+ LIVE CONTEXT ENGINE
+ RETRIEVAL
+ WORKING STATE
= PERSONAL SPECIALIST
```

The first production training target is Qwen2.5-class 3B models because MLX-LM's documented LoRA/QLoRA path explicitly supports the Qwen2 family. The model abstraction must permit future migration to newer Qwen models after compatibility and quality validation.

---

## 2. Goals

### 2.1 Writer goals

The Writer model must learn to:

- Produce prose that resembles the user's actual writing rather than generic assistant prose.
- Preserve sentence rhythm, vocabulary preferences, tone, argument construction, openings, transitions, evidence handling, and conclusions.
- Work from notes, research packets, source excerpts, outlines, and previous article sections.
- Maintain a thesis across long-form work.
- Avoid repeating arguments already made.
- Distinguish active instructions from superseded instructions.
- Compress historical context without dropping key constraints.
- Identify the most relevant source material for a section.
- Continue a document coherently from its current state.
- Revise drafts using learned editorial behavior.
- Produce articles in the 1,500–3,500+ word range through planned multi-section generation.

### 2.2 Code goals

The Code model must learn to:

- Follow the user's architecture and code-organization conventions.
- Prefer small maintainable modules over monoliths.
- Infer relevant files for a task.
- Respect project-level constraints and previous technical decisions.
- Generate code consistent with the project's existing language/framework style.
- Use current repository retrieval instead of relying on stale memorized code.
- Avoid modifying unrelated code.
- Generate/update tests where appropriate.
- Keep a compact representation of current implementation state.
- Understand superseded vs active architectural decisions.
- Produce useful plans and patches from a deliberately constructed context package.

### 2.3 Context goals shared by both models

Both specialist models must be explicitly trained to:

- **Select:** identify relevant information inside noisy context.
- **Compress:** reduce old state while preserving decisions, constraints, entities, dependencies, and unresolved work.
- **Prioritize:** distinguish critical constraints from background information.
- **Resolve:** prefer newer explicit decisions over superseded ones.
- **Continue:** use working state to continue a task without restarting.
- **Avoid duplication:** recognize what has already been completed or argued.
- **Retrieve:** formulate useful retrieval requests when context is incomplete.
- **Attribute:** retain provenance/source identity for facts when the task depends on sources.
- **Budget:** work within a bounded context/token budget instead of demanding that every available token be injected.

---

## 3. Non-Goals

Version 1 is not intended to:

- Train a foundation model from scratch.
- Permanently encode every article, source, repository file, or conversation into weights.
- Replace live repository indexing or document retrieval.
- Create a universal frontier model.
- Perform autonomous code deployment without explicit user control.
- Upload private training corpora to a third-party training service.
- Fine-tune continuously after every keystroke.
- Guarantee that a 3B model can reason like a frontier cloud model.

---

## 4. Initial Model Selection

### 4.1 Writer

**Preferred v1 base:** `Qwen/Qwen2.5-3B-Instruct` or a verified MLX 4-bit conversion.

Purpose:

- General instruction following.
- Writing and transformation.
- Context-management fine-tuning.
- Long-form section generation.

### 4.2 Code

**Preferred v1 base:** `Qwen/Qwen2.5-Coder-3B-Instruct` or a verified MLX 4-bit conversion.

Purpose:

- Code generation and understanding.
- Architecture/style specialization.
- Repository-context selection.
- Patch planning and implementation.

### 4.3 Quantization

Initial inference/training experiments should use a **4-bit quantized MLX build** where supported. The system must also retain the ability to train against a higher-precision base if evaluation demonstrates meaningful quality advantages.

### 4.4 Model abstraction

Never hard-code product logic to a Qwen class name.

```swift
protocol LocalModelProvider {
    var id: String { get }
    var displayName: String { get }
    var contextWindow: Int { get }
    func prepare() async throws
    func generate(_ request: GenerationRequest) async throws -> GenerationResult
    func tokenize(_ text: String) async throws -> TokenStats
}
```

Training should likewise use a backend abstraction:

```text
TrainingBackend
├── MLXLMBackend
├── FutureMLXBackend
└── FutureExternalLocalBackend
```

This prevents Qwen from becoming a product-level dependency.

---

## 5. Local Development Environment

Recommended repository:

```text
sixtwelve-local-ai/
├── README.md
├── pyproject.toml
├── .python-version
├── scripts/
├── trainer/
├── context/
├── datasets/
├── evals/
├── models/
├── adapters/
├── corpora/
├── reports/
└── tests/
```

Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -U mlx mlx-lm
```

The repository must pin known-good versions after the first successful training run. Do not leave production training dependent on unconstrained `latest` versions.

Record:

```text
python version
macOS version
MLX version
MLX-LM version
model repo + revision/commit hash
training configuration
adapter format version
dataset manifest hash
```

Every trained adapter must be reproducible from this metadata.

---

## 6. Local Data Layout

```text
~/Library/Application Support/SIXTWELVE AI/
├── Models/
│   ├── Bases/
│   └── Adapters/
├── Corpora/
│   ├── Writer/
│   └── Code/
├── Context/
│   ├── Indexes/
│   ├── State/
│   └── Graph/
├── Datasets/
│   ├── Writer/
│   └── Code/
├── Evals/
├── TrainingRuns/
├── Logs/
└── Backups/
```

Raw user material and generated training examples must be stored separately. Destructive dataset regeneration must never touch originals.

---

## 7. Writer Corpus Ingestion

### 7.1 Accepted sources

- `.txt`
- `.md`
- `.docx` via local parser
- `.pdf` where text extraction is reliable
- exported blog/newsletter archives
- drafts
- final published versions
- research notes
- outline files
- revision histories when available

### 7.2 Writer metadata

Each imported document should become a canonical record:

```json
{
  "id": "doc_uuid",
  "title": "...",
  "created_at": "...",
  "published_at": "...",
  "type": "article|essay|newsletter|note|draft",
  "status": "draft|final|published",
  "word_count": 0,
  "topics": [],
  "source_path": "...",
  "content_hash": "...",
  "quality": "gold|good|exclude",
  "relationships": []
}
```

### 7.3 Quality filtering

The user must be able to classify material:

- **Gold** — strongly representative; highest training weight.
- **Good** — representative; normal training weight.
- **Reference only** — searchable but not used as style supervision.
- **Exclude** — ignored by both training and retrieval when appropriate.

Avoid training on:

- material written primarily by another person;
- AI-generated text that the user did not substantially edit;
- duplicated publications;
- boilerplate;
- quoted source material mistaken for user prose;
- low-quality early drafts unless used specifically as draft→revision examples.

---

## 8. Code Corpus Ingestion

### 8.1 Accepted sources

- local Git repositories
- selected Git history
- README/spec/design docs
- source files
- tests
- migration files
- architecture decision records
- issue/PR text if locally exported/available

### 8.2 Default exclusions

Always exclude unless explicitly enabled:

```text
.git/
node_modules/
Pods/
DerivedData/
build/
dist/
.next/
.vendor/
vendor/
*.min.js
*.map
binary assets
model weights
third-party vendored libraries
secrets
.env*
credentials
certificates
```

### 8.3 Secret detection

Before dataset generation, scan for:

- API keys
- access tokens
- private keys
- passwords
- connection strings
- signed URLs
- credentials embedded in test fixtures

Any suspected secret must be removed from generated training material and flagged locally.

### 8.4 Code quality weighting

Repository content should be classified:

- canonical/current architecture
- current but ordinary
- legacy
- deprecated
- generated
- third-party
- experimental

Only canonical/current code should be heavily represented in behavioral training.

---

## 9. Dataset Design — The Most Important Component

Training must not consist of dumping raw files into the trainer. Build supervised examples that teach desired transformations.

The canonical chat record is:

```json
{"messages":[
  {"role":"system","content":"..."},
  {"role":"user","content":"..."},
  {"role":"assistant","content":"..."}
]}
```

Exact chat template must match the selected base model.

### 9.1 Writer dataset classes

#### W1 — Voice generation

Input: topic/notes/outline.  
Target: authentic user prose.

#### W2 — Research → prose

Input: selected source excerpts and goal.  
Target: paragraph/section authored by user.

#### W3 — Continuation

Input: article thesis + previous sections + next section objective.  
Target: next authentic section.

#### W4 — Rewrite/revision

Input: previous draft.  
Target: user's revised/final text.

#### W5 — Compression

Input: long project/article state.  
Target: concise state preserving all active constraints and unresolved items.

#### W6 — Relevance selection

Input: mixed relevant/irrelevant source fragments.  
Target: selected evidence with rationale or a compact context package.

#### W7 — Supersession

Input: old instruction + later changed instruction + discussion.  
Target: correct current instruction set.

#### W8 — Long-form planning

Input: research + objective.  
Target: thesis, argument map, section sequence, dependencies.

#### W9 — Non-repetition

Input: previously completed sections + goal.  
Target: next section that advances rather than repeats.

#### W10 — Provenance discipline

Input: labeled sources.  
Target: claims tied to sources and explicit uncertainty when evidence is absent.

### 9.2 Code dataset classes

#### C1 — Architecture continuation

Input: relevant architecture summary + request.  
Target: implementation approach consistent with project.

#### C2 — Relevant-file selection

Input: repo manifest + task.  
Target: minimal set of files to inspect.

#### C3 — Patch generation

Input: task + current relevant files.  
Target: actual accepted patch/code.

#### C4 — Refactoring

Input: prior implementation.  
Target: user's later improved implementation.

#### C5 — Bug-fix trajectory

Input: failing test/error + relevant code.  
Target: accepted fix.

#### C6 — Context compression

Input: lengthy development history.  
Target: current technical state.

#### C7 — Constraint retention

Input: project requirements + code.  
Target: patch respecting explicit constraints.

#### C8 — Superseded architecture

Input: old design + new ADR + codebase.  
Target: current architecture representation.

#### C9 — Test behavior

Input: feature/fix.  
Target: implementation plus tests matching house style.

#### C10 — Scope discipline

Input: narrowly scoped task + large repo context.  
Target: minimal correct change with no unrelated rewrites.

---

## 10. Synthetic Training Data Policy

Synthetic examples can be useful for explicit context skills, but must not pollute voice supervision.

Rules:

1. Authentic user writing always wins over synthetic prose.
2. Synthetic context-management inputs may be created around authentic targets.
3. Never label machine-generated prose as authentic user prose.
4. Maintain `provenance` metadata for every training example.
5. Provide a UI filter for `authentic`, `derived`, and `synthetic` examples.

Suggested record metadata:

```json
{
  "id":"...",
  "class":"W6",
  "provenance":"authentic|derived|synthetic",
  "source_ids":["..."],
  "quality":0.0,
  "generator_version":"...",
  "reviewed":true
}
```

---

## 11. Train / Validation / Test Split

A strict holdout policy is mandatory.

Recommended starting split:

```text
Train       85%
Validation   7.5%
Test         7.5%
```

Do **not** split chunks from the same article/repository feature across train and test. Split by whole logical unit to prevent leakage.

Examples:

- Entire article belongs to only one split.
- Related draft/final pairs belong to one split.
- A code feature and its related patch/tests belong to one split.

Create a permanent **Gold Evaluation Set** that is never used for training.

---

## 12. Context Management Representation

The surrounding context engine should construct a normalized working-state object.

```json
{
  "objective":"...",
  "active_constraints":[],
  "decisions":[],
  "superseded":[],
  "entities":[],
  "completed":[],
  "unresolved":[],
  "relevant_sources":[],
  "relevant_files":[],
  "claims_already_made":[],
  "retrieval_needed":[],
  "next_action":"..."
}
```

This structure is both a runtime object and a training target.

The model should learn to produce/update this state, but application code is responsible for storing, versioning, indexing, and validating it.

---

## 13. Context Engine Architecture

```text
RAW SOURCES
    │
    ├── conversations
    ├── documents
    ├── article drafts
    ├── research
    ├── repositories
    ├── commits
    └── project specs
          │
          ▼
      INGESTION
          │
          ▼
   NORMALIZATION
          │
     ┌────┴────┐
     ▼         ▼
  SEARCH     STATE
  INDEX      STORE
     │         │
     └────┬────┘
          ▼
 CONTEXT PLANNER
          │
          ▼
 TOKEN BUDGETER
          │
          ▼
 CONTEXT PACKAGE
          │
          ▼
  PERSONAL MODEL
```

### 13.1 Memory tiers

**L0 — Current request**  
The user's immediate instruction.

**L1 — Session context**  
Recent turns and current working material.

**L2 — Working state**  
Compressed, structured representation of the current project/document.

**L3 — Retrieval memory**  
Indexed documents, code, prior articles, decisions, history.

**L4 — Behavioral memory**  
LoRA adapter: durable patterns for writing/coding/context behavior.

Never use L4 as a replacement for L3.

---

## 14. Context Budgeting

The application must reserve the model context window deliberately.

For a generic budget `C`:

```text
System/instructions        5–10%
Working state              5–10%
Retrieved context         25–45%
Recent interaction         5–15%
Current source/draft      15–30%
Generation reserve        15–30%
```

Exact percentages are adaptive.

A context package should be scored by:

```text
relevance
recency
authority
constraint importance
novelty
source quality
redundancy penalty
token cost
```

A simple initial score:

```text
score = relevance × authority × importance × recencyFactor - redundancyPenalty
```

Do not make this formula a permanent product assumption; evaluate alternatives.

---

## 15. Retrieval

V1 requirements:

- chunking aware of document/code structure;
- local embeddings where practical;
- full-text fallback;
- metadata filters;
- source/path provenance;
- hybrid ranking;
- deduplication;
- recency and canonical-state weighting.

Writer chunks should prefer semantic boundaries such as paragraphs/sections.

Code chunks should prefer:

- symbol
- type
- function
- extension
- file
- test case
- architecture document section

Avoid arbitrary token slicing where structural parsing is possible.

---

## 16. Training Pipeline

```text
RAW CORPUS
   ↓
INGEST
   ↓
NORMALIZE
   ↓
DEDUPE
   ↓
FILTER
   ↓
CLASSIFY QUALITY
   ↓
BUILD TRAINING EXAMPLES
   ↓
VALIDATE FORMAT
   ↓
SPLIT
   ↓
BASELINE EVAL
   ↓
LoRA / QLoRA
   ↓
CHECKPOINT EVAL
   ↓
HUMAN/USER BLIND EVAL
   ↓
PROMOTE or REJECT
   ↓
VERSION ADAPTER
```

Every step must be resumable and deterministic where practical.

---

## 17. Training Runs

Do not hard-code hyperparameters in this specification as permanent defaults. Provide profiles and record all values.

Suggested experimental profiles:

### Smoke

Purpose: verify dataset/template/training path.

- very small sample
- low iteration count
- no promotion

### Standard

Purpose: first meaningful adapter.

- full curated dataset
- validation enabled
- periodic checkpoints
- periodic evaluation

### Context-heavy

Purpose: improve context-management tasks.

- higher proportion of W5–W10 or C2/C6–C10 examples
- long-context examples where memory permits

### Voice-heavy

Purpose: test stronger style specialization.

- higher proportion of authentic Gold writing
- lower synthetic proportion

Training must produce a run manifest:

```json
{
  "run_id":"...",
  "base_model":"...",
  "base_revision":"...",
  "dataset_manifest":"...",
  "adapter_config":{},
  "hyperparameters":{},
  "started_at":"...",
  "completed_at":"...",
  "machine":{},
  "metrics":{},
  "status":"candidate|rejected|promoted"
}
```

---

## 18. When Training Stops

A run stops when one or more of the following occurs:

- validation performance stops improving for the configured patience interval;
- validation loss worsens while training loss continues downward;
- Gold evaluation quality degrades;
- voice imitation becomes exaggerated/caricatured;
- repetition increases;
- context-retention score degrades;
- factual/source discipline worsens;
- code regression rate increases;
- memory/thermal limits are exceeded.

**More steps are not automatically better.**

Retain the best checkpoint, not simply the final checkpoint.

---

## 19. Evaluation Framework

### 19.1 Writer scores

Each candidate adapter is evaluated for:

- voice similarity
- naturalness
- sentence rhythm
- vocabulary fit
- argument structure
- thesis retention
- evidence discipline
- transition quality
- non-repetition
- long-form consistency
- context selection
- context compression
- superseded-instruction handling
- source attribution
- hallucination rate

### 19.2 Code scores

- task completion
- correctness/tests
- compilation/build success
- architectural fit
- file selection precision
- scope discipline
- coding-style fit
- regression rate
- context compression
- constraint retention
- relevant-context recall

### 19.3 Context benchmark

Build at least these benchmark families:

1. Needle-in-noise constraint retention.
2. Multiple conflicting decisions with a clear latest decision.
3. 20K+ token material → compact working state.
4. Relevant-source selection from distractors.
5. Long article continuation without duplicated claims.
6. Repo task requiring only 3–5 relevant files out of hundreds.
7. Previous failed attempts that must not be repeated.
8. Entity consistency across long contexts.
9. Provenance retention.
10. Missing-context detection: model should ask/retrieve rather than invent.

### 19.4 Blind comparison

Candidate outputs should be presented without version labels where possible:

```text
A
B
C
```

User chooses preferred result. Promotion should combine automated metrics and preference evaluation.

---

## 20. Continual Learning

The system supports indefinite improvement, but **not continuous live training**.

### Runtime immediacy

New work enters retrieval immediately.

```text
NEW ARTICLE/COMMIT
      │
      ├──> searchable/indexed now
      │
      └──> training inbox later
```

### Consolidation

When enough high-quality new work accumulates:

```text
active adapter
    +
curated incremental dataset
    ↓
new candidate adapter
    ↓
evaluation
    ↓
promote/reject
```

Recommended trigger is quality/novelty based, not calendar-only.

Examples:

- 10–30 substantial new writing pieces;
- a meaningful new project or architectural shift;
- a large set of reviewed code changes;
- meaningful changes in editorial behavior.

Never automatically promote a newly trained model.

---

## 21. Adapter Versioning

```text
sixtwelve-writer-v1
sixtwelve-writer-v2
sixtwelve-writer-v3

sixtwelve-code-v1
sixtwelve-code-v2
sixtwelve-code-v3
```

Each adapter version stores:

- base model ID + exact revision
- dataset manifest/hash
- training config
- eval results
- parent adapter/run
- creation date
- release notes
- compatible runtime range

Provide one-click rollback.

---

## 22. Adapter Strategy

V1 should retain **separate Writer and Code adapters**.

Do not merge them into one personality adapter prematurely.

Both can share context-management behavior through shared dataset-generation code, but examples should remain domain-aware.

Potential future layout:

```text
Base Qwen
├── Writer adapter
├── Code adapter
├── Research adapter
└── Organization adapter
```

If runtime hot-swapping becomes robust, a common base can reduce storage and memory overhead.

---

## 23. Long-Form Article Generation

Do not rely on a single 3,500-word completion.

Use an article controller:

```text
RESEARCH
   ↓
THESIS
   ↓
ARGUMENT MAP
   ↓
OUTLINE
   ↓
ARTICLE STATE
   ↓
SECTION BRIEF
   ↓
MODEL GENERATION
   ↓
STATE UPDATE
   ↓
NEXT SECTION
   ↓
GLOBAL COHERENCE PASS
```

Article state contains:

```json
{
  "thesis":"...",
  "sections_complete":[],
  "claims_made":[],
  "evidence_used":[],
  "entities":{},
  "open_threads":[],
  "do_not_repeat":[],
  "planned_conclusion":"..."
}
```

This is how a small model produces coherent long-form output without pretending the weights themselves are a long-term memory system.

---

## 24. Coding Agent Runtime

The Code model should not receive the entire repository.

```text
TASK
  ↓
REPO MAP
  ↓
FILE/SYMBOL RETRIEVAL
  ↓
CONTEXT PLANNER
  ↓
3–N RELEVANT FILES
  ↓
CODE MODEL
  ↓
PATCH
  ↓
BUILD/TEST
  ↓
RESULT + STATE UPDATE
```

V1 agent permissions should be explicit:

- read project
- propose patch
- apply patch
- run approved local commands
- never publish/push/deploy unless the host application explicitly implements and requests it

---

## 25. Privacy and Security

Core promises:

- training is local;
- inference is local by default;
- original files remain user-controlled;
- app records exactly what content is used for training;
- all generated datasets are inspectable/deletable;
- models/adapters are deletable;
- no silent telemetry containing user content;
- no secret should enter a code training dataset;
- network access for model download is distinct from corpus processing.

A future optional cloud feature must never silently change these guarantees.

---

## 26. Observability

Training logs should include:

- run progress
- train loss
- validation loss
- memory usage
- tokens/examples processed
- checkpoint path
- evaluation results
- errors

Runtime context debugging should expose an optional **Context Inspector**:

```text
Why was this included?
Why was this excluded?
Which source supplied this fact?
Which constraint has highest priority?
What was compressed?
```

This is important both as a developer tool and a commercial differentiator.

---

## 27. CLI for Development

Illustrative product-owned CLI:

```bash
sixai model download writer
sixai corpus import writer ~/Writing
sixai corpus import code ~/Developer/MyApp
sixai dataset build writer
sixai dataset validate writer
sixai train writer --profile standard
sixai eval writer --candidate <run-id>
sixai model promote writer <run-id>
sixai chat writer
sixai context inspect <session-id>
```

The CLI wraps MLX-LM. Users of the finished Mac app should not need to know MLX commands.

---

## 28. Acceptance Criteria — Training V1

Writer v1 is shippable internally when:

- complete local import→dataset→train→eval→promote pipeline works;
- no source material must leave the Mac;
- Gold test set remains isolated;
- candidate model beats base model on user-preference voice evaluation;
- context benchmark shows measurable improvement on at least selection, compression, continuation, and supersession;
- 3,500-word article workflow completes using section orchestration without severe repetition;
- adapter can be rolled back.

Code v1 is shippable internally when:

- repo import/secret filtering works;
- code dataset generation excludes vendor/build content;
- relevant-file benchmark materially beats naive whole-repo/random retrieval;
- candidate adapter improves project-style fit over base;
- test/build loop can evaluate generated patches;
- context state persists across multi-step coding work;
- adapter can be rolled back.

---

## 29. Development Phases

### Phase 0 — Reproducible MLX lab

- verify model load/inference;
- verify LoRA/QLoRA against selected Qwen2.5 bases;
- freeze environment versions;
- build smoke dataset.

### Phase 1 — Writer pipeline

- corpus ingestion;
- quality labeling;
- dataset builder;
- writer context benchmark;
- first adapter;
- article controller.

### Phase 2 — Code pipeline

- repo ingestion;
- secret/vendor filtering;
- symbol-aware indexing;
- code dataset builder;
- first adapter;
- patch/test harness.

### Phase 3 — Shared context engine

- state schema;
- retrieval;
- token budgeting;
- compression;
- provenance;
- Context Inspector.

### Phase 4 — Continual learning

- training inbox;
- incremental dataset generation;
- candidate comparison;
- promotion/rollback.

### Phase 5 — Product integration

- daemon/runtime API;
- macOS app bridge;
- model/adapters manager;
- local permissions;
- UI status/events.

---

## 30. Decisions That Must Remain Flexible

Do not prematurely freeze:

- exact Qwen generation;
- quantization level;
- embedding model;
- vector database implementation;
- LoRA rank/alpha/dropout;
- context chunk size;
- context scoring weights;
- training cadence;
- number of adapters;

These must be benchmark-driven.

---

## 31. Core Engineering Principle

The system should be designed around this distinction:

> **Fine-tuning changes how the model behaves. Retrieval and state tell it what is currently true.**

The strongest version of this product is not the model with the most memorized material. It is the smallest model that has learned the right behavior and is continuously supplied with the smallest sufficient context for the task.

