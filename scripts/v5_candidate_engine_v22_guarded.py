#!/usr/bin/env python3
"""Fail-closed V2.2 source-aware adapter for *future* unseen video evaluations.

Preserves and delegates to frozen V2.2 without adjusting its candidate signal.
Original claim provenance is mandatory. No claim of independent source truth
is inferred from V3's educational verdict, including PRIMARY_CONFIRMED.
"""
import re
from v5_candidate_engine_v22 import retrieve as frozen_v22_retrieve

VERDICTS=frozenset({
    "PRIMARY_CONFIRMED","QUALIFIED","HYPOTHETICAL","CONTRADICTED",
    "SPEAKER_OPINION",
})
CLAIMID=re.compile(r"^[A-Za-z0-9_-]{11}-\d{2,3}$")
VIDEOID=re.compile(r"^[A-Za-z0-9_-]{11}$")
REQUIRED=frozenset({"id","text","verdict","video_id","video_number"})

def _verify_claim(c):
    if not isinstance(c,dict) or not REQUIRED.issubset(c.keys()):
        raise ValueError("SOURCE_PROVENANCE_REQUIRED: missing original claim fields")
    if not isinstance(c["id"],str) or not CLAIMID.fullmatch(c["id"]):
        raise ValueError("INVALID_CLAIM_ID")
    if not isinstance(c["video_id"],str) or not VIDEOID.fullmatch(c["video_id"]) or not c["id"].startswith(c["video_id"]+"-"):
        raise ValueError("VIDEO_CLAIM_ID_MISMATCH")
    if not isinstance(c["video_number"],int) or isinstance(c["video_number"],bool) or c["video_number"]<1:
        raise ValueError("INVALID_VIDEO_ROSTER_NUMBER")
    if not isinstance(c["text"],str) or not c["text"].strip() or len(c["text"])>8192:
        raise ValueError("INVALID_OR_EMPTY_CLAIM_TEXT")
    if c["verdict"] not in VERDICTS:
        raise ValueError("MISSING_OR_UNKNOWN_VERIFICATION_STATUS")
    # The dictionary is not accepted as authoritative merely because its
    # structure validates. Callers must load it from checked Git provenance.
    return c

def retrieve_claims(left,right,legacy_signals=None):
    """Return retrieval candidate + strictly source-scoped human review record.

    Consumers must FIRST load claims from the immutable source-contract loader,
    never from caller-supplied arbitrary strings. No semantic fact approval.
    """
    a=_verify_claim(left);b=_verify_claim(right)
    if a["id"]==b["id"]:
        raise ValueError("SELF_PAIR_IS_NOT_CROSS_CLAIM_RETRIEVAL")
    hit,why=frozen_v22_retrieve(
        a["text"],b["text"],legacy_signals,
        left_verdict=a["verdict"],right_verdict=b["verdict"])
    is_refuted=(a["verdict"]=="CONTRADICTED" or b["verdict"]=="CONTRADICTED")
    unreplicated=(a["verdict"]=="HYPOTHETICAL" or b["verdict"]=="HYPOTHETICAL")
    if why["correction_only"]!=is_refuted or why["review_only"] is not True or why["automatic_knowledge_approval"] is not False or why["semantic_relation_prediction"] is not None:
        raise ValueError("FROZEN_ENGINE_SAFETY_CONTRACT_FAILED")
    why=dict(why)
    why.update({
        "source_provenance_required":True,
        "source_claim_ids":[a["id"],b["id"]],
        "source_verdicts":[a["verdict"],b["verdict"]],
        "source_risk":"CORRECTION_ONLY" if is_refuted
             else "UNREPLICATED_HYPOTHETICAL_SOURCE" if unreplicated
             else "HUMAN_REVIEW_ONLY",
        "independent_primary_or_numeric_verification_reperformed":False,
        "correction_only":is_refuted,
        "automatic_knowledge_approval":False,
        "semantic_relation_prediction":None,
        "automatic_merge_permitted":False,
        "investment_trade_instruction_permitted":False,
        "research_completion_certificate_permitted":False,
    })
    return hit,why
