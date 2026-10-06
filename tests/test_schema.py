"""
Tests for the extraction schema.

These tests prove that:
- Valid data parses successfully.
- Invalid statuses are rejected.
- Optional fields behave as expected.
- JSON round-trips work.
- Bad types are caught by Pydantic.
"""

import pytest
from pydantic import ValidationError

from src.schema import (
    Span,
    Evidence,
    Diagnosis,
    Medication,
    Extraction,
    Verdict,
    VerifierResponse,
)


# -----------------------------------------------------------------------------
# Span
# -----------------------------------------------------------------------------

def test_span_accepts_valid_offsets():
    s = Span(start=10, end=20)
    assert s.start == 10
    assert s.end == 20


def test_span_rejects_negative_start():
    with pytest.raises(ValidationError):
        Span(start=-1, end=20)


def test_span_rejects_zero_end():
    with pytest.raises(ValidationError):
        Span(start=0, end=0)


# -----------------------------------------------------------------------------
# Evidence
# -----------------------------------------------------------------------------

def test_evidence_requires_quote():
    with pytest.raises(ValidationError):
        Evidence()   # quote is required


def test_evidence_span_defaults_to_none():
    e = Evidence(quote="type 2 diabetes")
    assert e.span is None


def test_evidence_accepts_span():
    e = Evidence(quote="type 2 diabetes", span=Span(start=12, end=27))
    assert e.span.start == 12
    assert e.span.end == 27


# -----------------------------------------------------------------------------
# Diagnosis
# -----------------------------------------------------------------------------

def test_diagnosis_accepts_valid_input():
    d = Diagnosis(
        name_as_written="type 2 diabetes",
        normalised_name="type 2 diabetes mellitus",
        status="active",
        evidence=Evidence(quote="type 2 diabetes"),
    )
    assert d.status == "active"
    assert d.icd_candidates == []   # defaults to empty list


def test_diagnosis_rejects_bad_status():
    with pytest.raises(ValidationError):
        Diagnosis(
            name_as_written="x",
            normalised_name="x",
            status="ongoing",   # not in the Literal union
            evidence=Evidence(quote="x"),
        )


def test_diagnosis_lists_are_isolated_between_instances():
    d1 = Diagnosis(
        name_as_written="a", normalised_name="a", status="active",
        evidence=Evidence(quote="a"),
    )
    d2 = Diagnosis(
        name_as_written="b", normalised_name="b", status="active",
        evidence=Evidence(quote="b"),
    )
    d1.icd_candidates.append({"code": "E11.9"})
    assert d2.icd_candidates == []   # not shared


# -----------------------------------------------------------------------------
# Medication
# -----------------------------------------------------------------------------

def test_medication_optional_fields_default_to_none():
    m = Medication(
        name="Metformin",
        status="current",
        evidence=Evidence(quote="Metformin 500 mg twice daily"),
    )
    assert m.dose is None
    assert m.route is None
    assert m.frequency is None


def test_medication_rejects_bad_status():
    with pytest.raises(ValidationError):
        Medication(
            name="X", status="stopped",   # not allowed
            evidence=Evidence(quote="X"),
        )


# -----------------------------------------------------------------------------
# Extraction
# -----------------------------------------------------------------------------

def test_extraction_empty_is_valid():
    e = Extraction()
    assert e.diagnoses == []
    assert e.medications == []


def test_extraction_parses_from_json_string():
    raw = (
        '{"diagnoses": [{"name_as_written": "flu", '
        '"normalised_name": "influenza", "status": "active", '
        '"evidence": {"quote": "flu"}}]}'
    )
    e = Extraction.model_validate_json(raw)
    assert len(e.diagnoses) == 1
    assert e.diagnoses[0].name_as_written == "flu"


def test_extraction_roundtrips_through_json():
    original = Extraction(
        diagnoses=[
            Diagnosis(
                name_as_written="type 2 diabetes",
                normalised_name="type 2 diabetes mellitus",
                status="active",
                evidence=Evidence(quote="type 2 diabetes", span=Span(start=12, end=27)),
            )
        ],
    )
    dumped = original.model_dump_json()
    reparsed = Extraction.model_validate_json(dumped)
    assert reparsed.diagnoses[0].name_as_written == "type 2 diabetes"
    assert reparsed.diagnoses[0].evidence.span.start == 12


# -----------------------------------------------------------------------------
# VerifierResponse
# -----------------------------------------------------------------------------

def test_verifier_response_accepts_empty():
    vr = VerifierResponse()
    assert vr.verdicts == []
    assert vr.contradictions == []
    assert vr.missed_items == []


def test_verifier_response_parses_supported_verdict():
    raw = (
        '{"verdicts": [{"id": "d1", "verdict": "SUPPORTED", '
        '"status_correct": true, "icd_fit": "good", "reason": "ok"}]}'
    )
    vr = VerifierResponse.model_validate_json(raw)
    assert len(vr.verdicts) == 1
    assert vr.verdicts[0].verdict == "SUPPORTED"


def test_verifier_rejects_bad_icd_fit():
    with pytest.raises(ValidationError):
        Verdict(
            id="d1", verdict="SUPPORTED", status_correct=True,
            icd_fit="maybe", reason="x",
        )