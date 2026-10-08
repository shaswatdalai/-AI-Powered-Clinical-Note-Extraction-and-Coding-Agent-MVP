"""Tests for the injection shield."""

from src.guardrails import wrap_note, strip_delimiters


def test_wrap_adds_delimiters():
    wrapped = wrap_note("hello world")
    assert "<<<BEGIN_NOTE>>>" in wrapped
    assert "<<<END_NOTE>>>" in wrapped
    assert "hello world" in wrapped


def test_strip_recovers_original():
    original = "Patient has diabetes."
    wrapped = wrap_note(original)
    recovered = strip_delimiters(wrapped)
    assert recovered == original


def test_strip_on_unwrapped_text_returns_input():
    text = "just a plain string"
    assert strip_delimiters(text) == text


def test_strip_handles_multiline():
    original = "Chief Complaint: cough\n\nMedications: metformin"
    wrapped = wrap_note(original)
    recovered = strip_delimiters(wrapped)
    assert recovered == original