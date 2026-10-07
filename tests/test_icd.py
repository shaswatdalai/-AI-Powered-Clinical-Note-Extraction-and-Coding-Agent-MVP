"""Tests for the ICD-10 index — focusing on the RRF fusion logic."""

from src.icd_index import _rrf_fuse


def test_rrf_fuse_combines_both_lists():
    bm25 = [(0, 5.0), (1, 3.0), (2, 1.0)]
    vec = [(1, 0.9), (2, 0.8), (3, 0.7)]
    fused = _rrf_fuse(bm25, vec)
    fused_ids = [idx for idx, _ in fused]
    assert 0 in fused_ids
    assert 1 in fused_ids
    assert 2 in fused_ids
    assert 3 in fused_ids


def test_rrf_fuse_ranks_agreement_higher():
    # Item 1 appears high in both lists — should rank first
    bm25 = [(0, 5.0), (1, 3.0)]
    vec = [(1, 0.9), (2, 0.8)]
    fused = _rrf_fuse(bm25, vec)
    assert fused[0][0] == 1


def test_rrf_fuse_empty_lists():
    assert _rrf_fuse([], []) == []


def test_rrf_fuse_single_list():
    fused = _rrf_fuse([(0, 5.0), (1, 3.0)], [])
    assert fused[0][0] == 0