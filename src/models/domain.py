"""Domain models for claims, members, and denial codes."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class Claim(BaseModel):
    """Claim record."""

    claim_id: str = Field(..., description="Unique claim identifier")
    member_id: str = Field(..., description="Member who filed the claim")
    claim_date: date = Field(..., description="Date claim was filed")
    claim_amount: float = Field(..., description="Claim amount in USD")
    status: str = Field(..., description="Claim status")
    denial_code: str | None = Field(None, description="Denial code if denied")
    service_date: date = Field(..., description="Date of service")
    provider_name: str = Field(..., description="Healthcare provider name")
    icd_codes: list[str] = Field(default_factory=list, description="ICD-10 diagnosis codes")
    cpt_codes: list[str] = Field(default_factory=list, description="CPT procedure codes")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class Member(BaseModel):
    """Member record."""

    member_id: str = Field(..., description="Unique member identifier")
    first_name: str = Field(..., description="Member first name")
    last_name: str = Field(..., description="Member last name")
    date_of_birth: date = Field(..., description="Member DOB")
    enrollment_status: str = Field(..., description="Enrollment status")
    plan_type: str = Field(..., description="Plan type")
    group_number: str = Field(..., description="Employer group number")
    effective_date: date = Field(..., description="Coverage effective date")
    created_at: datetime = Field(..., description="Record creation timestamp")


class DenialCode(BaseModel):
    """Denial code definition."""

    code: str = Field(..., description="CARC or RARC code")
    description: str = Field(..., description="Human-readable description")
    category: str = Field(..., description="Category of denial")
    is_appealable: bool = Field(..., description="Whether this denial can be appealed")
    typical_resolution_time_days: int | None = Field(
        None,
        description="Typical days to resolve if appealed",
    )
