"""
PII masker for clinical notes.

Before any text is sent to an external model API, protected information
(names, dates, IDs, locations, phone numbers) is replaced with a
same-length filler so that all downstream character offsets remain valid.

Design rules:
- Same-length replacement: masks have exactly the same character count
  as the original text.
- Masked output is what gets sent to LLMs. The original note is never
  sent.
- The mask map (original -> position) stays LOCAL. It is never logged,
  never sent to any model, and never returned to the UI.
- Two detection layers: regex for structured patterns (dates, IDs,
  phone numbers) and spaCy NER for unstructured entities (names,
  locations).

Known limitations:
- spaCy's small English model (en_core_web_sm) is used. It misses some
  names, especially non-Western names.
- Regex patterns can over-match (e.g. "5 mg" might not look like a date
  but a naive pattern could flag it).
- This is a best-effort defense. Adversarial inputs may still leak PII
  through the model. Tested on an adversarial set (planned).
"""

import re
from typing import TypedDict

import spacy


# Load the spaCy model once at module import.
# If the model isn't downloaded, this line raises — the fix is
# `python -m spacy download en_core_web_sm`.
_NLP = spacy.load("en_core_web_sm")


class MaskEntry(TypedDict):
    """A single mask: what was masked, where, and what type."""
    type: str          # e.g. "PERSON", "DATE", "ID"
    start: int
    end: int
    original: str      # the original text — LOCAL ONLY, never logged


# Regex patterns for structured PII.
# Each pattern is (type_name, compiled_regex).
_REGEX_PATTERNS = [
    ("DATE", re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE,
    )),
    ("PHONE", re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    )),
    ("ID", re.compile(
        r"\b(?:MRN|ID|SSN)[-:\s]?\d{4,}\b",
        re.IGNORECASE,
    )),
    ("ZIP", re.compile(r"\b\d{5}(?:-\d{4})?\b")),
]


def _same_length_filler(length: int) -> str:
    """Return a filler string of exactly `length` characters."""
    return "X" * length


def mask_pii(note_text: str) -> tuple[str, list[MaskEntry]]:
    """
    Mask PII in a clinical note.

    Args:
        note_text: the raw note text.

    Returns:
        A tuple (masked_text, mask_entries).
        - masked_text has the same length as note_text.
        - mask_entries is a list of what was masked. Keep this LOCAL.
    """
    mask_entries: list[MaskEntry] = []

    # --- Layer 1: Regex for structured patterns ---
    regex_spans: list[tuple[int, int, str]] = []
    for pii_type, pattern in _REGEX_PATTERNS:
        for match in pattern.finditer(note_text):
            regex_spans.append((match.start(), match.end(), pii_type))

    # --- Layer 2: spaCy NER for names, locations, orgs ---
    doc = _NLP(note_text)
    spacy_spans: list[tuple[int, int, str]] = []
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "ORG", "FAC"}:
            spacy_spans.append((ent.start_char, ent.end_char, ent.label_))

    # --- Merge and de-overlap ---
    # Prefer regex spans over spaCy spans when they overlap (regex is
    # more precise for structured data).
    all_spans: list[tuple[int, int, str]] = []
    regex_ranges = [(s, e) for s, e, _ in regex_spans]
    for s, e, t in regex_spans:
        all_spans.append((s, e, t))
    for s, e, t in spacy_spans:
        # Skip if this span overlaps any regex span
        if any(s < re_end and e > re_start for re_start, re_end in regex_ranges):
            continue
        all_spans.append((s, e, t))

    # Sort by start position
    all_spans.sort(key=lambda x: x[0])

    # --- Remove overlapping spans ---
    # If two spans overlap, keep the one with the earlier start.
    filtered_spans: list[tuple[int, int, str]] = []
    last_end = -1
    for s, e, t in all_spans:
        if s < last_end:
            continue
        filtered_spans.append((s, e, t))
        last_end = e

    # --- Build masked text ---
    # Work right-to-left so earlier offsets don't shift as we replace.
    masked = note_text
    for s, e, t in reversed(filtered_spans):
        original = note_text[s:e]
        masked = masked[:s] + _same_length_filler(e - s) + masked[e:]
        mask_entries.append({
            "type": t,
            "start": s,
            "end": e,
            "original": original,
        })

    # Reverse mask_entries so they're in note order for readability
    mask_entries.reverse()

    return masked, mask_entries