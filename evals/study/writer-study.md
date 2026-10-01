| Condition | Style delta (lower = closer to author) | Sentence-length gap | Register violations / 100 words | Copy rate (8-gram) | Topic similarity | Clean outputs |
|---|---|---|---|---|---|---|
| Author's own writing (reference) | 1.530 | 4.6 | n/a | n/a | n/a | n/a |
| Base model | 2.054 | 4.8 | 0.65 | 0.0% | 0.742 | 100% |
| System prompt (voice spec) | 2.041 | 11.6 | 0.30 | 0.0% | 0.703 | 100% |
| Retrieved own writing | 1.764 | 4.2 | 0.33 | 1.4% | 0.689 | 100% |
| System prompt + retrieval | 2.085 | 2.3 | 0.57 | 7.8% | 0.649 | 100% |
| LoRA adapter | 2.165 | 3.4 | 0.38 | 0.0% | 0.754 | 100% |
| LoRA adapter + retrieval | 1.775 | 4.4 | 0.10 | 4.4% | 0.688 | 92% |
