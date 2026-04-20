"""Ingest policy documents into vector store."""

from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.logging_config import get_logger
from src.rag.vectorstore import initialize_vectorstore

logger = get_logger(__name__)


def ingest_policies() -> None:
    """Load and ingest policy documents into Chroma vector store."""
    policies_dir = Path("./data/policies")

    if not policies_dir.exists():
        logger.warning("policies_dir_not_found", path=str(policies_dir))
        print(f"Policy directory not found: {policies_dir}")
        return

    # Initialize vector store
    vectorstore = initialize_vectorstore()

    # Load policy documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )

    policy_files = list(policies_dir.glob("*.md"))
    logger.info("ingesting_policies", file_count=len(policy_files))

    for policy_file in policy_files:
        try:
            loader = TextLoader(str(policy_file))
            documents = loader.load()

            # Split documents
            split_docs = text_splitter.split_documents(documents)

            # Add source document metadata
            for doc in split_docs:
                doc.metadata["source"] = policy_file.name
                doc.metadata["section"] = extract_section_number(doc.page_content)

            # Add to vector store
            vectorstore.add_documents(split_docs)

            logger.info(
                "policy_ingested",
                file=policy_file.name,
                chunks=len(split_docs),
            )
            print(f"Ingested {policy_file.name} ({len(split_docs)} chunks)")

        except Exception as e:
            logger.error("policy_ingest_error", file=str(policy_file), error=str(e))
            print(f"Error ingesting {policy_file.name}: {e}")

    print("Policy ingestion complete!")


def extract_section_number(text: str) -> str:
    """Extract section number from document text.

    Args:
        text: Document text

    Returns:
        Section number or empty string
    """
    lines = text.split("\n")
    for line in lines:
        if line.startswith("#"):
            return line.lstrip("#").strip()[:50]
    return ""


if __name__ == "__main__":
    ingest_policies()
