"""MCP (Model Context Protocol) tool surface for Project 3 Claims.

This package exposes the claims/members/denial-code enterprise APIs as MCP
tools. The graph nodes call these tools via `MCPToolClient` (HTTP transport).
The underlying `ClaimsClient`, `MemberClient`, `DenialCodeClient` live behind
the MCP server and are *not* imported from the graph directly.

Modules:
    tool_handlers: Pure async functions that implement each tool.
    http_server:   FastAPI app implementing MCP-over-HTTP (tools/list, tools/call).
    client:        MCPToolClient used by the graph and any other consumer.
"""
