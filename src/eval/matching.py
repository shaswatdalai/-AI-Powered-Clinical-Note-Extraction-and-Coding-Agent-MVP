"""
Matching rules for evaluating extractor output against gold.

Two matchers:
- exact:   same normalized name AND any span overlap (IoU > 0).
- partial: exact name OR abbreviation-equivalent OR token Jaccard >= 0.5
           OR span overlap (IoU > 0) OR span containment.

Why these rules (see docs/FINDINGS.md for the full analysis):

1. Original `is_exact_match` required span IoU >= 0.5. That killed true
   matches whenever the extractor and gold chose slightly different
   substrings. Example from note_001: gold `"asthma"` span [520,526],
   extractor `"asthma"` span [520,526] matched, but a variation with
   [520,528] would have failed with IoU=0.75 — still fine — while a
   variation with [518,526] would have failed with IoU=0.75 too. The
   threshold was arbitrary; name equality is the real signal.

2. Vitals use different abbreviations in gold vs extractor output
   (`"Blood pressure"` vs `"BP"`, `"Weight"` vs `"Wt"`). A token-based
   match cannot bridge this. We add a small abbreviation map for
   vitals only, since it is the entity type where this is systematic.

3. Containment: gold span [805,811] (the value "124/78") is fully
   inside extractor span [790,811] ("blood pressure 124/78"). IoU is
   low (0.286) but the spans clearly refer to the same measurement.
   Containment catches this cleanly.
"""

from typing import Callable


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    """Lowercase and collapse whitespace."""
    if not s:
        return ""
    return " ".join(s.lower().split())


# ---------------------------------------------------------------------------
# Vitals abbreviation map. Applied ONLY when name_field == "name" and both
# items are vitals (checked in run_eval via ENTITY_TYPES). Keys and values
# are already normalised (lowercase, single spaces).
# ---------------------------------------------------------------------------

VITALS_ABBREVIATIONS: dict[str, str] = {
    "bp": "blood pressure",
    "blood pressure": "blood pressure",
    "hr": "heart rate",
    "heart rate": "heart rate",
    "pulse": "heart rate",
    "rr": "respiratory rate",
    "respiratory rate": "respiratory rate",
    "temp": "temperature",
    "temperature": "temperature",
    "wt": "weight",
    "weight": "weight",
    "ht": "height",
    "height": "height",
    "bmi": "bmi",
    "o2 sat": "oxygen saturation",
    "o2 saturation": "oxygen saturation",
    "oxygen saturation": "oxygen saturation",
    "spo2": "oxygen saturation",
}


def _canonical_vital(name: str) -> str:
    """Map a vital name to its canonical form. Returns normalized input
    unchanged if not in the map."""
    n = _normalize(name)
    return VITALS_ABBREVIATIONS.get(n, n)


# ---------------------------------------------------------------------------
# Span similarity
# ---------------------------------------------------------------------------

def span_iou(a: list[int] | None, b: list[int] | None) -> float:
    """IoU between two [start, end) spans."""
    if not a or not b or len(a) != 2 or len(b) != 2:
        return 0.0
    a_start, a_end = a
    b_start, b_end = b
    inter_start = max(a_start, b_start)
    inter_end = min(a_end, b_end)
    if inter_start >= inter_end:
        return 0.0
    intersection = inter_end - inter_start
    union = max(a_end, b_end) - min(a_start, b_start)
    return intersection / union if union > 0 else 0.0


def spans_overlap(a: list[int] | None, b: list[int] | None) -> bool:
    """True if the two [start, end) spans share at least one character."""
    if not a or not b or len(a) != 2 or len(b) != 2:
        return False
    return max(a[0], b[0]) < min(a[1], b[1])


def span_contains(a: list[int] | None, b: list[int] | None) -> bool:
    """True if either span fully contains the other."""
    if not a or not b or len(a) != 2 or len(b) != 2:
        return False
    a_inside_b = a[0] >= b[0] and a[1] <= b[1]
    b_inside_a = b[0] >= a[0] and b[1] <= a[1]
    return a_inside_b or b_inside_a


def token_jaccard(a: str, b: str) -> float:
    """Jaccard similarity between the token sets of two strings."""
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Matchers
# ---------------------------------------------------------------------------

def is_exact_match(
    gold: dict,
    pred: dict,
    name_field: str = "name_as_written",
) -> bool:
    """Exact: same normalized name AND any span overlap.

    Name equality is required. Span overlap is a sanity check that the
    two items refer to the same mention, but does not require a specific
    IoU threshold.
    """
    if _normalize(gold.get(name_field, "")) != _normalize(pred.get(name_field, "")):
        return False
    # If either side has no span, do not penalise — name equality alone
    # is sufficient evidence that the items refer to the same thing.
    g_span = gold.get("span")
    p_span = pred.get("span")
    if not g_span or not p_span:
        return True
    return spans_overlap(g_span, p_span)


def is_partial_match(
    gold: dict,
    pred: dict,
    name_field: str = "name_as_written",
) -> bool:
    """Partial: any of the following:
      - same normalized name
      - same canonical vital name (abbreviation map)
      - token Jaccard >= 0.5
      - spans overlap
      - one span fully contains the other
    """
    g_name = _normalize(gold.get(name_field, ""))
    p_name = _normalize(pred.get(name_field, ""))
    if g_name and g_name == p_name:
        return True

    if _canonical_vital(g_name) == _canonical_vital(p_name) and g_name and p_name:
        return True

    if token_jaccard(gold.get(name_field, ""), pred.get(name_field, "")) >= 0.5:
        return True

    g_span = gold.get("span")
    p_span = pred.get("span")
    if spans_overlap(g_span, p_span):
        return True
    if span_contains(g_span, p_span):
        return True

    return False


# Registry so run_eval can select via CLI: --matcher exact|partial
MATCHER_REGISTRY: dict[str, Callable] = {
    "exact": is_exact_match,
    "partial": is_partial_match,
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_prf(tp: int, fp: int, fn: int) -> dict:
    """Compute precision, recall, F1 from raw counts."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def evaluate_entity_type(
    gold_list: list[dict],
    pred_list: list[dict],
    name_field: str,
    matcher: Callable = is_exact_match,
) -> dict:
    """Greedy matching: for each gold item, find the first unmatched pred
    that matches.

    Returns {precision, recall, f1, tp, fp, fn}.
    """
    matched_pred: set[int] = set()
    tp = 0

    for g in gold_list:
        for pi, p in enumerate(pred_list):
            if pi in matched_pred:
                continue
            if matcher(g, p, name_field):
                tp += 1
                matched_pred.add(pi)
                break

    fp = len(pred_list) - tp
    fn = len(gold_list) - tp
    return compute_prf(tp, fp, fn)