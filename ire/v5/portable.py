"""IRE V5 private encrypted research checkpoint export and cross-session replay.

The source SRT, model-authored text and all receipts are private. This module
never invokes model inference, performs web searches or approves financial facts.
Cloud upload is an explicit separate operation, not performed by this module.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sys
import zlib

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .engine import ResearchRun, RunError, canonical, sha256, require, _exclusive_json, _private_dir

MAGIC = b"IRE_V5_PRIVATE_ARCHIVE_V1\n"
SALT_BYTES = 16
NONCE_BYTES = 12
MAX_DECOMPRESSED = 96_000_000
MAX_ARCHIVE = 70_000_000
ARCHIVE_SCHEMA = "IRE_V5_PRIVATE_ENCRYPTED_SNAPSHOT_V1"
NAME_PATTERN = re.compile(r"^\d{6}_[0-9a-f]{64}\.json$")


def _key(secret: str, salt: bytes) -> bytes:
    require(type(secret) is str and len(secret) >= 12,
            "ARCHIVE_PASSPHRASE_MUST_BE_AT_LEAST_12_CHARS")
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(secret.encode("utf-8"))


def _inflate(data: bytes) -> bytes:
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(data, MAX_DECOMPRESSED + 1)
    require(len(raw) <= MAX_DECOMPRESSED and decompressor.eof and
            not decompressor.unconsumed_tail and not decompressor.unused_data,
            "ARCHIVE_DECOMPRESS_BOUND_OR_TRAILING_DATA")
    return raw


def _private_write_bytes(path: Path, value: bytes) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def export_encrypted(run: ResearchRun, secret: str, archive_path: str | Path) -> dict:
    """Export current replay-verified event chain with exact source bytes and plan."""
    state = run.replay()
    events = []
    for path in sorted(run.events.glob("*.json")):
        require(bool(NAME_PATTERN.fullmatch(path.name)), "ARCHIVE_BAD_EVENT_FILENAME")
        events.append({"name": path.name, "value": json.loads(path.read_text("utf-8"))})
    payload = {
        "schema": ARCHIVE_SCHEMA,
        "source_srt_base64": base64.b64encode(run.source).decode("ascii"),
        "source_sha256": sha256(run.source),
        "manifest": run.manifest,
        "manifest_sha256": sha256(canonical(run.manifest)),
        "run_lock": run.lock,
        "events": events,
        "event_chain_head_sha256": state["event_chain_head_sha256"],
        "event_count": state["receipt_count"],
        "research_status": state["research_status"],
    }
    plaintext = canonical(payload)
    require(len(plaintext) <= MAX_DECOMPRESSED, "ARCHIVE_TOO_BIG")
    compressed = zlib.compress(plaintext, 9)
    salt = secrets.token_bytes(SALT_BYTES)
    nonce = secrets.token_bytes(NONCE_BYTES)
    ciphertext = AESGCM(_key(secret, salt)).encrypt(nonce, compressed, MAGIC)
    sealed = MAGIC + salt + nonce + ciphertext
    require(len(sealed) <= MAX_ARCHIVE, "ARCHIVE_ENCRYPTED_TOO_BIG")
    destination = Path(archive_path).expanduser().resolve()
    require(destination.parent.exists(), "ARCHIVE_PARENT_MISSING")
    require(not destination.exists(), "ARCHIVE_WOULD_OVERWRITE")
    _private_write_bytes(destination, sealed)
    return {
        "schema": ARCHIVE_SCHEMA,
        "archive_sha256": sha256(sealed),
        "source_sha256": payload["source_sha256"],
        "manifest_sha256": payload["manifest_sha256"],
        "receipt_count": payload["event_count"],
        "event_chain_head_sha256": payload["event_chain_head_sha256"],
        "research_status": payload["research_status"],
        "encrypted": True,
        "secret_saved_in_archive": False,
    }


def _decrypt_envelope(archive: bytes, secret: str) -> dict:
    require(len(archive) <= MAX_ARCHIVE and archive.startswith(MAGIC) and
            len(archive) > len(MAGIC) + SALT_BYTES + NONCE_BYTES + 16,
            "ARCHIVE_HEADER_INVALID")
    i = len(MAGIC)
    salt = archive[i:i+SALT_BYTES]
    nonce = archive[i+SALT_BYTES:i+SALT_BYTES+NONCE_BYTES]
    ciphertext = archive[i+SALT_BYTES+NONCE_BYTES:]
    try:
        packed = AESGCM(_key(secret, salt)).decrypt(nonce, ciphertext, MAGIC)
    except InvalidTag as e:
        raise RunError("ARCHIVE_PASSWORD_OR_INTEGRITY_FAILED") from e
    try:
        data = json.loads(_inflate(packed))
    except (ValueError, UnicodeError) as e:
        raise RunError("ARCHIVE_BODY_INVALID") from e
    require(type(data) is dict and data.get("schema") == ARCHIVE_SCHEMA,
            "ARCHIVE_SCHEMA_INVALID")
    return data


def import_encrypted(archive_path: str | Path, secret: str,
                     new_store: str | Path) -> dict:
    """Restore only to a new private directory; re-verify entire V5 event chain."""
    archive = Path(archive_path).expanduser().resolve().read_bytes()
    data = _decrypt_envelope(archive, secret)
    try:
        source = base64.b64decode(data["source_srt_base64"], validate=True)
    except (ValueError, KeyError) as e:
        raise RunError("ARCHIVE_SOURCE_INVALID") from e
    require(data.get("source_sha256") == sha256(source), "ARCHIVE_SOURCE_HASH_CHANGED")
    manifest = data.get("manifest")
    require(type(manifest) is dict and
            data.get("manifest_sha256") == sha256(canonical(manifest)),
            "ARCHIVE_MANIFEST_CHANGED")
    events = data.get("events")
    require(type(events) is list and len(events) == data.get("event_count") and
            len(events) <= 250_000, "ARCHIVE_EVENT_CENSUS_INVALID")
    destination = Path(new_store).expanduser().resolve()
    require(not destination.exists(), "RESTORE_DESTINATION_MUST_BE_NEW")
    require(destination.parent.is_dir(), "RESTORE_PARENT_MISSING")
    staging = destination.with_name(destination.name + ".stage-" + secrets.token_hex(8))
    try:
        staging.mkdir(mode=0o700)
        _private_dir(staging / "events")
        _private_write_bytes(staging / "private_source.srt", source)
        _exclusive_json(staging / "source_manifest.json", manifest)
        _exclusive_json(staging / "run_lock.json", data["run_lock"])
        seen = set()
        for i, entry in enumerate(events, 1):
            require(type(entry) is dict and type(entry.get("name")) is str and
                    bool(NAME_PATTERN.fullmatch(entry["name"])) and
                    entry["name"].startswith(f"{i:06d}_") and
                    entry["name"] not in seen and
                    type(entry.get("value")) is dict,
                    "ARCHIVE_EVENT_NAME_OR_BODY_INVALID")
            seen.add(entry["name"])
            _exclusive_json(staging / "events" / entry["name"], entry["value"])
        recreated = ResearchRun(source, manifest, staging)
        result = recreated.replay()
        require(result["event_chain_head_sha256"] ==
                data.get("event_chain_head_sha256") and
                result["receipt_count"] == data["event_count"] and
                result["research_status"] == data.get("research_status"),
                "RESTORED_EVENT_HEAD_OR_STATUS_CHANGED")
        os.rename(staging, destination)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {
        "schema": ARCHIVE_SCHEMA,
        "source_sha256": sha256(source),
        "manifest_sha256": sha256(canonical(manifest)),
        "receipt_count": result["receipt_count"],
        "event_chain_head_sha256": result["event_chain_head_sha256"],
        "research_status": result["research_status"],
        "restored_store": str(destination),
        "verified_by_real_v5_replay": True,
    }


def reopen_private_store(path: str | Path) -> ResearchRun:
    """Reopen restored V5 session without previous chat or original ZIP."""
    folder = _private_dir(Path(path))
    source = (folder / "private_source.srt").read_bytes()
    manifest = json.loads((folder / "source_manifest.json").read_text("utf-8"))
    return ResearchRun(source, manifest, folder)


def main() -> int:
    parser = argparse.ArgumentParser(description="Encrypted V5 research snapshot")
    parser.add_argument("action", choices=["export", "restore", "inspect"])
    parser.add_argument("--store", required=True)
    parser.add_argument("--archive")
    parser.add_argument("--source-srt")
    parser.add_argument("--manifest-json")
    args = parser.parse_args()
    secret = os.environ.get("IRE_V5_ARCHIVE_SECRET")
    if args.action in {"export", "restore"}:
        require(bool(secret), "IRE_V5_ARCHIVE_SECRET_ENV_REQUIRED")
        require(bool(args.archive), "ARCHIVE_PATH_REQUIRED")
    if args.action == "export":
        require(args.source_srt and args.manifest_json,
                "SOURCE_AND_MANIFEST_REQUIRED")
        source = Path(args.source_srt).read_bytes()
        manifest = json.loads(Path(args.manifest_json).read_text("utf-8"))
        output = export_encrypted(ResearchRun(source, manifest, args.store),
                                  secret, args.archive)
    elif args.action == "restore":
        output = import_encrypted(args.archive, secret, args.store)
        output.pop("restored_store", None)
    else:
        output = reopen_private_store(args.store).status()
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RunError, OSError, KeyError, ValueError) as exc:
        print(json.dumps({"status": "FAILED_CLOSED", "reason": str(exc)}))
        sys.exit(2)
