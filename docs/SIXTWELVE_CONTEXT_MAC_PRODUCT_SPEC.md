# SIXTWELVE Context — macOS Product Specification

**Status:** v1.0 product/design/engineering specification  
**Platform:** macOS, Apple Silicon  
**Distribution:** Direct download only; no Mac App Store build in v1  
**Signing:** Apple Developer ID  
**Release:** Apple notarized  
**Business model:** Paid professional software with optional free evaluation/onboarding tier  
**Core promise:** A private local AI that learns how you work and becomes exceptionally good at carrying context forward.

---

## 1. Product Thesis

Most AI tools have extraordinary general knowledge but weak continuity with an individual user's work. They repeatedly reconstruct context, lose prior decisions, over-ingest irrelevant files, and treat long-term history as either chat logs or a naive vector database.

**SIXTWELVE Context** is a native macOS AI workspace that combines:

- local specialist models;
- personal fine-tuning;
- durable project memory;
- context selection and compression;
- local document/repository retrieval;
- model versioning;
- transparent context inspection.

The product is not sold as a Qwen front end and not sold as “chat with your documents.”

### Primary positioning

> **AI that remembers how you work.**

Supporting message:

> Your work. Your context. Your model. On your Mac.

---

## 2. Target Customer

### Initial audience

Professional Mac users with a meaningful body of digital work:

- writers and journalists;
- software developers;
- researchers;
- founders;
- analysts;
- designers/product people;
- consultants;
- independent creators.

### Ideal early adopter

Someone who:

- already works heavily on a Mac;
- has years of documents/repos/projects;
- cares about privacy/IP;
- dislikes repeatedly re-explaining project context to AI;
- values consistent personal style and working conventions;
- can benefit from local Apple Silicon compute.

---

## 3. Product Principles

1. **Native, not web-in-a-box.** Swift/SwiftUI + selective AppKit.
2. **Local first.** User corpus remains local by default.
3. **Context before tokens.** Better selection beats larger indiscriminate prompts.
4. **Inspectable intelligence.** Users can see why context was selected.
5. **Model agnostic at the product boundary.** Qwen is v1, not the brand.
6. **No AI theater.** Avoid glowing brains, gradients everywhere, “magic” claims, and synthetic sci-fi UI.
7. **Professional Mac ergonomics.** Keyboard-first, drag-and-drop, excellent typography, native menus, undo where applicable.
8. **User-controlled learning.** Training never silently modifies the active model.
9. **Version everything.** Context state and model adapters can be inspected/rolled back.
10. **Direct-sale freedom.** Architecture is not constrained by Mac App Store sandboxing or review requirements.

---

## 4. Product Vocabulary

Use understandable product language.

| Technical term | Product language |
|---|---|
| Base model | Engine |
| LoRA adapter | Personal Model / Learning Layer |
| Fine-tuning | Learn / Training |
| RAG | Library / Project Memory |
| Vector index | Search Index |
| Context package | Working Context |
| Checkpoint | Model Version |
| Eval | Quality Check |

Advanced settings can reveal technical terminology.

---

## 5. Core Objects

```text
Context App
├── Spaces
│   ├── Writing Space
│   ├── Code Space
│   └── Custom Space
├── Projects
├── Library Sources
├── Sessions
├── Working States
├── Personal Models
├── Training Runs
└── Model Versions
```

### Space

A persistent domain with its own model, memory rules, sources, and tools.

### Project

A bounded body of work inside a Space.

### Session

An interaction thread with active Working Context.

### Personal Model

Base engine + selected personal adapter/version.

---

## 6. V1 Spaces

### Writer

Capabilities:

- chat/drafting;
- article workspace;
- research import;
- outline and argument map;
- section-by-section long-form generation;
- revision;
- voice learning;
- source-aware context;
- context inspector.

### Developer

Capabilities:

- attach local Git repo;
- repository map;
- ask/code mode;
- relevant-file selection;
- patch proposals;
- local file edits after permission;
- build/test command integration;
- architecture memory;
- coding-style learning;
- context inspector.

V1 should ship these two exceptional experiences before adding generic personas.

---

## 7. Information Architecture

```text
Sidebar
├── Home
├── Writer
│   ├── Projects
│   ├── Library
│   └── Model
├── Developer
│   ├── Projects
│   ├── Repositories
│   └── Model
├── Training
├── Models
└── Settings
```

The app opens to **Home / Continue**, not a blank chat box.

---

## 8. Home — Continue What Matters

The Home screen answers:

> What was I doing, and what should I continue?

Suggested layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ Context                                      Search   ⌘K    │
├──────────────────┬──────────────────────────────────────────┤
│ Home             │ Good evening                             │
│ Writer            │                                          │
│ Developer         │ Continue                                 │
│ Training          │ ┌──────────────────────────────────────┐ │
│ Models            │ │ Article: Institutional Accountability│ │
│                   │ │ 2 unresolved threads · Writer v3     │ │
│                   │ └──────────────────────────────────────┘ │
│                   │ ┌──────────────────────────────────────┐ │
│                   │ │ NauticGrid Operator                  │ │
│                   │ │ 4 relevant changes since last work   │ │
│                   │ └──────────────────────────────────────┘ │
│                   │                                          │
│                   │ Your Models                              │
│                   │ Writer  Ready     Developer  Ready       │
└──────────────────┴──────────────────────────────────────────┘
```

No noisy dashboard of vanity metrics.

---

## 9. Onboarding

### Step 1 — Welcome

```text
Context

AI that learns how you work.
Runs on your Mac.

[Get Started]
```

### Step 2 — Hardware check

Detect:

- Apple Silicon generation;
- unified memory;
- free disk;
- macOS version;
- expected supported model profile.

Human-facing result:

```text
Your Mac is ready.
32 GB unified memory
Recommended: Standard local models
```

### Step 3 — Choose first Space

```text
What should Context learn first?

[ Writer ]
Learn your voice, research patterns and long-form workflow.

[ Developer ]
Learn your architecture, code style and project context.
```

### Step 4 — Add sources

Writer:

```text
Drop writing folders, documents and archives.
```

Developer:

```text
Choose Git repositories.
```

Use `NSOpenPanel` and drag/drop. Never demand blanket disk access unnecessarily.

### Step 5 — Analysis

Display real work rather than fake animation:

```text
Analyzing your work

427 writing samples       ✓
83 draft/final pairs      ✓
18 duplicates             excluded
24 quoted-heavy documents review

Your originals are unchanged.
```

### Step 6 — Training review

Before first training:

```text
Ready to create Writer v1

Gold samples          214
Standard samples      173
Context exercises     186
Held-out tests         42

[Review Dataset]   [Train]
```

### Step 7 — Training

```text
Creating Writer v1

Preparing examples       ✓
Training                  ████████░░
Quality checks            pending

Processing is happening on this Mac.
```

Never promise a fake completion time. Show measurable progress only when available.

### Step 8 — Meet the model

Run a side-by-side base vs personal output comparison.

```text
Your Writer is ready.

Try it with one of your real projects.

[Start Writing]
```

---

## 10. Writer Workspace

This should feel closer to a great writing application than to ChatGPT.

```text
┌─────────────────────────────────────────────────────────────┐
│ Article Title                                 Writer v3     │
├──────────────┬──────────────────────────────┬───────────────┤
│ Outline      │                              │ Context       │
│              │        EDITOR                │               │
│ 1. Opening   │                              │ Thesis        │
│ 2. History   │                              │ Sources       │
│ 3. Case      │                              │ Claims used   │
│ 4. Analysis  │                              │ Open threads  │
│ 5. Close     │                              │               │
│              │                              │ Inspect →     │
├──────────────┴──────────────────────────────┴───────────────┤
│ Ask Writer…                                         ⌘↵     │
└─────────────────────────────────────────────────────────────┘
```

### Writer modes

- Draft
- Continue
- Rewrite
- Tighten
- Expand
- Build outline
- Challenge argument
- Source check
- Context check

Avoid a toolbar with dozens of AI actions. Most actions should be available through selection popover, command palette, or natural instruction.

### Long-form controller

The user can toggle **Article Plan**:

```text
Thesis
Argument map
Sections
Target length
Sources
Claims already made
Unresolved threads
```

The model generates section by section, and Working State updates after each accepted section.

---

## 11. Developer Workspace

```text
┌─────────────────────────────────────────────────────────────┐
│ NauticGrid Operator                          Developer v2   │
├────────────────┬────────────────────────────┬───────────────┤
│ Repository     │ Session                    │ Context       │
│                │                            │               │
│ Sources/       │ Implement entitlement      │ Relevant      │
│ Features/      │ separation...              │ Files 5       │
│ Tests/         │                            │ Decisions 3   │
│                │ Plan                       │ Constraints 4 │
│                │ ...                        │               │
│                │                            │ Inspect →     │
├────────────────┴────────────────────────────┴───────────────┤
│ Ask Developer…                                     ⌘↵     │
└─────────────────────────────────────────────────────────────┘
```

### Developer modes

- Ask
- Plan
- Implement
- Explain
- Debug
- Test
- Review changes

### Change safety

Before file writes, display proposed scope:

```text
Will modify
• EntitlementService.swift
• OperatorAccess.swift
• EntitlementServiceTests.swift

Will not modify
• Billing
• Newsletter dashboard

[Review Diff] [Apply]
```

The model should never silently broaden scope.

---

## 12. The Killer Feature — Context Inspector

A button named **Context** opens a first-class inspector, not a developer debug dump.

```text
Working Context

Objective
Separate Operator access from the existing intelligence product.

Active Constraints
• Operator is separately paid
• Existing newsletter product remains available
• Avoid monolithic services

Current Decisions
• Shared account
• Separate entitlements

Relevant Material
✓ operator-spec.md                     96%
✓ EntitlementService.swift             91%
✓ BillingPlan.swift                    84%

Not Included
○ old-pricing-draft.md   Superseded
○ README.md              Low relevance

Open Threads
• Upgrade transition behavior

[Why this context?]
```

Users should be able to:

- pin context;
- remove context;
- mark source canonical;
- mark decision superseded;
- inspect provenance;
- see approximate token cost;
- regenerate the context package.

This makes the product's intelligence visible and trustworthy.

---

## 13. Context Timeline

Projects should have a compact historical memory timeline:

```text
Aug 10  Decided separate Operator entitlement
Aug 11  Implemented entitlement service
Aug 12  Rejected unified navigation proposal
Aug 14  Pricing changed to ...
```

A timeline item can be:

- decision
- constraint
- milestone
- unresolved item
- architecture change
- publication/draft event

The timeline is application state, not merely model-generated chat history.

---

## 14. Training Center

```text
Training

Writer
Active: v3
New high-quality material: 17 items
[Review Learning Inbox]

Developer
Active: v2
New candidate examples: 43
[Review Learning Inbox]

Recent Runs
Writer v4 candidate     Better voice / weaker context   Rejected
Writer v3               Active                           ✓
Code v2                 Active                           ✓
```

### Learning Inbox

The app periodically identifies material that *could* improve the model but does not train automatically.

User controls:

- include;
- exclude;
- Gold;
- reference only;
- inspect generated example.

### Candidate promotion

After training:

```text
Writer v4 vs Writer v3

Voice                   +8%
Context retention       +4%
Repetition              -2%
Source discipline        0%

Your blind preference   14 / 20 for v4

[Keep v3]     [Promote v4]
```

The exact scores must not pretend to be scientific unless they genuinely come from defined evals.

---

## 15. Models Screen

Users should see a clean abstraction:

```text
Models

Writer v3
Engine        Qwen • Local
Learning      Your writing + context behavior
Storage       ...
Status        Ready

Developer v2
Engine        Qwen Coder • Local
Learning      Your coding + context behavior
Storage       ...
Status        Ready
```

Advanced disclosure:

- exact model ID;
- quantization;
- context window;
- adapter path;
- runtime version;
- dataset manifest;
- logs.

---

## 16. Local Runtime Architecture

Recommended process architecture:

```text
Context.app (Swift)
       │
       ├── UI / project state
       ├── permissions
       ├── licensing
       └── command orchestration
       │
       ▼
Context Runtime Service
       │
       ├── model host
       ├── MLX inference
       ├── training jobs
       ├── indexing
       ├── retrieval
       └── context planner
       │
       ▼
Local Storage
```

The runtime service should have a versioned local IPC/API contract. Prefer a controlled local XPC/service architecture where feasible; if a localhost HTTP service is used, bind to loopback only, use unpredictable authentication credentials, and never expose it to LAN by default.

---

## 17. macOS Technical Architecture

### App

- Swift 6+
- SwiftUI
- AppKit where superior for text/editor/window behavior
- Observation/structured concurrency
- SwiftData or SQLite/Core Data depending on scale/performance evaluation

### Major modules

```text
AppShell
ProjectDomain
WriterFeature
DeveloperFeature
ContextFeature
TrainingFeature
ModelManagement
LibraryIndex
RuntimeBridge
Licensing
UpdateService
Diagnostics
Security
```

No god objects and no feature module should know MLX implementation details directly.

### Actors/services

```text
@MainActor UI
RuntimeActor
IndexActor
ContextActor
TrainingActor
FileAccessActor
LicenseActor
UpdateActor
```

---

## 18. Python/MLX Packaging

Do not assume end users have Python installed.

The commercial app must ship or install a controlled runtime environment managed by the application.

Requirements:

- no `pip install` required by consumer;
- runtime version pinned;
- integrity verification;
- atomic runtime updates;
- ability to roll back runtime;
- model download resumable;
- models stored outside application bundle;
- training environment isolated from user shell environment.

Evaluate packaging approaches during technical spike; the user experience requirement is fixed even if the implementation changes.

---

## 19. Model Downloads

The application bundle should remain reasonably sized.

On first setup:

```text
Download Writer Engine
~X GB

Stored on this Mac.
[Download]
```

Model metadata service should supply:

- model ID;
- exact revision;
- size;
- checksum;
- license metadata;
- compatibility;
- minimum memory;
- minimum runtime version.

Do not silently change a user's active base model.

---

## 20. Direct Distribution

V1 is **direct sale/download only**.

Release flow:

```text
Xcode archive
   ↓
Developer ID signing
   ↓
Hardened Runtime
   ↓
Notarization
   ↓
Staple ticket
   ↓
Package .dmg
   ↓
Website/CDN
   ↓
Sparkle-style signed update feed or equivalent
```

The app should be signed with Developer ID and notarized before public release.

Do not build product architecture around Mac App Store sandbox constraints.

---

## 21. Updates

Requirements:

- signed updates;
- automatic update checks (user-configurable);
- release notes;
- stable/beta channel optionally later;
- runtime compatibility check before updating;
- never delete models/adapters during app update;
- database migration with rollback/recovery strategy.

Use a mature macOS updater or build equivalent signing/security correctly; do not create an ad-hoc insecure updater.

---

## 22. Licensing and Commerce

Keep billing provider behind an abstraction.

```swift
protocol EntitlementProvider {
    func refreshEntitlements() async throws -> Entitlements
    func activateLicense(_ token: String) async throws
    func deactivateDevice() async throws
}
```

Product must support:

- trial/evaluation mode;
- paid Pro license;
- Studio tier later;
- device activation policy;
- offline grace period;
- receipt/license restoration;
- refunds handled through commerce backend;
- no user data or training corpus used for entitlement decisions.

### Recommended business shape

**Free/Evaluation**

- test local inference;
- limited project/library;
- no or limited personal training.

**Pro**

- Writer personal model;
- Developer personal model;
- advanced context engine;
- training/versioning;
- multiple projects;
- Git integration.

**Studio** later

- more specialist Spaces;
- heavier training workflows;
- team/organization features if introduced.

Pricing must be validated with customers; do not bake prices into core architecture.

---

## 23. Privacy Promise

A dedicated Privacy screen should make the architecture explicit:

```text
Local Processing
✓ Model inference on this Mac
✓ Personal training on this Mac
✓ Document indexing on this Mac
✓ Repository analysis on this Mac

Network
Model downloads: Allowed
Update checks: Allowed
Diagnostics: Off / Optional
```

Users can inspect network-requiring features.

No document/content telemetry by default.

---

## 24. Permissions

Use least privilege.

- User-selected folder access.
- Security-scoped bookmarks where appropriate.
- Explicit repo selection.
- Explicit terminal/build-command permission.
- No Full Disk Access requirement unless a future feature genuinely needs it.

If an operation needs additional permission, explain **why**, at the moment it is required.

---

## 25. Design Language

### Visual personality

- unmistakably macOS;
- restrained;
- editorial;
- dense enough for professional work but never cramped;
- excellent typography;
- subtle material/blur only where native and useful;
- generous whitespace around important states;
- no neon AI gradients;
- no orb/brain/sparkle visual clichés;
- no fake terminal aesthetic unless displaying actual terminal output.

### Typography

Use system typography by default. Writer editor should prioritize legibility and long-form composition.

### Color

Use semantic macOS colors and a restrained accent. Support Light, Dark, and System.

### Motion

Motion communicates state changes only:

- context item added/removed;
- training state transitions;
- project restoration;
- panel changes.

Avoid decorative perpetual animations.

---

## 26. Design System Components

Create reusable components:

```text
SourceChip
ContextCard
DecisionRow
ConstraintRow
ModelBadge
TrainingRunCard
QualityBadge
ProjectCard
DiffCard
SourceCitation
TokenBudgetBar
StatusPill
InspectorSection
EmptyState
CommandPalette
```

All should support keyboard navigation and accessibility.

---

## 27. Command Palette

`⌘K` is a primary navigation/action surface.

Examples:

```text
Open project…
Start new article
Switch to Writer
Switch to Developer
Inspect context
Pin current source
Train new Writer candidate
Show Model Versions
Search Library
```

---

## 28. Search

Global search should span:

- projects;
- documents;
- articles;
- repository files/symbols;
- decisions;
- constraints;
- sessions;
- model versions.

Search result tells the user *what kind of memory* the hit belongs to.

---

## 29. Empty States

Good empty states teach the model:

Writer:

> Add the work that best represents how you write.

Developer:

> Choose a repository you understand well. Context will learn its structure before it changes anything.

Training:

> Your active model does not change until you approve a candidate.

---

## 30. Failure States

### Insufficient memory

Explain model cannot be loaded and offer a smaller compatible profile.

### Training interrupted

Resume from a safe checkpoint where supported; never imply originals are damaged.

### Corrupt model download

Verify checksum, discard partial corruption, resume/re-download.

### Retrieval uncertainty

Model/UI should say context is incomplete instead of inventing project facts.

### Build failure

Show command, output, files changed, and offer rollback.

---

## 31. Performance Targets

Initial targets:

- app launch feels immediate independent of model loading;
- model services lazy-load;
- UI remains responsive during training/inference;
- search feedback <200 ms for common local queries where index supports it;
- context assembly should normally complete fast enough to feel interactive;
- long-running indexing/training never blocks main thread;
- memory pressure produces graceful model unload rather than app crash;
- app can be used for non-model browsing while training is active.

Exact token/sec targets depend on hardware/model and should be measured, not promised globally.

---

## 32. Hardware Profiles

Example product profiles:

### Compact

Lower-memory Apple Silicon; smaller engine/context budgets.

### Standard

16–32 GB; primary small specialist models.

### Max

32+ GB; larger context budgets and optional larger engines.

The product selects safe defaults but lets advanced users override with warnings.

---

## 33. Data Portability

Users own their work.

Export:

- project metadata;
- context state;
- decisions/constraints;
- training dataset;
- adapters;
- eval reports;
- source manifest.

Delete:

- individual source;
- project;
- training run;
- model version;
- entire local Context data store.

A future account cancellation must not make local documents inaccessible.

---

## 34. Diagnostics

Optional diagnostics bundle must redact:

- document contents;
- code contents;
- prompt/output bodies by default;
- secrets;
- file paths where possible.

Bundle may include:

- runtime versions;
- crash logs;
- model manifest;
- memory metrics;
- training error metadata;
- anonymized operation timeline.

User previews diagnostics before sharing.

---

## 35. Website / Sales Experience

Landing page should lead with outcome, not model technology.

```text
CONTEXT
AI that remembers how you work.

A private personal AI for your writing, projects and code.
Built for Apple Silicon.

[Download for Mac]
```

Second section:

```text
It learns how you work.

Writer
Your voice. Your research. Your arguments.

Developer
Your architecture. Your conventions. Your projects.
```

Third:

```text
Context is the feature.

See what your AI remembers,
why it selected it,
and what it ignored.
```

Then privacy:

```text
Your Mac does the work.
Personal training and inference stay local by default.
```

Avoid leading with “Qwen,” “LoRA,” or “RAG.” Advanced technical page can explain those details.

---

## 36. Commercial Moat

The moat is not a bundled open model.

Build proprietary product value around:

1. corpus analysis and quality classification;
2. training-example generation;
3. context-state representation;
4. context selection/ranking;
5. context compression;
6. source/decision provenance;
7. model evaluation and promotion;
8. long-form orchestration;
9. repository-aware code context;
10. excellent Mac UX;
11. years of local personal/project memory in a portable data model.

Model providers can improve underneath this layer without destroying the product's value.

---

## 37. Product Metrics

Privacy-respecting aggregate metrics only if user opts in.

Business/product metrics:

- onboarding completion;
- first model created;
- time to first useful session;
- projects created;
- weekly active projects;
- training candidate promotion rate;
- Writer/Developer usage split;
- paid conversion;
- retention;
- crashes.

Local-only quality metrics can be richer and need not be transmitted:

- context precision;
- context compression ratio;
- preferred adapter win rate;
- repetition;
- retrieval hit rate;
- build/test success.

---

## 38. MVP Scope

### Must ship

- native macOS app;
- direct Developer ID/notarized distribution;
- onboarding/hardware check;
- managed model download;
- Writer Space;
- Developer Space;
- document/repo import;
- local indexing;
- Working Context;
- Context Inspector;
- local inference;
- local Writer/Code LoRA training;
- Training Center;
- model candidate evaluation;
- version promotion/rollback;
- Writer long-form controller;
- Developer relevant-file selection + diff/apply loop;
- licensing/trial;
- signed auto-update path;
- privacy controls.

### Explicitly defer

- iOS/iPad;
- Mac App Store;
- cloud inference;
- team collaboration;
- shared organization memory;
- plugin marketplace;
- autonomous deployment;
- multi-user hosted training;
- dozens of personas.

---

## 39. Engineering Milestones

### M0 — Runtime spike

Prove:

- bundled/managed MLX runtime;
- Qwen inference;
- Qwen LoRA training;
- Swift↔runtime communication;
- cancellation and progress reporting.

### M1 — Context foundation

- data model;
- file import;
- repo import;
- local index;
- Working State;
- Context Inspector prototype.

### M2 — Writer alpha

- editor;
- projects;
- article plan;
- retrieval;
- Writer model;
- first local training flow;
- long-form workflow.

### M3 — Developer alpha

- repo browser;
- repo map;
- context file selection;
- Code model;
- diff;
- apply;
- test/build integration.

### M4 — Learning system

- Learning Inbox;
- dataset review;
- candidate training;
- evals;
- version management;
- rollback.

### M5 — Commercial beta

- licensing;
- onboarding polish;
- updater;
- diagnostics;
- accessibility;
- privacy review;
- performance/thermal testing.

### M6 — 1.0

- Developer ID signed;
- notarized;
- website purchase/download;
- stable update feed;
- documentation;
- support workflow.

---

## 40. Security Review Checklist Before 1.0

- Hardened Runtime configured correctly.
- All bundled executables/libraries signed.
- Notarization passes from clean release artifact.
- Local model API inaccessible from non-loopback interfaces.
- Runtime requests authenticated if using HTTP IPC.
- No shell injection through build commands/path names.
- Secret scanner tested.
- Symlink/path traversal behavior tested.
- Download hashes verified.
- Update signatures verified.
- License endpoint compromise does not expose local corpus.
- Diagnostics redact content.
- User can identify/delete every indexed source.

---

## 41. Design Deliverables

Before implementation lock, produce:

1. Product map.
2. Onboarding flow.
3. Home/Continue.
4. Writer workspace.
5. Article Plan.
6. Developer workspace.
7. Diff/apply flow.
8. Context Inspector.
9. Context Timeline.
10. Training Center.
11. Learning Inbox.
12. Candidate comparison.
13. Models screen.
14. Settings/privacy.
15. Purchase/trial state.
16. Error/empty states.
17. Light and dark appearance.
18. Keyboard/command palette flows.

### Design-agent direction

The designer should study high-quality native professional Mac applications for information density and platform conventions, but must not clone a named competitor. The result should feel like an Apple-platform application designed by a serious productivity-software team, not a web dashboard port.

Key visual idea:

> **The AI is quiet. The user's work is primary. Context is visible when it matters.**

---

## 42. Acceptance Criteria — Product 1.0

A new Apple Silicon Mac user can:

1. download a notarized DMG from the website;
2. install/open without Terminal;
3. choose Writer or Developer;
4. import representative work;
5. understand exactly what will be used for learning;
6. download the required local engine;
7. create a personal model locally;
8. compare it to a baseline/candidate;
9. use it in a polished native workspace;
10. inspect the working context behind an answer;
11. continue a project days later with correct key state restored;
12. add new work to memory immediately;
13. later create a new model candidate from curated new work;
14. reject or promote that candidate;
15. roll back;
16. update the application safely;
17. manage/delete/export local data.

If any of those core flows requires the consumer to type an MLX/Python command, the product is not finished.

---

## 43. Final Product Definition

SIXTWELVE Context is **not** a local chatbot with fine-tuning bolted on.

It is a native Mac environment for maintaining a durable relationship between:

```text
THE USER'S WORK
      +
THE USER'S BEHAVIOR
      +
CURRENT PROJECT STATE
      +
THE RIGHT CONTEXT
      +
A SMALL LOCAL MODEL
```

The foundation model is replaceable. The durable product is the context layer, learning pipeline, project memory, evaluation system, and native interface around it.

The commercial promise is simple:

> **Open your project and continue. Context already knows where you left off.**

