"""Vector store initialization and management."""

from langchain_community.vectorstores import Chroma

from src.config import get_settings
from src.logging_config import get_logger
from src.rag.embeddings import get_embeddings

logger = get_logger(__name__)


def initialize_vectorstore() -> Chroma:
    """Initialize Chroma vector store for policy documents.

    Returns:
        Chroma vector store instance
    """
    settings = get_settings()
    embeddings = get_embeddings()

    vectorstore = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )

    logger.info(
        "vectorstore_initialized",
        collection=settings.chroma_collection_name,
        persist_dir=settings.chroma_persist_dir,
    )

    return vectorstore
