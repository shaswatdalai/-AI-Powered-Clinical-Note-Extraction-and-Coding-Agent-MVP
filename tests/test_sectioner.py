"""
Tests for the sectioner.

These tests prove that:
- Notes without headings produce a single UNSECTIONED section.
- Notes with headings produce one section per heading.
- Section offsets are correct — slicing the note with the offsets
  returns the expected body text.
- Sections are ordered by their position in the note.
- Empty or whitespace-only notes don't crash.
"""

from src.sectioner import section_note


# -----------------------------------------------------------------------------
# Happy path — headings
# -----------------------------------------------------------------------------

def test_finds_medications_section():
    note = "Chief Complaint: cough\n\nMedications: metformin 500 mg"
    sections = section_note(note)
    names = [s["name"] for s in sections]
    assert "Medications" in names
    assert "Chief Complaint" in names


def test_offsets_slice_correctly():
    note = "Chief Complaint: cough\nMedications: metformin 500 mg\nPlan: rest"
    sections = section_note(note)

    med = next(s for s in sections if s["name"] == "Medications")
    body = note[med["start"]:med["end"]]
    assert body == "metformin 500 mg"


def test_sections_are_in_note_order():
    note = "Medications: metformin\nPlan: rest\nAllergies: none"
    sections = section_note(note)
    starts = [s["start"] for s in sections]
    assert starts == sorted(starts)


def test_handles_common_abbreviations():
    # Note: "CC" and "PE" are intentionally NOT included as patterns because
    # they false-match inside ordinary prose. This test only covers the
    # multi-character medical abbreviations.
    note = "HPI: 3 days\nA&P: viral URI\nROS: negative"
    sections = section_note(note)
    names = [s["name"] for s in sections]
    assert "History of Present Illness" in names
    assert "Assessment and Plan" in names
    assert "Review of Systems" in names


# -----------------------------------------------------------------------------
# No headings
# -----------------------------------------------------------------------------

def test_unsectioned_note_returns_single_section():
    note = "Patient is a 58-year-old male with diabetes."
    sections = section_note(note)
    assert len(sections) == 1
    assert sections[0]["name"] == "UNSECTIONED"
    assert sections[0]["start"] == 0
    assert sections[0]["end"] == len(note)


# -----------------------------------------------------------------------------
# Edge cases
# -----------------------------------------------------------------------------

def test_empty_note_does_not_crash():
    sections = section_note("")
    assert len(sections) == 1
    assert sections[0]["name"] == "UNSECTIONED"


def test_whitespace_only_note_does_not_crash():
    sections = section_note("   \n\n   ")
    assert len(sections) == 1
    assert sections[0]["name"] == "UNSECTIONED"


def test_heading_with_empty_body_is_skipped():
    note = "Chief Complaint:\n\nMedications: metformin"
    sections = section_note(note)
    names = [s["name"] for s in sections]
    # Chief Complaint has no body, so it should not appear
    assert "Chief Complaint" not in names
    assert "Medications" in names