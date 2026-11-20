"""V218 E2: private source-pinned cross-atom join, never approval.

The frozen V6 native exchange carries individual atoms, not all discourse
edges. A review-sidecar makes every relation's fate explicit, binds 17
inter-atom dependencies and quarantines five missing visual sources.
This is an unapproved research graph, not external independent gold.
"""
from __future__ import annotations
import json
from collections import Counter
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v217_e2_private_crosscue_discourse_guard import audit_private_crosscue_discourse

SCHEMA = "IRE_V218_E2_PRIVATE_CROSS_ATOM_REVIEW_BRIDGE_V1"
RECEIPT = "IRE_V218_E2_SOURCE_PINNED_UNAPPROVED_DEPENDENCY_GRAPH_V1"
STATES = {"CROSS_ATOM_DEPENDENCY":"LINKED_UNAPPROVED",
          "SAME_ATOM_CONTEXT":"INTRA_ATOM_UNAPPROVED",
          "UNMAPPED_SOURCE_CUE_HOLD":"QUARANTINE_VISUAL_UNVERIFIED"}
REVIEW_FIELDS = {"relation_id","source_cue","target_cue","relation_type",
                 "review_state","source_atom_id","target_atom_id","reviewer_note",
                 "is_external_gold","speaker_audio_verified","video_frame_verified",
                 "financial_fact_approved","final_semantic_approval",
                 "knowledge_publication_authorized"}


def need(ok, label):
    if not ok:
        raise InvalidInput("V218_E2_"+label)


def pin(raw, obj, expected, label):
    need(type(raw) is bytes and type(obj) is dict and type(expected) is str
         and len(expected)==64,label+"_INPUT")
    try:
        restored=json.loads(raw)
    except (TypeError,ValueError,UnicodeError) as exc:
        raise InvalidInput("V218_E2_"+label+"_JSON_UNREADABLE") from exc
    need(sha256(raw)==expected and restored==obj,label+"_ORIGINAL_BYTES_CHANGED")


def audit_private_cross_atom_join(raw_srt,exchange,exchange_bytes,ledger,
       ledger_bytes,prior_receipt,prior_receipt_bytes,coverage,coverage_bytes,
       review,review_bytes,*,expected_source_sha256,expected_exchange_sha256,
       expected_ledger_sha256,expected_prior_receipt_sha256,
       expected_coverage_sha256,expected_review_sha256,window_size=20):
    for raw,obj,digest,label in (
            (exchange_bytes,exchange,expected_exchange_sha256,"NATIVE"),
            (ledger_bytes,ledger,expected_ledger_sha256,"LEDGER"),
            (prior_receipt_bytes,prior_receipt,expected_prior_receipt_sha256,"PRIOR"),
            (coverage_bytes,coverage,expected_coverage_sha256,"COVERAGE"),
            (review_bytes,review,expected_review_sha256,"REVIEW")):
        pin(raw,obj,digest,label)
    # Existing V217 validates source SHA, frozen V6 structure, and all quotes.
    custody=audit_private_crosscue_discourse(raw_srt,exchange,exchange_bytes,
        ledger,ledger_bytes,expected_source_sha256=expected_source_sha256,
        expected_exchange_sha256=expected_exchange_sha256,
        expected_ledger_sha256=expected_ledger_sha256,window_size=window_size)
    need(custody==prior_receipt,"PRIOR_CUSTODY_REPLAY_DRIFT")
    need(type(coverage.get("cues")) is list and
         coverage.get("source_sha256")==expected_source_sha256 and
         coverage.get("new_native_v6_exchange_sha256")==expected_exchange_sha256 and
         coverage.get("full_original_cue_count")==len(coverage["cues"])==
             custody["original_cues"] and
         coverage.get("independent_gold_certified") is False and
         coverage.get("e2_final_pass") is False,
         "COVERAGE_SOURCE_OR_GOLD_MISMATCH")
    # A flag isn't evidence of a particular visual claim, but quarantined
    # edges to an unanchored visual cue must retain its unresolved status.
    cues=coverage["cues"]
    for i,cue in enumerate(cues,1):
        need(type(cue) is dict and cue.get("cue_index")==i and
             type(cue.get("original_text")) is str and
             sha256(cue["original_text"].encode("utf-8"))==
                 cue.get("cue_text_sha256") and
             type(cue.get("needs_original_audio_or_screen")) is bool,
             "COVERAGE_CUE_SOURCE_DRIFT")
    false_top=("speaker_audio_available","video_frames_available",
               "old_v176_owner_sqlite_available","independent_gold_available",
               "e2_final_pass","e3_e4_e5_authorized",
               "knowledge_publication_authorized")
    need(type(review) is dict and review.get("schema")==SCHEMA and
         review.get("video_id")==exchange.get("video_id") and
         review.get("source_sha256")==expected_source_sha256 and
         review.get("native_exchange_sha256")==expected_exchange_sha256 and
         review.get("original_relation_ledger_sha256")==expected_ledger_sha256 and
         review.get("prior_v217_relationship_receipt_sha256")==
             expected_prior_receipt_sha256 and
         review.get("coverage_sha256")==expected_coverage_sha256 and
         review.get("review_author")=="CHATGPT_SOURCE_TEXT_ONLY_REVIEW" and
         all(review.get(k) is False for k in false_top) and
         type(review.get("rows")) is list and
         review.get("total_original_relations")==len(review["rows"])==
             custody["source_relations_checked"] and
         len(review["rows"])<=1000,
         "REVIEW_HEADER_OR_APPROVAL_FALSIFICATION")
    atoms=exchange.get("atoms")
    need(type(atoms) is list and len(atoms)<=512 and
         all(type(a) is dict and type(a.get("claim_id")) is str for a in atoms),
         "UNAPPROVED_ATOM_SET")
    atom_ids={a["claim_id"] for a in atoms}
    need(len(atom_ids)==len(atoms),"DUPLICATE_NATIVE_ATOM")
    ledger_rows=ledger.get("relations")
    prior_rows=prior_receipt.get("relation_rows")
    need(type(ledger_rows) is list and type(prior_rows) is list and
         len(ledger_rows)==len(prior_rows)==len(review["rows"]),
         "HISTORICAL_RELATION_ROW_COUNT_CHANGED")
    linked=[];intra=[];held=[];counts=Counter()
    seen=set()
    for original,prior,row in zip(ledger_rows,prior_rows,review["rows"]):
        need(type(original) is dict and type(prior) is dict and
             type(row) is dict and set(row)==REVIEW_FIELDS,
             "REVIEW_ROW_FIELDS")
        rid=original.get("relation_id")
        need(type(rid) is str and rid not in seen and
             prior.get("relation_id")==rid and row.get("relation_id")==rid and
             row.get("source_cue")==original.get("from_cue")==prior.get("source_cue") and
             row.get("target_cue")==original.get("to_cue")==prior.get("target_cue") and
             row.get("relation_type")==original.get("relation_type")==
                  prior.get("relation_type") and
             type(row.get("reviewer_note")) is str and
             12<=len(row["reviewer_note"])<=2000 and
             all(row.get(k) is False for k in (
                "is_external_gold","speaker_audio_verified","video_frame_verified",
                "financial_fact_approved","final_semantic_approval",
                "knowledge_publication_authorized")),
             "REVIEW_RELATION_SOURCE_OR_FALSE_APPROVAL")
        seen.add(rid)
        custody_state=prior.get("custody_state")
        need(custody_state in STATES and
             row.get("review_state")==STATES[custody_state],
             "REVIEW_STATE_CUSTODY_DRIFT")
        a=row.get("source_atom_id");b=row.get("target_atom_id")
        state=row["review_state"]
        if state=="LINKED_UNAPPROVED":
            need(type(a) is str and type(b) is str and a!=b and
                 a in atom_ids and b in atom_ids and
                 a in prior.get("source_native_ids",[]) and
                 b in prior.get("target_native_ids",[]),
                 "CROSS_ATOM_ENDPOINT_NOT_SOURCE_LINKED")
            linked.append({"relation_id":rid,"relation_type":row["relation_type"],
                 "from_atom_id":a,"to_atom_id":b,
                 "requires_joint_meaning_review":True,"approved":False})
        elif state=="INTRA_ATOM_UNAPPROVED":
            need(type(a) is str and a==b and a in atom_ids and
                 a in prior.get("same_native_context_ids",[]),
                 "INTRA_ATOM_CUE_NOT_SHARED")
            intra.append({"relation_id":rid,"atom_id":a,"approved":False})
        else:
            need(a is None and b is None and
                 type(row["target_cue"]) is int and
                 1<=row["target_cue"]<=len(cues) and
                 cues[row["target_cue"]-1]["needs_original_audio_or_screen"] is True and
                 not prior.get("same_native_context_ids") and
                 not prior.get("target_native_ids"),
                 "UNMAPPED_VISUAL_EVIDENCE_NOT_HELD")
            source_ids=prior.get("source_native_ids")
            need(type(source_ids) is list and
                 all(type(x) is str and x in atom_ids for x in source_ids),
                 "VISUAL_SOURCE_CONTEXT_INVALID")
            held.append({"relation_id":rid,"target_cue":row["target_cue"],
                 "origin_atom_ids":sorted(source_ids),
                 "evidence_required":"ORIGINAL_VIDEO_OR_AUDIO",
                 "financial_claim_approved":False})
        counts[state]+=1
    need(counts["LINKED_UNAPPROVED"]==review.get("cross_atom_edges_reviewed")==
              custody["cross_atom_unresolved_relations"] and
         counts["INTRA_ATOM_UNAPPROVED"]==review.get("intra_atom_context_reviewed")==
              custody["same_atom_context_relations"] and
         counts["QUARANTINE_VISUAL_UNVERIFIED"]==review.get("visual_quarantines_reviewed")==
              custody["unmapped_cue_relations"] and
         len(seen)==len(ledger_rows),"INCOMPLETE_RELATION_CENSUS")
    return {
       "schema":RECEIPT,"source_sha256":expected_source_sha256,
       "native_exchange_sha256":expected_exchange_sha256,
       "native_atom_digest":custody["frozen_v6_atom_digest"],
       "historical_relation_ledger_sha256":expected_ledger_sha256,
       "private_review_sha256":expected_review_sha256,
       "relations_total":len(seen),"cross_atom_linked_unapproved":len(linked),
       "same_atom_context_unapproved":len(intra),
       "audio_video_quarantined":len(held),
       "cross_atom_edges":linked,"same_atom_relations":intra,
       "evidence_quarantines":held,
       "unreviewed_relations":0,
       "source_relation_lineage_complete":True,
       "same_source_quoted_semantic_gold_independent":False,
       "speaker_audio_verified":False,"video_screen_verified":False,
       "financial_facts_approved":False,"e2_final_pass":False,
       "e3_e4_e5_authorized":False,"knowledge_published":False,
       "status":"DEPENDENCIES_EXPLICIT_UNAPPROVED_VISUAL_HOLD",
    }


def prepare_research_dependency_closure(requested_atom_ids,receipt):
    """Return bounded required context. This cannot authorize advice/approval."""
    need(type(receipt) is dict and receipt.get("schema")==RECEIPT and
         receipt.get("e2_final_pass") is False and
         receipt.get("financial_facts_approved") is False and
         type(receipt.get("cross_atom_edges")) is list and
         type(receipt.get("evidence_quarantines")) is list,
         "RESEARCH_RECEIPT_NOT_VERIFIED")
    need(type(requested_atom_ids) is list and 1<=len(requested_atom_ids)<=512 and
         all(type(x) is str and x for x in requested_atom_ids) and
         len(requested_atom_ids)==len(set(requested_atom_ids)),
         "RESEARCH_REQUEST_ATOM_IDS")
    edges=receipt["cross_atom_edges"]
    graph={}
    for edge in edges:
        need(type(edge) is dict and
             type(edge.get("from_atom_id")) is str and
             type(edge.get("to_atom_id")) is str and
             edge.get("approved") is False,
             "RESEARCH_EDGE_UNTRUSTED")
        a,b=edge["from_atom_id"],edge["to_atom_id"]
        graph.setdefault(a,set()).add(b)
        graph.setdefault(b,set()).add(a)
    universe=set(graph)
    universe.update(x for x in graph.values() for x in x)
    universe.update(x["atom_id"] for x in receipt.get("same_atom_relations",[])
                    if type(x) is dict and type(x.get("atom_id")) is str)
    need(all(a in universe for a in requested_atom_ids),
         "RESEARCH_UNKNOWN_ATOM_NO_PROVEN_CONTEXT")
    selected=set(requested_atom_ids)
    for _ in range(513):
        more=set().union(*(graph.get(x,set()) for x in selected)) if selected else set()
        if more.issubset(selected):
            break
        selected.update(more)
        need(len(selected)<=512,"RESEARCH_GRAPH_TOO_LARGE")
    else:
        raise InvalidInput("V218_E2_RESEARCH_GRAPH_CYCLE_BOUND")
    affected=[x["relation_id"] for x in edges if
              x["from_atom_id"] in selected or x["to_atom_id"] in selected]
    intra=[x["relation_id"] for x in receipt.get("same_atom_relations",[])
           if type(x) is dict and x.get("atom_id") in selected]
    held=[];global_unmapped=[]
    for item in receipt["evidence_quarantines"]:
        need(type(item) is dict and type(item.get("relation_id")) is str and
             type(item.get("origin_atom_ids")) is list and
             all(type(x) is str for x in item["origin_atom_ids"]) and
             item.get("financial_claim_approved") is False,
             "VISUAL_QUARANTINE_RECEIPT_UNTRUSTED")
        origin=set(item["origin_atom_ids"])
        if not origin:
            global_unmapped.append(item["relation_id"])
        elif origin & selected:
            held.append(item["relation_id"])
    return {"schema":"IRE_V218_E2_UNAPPROVED_CONTEXT_CLOSURE_V1",
        "requested_atom_ids":sorted(requested_atom_ids),
        "mandatory_context_atom_ids":sorted(selected),
        "source_relation_ids":sorted(affected),
        "intra_atom_relation_ids":sorted(intra),
        "media_evidence_quarantine_relation_ids":sorted(held),
        "global_unmapped_quarantine_relation_ids":sorted(global_unmapped),
        "media_quarantine_present":bool(held or global_unmapped),
        "knowledge_approval_authorized":False,
        "independent_gold_certified":False,
        "e2_final_pass":False}


def require_approved_handoff(receipt):
    """No frozen approval path is enabled from internal source-only reviews."""
    need(type(receipt) is dict and receipt.get("schema")==RECEIPT,
         "APPROVAL_GRAPH_RECEIPT_REQUIRED")
    raise InvalidInput("V218_E2_INDEPENDENT_GOLD_AND_MEDIA_EVIDENCE_REQUIRED")