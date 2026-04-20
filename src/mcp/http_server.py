"""HTTP transport for the claims MCP server.

We use HTTP because the MCP server runs as its own service in docker-compose
and deployment environments. HTTP works cleanly across container boundaries.

Exposed endpoints:
    POST /mcp/tools/list
    POST /mcp/tools/call
    GET  /healthz
    GET  /readyz
"""


import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.logging_config import get_logger
from src.mcp.tool_handlers import TOOL_SCHEMAS, call_tool

logger = get_logger(__name__)


class ToolCallRequest(BaseModel):
    """Input for /mcp/tools/call."""

    name: str = Field(..., description="Fully-qualified tool name")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")


class ToolCallContent(BaseModel):
    """MCP content block — always text for these tools."""

    type: str = "text"
    text: str


class ToolCallResponse(BaseModel):
    """MCP tool/call response shape."""

    content: list[ToolCallContent]
    isError: bool = False


class ToolsListResponse(BaseModel):
    """MCP tools/list response shape."""

    tools: list[dict]


def create_mcp_app() -> FastAPI:
    """Build the FastAPI MCP HTTP server."""
    app = FastAPI(
        title="Claims MCP Server",
        description="MCP tool surface for claims, members, and denial codes.",
        version="0.1.0",
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "healthy"}

    @app.get("/readyz")
    async def readyz() -> dict:
        return {"status": "ready", "tool_count": len(TOOL_SCHEMAS)}

    @app.post("/mcp/tools/list", response_model=ToolsListResponse)
    async def list_tools() -> ToolsListResponse:
        return ToolsListResponse(tools=TOOL_SCHEMAS)

    @app.post("/mcp/tools/call", response_model=ToolCallResponse)
    async def post_tool_call(req: ToolCallRequest) -> ToolCallResponse:
        logger.info("mcp_tool_call", tool=req.name, arg_keys=list(req.arguments.keys()))
        result = await call_tool(req.name, req.arguments)
        # Conform to MCP content envelope
        is_error = "error" in result and result.get("error") in {
            "unknown_tool",
            "invalid_arguments",
            "tool_execution_failed",
        }
        return ToolCallResponse(
            content=[ToolCallContent(type="text", text=json.dumps(result))],
            isError=is_error,
        )
    return app
app = create_mcp_app()
