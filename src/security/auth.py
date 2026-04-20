"""API key authentication dependency."""

from fastapi import Header, HTTPException, status

from src.config import get_settings


def verify_api_key(
    x_api_key: str = Header(..., description="API key for authentication"),
) -> str:
    """Verify API key from request header."""
    settings = get_settings()
    if x_api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key
