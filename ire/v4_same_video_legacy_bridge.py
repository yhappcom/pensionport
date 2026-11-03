"""IRE V4: old video-001 claim crosswalk using original primary cue overlap.

No historical claims are silently accepted as current semantic truth or imported
into the new IRE knowledge ledger. No model API. All comparisons are candidates.
"""
from __future__ import annotations
import json
import re
from .source import require,sha256

SCHEMA="IRE_V4_P0_LEGACY_VIDEO001_CUE_CROSSWALK_BASELINE_V1"
VERDICTS={"QUALIFIED","HYPOTHETICAL","CONTRADICTED","PRIMARY_CONFIRMED"}

def _canon(obj):
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def same_video_cue_candidates(draft,baseline,expected_source_sha,expected_git_blobs):
    require(type(draft) is dict and
            draft.get("schema")=="IRE_V4_P0_ADAPTIVE_PROVISIONAL_V1" and
            type(baseline) is dict and baseline.get("schema")==SCHEMA,
            "V4_OLD_NEW_SOURCE_SCHEMA_INVALID")
    require(draft.get("original_sha256")==baseline.get("source_sha256")==
            expected_source_sha,"V4_SOURCE_OR_VIDEO_IDENTITY_DRIFT")
    require(type(expected_git_blobs) is dict and len(expected_git_blobs)>=2,
            "V4_LEGACY_BLOB_PIN_REQUIRED")
    observed={v["path"]:v["git_blob_sha"] for v in baseline["pinned_git_blobs"]}
    require(observed==expected_git_blobs,"V4_PRIOR_RESEARCH_BLOB_CHANGED")
    require(baseline.get("allow_auto_merge") is False and
            baseline.get("allow_auto_financial_approval") is False and
            baseline.get("prior_approval_is_not_new_model_semantic_proof") is True and
            baseline.get("legacy_claims_are_not_independent_gold") is True,
            "V4_PRIOR_STUDY_PROMOTION_DENIED")
    old=baseline.get("claims")
    require(type(old) is list and len(old)==baseline.get("legacy_claims_count"),
            "V4_LEGACY_CENSUS")
    seen=set()
    for row in old:
        cid=row.get("legacy_claim_id")
        rng=row.get("source_cue_range")
        require(type(cid) is str and cid not in seen and
                type(rng) is list and len(rng)==2 and
                all(type(n) is int for n in rng) and
                1<=rng[0]<=rng[1]<=baseline["original_cue_count"] and
                row.get("historical_verification") in VERDICTS and
                row.get("expected_personal_investment_approval") is False,
                "V4_LEGACY_CUE_OR_VERDICT_INVALID")
        seen.add(cid)
    pairs=[];unmapped=[];new=set()
    for window in draft.get("windows",[]):
        wid=window.get("window_id")
        require(type(wid) is str and re.fullmatch(r"W\d{5}",wid),
                "V4_WINDOW_ID_INVALID")
        for claim in window["claims"]:
            cid=claim.get("claim_id")
            require(type(cid) is str and cid not in new and
                    claim.get("annotation_status")=="UNREVIEWED" and
                    type(claim.get("source_refs")) is list and
                    bool(claim["source_refs"]),
                    "V4_NEW_CLAIM_UNVERIFIED_SOURCE_REQUIRED")
            new.add(cid)
            cue_ids={r["cue_index"] for r in claim["source_refs"]}
            require(all(type(n) is int and
                        1<=n<=baseline["original_cue_count"] for n in cue_ids),
                    "V4_NEW_CUE_OUT_OF_RANGE")
            found=False
            for historical in old:
                start,end=historical["source_cue_range"]
                shared=sorted(n for n in cue_ids if start<=n<=end)
                if not shared:continue
                found=True
                pairs.append({
                    "new_claim_id":cid,"window_id":wid,
                    "legacy_claim_id":historical["legacy_claim_id"],
                    "overlapping_primary_cue_ids":shared,
                    "legacy_historical_verdict":historical["historical_verification"],
                    "prior_numeric_contradiction":historical["historical_verification"]=="CONTRADICTED",
                    "relation":"CANDIDATE_ONLY_REQUIRES_SCOPE_TIME_MEANING_REVIEW",
                    "identical_semantics_proven":False,
                    "independently_verified":False,
                    "automatic_merge":False})
            if not found:unmapped.append({"new_claim_id":cid,"window_id":wid,
                                          "status":"NO_DIRECT_LEGACY_CUE_OVERLAP"})
    body={"schema":"IRE_V4_P0_VIDEO001_SOURCE_OVERLAP_CANDIDATES_V1",
          "source_sha256":expected_source_sha,
          "legacy_baseline_sha256":sha256(_canon(baseline)),
          "old_claims":len(old),"new_provisional_claims":len(new),
          "source_overlap_candidate_pairs":len(pairs),
          "new_claims_without_direct_prior_source_overlap":len(unmapped),
          "prior_contradicted_overlap_pairs":sum(x["prior_numeric_contradiction"] for x in pairs),
          "confirmed_relation_decisions":0,"automatic_knowledge_merges":0,
          "financial_truth_approvals":0,
          "pairs":pairs,"unmapped":unmapped}
    return {**body,"report_sha256":sha256(_canon(body))}
