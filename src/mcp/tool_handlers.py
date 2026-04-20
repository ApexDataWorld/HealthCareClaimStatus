"""MCP tool implementations for claims, members, and denial codes."""


from typing import Any

from src.config import get_settings
from src.logging_config import get_logger
from src.tools.claims_client import ClaimsClient
from src.tools.denial_code_client import DenialCodeClient
from src.tools.member_client import MemberClient

logger = get_logger(__name__)


# Tool name constants — single source of truth. The graph and the server both
# reference these so a rename happens in exactly one place.
TOOL_CLAIMS_GET_STATUS = "claims.get_status"
TOOL_MEMBERS_GET_ELIGIBILITY = "members.get_eligibility"
TOOL_CODES_LOOKUP_DENIAL = "codes.lookup_denial_code"


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": TOOL_CLAIMS_GET_STATUS,
        "description": "Fetch a claim record by claim ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "claim_id": {
                    "type": "string",
                    "description": "Claim identifier (e.g., C-50012).",
                }
            },
            "required": ["claim_id"],
        },
    },
    {
        "name": TOOL_MEMBERS_GET_ELIGIBILITY,
        "description": "Fetch a member record with enrollment status and plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "member_id": {
                    "type": "string",
                    "description": "Member identifier (e.g., M10023).",
                }
            },
            "required": ["member_id"],
        },
    },
    {
        "name": TOOL_CODES_LOOKUP_DENIAL,
        "description": "Look up a CARC/RARC denial code and its appeal metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Denial code (e.g., CO-50, CO-197).",
                }
            },
            "required": ["code"],
        },
    },
]


def _get_claims_client() -> ClaimsClient:
    settings = get_settings()
    return ClaimsClient(
        base_url=settings.claims_api_url,
        api_key=None,
        mock_mode=settings.mock_mode,
    )


def _get_member_client() -> MemberClient:
    settings = get_settings()
    return MemberClient(
        base_url=settings.member_api_url,
        api_key=None,
        mock_mode=settings.mock_mode,
    )


def _get_denial_code_client() -> DenialCodeClient:
    settings = get_settings()
    return DenialCodeClient(
        base_url=settings.denial_code_api_url,
        api_key=None,
        mock_mode=settings.mock_mode,
    )



async def claims_get_status(claim_id: str) -> dict[str, Any]:
    """Return the full claim record as a dict.

    The full record (not a summary) so the caller can reconstruct a Claim
    model without a second lookup.
    """
    client = _get_claims_client()
    try:
        claim = await client.get_claim(claim_id)
        if claim is None:
            return {"error": "not_found", "claim_id": claim_id}
        # model_dump(mode="json") gives ISO date strings — round-trippable.
        return claim.model_dump(mode="json")
    finally:
        await client.close()


async def members_get_eligibility(member_id: str) -> dict[str, Any]:
    """Return the full member record as a dict."""
    client = _get_member_client()
    try:
        member = await client.get_member(member_id)
        if member is None:
            return {"error": "not_found", "member_id": member_id}
        return member.model_dump(mode="json")
    finally:
        await client.close()


async def codes_lookup_denial(code: str) -> dict[str, Any]:
    """Return the full denial-code record as a dict."""
    client = _get_denial_code_client()
    try:
        denial = await client.lookup_code(code)
        if denial is None:
            return {"error": "not_found", "code": code}
        return denial.model_dump(mode="json")
    finally:
        await client.close()


# Dispatch map: tool name → async callable. The server uses this to route calls.
TOOL_DISPATCH = {
    TOOL_CLAIMS_GET_STATUS: claims_get_status,
    TOOL_MEMBERS_GET_ELIGIBILITY: members_get_eligibility,
    TOOL_CODES_LOOKUP_DENIAL: codes_lookup_denial,
}


async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Invoke a tool by name. Central dispatch used by both transports."""
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        logger.warning("unknown_tool_call", tool=name)
        return {"error": "unknown_tool", "tool": name}

    try:
        return await handler(**arguments)
    except TypeError as e:
        # Bad argument shape — surfaces as a clean error not a 500
        logger.warning("tool_argument_error", tool=name, error=str(e))
        return {"error": "invalid_arguments", "tool": name, "detail": str(e)}
    except Exception as e:  
        logger.error("tool_execution_error", tool=name, error=str(e))
        return {"error": "tool_execution_failed", "tool": name, "detail": str(e)}
