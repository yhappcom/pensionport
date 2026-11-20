"""E1: independently stress V176-origin host batch→V123→V128 positive path.

All original speech, securities rules, legal bodies and ChatGPT verdicts are
SYNTHETIC. The test directly checks native GitHub code and private SQLite,
not real owner video, semantic truth or E3/E4/E5 acceptance.
"""
from __future__ import annotations

import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import ZERO_SHA, json_digest, sha256
from ire.v6.errors import InvalidInput
from v146_source_meaning_provenance import SCHEMA as V146_SCHEMA
from v166_shared_source_only_native_contract import compile_attested_source_only_quarantine
from v203_e1_v176_origin_native_host_bridge import (
    QUAL_SCHEMA,run_origin_native_e1)
from test_v126_chat_approved_knowledge_store import explicit_relation_decisions
import test_v202_e1_v176_native_positive_path as v202_fixture


class TestV203ActualNativeHostOrigin(unittest.TestCase):
    def setUp(self):
        self.fx=v202_fixture.TestV202SameInputE1Route(
            "test_01_preseeded_native_v166_cannot_impersonate_v176_verdict")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.native_children={}
        self.issued_host_events=[]
        source_ex,stage=self.fx.owner.compile_native_v6_stage()
        self.assertEqual(len(source_ex["atoms"]),3)
        target=next(a for a in source_ex["atoms"] if a["claim_id"]=="C00003")
        self.qualifiers={
            "schema":QUAL_SCHEMA,
            "review_executor":"CHATGPT_IN_CHAT",
            "owner_source_sha256":self.fx.owner.source.source_sha256,
            "owner_manifest_sha256":self.fx.owner.source.manifest_sha256,
            "owner_head_sha256":self.fx.owner.progress()["checkpoint_head_sha256"],
            "financial_truth_certified":False,
            "entries":[{
                "claim_id":"C00003",
                "field":"conditions",
                "term_ordinal":0,
                "verbatim_term":"소득에 따라",
                "cue_index":3,
                "cue_text_sha256":sha256(
                    self.fx.owner.source.cues[2].text.encode("utf-8")),
                "original_atom_sha256":json_digest(target),
                "chat_source_context_checked":True,
                "review_note_sha256":sha256(
                    b"SYNTHETIC E1 reviewer source term cue 3"),
            }]
        }
        self.qualifier_pin=json_digest(self.qualifiers)
        self.cb_calls=[]

    def child_inputs(self,segment_id,manifest,exchange):
        index=self.fx.fx.fx.checkpoint.child_ids.index(segment_id)
        prior=self.fx.fx.fx.packets[index]["case"]
        self.assertEqual(prior["manifest"],manifest)
        # Fresh path, not the already-host-committed V166 source_store.
        ledger=TransactionStore(self.root/("actual_"+segment_id+".db"))
        self.native_children[segment_id]=ledger
        return {
            "native_store":ledger,
            "scope_id":"actual_scope_"+segment_id.lower(),
            "inventory_bytes":prior["inventory_bytes"],
            "expected_inventory_sha256":prior["expected_inventory_sha256"],
            "prior_knowledge":copy.deepcopy(prior["prior_knowledge"]),
        }

    def native_review(self,segment_id,source,exchange,host,ledger,prior):
        """Synthetic chat callback AUTHORING review AFTER real V6 commit."""
        self.assertEqual(ledger.snapshot(host["scope_id"])["ledger_head_sha256"],
                         host["event_sha256"])
        self.assertTrue(host["atomic_batch_committed"])
        self.cb_calls.append(segment_id)
        index=self.fx.fx.fx.checkpoint.child_ids.index(segment_id)
        base=self.fx.fx.review if index==0 else (
            self.fx.fx.fx.packets[index]["case"]["chat_review"])
        row=copy.deepcopy(base)
        audit=audit_host_atomic_exchange(source,exchange)
        row.update(
            host_event_sha256=host["event_sha256"],
            host_bundle_sha256=host["bundle_sha256"],
            atom_candidate_digest=audit["atom_candidate_digest"],
            cue_disposition_digest=audit["cue_disposition_digest"])
        by_id={a["claim_id"]:a for a in exchange["atoms"]}
        for verdict in row["atom_verdicts"]:
            verdict["atom_sha256"]=json_digest(by_id[verdict["claim_id"]])
        # Explicit source-only ChatGPT attestation quarantines the hypothetical
        # at cue 2; the native V176 atom remains UNKNOWN/UNRESOLVED.
        if segment_id=="B0001":
            typed=copy.deepcopy(self.fx.fx.typed)
            typed["atom_sha256"]=json_digest(by_id["C00002"])
            typed["source_sha256"]=source.source_sha256
            transformed=compile_attested_source_only_quarantine(
                source,exchange,row,[typed],
                final_chat_quarantine_note=(
                    "ChatGPT 합성 검토: 원문에서 8%일 수 있다는 조건부 가설을 "
                    "source-only 발언으로 격리하고 금융 사실 승인이나 "
                    "개인 투자자문 지식으로는 사용하지 않습니다."))
            self.assertFalse(transformed["release_authorized_by_compiler"])
            row=transformed["compiled_chat_review"]

        # V146 is a separately authored, source-bound synthetic ChatGPT
        # meaning ledger. E1 does not generate this ledger itself.
        accepted={v["claim_id"] for v in row["atom_verdicts"]
                  if v["status"]=="ACCEPT_FOR_RESEARCH"}
        prov=[]
        for atom in exchange["atoms"]:
            if atom["claim_id"] not in accepted:
                continue
            indices=atom["context_cue_indices"]
            prov.append({
                "claim_id":atom["claim_id"],
                "atom_sha256":json_digest(atom),
                "source_cue_indices":indices,
                "source_context_sha256":json_digest([
                    {"cue_index":j,
                     "original_cue_text_sha256":
                         sha256(source.cues[j-1].text.encode("utf-8"))}
                    for j in indices]),
                "resolved_speaker_role":"UNATTRIBUTED_VIDEO_SPEAKER",
                "resolved_speech_act":"ASSERTION",
                "speaker_identity_not_inferred":True,
                "source_condition_exception_checked":True,
                "private_review_note_sha256":sha256(
                    ("SYNTHETIC E1 source meaning "+atom["claim_id"]).encode()),
            })
        if prov:
            row["source_meaning_provenance"]={
                "schema":V146_SCHEMA,
                "source_sha256":source.source_sha256,
                "manifest_sha256":source.manifest_sha256,
                "review_executor":"CHATGPT_IN_CHAT",
                "atom_rows":prov,
                "private_chat_source_meaning_sha256":sha256(
                    b"SYNTHETIC E1 CHAT meaning attestations only"),
            }
        self.issued_host_events.append(host["event_sha256"])
        official=self.fx.fx.fx.packets[index]["case"]["official_evidence_bodies"]
        return {
            "chat_review":row,
            "official_evidence_bodies":official,
            # ChatGPT fixture explicitly signs relation decisions for the
            # ACTUAL owner-origin atoms, not pre-seeded V166 atom hashes.
            "relation_decisions":explicit_relation_decisions(exchange,prior),
            "explicit_hold_revision":False,
        }

    def args(self, **updates):
        p=self.fx
        native=p.fx.fx
        args={
            "owner":p.owner,
            "parent_native_store":p.native,
            "checkpoint":native.checkpoint,
            "knowledge_store":native.knowledge,
            "scope_id":"e1_v203_true_origin",
            "inventory_bytes":native.p.inventory,
            "expected_inventory_sha256":native.p.inventory_sha,
            "expected_owner_head":p.owner.progress()["checkpoint_head_sha256"],
            "qualifier_attestation":self.qualifiers,
            "expected_qualifier_sha256":self.qualifier_pin,
            "native_child_inputs":self.child_inputs,
            "review_native_child":self.native_review,
            "review_seams":native.seams,
            "review_parent":native.parent_review,
            "expected_knowledge_head":ZERO_SHA,
            "new_parent_scope":True,
        }
        args.update(updates)
        return args

    def _knowledge_counts(self):
        with sqlite3.connect(self.fx.fx.fx.knowledge.path) as con:
            names={x[0] for x in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            return {n:con.execute("SELECT COUNT(*) FROM "+n).fetchone()[0]
                    if n in names else 0 for n in
                    ("events","knowledge","parent_publications")}

    def test_01_v176_is_actual_native_host_origin_for_both_children(self):
        result=run_origin_native_e1(**self.args())
        self.assertTrue(result["structural_synthetic_positive_path_pass"])
        self.assertTrue(result["source_first_v176_to_host_receipt_verified"])
        self.assertEqual(result["source_cues_checked"],4)
        self.assertEqual(result["owner_atoms_checked"],3)
        self.assertEqual(result["native_child_host_receipt_count"],2)
        self.assertEqual(self.cb_calls,["B0001","B0002"])
        self.assertEqual(result["knowledge_sqlite_delta"],
                         {"events":2,"knowledge":2,"parent_publications":1})
        self.assertEqual(result["original_v128_status"],
                         "WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY")
        for i,seg in enumerate(("B0001","B0002")):
            l=self.native_children[seg]
            scope="actual_scope_"+seg.lower()
            self.assertEqual(l.snapshot(scope)["ledger_head_sha256"],
                             result["native_child_host_event_sha256s"][i])
        self.assertFalse(result["formal_financial_fact_approved"])

    def test_02_unpinned_qualifier_map_rejected_before_native_write(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_DOCUMENT_PIN_OR_SOURCE_DRIFT"):
            run_origin_native_e1(**self.args(
                expected_qualifier_sha256="f"*64))
        self.assertEqual(self._knowledge_counts(),
                         {"events":0,"knowledge":0,"parent_publications":0})

    def test_03_missing_explicit_condition_anchor_cannot_publish(self):
        unpinned=copy.deepcopy(self.qualifiers)
        unpinned["entries"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_CENSUS_INCOMPLETE"):
            run_origin_native_e1(**self.args(
                qualifier_attestation=unpinned,
                expected_qualifier_sha256=json_digest(unpinned)))
        self.assertEqual(self._knowledge_counts(),
                         {"events":0,"knowledge":0,"parent_publications":0})

    def test_04_child_host_receipt_created_after_owner_review_not_v166(self):
        run_origin_native_e1(**self.args())
        old=self.fx.fx.fx.packets[0]["case"]["host_receipt"]["event_sha256"]
        self.assertNotEqual(old,self.issued_host_events[0])

    def test_05_finance_primary_body_removed_holds_parent_without_knowledge(self):
        old=self.native_review
        def missing(segment_id,source,exchange,host,ledger,prior):
            result=old(segment_id,source,exchange,host,ledger,prior)
            if segment_id=="B0002":
                result["official_evidence_bodies"]={}
            return result
        run=run_origin_native_e1(**self.args(review_native_child=missing))
        self.assertFalse(run["structural_synthetic_positive_path_pass"])
        self.assertEqual(run["knowledge_sqlite_delta"],
                         {"events":0,"knowledge":0,"parent_publications":0})

    def test_06_source_head_or_attestation_mutation_rejected(self):
        wrong=copy.deepcopy(self.qualifiers)
        wrong["owner_head_sha256"]="f"*64
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_DOCUMENT_PIN_OR_SOURCE_DRIFT"):
            run_origin_native_e1(**self.args(
                qualifier_attestation=wrong,
                expected_qualifier_sha256=json_digest(wrong)))

    def test_07_reopened_native_child_database_preserves_real_host_events(self):
        run=run_origin_native_e1(**self.args())
        for i,segment in enumerate(("B0001","B0002")):
            reopened=TransactionStore(self.root/("actual_"+segment+".db"))
            self.assertEqual(reopened.snapshot(
                "actual_scope_"+segment.lower())["ledger_head_sha256"],
                run["native_child_host_event_sha256s"][i])



    def test_08_same_owner_replay_publishes_no_duplicate_knowledge(self):
        first=run_origin_native_e1(**self.args())
        baseline=self._knowledge_counts()
        second=run_origin_native_e1(**self.args(new_parent_scope=False))
        self.assertTrue(first["structural_synthetic_positive_path_pass"])
        self.assertTrue(second["structural_synthetic_positive_path_pass"])
        self.assertTrue(second["parent_publication_idempotent"])
        self.assertEqual(second["knowledge_sqlite_delta"],
                         {"events":0,"knowledge":0,"parent_publications":0})
        self.assertEqual(self._knowledge_counts(),baseline)
        self.assertEqual(first["native_child_host_event_sha256s"],
                         second["native_child_host_event_sha256s"])

    def test_09_cross_child_source_qualifier_cannot_be_silently_discarded(self):
        from v203_e1_v176_origin_native_host_bridge import _child_exchange
        parent,_=self.fx.owner.compile_native_v6_stage()
        for atom in parent["atoms"]:
            if atom["claim_id"]=="C00003":
                atom["condition_cue_indices"]=[2]
                atom["context_cue_indices"]=[2,3]
        with self.assertRaisesRegex(InvalidInput,
                                    "CROSS_CHILD_QUALIFIER_NEEDS_EXPLICIT_SEAM"):
            _child_exchange(parent,self.fx.fx.fx.checkpoint.child_manifests[1])

    def test_10_owner_event_during_post_host_chat_review_blocks_release(self):
        did=[False]
        original=self.native_review

        def updated_owner_during_native_review(segment_id,source,exchange,host,ledger,prior):
            if not did[0]:
                task=self.fx.owner.prepare_evidence_request("W00001")
                self.assertIsNotNone(task)
                rows=[{
                    "cue_index":r["cue_index"],"claim_index":r["claim_index"],
                    "claim_sha256":r["claim_sha256"],
                    "evidence_state":"NOT_FOUND_KEEP_OPEN",
                    "official_source_url":None,
                    "source_excerpt":None,"effective_as_of":None,
                    "context_and_counterexamples":
                        "SYNTHETIC: source-first finance context remains unresolved without an actual primary issuer source.",
                    "original_body_sha256":None,
                    "final_financial_truth_certified":False,
                } for r in task["claim_evidence_tasks"]]
                from v176_chat_engine_loop import EVIDENCE
                self.fx.owner.submit_evidence_proposals(task,{
                    "schema":EVIDENCE,
                    "review_executor":"CHATGPT_IN_CHAT",
                    "challenge_sha256":task["challenge_sha256"],
                    "responses":rows})
                did[0]=True
            return original(segment_id,source,exchange,host,ledger,prior)

        with self.assertRaisesRegex(InvalidInput,
                                    "OWNER_REVIEW_HEAD_CHANGED_IN_FLIGHT"):
            run_origin_native_e1(**self.args(
                review_native_child=updated_owner_during_native_review))
        self.assertTrue(did[0])
        self.assertEqual(self._knowledge_counts(),
                         {"events":0,"knowledge":0,"parent_publications":0})

    def test_11_runtime_exception_after_native_host_is_safe_to_retry(self):
        """A temporary host error may interrupt between child 2 and parent.

        On retry the original V176 owner and committed V6 child host hashes
        must be reused exactly, without partial or duplicate V126 knowledge.
        """
        original_callback=self.native_review
        fault_once=[True]

        def interrupted_chat_host(segment_id,source,exchange,host,ledger,prior):
            if segment_id=="B0002" and fault_once[0]:
                fault_once[0]=False
                raise RuntimeError("SYNTHETIC_TRANSIENT_CHAT_HOST_INTERRUPT")
            return original_callback(segment_id,source,exchange,host,ledger,prior)

        with self.assertRaisesRegex(RuntimeError,
                                    "SYNTHETIC_TRANSIENT_CHAT_HOST_INTERRUPT"):
            run_origin_native_e1(**self.args(
                review_native_child=interrupted_chat_host))
        self.assertEqual(self._knowledge_counts(),
                         {"events":0,"knowledge":0,"parent_publications":0})
        # Both native child host batches have committed, but no research
        # knowledge has been released. Restarting is idempotent.
        before={
            segment:TransactionStore(
                self.root/("actual_"+segment+".db")).snapshot(
                "actual_scope_"+segment.lower())["ledger_head_sha256"]
            for segment in ("B0001","B0002")}
        result=run_origin_native_e1(**self.args(
            review_native_child=original_callback,new_parent_scope=False))
        self.assertTrue(result["structural_synthetic_positive_path_pass"])
        self.assertEqual(result["knowledge_sqlite_delta"],
                         {"events":2,"knowledge":2,"parent_publications":1})
        self.assertEqual(before,dict(zip(
            ("B0001","B0002"),
            result["native_child_host_event_sha256s"])))
        second=run_origin_native_e1(**self.args(
            review_native_child=original_callback,new_parent_scope=False))
        self.assertTrue(second["parent_publication_idempotent"])
        self.assertEqual(second["knowledge_sqlite_delta"],
                         {"events":0,"knowledge":0,"parent_publications":0})

if __name__=="__main__":
    unittest.main()
