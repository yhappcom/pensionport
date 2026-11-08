"""Owner-held inventory digest check, NOT an owner-identity signature.

The expected inventory digest must be provisioned independently of the run;
a value derived from the same untrusted input is NOT an external trust anchor.
All source bytes stay private. Public event payloads contain hashes only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .codec import VIDEO, canonical, require_hash, require_identifier, sha256
from .errors import InvalidInput
from .source import verify_source, VerifiedSource

MAX_INVENTORY_BYTES = 1024 * 1024


@dataclass(frozen=True)
class AnchoredSource:
    source: VerifiedSource
    inventory_sha256: str
    inventory_count: int

    def attestation(self) -> dict:
        return {
            "schema": "IRE_V6_OWNER_SOURCE_ANCHOR_V1",
            "video_id": self.source.video_id,
            "source_sha256": self.source.source_sha256,
            "manifest_sha256": self.source.manifest_sha256,
            "cue_census_sha256": self.source.cue_census_sha256,
            "inventory_sha256": self.inventory_sha256,
            "inventory_video_count": self.inventory_count,
            "owner_identity_verified": False,
            "operator_held_inventory_digest_matched": True,
            "private_source_replayed_this_call": True,
        }


def verify_owner_inventory(raw: bytes, manifest: dict, inventory_bytes: bytes,
                           *, expected_inventory_sha256: str) -> AnchoredSource:
    """Bind raw video bytes to an externally pinned, canonical full inventory.

    The inventory has one entry per video, preventing cross-cohort duplicate
    video IDs and source bytes inside THIS pinned inventory. It does not prove
    that the operator-supplied pin was obtained from the actual rights owner.
    """
    expected_inventory_sha256 = require_hash(expected_inventory_sha256,
                                              "OWNER_INVENTORY_TRUST_PIN")
    if (type(inventory_bytes) is not bytes or not inventory_bytes or
        len(inventory_bytes) > MAX_INVENTORY_BYTES):
        raise InvalidInput("OWNER_INVENTORY_BYTES_REQUIRED")
    if sha256(inventory_bytes) != expected_inventory_sha256:
        raise InvalidInput("OWNER_INVENTORY_PIN_MISMATCH")
    try:
        registry = json.loads(inventory_bytes.decode("utf-8"))
        if canonical(registry) != inventory_bytes:
            raise InvalidInput("OWNER_INVENTORY_NONCANONICAL")
    except (UnicodeError, ValueError, TypeError) as exc:
        raise InvalidInput("OWNER_INVENTORY_JSON_INVALID") from exc
    if (type(registry) is not dict or set(registry) != {"schema", "entries"} or
        registry["schema"] != "IRE_V6_OWNER_INVENTORY_V1"):
        raise InvalidInput("OWNER_INVENTORY_SCHEMA_INVALID")
    entries = registry["entries"]
    if type(entries) is not list or not 1 <= len(entries) <= 2000:
        raise InvalidInput("OWNER_INVENTORY_CENSUS_INVALID")
    video_ids = set()
    source_shas = set()
    indexed = {}
    for entry in entries:
        if type(entry) is not dict or set(entry) != {
            "video_id", "source_sha256", "manifest_sha256", "cue_census_sha256"
        }:
            raise InvalidInput("OWNER_INVENTORY_ENTRY_SCHEMA_INVALID")
        video_id = require_identifier(entry["video_id"], VIDEO, "INVENTORY_VIDEO_ID")
        hashes = [require_hash(entry[k], "INVENTORY_" + k.upper()) for k in
                  ("source_sha256", "manifest_sha256", "cue_census_sha256")]
        if video_id in video_ids or hashes[0] in source_shas:
            raise InvalidInput("OWNER_INVENTORY_DUPLICATE_VIDEO_OR_SOURCE")
        video_ids.add(video_id)
        source_shas.add(hashes[0])
        indexed[video_id] = entry
    if type(manifest) is not dict:
        raise InvalidInput("OWNER_INVENTORY_MANIFEST_REQUIRED")
    entry = indexed.get(manifest.get("video_id"))
    if entry is None:
        raise InvalidInput("OWNER_INVENTORY_VIDEO_NOT_LISTED")
    verified = verify_source(raw, manifest,
                             expected_source_sha256=entry["source_sha256"],
                             expected_manifest_sha256=entry["manifest_sha256"])
    if verified.cue_census_sha256 != entry["cue_census_sha256"]:
        raise InvalidInput("OWNER_INVENTORY_CUE_CENSUS_MISMATCH")
    return AnchoredSource(verified, expected_inventory_sha256, len(entries))
