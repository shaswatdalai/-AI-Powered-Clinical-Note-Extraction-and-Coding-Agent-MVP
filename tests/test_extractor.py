"""
Tests for the extractor.

These tests focus on the pure parts: span resolution and extraction
building. LLM calls are cached or mocked.
"""

from src.extractor import _resolve_span, _build_extraction
from src.schema import Span


def test_resolve_span_exact_match():
    note = "Patient has type 2 diabetes."
    span = _resolve_span(note, "type 2 diabetes")
    assert span is not None
    assert note[span.start:span.end] == "type 2 diabetes"


def test_resolve_span_returns_none_when_missing():
    note = "Patient has type 2 diabetes."
    span = _resolve_span(note, "hypertension")
    assert span is None


def test_resolve_span_empty_quote():
    note = "Patient has type 2 diabetes."
    span = _resolve_span(note, "")
    assert span is None


def test_resolve_span_whitespace_tolerant():
    note = "Patient has type 2 diabetes."
    # extra whitespace should still resolve
    span = _resolve_span(note, "type 2  diabetes")
    assert span is not None
    assert "diabetes" in note[span.start:span.end]


def test_build_extraction_resolves_spans():
    note = "Patient has type 2 diabetes. Taking Metformin 500 mg."
    raw = {
        "diagnoses": [
            {"name_as_written": "type 2 diabetes",
             "normalised_name": "type 2 diabetes mellitus",
             "status": "active",
             "evidence_quote": "type 2 diabetes"}
        ],
        "medications": [
            {"name": "Metformin", "dose": "500 mg", "status": "current",
             "evidence_quote": "Metformin 500 mg"}
        ],
        "procedures": [],
        "allergies": [],
        "vitals": [],
    }
    extraction = _build_extraction(raw, note)
    assert len(extraction.diagnoses) == 1
    assert extraction.diagnoses[0].evidence.span is not None
    assert note[extraction.diagnoses[0].evidence.span.start:
                extraction.diagnoses[0].evidence.span.end] == "type 2 diabetes"


def test_build_extraction_handles_empty():
    note = "Some note text."
    extraction = _build_extraction({}, note)
    assert extraction.diagnoses == []
    assert extraction.medications == []