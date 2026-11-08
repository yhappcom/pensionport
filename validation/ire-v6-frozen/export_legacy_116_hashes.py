#!/usr/bin/env python3
"""Export real canonical 116 approved claim fingerprints, without claim text.

This export is for a private ChatGPT original-SRT V6 ledger replay only.
It verifies exact Git blob identity and historical content immutability.
The exported baseline is a membership checksum set, NOT semantic accuracy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

CANONICAL_HEAD="f753ba57a1afabaa849f3eeca88170938c0b51f6"
CANONICAL_CLAIMS_GIT_BLOB="ab5af7eea02e65d5e36174546a2a94f4cc642d92"
CLAIMS_PATH=Path("data/claims.jsonl")
IDS=re.compile(r"GOMHEE-C[0-9]{1,3}\Z")


def git(*args):
    return subprocess.check_output(("git",)+args,text=True).strip()


def create_baseline() -> dict:
    if git("hash-object",str(CLAIMS_PATH)) != CANONICAL_CLAIMS_GIT_BLOB:
        raise ValueError("PROTECTED_LEGACY_116_CHANGED")
    if subprocess.run(("git","merge-base","--is-ancestor",CANONICAL_HEAD,"HEAD")).returncode:
        raise ValueError("CANONICAL_HEAD_NOT_ANCESTOR")
    if git("diff","--name-only",CANONICAL_HEAD,"HEAD","--",str(CLAIMS_PATH)):
        raise ValueError("PROTECTED_SOURCE_DIFF")
    raw=CLAIMS_PATH.read_bytes()
    records=[json.loads(x) for x in raw.decode("utf-8").splitlines() if x.strip()]
    if len(records)!=116:
        raise ValueError("EXACT_116_CLAIMS_REQUIRED")
    if any(set(x)!={"claim_id","topic","claim","supporting_videos","status","confidence"}
           or not IDS.fullmatch(x["claim_id"]) for x in records):
        raise ValueError("CANONICAL_CLAIM_SHAPE_CHANGED")
    if len({x["claim_id"] for x in records})!=116:
        raise ValueError("DUPLICATE_LEGACY_CLAIM_ID")
    entries=[]
    for claim in records:
        canonical=json.dumps(claim,ensure_ascii=False,sort_keys=True,
                             separators=(",",":")).encode("utf-8")
        entries.append({"id":claim["claim_id"],
                        "content_sha256":hashlib.sha256(canonical).hexdigest()})
    entries.sort(key=lambda x:x["id"])
    baseline={"schema":"IRE_V6_LEGACY_BASELINE_V1","entries":entries}
    direct_source="sz5N9WJS310"
    source_links=[c["claim_id"] for c in records if direct_source in c["supporting_videos"]]
    if source_links:
        raise ValueError("REAL_SOURCE_DIRECT_APPROVAL_UNEXPECTED")
    return {
        "schema":"IRE_V6_CANONICAL_LEGACY_BASELINE_EXPORT_V1",
        "exact_git_head":git("rev-parse","HEAD"),
        "protected_base_sha":CANONICAL_HEAD,
        "canonical_claims_git_blob_sha":CANONICAL_CLAIMS_GIT_BLOB,
        "canonical_claims_file_sha256":hashlib.sha256(raw).hexdigest(),
        "legacy116":baseline,
        "source_1_direct_approved_legacy_id_count":0,
        "real_private_srt_source_included":False,
        "existing_master_modified":False,
        "existing_relationships_semantically_adjudicated":False,
        "fact_accuracy_certified":False,
        "p0_go":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    report=create_baseline()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",
        encoding="utf-8")
    print("EXPORTED_HASH_ONLY_LEGACY_RECORDS",len(report["legacy116"]["entries"]))
    print("MASTER_GIT_BLOB",report["canonical_claims_git_blob_sha"])
    print("APPROVED_SOURCE1_DIRECT_RELATIONS",report["source_1_direct_approved_legacy_id_count"])
    print("INDEPENDENT_SEMANTIC_APPROVAL",report["existing_relationships_semantically_adjudicated"])


if __name__=="__main__":
    main()
