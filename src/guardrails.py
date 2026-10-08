"""
Guardrails for handling untrusted note text.

The clinical note is DATA, not instructions. If a note contains embedded
imperatives like "ignore previous instructions", they must not influence
the model.

Defence layers:
1. Delimiter wrapping — note text is surrounded by explicit markers.
2. System instruction — the system prompt tells the model that the
   note is data, not instructions.
3. Output validation — the JSON schema rejects unexpected output shapes.
"""


NOTE_DELIMITER_START = "<<<BEGIN_NOTE>>>"
NOTE_DELIMITER_END = "<<<END_NOTE>>>"


def wrap_note(note_text: str) -> str:
    """Wrap the note in explicit delimiters."""
    return f"{NOTE_DELIMITER_START}\n{note_text}\n{NOTE_DELIMITER_END}"


def strip_delimiters(wrapped_text: str) -> str:
    """Remove the delimiters to recover the original note text."""
    start = wrapped_text.find(NOTE_DELIMITER_START)
    end = wrapped_text.find(NOTE_DELIMITER_END)
    if start == -1 or end == -1:
        return wrapped_text
    body_start = start + len(NOTE_DELIMITER_START)
    return wrapped_text[body_start:end].strip()