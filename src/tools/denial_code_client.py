"""HTTP client for the denial code service."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.logging_config import get_logger
from src.models.domain import DenialCode
from src.tools.mock_store import get_mock_store

logger = get_logger(__name__)


class DenialCodeClient:
    """Client for fetching denial code information."""

    def __init__(self, base_url: str, api_key: str | None = None, mock_mode: bool = False) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.mock_store = get_mock_store() if mock_mode else None
        self.client = httpx.AsyncClient(timeout=10.0) if not mock_mode else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def lookup_code(self, code: str) -> DenialCode | None:
        """Look up a denial code by code."""
        if self.mock_mode:
            return self.mock_store.get_denial_code(code)

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = await self.client.get(f"{self.base_url}/denial-codes/{code}", headers=headers)
            response.raise_for_status()
            return DenialCode(**response.json())
        except httpx.HTTPError as exc:
            logger.error("denial_code_lookup_error", code=code, error=str(exc))
            return None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
