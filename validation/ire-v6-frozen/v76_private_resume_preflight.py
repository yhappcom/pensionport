"""Privacy-safe, fail-closed preflight for resuming V75 owner-only semantic work.

This does not extract claims or approve investment advice. SRT text is never
printed, persisted, or sent to GitHub. Queue membership must be reviewed by the
human/host AFTER this preflight; a SHA match is only evidence of byte identity.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

EXPECTED_SOURCE_ZIP = "00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
EXPECTED_V75_ZIP = "752f4f568c77eeb84695f6248315f4e7a4ad185763dcdd3d571faca497b02071"
EXPECTED_V75_BYTES = 1920514
EXPECTED_V75_ENTRY_COUNT = 11
EXPECTED_V75_BLOB_SHA = {
    "meaning60": "a31572a60daf171808718922740876d8f22343311f6d1126699807aafc172367",
    "queue298": "4252e656a72045ad9a1719161d316e4f6703ffaabd051c5641c4ab27f41102e4",
    "receipt": "0698d271741b123df9c5506217893d1e72f2ecebde61ba03c4f8d1cd6605e60d",
    "sqlite": "7cd1d30a2afec2a64fddbad1d913c6d8fc4d6391b90c6ac645a529bb1c839747",
}
VIDEO_CENSUS = (
    (1, "sz5N9WJS310", 1195, "2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f"),
    (2, "6VEfKF7BzZU", 1347, "a59b2fd424011c3f572aa52404411ff4ea435f6dd1e7e27e4f5c9e11f7218b72"),
    (3, "OiDTNstaSpM", 785, "e94b12a1084a8b57c3b9c2a630e27f840ae5a827b3a71c62526e15380a7c57bd"),
    (4, "aNfGrcO6WPI", 758, "853db2d4f01ab71bbc4f86b46714f4341aa32aa2bc07416f705a937b620ea12b"),
    (5, "qtluAViPpsQ", 1044, "af4fb6b702c5497e5c17bc7b9a3e87855a5488dd263cded32be9a09cec67a543"),
)
# Eight pre-existing OPEN cases collapse to these four cue anchors.
V42_CUE_ANCHORS = {
    ("6VEfKF7BzZU", 425): "fea1bc3a8f45469fb25230014108b01865ef47a0474385f7de0fdc2258f387e3",
    ("6VEfKF7BzZU", 520): "9c8de7c4c5e87403ba61f67250d45e1cdc57f8facbe0e46fcbd2dbf1b7a12085",
    ("sz5N9WJS310", 561): "6272dd49f96ceff5fd9dbff42b1b804a1ee905053031ffce7c2537e980b55b41",
    ("sz5N9WJS310", 618): "d9e801e3c3123081859a3fadf9a38e941252d30c7a7321ce425036b07cf3c311",
}
CUE_FORMAT = re.compile(r"(\d+)\s*\n\s*(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n([\s\S]*)\Z")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(1 << 20):
            h.update(data)
    return h.hexdigest()


def source_audit(source_zip: Path, expected_source_sha=EXPECTED_SOURCE_ZIP,
                 census=VIDEO_CENSUS, anchors=V42_CUE_ANCHORS) -> dict:
    if not source_zip.is_file():
        raise ValueError("OWNER_ORIGINAL_SOURCE_MISSING")
    if file_sha256(source_zip) != expected_source_sha:
        raise ValueError("OWNER_ORIGINAL_SOURCE_SHA_MISMATCH")
    result = []
    checked_anchors = 0
    with zipfile.ZipFile(source_zip) as z:
        paths = z.namelist()
        for number, vid, cue_count, source_sha in census:
            hits = [p for p in paths if p.endswith(f"{vid}.srt") and not p.startswith("__MACOSX/")]
            if len(hits) != 1:
                raise ValueError("SOURCE_VIDEO_ID_NOT_UNIQUE")
            raw = z.read(hits[0])
            if hashlib.sha256(raw).hexdigest() != source_sha:
                raise ValueError("ORIGINAL_VIDEO_SRT_SHA_MISMATCH")
            chunks = re.split(r"\r?\n\s*\r?\n", raw.decode("utf-8-sig").strip())
            if len(chunks) != cue_count:
                raise ValueError("ORIGINAL_CUE_COUNT_MISMATCH")
            for i, chunk in enumerate(chunks, 1):
                m = CUE_FORMAT.fullmatch(chunk)
                if m is None or int(m.group(1)) != i or m.group(2) > m.group(3):
                    raise ValueError("INVALID_CUE_FORMAT_ORDER_OR_TIME")
                anchor = anchors.get((vid, i))
                if anchor is not None:
                    if hashlib.sha256(m.group(4).encode("utf-8")).hexdigest() != anchor:
                        raise ValueError("SOURCE_CUE_ANCHOR_SHA_MISMATCH")
                    checked_anchors += 1
            result.append({"video_no": number, "video_id": vid, "cues": cue_count,
                           "source_sha256": source_sha})
    if checked_anchors != len(anchors):
        raise ValueError("MISSING_HISTORICAL_CUE_ANCHOR")
    return {"source_original_sha256": expected_source_sha,
            "original_video_census": result,
            "original_cues_checked": sum(row["cues"] for row in result),
            "original_40cue_windows": sum((row["cues"]+39)//40 for row in result),
            "historical_open_cases_with_rebound_source_anchors": 8 if len(anchors) == 4 else None,
            "unique_original_anchor_cues_checked": checked_anchors,
            "original_srt_text_exposed": False}


def bundle_audit(bundle: Path, expected_zip_sha=EXPECTED_V75_ZIP,
                 expected_bytes=EXPECTED_V75_BYTES,
                 expected_entries=EXPECTED_V75_ENTRY_COUNT,
                 expected_blob_sha=EXPECTED_V75_BLOB_SHA) -> dict:
    if not bundle.is_file():
        raise ValueError("V75_PRIVATE_BUNDLE_MISSING")
    if bundle.stat().st_size != expected_bytes or file_sha256(bundle) != expected_zip_sha:
        raise ValueError("V75_PRIVATE_BUNDLE_SHA_OR_SIZE_MISMATCH")
    hashes = {}
    with zipfile.ZipFile(bundle) as z:
        entries = z.infolist()
        if len(entries) != expected_entries or len(set(x.filename for x in entries)) != len(entries):
            raise ValueError("V75_BUNDLE_ENTRY_COUNT_OR_NAME_COLLISION")
        for item in entries:
            pp = PurePosixPath(item.filename)
            if pp.is_absolute() or ".." in pp.parts or "\\" in item.filename:
                raise ValueError("UNSAFE_ZIP_MEMBER_NAME")
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("ZIP_SYMLINK_NOT_ALLOWED")
            if item.is_dir():
                continue
            if item.file_size > 32 * 1024 * 1024:
                raise ValueError("OVERSIZED_PRIVATE_BUNDLE_MEMBER")
            h = hashlib.sha256()
            with z.open(item) as stream:
                while data := stream.read(1 << 20):
                    h.update(data)
            hashes.setdefault(h.hexdigest(), []).append(item.filename)
    missing = [kind for kind, sha in expected_blob_sha.items() if sha not in hashes]
    if missing:
        raise ValueError("V75_REQUIRED_RECEIPT_BLOB_MISSING:" + ",".join(sorted(missing)))
    return {"v75_private_zip_sha256": expected_zip_sha, "v75_private_zip_bytes": expected_bytes,
            "v75_private_entries": expected_entries,
            "v75_required_private_blob_hashes_confirmed": sorted(expected_blob_sha),
            "v75_queue_exact_bytes_available_for_source_first_host_review": True}


def preflight(source_zip: Path, bundle: Path | None) -> dict:
    out = {"schema": "IRE_V6_V76_FAIL_CLOSED_PRIVATE_RESUME_PREFLIGHT_V1",
           "v75_head": "829bcfbeb57431abd5c0e4e22e344b7aacf5d079",
           "new_semantic_parent_reviews": 0,
           "v75_remaining_context_risk": 298,
           "original_total_pending": 887,
           "historical_finance_issuer_audio_case_approvals": 0,
           "official_300_supplemental_416_merged": False,
           "external_finance_fact_truth_certified": False,
           "p0_go": False, "personal_advice_approved": False}
    try:
        out["source"] = source_audit(source_zip)
    except (ValueError, OSError, zipfile.BadZipFile, UnicodeError) as e:
        out["status"] = "BLOCKED_SOURCE_PROVENANCE"
        out["reason"] = str(e)
        return out
    try:
        out["bundle"] = bundle_audit(bundle) if bundle else None
    except (ValueError, OSError, zipfile.BadZipFile) as e:
        out["status"] = "BLOCKED_PRIVATE_V75_QUEUE_CUSTODY"
        out["reason"] = str(e)
        return out
    if bundle is None:
        out["status"] = "BLOCKED_PRIVATE_V75_QUEUE_CUSTODY"
        out["reason"] = "V75_PRIVATE_BUNDLE_MISSING"
        return out
    out["status"] = "READY_FOR_SOURCE_FIRST_HOST_REVIEW_NOT_P0_GO"
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--v75-private-zip", type=Path)
    args = parser.parse_args()
    r = preflight(args.source_zip, args.v75_private_zip)
    print(json.dumps(r, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if r["status"].startswith("READY_FOR_") else 2


if __name__ == "__main__":
    sys.exit(main())