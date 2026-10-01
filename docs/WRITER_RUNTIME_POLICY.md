# Writer runtime policy

The current reliable Writer runtime is:

```text
Qwen2.5-3B-Instruct base model + local Writer retrieval index + context-runtime gate
```

It is not a promoted personal adapter. It is the stable operational baseline while adapter training is improved.

Use it from the project directory:

```bash
.venv/bin/sixai context inspect writer "YOUR QUESTION"
.venv/bin/sixai context chat writer "YOUR QUESTION"
```

`context chat` defaults to the base model. This is intentional: no adapter has passed both the short operating profile and the longer stress profile.

| Adapter | Status | Reason |
| --- | --- | --- |
| `writer-smoke-001` | smoke only | Training-path proof; not a quality candidate. |
| `writer-chunked-001` | rejected for context use | Repetition on 2 of 5 reviewed context tasks. |
| `writer-context-001` | rejected | Severe looping under retrieved context. |
| `writer-context-002` | rejected | Empty completion under retrieved context. |
| `writer-voice-001` | conditional short-context trial | Passed 5/5 at 3k context / 220 tokens and won 2/3 blind voice prompts; failed one 400-token stress case. |

The context command runs an output gate. If an explicitly selected adapter gives an empty or repetitive result, it automatically retries with the base model unless `--no-fallback-base` is supplied. The fallback is announced in the terminal; it is never silent.

Promotion requires all of the following: passing human-labeled retrieval cases, passing every context-runtime case without fallback, a blind voice comparison, and a reviewed decision recorded in the implementation log.

For the constrained `writer-voice-001` trial only, use the explicit limits and retain automatic base fallback:

```bash
.venv/bin/sixai context chat writer "YOUR SPECIFIC WRITING TASK" -a writer-voice-001 --context-budget 3000 -n 220
```
