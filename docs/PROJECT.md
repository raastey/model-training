# PROJECT

## Objective

Build a private local Writer specialist that learns the user's voice while keeping current facts in a separate, inspectable Writer retrieval layer. A future Code specialist remains fully separate.

## Non-negotiables

- Writer and Code use separate corpora, datasets, base models, adapters, indexes, evaluations, and promotion histories.
- Original writing, embeddings, models, adapters, and reports remain local.
- A LoRA adapter teaches behavior; retrieval supplies current source material.
- No adapter is promoted without retrieval, runtime, and human-review evidence.
- Secrets are never logged or placed in artifacts.

## Current Writer baseline

The local Qwen Writer base model plus Writer-only hybrid retrieval is the operational context baseline. No personal adapter is active.

## Current Code baseline

The separate local Qwen2.5-Coder 3B base remains available for lightweight Ask/Explain/Plan. A separate unmodified Qwen2.5-Coder 7B 4-bit base is now the preferred Keel Code-chat model for reviewed interactive assistance: on identical held-out checks it passed 2/2 smoke, 1/2 bounded patch, and 3/3 real NauticGrid repairs, compared with 3B's 2/2, 2/2, and 1/3. The 7B base is not authorized for autonomous edits because it still misses one bounded whitespace case. All Code adapters are rejected/inactive, including `code-7b-v8-001`, which regressed the 7B base to 0/2 patch and 2/3 real. Writer and Code remain isolated.

## Pending Code v5 contract

The user approved `docs/CODE_MAINTENANCE_TASKSET_AND_CURRICULUM.md` on 2026-08-12. Its 12 one-file, test-guided tasks span Camera App, Tanzaku, Kineto, SixTwelve PhotoLab, a photo-editing app, Lumen, Dictionary, Mishkat Quran, and NauticGrid. `reports/code/task-manifests/v5-approved-001.json` records metadata and source/test hashes only. Code v5 held all nine evaluation projects out but was rejected: 2/2 smoke, 1/2 bounded patch, and 0/3 existing real-project tests versus the 3B base’s 2/2, 2/2, and 1/3. V5 also admitted dependency build/checkouts and had only 5/1,191 test-contract examples. Clean V6 excludes those paths and identifies 44/1,110 contracts; it remains untrained. A separate V7 used 120 token-validated, repair-only test contracts with a smaller two-layer LoRA, but `code-v7-001` was also rejected at 2/2 smoke, 1/2 patch, 0/3 real. The unmodified 7B Code base is now the preferred Keel runtime; 3B remains an optional lightweight fallback. Further adapter training is paused pending a substantial corpus of verified real-project repair episodes. Every evaluation runs in a temporary copy and must prove original-test pass plus controlled-mutation failure before it can count toward promotion.

## Commercial application direction

SIXTWELVE Context will be sold through direct download, with macOS as the launch platform and a Rust-core cross-platform desktop architecture. The consumer product must hide terminal/Python setup while preserving local-first processing, strict Writer/Developer isolation, inspectable Working Context, explicit candidate promotion, and reviewed code writes. The design handoff is `docs/SIXTWELVE_CONTEXT_CROSS_PLATFORM_DESIGN_SPEC.md`.
