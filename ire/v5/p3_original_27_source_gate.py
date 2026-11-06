"""Verify #1 W41-W67 source-cue claims without promoting provisional law or advice.

The live chat host compared all 67 compact window hashes to 2026-11-06
Drive original 1-100.zip and found exact SRT identity. GitHub CI does NOT
contain that private ZIP. --source-zip independently replays the same
proof when the owner supplies it. Archive bytes can differ from earlier
1-70 bundle while the five identical SRT bytes remain authoritative.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from .first_five_window_review_gate import source_windows

LEDGER=Path("ire/v5/validation/first_five_video1_w41_w67_source_atomic_review_20261106.json")
COMPACT=Path("ire/v5/validation/v5_first_five_video_01_window_review_20261106.json")
VIDEO_ID="sz5N9WJS310"
EXPECTED_SRT_SHA="2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f"
EXPECTED_100_ZIP_SHA="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
EXPECTED_OLD_ZIP_SHA="00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
KNOWN_HOSTS={"nts.go.kr","www.nts.go.kr","d.nts.go.kr",
 "regulation.krx.co.kr","law.go.kr","www.law.go.kr",
 "law.kofia.or.kr","m.shinhansec.com"}
CLAIM_KINDS={"TRANSCRIPTION_AMBIGUOUS","NUMERIC_HYPOTHESIS",
 "REGULATORY_REJECTED_OVERGENERAL","REGULATORY_SUPPORTED_SCOPED",
 "VIDEO_OPINION","VIDEO_QUESTION","HISTORICAL_CONTEXT",
 "NONFINANCIAL","PRODUCT_UNVERIFIED"}
HEX=re.compile(r"^[0-9a-f]{64}$")


class P3SourceError(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise P3SourceError(code)


def read(root: Path, path: Path) -> dict:
    return json.loads((Path(root)/path).read_text(encoding="utf-8"))


def verify(root: Path, *, source_zip: Path | None = None,
           replacement: dict | None = None) -> dict:
    root=Path(root)
    ledger=read(root,LEDGER) if replacement is None else replacement
    compact=read(root,COMPACT)
    provenance=ledger.get("provenance",{})
    scope=ledger.get("scope",{})
    require(ledger.get("schema")=="IRE_V5_P3_VIDEO1_W41_W67_SOURCE_ATOMIC_REVIEW_V1"
            and ledger.get("as_of")=="2026-11-06"
            and provenance.get("original_video_id")==VIDEO_ID
            and provenance.get("original_srt_sha256")==EXPECTED_SRT_SHA
            and provenance.get("input_archive_sha256")==EXPECTED_100_ZIP_SHA
            and provenance.get("historical_archive_sha256_different")==EXPECTED_OLD_ZIP_SHA
            and provenance.get("raw_original_archive_committed_to_github") is False
            and provenance.get("raw_source_bytes_replayed_by_github_ci") is False
            and provenance.get("asr_audio_verification_completed") is False
            and ledger.get("release")==
                "ORIGINAL_SRT_REPLAYED_AND_SOURCE_CUE_ADJUDICATED_EDUCATIONAL_SCOPE_ONLY",
            "P3_FALSE_SOURCE_OR_RELEASE")
    require(scope.get("reviewed_windows")==27 and scope.get("reviewed_cues")==486
            and scope.get("first_window")=="W00041"
            and scope.get("last_window")=="W00067"
            and scope.get("first_cue")==710 and scope.get("last_cue")==1195
            and scope.get("all_27_source_window_hashes_matched") is True
            and scope.get("source_content_in_chat_replayed") is True
            and scope.get("entire_5_video_atomic_recall_certified") is False
            and scope.get("independent_blind_reviewer_completed") is False
            and scope.get("formal_v5_engine_receipts_issued")==0
            and scope.get("financial_rule_entire_video_claims_approved")==0
            and scope.get("personalized_advice_approved") is False,
            "P3_FALSE_RESEARCH_CERTIFICATION")
    sources=ledger.get("source_catalog",{})
    require(type(sources) is dict and len(sources)>=6,
            "P3_OFFICIAL_SOURCE_CATALOG_MISSING")
    for entry in sources.values():
        url=entry.get("url","")
        parsed=urlparse(url)
        require(parsed.scheme=="https" and parsed.netloc in KNOWN_HOSTS
                and not parsed.username and not parsed.password
                and entry.get("authority") and entry.get("effective"),
                "P3_UNTRUSTED_OFFICIAL_REFERENCE")
    windows=ledger.get("windows")
    require(type(windows) is list and len(windows)==27
            and len(compact.get("records",[]))==67,
            "P3_WINDOW_MANIFEST_WRONG_COUNT")
    ids=set()
    histogram=collections.Counter()
    checked_cues=set()
    claims=0
    for idx,(w,original) in enumerate(zip(windows,compact["records"][40:]),41):
        require(w.get("window_id")==f"W{idx:05d}"==original["window_id"]
                and all(w.get(key)==original[oldkey]
                    for key,oldkey in (
                        ("first_cue","first_cue"),("last_cue","last_cue"),
                        ("start_ms","start_ms"),("end_ms","end_ms"),
                        ("source_window_sha256","primary_text_sha256"),
                        ("original_semantic_summary","semantic_summary"),
                        ("original_risk_review_codes","risk_review_codes")))
                and w.get("source_bytes_verified_by_current_chat_host") is True
                and w.get("official_legal_truth_independent_expert_certified") is False
                and w.get("all_atomic_recall_independently_measured") is False,
                "P3_SOURCE_WINDOW_CUE_ANCHOR_TAMPERED")
        rawclaims=w.get("claims",[])
        require(type(rawclaims) is list and len(rawclaims)>=1,
                "P3_NO_ATOMIC_CLAIM_REVIEW")
        covered=set()
        for c in rawclaims:
            cid=c.get("claim_id")
            require(isinstance(cid,str) and re.fullmatch(r"FV5-P3-\\d{4}",cid)
                    and cid not in ids
                    and c.get("meaning_class") in CLAIM_KINDS
                    and type(c.get("source_cue_start")) is int
                    and type(c.get("source_cue_end")) is int
                    and w["first_cue"]<=c["source_cue_start"]<=c["source_cue_end"]<=w["last_cue"]
                    and len(str(c.get("paraphrase","")).strip())>=20
                    and c.get("formal_financial_fact_approved") is False
                    and c.get("personal_application_approved") is False,
                    "P3_ATOMIC_CLAIM_INVALID_OR_FALSE_APPROVAL")
            refs=c.get("official_context_source_ids",[])
            require(type(refs) is list and
                    all(isinstance(ref,str) and ref in sources for ref in refs)
                    and (bool(refs) if c["meaning_class"]==
                         "REGULATORY_SUPPORTED_SCOPED" else True),
                    "P3_BAD_OFFICIAL_SCOPE_LINK")
            covered.update(range(c["source_cue_start"],c["source_cue_end"]+1))
            ids.add(cid);claims+=1;histogram[c["meaning_class"]]+=1
        contexts=w.get("non_claim_cues",[])
        require(type(contexts) is list and
                all(type(cue) is int and w["first_cue"]<=cue<=w["last_cue"]
                    for cue in contexts)
                and covered|set(contexts)==set(range(w["first_cue"],w["last_cue"]+1))
                and not (covered&set(contexts)),
                "P3_SOURCE_CUE_NOT_DISPOSITIONED")
        checked_cues.update(range(w["first_cue"],w["last_cue"]+1))
    require(claims==scope.get("source_anchored_claim_candidates")
            and claims==len(ids)
            and scope.get("source_anchored_claim_candidates")==89
            and set(ids)=={f"FV5-P3-{n:04d}" for n in range(1,90)}
            and len(checked_cues)==486 and checked_cues==set(range(710,1196))
            and dict(histogram)==ledger.get("claim_classes"),
            "P3_ATOMIC_CLAIM_COUNTER_OR_SCOPE_INVALID")
    # Passing without --source-zip proves frozen-record consistency only.
    replay=False
    if source_zip is not None:
        p=Path(source_zip)
        require(p.is_file(),"P3_ORIGINAL_SOURCE_ZIP_MISSING")
        archive_sha=hashlib.sha256(p.read_bytes()).hexdigest()
        require(archive_sha==EXPECTED_100_ZIP_SHA,
                "P3_ORIGINAL_SOURCE_ARCHIVE_HASH_CHANGED")
        with zipfile.ZipFile(p) as archive:
            expected=f"youtube-transcript-{VIDEO_ID}.srt"
            candidates=[n for n in archive.namelist()
                if not n.startswith("__MACOSX/")
                and (n==expected or n.endswith("/"+expected))]
            require(len(candidates)==1,"P3_ORIGINAL_SRT_NOT_UNIQUE")
            raw=archive.read(candidates[0])
        require(hashlib.sha256(raw).hexdigest()==EXPECTED_SRT_SHA,
                "P3_SRT_SOURCE_HASH_MISMATCH")
        source=source_windows(raw)
        require(len(source)==67 and all(
            all(x[k]==y[k] for k in x)
            for x,y in zip(source,compact["records"])),
            "P3_FULL_67_ORIGINAL_WINDOW_REPLAY_MISMATCH")
        replay=True
    return {
        "schema":"IRE_V5_P3_27_WINDOW_SOURCE_CUE_RECEIPT_V1",
        "original_srt_matched_in_prior_chat_host":True,
        "original_private_source_replayed_this_process":replay,
        "original_27_windows_checked":27,
        "original_cues_dispositioned":486,
        "source_anchored_candidates":claims,
        "claim_class_counts":dict(histogram),
        "official_scope_supported_source_statements":
            histogram["REGULATORY_SUPPORTED_SCOPED"],
        "regulatory_overgeneralizations_quarantined":
            histogram["REGULATORY_REJECTED_OVERGENERAL"],
        "asr_suspicions_await_audio":histogram["TRANSCRIPTION_AMBIGUOUS"],
        "full_atomic_recall_independently_proven":False,
        "formal_financial_fact_certifications":0,
        "new_formal_engine_window_receipts":0,
        "general_education_integration_candidate":True,
        "personal_investment_action_authorized":False,
        "five_video_formal_research_closure":False,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    args=p.parse_args()
    print(json.dumps(verify(args.root,source_zip=args.source_zip),
                     ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
