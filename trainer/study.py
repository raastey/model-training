"""Context-versus-weights study: one held-out task set, six conditions, repeatable metrics.

The same 3B base model is steered four ways (system prompt, retrieval, LoRA adapter, and
combinations). Every output is scored with metrics that need no remote judge, so any
reader can rerun the study on a Mac and get the same table.
"""

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from trainer.benchmarks import runtime_output_issue
from trainer.config import ProjectPaths
from trainer.context import retrieve_writer_context
from trainer.corpus import list_documents, writer_corpus_dir
from trainer.runtime import writer_context_prompt

TRAINING_SYSTEM = "You are SIXTWELVE Writer. Follow the user's editorial voice and preserve factual discipline."

VOICE_SPEC = (
    "You write analytical journalism in one specific house voice. Rules:\n"
    "1. Build each argument inside long compound sentences: accumulate evidence with 'and', pivot with "
    "'and yet', and land the conclusion at the end of the sentence. Do not write short staccato sentences.\n"
    "2. Never use em dashes.\n"
    "3. Never use these words: merely, mere, reveal, revealing, profound, underscore, stark, resonate, "
    "emerge, pattern, genuinely.\n"
    "4. No scaffolding phrases such as 'this is not X, it is Y', 'what follows is', or 'strip away'.\n"
    "5. No one-sentence paragraphs and no dramatic two-sentence endings.\n"
    "6. Be direct where the evidence supports it. Name institutions and mechanisms, not abstractions.\n"
    "7. Do not invent facts, quotations, or statistics."
)

BANNED_WORDS = ("merely", "mere", "reveal", "reveals", "revealed", "revealing", "profound", "profoundly",
                "underscore", "underscores", "stark", "starkly", "resonate", "resonates", "emerge", "emerges",
                "emerged", "pattern", "patterns", "genuinely")
SCAFFOLDING = (r"\bthis is not\b[^.]{0,80}\bit is\b", r"\bwhat follows is\b", r"\bstrip away\b",
               r"\bit'?s not just\b", r"\bin conclusion\b", r"\bin today'?s world\b")


@dataclass(frozen=True)
class Condition:
    id: str
    label: str
    system: str | None
    retrieval: bool
    adapter: bool


CONDITIONS = (
    Condition("base", "Base model", None, False, False),
    Condition("prompt", "System prompt (voice spec)", VOICE_SPEC, False, False),
    Condition("retrieval", "Retrieved own writing", None, True, False),
    Condition("prompt_retrieval", "System prompt + retrieval", VOICE_SPEC, True, False),
    Condition("adapter", "LoRA adapter", TRAINING_SYSTEM, False, True),
    Condition("adapter_retrieval", "LoRA adapter + retrieval", TRAINING_SYSTEM, True, True),
)

Generator = Callable[[str | None, str, bool], str]


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def _sentences(text: str) -> list[str]:
    return [part for part in re.split(r"(?<=[.!?])\s+", text.strip()) if len(part.split()) >= 3]


@dataclass(frozen=True)
class StyleProfile:
    """Burrows' Delta profile of the author's most frequent words across the corpus."""

    vocabulary: tuple[str, ...]
    means: tuple[float, ...]
    deviations: tuple[float, ...]
    mean_sentence_words: float
    corpus_ngrams: frozenset[int]

    def delta(self, text: str) -> float:
        counts = Counter(_words(text))
        total = max(sum(counts.values()), 1)
        return sum(abs((counts[word] / total - mean) / deviation)
                   for word, mean, deviation in zip(self.vocabulary, self.means, self.deviations, strict=True)) / len(self.vocabulary)

    def copy_rate(self, text: str, n: int = 8) -> float:
        """Share of output word 8-grams found verbatim in the author's corpus."""
        grams = _ngram_hashes(_words(text), n)
        return sum(gram in self.corpus_ngrams for gram in grams) / len(grams) if grams else 0.0


def _ngram_hashes(words: list[str], n: int = 8) -> list[int]:
    return [hash(" ".join(words[index:index + n])) for index in range(max(0, len(words) - n + 1))]


def build_style_profile(texts: list[str], vocabulary_size: int = 80) -> StyleProfile:
    frequencies = [Counter(_words(text)) for text in texts]
    totals = [max(sum(counts.values()), 1) for counts in frequencies]
    vocabulary = tuple(word for word, _ in sum(frequencies, Counter()).most_common(vocabulary_size))
    means, deviations = [], []
    for word in vocabulary:
        values = [counts[word] / total for counts, total in zip(frequencies, totals, strict=True)]
        mean = sum(values) / len(values)
        means.append(mean)
        deviations.append(math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) or 1e-9)
    sentence_lengths = [len(sentence.split()) for text in texts for sentence in _sentences(text)]
    ngrams = frozenset(gram for text in texts for gram in _ngram_hashes(_words(text)))
    return StyleProfile(vocabulary, tuple(means), tuple(deviations),
                        sum(sentence_lengths) / max(len(sentence_lengths), 1), ngrams)


def register_violations(text: str) -> int:
    lowered = text.lower()
    banned = sum(len(re.findall(rf"\b{word}\b", lowered)) for word in BANNED_WORDS)
    scaffolding = sum(len(re.findall(pattern, lowered)) for pattern in SCAFFOLDING)
    return text.count("—") + banned + scaffolding


def score_output(profile: StyleProfile, text: str) -> dict[str, object]:
    words = len(text.split())
    sentences = _sentences(text)
    mean_sentence = sum(len(sentence.split()) for sentence in sentences) / max(len(sentences), 1)
    return {
        "words": words,
        "issue": runtime_output_issue(text),
        "style_delta": round(profile.delta(text), 4),
        "sentence_gap": round(abs(mean_sentence - profile.mean_sentence_words), 2),
        "violations_per_100_words": round(100 * register_violations(text) / max(words, 1), 3),
        "copy_rate": round(profile.copy_rate(text), 4),
    }


def author_baseline(profile: StyleProfile, texts: list[str], words: int = 300, limit: int = 40) -> dict[str, float]:
    """Score 300-word excerpts of the author's own writing so model scores have a reference point."""
    deltas, gaps = [], []
    for text in texts[:limit]:
        excerpt = " ".join(text.split()[:words])
        deltas.append(profile.delta(excerpt))
        sentences = _sentences(excerpt)
        gaps.append(abs(sum(len(s.split()) for s in sentences) / max(len(sentences), 1) - profile.mean_sentence_words))
    return {"style_delta": round(sum(deltas) / len(deltas), 4), "sentence_gap": round(sum(gaps) / len(gaps), 2)}


def summarize(results: list[dict[str, object]]) -> dict[str, float]:
    count = len(results)
    def mean(key: str) -> float:
        return round(sum(float(item[key]) for item in results) / count, 4)
    return {
        "style_delta": mean("style_delta"),
        "sentence_gap": mean("sentence_gap"),
        "violations_per_100_words": mean("violations_per_100_words"),
        "copy_rate": mean("copy_rate"),
        "topic_similarity": mean("topic_similarity"),
        "clean_rate": round(sum(item["issue"] is None for item in results) / count, 4),
        "words": mean("words"),
    }


def load_tasks(path: Path) -> list[dict[str, str]]:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not tasks or not all(isinstance(t.get("id"), str) and isinstance(t.get("task"), str) for t in tasks):
        raise ValueError("Study tasks need string 'id' and 'task' fields.")
    return tasks


def author_texts(paths: ProjectPaths) -> list[str]:
    corpus_dir = writer_corpus_dir(paths)
    return [(corpus_dir / doc.storage_path).read_text(encoding="utf-8")
            for doc in sorted(list_documents(paths), key=lambda d: d.id) if doc.quality in {"gold", "good"}]


def mlx_generator(model_path: Path, adapter_path: Path, max_tokens: int = 450) -> Generator:
    """Load the base once and the adapter once; generation is seeded for repeatability."""
    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    loaded: dict[bool, tuple] = {}

    def run(system: str | None, user: str, adapter: bool) -> str:
        if adapter not in loaded:
            loaded[adapter] = load(str(model_path), adapter_path=str(adapter_path) if adapter else None)
        model, tokenizer = loaded[adapter]
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
        prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        mx.random.seed(2026)
        return generate(model, tokenizer, prompt, max_tokens=max_tokens, sampler=make_sampler(temp=0.3)).strip()

    return run


def run_writer_study(
    paths: ProjectPaths, tasks: list[dict[str, str]], generator: Generator,
    embed: Callable[[list[str]], list[list[float]]], conditions: tuple[Condition, ...] = CONDITIONS,
    retrieve: Callable[[str], list] | None = None,
) -> dict[str, object]:
    texts = author_texts(paths)
    profile = build_style_profile(texts)
    retrieve = retrieve or (lambda query: retrieve_writer_context(paths, query, limit=4, budget_characters=6000))
    retrieved = {task["id"]: retrieve(task["task"]) for task in tasks}
    task_vectors = dict(zip((t["id"] for t in tasks), embed([t["task"] for t in tasks]), strict=True))
    report_conditions = []
    for condition in conditions:
        results = []
        for task in tasks:
            user = writer_context_prompt(task["task"], retrieved[task["id"]]) if condition.retrieval else task["task"]
            output = generator(condition.system, user, condition.adapter)
            scored = score_output(profile, output)
            scored["topic_similarity"] = round(_cosine(task_vectors[task["id"]], embed([output])[0]), 4) if output else 0.0
            results.append({"id": task["id"], **scored, "output": output})
        report_conditions.append({"id": condition.id, "label": condition.label, "summary": summarize(results), "results": results})
    return {
        "kind": "writer_context_vs_weights_study",
        "author_baseline": author_baseline(profile, texts),
        "corpus_documents": len(texts),
        "tasks": tasks,
        "conditions": report_conditions,
    }


def _cosine(a: list[float], b: list[float]) -> float:
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0


def markdown_table(report: dict[str, object]) -> str:
    baseline = report["author_baseline"]
    lines = [
        "| Condition | Style delta (lower = closer to author) | Sentence-length gap | Register violations / 100 words | Copy rate (8-gram) | Topic similarity | Clean outputs |",
        "|---|---|---|---|---|---|---|",
        f"| Author's own writing (reference) | {baseline['style_delta']:.3f} | {baseline['sentence_gap']:.1f} | n/a | n/a | n/a | n/a |",
    ]
    for condition in report["conditions"]:
        s = condition["summary"]
        lines.append(
            f"| {condition['label']} | {s['style_delta']:.3f} | {s['sentence_gap']:.1f} | {s['violations_per_100_words']:.2f} "
            f"| {100 * s['copy_rate']:.1f}% | {s['topic_similarity']:.3f} | {100 * s['clean_rate']:.0f}% |"
        )
    return "\n".join(lines) + "\n"


BLIND_CONDITIONS = ("base", "prompt_retrieval", "adapter")


def build_blind_review(report: dict[str, object], seed: int = 2026) -> tuple[str, dict[str, dict[str, str]]]:
    """Return a self-contained review page and the hidden slot-to-condition key."""
    rng = random.Random(seed)
    by_condition = {c["id"]: {r["id"]: r["output"] for r in c["results"]} for c in report["conditions"]}
    items, key = [], {}
    for task in report["tasks"]:
        order = list(BLIND_CONDITIONS)
        rng.shuffle(order)
        key[task["id"]] = {slot: condition for slot, condition in zip("ABC", order, strict=True)}
        items.append({"id": task["id"], "task": task["task"],
                      "options": [{"slot": slot, "text": by_condition[condition][task["id"]]} for slot, condition in zip("ABC", order, strict=True)]})
    page = BLIND_PAGE.replace("__ITEMS__", json.dumps(items).replace("</", "<\\/"))
    return page, key


def score_blind_review(choices: dict[str, str], key: dict[str, dict[str, str]]) -> dict[str, object]:
    wins = Counter(key[task_id][slot] for task_id, slot in choices.items() if task_id in key and slot in key[task_id])
    judged = sum(wins.values())
    return {"judged": judged, "wins": {c: wins.get(c, 0) for c in BLIND_CONDITIONS},
            "win_rate": {c: round(wins.get(c, 0) / judged, 3) if judged else 0.0 for c in BLIND_CONDITIONS}}


BLIND_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blind voice review</title>
<style>
:root{--bg:#f7f6f2;--card:#fff;--text:#1d1d1b;--muted:#6b6a65;--line:#dedcd5;--accent:#1f5f8b}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#22221f;--text:#ecebe6;--muted:#a3a29b;--line:#3a3935;--accent:#7cb4dc}}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 -apple-system,system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 80px}h1{font-size:22px;margin:0 0 4px}.muted{color:var(--muted)}
.task{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:20px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-top:12px}
.opt{border:1px solid var(--line);border-radius:8px;padding:12px;white-space:pre-wrap;font-family:Georgia,serif;font-size:15px}
.opt.chosen{outline:3px solid var(--accent)}button{font:inherit;padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--text);cursor:pointer;margin-top:8px}
.bar{position:sticky;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:12px 16px;display:flex;gap:12px;align-items:center}
</style></head><body><main>
<h1>Blind voice review</h1>
<p class="muted">For each task, choose the answer that sounds most like your own writing. Labels are shuffled. When you finish, choose Download results.</p>
<div id="items"></div></main>
<div class="bar"><span id="count"></span><button id="download">Download results</button></div>
<script>
const items=__ITEMS__;const choices={};
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
document.getElementById('items').innerHTML=items.map(i=>`<section class="task"><strong>${i.id}</strong> <span class="muted">${esc(i.task)}</span><div class="grid">${i.options.map(o=>`<div class="opt" data-task="${i.id}" data-slot="${o.slot}"><strong>${o.slot}</strong>\\n${esc(o.text)}<br><button>Choose ${o.slot}</button></div>`).join('')}</div></section>`).join('');
const update=()=>{document.getElementById('count').textContent=`${Object.keys(choices).length} of ${items.length} chosen`;document.querySelectorAll('.opt').forEach(n=>n.classList.toggle('chosen',choices[n.dataset.task]===n.dataset.slot))};
document.querySelectorAll('.opt button').forEach(b=>b.onclick=()=>{const n=b.parentElement;choices[n.dataset.task]=n.dataset.slot;update()});
document.getElementById('download').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(choices,null,2)],{type:'application/json'}));a.download='blind-choices.json';a.click()};
update();
</script></body></html>
"""
