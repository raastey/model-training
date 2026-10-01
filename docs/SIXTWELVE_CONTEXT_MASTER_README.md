# SIXTWELVE Context — Master Specification

This project is specified in two implementation documents:

1. [`SIXTWELVE_LOCAL_AI_TRAINING_SPEC.md`](./SIXTWELVE_LOCAL_AI_TRAINING_SPEC.md) — local Qwen Writer/Code model training, context-management curriculum, evaluation, continual learning and MLX runtime architecture.
2. [`SIXTWELVE_CONTEXT_MAC_PRODUCT_SPEC.md`](./SIXTWELVE_CONTEXT_MAC_PRODUCT_SPEC.md) — commercial native macOS product, UX, direct distribution, local runtime, privacy, licensing and roadmap.
3. [`SIXTWELVE_CONTEXT_CROSS_PLATFORM_DESIGN_SPEC.md`](./SIXTWELVE_CONTEXT_CROSS_PLATFORM_DESIGN_SPEC.md) — finalized Rust-core, direct-sale, cross-platform product/design handoff for Claude Design. This supersedes the earlier Swift-only architecture direction while retaining macOS as the launch platform.
4. [`TRAINING_HANDOFF.md`](./TRAINING_HANDOFF.md) — verified current Writer/Code model readiness, candidate outcomes, and safe resume conditions for the local training laboratory.
5. [`CODE_MAINTENANCE_TASKSET_AND_CURRICULUM.md`](./CODE_MAINTENANCE_TASKSET_AND_CURRICULUM.md) — pending-approval cross-product evaluation suite and Code v5 curriculum proposal covering the user's camera, photo, Lumen, Dictionary, Quran, and TypeScript applications.
6. [`CODE_TASK_QUALIFICATION.md`](./CODE_TASK_QUALIFICATION.md) — live qualification record for the approved cross-product tasks. All 12 contracts have demonstrated safe local test runners; all Code adapters are rejected, while the separate unmodified 7B Code base is selected for reviewed Keel chat.

## Product thesis

> **AI that remembers how you work.**

The v1 product trains two local specialist models:

- Writer: voice + long-form behavior + context management.
- Developer: coding behavior + repository context management.

A shared local context engine maintains project state, retrieval, compression, provenance and context budgeting.

## V1 model decision

Use a stable Qwen2.5 3B-class pair for the first production training pipeline, behind an abstraction that allows migration to newer Qwen generations after benchmark and MLX compatibility validation.

## Distribution decision

macOS direct distribution only for v1: Developer ID signing, Apple notarization, website purchase/download, and signed application updates. No Mac App Store version is required.
