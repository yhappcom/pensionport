"""V238: build V6 PARTIAL child proposals without cross-scope semantic data loss.

The V6 partial-scope grammar refuses out-of-range refs.  For source-native
structural validation, stage only complete local-only atoms; keep *every*
cross-scope atom with exact source in independently verified V237 review
packets.  OPEN atoms are never silently split, rewritten or approved.  A
child draft is not a child host receipt and its derived inventory is not an
independent owner attestation.
"""
from __future__ import annotations

from copy import deepcopy

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from v237_e1_parent_child_review_contract import verify_child_review_tasks

SCHEMA = "IRE_V238_E1_PARTIAL_SCOPE_NATIVE_LOCAL_ONLY_DRAFT_V1"


def _need(ok, code):
    if not ok:
        raise InvalidInput("V238_E1_"+code)


def build_partial_native_drafts(*, origin: dict, checkpoint,
                                review_tasks: dict,
                                externally_pinned_review_tasks_sha256: str,
                                **source_args):
    audit=verify_child_review_tasks(review_tasks=review_tasks,
        externally_pinned_review_tasks_sha256=
            externally_pinned_review_tasks_sha256,origin=origin,
        checkpoint=checkpoint,**source_args)
    parent=origin["exchange"]
    by_cue={row["cue_index"]:row for row in parent["cue_dispositions"]}
    by_id={atom["claim_id"]:atom for atom in parent["atoms"]}
    seen=set(); local_all=set(); cross_all=set(); outputs=[]
    for task,child_id,manifest in zip(review_tasks["child_tasks"],
                                       checkpoint.child_ids,checkpoint.child_manifests):
        _need(task["segment_id"]==child_id and
              task["manifest_sha256"]==json_digest(manifest),
              "CHILD_ID_OR_PLAN_DRIFT")
        first,last=manifest["scope"]["first_cue"],manifest["scope"]["last_cue"]
        source=verify_source(origin["source_raw"],manifest,
            expected_source_sha256=origin["source_sha256"],
            expected_manifest_sha256=json_digest(manifest))
        local_ids=set();cross_ids=set()
        for atom in task["atom_review_tasks"]:
            cid=atom["claim_id"]
            _need(cid in by_id and cid not in seen and
                  atom["parent_atom_sha256"]==json_digest(by_id[cid]),
                  "CHILD_ATOM_OWNERSHIP_OR_SHA")
            seen.add(cid)
            if atom["requires_cross_child_semantic_review"]:
                cross_ids.add(cid)
            else:
                local_ids.add(cid)
        atoms=deepcopy([a for a in parent["atoms"] if a["claim_id"] in local_ids])
        _need(len(atoms)==len(local_ids),"LOCAL_ATOM_CENSUS")
        crows=[]
        newly_open=[]
        for i in range(first,last+1):
            row=deepcopy(by_cue[i])
            local_referenced=sorted(cid for cid in local_ids if any(
                r["cue_index"]==i for r in by_id[cid]["source_refs"]))
            original_refs=row["claim_ids"]
            if local_referenced:
                _need(row["disposition"]=="CANDIDATES" and
                      set(local_referenced).issubset(set(original_refs)),
                      "PARENT_CUE_CLAIM_RELATION_DRIFT")
                row["claim_ids"]=local_referenced
            elif row["disposition"]=="CANDIDATES":
                _need(all(cid in cross_ids for cid in original_refs),
                      "CUE_DROPPED_UNOWNED_CANDIDATE")
                row["disposition"]="UNRESOLVED"
                row["claim_ids"]=[]
                row["note"]="외부 구간 문맥 필요: 원본 부모 검토 업무에서 미승인 유지"
                newly_open.append(i)
            crows.append(row)
        scoped={"schema":parent["schema"],"video_id":parent["video_id"],
                "source_sha256":parent["source_sha256"],
                "manifest_sha256":json_digest(manifest),
                "cue_dispositions":crows,"atoms":atoms}
        checked=audit_host_atomic_exchange(source,scoped)
        _need(checked["proposed_atomic_claims"]==len(local_ids),
              "CHILD_V6_AUDIT_CLAIM_LOSS")
        outputs.append({"segment_id":child_id,"first_cue":first,"last_cue":last,
            "source_sha256":source.source_sha256,
            "child_manifest_sha256":source.manifest_sha256,
            "source_cue_census_sha256":source.cue_census_sha256,
            "native_draft_exchange":scoped,
            "native_draft_exchange_sha256":json_digest(scoped),
            "local_complete_atom_ids":sorted(local_ids),
            "cross_atom_ids_kept_in_parent_sidecar":sorted(cross_ids),
            "cross_atom_source_review_sha256":json_digest(task),
            "original_parent_cue_became_unresolved":newly_open,
            "native_child_draft_audit":checked,
            "independent_child_inventory_verified":False,
            "real_child_v6_host_committed":False,
            "formal_child_chat_review_completed":False,
            "e4_authorized":False})
        local_all|=local_ids;cross_all|=cross_ids
    _need(seen==set(by_id),"PARENT_ATOM_LOSS")
    _need(not(local_all&cross_all) and
          len(local_all)+len(cross_all)==len(seen) and
          len(cross_all)==audit["cross_segment_atom_count"],
          "CROSS_SEGMENT_ATOM_ESCROW_LOSS")
    _need(len(outputs)==audit["child_count"],"CHILD_CENSUS")
    return {"schema":SCHEMA,"status":"ALL_PARTIAL_DRAFTS_AUDITED_NEEDS_REAL_CHILD_OWNER_PINS_AND_CHAT",
        "parent_source_sha256":origin["source_sha256"],
        "parent_exchange_sha256":origin["native_exchange_digest"],
        "parent_plan_sha256":checkpoint.plan_pin,
        "review_tasks_sha256":externally_pinned_review_tasks_sha256,
        "child_count":len(outputs),"local_complete_parent_atom_count":len(local_all),
        "cross_parent_atom_count":len(cross_all),
        "cross_external_cue_edges_preserved_in_review_tasks":audit["external_cue_reference_edges"],
        "child_drafts":outputs,
        "actual_child_host_receipts":0,"child_formal_e3_approved":0,
        "e4_authorized":False,"e5_published":0}


def verify_partial_native_drafts(*, draft: dict,
                                 externally_pinned_draft_sha256: str,
                                 **source_args):
    _need(type(draft) is dict and json_digest(draft)==externally_pinned_draft_sha256,
          "CHILD_DRAFT_PIN_MISMATCH")
    expected=build_partial_native_drafts(**source_args)
    _need(draft==expected,"CHILD_DRAFT_SOURCE_OR_QUARANTINE_MUTATED")
    return {"status":"ALL_CHILD_NATIVE_DRAFTS_REPLAYED_NO_APPROVAL",
        "child_count":expected["child_count"],
        "locally_complete_atoms":expected["local_complete_parent_atom_count"],
        "cross_atoms_waiting_for_semantics":expected["cross_parent_atom_count"],
        "real_child_host_receipts":0,"e5_published":0}