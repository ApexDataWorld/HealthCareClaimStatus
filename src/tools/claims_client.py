"""HTTP client for the claims service."""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.logging_config import get_logger
from src.models.domain import Claim
from src.tools.mock_store import get_mock_store

logger = get_logger(__name__)


class ClaimsClient:
    """Client for fetching claim information."""

    def __init__(self, base_url: str, api_key: str | None = None, mock_mode: bool = False) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.mock_store = get_mock_store() if mock_mode else None
        self.client = httpx.AsyncClient(timeout=10.0) if not mock_mode else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_claim(self, claim_id: str) -> Claim | None:
        """Fetch a claim by ID."""
        if self.mock_mode:
            return self.mock_store.get_claim(claim_id)

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = await self.client.get(f"{self.base_url}/claims/{claim_id}", headers=headers)
            response.raise_for_status()
            return Claim(**response.json())
        except httpx.HTTPError as exc:
            logger.error("claims_fetch_error", claim_id=claim_id, error=str(exc))
            return None

    async def get_claims_by_member(self, member_id: str) -> list[Claim]:
        """Fetch all claims for a member."""
        if self.mock_mode:
            return self.mock_store.get_claims_by_member(member_id)

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = await self.client.get(
                f"{self.base_url}/members/{member_id}/claims",
                headers=headers,
            )
            response.raise_for_status()
            return [Claim(**item) for item in response.json()]
        except httpx.HTTPError as exc:
            logger.error("claims_list_error", member_id=member_id, error=str(exc))
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
