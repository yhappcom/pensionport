"""Crash-reconcilable V3 scoped evidence pair persistence.

A write-ahead pending journal is durable BEFORE receipt and V2 ledger files are
published. Recovery, under an exclusive process lock, reconciles exact byte
hashes: both valid => committed; one/none => rollback; changed => fail closed.
This protects a local private directory from process termination between writes,
not power loss on storage that violates fsync, cross-device transactions, or
cryptographic identity/financial-truth attestation.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re

from .checkpoint import safe_private_directory
from .source import require, sha256, DIGEST
from .v2_evidence import validate_evidence_ledger

PREFIX = "ire_v3_scope_txn_"
JOURNAL_SCHEMA = "IRE_V3_SCOPE_EVIDENCE_WAL_V1"
MAX_JOURNAL_BYTES = 2500


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sync_folder(root):
    descriptor = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_exclusive(file, data):
    fd = os.open(file, os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        file.unlink(missing_ok=True)
        raise
    _sync_folder(file.parent)


@contextmanager
def _folder_lock(root):
    lock = root / ".ire_v3_scope_evidence.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        require(os.fstat(fd).st_mode & 0o077 == 0,
                "V3_EVIDENCE_LOCK_NOT_PRIVATE")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _journal_record(ledger, receipt):
    require(type(receipt) is dict and
            type(receipt.get("receipt_sha256")) is str and
            DIGEST.fullmatch(receipt["receipt_sha256"]) is not None and
            sha256(_json({k: v for k, v in receipt.items()
                          if k != "receipt_sha256"})) == receipt["receipt_sha256"] and
            receipt.get("next_evidence_sha256") == ledger["snapshot_sha256"] and
            receipt.get("knowledge_snapshot_sha256") ==
                ledger["knowledge_snapshot_sha256"] and
            receipt.get("financial_advice_approved") is False and
            receipt.get("approved_financial_facts") == 0,
            "V3_SCOPE_WAL_INPUT_INVALID")
    body = {
        "schema": JOURNAL_SCHEMA,
        "receipt_name": "ire_v3_scope_" + receipt["receipt_sha256"] + ".json",
        "ledger_name": "ire_evidence_v" + str(ledger["version"]).zfill(6) +
                       "_" + ledger["snapshot_sha256"][:16] + ".json",
        "receipt_bytes_sha256": sha256(_json(receipt)),
        "ledger_bytes_sha256": sha256(_json(ledger)),
        "receipt_id": receipt["receipt_sha256"],
        "ledger_id": ledger["snapshot_sha256"],
        "knowledge_id": ledger["knowledge_snapshot_sha256"],
    }
    return {**body, "journal_sha256": sha256(_json(body))}


def _validate_journal(record):
    require(type(record) is dict and set(record) == {
        "schema", "receipt_name", "ledger_name", "receipt_bytes_sha256",
        "ledger_bytes_sha256", "receipt_id", "ledger_id", "knowledge_id",
        "journal_sha256"
    } and record["schema"] == JOURNAL_SCHEMA and
            all(type(record[key]) is str and DIGEST.fullmatch(record[key])
                for key in ("receipt_bytes_sha256", "ledger_bytes_sha256",
                            "receipt_id", "ledger_id", "knowledge_id",
                            "journal_sha256")) and
            record["receipt_name"] ==
                "ire_v3_scope_" + record["receipt_id"] + ".json" and
            re.fullmatch(r"ire_evidence_v\d{6,}_" +
                         record["ledger_id"][:16] + r"\.json",
                         record["ledger_name"]) is not None and
            sha256(_json({k: v for k, v in record.items()
                          if k != "journal_sha256"})) == record["journal_sha256"],
            "V3_SCOPE_WAL_TAMPER_OR_INVALID")


def _present_and_intact(root, name, digest):
    p = root / name
    if not p.exists() and not p.is_symlink():
        return False
    require(p.is_file() and not p.is_symlink() and
            sha256(p.read_bytes()) == digest,
            "V3_SCOPE_WAL_PAYLOAD_TAMPERED")
    return True


def _remove_if_intact(root, name, digest):
    if _present_and_intact(root, name, digest):
        (root / name).unlink()


def _promote(root, pending):
    committed = pending.with_suffix(".done")
    require(not committed.exists(), "V3_SCOPE_WAL_COMMIT_EXISTS")
    os.replace(pending, committed)
    _sync_folder(root)


def _recover_unlocked(root):
    report = {"committed_after_interruption": 0,
              "rolled_back_incomplete": 0,
              "verified_committed_transactions": 0,
              "pending_remaining": 0}
    for pending in sorted(root.glob(PREFIX + "*.pending")):
        require(not pending.is_symlink() and pending.is_file() and
                pending.stat().st_size <= MAX_JOURNAL_BYTES and
                re.fullmatch(PREFIX + r"[0-9a-f]{64}\.pending",
                             pending.name), "V3_SCOPE_WAL_FILENAME_INVALID")
        record = json.loads(pending.read_text(encoding="utf-8"))
        _validate_journal(record)
        require(pending.name == PREFIX + record["receipt_id"] + ".pending",
                "V3_SCOPE_WAL_FILENAME_MISMATCH")
        receipt_exists = _present_and_intact(
            root, record["receipt_name"], record["receipt_bytes_sha256"])
        ledger_exists = _present_and_intact(
            root, record["ledger_name"], record["ledger_bytes_sha256"])
        if receipt_exists and ledger_exists:
            _promote(root, pending)
            report["committed_after_interruption"] += 1
        else:
            _remove_if_intact(root, record["receipt_name"],
                              record["receipt_bytes_sha256"])
            _remove_if_intact(root, record["ledger_name"],
                              record["ledger_bytes_sha256"])
            pending.unlink()
            _sync_folder(root)
            report["rolled_back_incomplete"] += 1
    # A previously acknowledged pair must remain whole. Never silently
    # treat a missing or tampered committed receipt/ledger as still usable.
    for completed in sorted(root.glob(PREFIX + "*.done")):
        require(not completed.is_symlink() and completed.is_file() and
                completed.stat().st_size <= MAX_JOURNAL_BYTES and
                re.fullmatch(PREFIX + r"[0-9a-f]{64}\.done",
                             completed.name), "V3_SCOPE_WAL_DONE_FILENAME_INVALID")
        record = json.loads(completed.read_text(encoding="utf-8"))
        _validate_journal(record)
        require(completed.name == PREFIX + record["receipt_id"] + ".done" and
                _present_and_intact(root, record["receipt_name"],
                                    record["receipt_bytes_sha256"]) and
                _present_and_intact(root, record["ledger_name"],
                                    record["ledger_bytes_sha256"]),
                "V3_SCOPE_WAL_COMMITTED_PAIR_BROKEN")
        report["verified_committed_transactions"] += 1
    report["pending_remaining"] = len(list(root.glob(PREFIX + "*.pending")))
    report["schema"] = "IRE_V3_SCOPE_EVIDENCE_RECOVERY_V1"
    report["financial_facts_approved"] = 0
    return report


def recover_scope_evidence_pairs(directory):
    root = safe_private_directory(directory)
    with _folder_lock(root):
        return _recover_unlocked(root)


def commit_scope_evidence_pair(ledger, knowledge, receipt, directory,
                               save_receipt, save_ledger):
    validate_evidence_ledger(ledger, knowledge)
    record = _journal_record(ledger, receipt)
    _validate_journal(record)
    root = safe_private_directory(directory)
    pending = root / (PREFIX + record["receipt_id"] + ".pending")
    done = pending.with_suffix(".done")
    with _folder_lock(root):
        _recover_unlocked(root)
        if (pending.exists() or done.exists() or
                (root / record["receipt_name"]).exists() or
                (root / record["ledger_name"]).exists()):
            raise FileExistsError("V3_SCOPE_WAL_DUPLICATE_TRANSACTION")
        _write_exclusive(pending, _json(record))
        try:
            receipt_path = save_receipt(receipt, str(root))
            ledger_path = save_ledger(ledger, knowledge, str(root))
            require(Path(receipt_path).resolve() ==
                    (root / record["receipt_name"]).resolve() and
                    Path(ledger_path).resolve() ==
                    (root / record["ledger_name"]).resolve() and
                    _present_and_intact(root, record["receipt_name"],
                                        record["receipt_bytes_sha256"]) and
                    _present_and_intact(root, record["ledger_name"],
                                        record["ledger_bytes_sha256"]),
                    "V3_SCOPE_WAL_WRITTEN_PAYLOAD_MISMATCH")
        except Exception:
            # Only our own, exact hashed payloads may be rolled back.
            _remove_if_intact(root, record["receipt_name"],
                              record["receipt_bytes_sha256"])
            _remove_if_intact(root, record["ledger_name"],
                              record["ledger_bytes_sha256"])
            pending.unlink(missing_ok=True)
            _sync_folder(root)
            raise
        _sync_folder(root)
        _promote(root, pending)
        return ledger_path, receipt_path