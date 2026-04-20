"""Regex-based PHI redaction helpers."""

import re
from typing import Any


def redact_pii(text: str) -> str:
    """Redact common PHI-like values from text."""
    if not isinstance(text, str):
        return str(text)

    text = re.sub(r"\d{3}-\d{2}-\d{4}", "XXX-XX-XXXX", text)
    text = re.sub(r"\bM\d{5}\b", "MXXXXX", text)
    text = re.sub(r"\bC-\d{5}\b", "C-XXXXX", text)
    text = re.sub(r"\(\d{3}\)\s?\d{3}-\d{4}", "(XXX) XXX-XXXX", text)
    text = re.sub(r"\S+@\S+", "[EMAIL]", text)
    return text


def redact_dict(data: dict[str, Any], sensitive_keys: list[str] | None = None) -> dict[str, Any]:
    """Redact sensitive fields in a dictionary."""
    sensitive = {
        "member_id",
        "claim_id",
        "ssn",
        "date_of_birth",
        "email",
        "phone",
        "address",
    }
    if sensitive_keys:
        sensitive.update(key.lower() for key in sensitive_keys)

    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in sensitive:
            redacted[key] = redact_pii(value) if isinstance(value, str) else "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value, sensitive_keys)
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value

    return redacted
