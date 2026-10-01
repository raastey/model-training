# DECISIONS

| Date | Decision | Evidence / rationale |
| --- | --- | --- |
| 2026-08-11 | Keep Writer and Code fully separate. | Training implementation specification and user direction. |
| 2026-08-11 | Use local Qwen2.5 3B Writer base plus MLX LoRA candidates. | Local Apple Silicon runtime verified. |
| 2026-08-11 | Retain retrieval outside adapter weights. | Facts need inspectable, replaceable provenance. |
| 2026-08-11 | Reject `writer-context-001`. | Severe context-runtime repetition. |
| 2026-08-11 | Reject `writer-context-002`. | Empty completion on a reviewed context task. |
| 2026-08-11 | Reject `writer-chunked-001` for context use. | Repetition on 2 of 5 reviewed context tasks. |
| 2026-08-11 | Keep the base model as the operational context default. | Passed 5/5 runtime gates. |
| 2026-08-11 | Use all three `MD-Files` libraries in Writer v5. | Full re-import found all material already included; v5 records library composition. |
| 2026-08-11 | Test voice adaptation separately from context-task training. | `writer-chunked-001` ablation showed 3/5 at 3k but 1/5 at 6k and 9k; context size worsens behavior but does not fully explain repetition. |
| 2026-08-11 | Keep `writer-voice-001` as a candidate only. | It passes 5/5 at the intended 3k/220 profile but has not passed the 400-token stress condition or blind voice review. |
| 2026-08-11 | Permit a constrained `writer-voice-001` short-context trial, not promotion. | User's blind review selected it for evidence and accountability (2 wins) while base won power; the candidate still has one long-output stress failure. |
| 2026-08-11 | Prepare the Code pipeline before receiving a code repository. | Separate inspector/importer, corpus namespace, and Qwen2.5-Coder base are ready; no Code content has been imported. |
| 2026-08-11 | Keep `code-smoke-001` as a candidate only. | The 50-step, 4-layer Code LoRA passed 2/2 tiny executable Python/Swift checks, but those checks do not establish repository patch quality or test preservation. |
| 2026-08-11 | Do not use `code-smoke-001` for real repository maintenance. | Both base and candidate failed the first real NauticGrid controlled mutation fixture even with the existing Vitest test supplied; the candidate declined to return a replacement file. |
| 2026-08-11 | Build SIXTWELVE Context as a direct-sold Rust-core cross-platform desktop product, launching on macOS. | User direction supersedes the earlier Swift-only architecture assumption; direct distribution preserves local runtime, licensing, and updater control across platforms. |
| 2026-08-12 | Require rendered-token validation for every patch-oriented Code dataset. | The first v2 dataset emitted sequences exceeding the 2,048-token training limit. V4 uses the local Qwen tokenizer on the rendered chat format and caps examples at 1,800 tokens. |
| 2026-08-12 | Reject both completed Code adapters and keep the Code base as the only permitted runtime. | `code-smoke-001` reached only 1/3 on the expanded controlled real-project suite. `code-patch-003` stayed at 1/3 and regressed from 2/2 to 1/2 on bounded patch checks. |
| 2026-08-12 | Stop training at the verified checkpoint pending a representative future task set. | The current corpus and tests do not justify another adapter iteration; further training without a more targeted curriculum would create noise rather than product value. |
| 2026-08-12 | Expand the pending Code v5 evaluation proposal across the user's actual app portfolio. | The initial draft over-weighted NauticGrid. The revised 12-task suite includes camera, photo/video, Lumen, Dictionary, Mishkat Quran, and TypeScript product behavior; it remains pending user approval. |
| 2026-08-12 | Treat the Camera App and photo-editing Xcode platform warning as non-fatal for runner qualification. | Their Xcode result bundles record 2 and 1 passing selected tests respectively on the fixed iOS simulator. All 12 proposed source/test contracts are executable-qualified, but no controlled mutation or training is authorized yet. |
| 2026-08-12 | Begin Code v5 fixture construction from the approved 12-task suite. | User explicitly approved the suite. The first artifact is a metadata-only manifest with source/test hashes, not source contents; live repositories remain unchanged. |
| 2026-08-12 | Reject `code-v5-001` and retain the Code base as the only runtime. | The held-out v5 candidate completed, but scored 2/2 smoke, 1/2 patch, and 0/3 real tests. The base scored 2/2, 2/2, and 1/3. Further training needs exact controlled-mutation evidence rather than another generic patch dataset. |
| 2026-08-12 | Require a measured minimum of test-contract examples before another Code dataset/run. | V5 contained only 5 discovered test-contract examples out of 1,191 total. A configurable dataset guard now fails construction below the stated minimum; no future candidate may use generic full-file imitation as a substitute for repair episodes. |
| 2026-08-12 | Exclude SwiftPM build/checkouts from Code training and hold V6 untrained. | Legacy imports contained dependency source under `.build/checkouts`. Clean V6 raised verified contracts to 44 but still has only 44/1,110 contract-bearing examples, below a repair-first standard. |
| 2026-08-12 | Pause further Qwen2.5-Coder 3B adapter iterations. | The independent repair-only V7 curriculum used 120 test contracts and a smaller adapter yet still scored 2/2 smoke, 1/2 patch, 0/3 real—identical safety regression to V5. More iterations of the same base/data shape are not justified. |
| 2026-08-12 | Select the unmodified Qwen2.5-Coder 7B base as the preferred Keel Code-chat model; reject its adapter. | The 7B base passes 3/3 held-out real repairs, versus 3B's 1/3. Its minimal real-history adapter regressed to 2/3 real and 0/2 bounded patch. Use the stronger base directly, with reviewed rather than autonomous writes. |
