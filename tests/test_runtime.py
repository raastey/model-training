from trainer.context import ContextChunk, RetrievedChunk
from trainer.runtime import (
    complete_sentences_for_display,
    evaluate_context_output,
    fit_complete_sentences_to_words,
    writer_context_prompt,
)


def test_context_runtime_rejects_empty_output() -> None:
    assert evaluate_context_output("", []).issue == "EMPTY"


def test_context_prompt_requires_answer_only_source_discipline() -> None:
    chunk = ContextChunk("writer-1:1", "writer-1", "Evidence", 1, "Evidence makes claims testable.")
    prompt = writer_context_prompt("Why evidence?", [RetrievedChunk(chunk, 1.0, ("evidence",))])
    assert "Do not mention this working context" in prompt
    assert "requested format and length exactly" in prompt
    assert "begin with the general claim" in prompt
    assert "Evidence makes claims testable." in prompt


def test_complete_sentences_for_display_drops_only_a_trailing_fragment() -> None:
    assert complete_sentences_for_display("Evidence matters. It keeps") == "Evidence matters."
    assert complete_sentences_for_display("Evidence matters.") == "Evidence matters."


def test_fit_complete_sentences_to_words_respects_budget() -> None:
    output = "Evidence makes claims testable. It lets people assess public power."
    assert fit_complete_sentences_to_words(output, 5) == "Evidence makes claims testable."
