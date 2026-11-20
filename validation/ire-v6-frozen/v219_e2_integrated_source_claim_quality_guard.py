"""V219: frozen-real-source and source-cue custody, NOT a semantic-gold certificate.

Owner-private originals and sidecars are never committed. The public CI runs
synthetic regressions only; the owner-private replay uses original SRT bytes.
"""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan

SCHEMA_CENSUS="IRE_V219_PRIVATE_SOURCE_FIRST_250_CUE_REVIEW_V1"
SCHEMA_FINANCE="IRE_V219_PRIVATE_ALL_66_ATOMS_SEMANTIC_FINANCE_REVIEW_V1"
SCHEMA_LEGACY="IRE_V219_PRIVATE_V182_17OPEN_SOURCE_ONLY_V176_OWNER_UNAVAILABLE_CROSSWALK_V1"
SCHEMA_PATCH="IRE_V219_NATIVE66_SOURCE_RISK_PRECISE_CORRECTIONS_V1"
SCHEMA_RECEIPT="IRE_V219_E2_INTEGRATED_REAL_SOURCE_AND_UNAPPROVED_CLAIM_CUSTODY_V1"
STATES={"PRIMARY_UNAPPROVED","CONTEXT_UNAPPROVED_NEEDS_CLAIM_OMISSION_REVIEW",
        "MEDIA_DEPENDENT_UNMAPPED_QUARANTINE","DISCOURSE_OR_NONCLAIM_PROVISIONAL"}
ALLOWED_DIFF={"proposition","numeric_references"}


def require(ok,code):
    if not ok:
        raise InvalidInput("V219_E2_"+code)


def pin_json(raw,obj,expected,label):
    require(type(raw) is bytes and type(obj) is dict and type(expected) is str
            and len(expected)==64,"BAD_"+label+"_INPUT")
    require(len(raw)<=12*1024*1024,"OVERSIZE_"+label)
    try:
        parsed=json.loads(raw)
    except (TypeError,ValueError,UnicodeError) as exc:
        raise InvalidInput("V219_E2_INVALID_"+label+"_JSON") from exc
    require(parsed==obj and sha256(raw)==expected,"CHANGED_"+label+"_BYTES")


def audit_exact_source_cue_taxonomy(source,exchange,census):
    """Census is a reviewer HOLD, not the independent gold for recall."""
    require(type(census) is dict and census.get("schema")==SCHEMA_CENSUS and
            census.get("video_id")==exchange["video_id"] and
            census.get("original_source_sha256")==source.source_sha256 and
            type(census.get("rows")) is list and len(census["rows"])==len(source.cues) and
            census.get("cue_count")==len(source.cues) and
            census.get("original_audio_screen_available") is False and
            census.get("independent_gold_available") is False and
            census.get("speaker_verified") is False and
            census.get("e2_final_pass") is False and
            census.get("financial_fact_approved") is False,
            "CUE_CENSUS_HEADER_OR_FALSE_GOLD")
    byprim={i:set() for i in range(1,len(source.cues)+1)}
    bycontext={i:set() for i in byprim}
    for a in exchange["atoms"]:
        for r in a["source_refs"]:byprim[r["cue_index"]].add(a["claim_id"])
        for idx in a["context_cue_indices"]:bycontext[idx].add(a["claim_id"])
    summary=Counter();flags=0
    for idx,row in enumerate(census["rows"],1):
        require(type(row) is dict and type(row.get("cue_index")) is int and
                row["cue_index"]==idx and
                row.get("source_quote")==source.cues[idx-1].text and
                row.get("cue_text_sha256")==sha256(source.cues[idx-1].text.encode("utf-8")),
                "CUE_OR_QUOTE_NOT_ORIGINAL")
        require(row.get("source_anchor_claim_ids")==sorted(byprim[idx]) and
                row.get("context_claim_ids")==sorted(bycontext[idx]) and
                row.get("classification") in STATES and
                row.get("independent_omission_review_complete") is False and
                row.get("classification_is_chatgpt_source_review_not_external_gold") is True and
                row.get("financial_fact_approved") is False and
                row.get("e2_final_pass") is False and
                type(row.get("original_audio_or_screen_review_required")) is bool,
                "CUE_NATIVE_LINK_OR_PREMATURE_OMISSION_GOLD")
        expected=("PRIMARY_UNAPPROVED" if byprim[idx] else
                  "CONTEXT_UNAPPROVED_NEEDS_CLAIM_OMISSION_REVIEW" if bycontext[idx] else
                  "MEDIA_DEPENDENT_UNMAPPED_QUARANTINE" if row.get("visual_claim_requires_original_frames") is True else
                  "DISCOURSE_OR_NONCLAIM_PROVISIONAL")
        require(row["classification"]==expected,"MISCLASSIFIED_SOURCE_CUE")
        if row["classification"]=="MEDIA_DEPENDENT_UNMAPPED_QUARANTINE":
            require(row["original_audio_or_screen_review_required"] is True,
                    "VIDEO_HOLD_DROPPED")
        if row["classification"]=="DISCOURSE_OR_NONCLAIM_PROVISIONAL":
            require(type(row.get("nonclaim_or_discourse_explanation")) is str and
                    len(row["nonclaim_or_discourse_explanation"])>4,
                    "UNJUSTIFIED_NO_ATOM_CLASSIFICATION")
        if row["original_audio_or_screen_review_required"]:flags+=1
        summary[row["classification"]]+=1
    require(census.get("classification_counts")==dict(sorted(summary.items())) and
            census.get("distinct_primary_claim_ids")==len({a for ids in byprim.values() for a in ids}) and
            census.get("audio_screen_flagged_cue_count")<=flags,
            "FAKE_CUE_CLASS_TOTALS")
    return dict(sorted(summary.items())),flags


def audit_semantic_native_delta(old,new,changes,source):
    require(type(old) is dict and type(new) is dict and type(changes) is dict and
            changes.get("schema")==SCHEMA_PATCH and
            changes.get("source_sha256")==source.source_sha256 and
            changes.get("atom_count_before")==len(old.get("atoms",[])) and
            changes.get("atom_count_after")==len(new.get("atoms",[])) and
            changes.get("speaker_diarization_verified") is False and
            changes.get("e2_final_pass") is False and
            new.get("cue_dispositions")==old.get("cue_dispositions"),
            "NATIVE_CHANGE_CUSTODY_INVALID")
    old_by={a["claim_id"]:a for a in old["atoms"]}
    new_by={a["claim_id"]:a for a in new["atoms"]}
    require(len(old_by)==len(new_by)==len(old["atoms"])==len(new["atoms"]) and
            set(old_by)==set(new_by),"NATIVE_IDS_CHANGED")
    delta=[]
    for cid in sorted(old_by):
        a,b=old_by[cid],new_by[cid]
        changed={k for k in a if a[k]!=b.get(k)} | (set(b)-set(a))
        require(changed<=ALLOWED_DIFF,"NATIVE_OWNER_CONTEXT_OR_STATUS_TAMPERED")
        for key in sorted(changed):
            cue=a["source_refs"][0]["cue_index"]
            delta.append({"claim_id":cid,"field":key,"previous_value":a[key],
                "corrected_value":b[key],"original_primary_cue":cue,
                "source_cue_text_sha256":sha256(source.cues[cue-1].text.encode("utf-8")),
                "financial_fact_approved":False})
    require(type(changes.get("changes")) is list and delta==changes["changes"] and
            changes.get("changed_claim_ids")==sorted({r["claim_id"] for r in delta}) and
            changes.get("changed_fields_count")==len(delta),
            "NATIVE_EDIT_LOG_INCOMPLETE_OR_FALSE")
    # Source-size contamination: high-volume cue 228 may not inherit unrelated
    # 415 AUM from source context cue 227 as the volume proposition's number.
    if "C00067" in new_by:
        require(not any(ref.get("cue_index")==227 and ref.get("token")=="415"
            for ref in new_by["C00067"].get("numeric_references",[])),
            "VOLUME_INHERITED_ASSET_NUMBER")
    return len(delta),len({r["claim_id"] for r in delta})


def audit_financial_and_legacy_hold(source,exchange,finance,legacy,old_open):
    require(type(finance) is dict and finance.get("schema")==SCHEMA_FINANCE and
            finance.get("source_sha256")==source.source_sha256 and
            finance.get("video_id")==exchange["video_id"] and
            finance.get("original_audio_screen_available") is False and
            finance.get("human_independent_gold_available") is False and
            finance.get("external_independent_gold") is False and
            finance.get("precision_measured") is False and
            finance.get("recall_measured") is False and
            finance.get("high_risk_miss_zero_certified") is False and
            finance.get("e2_final_pass") is False and
            finance.get("knowledge_publication_authorized") is False and
            type(finance.get("atoms")) is list and
            finance.get("all_atoms_reviewed_source_claims")==len(finance["atoms"])==len(exchange["atoms"]),
            "FINANCE_FALSE_CERTIFICATION_OR_CENSUS")
    amap={a["claim_id"]:a for a in exchange["atoms"]}
    seen=set();risk=0
    for r in finance["atoms"]:
        require(type(r) is dict and type(r.get("claim_id")) is str and
                r["claim_id"] in amap and r["claim_id"] not in seen,
                "FINANCE_DUPLICATE_OR_MISSING_CLAIM")
        a=amap[r["claim_id"]];seen.add(r["claim_id"])
        cues=[x["cue_index"] for x in a["source_refs"]]
        require(r.get("kind")==a["kind"] and
                r.get("primary_cue_ids")==cues and
                r.get("primary_original_text_sha256")==[
                    sha256(source.cues[i-1].text.encode("utf-8")) for i in cues] and
                r.get("context_cue_indices")==a["context_cue_indices"] and
                r.get("numeric_source_token_cue_pairs")==[
                    {"cue_index":t["cue_index"],"source_token":t["token"]}
                    for t in a["numeric_references"]],
                "FINANCIAL_TOKEN_OR_SOURCE_MISATTRIBUTION")
        tags=r.get("risk_tags")
        require(type(tags) is list and all(type(t) is str and 3<=len(t)<=100 for t in tags) and
                len(set(tags))==len(tags) and
                r.get("speaker_verified") is False and r.get("stance_confirmed") is False and
                r.get("financial_truth_certified") is False and
                r.get("semantically_gold_verified") is False and
                r.get("claim_approved") is False and
                r.get("risk_review_status")==(
                    "HOLD_REQUIRES_OFFICIAL_OR_MEDIA_REVIEW" if tags else
                    "SOURCE_ANCHORED_BUT_NOT_INDEPENDENT_GOLD"),
                "FINANCE_RISK_BYPASS_OR_FALSE_APPROVAL")
        risk+=int(bool(tags))
    require(seen==set(amap) and finance.get("risk_tagged_atom_count")==risk and
            finance.get("risk_tag_types")==sorted({t for r in finance["atoms"] for t in r["risk_tags"]}),
            "FINANCE_RISK_COUNT_DRIFT")
    require(type(legacy) is dict and type(old_open) is dict and
            legacy.get("schema")==SCHEMA_LEGACY and
            legacy.get("source_sha256")==source.source_sha256 and
            legacy.get("native_exchange_sha256")==finance.get("native_exchange_sha256") and
            legacy.get("historical_recovered_owner_sqlite") is False and
            legacy.get("historical_v176_claim61_69_71_verified") is False and
            legacy.get("historical_cases_resolved")==0 and
            legacy.get("e2_final_pass") is False and
            type(legacy.get("rows")) is list and type(old_open.get("rows")) is list and
            legacy.get("source_only_legacy_risk_rows_verified")==len(legacy["rows"])==len(old_open["rows"]),
            "HISTORICAL_OWNER_FORGED_OR_OPEN_DROPPED")
    for old,row in zip(old_open["rows"],legacy["rows"]):
        require(type(old) is dict and type(row) is dict,
                "MALFORMED_HISTORICAL_ROW")
        idx=old.get("cue_index")
        prim=sorted({a["claim_id"] for a in exchange["atoms"] for q in a["source_refs"]
                     if q["cue_index"]==idx})
        ctx=sorted({a["claim_id"] for a in exchange["atoms"]
                    if idx in a["context_cue_indices"]})
        require(type(idx) is int and 1<=idx<=len(source.cues) and
                old["source_quote"]==source.cues[idx-1].text and
                old["source_text_sha256"]==sha256(source.cues[idx-1].text.encode("utf-8")) and
                row.get("cue_index")==idx and
                row.get("open_type")==old["historical_v182_open_type"] and
                row.get("cue_text_sha256")==old["source_text_sha256"] and
                row.get("linked_native_unapproved_primary_ids")==prim and
                row.get("linked_native_unapproved_context_ids")==ctx and
                row.get("historical_open_still_unresolved") is True and
                row.get("owner_sqlite_source_event_chain_verified") is False and
                row.get("independent_gold_verified") is False and
                row.get("financial_fact_approved") is False,
                "V182_OPEN_CASE_CHANGED_OR_FALSE_RECOVERY")
    return risk,len(legacy["rows"])


def run_integrated_e2_source_gate(raw_srt,old_native,old_native_bytes,new_native,
        new_native_bytes,census,census_bytes,finance,finance_bytes,legacy,legacy_bytes,
        old_open,old_open_bytes,patch,patch_bytes,prior_graph,prior_graph_bytes,
        *,expected_hashes,window_size=20):
    names={"source":raw_srt,"old_native":old_native_bytes,
           "new_native":new_native_bytes,"census":census_bytes,
           "finance":finance_bytes,"legacy":legacy_bytes,
           "old_open":old_open_bytes,"patch":patch_bytes,"prior_graph":prior_graph_bytes}
    require(type(expected_hashes) is dict and set(expected_hashes)==set(names) and
            all(type(x) is bytes for x in names.values()) and
            all(type(expected_hashes[k]) is str and len(expected_hashes[k])==64 and
                sha256(names[k])==expected_hashes[k] for k in names),
            "SOURCE_SIDECAR_BYTE_HASH_MISMATCH")
    for label,obj in (("old_native",old_native),("new_native",new_native),
                      ("census",census),("finance",finance),("legacy",legacy),
                      ("old_open",old_open),("patch",patch),("prior_graph",prior_graph)):
        pin_json(names[label],obj,expected_hashes[label],label)
    require(type(window_size) is int and 1<=window_size<=1000,
            "SOURCE_WINDOW_SIZE")
    source,_=make_original_plan(raw_srt,new_native["video_id"],
            expected_source_sha256=expected_hashes["source"],window_size=window_size)
    old_receipt=audit_host_atomic_exchange(source,old_native)
    new_receipt=audit_host_atomic_exchange(source,new_native)
    require(census.get("native_exchange_sha256")==expected_hashes["new_native"] and
            finance.get("native_exchange_sha256")==expected_hashes["new_native"] and
            legacy.get("native_exchange_sha256")==expected_hashes["new_native"] and
            patch.get("previous_native_sha256")==expected_hashes["old_native"] and
            patch.get("corrected_native_sha256")==expected_hashes["new_native"] and
            patch.get("source_sha256")==expected_hashes["source"] and
            prior_graph.get("source_sha256")==expected_hashes["source"] and
            prior_graph.get("native_exchange_sha256")==expected_hashes["old_native"] and
            prior_graph.get("native_atom_digest")==old_receipt["atom_candidate_digest"] and
            prior_graph.get("relations_total")==sum([
                prior_graph.get("cross_atom_linked_unapproved",-1),
                prior_graph.get("same_atom_context_unapproved",-1),
                prior_graph.get("audio_video_quarantined",-1)]) and
            prior_graph.get("same_source_quoted_semantic_gold_independent") is False and
            prior_graph.get("financial_facts_approved") is False and
            prior_graph.get("e2_final_pass") is False,
            "PREVIOUS_GRAPH_OR_SOURCE_CUSTODY_INVALID")
    counts,flags=audit_exact_source_cue_taxonomy(source,new_native,census)
    changes,changed_ids=audit_semantic_native_delta(old_native,new_native,patch,source)
    risk,legacy_n=audit_financial_and_legacy_hold(source,new_native,finance,legacy,old_open)
    require(type(prior_graph.get("cross_atom_edges")) is list and
            type(prior_graph.get("same_atom_relations")) is list and
            type(prior_graph.get("evidence_quarantines")) is list and
            type(prior_graph.get("cross_atom_linked_unapproved")) is int and
            prior_graph["cross_atom_linked_unapproved"]>=0 and
            len(prior_graph["cross_atom_edges"])==prior_graph["cross_atom_linked_unapproved"] and
            len(prior_graph["same_atom_relations"])==prior_graph["same_atom_context_unapproved"] and
            len(prior_graph["evidence_quarantines"])==prior_graph["audio_video_quarantined"],
            "GRAPH_RELATION_ROWS_INCOMPLETE")
    existing={a["claim_id"]:a for a in new_native["atoms"]}
    for row in prior_graph["cross_atom_edges"]:
        require(type(row) is dict and row.get("from_atom_id") in existing and
                row.get("to_atom_id") in existing and
                row.get("from_atom_id")!=row.get("to_atom_id") and
                row.get("approved") is False and
                row.get("requires_joint_meaning_review") is True,
                "INHERITED_GRAPH_EDGE_BROKEN")
    for row in prior_graph["evidence_quarantines"]:
        require(type(row) is dict and row.get("financial_claim_approved") is False and
                row.get("evidence_required")=="ORIGINAL_VIDEO_OR_AUDIO" and
                type(row.get("target_cue")) is int and
                1<=row["target_cue"]<=len(source.cues),
                "INHERITED_GRAPH_MEDIA_HOLD_DROPPED")
    return {"schema":SCHEMA_RECEIPT,"original_source_sha256":expected_hashes["source"],
        "original_cues_verified":len(source.cues),
        "new_native_sha256":expected_hashes["new_native"],
        "native_unapproved_atoms":new_receipt["proposed_atomic_claims"],
        "new_native_atom_digest":new_receipt["atom_candidate_digest"],
        "new_native_unresolved_primary_cues":new_receipt["unresolved_cues"],
        "all_cue_review_state_counts":counts,
        "cues_flagged_audio_or_video_or_screen":flags,
        "source_risk_tagged_native_atoms":risk,
        "native_correction_field_count":changes,
        "native_correction_claim_ids":changed_ids,
        "historical_v182_source_open_cases_unresolved":legacy_n,
        "source_grounded_v218_cross_atom_relations_retained":prior_graph["cross_atom_linked_unapproved"],
        "source_grounded_v218_intra_atom_relations_retained":prior_graph["same_atom_context_unapproved"],
        "unverified_media_graph_relations_retained":prior_graph["audio_video_quarantined"],
        "historical_v176_owner_sqlite_recovered":False,
        "separate_blind_independent_gold_measured":False,
        "precision_recall_validly_computable":False,
        "financial_facts_approved":False,"e2_final_pass":False,
        "e3_e4_e5_authorized":False,"knowledge_published":False,
        "status":"HOLD_SOURCE_AND_RELATION_CUSTODY_PASS_INDEPENDENT_GOLD_OWNER_AND_MEDIA_MISSING"}


def require_gold_before_approval(receipt):
    require(type(receipt) is dict and receipt.get("schema")==SCHEMA_RECEIPT,
            "RECEIPT_NOT_A_V219_PROOF")
    require(receipt.get("separate_blind_independent_gold_measured") is True and
            receipt.get("historical_v176_owner_sqlite_recovered") is True and
            receipt.get("precision_recall_validly_computable") is True and
            receipt.get("e2_final_pass") is True,
            "INDEPENDENT_GOLD_OWNER_AND_MEDIA_NOT_CERTIFIED")
    raise InvalidInput("V219_E2_APPROVAL_REQUIRES_SEPARATE_AUTHORIZED_GATE")