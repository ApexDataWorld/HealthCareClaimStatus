"""HTTP client for calling the claims MCP server.

The graph consumes only this client. It never imports ClaimsClient /
MemberClient / DenialCodeClient. That's what makes MCP a real tool surface
instead of a parallel path.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.logging_config import get_logger

logger = get_logger(__name__)


class MCPToolError(RuntimeError):
    """Raised when the MCP server returns an error envelope."""


class MCPToolClient:
    """HTTP client for the claims MCP tool surface.

    Usage:
        mcp = MCPToolClient(base_url="http://localhost:3001")
        tools = await mcp.list_tools()
        claim_dict = await mcp.call_tool("claims.get_status", {"claim_id": "C-50012"})
        await mcp.close()
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 10.0,
        api_key: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key
        headers = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout_seconds,
            headers=headers,
        )

    async def close(self) -> None:
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def list_tools(self) -> list[dict[str, Any]]:
        """Return the tool schema list from the MCP server."""
        resp = await self._client.post("/mcp/tools/list", json={})
        resp.raise_for_status()
        return resp.json().get("tools", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.TransportError,)),
        reraise=True,
    )
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke an MCP tool and return the parsed JSON payload.

        Raises:
            MCPToolError: if the server returned True
            httpx.HTTPStatusError: on failure 4xx / 5xx
        """
        logger.info("mcp_client_call", tool=name, arg_keys=list(arguments.keys()))
        resp = await self._client.post(
            "/mcp/tools/call",
            json={"name": name, "arguments": arguments},
        )
        resp.raise_for_status()

        envelope = resp.json()
        content = envelope.get("content") or []
        if not content:
            raise MCPToolError(f"empty MCP response for tool={name}")

        # We only emit text content; decode the JSON payload.
        raw = content[0].get("text") or "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            raise MCPToolError(f"invalid JSON from tool={name}: {e}")

        if envelope.get("isError"):
            logger.warning("mcp_tool_error_envelope", tool=name, payload=payload)
            raise MCPToolError(
                f"tool={name} returned error: {payload.get('error')} — {payload.get('detail', '')}"
            )

        return payload


# Module-level singleton — set from main.py lifespan so every graph invocation
# shares one pooled HTTP client. Set to None until initialised.
_mcp_client: Optional[MCPToolClient] = None


def set_mcp_client(client: Optional[MCPToolClient]) -> None:
    """Install (or clear) the process-wide MCP client."""
    global _mcp_client
    _mcp_client = client


def get_mcp_client() -> MCPToolClient:
    """Return the installed MCP client, or raise if never initialised."""
    if _mcp_client is None:
        raise RuntimeError(
            "MCPToolClient is not initialised. Call set_mcp_client(...) in lifespan first."
        )
    return _mcp_client
