"""E1 repair: create native V6 child host batches from real V176 journal.

Unlike V202's failed test, this never takes an already-host-committed V166
case as native input. Each child V6 model, ledger proof and host receipt is
created FROM the V176 source-first journal and separately SHA-pinned explicit
qualifier anchors. The chat host authors post-host V123 review and relations.

No built-in financial conclusions, source meaning, law checks or approval.
Do not claim E2/E3/E4/E5 PASS merely from synthetic green tests.
"""
from __future__ import annotations

import copy
import sqlite3

from ire.v6 import TransactionStore
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from v176_chat_engine_loop import EngineChatSession
from v201_e1_native_source_bridge import bridge_v176_to_v6
from v166_e3_chat_decision_delivery import run_full_video_with_e3_decisions

SCHEMA="IRE_E1_V176_ORIGIN_NATIVE_HOST_TO_V128_V1"
QUAL_SCHEMA="IRE_E1_SOURCE_QUALIFIER_ATTESTATION_V1"


def need(ok, code):
    if not ok:
        raise InvalidInput("E1_NATIVE_ORIGIN_" + code)


def _source_constraints(owner, full_exchange):
    """Read frozen private V176 claim records, never a V166 approved packet."""
    with owner._connect() as con:
        _, reviewed=owner._audit(con)
    result={}
    for atom in full_exchange["atoms"]:
        idx=atom["source_refs"][0]["cue_index"]
        need(idx in reviewed and reviewed[idx][1]["disposition"]=="ASSERTION",
             "SOURCE_CLAIM_NOT_REVIEWED")
        original=reviewed[idx][1]["claims"]
        matched=[c for c in original if
                 c["proposition"]==atom["proposition"] and
                 c["kind"]==atom["kind"] and
                 c["quote"]==atom["source_refs"][0]["quote"]]
        need(len(matched)==1,"SOURCE_CLAIM_AMBIGUOUS_OR_MISSING")
        result[atom["claim_id"]]=matched[0]
    return result


def bind_explicit_qualifiers(owner, full_exchange, qualifier_attestation, *,
                             expected_qualifier_sha256, expected_owner_head):
    """Project only source-quoted qualifier terms explicitly bound by ChatGPT.

    A SHA equality is a custody check, NOT a signature or semantic truth proof.
    The qualifier mapping must have been authored and externally pinned before
    the function, not constructed silently from the source text here.
    """
    need(type(qualifier_attestation) is dict and
         set(qualifier_attestation)=={
             "schema","review_executor","owner_source_sha256",
             "owner_head_sha256","owner_manifest_sha256",
             "entries","financial_truth_certified"},
         "EXPLICIT_QUALIFIER_DOCUMENT_REQUIRED")
    doc=qualifier_attestation
    need(doc["schema"]==QUAL_SCHEMA and
         doc["review_executor"]=="CHATGPT_IN_CHAT" and
         doc["financial_truth_certified"] is False and
         doc["owner_source_sha256"]==owner.source.source_sha256 and
         doc["owner_manifest_sha256"]==owner.source.manifest_sha256 and
         doc["owner_head_sha256"]==expected_owner_head and
         json_digest(doc)==expected_qualifier_sha256 and
         type(doc["entries"]) is list,
         "QUALIFIER_DOCUMENT_PIN_OR_SOURCE_DRIFT")
    source_claims=_source_constraints(owner, full_exchange)
    expected=[]
    for atom in full_exchange["atoms"]:
        claim=source_claims[atom["claim_id"]]
        for field in ("conditions","exceptions"):
            for ordinal,term in enumerate(claim[field]):
                expected.append((atom["claim_id"],field,ordinal,term))
    seen=set()
    out=copy.deepcopy(full_exchange)
    by_id={atom["claim_id"]:atom for atom in out["atoms"]}
    for row in doc["entries"]:
        need(type(row) is dict and set(row)=={
            "claim_id","field","term_ordinal","verbatim_term",
            "cue_index","cue_text_sha256","original_atom_sha256",
            "chat_source_context_checked","review_note_sha256"},
            "QUALIFIER_ENTRY_SCHEMA")
        cid=row["claim_id"]
        key=(cid,row["field"],row["term_ordinal"],row["verbatim_term"])
        need(key in expected and key not in seen and
             type(row["cue_index"]) is int and
             1<=row["cue_index"]<=len(owner.source.cues) and
             row["cue_text_sha256"]==
                sha256(owner.source.cues[row["cue_index"]-1].text.encode("utf-8")) and
             row["original_atom_sha256"]==
                json_digest(next(x for x in full_exchange["atoms"]
                                 if x["claim_id"]==cid)) and
             row["verbatim_term"] in owner.source.cues[row["cue_index"]-1].text and
             row["chat_source_context_checked"] is True and
             type(row["review_note_sha256"]) is str and
             len(row["review_note_sha256"])==64,
             "QUALIFIER_ANCHOR_OR_UNAUTHORISED_SCOPE")
        seen.add(key)
        atom=by_id[cid]
        target=("condition_cue_indices" if row["field"]=="conditions"
                else "exception_cue_indices")
        atom[target]=sorted(set(atom[target]+[row["cue_index"]]))
        atom["context_cue_indices"]=sorted(
            set(atom["context_cue_indices"]+[row["cue_index"]]))
    need(seen==set(expected),"QUALIFIER_CENSUS_INCOMPLETE")
    return out


def _child_exchange(parent, child_manifest):
    first,last=(child_manifest["scope"]["first_cue"],
                child_manifest["scope"]["last_cue"])
    result=copy.deepcopy(parent)
    result["manifest_sha256"]=json_digest(child_manifest)
    result["cue_dispositions"]=[
        r for r in parent["cue_dispositions"]
        if first<=r["cue_index"]<=last]
    result["atoms"]=[]
    for candidate in parent["atoms"]:
        sources=[r["cue_index"] for r in candidate["source_refs"]]
        if sources and first<=sources[0]<=last:
            need(all(first<=x<=last for x in sources),
                 "CROSS_CHILD_SOURCE_ANCHOR_NEEDS_SEAM_REVIEW")
            atom=copy.deepcopy(candidate)
            # The parent's context may include adjacent children. Keep only
            # inside-child references and REQUIRE explicit parent seam review.
            for key in ("context_cue_indices","condition_cue_indices",
                        "exception_cue_indices"):
                atom[key]=[i for i in atom[key] if first<=i<=last]
            atom["numeric_references"]=[
                x for x in atom["numeric_references"]
                if first<=x["cue_index"]<=last]
            result["atoms"].append(atom)
    return result


def _native_models(source, exchange):
    models,reviews={},{}
    for wid,_,_ in source.primary_windows:
        claims=[]
        for atom in exchange["atoms"]:
            if atom["owner_window_id"]!=wid:
                continue
            refs=[x["cue_index"] for x in atom["source_refs"]]
            claims.append({
                "claim_id":atom["claim_id"],
                "proposition":atom["proposition"],
                "kind":atom["kind"],
                "owner_window_id":wid,
                "source_refs":atom["source_refs"],
                "context_first_cue":min(refs),
                "context_last_cue":max(refs)})
        models[wid]={"schema":"IRE_V6_ATOMIC_MODEL_V1","claims":claims}
        reviews[wid]={"schema":"IRE_V6_STRUCTURAL_REVIEW_V1",
                      "review_scope":"SOURCE_ANCHORS_ONLY",
                      "reviewed_claim_ids":sorted(x["claim_id"] for x in claims),
                      "independent_gold_verified":False}
    return models,reviews


def _counts(store):
    with sqlite3.connect(store.path) as con:
        names={r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        return {n:con.execute("SELECT COUNT(*) FROM "+n).fetchone()[0]
                if n in names else 0 for n in
                ("events","knowledge","parent_publications")}


def run_origin_native_e1(owner, parent_native_store, checkpoint, knowledge_store,
                         *, scope_id, inventory_bytes,
                         expected_inventory_sha256, expected_owner_head,
                         qualifier_attestation, expected_qualifier_sha256,
                         native_child_inputs, review_native_child,
                         review_seams, review_parent,
                         expected_knowledge_head, new_parent_scope=True):
    """One synchronous structural pass using V176-derived native host receipts.

    Native child inputs callback supplies fresh PRIVATE TransactionStore,
    independent child-owner inventory, and externally pre-frozen prior metadata.
    ChatGPT review callback is invoked ONLY AFTER the actual host batch.
    Both are explicit user/host inputs; no synthetic review is made in code.
    """
    need(type(owner) is EngineChatSession and
         type(parent_native_store) is TransactionStore and
         all(callable(fn) for fn in (
             native_child_inputs,review_native_child,review_seams,review_parent)),
         "ACTUAL_PRIVATE_STORES_AND_CHAT_CALLBACKS_REQUIRED")
    progress=owner.progress()
    need(progress["checkpoint_head_sha256"]==expected_owner_head and
         progress["source_first_review_complete"] is True and
         progress["cue_remaining"]==0 and progress["unresolved_open_cues"]==0,
         "OWNER_SOURCE_NOT_FROZEN_AND_REVIEWED")
    need(checkpoint.raw==owner.raw and
         checkpoint.parent_manifest==owner.manifest,
         "PARENT_SOURCE_PLAN_SUBSTITUTED")
    source_exchange,stage=owner.compile_native_v6_stage()
    need(stage["checkpoint_head_sha256"]==expected_owner_head and
         source_exchange["source_sha256"]==progress["source_sha256"],
         "OWNER_NATIVE_STAGE_DRIFT")
    exchange=bind_explicit_qualifiers(
        owner,source_exchange,qualifier_attestation,
        expected_qualifier_sha256=expected_qualifier_sha256,
        expected_owner_head=expected_owner_head)
    audit_host_atomic_exchange(owner.source,exchange)
    source_read=bridge_v176_to_v6(
        owner,parent_native_store,scope_id=scope_id,
        inventory_bytes=inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256,
        expected_owner_head=expected_owner_head,new_scope=new_parent_scope)
    baseline=_counts(knowledge_store)
    used_cues=set()
    used_claims=set()
    native_seals=[]

    def assert_head():
        need(owner.progress()["checkpoint_head_sha256"]==expected_owner_head,
             "OWNER_REVIEW_HEAD_CHANGED_IN_FLIGHT")

    def child_callback(segment_id, child_manifest, stage_name, original_raw):
        assert_head()
        need(original_raw==owner.raw,"CHILD_RAW_NOT_PARENT_SOURCE")
        ex=_child_exchange(exchange,child_manifest)
        source=verify_source(
            original_raw,child_manifest,
            expected_source_sha256=progress["source_sha256"],
            expected_manifest_sha256=json_digest(child_manifest))
        audit_host_atomic_exchange(source,ex)
        first,last=source.scope_first_cue,source.scope_last_cue
        cue_ids=set(range(first,last+1))
        claim_ids={a["claim_id"] for a in ex["atoms"]}
        need(not (cue_ids & used_cues or claim_ids & used_claims),
             "CHILD_DUPLICATE_CUES_OR_CLAIMS")
        # Nothing from an already approved V166 case is used to construct
        # the native host exchange or host model/proof receipts.
        supplied=native_child_inputs(segment_id,child_manifest,ex)
        need(type(supplied) is dict and set(supplied)=={
            "native_store","scope_id","inventory_bytes",
            "expected_inventory_sha256","prior_knowledge"} and
            type(supplied["native_store"]) is TransactionStore and
            type(supplied["prior_knowledge"]) is dict,
            "HOST_INPUTS_MISSING_OR_PREAUTHORISED")
        ledger=supplied["native_store"]
        cid=supplied["scope_id"]
        # Fresh child scope must be genuinely newly created or resumed through
        # the separately validated idempotent real-host replay (not in E1).
        creation=ledger.create_scope(
            scope_id=cid,video_id=source.video_id,
            source_sha256=source.source_sha256,
            manifest_sha256=source.manifest_sha256,
            command_id="e1_from_v176_new_scope")
        pinned=ledger.attest_source(
            scope_id=cid,command_id="e1_from_v176_original_source",
            expected_head=creation["event_sha256"],
            raw=original_raw,manifest=child_manifest)
        owner_pin=ledger.attest_owner_inventory(
            scope_id=cid,command_id="e1_from_v176_owner_inventory",
            expected_head=pinned["event_sha256"],
            raw=original_raw,manifest=child_manifest,
            inventory_bytes=supplied["inventory_bytes"],
            expected_inventory_sha256=supplied["expected_inventory_sha256"])
        models,reviews=_native_models(source,ex)
        run_id="v176_e1_"+segment_id.lower()
        batch_args=dict(
            scope_id=cid,run_id=run_id,
            expected_head=owner_pin["event_sha256"],
            raw=original_raw,manifest=child_manifest,
            inventory_bytes=supplied["inventory_bytes"],
            expected_inventory_sha256=supplied["expected_inventory_sha256"],
            exchange=ex,knowledge=supplied["prior_knowledge"],
            window_models=models,window_reviews=reviews)
        host=ledger.submit_host_atomic_batch(**batch_args)
        need(host["atomic_batch_committed"] is True and
             host["semantic_truth_certified"] is False and
             ledger.snapshot(cid)["ledger_head_sha256"]==host["event_sha256"],
             "V176_DERIVED_NATIVE_HOST_PROOF_NOT_COMMITTED")
        native_seals.append(host["event_sha256"])
        assert_head()
        authored=review_native_child(
            segment_id,source,ex,host,ledger,
            supplied["prior_knowledge"])
        assert_head()
        need(type(authored) is dict and set(authored)=={
             "chat_review","official_evidence_bodies",
             "relation_decisions","explicit_hold_revision"},
             "AUTHORED_POST_HOST_CHAT_REVIEW_REQUIRED")
        case={
            "manifest":child_manifest,
            "inventory_bytes":supplied["inventory_bytes"],
            "expected_inventory_sha256":supplied["expected_inventory_sha256"],
            "source":source,
            "exchange":ex,
            "prior_knowledge":supplied["prior_knowledge"],
            "source_store":ledger,
            "host_receipt":host,
            "chat_review":authored["chat_review"],
            "official_evidence_bodies":authored["official_evidence_bodies"]}
        used_cues.update(cue_ids)
        used_claims.update(claim_ids)
        return {"case":case,
                "relation_decisions":authored["relation_decisions"],
                "original_host_batch_replay_args":batch_args,
                "explicit_hold_revision":authored["explicit_hold_revision"]}

    def seam_callback(parent, cases):
        assert_head()
        out=review_seams(parent,cases)
        assert_head()
        return out

    def parent_callback(parent, assembly, seams, packets):
        assert_head()
        out=review_parent(parent,assembly,seams,packets)
        assert_head()
        return out

    assert_head()
    result=run_full_video_with_e3_decisions(
        checkpoint,knowledge_store,
        review_or_load_child=child_callback,
        review_seams=seam_callback,review_parent=parent_callback,
        expected_knowledge_head=expected_knowledge_head)
    assert_head()
    counts=_counts(knowledge_store)
    delta={k:counts[k]-baseline[k] for k in counts}
    published=result["all_video_knowledge_published"] is True
    if published:
        need(used_cues==set(range(1,progress["cue_total"]+1)) and
             used_claims=={a["claim_id"] for a in exchange["atoms"]} and
             delta["knowledge"]>0 and delta["events"]==delta["knowledge"] and
             delta["parent_publications"]==1,
             "INCOMPLETE_OR_NONATOMIC_PARENT_PUBLICATION")
    else:
        need(all(v==0 for v in delta.values()),
             "HELD_PARENT_LEAKED_KNOWLEDGE")
    return {"schema":SCHEMA,
            "source_sha256":progress["source_sha256"],
            "owner_head_sha256":expected_owner_head,
            "qualifier_attestation_sha256":expected_qualifier_sha256,
            "parent_native_source_head_sha256":source_read["native_v6_head_sha256"],
            "native_child_host_receipt_count":len(native_seals),
            "native_child_host_event_sha256s":native_seals,
            "source_cues_checked":len(used_cues),
            "owner_atoms_checked":len(used_claims),
            "source_first_v176_to_host_receipt_verified":True,
            "frozen_v123_to_v126_invoked":True,
            "original_v128_status":result["native_v128_status"],
            "knowledge_sqlite_before":baseline,
            "knowledge_sqlite_delta":delta,
            "structural_synthetic_positive_path_pass":published,
            "formal_financial_fact_approved":False,
            "independent_meaning_quality_certified":False,
            "user_video_13_scopes_published":False,
            "investment_advice_authorized":False}
