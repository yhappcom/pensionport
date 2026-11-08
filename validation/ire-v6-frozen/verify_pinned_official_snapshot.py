#!/usr/bin/env python3
"""Revalidate first-party public raw snapshot originally fetched by GitHub Actions.

The pinned GitHub artifact comes from a prior successful HTTPS capture. Offline
hash validation prevents an unrelated transient public-site DNS failure from
invalidating canonical V5/V6 regression tests. Pinned snapshot is NOT fresh
law or human semantic fact approval. It expires and must be renewed separately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RECORDS = {
    "decree_40_3": {
        "filename": "decree_40_3.html",
        "sha256": "5540ac2a9ecfad76382580cf7f46c947e2e0f11469ac700f4855b3a16f9115c2",
        "bytes": 78056,
        "effective_date": "2026-10-01",
    },
    "nts_pension": {
        "filename": "nts_pension.html",
        "sha256": "9cd242c9778c6248dba8c01e6bfa35e7fcc649347714ab57a348f6881dbb107d",
        "bytes": 200399,
        "effective_date": None,
    },
}
MANIFEST_SHA256 = "32d837d4b60ee0f43b4c0af741690acdf54445d64cc49b8938340aa089b23fe1"
SOURCE_ARTIFACT_ID = 13610822539
SOURCE_RUN_ID = 42464865238
EXPIRATION_UTC = "2026-11-22T08:54:23Z"


def validate_record(record: dict, pin: dict):
    if type(record) is not dict:
        raise ValueError("SNAPSHOT_RECORD_MISSING")
    if (record.get("source_id") not in RECORDS or
            record.get("artifact_name") != pin["filename"] or
            record.get("captured_body_sha256") != pin["sha256"] or
            record.get("captured_body_bytes") != pin["bytes"] or
            record.get("visible_effective_date") != pin["effective_date"]):
        raise ValueError("SNAPSHOT_RECORD_METADATA_DRIFT")
    if (record.get("finance_fact_approved") is not False or
            record.get("issuer_digital_signature_verified") is not False or
            record.get("independent_semantic_support_verified") is not False or
            record.get("p0_go") is not False):
        raise ValueError("SNAPSHOT_FALSE_AUTHORITY_OR_GO")


def verify(directory: Path) -> dict:
    if not directory.is_dir():
        raise ValueError("PINNED_GITHUB_ARTIFACT_NOT_AVAILABLE")
    expected_names = {"capture_manifest.json"} | {x["filename"] for x in RECORDS.values()}
    names = {p.name for p in directory.iterdir() if p.is_file()}
    if names != expected_names:
        raise ValueError("PINNED_SNAPSHOT_UNEXPECTED_OR_MISSING_FILE")
    manifest_bytes = (directory/"capture_manifest.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise ValueError("ORIGINAL_CAPTURE_MANIFEST_TAMPERED")
    manifest = json.loads(manifest_bytes)
    if (manifest.get("schema") != "IRE_V6_OFFICIAL_RAW_SOURCE_EVIDENCE_V1" or
            manifest.get("private_original_srt_included") is not False or
            manifest.get("precision_recall_measured") is not False or
            manifest.get("human_review_completed") is not False or
            manifest.get("p0_go") is not False):
        raise ValueError("ORIGINAL_CAPTURE_AUTHORITY_CHANGED")
    record_map = {v["source_id"]:v for v in manifest["records"]}
    if set(record_map)!=set(RECORDS) or len(manifest["records"])!=len(RECORDS):
        raise ValueError("SOURCE_CENSUS_DRIFT")
    for key,pin in sorted(RECORDS.items()):
        b=(directory/pin["filename"]).read_bytes()
        if len(b)!=pin["bytes"] or hashlib.sha256(b).hexdigest()!=pin["sha256"]:
            raise ValueError("OFFICIAL_RAW_RESPONSE_TAMPERED:"+key)
        validate_record(record_map[key],pin)
    return {
        "schema":"IRE_V6_PINNED_OFFICIAL_RAW_REPLAY_V1",
        "original_capture_run_id":SOURCE_RUN_ID,
        "original_capture_artifact_id":SOURCE_ARTIFACT_ID,
        "original_artifact_expires_at":EXPIRATION_UTC,
        "government_raw_body_files_reverified":2,
        "all_body_bytes_hash_match":True,
        "live_government_site_contacted_this_run":False,
        "effective_date_scope_independently_reviewed":False,
        "financial_atomic_claim_approved":False,
        "semantic_accuracy_measured":False,
        "p0_go":False,
        "status":"OFFICIAL_FIRST_PARTY_ORIGINAL_BYTES_REPLAY_PASS_NOT_FACT_APPROVAL"
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--directory",type=Path,required=True)
    args=ap.parse_args()
    try:
        result=verify(args.directory)
    except (OSError,ValueError,KeyError,TypeError) as e:
        print("PINNED_OFFICIAL_REPLAY_BLOCKED",type(e).__name__,str(e),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
