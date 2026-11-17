"""V166 E4: original B0001 ALL EIGHT native V123 OPEN claims, one HOLD.

Existing V164 five speech-act reviews are NOT new research and MUST be reused,
not re-reviewed as if unexamined. E4's 3 later documentary receipts cover
ONLY 3 objective claim contexts. This reconciler validates both ledgers against
ONE original V6 source and V123 review with 8/8 cryptographic claim anchors.
It never upgrades OPEN, publishes V128 research, or calls investment advice.
"""
from __future__ import annotations

from collections import Counter

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import VerifiedSource
from v164_typed_v123 import B0001_EXPECTED,audit_typed_speech_row
from v166_e4_owner_open_partial_source import (
    OPEN_CLAIMS,audit_partial_open_video_census)

SCHEMA="IRE_V166_E4_B0001_ALL8_OPEN_V164_PLUS_E4_HOLD_V1"
TYPED_IDS=frozenset(B0001_EXPECTED)
DOCUMENT_IDS=frozenset(OPEN_CLAIMS)
EXPECTED_OPEN=TYPED_IDS|DOCUMENT_IDS
EXPECTED_NATIVE_COUNTS={
    "ACCEPT_FOR_RESEARCH":7,
    "OPEN":8,
    "EXCLUDE_FROM_RESEARCH":1,
}

def _need(condition,code):
    if not condition:
        raise InvalidInput("V166_E4_B0001_FULL_OPEN_"+code)


def audit_b0001_eight_open(source,exchange,original_v123_review,
                          v164_source_only_rows,e4_three_document_rows):
    """Check exact original 16-atom 120-cue source review; always HOLD.

    Source and V123 are already caller-attested. We recompute every
    source_ref and cue review hash here to eliminate cross-atom substitution.
    No inferred named-speaker/audio truth.
    """
    _need(isinstance(source,VerifiedSource)
          and type(exchange) is dict
          and type(original_v123_review) is dict
          and type(v164_source_only_rows) is list
          and type(e4_three_document_rows) is list,
          "NATIVE_INPUT_TYPES")
    _need(len(EXPECTED_OPEN)==8 and not TYPED_IDS&DOCUMENT_IDS,
          "FIXED_REVIEW_COVERAGE_OVERLAP")
    _need(source.scope_first_cue==1 and source.scope_last_cue==120,
          "EXPECTED_B0001_120_CUE_SCOPE")
    _need(exchange.get("source_sha256")==source.source_sha256 and
          exchange.get("manifest_sha256")==source.manifest_sha256 and
          original_v123_review.get("source_sha256")==source.source_sha256 and
          original_v123_review.get("manifest_sha256")==source.manifest_sha256,
          "VIDEO_OR_REVIEW_CUSTODY_MISMATCH")
    atoms=exchange.get("atoms")
    verdicts=original_v123_review.get("atom_verdicts")
    cue_rows=original_v123_review.get("source_cues")
    _need(type(atoms) is list and len(atoms)==16
          and type(verdicts) is list and len(verdicts)==16
          and type(cue_rows) is list and len(cue_rows)==120,
          "ORIGINAL_ATOM_AND_CUE_CENSUS")
    A={a["claim_id"]:a for a in atoms}
    V={v["claim_id"]:v for v in verdicts}
    _need(len(A)==16 and len(V)==16 and set(A)==set(V),
          "ORIGINAL_CLAIM_ID_CENSUS")
    counts=Counter(v["status"] for v in verdicts)
    _need(dict(counts)==EXPECTED_NATIVE_COUNTS,
          "FROZEN_V123_7_ACCEPT_8_OPEN_1_EXCLUDE_CHANGED")
    native_open={cid for cid,v in V.items() if v["status"]=="OPEN"}
    _need(native_open==EXPECTED_OPEN,
          "OPEN_IDENTITY_CHANGED_OR_A_NINTH_CLAIM_MISSING")
    review_cues={}
    for r in cue_rows:
        _need(type(r) is dict and type(r.get("cue_index")) is int
              and 1<=r["cue_index"]<=120
              and r.get("status")=="REVIEWED" and
              r.get("cue_text_sha256")==
                  sha256(source.cues[r["cue_index"]-1].text.encode("utf-8"))
              and r["cue_index"] not in review_cues,
              "REVIEWED_CUE_NOT_SOURCE_BYTE_PINNED")
        review_cues[r["cue_index"]]="REVIEWED"
    _need(len(review_cues)==120,"SOURCE_CUE_REVIEW_COMPLETENESS")
    total_refs=0
    for a in atoms:
        cid=a["claim_id"]
        _need(V[cid].get("atom_sha256")==json_digest(a),
              "ANY_ATOM_V123_DIGEST_MISMATCH")
        refs=a.get("source_refs")
        _need(type(refs) is list and len(refs)>0 and
              all(type(ref) is dict
                  and type(ref.get("cue_index")) is int
                  and 1<=ref["cue_index"]<=120
                  and type(ref.get("quote")) is str
                  and ref["quote"] in source.cues[ref["cue_index"]-1].text
                  and ref["cue_index"] in a["context_cue_indices"]
                  for ref in refs),
              "ANY_SOURCE_REF_NOT_DIRECT_OWNER_CUE")
        total_refs+=len(refs)
    typed_ids=[r.get("claim_id") for r in v164_source_only_rows
               if type(r) is dict]
    _need(len(v164_source_only_rows)==5
          and len(typed_ids)==5 and set(typed_ids)==TYPED_IDS,
          "V164_FIVE_SOURCE_ONLY_CENSUS")
    typed_checked=[]
    for r in v164_source_only_rows:
        cid=r["claim_id"]
        atom=A[cid]
        anchor=r["verbatim_anchor"]
        idx=r["verbatim_anchor_cue_index"]
        _need(any(ref["cue_index"]==idx and
                  anchor in ref["quote"] for ref in atom["source_refs"]),
              "SOURCE_ONLY_ANCHOR_BORROWED_FROM_NEIGHBOR_CUE")
        attested=audit_typed_speech_row(
            source,atom,V[cid],r,review_cues)
        _need(attested["research_knowledge_export_allowed"] is False and
              attested["investment_recommendation_approved"] is False and
              attested["financial_fact_verified"] is False,
              "V164_SOURCE_ONLY_CANNOT_BE_RELEASED")
        typed_checked.append(cid)
    partial=audit_partial_open_video_census(
        source,exchange,original_v123_review,e4_three_document_rows)
    _need(partial["n_open_unapproved"]==8 and
          set(partial["still_open_claim_ids"])==EXPECTED_OPEN and
          set(partial["other_native_open_claim_ids"])==TYPED_IDS and
          partial["n_targeted_partial_claims"]==3 and
          partial["n_other_native_open_claims"]==5 and
          partial["real_owner_parent_release_allowed"] is False,
          "PARTIAL_THREE_MISREPRESENTED_AS_FULL_EIGHT")
    return {
        "schema":SCHEMA,
        "source_sha256":source.source_sha256,
        "original_exchange_sha256":json_digest(exchange),
        "original_native_v123_review_sha256":json_digest(original_v123_review),
        "v164_five_source_speech_sha256":json_digest(v164_source_only_rows),
        "e4_three_partial_document_sha256":json_digest(e4_three_document_rows),
        "b0001_atom_census":16,
        "b0001_cues_reviewed":120,
        "all_direct_atom_source_refs_replayed":total_refs,
        "native_accepted_claims":7,
        "native_open_claims":8,
        "native_excluded_claims":1,
        "source_only_v164_previously_reviewed_claim_ids":sorted(typed_checked),
        "documentary_partial_e4_claim_ids":sorted(DOCUMENT_IDS),
        "all_open_claim_ids":sorted(EXPECTED_OPEN),
        "source_only_speech_not_financial_truth":True,
        "three_external_document_claims_partial_only":True,
        "speaker_original_audio_authenticated":False,
        "native_v123_verdict_changed":False,
        "approved_open_claims_newly_added":0,
        "full_v123_video_pass":False,
        "v128_real_owner_approved_knowledge_published":0,
        "e4_step_pass":False,
        "e4_status":"HOLD_ALL_EIGHT_NATIVE_OPEN_RECONCILED",
        "e5_authorized":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
