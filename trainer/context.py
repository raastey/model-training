"""Local lexical retrieval and inspectable Writer working-context packages."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from trainer.config import ProjectPaths
from trainer.corpus import list_documents, writer_corpus_dir
from trainer.dataset import chunk_writer_text

INDEX_VERSION = 1
STOPWORDS = {"a", "about", "an", "and", "answer", "are", "as", "at", "be", "by", "concise", "does", "direct", "draft", "explain", "for", "from", "how", "in", "is", "it", "matter", "matters", "of", "on", "one", "opening", "or", "paragraph", "public", "short", "something", "that", "the", "this", "to", "topic", "what", "why", "with", "write"}


@dataclass(frozen=True)
class ContextChunk:
    id: str
    document_id: str
    title: str
    section_number: int
    text: str


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: ContextChunk
    score: float
    matched_terms: tuple[str, ...]
    semantic_score: float = 0.0


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z]{3,}", text.lower()) if token not in STOPWORDS]


def writer_index_path(paths: ProjectPaths) -> Path:
    return paths.root / "context" / "indexes" / "writer-v1.json"


def _embedding_model_path(paths: ProjectPaths) -> Path:
    return paths.root / "models" / "embeddings" / "bge-small-en-v1.5-4bit"


@lru_cache(maxsize=2)
def _embedding_runtime(model_path: str):
    from mlx_embeddings import generate, load

    model, tokenizer = load(model_path)
    return model, tokenizer, generate


def _embed_texts(paths: ProjectPaths, texts: list[str]) -> list[list[float]]:
    """Embed locally, reusing the loaded embedding model within one CLI run."""
    model, tokenizer, generate = _embedding_runtime(str(_embedding_model_path(paths)))
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 32):
        output = generate(model, tokenizer, texts[start:start + 32]).text_embeds
        vectors.extend(output.tolist())
    return vectors


def build_writer_index(paths: ProjectPaths, chunk_characters: int = 3000, use_semantic: bool = False) -> int:
    """Index only explicit Writer training/retrieval material; never Code content."""
    chunks: list[ContextChunk] = []
    corpus_dir = writer_corpus_dir(paths)
    for document in list_documents(paths):
        if document.quality not in {"gold", "good", "reference_only"}:
            continue
        text = (corpus_dir / document.storage_path).read_text(encoding="utf-8")
        for section_number, chunk in enumerate(chunk_writer_text(text, chunk_characters), start=1):
            chunks.append(ContextChunk(f"{document.id}:{section_number}", document.id, document.title, section_number, chunk))
    index_path = writer_index_path(paths)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    semantic_vectors: dict[str, list[float]] = {}
    if use_semantic:
        if not (_embedding_model_path(paths) / "model.safetensors").is_file():
            raise ValueError("Local embedding model is missing.")
        semantic_vectors = dict(zip((chunk.id for chunk in chunks), _embed_texts(paths, [chunk.text for chunk in chunks]), strict=True))
    index_path.write_text(
        json.dumps({"version": INDEX_VERSION, "space": "writer", "chunks": [asdict(chunk) for chunk in chunks], "semantic_vectors": semantic_vectors}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return len(chunks)


def retrieve_writer_context(paths: ProjectPaths, query: str, limit: int = 5, budget_characters: int = 9000) -> list[RetrievedChunk]:
    index_path = writer_index_path(paths)
    if not index_path.is_file():
        raise ValueError("Writer context index is missing. Run: sixai context build-index writer")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("space") != "writer":
        raise ValueError("Context index namespace is invalid.")
    query_terms = set(_tokens(query))
    if not query_terms:
        return []
    all_chunks = [ContextChunk(**value) for value in index["chunks"]]
    term_counts = [Counter(_tokens(chunk.title + " " + chunk.text)) for chunk in all_chunks]
    document_frequency = Counter(term for counts in term_counts for term in counts)
    average_length = sum(sum(counts.values()) for counts in term_counts) / max(len(term_counts), 1)
    query_vector: list[float] | None = None
    if index.get("semantic_vectors"):
        query_vector = _embed_texts(paths, [query])[0]
    ranked: list[RetrievedChunk] = []
    for chunk, counts in zip(all_chunks, term_counts, strict=True):
        matched = tuple(sorted(query_terms & set(counts)))
        semantic_score = sum(a * b for a, b in zip(query_vector, index.get("semantic_vectors", {}).get(chunk.id, []), strict=True)) if query_vector else 0.0
        length = sum(counts.values())
        score = 0.0
        for term in matched:
            idf = math.log(1 + (len(all_chunks) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            score += idf * (counts[term] * 2.2) / (counts[term] + 1.2 * (1 - 0.75 + 0.75 * length / average_length))
        if len(matched) >= 2 or semantic_score >= 0.55:
            ranked.append(RetrievedChunk(chunk, score / 10 + semantic_score, matched, semantic_score))
    selected: list[RetrievedChunk] = []
    used = 0
    for item in sorted(ranked, key=lambda result: (-result.score, result.chunk.id)):
        if len(selected) >= limit or used + len(item.chunk.text) > budget_characters:
            continue
        selected.append(item)
        used += len(item.chunk.text)
    return selected


def format_working_context(query: str, retrieved: list[RetrievedChunk]) -> str:
    sources = "\n\n".join(
        f"[Source {index}: {item.chunk.title}, section {item.chunk.section_number}]\n{item.chunk.text}"
        for index, item in enumerate(retrieved, start=1)
    )
    return (
        "Working context for a Writer task. Use only relevant supplied material; preserve source uncertainty and do not invent missing facts.\n\n"
        f"Objective: {query}\n\nRetrieved sources:\n{sources}"
    )
