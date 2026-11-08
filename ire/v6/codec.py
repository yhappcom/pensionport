"""Strict, deterministic cross-process JSON encoding for V6 events."""
from __future__ import annotations

import hashlib
import json
import re

from .errors import InvalidInput

ZERO_SHA = "0" * 64
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IDENT = re.compile(r"[A-Za-z0-9_-]{3,80}\Z")
WINDOW = re.compile(r"W[0-9]{5,8}\Z")
VIDEO = re.compile(r"[A-Za-z0-9_-]{11}\Z")
MAX_EVENT_BYTES = 1_048_576


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _check_json(value, depth: int = 0) -> None:
    if depth > 32:
        raise InvalidInput("JSON_NESTING_TOO_DEEP")
    if value is None or type(value) in (str, bool):
        if type(value) is str:
            try:
                value.encode("utf-8", errors="strict")
            except UnicodeEncodeError as e:
                raise InvalidInput("INVALID_UNICODE") from e
        return
    if type(value) is int:
        if not -(2**63) <= value < 2**63:
            raise InvalidInput("INTEGER_OUT_OF_64BIT_RANGE")
        return
    if type(value) is list:
        for item in value:
            _check_json(item, depth + 1)
        return
    if type(value) is dict:
        for k, item in value.items():
            if type(k) is not str:
                raise InvalidInput("JSON_KEY_NOT_STRING")
            _check_json(k, depth + 1)
            _check_json(item, depth + 1)
        return
    # Floats are disallowed: financial amounts must be decimal strings with
    # explicit units; NaN, inf and platform float serializations are not stable.
    raise InvalidInput("NON_CANONICAL_JSON_TYPE")


def canonical(value) -> bytes:
    _check_json(value)
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as e:
        raise InvalidInput("JSON_SERIALIZATION_FAILED") from e
    if len(raw) > MAX_EVENT_BYTES:
        raise InvalidInput("CANONICAL_OBJECT_TOO_LARGE")
    return raw


def json_digest(value) -> str:
    return sha256(canonical(value))


def require_identifier(value, pattern=IDENT, name="IDENTIFIER") -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise InvalidInput(name + "_INVALID")
    return value


def require_hash(value, name="SHA256") -> str:
    if type(value) is not str or HEX64.fullmatch(value) is None:
        raise InvalidInput(name + "_INVALID")
    return value
