"""
Extraction schema for the clinical note extraction pipeline.

Every item the extractor LLM returns is validated against these models.
If validation fails, the item is not trusted and will not be accepted.

Design rules:
- Every item MUST carry an evidence quote from the note.
- Spans (start/end offsets) are filled by CODE, never by the LLM.
- Statuses use strict Literal unions so bad values are rejected at parse time.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class Span(BaseModel):
    """Character offsets into the ORIGINAL note (not the masked note)."""
    start: int = Field(ge=0, description="Inclusive start offset")
    end: int = Field(gt=0, description="Exclusive end offset")


class Evidence(BaseModel):
    """
    Evidence for a single extracted item.
    The LLM returns `quote`; code fills `span` by searching the note.
    """
    quote: str = Field(description="Verbatim text from the note") #quote is the string that the LLM returns as evidence for the extracted item
    span: Optional[Span] = Field(
        default=None,
        description="Filled by code, never trusted from the LLM",
    )


class Diagnosis(BaseModel):
    name_as_written: str
    normalised_name: str
    status: Literal["active", "historical", "ruled_out", "suspected"]
    evidence: Evidence
    icd_candidates: list[dict] = Field(default_factory=list)


class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    status: Literal["current", "discontinued", "newly_prescribed"]
    evidence: Evidence


class Procedure(BaseModel):
    name: str
    date: Optional[str] = None
    evidence: Evidence


class Allergy(BaseModel):
    substance: str
    reaction: Optional[str] = None
    evidence: Evidence


class Vital(BaseModel):
    name: str
    value: str # this is string because the LLM may return "120/80" or "98.6 F" or "72 bpm" etc.
    unit: Optional[str] = None
    evidence: Evidence


class Extraction(BaseModel):
    """
    Top-level shape returned by the extractor LLM.
    Empty lists are always present, never None.
    """
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    procedures: list[Procedure] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    vitals: list[Vital] = Field(default_factory=list)


class Verdict(BaseModel):
    """A single verifier verdict for one item."""
    id: str
    verdict: Literal["SUPPORTED", "REJECTED"]
    status_correct: bool
    icd_fit: Optional[Literal["good", "poor", "none"]] = None
    reason: str


class Contradiction(BaseModel):
    """A contradiction between two or more items in the note."""
    items: list[str]
    description: str


class MissedItem(BaseModel):
    """An item the verifier believes the extractor missed."""
    type: str
    text: str
    span_text: str


class VerifierResponse(BaseModel):
    """Top-level shape returned by the verifier LLM."""
    verdicts: list[Verdict] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    missed_items: list[MissedItem] = Field(default_factory=list)