"""
Section detection for clinical notes.

A clinical note is usually divided into sections with headings
(Chief Complaint, Medications, Plan, etc). This module finds those
sections and returns their character offsets.

If no headings are found, the entire note is returned as one
section named "UNSECTIONED".

Design rules:
- Section bodies are recorded as [start, end) offsets into the note.
- The start of a section body is the position immediately AFTER the heading's colon.
- Section ordering in the output matches the order in the note.
"""

# Known limitations:
# - Only recognizes a fixed set of heading patterns (see SECTION_PATTERNS).
#   Notes with headings outside this list (e.g. "Review of Systems",
#   "Social History") are not split correctly at those points. Sections
#   between two recognized headings get attributed to the preceding
#   recognized section.
# - If a real note has 15+ section headings, some will be missed.
# - This is best-effort. The pipeline works with SECTIONLESS notes too.

import re
from typing import TypedDict


class Section(TypedDict):
    """A section of a clinical note, with offsets into the original note."""
    name: str
    start: int
    end: int


SECTION_PATTERNS: list[tuple[str, str]] = [
    # More specific patterns first. Short abbreviations (2 chars) are avoided
    # because they false-match inside ordinary prose.
    ("Assessment and Plan", r"(?i)\b(assessment and plan|a&p|a/p)\s*[:,]?\s*"),
    ("History of Present Illness", r"(?i)\b(history of present illness|hpi)\s*[:,]?\s*"),
    ("Past Medical History", r"(?i)\b(past medical history|pmh)\s*[:,]?\s*"),
    ("Review of Systems", r"(?i)\b(review of systems|ros)\s*[:,]?\s*"),
    ("Family History", r"(?i)\b(family history)\s*[:,]?\s*"),
    ("Social History", r"(?i)\b(social history)\s*[:,]?\s*"),
    ("Physical Examination", r"(?i)\b(physical examination|physical exam)\s*[:,]?\s*"),
    ("Discharge Medications", r"(?i)\b(discharge medications)\s*[:,]?\s*"),
    ("Discharge Instructions", r"(?i)\b(discharge instructions)\s*[:,]?\s*"),
    ("Hospital Course", r"(?i)\b(hospital course)\s*[:,]?\s*"),
    ("Vital Signs", r"(?i)\b(vital signs|vitals)\s*[:,]?\s*"),
    ("Laboratory Data", r"(?i)\b(laboratory data|labs)\s*[:,]?\s*"),
    ("Chief Complaint", r"(?i)\b(chief complaint)\s*[:,]?\s*"),
    ("Medications", r"(?i)\b(medications|meds|current medications)\s*[:,]?\s*"),
    ("Allergies", r"(?i)\b(allergies)\s*[:,]?\s*"),
    ("Assessment", r"(?i)\b(assessment)\s*[:,]?\s*"),
    ("Plan", r"(?i)\b(plan)\s*[:,]?\s*"),
    ("Procedures", r"(?i)\b(procedures?)\s*[:,]?\s*"),
]
def section_note(note_text: str) -> list[Section]:
    """
    Detect sections in a clinical note.

    Args:
        note_text: the raw note text.

    Returns:
        A list of Section dicts, each with name, start, end.
        If no headings are found, a single "UNSECTIONED" section is returned.
    """
    if not note_text or not note_text.strip():
        return [{"name": "UNSECTIONED", "start": 0, "end": len(note_text or "")}]

    # Step 1: find every heading match in the note
    headings: list[dict] = []
    for canonical_name, pattern in SECTION_PATTERNS:
        for match in re.finditer(pattern, note_text):
            headings.append({
                "name": canonical_name,
                "heading_start": match.start(),
                "body_start": match.end(),
            })

    # Step 2: no headings found -> whole note is one section
    if not headings:
        return [{"name": "UNSECTIONED", "start": 0, "end": len(note_text)}]

    # Step 3: sort by heading start so sections appear in note order
    headings.sort(key=lambda h: h["heading_start"])

    # Step 4: remove overlapping headings (keep first at each position)
    # If two patterns matched the same region, keep the one with the
    # earliest body_start.
    cleaned: list[dict] = []
    for h in headings:
        if cleaned and h["heading_start"] < cleaned[-1]["body_start"]:
            continue  # skip overlapping
        cleaned.append(h)

    # Step 5: build sections. Each section runs from this heading's body start
    # to the next heading's start (or end of note).
    sections: list[Section] = []
    for i, h in enumerate(cleaned):
        body_start = h["body_start"]
        body_end = cleaned[i + 1]["heading_start"] if i + 1 < len(cleaned) else len(note_text)
        # Trim trailing whitespace so body text is clean
        trimmed = note_text[body_start:body_end].strip()
        if not trimmed:
            # Skip empty sections (heading with no body before next heading)
            continue
        # Adjust start forward past leading whitespace
        leading = len(note_text[body_start:body_end]) - len(note_text[body_start:body_end].lstrip())
        sections.append({
            "name": h["name"],
            "start": body_start + leading,
            "end": body_start + leading + len(trimmed),
        })

    if not sections:
        return [{"name": "UNSECTIONED", "start": 0, "end": len(note_text)}]

    return sections