"""Append-only audit logging."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.logging_config import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """Append-only audit log writer."""

    def __init__(self, audit_dir: str = "./audit_logs") -> None:
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def _hash_string(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def log_claim_explanation(
        self,
        correlation_id: str,
        agent_id: str,
        member_id: str,
        claim_id: str,
        tools_called: list[str],
        retrieved_doc_ids: list[str],
        explanation: str,
    ) -> None:
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "agent_id": agent_id,
            "member_id_hash": self._hash_string(member_id),
            "claim_id_hash": self._hash_string(claim_id),
            "tools_called": tools_called,
            "retrieved_doc_ids": retrieved_doc_ids,
            "explanation_hash": self._hash_string(explanation),
            "explanation_length_chars": len(explanation),
        }
        self._append_to_log(audit_entry)

    def log_error(
        self,
        correlation_id: str,
        agent_id: str,
        error_type: str,
        error_message: str,
    ) -> None:
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "agent_id": agent_id,
            "event_type": "ERROR",
            "error_type": error_type,
            "error_message": error_message,
        }
        self._append_to_log(audit_entry)

    def _append_to_log(self, entry: dict) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self.audit_dir / f"audit-{today}.jsonl"

        try:
            with open(log_file, "a") as file:
                file.write(json.dumps(entry) + "\n")
        except IOError as exc:
            logger.error(
                "audit_log_write_error",
                error=str(exc),
                log_file=str(log_file),
            )


_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Return the shared audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
