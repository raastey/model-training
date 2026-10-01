# Writer conceptual relevance review

This is the human quality gate for the Writer working-context system. The title-to-source smoke test proves only that the index functions. It does not tell us whether the system selects the *right* source for a real conceptual request.

For each real writing task below, run:

```bash
.venv/bin/sixai context inspect writer "YOUR QUERY"
```

Then record the IDs of one or more sources that you judge genuinely useful in `docs/writer-relevance-cases.json`. The initial R1–R5 labels were chosen by a provisional system review at the user's direction; they are inspectable and replaceable. The Context Inspector now displays source IDs directly. Do not label a result merely because it shares a word with the prompt. A source should meaningfully help answer the request.

| Case | Real writing task | Relevant source IDs | Notes |
| --- | --- | --- | --- |
| R1 | Explain why evidence matters in public debate. |  |  |
| R2 | Write about the role of accountability in political power. |  |  |
| R3 | Explain how money influences democratic representation. |  |  |
| R4 | Draft a concise argument about narrative and public opinion. |  |  |
| R5 | Explain the human consequences of policy decisions. |  |  |

Promotion rule: before a replacement context adapter is trained, the hybrid retriever must retrieve at least one user-labeled relevant source in the top five for every completed case, and the resulting model must pass the no-repetition runtime gate.

After every `expected_document_ids` list contains at least one ID, run:

```bash
.venv/bin/sixai eval relevance writer
```
