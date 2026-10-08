"""Tests for the verifier — focused on pure parts, not the live LLM call.

The LLM call itself is verified via src/utils/try_verifier.py.
"""

from src.verifier import _empty_unverified_response, verify
from src.schema import VerifierResponse


def test_empty_items_returns_empty_response():
    result = verify("some note", [])
    assert isinstance(result, VerifierResponse)
    assert result.verdicts == []


def test_unverified_response_marks_all_rejected():
    result = _empty_unverified_response(["d1", "m1"], "timeout")
    assert len(result["verdicts"]) == 2
    for v in result["verdicts"]:
        assert v["verdict"] == "REJECTED"
        assert v["status_correct"] is False
        assert "verifier unavailable" in v["reason"]


def test_unverified_response_ids_match():
    result = _empty_unverified_response(["d1", "d2", "m1"], "boom")
    ids = [v["id"] for v in result["verdicts"]]
    assert ids == ["d1", "d2", "m1"]