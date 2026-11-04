"""Fail-closed V5 audit of 44 previously unreviewed subtitle claims.

A verified SRT span hash establishes *text provenance*, not the correctness
of the claim, the existence of a legal exception, or suitability for advice.
This module never promotes claims into the approved knowledge ledger.

Usage:
  python -m ire.v5.review44_gate --root .
  python -m ire.v5.review44_gate --root . --private-zip /secure/201-300.zip

The optional private ZIP re-verifies all 44 complete original cue spans.
CI has no access to private copyrighted subtitles and does not claim it does.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

AUDIT="ire/v5/advisory_knowledge/review44_20261104/triage.json"
STUDY_FOLDER="ire/v5/studies"
STATUS={
    "EDUCATION_CANDIDATE",
    "CONDITIONAL_RULE_OPEN",
    "ACCOUNT_OR_PRODUCT_OPEN",
    "HISTORICAL_ONLY",
    "NUMERIC_OR_ASR_OPEN",
    "PERSONAL_SUITABILITY_OPEN",
    "UNSAFE_GENERALIZATION_BLOCKED",
    "OUT_OF_SCOPE",
}
SAFE_HOSTS={
    "www.law.go.kr","nts.go.kr","d.nts.go.kr",
    "www.moel.go.kr","m.krx.co.kr","www.krx.co.kr",
    "www.investor.gov",
}
FIXED_HAZARDS={
    "A237-08":"UNSAFE_GENERALIZATION_BLOCKED",
    "A237-09":"OUT_OF_SCOPE",
    "A237-10":"OUT_OF_SCOPE",
    "E229-06":"HISTORICAL_ONLY",
    "E229-08":"HISTORICAL_ONLY",
    "E229-09":"HISTORICAL_ONLY",
    "E229-10":"HISTORICAL_ONLY",
}
class Review44Error(ValueError):
    pass

def check(ok:bool, code:str)->None:
    if not ok: raise Review44Error(code)

def read(p:Path)->dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))

def normalized_cues(raw:bytes)->dict[int,dict]:
    txt=raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
    out={}
    for part in re.split(r"\n\s*\n",txt.strip()):
        lines=part.splitlines()
        check(len(lines)>=3 and lines[0].strip().isdigit(),"RAW_SRT_MALFORMED")
        index=int(lines[0].strip())
        check(index==len(out)+1 and " --> " in lines[1],"RAW_SRT_NONCONTIGUOUS")
        out[index]={"cue":index,"time":lines[1].strip(),
                    "text":" ".join(lines[2:])}
    return out

def verify(root:Path, review:dict|None=None,
           private_zip:Path|None=None)->dict:
    root=Path(root)
    review=review if review is not None else read(root/AUDIT)
    check(review.get("schema")=="IRE_V5_REMAINING_44_EVIDENCE_TRIAGE_V1"
          and review.get("as_of")=="2026-11-04"
          and review.get("record_count")==44,
          "REVIEW44_SCHEMA_OR_COUNT_BAD")
    check(review.get("human_blind_reference_labels_present") is False
          and review.get("official_full_text_snapshots_archived") is False
          and review.get("personalized_advisory_go") is False
          and review.get("independent_financial_fact_approvals")==0
          and review.get("reviewer")=="CHATGPT_CURRENT_CONVERSATION_NONBLIND",
          "REVIEW44_UNAUTHORIZED_BLIND_OR_ADVISORY_APPROVAL")
    check(review.get("archive_sha256")==
          "9ccd094766fc0b896d1b237edcf7ea4ef7b7622007262275f0d9e4c0518fee10",
          "REVIEW44_PRIVATE_ARCHIVE_HASH_CHANGED")
    sources=review.get("external_authorities")
    check(type(sources) is list and len(sources)>=8,
          "REVIEW44_EXTERNAL_REFERENCE_CATALOG_MISSING")
    authority={}
    for r in sources:
        sid=r.get("id")
        check(type(sid) is str and sid not in authority,
              "REVIEW44_DUPLICATED_AUTHORITY_ID")
        u=urlparse(str(r.get("url","")))
        check(u.scheme=="https" and u.hostname in SAFE_HOSTS,
              "REVIEW44_UNTRUSTED_REFERENCE_DOMAIN")
        effective=r.get("legal_effective_from")
        if effective is not None:
            check(date.fromisoformat(effective)<=date(2026,11,4),
                  "REVIEW44_FUTURE_LEGAL_EFFECTIVE_DATE")
        check(r.get("immutable_fulltext_snapshot") is False
              and r.get("external_human_verified") is False
              and r.get("checked_date")=="2026-11-04",
              "REVIEW44_FAKE_INDEPENDENT_REFERENCE_APPROVAL")
        authority[sid]=r
    catalog=read(root/"ire/v5/source_catalog/201-300.json")
    original={x["video_id"]:x for x in catalog["files"]}
    studies={}
    for path in sorted((root/STUDY_FOLDER).glob("*.json")):
        if path.name=="evidence_20261104.json":continue
        o=read(path)
        studies[o["video_id"]]=o
    old=read(root/"ire/v5/advisory_knowledge/verification_20261104/adjudications.json")
    assessed={x["source_study_claim_id"] for x in old["rows"]}
    prior={x["claim_id"] for line in
           (root/"data/claims.jsonl").read_text(encoding="utf-8").splitlines()
           if line.strip() for x in [json.loads(line)]}
    all_claims={c["claim_id"]:(v,c) for v in studies.values()
                for c in v["claims"]}
    remaining=set(all_claims)-assessed
    check(len(all_claims)==53 and len(assessed)==9 and len(remaining)==44,
          "REVIEW44_SOURCE_UNIVERSE_MISMATCH")
    rows=review.get("records")
    check(type(rows) is list and len(rows)==44,"REVIEW44_RECORD_COUNT_MISMATCH")
    encountered=set()
    votes=Counter()
    for r in rows:
        cid=r.get("claim_id")
        check(cid in remaining and cid not in encountered,
              "REVIEW44_DUPLICATE_OR_PREVIOUSLY_ASSESSED_CLAIM")
        encountered.add(cid)
        v,c=all_claims[cid]
        video=v["video_id"]
        check(r.get("video_id")==video
              and r.get("source_sha256")==v["source_sha256"]
              and original[video]["source_sha256"]==v["source_sha256"]
              and r.get("first_cue")==c["first_cue"]
              and r.get("last_cue")==c["last_cue"]
              and 1<=c["first_cue"]<=c["last_cue"]<=v["total_cues"]
              and re.fullmatch("[0-9a-f]{64}",str(r.get("original_cue_span_sha256",""))),
              "REVIEW44_SOURCE_PROVENANCE_CHANGED")
        check(r.get("source_paraphrase")==c["proposition"]
              and r.get("source_qualification")==c["scope_or_error"]
              and r.get("prior_claim_ids")==c["prior_claim_ids"]
              and set(r["prior_claim_ids"])<=prior
              and r.get("existing_provisional_relationship")==c["relationship"],
              "REVIEW44_LEGACY_CONTEXT_OR_MEANING_CHANGED")
        state=r.get("disposition")
        check(state in STATUS,"REVIEW44_DISPOSITION_INVALID")
        if cid in FIXED_HAZARDS:
            check(state==FIXED_HAZARDS[cid],
                  "REVIEW44_HAZARDOUS_CLAIM_UNSAFE_PROMOTION")
        evidence=r.get("official_reference_ids")
        check(type(evidence) is list and
              len(evidence)==len(set(evidence)) and set(evidence)<=set(authority),
              "REVIEW44_UNKNOWN_OR_DUPLICATED_AUTHORITY")
        if state=="EDUCATION_CANDIDATE":
            check(bool(evidence) and c["relationship"]!="UNRELATED",
                  "REVIEW44_UNSUPPORTED_EDUCATION_PROMOTION")
        if state=="OUT_OF_SCOPE":
            check(c["relationship"]=="UNRELATED",
                  "REVIEW44_NONINVESTMENT_SCOPE_HIDDEN")
        check(type(r.get("review_note")) is str and len(r["review_note"])>=25
              and type(r.get("source_paraphrase")) is str
              and len(r["source_paraphrase"])>=20,
              "REVIEW44_NO_INDIVIDUAL_EVIDENCE_ASSESSMENT")
        check(r.get("source_bytes_personally_rechecked_from_drive_zip") is True
              and r.get("authority_scope_is_limited") is True
              and r.get("external_blind_human_grade") is False
              and r.get("individual_investment_advice_approved") is False
              and r.get("formal_financial_fact_certified") is False,
              "REVIEW44_FABRICATED_APPROVAL_OR_PROVENANCE")
        votes[state]+=1
    check(encountered==remaining and
          review["summary"]==dict(votes) and
          sum(votes.values())==44,
          "REVIEW44_NOT_EXHAUSTIVE_OR_COUNTERS_WRONG")
    # Current GitHub is public: source ZIP is optional, never checked in.
    # This local branch provides byte-for-byte audit proof for every claim.
    reverified=0
    if private_zip is not None:
        data=Path(private_zip).read_bytes()
        check(hashlib.sha256(data).hexdigest()==review["archive_sha256"],
              "REVIEW44_PRIVATE_ZIP_HASH_MISMATCH")
        with zipfile.ZipFile(private_zip) as z:
            cue_lookup={}
            for vid in {x["video_id"] for x in rows}:
                matches=[name for name in z.namelist() if
                         name.endswith("youtube-transcript-"+vid+".srt")
                         and not name.startswith("__MACOSX/")
                         and "/._" not in name]
                check(len(matches)==1,"REVIEW44_PRIVATE_SRT_MISSING")
                raw=z.read(matches[0])
                check(hashlib.sha256(raw).hexdigest()==original[vid]["source_sha256"],
                      "REVIEW44_PRIVATE_SRT_HASH_CHANGED")
                cue_lookup[vid]=normalized_cues(raw)
            for row in rows:
                cues=cue_lookup[row["video_id"]]
                selected=[cues[i] for i in range(row["first_cue"],
                                                 row["last_cue"]+1)]
                content=json.dumps(selected,ensure_ascii=False,sort_keys=True,
                                   separators=(",",":")).encode("utf-8")
                check(hashlib.sha256(content).hexdigest()==
                      row["original_cue_span_sha256"],
                      "REVIEW44_ORIGINAL_CUE_TEXT_HASH_MISMATCH")
                reverified+=1
    return {
        "schema":"IRE_V5_REVIEW44_GATE_RESULT_V1",
        "original_source_claims_addressed":len(encountered),
        "education_candidates_nonblind":votes["EDUCATION_CANDIDATE"],
        "claims_requiring_further_context_or_evidence":
            votes["CONDITIONAL_RULE_OPEN"]+votes["ACCOUNT_OR_PRODUCT_OPEN"]+
            votes["NUMERIC_OR_ASR_OPEN"]+votes["PERSONAL_SUITABILITY_OPEN"],
        "historical_only":votes["HISTORICAL_ONLY"],
        "unsafe_generalizations_blocked":votes["UNSAFE_GENERALIZATION_BLOCKED"],
        "outside_investment_scope":votes["OUT_OF_SCOPE"],
        "original_claim_spans_byte_reverified_this_run":reverified,
        "external_blind_human_approval_count":0,
        "independent_financial_fact_approvals":0,
        "personalized_investment_advice_go":False,
        "release":"TRIAGED_WITH_SOURCE_INTEGRITY_NOT_FINANCIAL_ADVICE",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--private-zip",type=Path)
    args=p.parse_args()
    print(json.dumps(verify(args.root,private_zip=args.private_zip),
                     ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    main()
