"""V217: original-byte-pinned cross-cue condition, exception and fictional-scope custody.

A frozen V6 structural pass does not prove that meaning survives when atoms
are passed downstream individually. Source, native and reviewer relation bytes
are all pinned. Receipt carries no source text and never grants approval.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan


def require(ok, reason):
    if not ok:
        raise InvalidInput("V217_E2_" + reason)


def pin_json(raw, parsed, expected, label):
    require(type(raw) is bytes and type(parsed) is dict and
            type(expected) is str and len(expected)==64,
            label+"_INPUT")
    try:
        obj=json.loads(raw)
    except (ValueError,UnicodeError,TypeError) as exc:
        raise InvalidInput("V217_E2_"+label+"_JSON_UNREADABLE") from exc
    require(obj==parsed and sha256(raw)==expected, label+"_BYTE_TAMPER")


def audit_private_crosscue_discourse(raw_srt,exchange,exchange_bytes,ledger,ledger_bytes,*,
        expected_source_sha256,expected_exchange_sha256,expected_ledger_sha256,
        window_size=20):
    require(type(raw_srt) is bytes and type(expected_source_sha256) is str and
            sha256(raw_srt)==expected_source_sha256,
            "ORIGINAL_SOURCE_BYTES_CHANGED")
    pin_json(exchange_bytes,exchange,expected_exchange_sha256,"NATIVE")
    pin_json(ledger_bytes,ledger,expected_ledger_sha256,"LEDGER")
    require(type(window_size) is int and 1<=window_size<=1000 and
            type(exchange.get("video_id")) is str,
            "SOURCE_PLAN_ARGS")
    source,_=make_original_plan(raw_srt,exchange["video_id"],
            expected_source_sha256=expected_source_sha256,
            window_size=window_size)
    native_receipt=audit_host_atomic_exchange(source,exchange)
    require(ledger.get("video_id")==source.video_id and
            ledger.get("original_source_sha256")==expected_source_sha256 and
            ledger.get("total_cues")==len(source.cues) and
            ledger.get("chat_review_of_relation_not_external_gold") is True and
            ledger.get("each_relation_has_both_original_quotes") is True and
            ledger.get("e2_final_pass") is False and
            ledger.get("e3_e4_e5_authorized") is False and
            ledger.get("financial_truth_certified") is False and
            ledger.get("native_v6_claims_issued") is False,
            "LEDGER_CUSTODY_OR_FALSE_APPROVAL")
    relations=ledger.get("relations")
    require(type(relations) is list and 1<=len(relations)<=1000 and
            ledger.get("relation_count")==len(relations) and
            len(source.cues)<=2000 and len(exchange["atoms"])<=512,
            "BOUNDED_RELATION_CENSUS")
    bycue=defaultdict(set)
    for atom in exchange["atoms"]:
        require(type(atom.get("claim_id")) is str and
                type(atom.get("context_cue_indices")) is list and
                atom.get("speaker")=="UNKNOWN" and
                atom.get("stance")=="UNRESOLVED",
                "UNAPPROVED_ATOM_REQUIRED")
        for i in atom["context_cue_indices"]:
            require(type(i) is int and 1<=i<=len(source.cues),
                    "INVALID_NATIVE_CONTEXT_CUE")
            bycue[i].add(atom["claim_id"])
    results=[];seen=set();counts=Counter()
    required={"relation_id","from_cue","to_cue","from_quote","to_quote",
        "from_source_text_sha256","to_source_text_sha256","relation_type",
        "chat_reviewer_interpretation_not_source_speaker",
        "semantic_relation_independently_confirmed","financial_fact_approved"}
    for item in relations:
        require(type(item) is dict and set(item)==required,
                "RELATION_FIELDS")
        rid=item["relation_id"];i=item["from_cue"];j=item["to_cue"]
        require(type(rid) is str and rid and rid not in seen and
                type(i) is int and type(j) is int and
                1<=i<=len(source.cues) and 1<=j<=len(source.cues) and i!=j and
                type(item["relation_type"]) is str and
                2<=len(item["relation_type"])<=80 and
                type(item["chat_reviewer_interpretation_not_source_speaker"]) is str and
                item["semantic_relation_independently_confirmed"] is False and
                item["financial_fact_approved"] is False,
                "RELATION_ID_SCOPE_OR_FALSE_GOLD")
        seen.add(rid)
        for cue_index,prefix in ((i,"from"),(j,"to")):
            quote=item[prefix+"_quote"];expected=item[prefix+"_source_text_sha256"]
            cue=source.cues[cue_index-1].text
            require(type(quote) is str and len(quote.strip())>=2 and
                    quote in cue and type(expected) is str and
                    sha256(cue.encode("utf-8"))==expected,
                    "RELATION_QUOTE_OR_SOURCE_SHA_CHANGED")
        a,b=bycue[i],bycue[j];shared=a&b
        cls=("SAME_ATOM_CONTEXT" if shared else
             "CROSS_ATOM_DEPENDENCY" if a and b else
             "UNMAPPED_SOURCE_CUE_HOLD")
        counts[cls]+=1
        results.append({"relation_id":rid,"relation_type":item["relation_type"],
            "source_cue":i,"target_cue":j,
            "source_native_ids":sorted(a),"target_native_ids":sorted(b),
            "same_native_context_ids":sorted(shared),
            "custody_state":cls,
            "fully_reconciled_for_semantic_approval":False,
            "external_gold_certified":False,
            "approval_handback_authorized":False})
    return {"schema":"IRE_V217_E2_OWNER_PRIVATE_CROSS_CUE_DISCOURSE_CUSTODY_V1",
        "source_sha256":expected_source_sha256,
        "native_exchange_sha256":expected_exchange_sha256,
        "relation_ledger_sha256":expected_ledger_sha256,
        "frozen_v6_atom_digest":native_receipt["atom_candidate_digest"],
        "original_cues":len(source.cues),"native_unapproved_atoms":len(exchange["atoms"]),
        "source_relations_checked":len(relations),
        "same_atom_context_relations":counts["SAME_ATOM_CONTEXT"],
        "cross_atom_unresolved_relations":counts["CROSS_ATOM_DEPENDENCY"],
        "unmapped_cue_relations":counts["UNMAPPED_SOURCE_CUE_HOLD"],
        "relation_rows":results,
        "owner_v176_historical_lineage_replayed":False,
        "automatic_qualifier_inference":False,
        "automatic_merge":False,
        "independent_semantic_gold_certified":False,
        "financial_fact_approved":False,"e2_final_pass":False,
        "e3_e4_e5_authorized":False,"knowledge_published":False,
        "status":"HOLD_CROSS_ATOM_DEPENDENCY_OR_UNMAPPED_CUE"}


def require_no_unresolved_discourse_for_approval(receipt):
    """Block downstream use until explicit edges and independent gold exist."""
    require(type(receipt) is dict and
            receipt.get("schema")=="IRE_V217_E2_OWNER_PRIVATE_CROSS_CUE_DISCOURSE_CUSTODY_V1" and
            receipt.get("e2_final_pass") is False and
            receipt.get("independent_semantic_gold_certified") is False,
            "SIDE_CAR_NOT_APPROVAL_PROOF")
    require(receipt.get("cross_atom_unresolved_relations")==0 and
            receipt.get("unmapped_cue_relations")==0 and
            receipt.get("source_relations_checked",0)>0,
            "UNRESOLVED_RELATIONS_BLOCK_APPROVAL")
    raise InvalidInput("V217_E2_INDEPENDENT_MEANING_GOLD_NOT_ATTESTED")
