"""Small, verified synthetic repair curriculum; independent of held-out evaluation tasks."""

from __future__ import annotations

import json

from trainer.code import code_dataset_dir, validate_code_dataset
from trainer.config import ProjectPaths


def _episode(index: int) -> dict[str, object]:
    threshold = 10 + index
    correct = (
        "def discounted_total(subtotal: float) -> float:\n"
        f"    return subtotal * 0.9 if subtotal >= {threshold} else subtotal\n"
    )
    broken = (
        "def discounted_total(subtotal: float) -> float:\n"
        f"    return subtotal * 0.9 if subtotal > {threshold} else subtotal\n"
    )
    test = (
        "import unittest\nfrom pricing import discounted_total\n\n"
        "class PricingTests(unittest.TestCase):\n"
        f"    def test_discount_at_threshold(self):\n        self.assertEqual(discounted_total({threshold}), {threshold * .9})\n"
        f"    def test_keeps_lower_amount(self):\n        self.assertEqual(discounted_total({threshold - 1}), {threshold - 1})\n"
    )
    prompt = (
        "Fix the bug in this existing Python module. Preserve its public function name and type signature. "
        "Return only the complete replacement contents of pricing.py. Use the existing test as the behavioral contract.\n\n"
        f"Existing pricing.py:\n{broken}\nExisting pricing_test.py:\n{test}"
    )
    return {"messages": [
        {"role": "system", "content": "You are SIXTWELVE Code. Return only the complete requested replacement file. Preserve public names and types."},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": correct},
    ]}


def build_repair_curriculum(paths: ProjectPaths, name: str = "v7", episodes: int = 120) -> dict[str, int]:
    """Create a token-safe, test-guided repair-only dataset, separate from evaluation."""
    output = code_dataset_dir(paths, name)
    if output.exists():
        raise ValueError(f"Dataset output already exists: {output}")
    if episodes < 30:
        raise ValueError("Repair curriculum requires at least 30 independent episodes.")
    from transformers import AutoTokenizer

    from trainer.models import code_model
    tokenizer = AutoTokenizer.from_pretrained(code_model(paths).path)
    rows = {"train": [], "validation": [], "test": []}
    metadata = []
    for index in range(episodes):
        row = _episode(index)
        rendered = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False)
        tokens = len(tokenizer.encode(rendered, add_special_tokens=False))
        if tokens > 1800:
            raise ValueError(f"Synthetic repair episode exceeded token limit: {index}")
        split = "test" if index % 10 == 0 else "validation" if index % 10 == 1 else "train"
        rows[split].append(row)
        metadata.append({"id": f"repair-boundary-{index:03d}", "project": f"synthetic-repair-{index:03d}", "language": "py", "split": split, "kind": "verified-test-guided-repair", "test_source_id": f"synthetic-test-{index:03d}", "tokens": tokens})
    output.mkdir(parents=True)
    for split, items in rows.items():
        (output / f"{split}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in items), encoding="utf-8")
    manifest = {"schema_version": 5, "space": "code", "dataset_name": name, "profile": "repair-first-synthetic-boundary", "split_counts": {key: len(value) for key, value in rows.items()}, "languages": {"py": episodes}, "projects": {item["project"]: 1 for item in metadata}, "examples": metadata, "held_out_projects": [], "minimum_test_contract_examples": episodes, "test_contract_examples": episodes, "synthetic": True, "max_training_tokens": 1800, "source_artifacts_retained": False}
    (output / "dataset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_code_dataset(output)
    return manifest["split_counts"]
