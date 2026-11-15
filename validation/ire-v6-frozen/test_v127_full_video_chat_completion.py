"""V127 synthetic multi-scope parent replay with real V6 host and V123 gate.

These ChatGPT verdicts and official bytes are synthetic; not authentic finance.
"""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import canonical,json_digest,sha256
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.full_video_segments import propose_full_video_segments
from ire.v6.source import verify_source
from ire.v6.tests.test_host_batch import HostBatchTests
from v123_chat_final_gate import SCHEMA
from v127_full_video_chat_completion import assess_full_video_chat_assembly


class V127FullVideoChatReviewAggregationTests(unittest.TestCase):
    def setUp(self):
        p=HostBatchTests("test_one_command_commits_all_models_and_proofs_atomically")
        p.setUp()
        self.addCleanup(p.doCleanups)
        self.parent=p
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw=p.fx.raw
        self.manifest=p.fx.manifest
        self.inventory=p.owner
        self.inventory_sha=p.pin
        self.plan=propose_full_video_segments(self.raw,self.manifest,self.inventory,
                       expected_inventory_sha256=self.inventory_sha,max_cues=2)
        self.cases=[]
        for part in self.plan["segments"]:
            manifest=part["child_manifest"]
            source=verify_source(self.raw,manifest,expected_source_sha256=sha256(self.raw),
                                 expected_manifest_sha256=json_digest(manifest))
            first,last=part["first_cue"],part["last_cue"]
            ex=copy.deepcopy(p.fx.exchange)
            ex["manifest_sha256"]=json_digest(manifest)
            ex["cue_dispositions"]=[x for x in ex["cue_dispositions"] if first<=x["cue_index"]<=last]
            ex["atoms"]=[x for x in ex["atoms"] if first<=x["source_refs"][0]["cue_index"]<=last]
            # Parent fixture includes optional cross-window context [2,3].
            # Resolve it inside the child and enforce boundary review separately.
            for atom in ex["atoms"]:
                atom["context_cue_indices"]=[x for x in atom["context_cue_indices"] if first<=x<=last]
                atom["condition_cue_indices"]=[x for x in atom["condition_cue_indices"] if first<=x<=last]
            original_prior=copy.deepcopy(p.knowledge)
            original_prior["relations"]=[r for r in original_prior["relations"] if r["claim_id"] in {a["claim_id"] for a in ex["atoms"]}]
            inventory=canonical({"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
                "video_id":source.video_id,"source_sha256":source.source_sha256,
                "manifest_sha256":source.manifest_sha256,"cue_census_sha256":source.cue_census_sha256}]})
            pin=sha256(inventory)
            store=TransactionStore(Path(self.tmp.name)/f"child_{first}.db")
            store.create_scope(scope_id=f"subscope_{first}",video_id=source.video_id,
                               source_sha256=source.source_sha256,
                               manifest_sha256=source.manifest_sha256,
                               command_id="create")
            store.attest_source(scope_id=f"subscope_{first}",command_id="attest_source",
                                expected_head=store.snapshot(f"subscope_{first}")["ledger_head_sha256"],
                                raw=self.raw,manifest=manifest)
            store.attest_owner_inventory(scope_id=f"subscope_{first}",command_id="attest_inventory",
                                         expected_head=store.snapshot(f"subscope_{first}")["ledger_head_sha256"],
                                         raw=self.raw,manifest=manifest,inventory_bytes=inventory,
                                         expected_inventory_sha256=pin)
            models,reviews={},{}
            for wid,_,_ in source.primary_windows:
                rows=[]
                for atom in ex["atoms"]:
                    if atom["owner_window_id"] != wid:
                        continue
                    indices=[x["cue_index"] for x in atom["source_refs"]]
                    rows.append({"claim_id":atom["claim_id"],"proposition":atom["proposition"],
                                 "kind":atom["kind"],"owner_window_id":wid,
                                 "source_refs":atom["source_refs"],
                                 "context_first_cue":indices[0],"context_last_cue":indices[-1]})
                models[wid]={"schema":"IRE_V6_ATOMIC_MODEL_V1","claims":rows}
                reviews[wid]={"schema":"IRE_V6_STRUCTURAL_REVIEW_V1",
                              "review_scope":"SOURCE_ANCHORS_ONLY",
                              "reviewed_claim_ids":sorted(x["claim_id"] for x in rows),
                              "independent_gold_verified":False}
            host=store.submit_host_atomic_batch(
                scope_id=f"subscope_{first}",run_id=f"stage_{first}",
                expected_head=store.snapshot(f"subscope_{first}")["ledger_head_sha256"],
                raw=self.raw,manifest=manifest,inventory_bytes=inventory,
                expected_inventory_sha256=pin,exchange=ex,knowledge=original_prior,
                window_models=models,window_reviews=reviews)
            audited=audit_host_atomic_exchange(source,ex)
            body=b"<html>FAKE government original for synthetic negative-control only</html>"
            review={"schema":SCHEMA,"review_executor":"CHATGPT_IN_CHAT","as_of":"2026-11-15",
                    "source_sha256":source.source_sha256,"manifest_sha256":source.manifest_sha256,
                    "host_event_sha256":host["event_sha256"],"host_bundle_sha256":host["bundle_sha256"],
                    "atom_candidate_digest":audited["atom_candidate_digest"],
                    "cue_disposition_digest":audited["cue_disposition_digest"],
                    "blindness":"PRIOR_EXPOSED","source_first_pass_completed":True,
                    "counterexample_pass_completed":True,"disagreements_adjudicated":True,
                    "source_cues":[{"cue_index":idx,
                                    "cue_text_sha256":sha256(source.cues[idx-1].text.encode("utf-8")),
                                    "status":"REVIEWED",
                                    "review_note_sha256":sha256(f"fake cue {idx}".encode())}
                                   for idx in range(first,last+1)],
                    "atom_verdicts":[{"claim_id":atom["claim_id"],"atom_sha256":json_digest(atom),
                                       "status":"ACCEPT_FOR_RESEARCH","speaker_stance_checked":True,
                                       "conditions_exceptions_checked":True,"numeric_period_checked":True,
                                       "counterexample_checked":True,"high_risk":True,"financial_claim":True,
                                       "finance_evidence_status":"PRIMARY_BODY_AND_DATE_CHAT_CHECKED",
                                       "official_body_sha256":sha256(body),"official_effective_as_of":"2026-11-01",
                                       "financial_scope_checked":True,
                                       "private_review_note_sha256":sha256((atom["claim_id"]+" fake review").encode())}
                                      for atom in ex["atoms"]],
                    "unresolved_high_risk_omissions":0,"unresolved_audio_visual":0,
                    "external_independent_certified":False,"personalized_advice_approved":False,
                    "p0_go":False,"review_private_evidence_sha256":sha256(b"not a real goldset")}
            self.cases.append({"manifest":manifest,"inventory_bytes":inventory,
                               "expected_inventory_sha256":pin,"source":source,"exchange":ex,
                               "prior_knowledge":original_prior,"source_store":store,
                               "host_receipt":host,"chat_review":review,
                               "official_evidence_bodies":{a["claim_id"]:body for a in ex["atoms"]}})
        cues=self.parent.fx.source.cues
        self.seams=[{"left_last_cue":2,"right_first_cue":3,
                     "left_text_sha256":sha256(cues[1].text.encode("utf-8")),
                     "right_text_sha256":sha256(cues[2].text.encode("utf-8")),
                     "chat_executor":"CHATGPT_IN_CHAT",
                     "condition_exception_and_rebuttal_checked":True,
                     "cross_segment_atomic_join_resolved":True,
                     "unresolved_semantic_cases":0,
                     "private_review_note_sha256":sha256(b"synthetic chat seam") }]

    def run_audit(self,**kw):
        params=dict(raw=self.raw,parent_manifest=self.manifest,
                    parent_inventory=self.inventory,expected_parent_inventory_sha256=self.inventory_sha,
                    max_cues=2,child_runs=self.cases,seam_reviews=self.seams)
        params.update(kw)
        return assess_full_video_chat_assembly(**params)

    def test_every_parent_cue_and_multiwindow_child_replayed_in_one_call(self):
        r=self.run_audit()
        self.assertEqual(r["total_parent_cues"],4)
        self.assertEqual(r["reviewed_cues"],4)
        self.assertEqual(r["atomic_candidates"],3)
        self.assertEqual(r["cross_scope_seams_reviewed"],1)
        self.assertEqual(r["child_scopes"],2)
        self.assertEqual(r["status"],"ALL_CHILD_CHATS_REVIEWED_STAGING_NOT_PUBLISHED")
        self.assertFalse(r["research_candidates_export_allowed"])
        self.assertFalse(r["whole_video_research_complete"])

    def test_second_child_missing_means_hold_and_zero_export(self):
        r=self.run_audit(child_runs=self.cases[:1])
        self.assertEqual(r["status"],"HOLD_INCOMPLETE_CHILD_SCOPES")
        self.assertFalse(r["research_candidates_export_allowed"])

    def test_second_child_finance_open_holds_parent(self):
        c=copy.copy(self.cases)
        c[1]=copy.deepcopy({k:v for k,v in self.cases[1].items() if k not in ("source_store",)})
        c[1]["source_store"]=self.cases[1]["source_store"]
        c[1]["chat_review"]["atom_verdicts"][0].update(
            status="OPEN",finance_evidence_status="OPEN",
            official_body_sha256=None,official_effective_as_of=None,
            financial_scope_checked=False)
        r=self.run_audit(child_runs=c)
        self.assertEqual(r["status"],"HOLD_CHILD_CHAT_FINAL_NOT_ALL_PASSED")
        self.assertFalse(r["research_candidates_export_allowed"])

    def test_missing_or_forged_boundary_challenge_is_blocked(self):
        with self.assertRaisesRegex(QualityNotProven,"MISSING_CROSS_SEGMENT"):
            self.run_audit(seam_reviews=[])
        reviews=copy.deepcopy(self.seams)
        reviews[0]["cross_segment_atomic_join_resolved"]=False
        with self.assertRaisesRegex(QualityNotProven,"CROSS_SEGMENT_SEMANTIC_SEAM_OPEN"):
            self.run_audit(seam_reviews=reviews)

    def test_child_manifest_substitution_blocked_before_chat(self):
        c=copy.copy(self.cases)
        c[1]=dict(c[1]); c[1]["manifest"]=self.manifest
        with self.assertRaisesRegex(QualityNotProven,"CHILD_MANIFEST_NOT_PARENT_APPROVED_PLAN"):
            self.run_audit(child_runs=c)

    def test_original_srt_tamper_is_blocked(self):
        with self.assertRaises(InvalidInput):
            self.run_audit(raw=self.raw+b" ")

    def test_duplicate_atom_across_children_is_blocked(self):
        c=copy.copy(self.cases)
        c[1]=dict(c[1]); c[1]["exchange"]=copy.deepcopy(c[1]["exchange"])
        c[1]["exchange"]["atoms"][0]["claim_id"]="C00001"
        with self.assertRaisesRegex(QualityNotProven,"CROSS_SCOPE_DUPLICATE_ATOM_ID"):
            self.run_audit(child_runs=c)

    def test_stale_child_store_head_cannot_pass_parent(self):
        c=copy.copy(self.cases)
        c[1]=dict(c[1]); c[1]["host_receipt"]=dict(c[1]["host_receipt"])
        c[1]["host_receipt"]["event_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            self.run_audit(child_runs=c)

if __name__=="__main__":
    unittest.main()