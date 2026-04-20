"""Run the claims MCP server over HTTP.

This is the deployable MCP process. It hosts the FastAPI app defined in
`src.mcp.http_server` and exposes:

    POST /mcp/tools/list
    POST /mcp/tools/call
    POST /mcp              (JSON-RPC body)
    GET  /healthz
    GET  /readyz

Why HTTP (not stdio)? The deployment topology runs the MCP server as its
own process/pod (docker-compose, Kubernetes). HTTP works across container
boundaries; stdio does not.

Usage:
    python -m scripts.run_mcp_server
    MCP_PORT=3001 python -m scripts.run_mcp_server
"""

from __future__ import annotations

import os

import uvicorn

from src.config import get_settings
from src.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "3001"))

    logger.info("mcp_http_server_starting", host=host, port=port, mock_mode=settings.mock_mode)

    # NOTE: import-by-string so uvicorn's reloader (if enabled) can reimport.
    uvicorn.run(
        "src.mcp.http_server:app",
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()
