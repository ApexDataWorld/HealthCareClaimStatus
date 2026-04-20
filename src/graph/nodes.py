"""LangGraph nodes for the claims-explanation workflow."""

import json
from typing import Any

from langchain_anthropic import ChatAnthropic

from src.config import get_settings
from src.graph.state import ClaimsGraphState
from src.logging_config import get_logger
from src.mcp.client import MCPToolError, get_mcp_client
from src.mcp.tool_handlers import (
    TOOL_CLAIMS_GET_STATUS,
    TOOL_CODES_LOOKUP_DENIAL,
    TOOL_MEMBERS_GET_ELIGIBILITY,
)
from src.models.domain import Claim, DenialCode, Member
from src.rag.prompts import EXPLAIN_CLAIM_PROMPT, PARSE_INTENT_PROMPT
from src.rag.retriever import PolicyRetriever
from src.security.audit import get_audit_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()


def _append_error(state: ClaimsGraphState, message: str) -> dict[str, Any]:
    return {"errors": state.get("errors", []) + [message]}


def _get_llm() -> ChatAnthropic:
    settings = get_settings()
    return ChatAnthropic(api_key=settings.anthropic_api_key, model=settings.parse_model)


def _strip_code_fences(content: str) -> str:
    content = content.strip()
    if not content.startswith("```"):
        return content

    content = content.split("```")[1]
    if content.startswith("json"):
        content = content[4:]
    return content.strip()


async def _fetch_model(
    *,
    state: ClaimsGraphState,
    tool_name: str,
    arguments: dict[str, Any],
    not_found_message: str,
    model_cls,
    warn_event: str,
    error_event: str,
    invalid_event: str,
    extra_log_fields: dict[str, Any],
    output_key: str,
) -> dict[str, Any]:
    mcp = get_mcp_client()
    try:
        payload = await mcp.call_tool(tool_name, arguments)
    except MCPToolError as exc:
        logger.warning(warn_event, correlation_id=state["correlation_id"], error=str(exc), **extra_log_fields)
        return _append_error(state, f"MCP tool error: {exc}")
    except Exception as exc:  
        logger.error(error_event, correlation_id=state["correlation_id"], error=str(exc), **extra_log_fields)
        return _append_error(state, f"Failed to fetch data: {exc}")

    if payload.get("error") == "not_found":
        return _append_error(state, not_found_message)

    try:
        model = model_cls.model_validate(payload)
    except Exception as exc:  
        logger.error(invalid_event, correlation_id=state["correlation_id"], error=str(exc), **extra_log_fields)
        return _append_error(state, f"Invalid payload from MCP: {exc}")

    return {output_key: model}


def _build_policy_context(excerpts: list[dict[str, Any]]) -> str:
    if not excerpts:
        return "No specific policy sections available."

    sections = ["Relevant Policy Sections:"]
    for index, excerpt in enumerate(excerpts[:3], start=1):
        sections.append(
            f"\n{index}. {excerpt.get('section', 'Section')} ({excerpt.get('source', '')})\n"
            f"   {excerpt.get('content', '')[:500]}"
        )
    return "".join(sections)


async def parse_intent(state: ClaimsGraphState) -> dict[str, Any]:
    """Extract `member_id` and `claim_id` from the user's natural-language question."""
    logger.info("node_start", node="parse_intent", correlation_id=state["correlation_id"])

    try:
        response = _get_llm().invoke(PARSE_INTENT_PROMPT.format(question=state["question"]))
        parsed = json.loads(_strip_code_fences(response.content))
        member_id = parsed.get("member_id")
        claim_id = parsed.get("claim_id")
        logger.info(
            "intent_parsed",
            correlation_id=state["correlation_id"],
            member_id=member_id,
            claim_id=claim_id,
        )
        return {"member_id": member_id, "claim_id": claim_id}
    except Exception as exc: 
        logger.error("intent_parse_error", correlation_id=state["correlation_id"], error=str(exc))
        return _append_error(state, f"Failed to parse intent: {exc}")


async def fetch_claim(state: ClaimsGraphState) -> dict[str, Any]:
    """Fetch a claim record via the MCP tool surface."""
    logger.info("node_start", node="fetch_claim", correlation_id=state["correlation_id"])

    claim_id = state.get("claim_id")
    if not claim_id:
        return _append_error(state, "No claim ID available")

    result = await _fetch_model(
        state=state,
        tool_name=TOOL_CLAIMS_GET_STATUS,
        arguments={"claim_id": claim_id},
        not_found_message=f"Claim {claim_id} not found",
        model_cls=Claim,
        warn_event="claim_fetch_mcp_error",
        error_event="claim_fetch_error",
        invalid_event="claim_payload_invalid",
        extra_log_fields={"claim_id": claim_id},
        output_key="claim",
    )
    claim = result.get("claim")
    if claim:
        logger.info(
            "claim_fetched",
            correlation_id=state["correlation_id"],
            claim_id=claim_id,
            status=claim.status,
        )
    return result


async def fetch_member(state: ClaimsGraphState) -> dict[str, Any]:
    """Fetch a member record via the MCP tool surface."""
    logger.info("node_start", node="fetch_member", correlation_id=state["correlation_id"])

    member_id = state.get("member_id")
    if not member_id:
        return _append_error(state, "No member ID available")

    result = await _fetch_model(
        state=state,
        tool_name=TOOL_MEMBERS_GET_ELIGIBILITY,
        arguments={"member_id": member_id},
        not_found_message=f"Member {member_id} not found",
        model_cls=Member,
        warn_event="member_fetch_mcp_error",
        error_event="member_fetch_error",
        invalid_event="member_payload_invalid",
        extra_log_fields={"member_id": member_id},
        output_key="member",
    )
    member = result.get("member")
    if member:
        logger.info(
            "member_fetched",
            correlation_id=state["correlation_id"],
            member_id=member_id,
            enrollment_status=member.enrollment_status,
        )
    return result


async def fetch_denial_code(state: ClaimsGraphState) -> dict[str, Any]:
    """Fetch a denial-code definition via MCP."""
    logger.info("node_start", node="fetch_denial_code", correlation_id=state["correlation_id"])

    claim = state.get("claim")
    if not claim or claim.status != "DENIED" or not claim.denial_code:
        logger.info(
            "denial_code_skipped",
            correlation_id=state["correlation_id"],
            reason="claim not denied or no denial code",
        )
        return {}

    mcp = get_mcp_client()
    try:
        payload = await mcp.call_tool(TOOL_CODES_LOOKUP_DENIAL, {"code": claim.denial_code})
    except MCPToolError as exc:
        logger.warning(
            "denial_code_mcp_error",
            correlation_id=state["correlation_id"],
            denial_code=claim.denial_code,
            error=str(exc),
        )
        return {}
    except Exception as exc:  
        logger.error(
            "denial_code_fetch_error",
            correlation_id=state["correlation_id"],
            denial_code=claim.denial_code,
            error=str(exc),
        )
        return {}

    if payload.get("error") == "not_found":
        logger.warning(
            "denial_code_not_found",
            correlation_id=state["correlation_id"],
            denial_code=claim.denial_code,
        )
        return {}

    try:
        denial_code = DenialCode.model_validate(payload)
    except Exception as exc:  
        logger.error(
            "denial_code_payload_invalid",
            correlation_id=state["correlation_id"],
            denial_code=claim.denial_code,
            error=str(exc),
        )
        return {}

    logger.info(
        "denial_code_fetched",
        correlation_id=state["correlation_id"],
        denial_code=claim.denial_code,
    )
    return {"denial_code": denial_code}


async def retrieve_policy_context(state: ClaimsGraphState) -> dict[str, Any]:
    """Retrieve relevant policy excerpts via RAG."""
    logger.info("node_start", node="retrieve_policy_context", correlation_id=state["correlation_id"])

    claim = state.get("claim")
    denial_code = state.get("denial_code")
    if not claim:
        return {}

    queries = [f"{claim.status} claim"]
    if denial_code:
        queries.extend([denial_code.category, denial_code.description])

    retriever = PolicyRetriever()
    all_excerpts: list[dict[str, Any]] = []

    try:
        for query in queries:
            all_excerpts.extend(await retriever.retrieve_policy_context(query, top_k=3))

        unique_excerpts: list[dict[str, Any]] = []
        seen: set[tuple[Any, Any]] = set()
        for excerpt in all_excerpts:
            key = (excerpt.get("source"), excerpt.get("section"))
            if key not in seen:
                seen.add(key)
                unique_excerpts.append(excerpt)

        logger.info(
            "policy_context_retrieved",
            correlation_id=state["correlation_id"],
            excerpt_count=len(unique_excerpts),
        )
        return {"policy_excerpts": unique_excerpts}
    except Exception as exc:  
        logger.error("policy_retrieval_error", correlation_id=state["correlation_id"], error=str(exc))
        return {"policy_excerpts": []}


async def assemble_context(state: ClaimsGraphState) -> dict[str, Any]:
    """Log that all context is in place. No state mutation."""
    logger.info("node_start", node="assemble_context", correlation_id=state["correlation_id"])
    logger.info(
        "context_assembled",
        correlation_id=state["correlation_id"],
        has_claim=bool(state.get("claim")),
        has_member=bool(state.get("member")),
        has_denial_code=bool(state.get("denial_code")),
        policy_excerpt_count=len(state.get("policy_excerpts", [])),
    )
    return {}


async def llm_explain(state: ClaimsGraphState) -> dict[str, Any]:
    """Generate the plain-English claim explanation."""
    logger.info("node_start", node="llm_explain", correlation_id=state["correlation_id"])

    claim = state.get("claim")
    member = state.get("member")
    denial_code = state.get("denial_code")
    excerpts = state.get("policy_excerpts", [])

    if not claim or not member:
        return _append_error(state, "Missing required claim or member data")

    denial_section = ""
    if claim.status == "DENIED" and denial_code:
        denial_section = (
            f"- Denial Code: {claim.denial_code}\n"
            f"- Denial Reason: {denial_code.description}\n"
            f"- Category: {denial_code.category}\n"
            f"- Appealable: {'Yes' if denial_code.is_appealable else 'No'}"
        )

    prompt = EXPLAIN_CLAIM_PROMPT.format(
        claim_id=claim.claim_id,
        member_name=f"{member.first_name} {member.last_name}",
        service_date=claim.service_date,
        claim_amount=claim.claim_amount,
        claim_status=claim.status,
        denial_section=denial_section,
        policy_context=_build_policy_context(excerpts),
    )

    try:
        response = _get_llm().invoke(prompt)
        logger.info(
            "explanation_generated",
            correlation_id=state["correlation_id"],
            claim_id=claim.claim_id,
        )
        return {"explanation": response.content}
    except Exception as exc: 
        logger.error(
            "explanation_generation_error",
            correlation_id=state["correlation_id"],
            error=str(exc),
        )
        return _append_error(state, f"Failed to generate explanation: {exc}")


async def audit_log(state: ClaimsGraphState) -> dict[str, Any]:
    """Emit a HIPAA-aware audit record of the interaction."""
    logger.info("node_start", node="audit_log", correlation_id=state["correlation_id"])

    claim = state.get("claim")
    member = state.get("member")
    explanation = state.get("explanation")
    if not (claim and member and explanation):
        return {}

    tools_called = [TOOL_CLAIMS_GET_STATUS, TOOL_MEMBERS_GET_ELIGIBILITY]
    if state.get("denial_code"):
        tools_called.append(TOOL_CODES_LOOKUP_DENIAL)

    audit_logger.log_claim_explanation(
        correlation_id=state["correlation_id"],
        agent_id=state["agent_id"],
        member_id=member.member_id,
        claim_id=claim.claim_id,
        tools_called=tools_called,
        retrieved_doc_ids=[str(exc.get("section")) for exc in state.get("policy_excerpts", [])],
        explanation=explanation,
    )
    return {}
