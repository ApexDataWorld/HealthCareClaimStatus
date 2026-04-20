"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router, set_claims_graph
from src.config import get_settings
from src.graph.workflow import get_claims_graph
from src.logging_config import configure_logging, get_logger
from src.mcp.client import MCPToolClient, set_mcp_client
from src.rag.vectorstore import initialize_vectorstore

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared clients and graph state for the app lifecycle."""
    logger.info("app_startup")
    settings = get_settings()
    configure_logging(settings.log_level)

    mcp_client = MCPToolClient(base_url=settings.mcp_server_url)
    set_mcp_client(mcp_client)
    logger.info("mcp_client_installed", base_url=settings.mcp_server_url)

    claims_graph = get_claims_graph().compile()
    set_claims_graph(claims_graph)

    try:
        vectorstore = initialize_vectorstore()
        doc_count = vectorstore._collection.count() if hasattr(vectorstore, "_collection") else 0
        logger.info("vectorstore_ready", doc_count=doc_count)
    except Exception as exc:  # noqa: BLE001
        logger.warning("vectorstore_initialization_warning", error=str(exc))

    logger.info("app_startup_complete")

    try:
        yield
    finally:
        logger.info("app_shutdown")
        try:
            await mcp_client.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("mcp_client_close_error", error=str(exc))
        set_mcp_client(None)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return FastAPI(
        title="Project 3: Claims Status + Denial/Payment Code Explanation",
        description="Production-grade health insurance claim denial explanation system",
        version="0.1.0",
        lifespan=lifespan,
    )


app = create_app()
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
