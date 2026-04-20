"""MCP tests."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.mcp import tool_handlers
from src.mcp.client import MCPToolClient, MCPToolError
from src.mcp.http_server import create_mcp_app
from src.mcp.tool_handlers import TOOL_CLAIMS_GET_STATUS, call_tool


@pytest.fixture
def mcp_http_client():
    return TestClient(create_mcp_app())


@pytest.mark.asyncio
async def test_call_tool_unknown_tool():
    result = await call_tool("missing.tool", {})
    assert result["error"] == "unknown_tool"


def test_mcp_healthz(mcp_http_client):
    response = mcp_http_client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_mcp_tools_list(mcp_http_client):
    response = mcp_http_client.post("/mcp/tools/list", json={})
    assert response.status_code == 200
    assert "tools" in response.json()


def test_mcp_tools_call_success(mcp_http_client):
    async def fake_handler(claim_id: str):
        return {"claim_id": claim_id, "status": "DENIED"}

    with patch.dict(tool_handlers.TOOL_DISPATCH, {TOOL_CLAIMS_GET_STATUS: fake_handler}):
        response = mcp_http_client.post(
            "/mcp/tools/call",
            json={"name": TOOL_CLAIMS_GET_STATUS, "arguments": {"claim_id": "C-50012"}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["isError"] is False
    payload = json.loads(body["content"][0]["text"])
    assert payload["claim_id"] == "C-50012"


@pytest.mark.asyncio
async def test_mcp_tool_client_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": json.dumps({"claim_id": "C-50012"})}],
                "isError": False,
            },
        )

    client = MCPToolClient(base_url="http://test")
    client._client = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(handler),
    )
    try:
        result = await client.call_tool(TOOL_CLAIMS_GET_STATUS, {"claim_id": "C-50012"})
        assert result["claim_id"] == "C-50012"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_tool_client_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": json.dumps({"error": "unknown_tool"})}],
                "isError": True,
            },
        )

    client = MCPToolClient(base_url="http://test")
    client._client = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(MCPToolError):
            await client.call_tool("bad.tool", {})
    finally:
        await client.close()
