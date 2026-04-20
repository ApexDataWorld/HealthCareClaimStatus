"""Shared pytest fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api import routes
from src.main import create_app


@pytest.fixture(autouse=True)
def env_defaults(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("ALLOWED_API_KEYS", "dev-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-ant-key")
    monkeypatch.setenv("MCP_SERVER_URL", "http://mcp-stub:3001")


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {"X-API-Key": "dev-key", "Content-Type": "application/json"}


@pytest.fixture
def sample_claim_question() -> dict:
    return {
        "question": "Why was claim C-50012 denied for member M10023?",
        "agent_id": "AGT-001",
    }


@pytest.fixture
def test_app() -> TestClient:
    stub_graph = MagicMock()
    stub_graph.ainvoke = AsyncMock(
        return_value={
            "correlation_id": "test-corr-1",
            "agent_id": "AGT-001",
            "question": "Why was claim C-50012 denied for member M10023?",
            "claim": MagicMock(claim_id="C-50012"),
            "member": MagicMock(member_id="M10023"),
            "denial_code": None,
            "policy_excerpts": [
                {
                    "section": "3.2",
                    "content": "Services by non-participating providers are not covered.",
                    "source": "network_policy.md",
                }
            ],
            "explanation": (
                "SUMMARY: Claim denied due to non-covered service.\n"
                "SPECIFIC_REASON: The billed service is not covered under the member plan.\n"
                "NEXT_STEPS:\n"
                "- Review plan coverage\n"
                "- File an appeal if needed\n"
                "CONFIDENCE: 0.92\n"
            ),
            "errors": [],
        }
    )

    routes.set_claims_graph(stub_graph)
    return TestClient(create_app())
