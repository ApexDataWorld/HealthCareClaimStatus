"""API error classes."""

from fastapi import HTTPException, status


class ClaimsAPIError(HTTPException):
    """Base exception for claims API errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)


class ClaimNotFoundError(ClaimsAPIError):
    """Raised when a claim cannot be found."""

    def __init__(self, claim_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found",
        )


class MemberNotFoundError(ClaimsAPIError):
    """Raised when a member cannot be found."""

    def __init__(self, member_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member {member_id} not found",
        )


class InvalidQueryError(ClaimsAPIError):
    """Raised when the request query is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query: {message}",
        )
