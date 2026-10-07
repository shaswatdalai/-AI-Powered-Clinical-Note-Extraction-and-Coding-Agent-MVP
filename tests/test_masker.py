"""
Tests for the PII masker.

These tests prove that:
- Masked text is the same length as the original.
- Masking doesn't shift character offsets.
- Structured PII (dates, IDs, phone numbers) is masked.
- Names and locations (via spaCy) are masked.
- An empty note doesn't crash.
"""

from src.masker import mask_pii


def test_masked_length_equals_original():
    note = "Patient John Smith visited on 12/03/1965."
    masked, _ = mask_pii(note)
    assert len(masked) == len(note)


def test_date_is_masked():
    note = "Visit date: 12/03/1965."
    masked, entries = mask_pii(note)
    assert "12/03/1965" not in masked
    assert any(e["type"] == "DATE" for e in entries)


def test_mrn_is_masked():
    note = "Patient MRN-1234567 admitted today."
    masked, entries = mask_pii(note)
    assert "MRN-1234567" not in masked
    assert any(e["type"] == "ID" for e in entries)


def test_phone_is_masked():
    note = "Contact: 555-123-4567 for follow-up."
    masked, entries = mask_pii(note)
    assert "555-123-4567" not in masked
    assert any(e["type"] == "PHONE" for e in entries)


def test_person_name_is_masked():
    note = "Patient Sarah Johnson reports chest pain."
    masked, entries = mask_pii(note)
    # spaCy should catch "Sarah Johnson"
    assert "Sarah Johnson" not in masked


def test_masking_preserves_offsets():
    note = "Patient John Smith visited."
    masked, entries = mask_pii(note)
    # Every entry's span should still slice to same-length text in masked
    for e in entries:
        assert len(masked[e["start"]:e["end"]]) == len(e["original"])


def test_empty_note_does_not_crash():
    masked, entries = mask_pii("")
    assert masked == ""
    assert entries == []


def test_whitespace_only_note():
    masked, entries = mask_pii("   \n\n   ")
    assert len(masked) == len("   \n\n   ")