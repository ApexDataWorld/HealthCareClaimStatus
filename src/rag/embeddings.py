"""Embedding model initialization."""

from langchain_community.embeddings import HuggingFaceEmbeddings


def get_embeddings() -> HuggingFaceEmbeddings:
    """Get embedding model for RAG.

    Returns:
        HuggingFaceEmbeddings instance using sentence-transformers
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True},
    )
