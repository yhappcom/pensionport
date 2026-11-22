"""V244 P0-1-02: source-byte-anchored parent → 13 child cue/atom lineage.

This is an E1 ORIGINAL-SOURCE STRUCTURE AUDIT only. It neither copies owner
SRT to GitHub nor approves a single E2 semantic verdict, E3/E4 fact or E5
publication. Synthetic tests cover failures; live owner/private ZIP must be
replayed independently with externally pinned SHA before release.
"""
from __future__ import annotations
import json
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from v228_v193_actual_two_turn_runtime_gate import audit_study, digest

SCHEMA="IRE_V244_E1_PRIVATE_ORIGINAL_PARENT_CHILD_SOURCE_GRAPH_V1"


def _need(ok,code):
    if not ok:
        raise InvalidInput("V244_SOURCE_GRAPH_"+code)


def source_child_plan(raw:bytes,video_id:str,*,expected_source_sha256:str,
                      window_size:int=20)->dict:
    """Canonical original bytes → every cue assigned to one child once."""
    _need(type(raw) is bytes and type(expected_source_sha256) is str,
          "SOURCE_BYTES_AND_EXTERNAL_PIN_REQUIRED")
    source,manifest=make_original_plan(
        raw,video_id,expected_source_sha256=expected_source_sha256,
        window_size=window_size)
    children=[];cue_rows=[]
    for n,(wid,start,stop) in enumerate(source.primary_windows,1):
        cid=f"B{n:04d}"
        rows=[]
        for i in range(start,stop+1):
            cue=source.cues[i-1]
            _need(cue.index==i and source.owner(i)==wid, "CUE_OWNER_OR_INDEX")
            row={"cue_index":i,"child_id":cid,"owner_window_id":wid,
                 "start_ms":cue.start_ms,"end_ms":cue.end_ms,
                 "source_quote_sha256":sha256(cue.text.encode("utf-8"))}
            rows.append(row)
            cue_rows.append(row)
        children.append({
            "child_id":cid,"owner_window_id":wid,"first_cue":start,
            "last_cue":stop,"cue_count":len(rows),
            "original_window_text_sha256":manifest["windows"][n-1]["text_sha256"],
            "cue_byte_lineage_sha256":json_digest(rows)
        })
    _need([r["cue_index"] for r in cue_rows]==list(range(1,len(source.cues)+1)),
          "CUE_GAP_DUPLICATE_OR_REORDER")
    _need(len(children)==(len(source.cues)+window_size-1)//window_size,
          "CHILD_PLAN_INCOMPLETE")
    return {"source":source,"manifest":manifest,"children":children,
            "cue_rows":cue_rows}


def foreign_context_links(source,atoms:list[dict])->list[dict]:
    """Full-parent foreign cue refs, never strip a child-external condition."""
    links=[]
    roles=("context_cue_indices","condition_cue_indices",
           "exception_cue_indices")
    for atom in atoms:
        owner=atom["owner_window_id"]
        _need(owner in {w[0] for w in source.primary_windows},
              "CLAIM_OWNER_NOT_IN_SOURCE_PLAN")
        cid=atom["claim_id"]
        # For one cross-window cue, retain all roles in one typed edge.
        foreign={}
        for role in roles:
            for i in atom[role]:
                target=source.owner(i)
                _need(target is not None,"CROSS_CONTEXT_SOURCE_OUTSIDE_PARENT")
                if target!=owner:
                    foreign.setdefault(i,set()).add(role)
        for nr in atom["numeric_references"]:
            i=nr["cue_index"]
            target=source.owner(i)
            _need(target is not None,"CROSS_NUMERIC_SOURCE_OUTSIDE_PARENT")
            if target!=owner:
                foreign.setdefault(i,set()).add("numeric_references")
        for sr in atom["source_refs"]:
            i=sr["cue_index"]
            target=source.owner(i)
            _need(target is not None,"CROSS_PRIMARY_SOURCE_OUTSIDE_PARENT")
            if target!=owner:
                foreign.setdefault(i,set()).add("source_refs")
        for i in sorted(foreign):
            target=source.owner(i)
            links.append({"claim_id":cid,"owner_child_id":f"B{int(owner[1:]):04d}",
                          "referenced_child_id":f"B{int(target[1:]):04d}",
                          "referenced_cue_index":i,
                          "foreign_reference_roles":sorted(foreign[i]),
                          "original_cue_quote_sha256":
                             sha256(source.cues[i-1].text.encode("utf-8"))})
    return links


def audit_parent_child_lineage(source_raw:bytes,native_raw:bytes,
                               cue_raw:bytes,e3_raw:bytes,pairs_raw:bytes,*,
                               expected_source_sha256:str,
                               expected_native_sha256:str,
                               expected_cue_count:int,
                               expected_child_count:int,
                               window_size:int=20)->dict:
    """Full frozen V228 audit followed by original cue/claim child lineage.

    Every source quote and V6 atom is audited with the original V228 code.
    Parent-to-child edges and escaped cross-window conditions are represented
    as SHA-only records. No child-local rewrite of source claims is authorized.
    """
    _need(type(expected_cue_count) is int and expected_cue_count>0 and
          type(expected_child_count) is int and expected_child_count>0,
          "EXPECTED_CENSUS_REQUIRED")
    _need(digest(source_raw)==expected_source_sha256 and
          digest(native_raw)==expected_native_sha256,
          "OWNER_SOURCE_OR_NATIVE_PIN_DRIFT")
    study=audit_study(source_raw,native_raw,cue_raw,e3_raw,pairs_raw,
                      window_size=window_size)
    native=json.loads(native_raw)
    plan=source_child_plan(source_raw,native["video_id"],
                           expected_source_sha256=expected_source_sha256,
                           window_size=window_size)
    source=plan["source"]
    _need(study["original_cues"]==expected_cue_count==
          len(plan["cue_rows"]),"CUE_250_CENSUS_DRIFT")
    _need(len(plan["children"])==expected_child_count,
          "THIRTEEN_CHILD_PLAN_CENSUS_DRIFT")
    _need(source.manifest_sha256==native["manifest_sha256"],
          "PARENT_NATIVE_MANIFEST_DRIFT")
    bywindow={w["owner_window_id"]:w for w in plan["children"]}
    atom_rows=[]
    for atom in native["atoms"]:
        wid=atom["owner_window_id"]
        _need(wid in bywindow,"ATOM_OWNER_MISSING_CHILD")
        parent_refs=[]
        for ref in atom["source_refs"]:
            i=ref["cue_index"]
            _need(source.owner(i)==wid,"ATOM_PRIMARY_CUE_OWNER_CHANGED")
            _need(ref["quote"] in source.cues[i-1].text,"ATOM_PRIMARY_QUOTE_DRIFT")
            parent_refs.append({"cue_index":i,
                    "cue_quote_sha256":sha256(source.cues[i-1].text.encode("utf-8")),
                    "source_excerpt_sha256":sha256(ref["quote"].encode("utf-8"))})
        atom_rows.append({"claim_id":atom["claim_id"],
                "owner_child_id":bywindow[wid]["child_id"],
                "primary_source_refs":parent_refs,
                "full_parent_atom_sha256":json_digest(atom)})
    _need(len({r["claim_id"] for r in atom_rows})==len(atom_rows)==
          study["unapproved_native_atoms"],"ATOM_DUPLICATE_OR_LOSS")
    links=foreign_context_links(source,native["atoms"])
    crossids=sorted({r["claim_id"] for r in links})
    core={"original_source_sha256":source.source_sha256,
          "parent_manifest_sha256":source.manifest_sha256,
          "native_exchange_sha256":expected_native_sha256,
          "cue_census_sha256":source.cue_census_sha256,
          "children":plan["children"],"cue_rows":plan["cue_rows"],
          "parent_atom_rows":atom_rows,
          "cross_child_full_parent_source_edges":links}
    return {"schema":SCHEMA,
            "video_id":source.video_id,
            "original_source_sha256":source.source_sha256,
            "parent_manifest_sha256":source.manifest_sha256,
            "original_cue_count":len(plan["cue_rows"]),
            "child_count":len(plan["children"]),
            "atomic_candidate_count":len(atom_rows),
            "cross_child_parent_atom_count":len(crossids),
            "cross_child_typed_source_edge_count":len(links),
            "source_graph_sha256":json_digest(core),
            "child_manifest_sha256s":[json_digest(x) for x in plan["children"]],
            "children":plan["children"],
            "source_cue_hashes":[r["source_quote_sha256"] for r in plan["cue_rows"]],
            "cross_child_source_links":links,
            "all_cues_exact_original_replayed":True,
            "parent_to_child_lineage_loss_count":0,
            "source_first_review_is_not_e2_gold":True,
            "e3_final_approved":False,
            "e4_financial_fact_approved":False,
            "e5_knowledge_published":False,
            "p0_go":False}
