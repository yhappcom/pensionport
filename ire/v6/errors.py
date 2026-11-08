"""Stable, typed failure codes for V6 fail-closed contracts."""


class V6Error(Exception):
    code = "V6_ERROR"

    def __init__(self, detail=""):
        self.detail = detail
        super().__init__(self.code + ((": " + detail) if detail else ""))


class InvalidInput(V6Error):
    code = "V6_INPUT_INVALID"


class ConcurrentHeadChanged(V6Error):
    code = "V6_CONCURRENT_HEAD_CHANGED"


class IdempotencyConflict(V6Error):
    code = "V6_IDEMPOTENCY_KEY_REUSED_DIFFERENT_CONTENT"


class LedgerCorrupted(V6Error):
    code = "V6_LEDGER_CORRUPTED"


class DomainConflict(V6Error):
    code = "V6_DOMAIN_CONFLICT"


class UnsupportedSchema(V6Error):
    code = "V6_SCHEMA_NOT_SUPPORTED"


class QualityNotProven(V6Error):
    code = "V6_REQUIRED_PROOFS_NOT_VERIFIED"
