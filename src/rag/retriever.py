"""Policy retriever for RAG."""

from langchain_community.vectorstores import Chroma

from src.logging_config import get_logger
from src.rag.vectorstore import initialize_vectorstore

logger = get_logger(__name__)


class PolicyRetriever:
    """Retrieve relevant policy excerpts from the vector store."""

    def __init__(self, vectorstore: Chroma | None = None) -> None:
        self.vectorstore = vectorstore or initialize_vectorstore()

    async def retrieve_policy_context(self, query: str, top_k: int = 5) -> list[dict[str, str]]:
        """Retrieve relevant policy documents for a query."""
        try:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            results = [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "section": doc.metadata.get("section", ""),
                }
                for doc in docs
            ]

            logger.info(
                "policy_retrieval_success",
                query=query,
                results_count=len(results),
            )
            return results
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "policy_retrieval_error",
                query=query,
                error=str(exc),
            )
            return []

    def get_collection_info(self) -> dict[str, int | str]:
        """Return basic vector collection metadata."""
        try:
            collection = self.vectorstore._collection
            return {
                "collection_name": collection.name,
                "doc_count": collection.count(),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("collection_info_error", error=str(exc))
            return {}
