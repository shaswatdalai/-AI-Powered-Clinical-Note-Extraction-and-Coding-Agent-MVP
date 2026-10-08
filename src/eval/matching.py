"""
Matching rules for evaluating extractor output against gold.

Two levels:
- Exact match: same type, same normalized name, span IoU >= 0.5.
- Partial match: same type, token Jaccard >= 0.5 OR span IoU >= 0.3.

Strict and lenient scores reported separately.
"""

from typing import Any


def _normalize(s: str) -> str:
    """Lowercase and collapse whitespace."""
    if not s:
        return ""
    return " ".join(s.lower().split())


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


def token_jaccard(a: str, b: str) -> float:
    """Jaccard similarity between the token sets of two strings."""
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def is_exact_match(
    gold: dict,
    pred: dict,
    name_field: str = "name_as_written",
) -> bool:
    """Exact: same normalized name AND span IoU >= 0.5."""
    if _normalize(gold.get(name_field, "")) != _normalize(pred.get(name_field, "")):
        return False
    return span_iou(gold.get("span"), pred.get("span")) >= 0.5


def is_partial_match(
    gold: dict,
    pred: dict,
    name_field: str = "name_as_written",
) -> bool:
    """Partial: exact name match OR token Jaccard >= 0.5 OR span IoU >= 0.3."""
    if _normalize(gold.get(name_field, "")) == _normalize(pred.get(name_field, "")):
        return True
    if token_jaccard(gold.get(name_field, ""), pred.get(name_field, "")) >= 0.5:
        return True
    return span_iou(gold.get("span"), pred.get("span")) >= 0.3


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
    matcher=is_exact_match,
) -> dict:
    """Greedy matching: for each gold item, find the first unmatched pred that matches.

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