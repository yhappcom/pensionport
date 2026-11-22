"""V245: lossless typed parent-to-child SOURCE-FIRST review input.

Keep original unapproved parent V6 atoms intact when their qualifiers, numeric
sources or exceptions occur in another child. No external-model API. Never
treat an inherited cue, a source hash, or a manual two-turn claim as E3 approval.
The returned object contains PRIVATE original quotes and MUST NOT be uploaded
to GitHub. Public evidence must contain only SHA-256 digests and counts.
"""
from __future__ import annotations

import json
from copy import deepcopy

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v244_e1_private_parent_child_source_graph import (
    audit_parent_child_lineage, source_child_plan,
)

SCHEMA="IRE_V245_E1_LOSSLESS_TYPED_PARENT_CHILD_REVIEW_INPUT_V1"
ROLES={
    "source_refs":"PRIMARY_SOURCE",
    "context_cue_indices":"CONTEXT",
    "condition_cue_indices":"CONDITION",
    "exception_cue_indices":"EXCEPTION",
    "numeric_references":"NUMERIC_SOURCE",
}


def _need(ok,code):
    if not ok:
        raise InvalidInput("V245_TYPED_OVERLAY_"+code)


def typed_parent_atom_review(atom,source,child_id):
    """Full original atom + source-verified typed references, NO atom projection."""
    owner=f"B{int(atom['owner_window_id'][1:]):04d}"
    _need(owner==child_id,"PARENT_PRIMARY_OWNER_DRIFT")
    roles={}
    for role in ("context_cue_indices","condition_cue_indices",
                 "exception_cue_indices"):
        for i in atom[role]:
            roles.setdefault(i,set()).add(ROLES[role])
    for nr in atom["numeric_references"]:
        roles.setdefault(nr["cue_index"],set()).add("NUMERIC_SOURCE")
    for ref in atom["source_refs"]:
        roles.setdefault(ref["cue_index"],set()).add("PRIMARY_SOURCE")
    rows=[]
    for i in sorted(roles):
        _need(type(i) is int and 1<=i<=len(source.cues),
              "REFERENCE_OUT_OF_PARENT_SOURCE")
        original=source.cues[i-1]
        target=source.owner(i)
        _need(target is not None,"REFERENCED_CUE_NOT_OWNED")
        target_child=f"B{int(target[1:]):04d}"
        excerpt=[ref["quote"] for ref in atom["source_refs"]
                 if ref["cue_index"]==i]
        _need(all(type(s) is str and s in original.text for s in excerpt),
              "PRIMARY_QUOTE_SOURCE_DRIFT")
        tokens=[nr["token"] for nr in atom["numeric_references"]
                if nr["cue_index"]==i]
        rows.append({
            "cue_index":i,"source_child_id":target_child,
            "external_to_owner_child":target_child!=child_id,
            "original_source_quote":original.text,
            "original_source_quote_sha256":sha256(original.text.encode("utf8")),
            "reference_roles":sorted(roles[i]),
            "source_excerpts_exact":excerpt,
            "numeric_tokens_exact":tokens,
        })
    _need(len(rows)==len(roles),"TYPED_REF_LOSS")
    return {
        "claim_id":atom["claim_id"],
        "owner_child_id":child_id,
        "full_original_parent_atom":deepcopy(atom),
        "full_original_parent_atom_sha256":json_digest(atom),
        "typed_source_references":rows,
        "external_source_reference_count":sum(
            x["external_to_owner_child"] for x in rows),
        "cross_child_condition_count":sum(
            x["external_to_owner_child"] and
            ("CONDITION" in x["reference_roles"] or
             "EXCEPTION" in x["reference_roles"])
            for x in rows),
        "cross_child_numeric_count":sum(
            x["external_to_owner_child"] and
            "NUMERIC_SOURCE" in x["reference_roles"] for x in rows),
        "semantic_review_status":"UNRESOLVED_SOURCE_FIRST_CHATGPT_REQUIRED",
        "e3_approved":False,"e4_approved":False,"e5_published":False,
    }


def _extract_foreign_edges(inputs):
    edges=[]
    for child in inputs:
        for atom in child["parent_atom_review_tasks"]:
            for ref in atom["typed_source_references"]:
                if not ref["external_to_owner_child"]:
                    continue
                translated={
                    "CONTEXT":"context_cue_indices",
                    "CONDITION":"condition_cue_indices",
                    "EXCEPTION":"exception_cue_indices",
                    "NUMERIC_SOURCE":"numeric_references",
                    "PRIMARY_SOURCE":"source_refs",
                }
                edges.append({
                    "claim_id":atom["claim_id"],
                    "owner_child_id":atom["owner_child_id"],
                    "referenced_child_id":ref["source_child_id"],
                    "referenced_cue_index":ref["cue_index"],
                    "foreign_reference_roles":sorted(
                        translated[k] for k in ref["reference_roles"]),
                    "original_cue_quote_sha256":
                        ref["original_source_quote_sha256"],
                })
    return edges


def build_typed_parent_review_overlay(source_raw,native_raw,cue_raw,
                                     e3_raw,pairs_raw,*,
                                     expected_source_sha256,
                                     expected_native_sha256,
                                     expected_graph_sha256,
                                     expected_cue_count=250,
                                     expected_child_count=13,
                                     expected_atom_count=68,
                                     expected_cross_atom_count=21,
                                     expected_cross_edge_count=49,
                                     window_size=20,
                                     required_cross_scope_claim=None):
    """Rebuild from externally pinned original bytes, not a child-local draft.

    Private response is source-first input, NOT a V123 case or a final verdict.
    """
    _need(type(expected_graph_sha256) is str and
          len(expected_graph_sha256)==64,"GRAPH_PIN_REQUIRED")
    graph=audit_parent_child_lineage(
        source_raw,native_raw,cue_raw,e3_raw,pairs_raw,
        expected_source_sha256=expected_source_sha256,
        expected_native_sha256=expected_native_sha256,
        expected_cue_count=expected_cue_count,
        expected_child_count=expected_child_count,
        window_size=window_size)
    _need(graph["source_graph_sha256"]==expected_graph_sha256,
          "PARENT_SOURCE_GRAPH_PIN_DRIFT")
    _need((graph["atomic_candidate_count"],
           graph["cross_child_parent_atom_count"],
           graph["cross_child_typed_source_edge_count"]) ==
          (expected_atom_count,expected_cross_atom_count,
           expected_cross_edge_count),"ATOM_OR_CROSS_EDGE_CENSUS_DRIFT")
    native=json.loads(native_raw)
    plan=source_child_plan(source_raw,native["video_id"],
                           expected_source_sha256=expected_source_sha256,
                           window_size=window_size)
    by_child={x["child_id"]:[] for x in plan["children"]}
    seen=set()
    for atom in native["atoms"]:
        child=f"B{int(atom['owner_window_id'][1:]):04d}"
        _need(child in by_child and atom["claim_id"] not in seen,
              "ATOM_CHILD_OWNER_DUPLICATE_OR_MISSING")
        seen.add(atom["claim_id"])
        by_child[child].append(typed_parent_atom_review(
            atom,plan["source"],child))
    _need(len(seen)==expected_atom_count,"ATOM_CENSUS_LOSS")
    if required_cross_scope_claim is not None:
        _need(type(required_cross_scope_claim) is dict and
              set(required_cross_scope_claim)=={
                  "claim_id","owner_child_id","primary_cue_index",
                  "inherited_condition_cue_indices"},
              "REQUIRED_CROSS_CLAIM_SCHEMA")
        hits=[x for group in by_child.values() for x in group
              if x["claim_id"]==required_cross_scope_claim["claim_id"]]
        _need(len(hits)==1 and
              hits[0]["owner_child_id"]==required_cross_scope_claim["owner_child_id"],
              "REQUIRED_CROSS_CLAIM_NOT_FOUND")
        actual=hits[0]
        indices={x["cue_index"] for x in
                 actual["full_original_parent_atom"]["source_refs"]}
        _need(required_cross_scope_claim["primary_cue_index"] in indices,
              "PRIMARY_CUE_DRIFT")
        for i in required_cross_scope_claim["inherited_condition_cue_indices"]:
            _need(any(x["cue_index"]==i and
                      x["external_to_owner_child"] and
                      "CONDITION" in x["reference_roles"]
                      for x in actual["typed_source_references"]),
                  "INHERITED_CONDITION_MISSING")
    child_inputs=[]
    for child in plan["children"]:
        begin,end=child["first_cue"],child["last_cue"]
        source_first=[{
            "cue_index":i,
            "quote":plan["source"].cues[i-1].text,
            "quote_sha256":sha256(plan["source"].cues[i-1].text.encode("utf8"))
        } for i in range(begin,end+1)]
        packet={
            "child_id":child["child_id"],
            "original_source_sha256":expected_source_sha256,
            "parent_source_graph_sha256":expected_graph_sha256,
            "child_plan_sha256":json_digest(child),
            "source_first_cues_exact":source_first,
            "parent_atom_review_tasks":by_child[child["child_id"]],
            "review_contract":"SOURCE_FIRST_THEN_COMPARE_ALL_PARENT_ATOMS",
            "all_cross_child_conditions_and_numeric_sources_visible":True,
            "e3_review_approved":False,
            "e4_authorized":False,"e5_published":False,
        }
        child_inputs.append({
            **packet,"review_input_sha256":json_digest(packet)
        })
    foreign=_extract_foreign_edges(child_inputs)
    _need(foreign==graph["cross_child_source_links"],
          "FOREIGN_SOURCE_EDGE_OR_ROLE_LOSS")
    _need(len(foreign)==expected_cross_edge_count,
          "CROSS_EDGE_LOSS")
    core={
        "schema":SCHEMA,
        "source_sha256":expected_source_sha256,
        "native_sha256":expected_native_sha256,
        "graph_sha256":expected_graph_sha256,
        "cue_count":expected_cue_count,
        "child_count":expected_child_count,
        "atom_count":expected_atom_count,
        "cross_atom_count":expected_cross_atom_count,
        "cross_typed_edge_count":expected_cross_edge_count,
        "child_review_inputs":child_inputs,
        "unapproved_source_first_only":True,
    }
    return {**core,"typed_overlay_sha256":json_digest(core),
            "e3_final_approved":False,"e4_authorized":False,
            "e5_published":False,"formal_financial_fact_approved":False}


def verify_typed_parent_review_overlay(overlay,*,expected_overlay_sha256,
                                       **source_params):
    """Require exact private text, parent atoms, roles and child task digest."""
    _need(type(overlay) is dict and type(expected_overlay_sha256) is str,
          "OWNER_TYPED_OVERLAY_PIN_REQUIRED")
    _need(overlay.get("typed_overlay_sha256")==expected_overlay_sha256,
          "OWNER_TYPED_OVERLAY_DIGEST_DRIFT")
    rebuilt=build_typed_parent_review_overlay(**source_params)
    _need(overlay==rebuilt,
          "PRIVATE_CUE_CONDITION_NUMERIC_OR_EXCEPTION_MUTATED")
    return {
        "status":"PARENT_TYPED_CHILD_INPUTS_SOURCE_VERIFIED_NOT_APPROVED",
        "source_sha256":rebuilt["source_sha256"],
        "graph_sha256":rebuilt["graph_sha256"],
        "typed_overlay_sha256":rebuilt["typed_overlay_sha256"],
        "child_count":rebuilt["child_count"],
        "atom_count":rebuilt["atom_count"],
        "cross_atom_count":rebuilt["cross_atom_count"],
        "cross_typed_edge_count":rebuilt["cross_typed_edge_count"],
        "e3_approved":False,"e4_authorized":False,"e5_published":False
    }
