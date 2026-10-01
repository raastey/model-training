# Testing the local training lab

Run all commands from the `model-training` directory. They operate only on your local files.

## After any code change

```bash
bash scripts/test.sh
```

This runs the synthetic test suite and the non-mutating environment diagnostic. A passing test run should never print your Hugging Face token or corpus content.

## Inspect the Writer corpus

```bash
.venv/bin/sixai corpus list writer
```

This prints each document's ID, quality label, word count, and title. To change a label:

```bash
.venv/bin/sixai corpus label writer DOCUMENT_ID gold
```

## Build and validate a dataset

The current dataset is already built as `v1`. Validate it any time:

```bash
.venv/bin/sixai dataset validate writer --name v1
```

To build a new immutable dataset after corpus changes, use a new name:

```bash
.venv/bin/sixai dataset build writer --name v2
.venv/bin/sixai dataset validate writer --name v2
```

For training, use section-sized examples rather than full articles:

```bash
.venv/bin/sixai dataset build writer --name v2 --chunk-characters 5000
```

To include explicit Writer context-management examples, use:

```bash
.venv/bin/sixai dataset build writer --name v3 --chunk-characters 3000 --context-tasks
```

The builder refuses to overwrite an existing dataset. It validates chat structure, secret absence, provenance metadata, source/split isolation, and split-file counts before reporting success.

## Test the local Writer base model

```bash
.venv/bin/sixai model status writer
.venv/bin/sixai chat writer "In one sentence, explain what a thesis is." --max-tokens 80
```

The second command performs local GPU inference. It uses the downloaded base model only; it does not yet use a trained personal adapter.

## Smoke training

The first training run is deliberately tiny and never promotes an adapter:

```bash
.venv/bin/sixai train smoke writer
```

It stages immutable MLX-compatible `train.jsonl`, `valid.jsonl`, and `test.jsonl` files under `runs/`, trains only 4 layers for 10 steps, evaluates one test batch, and writes its adapter under `adapters/`. Do not interrupt it unless you want to abandon this candidate run.

Compare the base and a candidate adapter with the same prompt:

```bash
.venv/bin/sixai chat writer "Explain why a thesis matters." --max-tokens 80
.venv/bin/sixai chat writer "Explain why a thesis matters." --max-tokens 80 -a writer-smoke-001
```

`writer-smoke-001` is only a training-path check, not a promoted personal model.

## First section-sized candidate

After `v2` has been built and validated, start the initial chunked candidate:

```bash
.venv/bin/sixai train chunked writer
```

This is a distinct 100-step candidate with 8 trainable layers. It does not alter `writer-smoke-001`, the base model, or a promoted model.

## First context-aware candidate

```bash
.venv/bin/sixai train context writer
```

This distinct 150-step candidate uses `v3`: voice supervision plus explicit continuation, working-state, supersession, and non-repetition tasks. It teaches context behavior, but a future live retrieval/state engine still supplies the current facts at runtime.

`writer-context-001` was rejected for severe repetition. The replacement uses a rebalanced all-library v5 curriculum, so first build it and then start its distinct run:

```bash
.venv/bin/sixai dataset build writer --name v5 --chunk-characters 3000 --context-tasks --context-profile balanced
.venv/bin/sixai train context writer
```

## Local Writer context retrieval

```bash
.venv/bin/sixai context build-index writer
.venv/bin/sixai context inspect writer "Why does evidence matter in public debate?"
```

This indexes only the Writer corpus and displays selected source titles, sections, matched terms, and hybrid lexical/semantic relevance scores. It abstains rather than injecting context when the query has insufficient overlap. It does not send your writing anywhere or involve the Code corpus.

Use selected context with the context-aware candidate:

```bash
.venv/bin/sixai context chat writer "Write a short argument about evidence in public debate." -a writer-context-001
```

Run `context inspect` with the same query first whenever you want to see exactly what was supplied to the model.

For a short answer, keep the request explicit and set a bound when needed:

```bash
.venv/bin/sixai context chat writer "Write one concise paragraph about why evidence matters." -n 120
```

`X` is only a placeholder. Context chat now declines generic requests rather than retrieving unrelated writing; replace it with a real topic such as `why evidence matters`.

When a token limit would end midway through a sentence, Context Chat removes only that unfinished final fragment and tells you it did so.

For a true short final answer, add the word-budget option (it keeps complete sentences only):

```bash
.venv/bin/sixai context chat writer "Write one concise paragraph about why evidence matters in public debate." -n 160 -w 60
```

The stable context runtime currently uses the base model. See `docs/WRITER_RUNTIME_POLICY.md` for the evaluated adapter status and the explicit fallback behavior.

## Repetition gate

Copy a model response into this command before considering it for promotion:

```bash
.venv/bin/sixai eval repetition "MODEL RESPONSE HERE"
```

A repeated 5-gram ratio above `0.10`, or an empty model completion, requires review and blocks promotion until the cause is understood.

## Retrieval infrastructure smoke test

```bash
.venv/bin/sixai eval retrieval-smoke writer --cases 10
```

This checks whether ten Writer documents can be retrieved from their own titles and saves the local report under `evals/writer/`. It verifies that the index is functioning; it does **not** prove that a conceptual question receives the best source. Human-labeled relevance cases are still required before retraining context behavior.

## Full context-runtime evaluation

```bash
.venv/bin/sixai eval context-runtime writer
.venv/bin/sixai eval context-runtime writer --candidate writer-chunked-001
.venv/bin/sixai eval context-runtime writer --candidate writer-voice-001 --context-budget 3000 -n 220
```

The first command evaluates the base model; the second evaluates an adapter. Each runs all reviewed relevance tasks and blocks a pass for empty or repeated outputs. The report records only case IDs, output lengths, source IDs, and gate results—not generated prose.

## Context-budget diagnosis

```bash
.venv/bin/sixai eval context-ablation writer --candidate writer-chunked-001
```

This local diagnostic evaluates the same adapter at 3,000, 6,000, and 9,000 context characters. It does not promote an adapter; it identifies whether source-package size changes runtime reliability.

## Authentic-prose voice candidate

```bash
.venv/bin/sixai dataset build writer --name v6 --chunk-characters 3000
.venv/bin/sixai train voice writer
```

This distinct candidate uses only authentic Writer prose from all approved libraries, with 4 trainable layers and 50 steps. It is a controlled response to the context-adapter failures, not a promotion.

## Blind comparison

```bash
.venv/bin/sixai eval blind writer --candidate writer-chunked-001
```

Open the reported `blind-review.md` and choose A or B for each prompt before reading the private mapping file. A candidate is not promoted from automated checks alone.
