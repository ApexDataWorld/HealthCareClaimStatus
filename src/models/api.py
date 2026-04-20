"""API request and response models."""

from datetime import datetime

from pydantic import BaseModel, Field


class ClaimsQueryRequest(BaseModel):
    """Request to explain a claim status or denial."""

    question: str = Field(..., description="Natural language question about claim status")
    agent_id: str = Field(..., description="Agent identifier")
    correlation_id: str | None = Field(None, description="Correlation ID for tracing")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why was claim C-50012 denied for member M10023?",
                "agent_id": "AGT-001",
                "correlation_id": "corr-123456",
            }
        }


class Citation(BaseModel):
    """A policy citation in the explanation."""

    section: str = Field(..., description="Policy section identifier")
    text: str = Field(..., description="Relevant policy text")
    source_document: str = Field(..., description="Source policy document name")


class ExplanationOutput(BaseModel):
    """Full explanation output with citations."""

    claim_id: str = Field(..., description="Claim identifier")
    member_id: str = Field(..., description="Member identifier")
    summary: str = Field(..., description="Plain-English summary of claim status")
    specific_reason: str = Field(..., description="Specific reason for denial or payment status")
    citations: list[Citation] = Field(default_factory=list, description="Policy citations")
    next_steps: list[str] = Field(default_factory=list, description="Recommended next steps")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in explanation accuracy",
    )


class ClaimsQueryResponse(BaseModel):
    """Response to a claims query."""

    correlation_id: str = Field(..., description="Correlation ID for tracing")
    success: bool = Field(..., description="Whether query was successful")
    explanation: ExplanationOutput | None = Field(None, description="Detailed explanation output")
    error: str | None = Field(None, description="Error message if query failed")
    processing_time_ms: float = Field(..., description="Time taken to process request")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
