"""Redaction tests."""

from src.security.redaction import redact_dict, redact_pii


def test_redact_pii_masks_common_values():
    text = "Member M10023 with claim C-50012 has SSN 123-45-6789 and email jane@example.com"
    result = redact_pii(text)

    assert "M10023" not in result
    assert "C-50012" not in result
    assert "123-45-6789" not in result
    assert "jane@example.com" not in result


def test_redact_pii_leaves_safe_text_unchanged():
    text = "The appeals process allows 180 days."
    assert redact_pii(text) == text


def test_redact_dict_masks_sensitive_fields():
    data = {
        "member_id": "M10023",
        "claim_id": "C-50012",
        "plan_type": "PPO",
    }

    result = redact_dict(data)

    assert result["member_id"] != "M10023"
    assert result["claim_id"] != "C-50012"
    assert result["plan_type"] == "PPO"


def test_redact_dict_handles_nested_values():
    data = {"request": {"member_id": "M10023", "question": "Why denied?"}}
    result = redact_dict(data)

    assert result["request"]["member_id"] != "M10023"
    assert result["request"]["question"] == "Why denied?"
