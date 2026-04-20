"""API routes for claims explanation."""

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.graph.state import ClaimsGraphState
from src.logging_config import get_logger
from src.models.api import (
    Citation,
    ClaimsQueryRequest,
    ClaimsQueryResponse,
    ExplanationOutput,
    HealthResponse,
)
from src.security.auth import verify_api_key
from src.security.audit import get_audit_logger

logger = get_logger(__name__)

router = APIRouter()

# These will be set by the main app
_claims_graph = None
_settings = None


def set_claims_graph(graph) -> None:
    """Set the claims graph instance."""
    global _claims_graph
    _claims_graph = graph


def set_settings(settings) -> None:
    """Set the settings instance."""
    global _settings
    _settings = settings


@router.post("/v1/claims/explain", response_model=ClaimsQueryResponse)
async def explain_claim(
    request: ClaimsQueryRequest,
    api_key: str = Depends(verify_api_key),
) -> ClaimsQueryResponse:
    """Explain a claim status or denial.

    Args:
        request: Claims query request with question and agent_id
        api_key: Verified API key

    Returns:
        ClaimsQueryResponse with explanation or error
    """
    start_time = time.time()
    correlation_id = request.correlation_id or str(uuid.uuid4())

    logger.info(
        "claim_explain_request",
        correlation_id=correlation_id,
        agent_id=request.agent_id,
        question=request.question[:100],
    )

    try:
        # Initialize graph state
        initial_state: ClaimsGraphState = {
            "correlation_id": correlation_id,
            "agent_id": request.agent_id,
            "question": request.question,
            "member_id": None,
            "claim_id": None,
            "claim": None,
            "member": None,
            "denial_code": None,
            "policy_excerpts": [],
            "explanation": None,
            "errors": [],
        }

        # Run the graph
        final_state = await _claims_graph.ainvoke(initial_state)

        processing_time_ms = (time.time() - start_time) * 1000

        # Handle errors
        if final_state.get("errors"):
            logger.warning(
                "claim_explain_completed_with_errors",
                correlation_id=correlation_id,
                errors=final_state["errors"],
            )
            return ClaimsQueryResponse(
                correlation_id=correlation_id,
                success=False,
                explanation=None,
                error="; ".join(final_state["errors"]),
                processing_time_ms=processing_time_ms,
            )

        # Build explanation output
        explanation = final_state.get("explanation", "")
        print("\nRAW EXPLANATION:\n", explanation)

        claim = final_state.get("claim")
        member = final_state.get("member")
        policy_excerpts = final_state.get("policy_excerpts", [])

        # Parse explanation into sections
               # Parse explanation into sections
        summary = ""
        specific_reason = ""
        next_steps = []
        confidence = 0.85

        if explanation:
            lines = explanation.splitlines()

            for i, line in enumerate(lines):
                cleaned = line.strip().replace("**", "")

                if cleaned.startswith("SUMMARY:"):
                    value = cleaned.replace("SUMMARY:", "", 1).strip()
                    if value:
                        summary = value
                    elif i + 1 < len(lines):
                        summary = lines[i + 1].strip()

                elif cleaned.startswith("SPECIFIC_REASON:"):
                    value = cleaned.replace("SPECIFIC_REASON:", "", 1).strip()
                    if value:
                        specific_reason = value
                    elif i + 1 < len(lines):
                        specific_reason = lines[i + 1].strip()

                elif cleaned.startswith("NEXT_STEPS:"):
                    j = i + 1
                    while j < len(lines):
                        step_line = lines[j].strip().replace("**", "")
                        if not step_line:
                            j += 1
                            continue

                        if step_line.startswith("-"):
                            next_steps.append(step_line.lstrip("- ").strip())
                            j += 1
                            continue

                        if ". " in step_line and step_line.split(". ", 1)[0].isdigit():
                            next_steps.append(step_line.split(". ", 1)[1].strip())
                            j += 1
                            continue

                        break


                elif cleaned.startswith("CONFIDENCE:"):
                    value = cleaned.replace("CONFIDENCE:", "", 1).strip()
                    if not value and i + 1 < len(lines):
                        value = lines[i + 1].strip()
                    try:
                        confidence = float(value)
                    except ValueError:
                        confidence = 0.85



        # Build citations from policy excerpts
        citations = []
        for exc in policy_excerpts[:3]:
            citations.append(
                Citation(
                    section=exc.get("section", ""),
                    text=exc.get("content", "")[:200],
                    source_document=exc.get("source", ""),
                )
            )

        explanation_output = ExplanationOutput(
            claim_id=claim.claim_id if claim else "unknown",
            member_id=member.member_id if member else "unknown",
            summary=summary or "Claim processed.",
            specific_reason=specific_reason or "See policy context above.",
            citations=citations,
            next_steps=next_steps or ["Contact your insurance provider for more details."],
            confidence_score=min(1.0, max(0.0, confidence)),
        )

        logger.info(
            "claim_explain_success",
            correlation_id=correlation_id,
            claim_id=claim.claim_id if claim else None,
            member_id=member.member_id if member else None,
        )

        return ClaimsQueryResponse(
            correlation_id=correlation_id,
            success=True,
            explanation=explanation_output,
            error=None,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(
            "claim_explain_error",
            correlation_id=correlation_id,
            error=str(e),
        )
        return ClaimsQueryResponse(
            correlation_id=correlation_id,
            success=False,
            explanation=None,
            error=f"Failed to process request: {str(e)}",
            processing_time_ms=processing_time_ms,
        )


@router.get("/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with status and version
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
    )


@router.get("/readyz", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness check endpoint.

    Returns:
        HealthResponse if ready
    """
    if _claims_graph is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "0.1.0",
            },
        )

    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow(),
        version="0.1.0",
    )
