from __future__ import annotations

import os
import sys

from models import InvalidInputError


def decode_limited(content: bytes, max_bytes: int) -> tuple[str, bool]:
    truncated = len(content) > max_bytes
    return content[:max_bytes].decode("utf-8", errors="replace"), truncated


def validate_positive_int(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidInputError(f"{name} must be an integer")
    if value < 1:
        raise InvalidInputError(f"{name} must be >= 1")
    return value


def validate_positive_float(value: float | str, name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidInputError(f"{name} must be a number") from exc
    if parsed <= 0:
        raise InvalidInputError(f"{name} must be > 0")
    return parsed


def env_positive_float(name: str, default: float) -> float:
    return validate_positive_float(os.getenv(name, str(default)), name.lower())


def log_startup(message: str) -> None:
    print(f"[startup] {message}", file=sys.stderr, flush=True)
