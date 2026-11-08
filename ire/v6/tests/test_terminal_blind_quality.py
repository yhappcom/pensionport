"""V6-5/6/7 isolated, synthetic-only cross-stage and adversarial regression.

The gold here is constructed by the test author and is NOT independent human
review. Arithmetic PASS cannot and must not produce ENGINE QUALITY GO.
"""
from __future__ import annotations
import copy
from contextlib import closing
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import (ConcurrentHeadChanged, DomainConflict,
                           IdempotencyConflict, InvalidInput, LedgerCorrupted,
                           QualityNotProven, UnsupportedSchema)
from ire.v6.evaluation import measure_blind
from ire.v6.source import verify_source
from ire.v6.state_machine import reduce_event
from ire.v6.store import TransactionStore
from ire.v6.tests.test_source_and_proof import (VIDEO, make_srt, make_manifest,
                                                 make_model, make_review)
from ire.v6.tests.test_owner_finance_chain import fixture_baseline

SCOPE="audit_scope_A"


def sample_frame():
    return {"modality":"HYPOTHETICAL", "conditions":"hypothetical only",
            "exceptions":"exception exists", "measurements":"none",
            "speaker_attribution":"test narrator", "effective_date":"not law"}


def one_claim_gold(cid="G00001", cue1=2, cue2=3, *, cat="PENSION"):
    src=make_srt()
    from ire.v6.source import parse_srt
    cues=parse_srt(src)
    return {"gold_id":cid,"category":cat,"proposition":"A linked conditional statement",
            "source_refs":[{"cue_index":i,"quote":cues[i-1].text} for i in (cue1,cue2)],
            "frame":sample_frame()}


def build_gold():
    return {"schema":"IRE_V6_BLIND_GOLD_V1","video_id":VIDEO,
            "source_sha256":sha256(make_srt()),"claims":[one_claim_gold()]}


def build_plan(src, manifest, gold=None):
    gold=gold or build_gold()
    return {"schema":"IRE_V6_BLIND_EVAL_PLAN_V1", "video_id":VIDEO,
            "source_sha256":sha256(src),"manifest_sha256":json_digest(manifest),
            "window_ids":[w["window_id"] for w in manifest["windows"]],
            "sampling_protocol":"Two synthetic windows with one nonindependent reference atom",
            "rubric_version":"contract_v6_1", "gold_commitment_sha256":json_digest(gold),
            "reviewer_protocol_sha256":sha256(b"synthetic protocol NOT independent"),
            "precision_min_ppm":800000,"recall_min_ppm":800000,
            "high_risk_recall_min_ppm":800000,
            "gold_sealed_before_predictions":True}


def build_prediction_from_model():
    claim=make_model()["claims"][0]
    return {"schema":"IRE_V6_BLIND_PREDICTIONS_V1", "video_id":VIDEO,
            "source_sha256":sha256(make_srt()), "claims":[{
                "claim_id":claim["claim_id"],"category":"PENSION",
                "proposition":claim["proposition"],"source_refs":claim["source_refs"],
                "frame":sample_frame()}]}


def build_alignment(plan,gold,pred):
    return {"schema":"IRE_V6_BLIND_ALIGNMENT_V1",
            "plan_sha256":json_digest(plan),"gold_sha256":json_digest(gold),
            "predictions_sha256":json_digest(pred),"adjudicator_id":"synthetic_judge",
            "pairs":[{"gold_id":"G00001","predicted_id":"C00001","verdict":"EXACT",
                      "field_verdicts":{k:"CORRECT" for k in sample_frame()}}],
            "all_claims_compared":True}


class TerminalAndBlindEvaluationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db=Path(tmp.name)/"private"/"v6.db"
        self.store=TransactionStore(self.db)
        self.raw=make_srt()
        self.manifest=make_manifest(self.raw)
        src=verify_source(self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
                          expected_manifest_sha256=json_digest(self.manifest))
        self.inventory={"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":VIDEO,"source_sha256":sha256(self.raw),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":src.cue_census_sha256}]}
        self.inv_bytes=canonical(self.inventory)
        self.inv_sha=sha256(self.inv_bytes)
        self.store.create_scope(scope_id=SCOPE,video_id=VIDEO,source_sha256=sha256(self.raw),
                 manifest_sha256=json_digest(self.manifest),command_id="create_scope")
        self.official_bytes=b"Synthetic-only fictional exception condition. Not official law."
        self.proposal={"schema":"IRE_V6_OFFICIAL_CANDIDATE_V1","claim_id":"C00001",
            "issuer":"Synthetic Test Office", "url":"https://example.org/fictional",
            "quote":"fictional exception condition","published_on":"2025-01-05",
            "effective_from":"2025-02-01","effective_until":None,
            "retrieved_on":"2026-01-10","jurisdiction":"TEST_ONLY",
            "scope_note":"fictional", "claim_support_verdict":"UNREVIEWED"}
        self.baseline=fixture_baseline()
        self.relation={"schema":"IRE_V6_PRIOR_RELATION_CANDIDATE_V1","claim_id":"C00001",
            "prior_id":"LEGACY-000","relationship":"OPEN", "rationale":"synthetic",
            "semantic_relation_verified":False}
    def head(self):return self.store.snapshot(SCOPE)["ledger_head_sha256"]
    def attest_pin(self):
        self.store.attest_source(scope_id=SCOPE,command_id="attest_source",
            expected_head=self.head(),raw=self.raw,manifest=self.manifest)
        self.store.attest_owner_inventory(scope_id=SCOPE,command_id="pin_source",
            expected_head=self.head(),raw=self.raw,manifest=self.manifest,
            inventory_bytes=self.inv_bytes,expected_inventory_sha256=self.inv_sha)
    def model(self, *, kind="A", key="record_model_A"):
        m=make_model()
        if kind!="A":m["claims"][0]["proposition"]="Version "+kind+" of interpretation"
        return self.store.submit(scope_id=SCOPE,command_id=key,
            expected_head=self.head(),kind="MODEL_RECORDED",
            payload={"window_id":"W00001","model":m})
    def proof(self,*,key="proof_A"):
        return self.store.submit_structural_proof(scope_id=SCOPE,command_id=key,
            expected_head=self.head(),raw=self.raw,manifest=self.manifest,
            window_id="W00001",review=make_review())
    def finance_inputs(self):
        return {"W00001:C00001":dict(official_document_raw=self.official_bytes,
                official_proposal=self.proposal,expected_official_sha256=sha256(self.official_bytes),
                as_of="2026-02-01",prior_baseline=self.baseline,prior_relation=self.relation,
                expected_baseline_sha256=json_digest(self.baseline))}
    def finance(self):
        args=self.finance_inputs()["W00001:C00001"]
        return self.store.submit_finance_candidate(scope_id=SCOPE,
             command_id="finance_A",expected_head=self.head(),window_id="W00001",
             raw=self.raw,manifest=self.manifest,inventory_bytes=self.inv_bytes,
             expected_inventory_sha256=self.inv_sha,**args)
    def stage(self, finance=False):
        self.attest_pin();self.model();self.proof()
        if finance:self.finance()
    def audit(self, *, key="audit_A", expected=None, finance=None, **overrides):
        args=dict(scope_id=SCOPE,command_id=key,expected_head=expected or self.head(),
             raw=self.raw,manifest=self.manifest,inventory_bytes=self.inv_bytes,
             expected_inventory_sha256=self.inv_sha,
             finance_inputs={} if finance is None else finance)
        args.update(overrides)
        return self.store.issue_terminal_audit_receipt(**args)

    def test_audit_rejects_unattested_source_without_ledger_change(self):
        before=self.store.snapshot(SCOPE)
        with self.assertRaisesRegex(DomainConflict,"OWNER_PIN"):
            self.audit()
        self.assertEqual(before,self.store.snapshot(SCOPE))
    def test_audit_requires_private_finance_replay_inputs(self):
        self.stage(finance=True);before=self.store.snapshot(SCOPE)
        with self.assertRaisesRegex(InvalidInput,"FINANCE_REPLAY_INPUT_MISSING"):
            self.audit()
        self.assertEqual(before,self.store.snapshot(SCOPE))
    def test_future_effective_official_candidate_is_explicit_audit_blocker(self):
        self.proposal["effective_from"]="2027-01-01"
        self.stage(finance=True)
        result=self.audit(finance=self.finance_inputs())
        self.assertIn("OFFICIAL_EVIDENCE_DATE_NOT_APPLICABLE",
                      result["audit_report"]["blockers"])
        self.assertFalse(result["research_complete"])

    def test_audit_source_and_finance_tamper_abort_without_partial_event(self):
        self.stage(finance=True)
        orig=self.store.snapshot(SCOPE)
        altered=self.raw.replace(b"second narrator",b"invented speaker")
        with self.assertRaises(InvalidInput):
            self.audit(raw=altered,finance=self.finance_inputs())
        data=self.finance_inputs();data["W00001:C00001"]["official_document_raw"]=b"tampered"
        with self.assertRaises(InvalidInput):self.audit(finance=data)
        self.assertEqual(orig,self.store.snapshot(SCOPE))
    def test_audit_emits_immutable_blocked_receipt_no_quality_go(self):
        self.stage(finance=True)
        prior=self.head()
        result=self.audit(finance=self.finance_inputs())
        self.assertEqual(result["terminal_outcome"],"TERMINAL_BLOCKED")
        self.assertEqual(result["base_head_sha256"],prior)
        report=result["audit_report"]
        self.assertEqual(report["proofs_replayed"],1)
        self.assertEqual(report["finance_candidates_replayed"],1)
        self.assertTrue(report["source_bytes_replayed_in_this_transaction"])
        self.assertIn("MODEL_WINDOWS_MISSING",report["blockers"])
        self.assertFalse(report["engine_quality_certified"])
        same=TransactionStore(self.db).read_terminal_audit_receipt(scope_id=SCOPE,
              audit_event_sha256=result["event_sha256"])
        self.assertTrue(same["is_latest_event"])
        self.assertEqual(same["report"],report)
        self.assertFalse(same["p0_go"])
        with self.assertRaises(QualityNotProven):self.store.issue_terminal_receipt(SCOPE)
    def test_historical_audit_exact_retry_is_marked_historical(self):
        self.stage();head=self.head()
        old=self.audit(expected=head)
        self.model(kind="B",key="model_B")
        retry=self.audit(expected=head)
        self.assertTrue(retry["idempotent_replay"])
        self.assertTrue(retry["historical"])
        self.assertEqual(retry["audit_report"],old["audit_report"])
        self.assertFalse(retry["p0_go"])

    def test_historical_audit_never_masquerades_as_current(self):
        self.stage()
        audited=self.audit()
        self.model(kind="B",key="model_B")
        result=self.store.read_terminal_audit_receipt(scope_id=SCOPE,
                    audit_event_sha256=audited["event_sha256"])
        self.assertFalse(result["is_latest_event"])
        self.assertEqual(result["outcome"],"TERMINAL_BLOCKED")
        again=self.audit(key="audit_B")
        self.assertEqual(again["audit_report"]["proofs_replayed"],0)
        self.assertIn("STRUCTURAL_PROOFS_MISSING",again["audit_report"]["blockers"])
    def test_audit_commit_failure_does_not_publish_ghost(self):
        self.stage();before=self.store.snapshot(SCOPE)
        for stage in ("after_event_insert","after_head_update"):
            def fault(at):
                if at==stage:raise OSError("injected COMMIT fault")
            self.store._before_commit=fault
            with self.assertRaises(OSError):self.audit()
            self.store._before_commit=lambda at:None
            self.assertEqual(TransactionStore(self.db).snapshot(SCOPE),before)
        self.assertEqual(self.audit()["sequence"],before["sequence"]+1)
    def test_audit_idempotence_and_conflicting_resubmission(self):
        self.stage();head=self.head()
        r=self.audit(expected=head)
        second=self.audit(expected=head)
        self.assertEqual(second["event_sha256"],r["event_sha256"])
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(second["terminal_outcome"],"TERMINAL_BLOCKED")
        self.assertEqual(second["audit_report"],r["audit_report"])
        self.assertFalse(second["historical"])
        with self.assertRaises(IdempotencyConflict):
            self.audit(expected=self.head())
    def test_audit_concurrent_same_head_only_one_commit(self):
        self.stage();head=self.head()
        def attempt(n):
            try:return self.audit(key="audit_concurrent_"+str(n),expected=head)
            except ConcurrentHeadChanged:return "STALE"
        with ThreadPoolExecutor(max_workers=2) as ex:
            results=list(ex.map(attempt,(1,2)))
        self.assertEqual(len([r for r in results if isinstance(r,dict)]),1)
        self.assertEqual(results.count("STALE"),1)
    def test_raw_terminal_approval_event_forbidden(self):
        self.stage()
        before=self.store.snapshot(SCOPE)
        with self.assertRaises(DomainConflict):
            self.store.submit(scope_id=SCOPE,command_id="forge_GO",expected_head=self.head(),
                  kind="TERMINAL_AUDIT_RECORDED",payload={"p0_go":True})
        with self.assertRaises(InvalidInput):
            reduce_event(before["state"],"TERMINAL_AUDIT_RECORDED",
             {"schema":"IRE_V6_TERMINAL_AUDIT_EVENT_V1","base_head_sha256":self.head(),
              "base_state_sha256":before["state_sha256"],
              "report":{"schema":"IRE_V6_TERMINAL_AUDIT_REPORT_V1","outcome":"GO",
                        "research_complete":True,"blockers":[]}},sha256(b"fake"))
        self.assertEqual(self.store.snapshot(SCOPE),before)
    def test_owner_pin_loses_trust_after_synthetic_registry_replacement(self):
        self.stage()
        prior=self.store.snapshot(SCOPE)
        altered=copy.deepcopy(self.inventory)
        altered["entries"][0]["source_sha256"]=sha256(b"fraud")
        with self.assertRaises(InvalidInput):
            self.audit(inventory_bytes=canonical(altered))
        self.assertEqual(self.store.snapshot(SCOPE),prior)
    def test_blind_plan_cannot_be_registered_after_predictions(self):
        self.attest_pin();self.model()
        plan=build_plan(self.raw,self.manifest)
        with self.assertRaisesRegex(DomainConflict,"BEFORE|PREDICTIONS"):
            self.freeze(plan)
    def freeze(self,plan,key="freeze_plan",expected=None):
        return self.store.freeze_blind_plan(scope_id=SCOPE,command_id=key,
            expected_head=expected or self.head(),raw=self.raw,manifest=self.manifest,
            inventory_bytes=self.inv_bytes,expected_inventory_sha256=self.inv_sha,plan=plan)
    def test_blind_plan_is_persisted_precommitment_and_replayed(self):
        self.attest_pin()
        plan=build_plan(self.raw,self.manifest)
        first=self.freeze(plan)
        # Duplicate command with different expected head must never rewrite.
        with self.assertRaises((IdempotencyConflict, DomainConflict)):
            self.freeze(plan)
        self.assertFalse(first["idempotent_replay"])
        self.assertEqual(self.store.snapshot(SCOPE)["state"]["blind_plan"]["plan_sha256"],json_digest(plan))
    def test_blind_gold_precommitted_digest_rejects_postprediction_substitution(self):
        self.attest_pin()
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        self.freeze(plan)
        self.model()
        pred=build_prediction_from_model()
        alt=copy.deepcopy(gold);alt["claims"][0]["proposition"]="Changed after viewing output"
        alignment=build_alignment(plan,gold,pred)
        with self.assertRaisesRegex(InvalidInput,"SUBSTITUTION"):
            measure_blind(self.raw,self.manifest,plan,alt,pred,alignment)
    def test_blind_metrics_are_conditional_not_independent_approval(self):
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        m=measure_blind(self.raw,self.manifest,plan,gold,pred,align)
        self.assertEqual(m["counts"],{"tp":1,"fp":0,"fn":0,"predictions":1,"gold":1})
        self.assertEqual(m["recall"]["denominator"],1)
        self.assertTrue(m["pre_registered_thresholds_met_arithmetically"])
        self.assertFalse(m["actual_reviewer_identity_verified"])
        self.assertFalse(m["semantic_accuracy_certified"])
        self.assertFalse(m["p0_go"])
    def test_blind_exact_requires_field_and_category_agreement(self):
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        wrong=copy.deepcopy(align);wrong["pairs"][0]["field_verdicts"]["exceptions"]="INCORRECT"
        with self.assertRaisesRegex(InvalidInput,"FALSE_EXACT"):
            measure_blind(self.raw,self.manifest,plan,gold,pred,wrong)
        wrong=copy.deepcopy(pred);wrong["claims"][0]["category"]="TAX"
        align2=build_alignment(plan,gold,wrong)
        with self.assertRaisesRegex(InvalidInput,"FALSE_EXACT"):
            measure_blind(self.raw,self.manifest,plan,gold,wrong,align2)
    def test_blind_partial_is_fp_and_fn_not_tp(self):
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        align["pairs"][0]["verdict"]="PARTIAL"
        m=measure_blind(self.raw,self.manifest,plan,gold,pred,align)
        self.assertEqual((m["counts"]["tp"],m["counts"]["fp"],m["counts"]["fn"]),(0,1,1))
        self.assertEqual(m["recall"]["parts_per_million"],0)
        self.assertFalse(m["pre_registered_thresholds_met_arithmetically"])
    def test_blind_alignment_duplicate_and_untraceable_gold_rejected(self):
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        bad=copy.deepcopy(gold);bad["claims"][0]["source_refs"][0]["quote"]="fabricated investor statement"
        bplan=build_plan(self.raw,self.manifest,bad)
        with self.assertRaises(InvalidInput):measure_blind(self.raw,self.manifest,bplan,bad,pred,build_alignment(bplan,bad,pred))
        align["pairs"].append(copy.deepcopy(align["pairs"][0]))
        with self.assertRaises(InvalidInput):measure_blind(self.raw,self.manifest,plan,gold,pred,align)
    def test_record_blind_measurement_refuses_missing_window_and_model_drift(self):
        self.attest_pin()
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        self.freeze(plan);self.model();self.proof()
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        with self.assertRaisesRegex(DomainConflict,"MISSING_MODEL_WINDOW"):
            self.record(gold,pred,align)
        changed=copy.deepcopy(pred);changed["claims"][0]["proposition"]="invented after prediction"
        with self.assertRaisesRegex(DomainConflict,"MISSING_MODEL_WINDOW"):
            self.record(gold,changed,align)
    def record(self,gold,pred,align,**extra):
        args=dict(scope_id=SCOPE,command_id="blind_measurement",expected_head=self.head(),
             raw=self.raw,manifest=self.manifest,inventory_bytes=self.inv_bytes,
             expected_inventory_sha256=self.inv_sha,gold=gold,predictions=pred,alignment=align)
        args.update(extra)
        return self.store.record_blind_measurement(**args)
    def test_blind_plan_and_prediction_revision_sequence_persisted_as_observation_only(self):
        # This test uses a one-window synthetic plan so all model predictions are recorded.
        self.manifest=make_manifest(self.raw,scope_first=1,scope_last=4,cut=4)
        # Scope was already declared with the original manifest. Re-create a properly pinned scope.
        # Separate temp DB ensures no silent manifest rebind is possible.
        another=TransactionStore(self.db.parent/"other.db")
        another.create_scope(scope_id=SCOPE,video_id=VIDEO,source_sha256=sha256(self.raw),
            manifest_sha256=json_digest(self.manifest),command_id="create_other_scope")
        self.store=another
        self.inv_sha=None
        src=verify_source(self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
                          expected_manifest_sha256=json_digest(self.manifest))
        self.inventory["entries"][0].update(manifest_sha256=json_digest(self.manifest),
                                                cue_census_sha256=src.cue_census_sha256)
        self.inv_bytes=canonical(self.inventory);self.inv_sha=sha256(self.inv_bytes)
        self.attest_pin()
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        self.freeze(plan)
        self.model();self.proof()
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        result=self.record(gold,pred,align)
        snap=self.store.snapshot(SCOPE)
        self.assertTrue(snap["progress"]["blind_measurement_recorded"])
        self.assertFalse(snap["progress"]["independent_semantic_recall_measured"])
        self.assertFalse(snap["progress"]["engine_quality_certified"])
        self.assertEqual(result["sequence"],7)
        audited=self.audit()
        self.assertTrue(audited["audit_report"]["blind_measurement_current"])
        self.assertFalse(audited["audit_report"]["independent_gold_review_verified"])
        old=self.store.snapshot(SCOPE)["state"]["blind_measurement"]["revision_set_sha256"]
        self.model(kind="B",key="new_revision")
        newer=self.audit(key="after_correction")
        self.assertFalse(newer["audit_report"]["blind_measurement_current"])
        self.assertNotEqual(old,newer["audit_report"]["revision_set_sha256"])
    def test_legacy_v3_database_requires_migration(self):
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("PRAGMA user_version = 3")
        with self.assertRaisesRegex(UnsupportedSchema,"MIGRATION"):
            TransactionStore(self.db)

    # V6-7 integrated acceptance on actual SQLite files, synthetic input.
    def _one_window(self):
        manifest=make_manifest(self.raw,scope_first=1,scope_last=4,cut=4)
        store=TransactionStore(self.db.parent/"integration_v6.db")
        store.create_scope(scope_id=SCOPE,video_id=VIDEO,source_sha256=sha256(self.raw),
             manifest_sha256=json_digest(manifest),command_id="one_window_scope")
        src=verify_source(self.raw,manifest,expected_source_sha256=sha256(self.raw),
                          expected_manifest_sha256=json_digest(manifest))
        self.inventory["entries"][0].update(manifest_sha256=json_digest(manifest),
                                             cue_census_sha256=src.cue_census_sha256)
        self.inv_bytes=canonical(self.inventory);self.inv_sha=sha256(self.inv_bytes)
        self.store=store;self.manifest=manifest

    def test_private_gold_replay_recomputes_stored_arithmetic(self):
        self._one_window();self.attest_pin()
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        self.freeze(plan);self.model();self.proof()
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        self.record(gold,pred,align)
        replay=TransactionStore(self.store.path).snapshot_with_blind_measurement(
            scope_id=SCOPE,raw=self.raw,manifest=self.manifest,
            inventory_bytes=self.inv_bytes,expected_inventory_sha256=self.inv_sha)
        self.assertTrue(replay["arithmetic_replayed_this_call"])
        self.assertEqual(replay["counts"],{"tp":1,"fp":0,"fn":0,"predictions":1,"gold":1})
        self.assertFalse(replay["actual_reviewer_identity_verified"])
        altered=self.raw.replace(b"second narrator",b"invented source text")
        with self.assertRaises(InvalidInput):
            self.store.snapshot_with_blind_measurement(scope_id=SCOPE,raw=altered,
                 manifest=self.manifest,inventory_bytes=self.inv_bytes,
                 expected_inventory_sha256=self.inv_sha)
        self.model(kind="B",key="revision_B")
        with self.assertRaisesRegex(DomainConflict,"MODEL_REVISED"):
            self.store.snapshot_with_blind_measurement(scope_id=SCOPE,raw=self.raw,
                 manifest=self.manifest,inventory_bytes=self.inv_bytes,
                 expected_inventory_sha256=self.inv_sha)
    def test_full_synthetic_one_turn_source_gold_proof_finance_terminal_blocked(self):
        self._one_window();self.attest_pin()
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        self.freeze(plan);self.model();self.proof();self.finance()
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        recorded=self.record(gold,pred,align)
        self.assertEqual(recorded["sequence"],8)
        report=self.audit(finance=self.finance_inputs())
        self.assertEqual(report["audit_report"]["scope_windows"],1)
        self.assertEqual(report["audit_report"]["proofs_replayed"],1)
        self.assertEqual(report["audit_report"]["finance_candidates_replayed"],1)
        self.assertTrue(report["audit_report"]["blind_measurement_current"])
        self.assertEqual(report["audit_report"]["blockers"],sorted([
            "OWNER_IDENTITY_NOT_INDEPENDENTLY_VERIFIED",
            "FINANCIAL_ENTAILMENT_NOT_VERIFIED",
            "GOLD_REVIEWER_INDEPENDENCE_NOT_VERIFIED"]))
        assert not report["p0_go"]
        reloaded=TransactionStore(self.store.path)
        last=reloaded.read_terminal_audit_receipt(scope_id=SCOPE,
                    audit_event_sha256=report["event_sha256"])
        self.assertTrue(last["is_latest_event"])
        self.assertFalse(last["research_complete"])
        with self.assertRaises(QualityNotProven):reloaded.issue_terminal_receipt(SCOPE)
    def test_wrong_gold_or_predicted_frame_cannot_be_smuggled_into_record(self):
        self._one_window();self.attest_pin()
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        self.freeze(plan);self.model();self.proof()
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        base=self.store.snapshot(SCOPE)
        altered=copy.deepcopy(pred);altered["claims"][0]["proposition"]="changed afterward"
        with self.assertRaises(DomainConflict):self.record(gold,altered,align)
        changed=copy.deepcopy(gold);changed["claims"][0]["proposition"]="changed afterward"
        with self.assertRaises(InvalidInput):self.record(changed,pred,align)
        self.assertEqual(self.store.snapshot(SCOPE),base)
    def test_blind_score_unverified_even_if_all_synthetic_exact(self):
        gold=build_gold();plan=build_plan(self.raw,self.manifest,gold)
        pred=build_prediction_from_model();align=build_alignment(plan,gold,pred)
        result=measure_blind(self.raw,self.manifest,plan,gold,pred,align)
        self.assertEqual(result["precision_wilson_95"]["upper_ppm"],1000000)
        self.assertLess(result["recall_wilson_95"]["lower_ppm"],1000000)
        self.assertFalse(result["actual_blindness_independently_verified"])
        self.assertFalse(result["engine_quality_certified"])
    def test_bogus_blind_plan_type_fails_without_python_typeerror(self):
        self.attest_pin()
        plan=build_plan(self.raw,self.manifest)
        for field,bad in (("precision_min_ppm","0.9"),("window_ids","W00001"),
                          ("gold_commitment_sha256",["x"]),("rubric_version",["evil"])):
            evil=copy.deepcopy(plan);evil[field]=bad
            with self.subTest(field=field),self.assertRaises(InvalidInput):self.freeze(evil)
    def test_audit_submitted_with_changed_private_input_rejected_as_idempotency_conflict(self):
        self.stage(finance=True);at=self.head()
        first=self.audit(expected=at,finance=self.finance_inputs())
        changed=self.finance_inputs();changed["W00001:C00001"]["official_document_raw"]+=b"!"
        with self.assertRaises(IdempotencyConflict):
            self.audit(expected=at,finance=changed)
        self.assertEqual(self.store.snapshot(SCOPE)["ledger_head_sha256"],first["event_sha256"])
    def test_audit_power_loss_after_head_change_rolls_back(self):
        self.stage();prior=self.store.snapshot(SCOPE)
        # Local-only synthetic input loaded from deterministic tests in child.
        script="""
import os,sys
from ire.v6.store import TransactionStore
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from ire.v6.codec import canonical,sha256,json_digest
from ire.v6.source import verify_source
s=TransactionStore(sys.argv[1]);raw=make_srt();m=make_manifest(raw)
v=verify_source(raw,m,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(m))
i={'schema':'IRE_V6_OWNER_INVENTORY_V1','entries':[{'video_id':v.video_id,
'source_sha256':v.source_sha256,'manifest_sha256':v.manifest_sha256,
'cue_census_sha256':v.cue_census_sha256}]};b=canonical(i)
s._before_commit=lambda stage:os._exit(83) if stage=='after_head_update' else None
s.issue_terminal_audit_receipt(scope_id='audit_scope_A',command_id='power_loss',
expected_head=sys.argv[2],raw=raw,manifest=m,inventory_bytes=b,
expected_inventory_sha256=sha256(b),finance_inputs={})
"""
        result=subprocess.run([sys.executable,"-c",script,str(self.db),prior["ledger_head_sha256"]],
                    cwd=Path(__file__).resolve().parents[3],capture_output=True,timeout=15)
        self.assertEqual(result.returncode,83,result.stderr.decode("utf-8","replace"))
        self.assertEqual(TransactionStore(self.db).snapshot(SCOPE),prior)
        self.assertEqual(self.audit()["sequence"],prior["sequence"]+1)


if __name__=="__main__":unittest.main()
