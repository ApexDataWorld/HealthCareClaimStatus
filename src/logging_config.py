"""Simple logging configuration with PHI redaction."""

import logging
import re


def redact_phi(text: str) -> str:
    """Redact a few common PHI-like patterns from text."""
    if not isinstance(text, str):
        return str(text)

    text = re.sub(r"\d{3}-\d{2}-\d{4}", "XXX-XX-XXXX", text)
    text = re.sub(r"\bM\d{5}\b", "MXXXXX", text)
    text = re.sub(r"\bC-\d{5}\b", "C-XXXXX", text)
    text = re.sub(r"\(\d{3}\)\s?\d{3}-\d{4}", "(XXX) XXX-XXXX", text)
    text = re.sub(r"\S+@\S+", "[EMAIL]", text)
    return text


def configure_logging(log_level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


class AppLogger:
    """Small logger wrapper that redacts keyword values."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def info(self, message: str, **kwargs) -> None:
        self._logger.info(self._format(message, kwargs))

    def warning(self, message: str, **kwargs) -> None:
        self._logger.warning(self._format(message, kwargs))

    def error(self, message: str, **kwargs) -> None:
        self._logger.error(self._format(message, kwargs))

    def _format(self, message: str, kwargs: dict) -> str:
        if not kwargs:
            return message
        safe_kwargs = {key: redact_phi(value) for key, value in kwargs.items()}
        return f"{message} | {safe_kwargs}"


def get_logger(name: str) -> AppLogger:
    """Return an application logger."""
    return AppLogger(name)
