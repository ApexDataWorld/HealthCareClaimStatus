"""LangGraph state definition for claims workflow."""

from typing import Any, Optional

from typing_extensions import TypedDict

from src.models.domain import Claim, DenialCode, Member


class ClaimsGraphState(TypedDict, total=False):
    """State object passed through the claims explanation graph.

    Attributes:
        correlation_id: Request correlation ID for tracing
        agent_id: Agent identifier making the request
        question: Natural language question from the user
        member_id: Extracted member ID
        claim_id: Extracted claim ID
        claim: Fetched claim object
        member: Fetched member object
        denial_code: Fetched denial code object (if claim denied)
        policy_excerpts: List of relevant policy excerpts from RAG
        explanation: Final generated explanation
        errors: List of errors encountered during processing
    """

    correlation_id: str
    agent_id: str
    question: str
    member_id: Optional[str]
    claim_id: Optional[str]
    claim: Optional[Claim]
    member: Optional[Member]
    denial_code: Optional[DenialCode]
    policy_excerpts: list[dict[str, str]]
    explanation: Optional[str]
    errors: list[str]
