"""Generate seed mock data if not already present."""

import json
from pathlib import Path

from src.tools.mock_store import DEFAULT_CLAIMS, DEFAULT_DENIAL_CODES, DEFAULT_MEMBERS


def seed_mock_data() -> None:
    """Create mock data JSON files if they don't exist."""
    data_dir = Path("./data/mock_data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Seed claims
    claims_file = data_dir / "claims.json"
    if not claims_file.exists():
        with open(claims_file, "w") as f:
            json.dump(DEFAULT_CLAIMS, f, indent=2, default=str)
        print(f"Created {claims_file}")
    else:
        print(f"{claims_file} already exists")

    # Seed members
    members_file = data_dir / "members.json"
    if not members_file.exists():
        with open(members_file, "w") as f:
            json.dump(DEFAULT_MEMBERS, f, indent=2, default=str)
        print(f"Created {members_file}")
    else:
        print(f"{members_file} already exists")

    # Seed denial codes
    codes_file = data_dir / "denial_codes.json"
    if not codes_file.exists():
        with open(codes_file, "w") as f:
            json.dump(DEFAULT_DENIAL_CODES, f, indent=2, default=str)
        print(f"Created {codes_file}")
    else:
        print(f"{codes_file} already exists")

    print("Mock data seeding complete!")


if __name__ == "__main__":
    seed_mock_data()
