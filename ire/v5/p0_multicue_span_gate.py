"""V5 cross-window source-cue coverage contract (structural + optional private replay).

A single anchor is not enough to demonstrate that an adjacent caveat, amount or
assumption was considered. This requires an explicit, SHA-pinned disposition
of EVERY cue in the declared cross-window span and a list of reviewer-selected
material roles. It does not infer or certify that the selected roles or span
are semantically complete. A separate independent blinded adjudicator remains
mandatory before any financial fact approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile

from .engine import cues_from_srt, RunError
from .p0_claim_ownership_gate import (
    REGISTRY as OWNER_REGISTRY,
    _record_window_plan,
    validate_claim_ownership,
    verify_private_source,
)

SCHEMA = "IRE_V5_P0_MULTICUE_CONTEXT_V1"
REGISTRY_SCHEMA = "IRE_V5_P0_MULTICUE_CONTEXT_REGISTRY_V1"
REGISTRY = Path("ire/v5/validation/p0_multicue_context_registry.json")
SHA = re.compile(r"[0-9a-f]{64}\Z")
TIME = re.compile(r"(?:[0-9]{2}:){2}[0-9]{2},[0-9]{3}\Z")
ROLES = {
    "CONTEXT", "FORECAST", "QUALIFIER", "RISK_CONDITION", "ACTION",
    "BORROWING", "AMOUNT", "AGGREGATE_AMOUNT", "TIME", "SPEAKER_TURN",
    "EXCEPTION", "ASSUMPTION", "CAUSAL_LINK", "OUTCOME",
}
NON_MATERIAL = {"CONTEXT", "SPEAKER_TURN"}


class MultiCueSpanError(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise MultiCueSpanError(reason)


def _safe_path(root: Path, rel: str) -> Path:
    require(type(rel) is str and rel.startswith("ire/v5/validation/") and
            rel.endswith(".json") and not Path(rel).is_absolute() and
            all(x not in ("", ".", "..") for x in Path(rel).parts),
            "UNSAFE_MULTICUE_PATH")
    f = (root / rel).resolve()
    require(f.is_relative_to((root / "ire/v5/validation").resolve()) and f.is_file(),
            "MULTICUE_FILE_MISSING_OR_ESCAPED")
    return f


def _load_registry(root: Path, registry_path: Path | None = None):
    root = Path(root).resolve()
    f = root / REGISTRY if registry_path is None else Path(registry_path)
    obj = json.loads(f.read_text("utf-8"))
    require(type(obj) is dict and obj.get("schema") == REGISTRY_SCHEMA and
            obj.get("p0_go") is False and
            type(obj.get("entries")) is list and bool(obj["entries"]),
            "MULTICUE_REGISTRY_SCHEMA")
    owner_registry = json.loads((root / OWNER_REGISTRY).read_text("utf-8"))
    require(type(owner_registry) is dict and
            type(owner_registry.get("entries")) is list, "OWNER_REGISTRY_MISSING")
    owner_pins = {
        x["path"]: x["record_sha256"] for x in owner_registry["entries"]
    }
    seen = set()
    rows = []
    for entry in obj["entries"]:
        require(type(entry) is dict, "MULTICUE_ENTRY_INVALID")
        path = entry.get("path")
        require(path not in seen, "MULTICUE_DUPLICATE_FILE")
        seen.add(path)
        content = _safe_path(root, path).read_bytes()
        require(type(entry.get("record_sha256")) is str and
                SHA.fullmatch(entry["record_sha256"]) is not None and
                hashlib.sha256(content).hexdigest() == entry["record_sha256"],
                "MULTICUE_RECORD_HASH_DRIFT")
        doc = json.loads(content)
        owner_path = doc.get("owner_record_path")
        owner_file = _safe_path(root, owner_path)
        require(owner_path in owner_pins and
                owner_pins[owner_path] == doc.get("owner_record_sha256"),
                "MULTICUE_OWNER_NOT_CANONICALLY_PINNED")
        owner_bytes = owner_file.read_bytes()
        require(hashlib.sha256(owner_bytes).hexdigest() ==
                doc["owner_record_sha256"], "MULTICUE_OWNER_RECORD_DRIFT")
        rows.append((doc, json.loads(owner_bytes)))
    return rows


def validate_multicue_record(doc: dict, owner: dict) -> dict:
    """No truth verification: require declared multi-cue span proof and OPEN gate."""
    require(type(doc) is dict and doc.get("schema") == SCHEMA,
            "MULTICUE_SCHEMA_INVALID")
    validate_claim_ownership(owner)
    require(doc.get("video_id") == owner["video_id"] and
            doc.get("source_sha256") == owner["source_sha256"] and
            doc.get("archive_sha256") == owner["archive_sha256"],
            "MULTICUE_SOURCE_IDENTITY_DRIFT")
    require(doc.get("source_bytes_replayed_by_public_ci") is False and
            doc.get("independent_recall_certified") is False and
            doc.get("p0_go") is False,
            "MULTICUE_FALSE_QUALITY_APPROVAL")
    owner_map, _ = _record_window_plan(owner)
    claims = {c["candidate_id"]: c for c in owner["claims"]}
    must_review = {c["candidate_id"] for c in owner["claims"]
                   if c["cross_window_context_open"] is True}
    cases = doc.get("cases")
    require(type(cases) is list and bool(cases), "MULTICUE_CASES_MISSING")
    require(len(cases) <= 100000, "MULTICUE_CASES_TOO_MANY")
    seen = set()
    cue_count = 0
    for case in cases:
        require(type(case) is dict and type(case.get("candidate_id")) is str,
                "MULTICUE_CASE_BAD_ID")
        cid = case["candidate_id"]
        require(cid not in seen and cid in must_review, "MULTICUE_UNKNOWN_OR_DUPLICATE_CLAIM")
        seen.add(cid)
        claim = claims[cid]
        first, last = claim["context_first_cue"], claim["context_last_cue"]
        require(case.get("first_cue") == first and case.get("last_cue") == last and
                case.get("window_id") == claim["window_id"] and
                case.get("anchor_cue") == claim["anchor_cue"],
                "MULTICUE_CROSS_WINDOW_SPAN_DRIFT")
        require(case.get("status") == "OPEN_SECOND_PASS_REQUIRED" and
                case.get("independent_blind_reviewed") is False and
                case.get("material_semantics_certified") is False and
                case.get("financial_fact_approved") is False,
                "MULTICUE_UNSUPPORTED_SEMANTIC_CLOSURE")
        required = case.get("required_roles")
        require(type(required) is list and bool(required) and
                len(required) == len(set(required)) and
                set(required) <= ROLES and
                set(required).isdisjoint(NON_MATERIAL),
                "MULTICUE_REQUIRED_ROLES_INVALID")
        coverage = case.get("cue_coverage")
        require(type(coverage) is list and
                [x.get("cue_index") for x in coverage if type(x) is dict] ==
                list(range(first, last + 1)) and
                len(coverage) == last - first + 1,
                "MULTICUE_MISSING_OR_DUPLICATED_CONTEXT_CUE")
        covered_roles = set()
        covered_owners = set()
        substantive_after_boundary = False
        for row in coverage:
            n = row["cue_index"]
            covered_owners.add(owner_map[n])
            digest = row.get("cue_sha256")
            require(type(digest) is str and SHA.fullmatch(digest) is not None,
                    "MULTICUE_CUE_HASH_FORMAT_INVALID")
            t = row.get("start_time")
            require(type(t) is str and TIME.fullmatch(t) is not None,
                    "MULTICUE_TIMESTAMP_FORMAT_INVALID")
            roles = row.get("roles")
            require(type(roles) is list and bool(roles) and
                    len(roles) == len(set(roles)) and set(roles) <= ROLES,
                    "MULTICUE_CUE_ROLE_INVALID")
            note = row.get("role_note")
            require(type(note) is str and len(note.strip()) >= 15 and
                    not any(key in row for key in
                            ("raw_srt", "transcript", "raw_cue_text", "quote")),
                    "MULTICUE_ROLE_REASON_REQUIRED_OR_PRIVATE_TEXT")
            covered_roles.update(roles)
            if owner_map[n] != claim["window_id"] and not set(roles) <= NON_MATERIAL:
                substantive_after_boundary = True
            if n == claim["anchor_cue"]:
                require(digest == claim["anchor_cue_sha256"] and
                        t == claim["anchor_start_time"],
                        "MULTICUE_ANCHOR_SOURCE_DRIFT")
        require(len(covered_owners) == 2 and substantive_after_boundary,
                "MULTICUE_ADJACENT_MATERIAL_NOT_REVIEWED")
        require(set(required) <= covered_roles,
                "MULTICUE_REQUIRED_MATERIAL_SLOT_MISSING")
        cue_count += len(coverage)
    require(seen == must_review, "MULTICUE_UNREGISTERED_CROSS_WINDOW_CLAIM")
    return {
        "video_id": owner["video_id"],
        "multicue_claims_reviewed_structurally": len(cases),
        "source_cues_with_roles": cue_count,
        "cross_window_owner_census_complete": True,
        "private_original_spans_replayed": False,
        "semantic_role_labels_independently_verified": False,
        "p0_go": False,
    }


def verify(root: Path, registry_path: Path | None = None) -> dict:
    rows = _load_registry(Path(root).resolve(), registry_path)
    results = [validate_multicue_record(doc, owner) for doc, owner in rows]
    seen = set()
    for doc, _ in rows:
        for case in doc["cases"]:
            key = (doc["video_id"], case["candidate_id"])
            require(key not in seen, "MULTICUE_REPEATED_ATOM_ACROSS_BATCHES")
            seen.add(key)
    return {
        "schema": "IRE_V5_P0_MULTICUE_SPAN_GATE_V1",
        "batches": len(results),
        "claims_with_complete_declared_context_census": sum(
            r["multicue_claims_reviewed_structurally"] for r in results),
        "cue_roles_reviewed_structurally": sum(
            r["source_cues_with_roles"] for r in results),
        "private_original_spans_replayed": False,
        "independent_semantic_recall_proven": False,
        "p0_go": False,
    }


def verify_private(root: Path, private_zip: Path,
                   registry_path: Path | None = None) -> dict:
    """Replay private source digest/time for EVERY context cue, not just anchors."""
    root = Path(root).resolve()
    private_zip = Path(private_zip)
    # Existing archive SHA, original source, every anchor and every window is
    # checked first. It does not certify semantic accuracy.
    private_owner = verify_private_source(root, private_zip)
    rows = _load_registry(root, registry_path)
    records = [validate_multicue_record(doc, owner) for doc, owner in rows]
    require(private_owner["source_original_bytes_replayed"] is True,
            "MULTICUE_OWNER_SOURCE_REPLAY_NOT_COMPLETE")
    source_cache = {}
    cues_checked = 0
    with zipfile.ZipFile(private_zip, "r") as z:
        for doc, _ in rows:
            video = doc["video_id"]
            if video not in source_cache:
                filename = f"youtube-transcript-{video}.srt"
                names = [x for x in z.infolist() if not x.is_dir() and
                         x.filename.split("/")[-1] == filename and
                         "__MACOSX" not in x.filename.split("/")]
                require(len(names) == 1 and names[0].file_size <= 15_000_000,
                        "MULTICUE_PRIVATE_MEMBER_AMBIGUOUS")
                raw = z.read(names[0])
                require(hashlib.sha256(raw).hexdigest() == doc["source_sha256"],
                        "MULTICUE_PRIVATE_SRT_SOURCE_MISMATCH")
                try:
                    source_cache[video] = (hashlib.sha256(raw).hexdigest(),
                                           cues_from_srt(raw))
                except (RunError, UnicodeError) as e:
                    raise MultiCueSpanError("MULTICUE_PRIVATE_SOURCE_PARSE_ERROR") from e
            source_hash, cues = source_cache[video]
            require(source_hash == doc["source_sha256"],
                    "MULTICUE_PRIVATE_BATCH_SOURCE_DRIFT")
            for case in doc["cases"]:
                for row in case["cue_coverage"]:
                    idx = row["cue_index"]
                    require(idx in cues, "MULTICUE_PRIVATE_CUE_NOT_PRESENT")
                    cue = cues[idx]
                    require(hashlib.sha256(cue.text.encode("utf-8")).hexdigest() ==
                            row["cue_sha256"], "MULTICUE_PRIVATE_CUE_DIGEST_MISMATCH")
                    ms = cue.start_ms
                    t = (f"{ms//3600000:02d}:{(ms//60000)%60:02d}:"
                         f"{(ms//1000)%60:02d},{ms%1000:03d}")
                    require(row["start_time"] == t,
                            "MULTICUE_PRIVATE_CUE_TIMESTAMP_MISMATCH")
                    cues_checked += 1
    return {
        "schema": "IRE_V5_P0_MULTICUE_PRIVATE_REPLAY_V1",
        "original_private_cues_replayed": cues_checked,
        "multicue_cases_structurally_reviewed": sum(
            r["multicue_claims_reviewed_structurally"] for r in records),
        "source_original_bytes_replayed": True,
        "independent_semantic_completeness_proven": False,
        "p0_go": False,
    }
