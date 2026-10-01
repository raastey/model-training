# SIXTWELVE Context — Cross-Platform Product and Design Specification

**Status:** finalized design handoff v1

**Audience:** Claude Design, product design, and future application engineering

**Product form:** paid, direct-distributed desktop software. Launch platform: macOS. Architecture: cross-platform desktop application with a Rust core. The same product should later ship for Windows and Linux without changing the product model.

## Product definition

SIXTWELVE Context is a private desktop work environment where a person can write, research, plan, code, test, and continue projects with local AI that has visible project context and can learn their working patterns.

> AI that remembers how you work.

Supporting line:

> Your work. Your context. Your model. On your computer.

## What the user is buying

Not a model download and not a chatbot. They are buying:

- a durable local Library of their work;
- a Writer specialist and Developer specialist that stay separate;
- Working Context that makes a current task understandable without re-explaining it;
- transparent source selection, decisions, constraints, and project history;
- supervised learning with candidate models, quality checks, promotion, and rollback;
- a professional native-feeling desktop environment.

## Product pillars

1. **Local first.** Inference, indexing, context creation, and personal training happen on the user's computer by default.
2. **Project continuity.** Opening a project restores the objective, decisions, open threads, and relevant material.
3. **Inspectable context.** The user can see why material was included, what was excluded, and change it.
4. **Controlled learning.** New work enters a Learning Inbox. Training creates a candidate; it never silently changes the active model.
5. **Safe code changes.** The Developer specialist proposes scope and diffs. It never silently changes a repository.
6. **Cross-platform core, platform-native surface.** The same concepts and data work across operating systems; menus, shortcuts, file pickers, updates, and visuals respect the host platform.

## Primary customers

- writers, journalists, researchers, analysts, founders, consultants, and independent creators;
- developers who work across multiple repositories and want local, project-aware assistance;
- privacy/IP-sensitive professionals who do not want private work used for remote training.

## Product language

| Technical concept | Product language |
| --- | --- |
| Base model | Engine |
| LoRA adapter | Personal Model |
| Fine-tuning | Learning / Training |
| Retrieval augmented generation | Library / Working Context |
| Vector index | Search Index |
| Evaluation | Quality Check |
| Candidate adapter | Candidate Model |

Use technical language only in Advanced details.

## Non-negotiable product rules

- Writer and Developer never share a Library, Personal Model, training set, context index, or evaluation history.
- Original files are read-only unless the user explicitly edits them or approves a Developer diff.
- Secret-looking repository files are quarantined and never included in learning or context by default.
- The active Personal Model never changes because a training run completed.
- A model is not presented as ready for code changes without passing defined repository-level quality checks.
- The product never claims that all user work has been “memorized.” It shows selected Working Context.
- No content telemetry by default.

## Platform and architecture direction

### Recommended architecture

```text
Desktop application shell
├── Rust Core
│   ├── project and library domain
│   ├── local database and encrypted/sealed metadata where appropriate
│   ├── indexing, retrieval, context assembly, and working state
│   ├── model/download/run registry
│   ├── training orchestration and quality-check registry
│   ├── safe filesystem and repository access
│   ├── licensing, update, diagnostics, and privacy policy
│   └── local IPC to inference/training runtime
├── UI layer
│   ├── macOS first-class desktop interface
│   ├── Windows and Linux host adaptations later
│   └── shared product design system
└── managed local model runtime
    ├── inference
    ├── training
    ├── indexing/embeddings
    └── loopback or local IPC only
```

Rust owns durable business rules and all sensitive boundaries. UI must not directly manipulate models, indexes, or arbitrary filesystem paths.

### UI implementation decision

The design must not assume a web-dashboard aesthetic. The engineering team may use Tauri + Rust with a carefully built desktop UI, or another Rust-compatible desktop shell, but must retain:

- native menus and file dialogs;
- accessible keyboard navigation;
- host-platform window behavior;
- direct-distribution update support;
- no browser-like URL/navigation chrome;
- strong large-text and high-contrast support.

### Distribution

Direct sale/download only in v1.

- macOS: Developer ID signing, Hardened Runtime, notarization, signed update feed.
- Windows: Authenticode signing and signed updater.
- Linux: signed packages/archives plus a clear update strategy.
- Never depend on App Store, Microsoft Store, or cloud inference for core use.

## Application map

```text
Home
Writer
  Projects
  Library
  Sessions
  Personal Model
Developer
  Projects
  Repositories
  Sessions
  Personal Model
Training
  Overview
  Learning Inbox
  Runs
  Comparisons
Models
Settings
  General, Storage, Privacy, Permissions, Updates, License, Advanced
```

## Global shell

The app uses a professional three-pane desktop layout.

```text
┌──────────────────┬─────────────────────────────────────────────────────────┐
│ Home             │ Header: project title / Search / profile                 │
│ Writer           ├─────────────────────────────────────────────────────────┤
│ Developer        │                                                         │
│                  │                 Current feature workspace               │
│ Training         │                                                         │
│ Models           │                                                         │
│                  │                                                         │
│ Settings         │                                                         │
└──────────────────┴─────────────────────────────────────────────────────────┘
```

Required global behavior:

- keyboard command palette;
- standard platform shortcuts and context menus;
- collapsible sidebar;
- resizable inspector;
- no noisy productivity analytics or token dashboard;
- status language is explicit: Ready, Candidate, Needs review, Training, Interrupted, Not ready, Error.

## Screen specifications

### 1. Welcome and setup

Opening statement:

```text
Context

AI that remembers how you work.

Private local AI for your writing, projects, and code.

[ Get Started ]
```

Onboarding sequence:

1. hardware capability check;
2. choose Writer or Developer first;
3. add a writing folder or repository;
4. analyze material locally;
5. review exclusions and items needing decisions;
6. download compatible Engine;
7. enter a useful new project workspace.

Never demand terminal use, Python installation, blanket disk permission, or a cloud account to reach first use.

### 2. Home / Continue

The default post-onboarding screen answers: **What was I doing, and what should I continue?**

Show at most three Continue cards, then a recent-project list. A card includes Space, project name, last activity, one open thread, and context/readiness state.

```text
Institutional Accountability                         Writer
Last worked on yesterday
Open thread: strengthen the opening evidence chain
Working Context ready · 7 selected sources
```

### 3. Writer workspace

Writer is a true writing environment, not a chat page.

```text
┌────────────────┬──────────────────────────────────┬──────────────────────┐
│ Project / Plan │ Editable article                  │ Context              │
│ Outline        │                                  │ Objective            │
│ Research       │ User-owned document               │ Thesis               │
│ Versions       │                                  │ Sources              │
│                │                                  │ Decisions            │
├────────────────┴──────────────────────────────────┴──────────────────────┤
│ Ask Writer…               Mode: Continue ▾                     Send ⌘↵     │
└──────────────────────────────────────────────────────────────────────────┘
```

Modes: Draft, Continue, Rewrite, Tighten, Expand, Build outline, Challenge argument, Source check, Context check.

Selected text opens a compact action popover. Every response offers a review path: Insert below, Replace selection, Apply, Copy, Discard. AI output never silently overwrites prose.

Article Plan includes thesis, audience, target length, sections, evidence, claims already made, and unresolved threads.

### 4. Developer workspace

```text
┌──────────────────┬────────────────────────────────┬─────────────────────┐
│ Repository tree   │ Task / plan / response          │ Context             │
│ Features          │                                 │ Relevant files      │
│ Tests             │ Proposed plan                   │ Constraints         │
│ Changes           │ Diff when applicable            │ Decisions           │
│                   │                                 │ Tests to run        │
├──────────────────┴────────────────────────────────┴─────────────────────┤
│ Ask Developer…             Mode: Plan ▾                     Send ⌘↵         │
└──────────────────────────────────────────────────────────────────────────┘
```

Modes: Ask, Explain, Plan, Implement, Debug, Test, Review changes.

The edit flow is mandatory:

1. show planned scope;
2. show files to read/change and let user remove any;
3. generate a diff;
4. user chooses Apply, Copy, Save patch, or Discard;
5. user authorizes tests/build separately;
6. show command, duration, pass/fail, concise diagnostics.

If a Code Personal Model is experimental or has not passed real maintenance checks, show “Not ready for repository edits.” The base Engine remains useful for Ask, Explain, and Plan.

### 5. Context Inspector

This is the signature trust feature and opens from Writer/Developer with a persistent shortcut.

Sections, in order:

1. Objective
2. Active constraints
3. Current decisions
4. Relevant material
5. Not included (with reason: superseded, duplicate, low relevance, over budget, not permitted)
6. Open threads
7. Context budget: Comfortable / Near limit / Too much context

Every included item supports preview, open source, pin, remove for this response, mark canonical, and “Why included?” The user can regenerate the context package and see what changed.

### 6. Library and repositories

Writer Library is a source browser with statuses: Included, Gold, Reference only, Needs review, Excluded.

Developer Repositories show path, language mix, last index, source count, exclusions, quarantined items, and reindex/forget controls. Do not reveal secret content.

### 7. Training Center

Training is supervised and visually serious.

```text
Writer Personal Model
Active · Ready
Approved learning material: 214 items
Last Quality Check: passed
[ Details ]

New candidate
Needs review
Quality checks: 5 of 6 passed
Human comparison: pending
[ Compare ] [ Review ] [ Reject ]
```

Required run states: Preparing, Training, Checking quality, Needs review, Ready to promote, Active, Rejected, Interrupted, Incompatible.

Use amber for “Needs review”; do not use success green for a model that merely completed training.

### 8. Learning Inbox

New material is suggested but never auto-trained. Rows show title/path, type, recommendation, short reason, and status. Batch actions: Include, Gold, Reference only, Exclude, Review source, Undo.

### 9. Candidate comparison and promotion

Side-by-side Active/Base vs Candidate comparison. For Writer, show voice, context reliability, repetition, and blind preferences. For Developer, show patch success, test preservation, scope discipline, and known limitations.

Actions: Keep current, Run more checks, Compare in a real task, Promote candidate, Reject candidate. Promotion uses a confirmation sheet and preserves rollback.

### 10. Models, Privacy, and Storage

Models screen uses plain language: Engine, Personal Model, Working Context, storage, and readiness. Advanced disclosure shows technical metadata.

Privacy screen:

```text
On this computer
✓ Inference
✓ Library indexing
✓ Training
✓ Project context

Network
Model downloads          Allowed
App update checks        Allowed
Optional diagnostics     Off
```

Settings also include permissions, storage by category, export, scoped deletion, update channel, and license/device activation.

## Essential states

Design all primary screens in light and dark, plus:

- no Engine installed;
- insufficient device memory;
- interrupted/resumable download;
- training in progress;
- interrupted training;
- candidate failed a Quality Check;
- no relevant context;
- context over budget;
- source moved or permission lost;
- likely secret quarantined;
- Developer test/build failure;
- offline license grace period.

## Visual design direction

- Calm, editorial, dense but breathable professional desktop software.
- Respect platform conventions. macOS should feel at home on macOS; later Windows/Linux ports adapt controls without losing hierarchy.
- System typography by default; a reading-oriented type option can exist inside Writer only.
- Neutral base palette, restrained accent, semantic status colors, no color-only status.
- Use hierarchy, whitespace, separators, and native materials rather than excessive cards and rounded containers.
- Motion only signals meaningful state changes: panel changes, context changes, training transitions, project restoration.

Never use AI orbs, bots, brains, sparkles, neon gradients, fake terminal interfaces, chat bubbles as the primary Writer layout, gamification, or fake training time estimates.

## Components to design

SidebarRow, SpaceBadge, ProjectCard, SourceChip, ContextCard, DecisionRow, ConstraintRow, OpenThreadRow, ReadinessBadge, ModelCard, TrainingRunRow, QualityCheckRow, DiffCard, SourceCitation, ContextBudgetBar, QuarantineNotice, EmptyState, ConfirmationSheet, CommandPalette, ErrorBanner, ProgressState.

## Claude Design deliverables

Produce high-fidelity desktop designs and clickable prototypes for:

1. onboarding from Welcome through first Writer and Developer project;
2. Home/Continue populated and empty states;
3. Writer editor, Article Plan, selection actions, Context Inspector, and apply flow;
4. Developer repository workspace, scope review, diff, test result, and Context Inspector;
5. Library/repository management;
6. Training Center, Learning Inbox, candidate comparison, promotion, rejection, and rollback;
7. Models and Privacy/Storage settings;
8. Command Palette;
9. all critical error/empty states above;
10. light and dark versions of all core screens.

## Design acceptance test

A first-time buyer should understand, without reading technical documentation, that the application:

1. works locally on their computer;
2. keeps Writer and Developer separate;
3. does not silently alter original work or repositories;
4. shows the context behind an answer;
5. treats training results as candidates, not automatic truth;
6. supports a paid professional workflow they can return to days later;
7. is a real cross-platform desktop product, not a browser dashboard or model demo.

## Related specifications

- `docs/SIXTWELVE_CONTEXT_MAC_PRODUCT_SPEC.md` — original detailed macOS-first product specification; use for deeper flow detail but treat its Swift-only architecture as superseded by this document's Rust cross-platform direction.
- `docs/SIXTWELVE_LOCAL_AI_TRAINING_SPEC.md` — local training and context system behavior.
- `docs/SIXTWELVE_CONTEXT_MASTER_README.md` — specification index.
