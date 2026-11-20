"""V204 independent E1 input-shape adversarial checks.

These cases were absent from V203's positive 4-cue/2-child sample.
The expected behavior is explicit fail-closed without discarding any
source reference, or legitimate no-atom structural accommodation.
"""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.codec import canonical

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.proof import audit_model_anchors
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_manifest
from v203_e1_v176_origin_native_host_bridge import _native_models,_child_exchange
import test_v203_e1_v176_origin_native_host_bridge as earlier


class IndependentE1AuditV204(unittest.TestCase):
    def setUp(self):
        self.fx=earlier.TestV203ActualNativeHostOrigin(
            "test_01_v176_is_actual_native_host_origin_for_both_children")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)

    def test_01_nonresearch_only_window_must_be_auditable_without_fake_claim(self):
        owner=self.fx.fx.owner
        raw=owner.raw
        # Four existing cues, re-windowed to 1 cue each: the fourth is
        # non-research (no atoms). This is a valid documentary input.
        manifest=make_manifest(raw,cut=1)
        source=verify_source(raw,manifest,
                             expected_source_sha256=sha256(raw),
                             expected_manifest_sha256=json_digest(manifest))
        exchange,_=owner.compile_native_v6_stage()
        exchange=copy.deepcopy(exchange)
        exchange["manifest_sha256"]=source.manifest_sha256
        for atom in exchange["atoms"]:
            atom["owner_window_id"]=source.owner(
                atom["source_refs"][0]["cue_index"])
        models,reviews=_native_models(source,exchange)
        self.assertEqual(models["W00004"]["claims"],[])
        audit=audit_model_anchors(
            source,"W00004",models["W00004"],reviews["W00004"])
        self.assertEqual(audit["claim_count"],0)
        self.assertFalse(audit["financial_facts_approved"])

    def test_02_cross_child_numeric_context_must_not_be_erased(self):
        owner=self.fx.fx.owner
        parent,_=owner.compile_native_v6_stage()
        parent=copy.deepcopy(parent)
        atom=next(a for a in parent["atoms"] if a["claim_id"]=="C00003")
        self.assertIn("8%",owner.source.cues[1].text)
        atom["context_cue_indices"]=sorted(set(
            atom["context_cue_indices"]+[2]))
        atom["numeric_references"].append({"cue_index":2,"token":"8%"})
        child=self.fx.fx.fx.fx.checkpoint.child_manifests[1]
        with self.assertRaisesRegex(InvalidInput,
                                    "CROSS_CHILD_CONTEXT_OR_NUMBER_LOST"):
            _child_exchange(parent,child)


    def _prepare_legitimate_empty_window_host(self, with_unresolved=False):
        owner=self.fx.fx.owner
        raw=owner.raw
        manifest=make_manifest(raw,scope_first=3,scope_last=4,
                               start_window=2,cut=1,mode="PARTIAL")
        source=verify_source(raw,manifest,
                             expected_source_sha256=sha256(raw),
                             expected_manifest_sha256=json_digest(manifest))
        parent,_=owner.compile_native_v6_stage()
        child=_child_exchange(parent,manifest)
        # The cue-4 window genuinely has no research proposition.
        self.assertEqual([a["claim_id"] for a in child["atoms"]],["C00003"])
        if with_unresolved:
            last=child["cue_dispositions"][-1]
            self.assertEqual(last["cue_index"],4)
            last["disposition"]="UNRESOLVED"
            last["note"]="원문은 채팅에서 아직 검토하지 못함"
        models,reviews=_native_models(source,child)
        self.assertEqual(models["W00003"]["claims"],[])
        prior=copy.deepcopy(
            self.fx.fx.fx.fx.packets[1]["case"]["prior_knowledge"])
        inventory={"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":source.video_id,
            "source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,
            "cue_census_sha256":source.cue_census_sha256}]}
        inv=canonical(inventory)
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        ledger=TransactionStore(Path(temp.name)/"native_empty.db")
        created=ledger.create_scope(
            scope_id="e1_v204_nonresearch_win",video_id=source.video_id,
            source_sha256=source.source_sha256,
            manifest_sha256=source.manifest_sha256,
            command_id="genesis")
        attested=ledger.attest_source(
            scope_id="e1_v204_nonresearch_win",
            command_id="source",expected_head=created["event_sha256"],
            raw=raw,manifest=manifest)
        own=ledger.attest_owner_inventory(
            scope_id="e1_v204_nonresearch_win",
            command_id="owner",expected_head=attested["event_sha256"],
            raw=raw,manifest=manifest,inventory_bytes=inv,
            expected_inventory_sha256=sha256(inv))
        return ledger,dict(
            scope_id="e1_v204_nonresearch_win",run_id="e1_v204_real",
            expected_head=own["event_sha256"],
            raw=raw,manifest=manifest,
            inventory_bytes=inv,expected_inventory_sha256=sha256(inv),
            exchange=child,knowledge=prior,window_models=models,
            window_reviews=reviews)

    def test_03_real_native_host_accepts_only_explicit_nonresearch_window(self):
        ledger,kwargs=self._prepare_legitimate_empty_window_host()
        receipt=ledger.submit_host_atomic_batch(**kwargs)
        self.assertTrue(receipt["atomic_batch_committed"])
        self.assertEqual(receipt["source_and_proof_model_windows"],2)
        snap=ledger.snapshot(kwargs["scope_id"])
        self.assertEqual(snap["ledger_head_sha256"],receipt["event_sha256"])
        self.assertFalse(receipt["semantic_truth_certified"])

    def test_04_unreviewed_window_never_sneaks_through_empty_model(self):
        ledger,kwargs=self._prepare_legitimate_empty_window_host(
            with_unresolved=True)
        with self.assertRaisesRegex(Exception,
                                    "UNRESOLVED_SOURCE_RESIDUALS|EMPTY_WINDOW_NOT_EXPLICITLY_NO_ATOM"):
            ledger.submit_host_atomic_batch(**kwargs)
        snap=ledger.snapshot(kwargs["scope_id"])
        self.assertEqual(snap["progress"]["model_windows_recorded"],0)


if __name__=="__main__":
    unittest.main()
