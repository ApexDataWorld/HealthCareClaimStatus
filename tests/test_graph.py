"""Workflow tests."""

from unittest.mock import MagicMock

from src.graph.workflow import build_claims_graph, should_fetch_denial_code


def test_should_fetch_denial_code_when_denied_with_code():
    claim = MagicMock(status="DENIED", denial_code="CO-242")
    assert should_fetch_denial_code({"claim": claim}) is True


def test_should_not_fetch_denial_code_otherwise():
    assert should_fetch_denial_code({"claim": None}) is False
    assert should_fetch_denial_code({"claim": MagicMock(status="DENIED", denial_code=None)}) is False
    assert should_fetch_denial_code({"claim": MagicMock(status="PAID", denial_code="CO-242")}) is False


def test_graph_builds_and_compiles():
    graph = build_claims_graph()
    assert graph is not None
    assert graph.compile() is not None
