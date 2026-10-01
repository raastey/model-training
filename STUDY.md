# Context versus weights: steering small local models

Two studies on Apple silicon (M1 Pro, 32 GB) with 4-bit MLX models. Both ask one product question: when you need a model to behave differently, what should you change first, the context or the weights?

Everything here reruns on a Mac with:

```sh
.venv/bin/sixai study writer   # about 6 minutes
.venv/bin/sixai study code     # about 4 minutes
```

## Study 1: Writer voice (Qwen2.5-3B-Instruct)

**Goal.** Make a general 3B model write like one specific journalist, using 250 of his published articles.

**Method.** 12 held-out writing tasks ([`evals/study/writer-tasks.json`](evals/study/writer-tasks.json)), six steering conditions, the same seed and sampling for all. No remote judge; every metric is deterministic:

- **Style delta.** Burrows' Delta over the author's 80 most frequent words, a standard authorship-attribution distance. Lower is closer to the author. 300-word excerpts of the author's own writing score 1.53, which sets the floor.
- **Register violations.** Banned words, em dashes, and scaffolding phrases from the author's written style rules, per 100 words.
- **Copy rate.** Share of output 8-grams found verbatim in the corpus. This is the memorization and plagiarism risk.
- **Topic similarity.** Embedding cosine (bge-small) between the task and the output.
- **Clean outputs.** No empty or degenerate repetitive generation.

| Condition | Style delta | Sentence-length gap | Violations / 100 words | Copy rate | Topic similarity | Clean |
|---|---|---|---|---|---|---|
| Author's own writing (reference) | 1.530 | 4.6 | | | | |
| Base model | 2.054 | 4.8 | 0.65 | 0.0% | 0.742 | 100% |
| System prompt (voice spec) | 2.041 | 11.6 | 0.30 | 0.0% | 0.703 | 100% |
| Retrieved own writing | **1.764** | 4.2 | 0.33 | 1.4% | 0.689 | 100% |
| System prompt + retrieval | 2.085 | **2.3** | 0.57 | 7.8% | 0.649 | 100% |
| LoRA adapter (`writer-voice-001`) | 2.165 | 3.4 | 0.38 | 0.0% | **0.754** | 100% |
| LoRA adapter + retrieval | 1.775 | 4.4 | **0.10** | 4.4% | 0.688 | 92% |

**Findings.**

1. **Retrieval moves style most.** Supplying four sections of the author's own writing closes 55% of the gap between the base model and the author (2.054 to 1.764, floor 1.530), at a 1.4% copy rate. It is the cheapest lever and it needs no training.
2. **The prompt follows the rules and breaks the brief.** The voice specification halves rule violations, yet answers fall to about 110 words against a 250-word request, and sentence length overshoots the author by 11.6 words. A rule that says "write long compound sentences" is obeyed too literally by a 3B model.
3. **Stacking prompt and retrieval is worse than retrieval alone.** Style delta returns to base level and the copy rate rises to 7.8%: the model copies the sources to satisfy the rules. One output still used a banned word.
4. **The adapter alone did not move style.** `writer-voice-001` (LoRA rank 8, 4 layers, 50 iterations) slightly worsens style delta, while keeping the best topic adherence. This agrees with the earlier decision to keep it unpromoted, and it shows a small adapter learns the format of the training examples more than the function-word habits of the author.
5. **Adapter plus retrieval is the strongest rule-follower** (0.10 violations per 100 words, near-best style), but one output in twelve degenerated into repetition. It is a candidate, not a default.

**Decision.** Ship retrieval as the default steering method for the Writer, keep the adapter behind the blind-comparison gate, and do not stack the voice prompt on retrieval. **Blind human review.** The author judged all 12 tasks blind, choosing which of three shuffled outputs (base, prompt + retrieval, adapter) sounded most like his own writing ([page](evals/study/blind-review.html), [result](evals/study/blind-review-result.json)):

| Condition | Wins | Style delta |
|---|---|---|
| Base model | 5 / 12 | 2.054 |
| System prompt + retrieval | 5 / 12 | 2.085 |
| LoRA adapter | 2 / 12 | 2.165 |

The human ranking matches the automatic style metric: the two conditions with near-equal style delta tie, and the adapter, with the worst delta, loses clearly. This is evidence that Burrows' Delta tracks what the author himself hears as his voice, so it can stand in for human review in future runs. It also reverses an earlier, shorter blind review that preferred the adapter 2 to 1, which is why one small review is never enough to promote a model. Retrieval alone, the best condition on the metric, was not in this review; it is the first condition to add in the next round.

**Limits.** 12 tasks is a small sample; differences under about 0.1 in style delta should not be read as real. Register violations are measured with the same rules the voice prompt states, so that metric favours the prompt condition. Topic similarity penalizes outputs that become specific (retrieval grounds answers in named cases), so a lower value is not always worse.

## Study 2: Agentic code repair (Qwen2.5-Coder 3B and 7B)

**Goal.** Measure what the harness around a model adds: context, and a loop that runs tests and returns failures.

**Method.** 8 small public bug-fix tasks ([`evals/study/code-tasks.json`](evals/study/code-tasks.json)). Each was verified so the buggy file fails its tests and a correct fix passes. The model returns a full replacement file, the real unit tests run, and the result is pass or fail. Three harnesses:

- **Request only.** One attempt, with no tests shown.
- **Request + tests.** One attempt, with the test file in context.
- **Agent loop.** Tests in context, and up to 3 attempts with the failure output fed back.

| Model | Request only | Request + tests | Agent loop (≤3 attempts) |
|---|---|---|---|
| Qwen2.5-Coder-3B | 1/8 | **5/8** | 5/8 |
| Qwen2.5-Coder-7B | 3/8 | 4/8 | **5/8** |

**Findings.**

1. **Context beats parameters.** Showing the tests raises the 3B model from 1/8 to 5/8. The 3B model with tests beats the 7B model without them (3/8), at a lower cost per task.
2. **Feedback helps only the larger model.** The 7B model fixed one more task (Roman numerals) on its second attempt, after reading the failure. The 3B model could not use the feedback and gained nothing.
3. **The tests are the specification.** The request text is vague on purpose ("Fix it"). Requirements that only the tests state, such as raising `ValueError` or handling ties, are the main reason the request-only condition fails.

**Decision.** For small local models, spend effort on context first (tests, specs, examples), and add a feedback loop when the model is large enough to use it.

## Where this lives in a product

[Keel](https://github.com/raastey/keel-app) turns these findings into interface: the Context Inspector shows what a model receives, the Context Lab compares the same request with and without context, and a trained adapter cannot be activated until quality checks and a blind comparison pass.
