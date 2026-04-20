"""In-memory mock data store for development and testing."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from src.models.domain import Claim, DenialCode, Member

# Default mock data embedded in module
DEFAULT_CLAIMS = [
    {
        "claim_id": "C-50012",
        "member_id": "M10023",
        "claim_date": "2024-01-15",
        "claim_amount": 5000.00,
        "status": "DENIED",
        "denial_code": "CO-50",
        "service_date": "2024-01-10",
        "provider_name": "St. Mary's Hospital",
        "icd_codes": ["J18.9"],
        "cpt_codes": ["99285", "71046"],
        "created_at": "2024-01-15T09:30:00Z",
        "updated_at": "2024-01-20T14:22:00Z",
    },
    {
        "claim_id": "C-50013",
        "member_id": "M10023",
        "claim_date": "2024-02-01",
        "claim_amount": 250.00,
        "status": "PAID",
        "denial_code": None,
        "service_date": "2024-01-28",
        "provider_name": "Johnson Primary Care",
        "icd_codes": ["Z00.00"],
        "cpt_codes": ["99213"],
        "created_at": "2024-02-01T10:15:00Z",
        "updated_at": "2024-02-05T11:45:00Z",
    },
    {
        "claim_id": "C-50014",
        "member_id": "M10024",
        "claim_date": "2024-02-10",
        "claim_amount": 1500.00,
        "status": "PENDING",
        "denial_code": None,
        "service_date": "2024-02-08",
        "provider_name": "Central Lab Services",
        "icd_codes": ["E11.9"],
        "cpt_codes": ["80053"],
        "created_at": "2024-02-10T08:20:00Z",
        "updated_at": "2024-02-10T08:20:00Z",
    },
    {
        "claim_id": "C-50015",
        "member_id": "M10025",
        "claim_date": "2024-01-20",
        "claim_amount": 8500.00,
        "status": "DENIED",
        "denial_code": "CO-197",
        "service_date": "2024-01-18",
        "provider_name": "Specialty Surgery Center",
        "icd_codes": ["K80.00"],
        "cpt_codes": ["47600", "47610"],
        "created_at": "2024-01-20T11:05:00Z",
        "updated_at": "2024-01-25T13:30:00Z",
    },
    {
        "claim_id": "C-50016",
        "member_id": "M10023",
        "claim_date": "2024-03-01",
        "claim_amount": 350.00,
        "status": "PAID",
        "denial_code": None,
        "service_date": "2024-02-28",
        "provider_name": "Pharmacy Plus",
        "icd_codes": ["I10"],
        "cpt_codes": ["99605"],
        "created_at": "2024-03-01T09:00:00Z",
        "updated_at": "2024-03-05T10:30:00Z",
    },
    {
        "claim_id": "C-50017",
        "member_id": "M10024",
        "claim_date": "2024-02-15",
        "claim_amount": 1200.00,
        "status": "DENIED",
        "denial_code": "CO-96",
        "service_date": "2024-02-12",
        "provider_name": "Out-of-Network Radiology",
        "icd_codes": ["M79.3"],
        "cpt_codes": ["70450", "70451"],
        "created_at": "2024-02-15T14:40:00Z",
        "updated_at": "2024-02-20T09:15:00Z",
    },
    {
        "claim_id": "C-50018",
        "member_id": "M10025",
        "claim_date": "2024-03-05",
        "claim_amount": 600.00,
        "status": "PAID",
        "denial_code": None,
        "service_date": "2024-03-03",
        "provider_name": "Community Health Center",
        "icd_codes": ["M79.3"],
        "cpt_codes": ["99214"],
        "created_at": "2024-03-05T10:30:00Z",
        "updated_at": "2024-03-08T16:20:00Z",
    },
    {
        "claim_id": "C-50019",
        "member_id": "M10026",
        "claim_date": "2024-02-28",
        "claim_amount": 450.00,
        "status": "PENDING",
        "denial_code": None,
        "service_date": "2024-02-25",
        "provider_name": "Urgent Care Express",
        "icd_codes": ["J00"],
        "cpt_codes": ["99285"],
        "created_at": "2024-02-28T16:45:00Z",
        "updated_at": "2024-02-28T16:45:00Z",
    },
    {
        "claim_id": "C-50020",
        "member_id": "M10027",
        "claim_date": "2024-03-10",
        "claim_amount": 2500.00,
        "status": "DENIED",
        "denial_code": "CO-29",
        "service_date": "2023-12-15",
        "provider_name": "Regional Medical Center",
        "icd_codes": ["E11.65"],
        "cpt_codes": ["99291"],
        "created_at": "2024-03-10T11:20:00Z",
        "updated_at": "2024-03-15T09:00:00Z",
    },
    {
        "claim_id": "C-50021",
        "member_id": "M10023",
        "claim_date": "2024-03-15",
        "claim_amount": 100.00,
        "status": "PAID",
        "denial_code": None,
        "service_date": "2024-03-14",
        "provider_name": "Local Clinic",
        "icd_codes": ["Z23"],
        "cpt_codes": ["90686"],
        "created_at": "2024-03-15T13:10:00Z",
        "updated_at": "2024-03-18T14:50:00Z",
    },
]

DEFAULT_MEMBERS = [
    {
        "member_id": "M10023",
        "first_name": "Robert",
        "last_name": "Martinez",
        "date_of_birth": "1965-05-12",
        "enrollment_status": "ACTIVE",
        "plan_type": "PPO",
        "group_number": "GRP-2024-001",
        "effective_date": "2023-01-01",
        "created_at": "2023-01-01T08:00:00Z",
    },
    {
        "member_id": "M10024",
        "first_name": "Jennifer",
        "last_name": "Chen",
        "date_of_birth": "1978-08-23",
        "enrollment_status": "ACTIVE",
        "plan_type": "HMO",
        "group_number": "GRP-2024-002",
        "effective_date": "2023-06-01",
        "created_at": "2023-06-01T09:30:00Z",
    },
    {
        "member_id": "M10025",
        "first_name": "David",
        "last_name": "Thompson",
        "date_of_birth": "1955-11-30",
        "enrollment_status": "ACTIVE",
        "plan_type": "PPO",
        "group_number": "GRP-2024-001",
        "effective_date": "2023-01-01",
        "created_at": "2023-01-01T08:00:00Z",
    },
    {
        "member_id": "M10026",
        "first_name": "Maria",
        "last_name": "Garcia",
        "date_of_birth": "1990-02-14",
        "enrollment_status": "ACTIVE",
        "plan_type": "HDHP",
        "group_number": "GRP-2024-003",
        "effective_date": "2024-01-01",
        "created_at": "2024-01-01T10:15:00Z",
    },
    {
        "member_id": "M10027",
        "first_name": "James",
        "last_name": "Wilson",
        "date_of_birth": "1972-07-08",
        "enrollment_status": "TERMINATED",
        "plan_type": "PPO",
        "group_number": "GRP-2024-001",
        "effective_date": "2022-01-01",
        "created_at": "2022-01-01T08:00:00Z",
    },
]

DEFAULT_DENIAL_CODES = [
    {
        "code": "CO-50",
        "description": "Non-covered service or item. This charge is not covered under the patient's health plan.",
        "category": "Non-covered",
        "is_appealable": True,
        "typical_resolution_time_days": 30,
    },
    {
        "code": "CO-96",
        "description": "Non-covered charge(s). Referred to payer's contracts, agreements, plan rules or federal/state law.",
        "category": "Non-covered",
        "is_appealable": True,
        "typical_resolution_time_days": 30,
    },
    {
        "code": "CO-197",
        "description": "Precertification/authorization absent. Service requires prior authorization which was not obtained.",
        "category": "Prior Auth Required",
        "is_appealable": True,
        "typical_resolution_time_days": 45,
    },
    {
        "code": "CO-29",
        "description": "Time limit for filing has expired. Claim was not submitted within the required time period.",
        "category": "Timely Filing",
        "is_appealable": False,
        "typical_resolution_time_days": None,
    },
    {
        "code": "CO-80",
        "description": "Claim denied or reduced based on information provider submitted. Documentation insufficient to support charges.",
        "category": "Medical Necessity",
        "is_appealable": True,
        "typical_resolution_time_days": 30,
    },
    {
        "code": "CO-156",
        "description": "Claim frequency exceeded. Service frequency limit for this service has been reached.",
        "category": "Frequency Limit",
        "is_appealable": True,
        "typical_resolution_time_days": 30,
    },
    {
        "code": "CO-120",
        "description": "Deductible not met. Deductible must be satisfied before benefits are payable.",
        "category": "Benefit Limitation",
        "is_appealable": False,
        "typical_resolution_time_days": None,
    },
    {
        "code": "CO-179",
        "description": "Non-covered service. This service is specifically excluded from coverage.",
        "category": "Non-covered",
        "is_appealable": False,
        "typical_resolution_time_days": None,
    },
    {
        "code": "CO-4",
        "description": "Procedure code and billing code do not match. Code submitted is inconsistent.",
        "category": "Coding Error",
        "is_appealable": True,
        "typical_resolution_time_days": 15,
    },
    {
        "code": "CO-222",
        "description": "Out-of-network provider. Services by non-contracted provider not covered as in-network.",
        "category": "Network Status",
        "is_appealable": True,
        "typical_resolution_time_days": 30,
    },
    {
        "code": "CO-18",
        "description": "Duplicate claim/service. This claim or service has already been processed and paid.",
        "category": "Duplicate",
        "is_appealable": False,
        "typical_resolution_time_days": None,
    },
    {
        "code": "CO-7",
        "description": "The benefit for this service is included in the payment for another service.",
        "category": "Bundled",
        "is_appealable": False,
        "typical_resolution_time_days": None,
    },
    {
        "code": "CO-33",
        "description": "Claim submitted with no valid/qualifying diagnosis code. Documentation required.",
        "category": "Missing Information",
        "is_appealable": True,
        "typical_resolution_time_days": 20,
    },
    {
        "code": "CO-42",
        "description": "Claim submitted without referral. Referral required for this service.",
        "category": "Authorization",
        "is_appealable": True,
        "typical_resolution_time_days": 30,
    },
    {
        "code": "CO-231",
        "description": "Zip code indicates member out of service area. Service not available in patient's location.",
        "category": "Service Area",
        "is_appealable": False,
        "typical_resolution_time_days": None,
    },
]


class MockStore:
    """In-memory mock data store for development."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize mock store.

        Args:
            data_dir: Optional directory to load data from JSON files
        """
        self.claims: dict[str, Claim] = {}
        self.members: dict[str, Member] = {}
        self.denial_codes: dict[str, DenialCode] = {}

        if data_dir:
            self._load_from_files(data_dir)
        else:
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default mock data."""
        for claim_data in DEFAULT_CLAIMS:
            claim = Claim(**claim_data)
            self.claims[claim.claim_id] = claim

        for member_data in DEFAULT_MEMBERS:
            member = Member(**member_data)
            self.members[member.member_id] = member

        for code_data in DEFAULT_DENIAL_CODES:
            code = DenialCode(**code_data)
            self.denial_codes[code.code] = code

    def _load_from_files(self, data_dir: str) -> None:
        """Load mock data from JSON files.

        Args:
            data_dir: Directory containing claims.json, members.json, denial_codes.json
        """
        data_path = Path(data_dir)

        claims_file = data_path / "claims.json"
        if claims_file.exists():
            with open(claims_file) as f:
                claims_data = json.load(f)
                for claim_data in claims_data:
                    claim = Claim(**claim_data)
                    self.claims[claim.claim_id] = claim

        members_file = data_path / "members.json"
        if members_file.exists():
            with open(members_file) as f:
                members_data = json.load(f)
                for member_data in members_data:
                    member = Member(**member_data)
                    self.members[member.member_id] = member

        codes_file = data_path / "denial_codes.json"
        if codes_file.exists():
            with open(codes_file) as f:
                codes_data = json.load(f)
                for code_data in codes_data:
                    code = DenialCode(**code_data)
                    self.denial_codes[code.code] = code

    def get_claim(self, claim_id: str) -> Optional[Claim]:
        """Get claim by ID."""
        return self.claims.get(claim_id)

    def get_member(self, member_id: str) -> Optional[Member]:
        """Get member by ID."""
        return self.members.get(member_id)

    def get_denial_code(self, code: str) -> Optional[DenialCode]:
        """Get denial code by code."""
        return self.denial_codes.get(code)

    def get_claims_by_member(self, member_id: str) -> list[Claim]:
        """Get all claims for a member."""
        return [c for c in self.claims.values() if c.member_id == member_id]


# Global mock store instance
_mock_store: MockStore | None = None


def get_mock_store(data_dir: Optional[str] = None) -> MockStore:
    """Get or create global mock store instance."""
    global _mock_store
    if _mock_store is None:
        _mock_store = MockStore(data_dir)
    return _mock_store
