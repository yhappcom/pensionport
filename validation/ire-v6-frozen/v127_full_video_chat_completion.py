"""V127 complete-parent preflight over bounded, independently pinned child scopes.

Additive pre-publication barrier. The ChatGPT host must actually perform every
child's semantic work; this code does not invoke a model or certify recall.
No accumulation happens here. A subsequent *atomic* parent knowledge commit is
needed for full-video release. Owner identity is NOT proven by a SHA digest.
"""
from __future__ import annotations

import re

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.full_video_segments import propose_full_video_segments
from ire.v6.trust import verify_owner_inventory
from ire.v6.prior_knowledge import audit_prior_candidates
from v123_chat_final_gate import assess_chat_final_gate

HASH = re.compile(r"[a-f0-9]{64}\Z")


def _stop(code):
    raise QualityNotProven("V127_" + code)


def assess_full_video_chat_assembly(raw, parent_manifest, parent_inventory, *,
                                    expected_parent_inventory_sha256, max_cues,
                                    child_runs, seam_reviews):
    """Audit every child of a *single original video* and all cross-child seams.

    child_runs are already-created V6 host+ChatGPT records in proposed order.
    Missing children yield HOLD (with zero export), never partial publication.
    For a video within the limit, the one child must exactly equal the parent.
    """
    plan = propose_full_video_segments(
        raw, parent_manifest, parent_inventory,
        expected_inventory_sha256=expected_parent_inventory_sha256,
        max_cues=max_cues)
    parent = verify_owner_inventory(
        raw,parent_manifest,parent_inventory,
        expected_inventory_sha256=expected_parent_inventory_sha256).source
    if type(child_runs) is not list or len(child_runs) > 512:
        raise InvalidInput("V127_CHILD_RUNS_INVALID")
    if type(seam_reviews) is not list:
        raise InvalidInput("V127_SEAM_REVIEWS_INVALID")
    expected = ([x["child_manifest"] for x in plan["segments"]]
                if plan["segmentation_needed"] else [parent_manifest])
    expected_spans = [(x["scope"]["first_cue"],x["scope"]["last_cue"])
                      for x in expected]
    if len(child_runs) != len(expected):
        return {"schema":"IRE_V127_FULL_VIDEO_CHAT_ASSEMBLY_V1",
                "status":"HOLD_INCOMPLETE_CHILD_SCOPES", "expected_child_scopes":len(expected),
                "supplied_child_scopes":len(child_runs),"reviewed_cues":0,
                "research_candidates_export_allowed":False,
                "whole_video_research_complete":False,"p0_go":False}
    expected_seams = []
    for left,right in zip(expected_spans,expected_spans[1:]):
        if left[1]+1 != right[0]:
            _stop("GAP_OR_OVERLAP_IN_PARENT_PLAN")
        expected_seams.append((left[1],right[0]))
    if len(seam_reviews) != len(expected_seams):
        _stop("MISSING_CROSS_SEGMENT_SEMANTIC_SEAM_REVIEW")
    for review,(left,right) in zip(seam_reviews,expected_seams):
        if (type(review) is not dict or set(review) != {
            "left_last_cue","right_first_cue","left_text_sha256",
            "right_text_sha256","chat_executor","condition_exception_and_rebuttal_checked",
            "cross_segment_atomic_join_resolved","unresolved_semantic_cases",
            "private_review_note_sha256"
        } or review["left_last_cue"] != left or review["right_first_cue"] != right or
            review["left_text_sha256"] != sha256(parent.cues[left-1].text.encode("utf-8")) or
            review["right_text_sha256"] != sha256(parent.cues[right-1].text.encode("utf-8")) or
            review["chat_executor"] != "CHATGPT_IN_CHAT" or
            review["condition_exception_and_rebuttal_checked"] is not True or
            review["cross_segment_atomic_join_resolved"] is not True or
            type(review["unresolved_semantic_cases"]) is not int or
            review["unresolved_semantic_cases"] != 0 or
            type(review["private_review_note_sha256"]) is not str or
            not HASH.fullmatch(review["private_review_note_sha256"])):
            _stop("CROSS_SEGMENT_SEMANTIC_SEAM_OPEN")
    seen_cues = set()
    seen_claim_ids = set()
    gated = []
    total_atoms = 0
    for i,(case,plan_manifest) in enumerate(zip(child_runs,expected),1):
        if type(case) is not dict or set(case) != {
            "manifest","inventory_bytes","expected_inventory_sha256",
            "source","exchange","prior_knowledge","source_store",
            "host_receipt","chat_review","official_evidence_bodies"
        }:
            _stop("CHILD_RUN_SCHEMA_MISMATCH")
        if case["manifest"] != plan_manifest:
            _stop("CHILD_MANIFEST_NOT_PARENT_APPROVED_PLAN")
        child = verify_owner_inventory(
            raw,case["manifest"],case["inventory_bytes"],
            expected_inventory_sha256=case["expected_inventory_sha256"]).source
        supplied = case["source"]
        if (child.attestation() != supplied.attestation() or
                child.source_sha256 != parent.source_sha256 or
                child.video_id != parent.video_id or
                child.cue_census_sha256 != parent.cue_census_sha256):
            _stop("CHILD_SOURCE_PARENT_DRIFT")
        portion = set(range(child.scope_first_cue,child.scope_last_cue+1))
        if seen_cues.intersection(portion):
            _stop("DUPLICATE_PARENT_CUE_OWNERSHIP")
        seen_cues.update(portion)
        atom_ids = {a["claim_id"] for a in case["exchange"]["atoms"]}
        if len(atom_ids)!=len(case["exchange"]["atoms"]) or seen_claim_ids.intersection(atom_ids):
            _stop("CROSS_SCOPE_DUPLICATE_ATOM_ID")
        seen_claim_ids.update(atom_ids)
        verdict = assess_chat_final_gate(
            child,case["exchange"],host_receipt=case["host_receipt"],
            chat_review=case["chat_review"],store=case["source_store"],
            official_evidence_bodies=case["official_evidence_bodies"])
        prior = audit_prior_candidates(child,case["exchange"],case["prior_knowledge"])
        if prior["host_candidate_atoms_accounted_for"] != len(atom_ids):
            _stop("PRIOR_KNOWLEDGE_CENSUS_DRIFT")
        gated.append(verdict)
        total_atoms += len(atom_ids)
    if seen_cues != set(range(1,len(parent.cues)+1)):
        _stop("PARENT_CUE_CENSUS_NOT_COMPLETE")
    result = {"schema":"IRE_V127_FULL_VIDEO_CHAT_ASSEMBLY_V1",
              "video_id":parent.video_id,"parent_source_sha256":parent.source_sha256,
              "parent_manifest_sha256":parent.manifest_sha256,
              "parent_inventory_sha256":expected_parent_inventory_sha256,
              "parent_cue_census_sha256":parent.cue_census_sha256,
              "total_parent_cues":len(parent.cues),
              "reviewed_cues":sum(x["cues_reviewed"] for x in gated),
              "child_scopes":len(gated),"cross_scope_seams_reviewed":len(expected_seams),
              "atomic_candidates":total_atoms,
              "child_statuses":[x["status"] for x in gated],
              "child_gate_receipts_sha256":json_digest(gated),
              "unresolved_chat_claims":sum(x["atoms_open"] for x in gated),
              "independent_semantic_recall_certified":False,
              "owner_identity_independently_verified":False,
              "whole_video_research_complete":False,
              "new_knowledge_published":False,
              "research_candidates_export_allowed":False,
              "p0_go":False}
    if any(x["status"] != "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY" for x in gated):
        result["status"]="HOLD_CHILD_CHAT_FINAL_NOT_ALL_PASSED"
    else:
        result["status"]="ALL_CHILD_CHATS_REVIEWED_STAGING_NOT_PUBLISHED"
    return result