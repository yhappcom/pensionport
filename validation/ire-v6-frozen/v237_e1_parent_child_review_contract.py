"""V237: lossless source-native full-video -> child ChatGPT review task contract.

This is a verifiable **review input**, never a V6 child host event, a V123
verdict, E4 authorization, independent gold or an identity assertion.  Every
parent atom is assigned once; cross-child source roles remain intact.
"""
from __future__ import annotations

from typing import Any

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v234_e1_cross_child_context_custody import verify_escrow_bytes, _child_map

SCHEMA = "IRE_V237_E1_PARENT_TO_CHILD_SOURCE_BOUND_REVIEW_TASKS_V1"


def _need(condition: Any, reason: str):
    if not condition:
        raise InvalidInput("V237_E1_" + reason)


def build_child_review_tasks(*, origin: dict, checkpoint, cross_context_escrow: dict,
                             externally_pinned_escrow_sha256: str,
                             externally_pinned_parent_plan_sha256: str,
                             externally_pinned_checkpoint_head_sha256: str,
                             externally_pinned_source_sha256: str,
                             externally_pinned_exchange_digest: str) -> dict:
    """No ref truncation. Review task creation must work with open cross links."""
    context_audit = verify_escrow_bytes(
        origin=origin,checkpoint=checkpoint,escrow=cross_context_escrow,
        externally_pinned_escrow_sha256=externally_pinned_escrow_sha256,
        externally_pinned_parent_plan_sha256=externally_pinned_parent_plan_sha256,
        externally_pinned_checkpoint_head_sha256=externally_pinned_checkpoint_head_sha256,
        externally_pinned_source_sha256=externally_pinned_source_sha256,
        externally_pinned_exchange_digest=externally_pinned_exchange_digest)
    source = origin["source"]
    exchange = origin["exchange"]
    child_of = _child_map(checkpoint)
    atom_lookup = {a["claim_id"]:a for a in exchange["atoms"]}
    _need(len(atom_lookup) == origin["unapproved_atoms"], "ATOM_IDS_NOT_UNIQUE")
    cross_ids = {x["claim_id"] for x in cross_context_escrow["cross_segment_atom_rows"]}
    _need(len(cross_ids) == context_audit["cross_segment_atom_count"], "ESCROW_ATOM_IDS_DUPLICATE")
    tasks = []
    assigned = set()
    seen_cues = set()
    external_edges = 0
    external_qualifier_claims = set()
    external_numeric_claims = set()
    for child_id, manifest in zip(checkpoint.child_ids,checkpoint.child_manifests):
        first,last = manifest["scope"]["first_cue"],manifest["scope"]["last_cue"]
        child_cues = []
        for i in range(first,last+1):
            _need(i not in seen_cues, "SOURCE_CUE_DUPLICATE")
            seen_cues.add(i)
            c = source.cues[i-1]
            child_cues.append({"cue_index":i,"quote":c.text,
                               "quote_sha256":sha256(c.text.encode("utf-8"))})
        child_atoms = []
        for atom in exchange["atoms"]:
            cid = atom["claim_id"]
            if child_of[atom["source_refs"][0]["cue_index"]] != child_id:
                continue
            _need(cid not in assigned, "ATOM_MULTI_CHILD_OWNER")
            assigned.add(cid)
            src = {ref["cue_index"] for ref in atom["source_refs"]}
            ctx = set(atom["context_cue_indices"])
            cond = set(atom["condition_cue_indices"])
            exc = set(atom["exception_cue_indices"])
            nums = atom["numeric_references"]
            nidx = {n["cue_index"] for n in nums}
            referenced = sorted(src | ctx | cond | exc | nidx)
            references=[]
            ex_qual,ex_num=False,False
            for idx in referenced:
                c=source.cues[idx-1]
                outside=child_of[idx]!=child_id
                roles=(["PRIMARY_SOURCE"] if idx in src else [])
                roles+=(["CONTEXT"] if idx in ctx else [])
                roles+=(["CONDITION"] if idx in cond else [])
                roles+=(["EXCEPTION"] if idx in exc else [])
                roles+=(["NUMERIC_SOURCE"] if idx in nidx else [])
                if outside:
                    external_edges+=1
                    ex_qual |= idx in cond or idx in exc
                    ex_num |= idx in nidx
                references.append({"cue_index":idx,"source_child_id":child_of[idx],
                    "external_to_owner_child":outside,"quote":c.text,
                    "quote_sha256":sha256(c.text.encode("utf-8")),"roles":roles,
                    "source_quote_spans":[r["quote"] for r in atom["source_refs"] if r["cue_index"]==idx],
                    "numeric_tokens":[n["token"] for n in nums if n["cue_index"]==idx]})
            has_external=any(r["external_to_owner_child"] for r in references)
            _need(has_external == (cid in cross_ids), "CROSS_ATOM_OWNERSHIP_CONFLICT")
            if ex_qual:external_qualifier_claims.add(cid)
            if ex_num:external_numeric_claims.add(cid)
            child_atoms.append({"claim_id":cid,"parent_atom_sha256":json_digest(atom),
                "parent_proposition":atom["proposition"],"speaker_provisional":atom["speaker"],
                "stance_provisional":atom["stance"],"parent_atom":atom,
                "requires_cross_child_semantic_review":has_external,
                "source_context_references":references,
                "formal_v123_verdict":None,"e4_authorized":False,
                "independent_gold_verified":False})
        tasks.append({"segment_id":child_id,"manifest_sha256":json_digest(manifest),
            "source_sha256":source.source_sha256,"scope":{"first_cue":first,"last_cue":last},
            "source_cues":child_cues,"atom_review_tasks":child_atoms,
            "child_semantic_review_state":"PENDING_DISTINCT_CHATGPT_REVIEW",
            "child_v6_host_event_sha256":None,"child_v123_approved":False})
    _need(seen_cues==set(range(1,len(source.cues)+1)),"SOURCE_CUE_GAP")
    _need(assigned==set(atom_lookup),"ATOM_CENSUS_INCOMPLETE")
    _need(external_edges==context_audit["external_cue_reference_edges"],
          "CROSS_SOURCE_EDGE_LOSS")
    _need(len(external_qualifier_claims)==context_audit["cross_segment_qualifier_atom_count"],
          "EXTERNAL_CONDITION_OR_EXCEPTION_LOSS")
    _need(len(external_numeric_claims)==context_audit["cross_segment_numeric_atom_count"],
          "EXTERNAL_NUMERIC_CONTEXT_LOSS")
    _need(len(tasks)==len(checkpoint.child_ids),"CHILD_CENSUS_LOSS")
    return {"schema":SCHEMA,"status":"ALL_CHILD_REVIEW_TASKS_CREATED_UNAPPROVED",
        "source_sha256":source.source_sha256,"parent_plan_sha256":checkpoint.plan_pin,
        "parent_exchange_digest":externally_pinned_exchange_digest,
        "parent_context_escrow_sha256":externally_pinned_escrow_sha256,
        "checkpoint_head_sha256":externally_pinned_checkpoint_head_sha256,
        "source_cue_count":len(seen_cues),"parent_atom_count":len(assigned),
        "child_count":len(tasks),"cross_segment_atom_count":len(cross_ids),
        "cross_segment_qualifier_atom_count":len(external_qualifier_claims),
        "cross_segment_numeric_atom_count":len(external_numeric_claims),
        "external_cue_reference_edges":external_edges,"child_tasks":tasks,
        "manual_2turn_ref_is_host_cryptographic_proof":False,
        "e3_formal_child_approvals":0,"e4_authorized":False,"e5_published":0}


def verify_child_review_tasks(*, review_tasks: dict, externally_pinned_review_tasks_sha256: str,
                              **source_args) -> dict:
    _need(type(review_tasks) is dict and json_digest(review_tasks)==externally_pinned_review_tasks_sha256,
          "REVIEW_TASKS_DIGEST_MISMATCH")
    expected=build_child_review_tasks(**source_args)
    _need(review_tasks==expected,"REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION")
    return {"status":"CHILD_TASKS_EXACT_SOURCE_VERIFIED_NO_APPROVAL",
            "child_count":expected["child_count"],
            "parent_atom_count":expected["parent_atom_count"],
            "cross_segment_atom_count":expected["cross_segment_atom_count"],
            "external_cue_reference_edges":expected["external_cue_reference_edges"],
            "e3_approved":False,"e4_authorized":False,"e5_published":0}