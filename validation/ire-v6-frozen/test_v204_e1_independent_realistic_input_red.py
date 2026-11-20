"""V204 independent E1 input-shape adversarial checks.

These cases were absent from V203's positive 4-cue/2-child sample.
The expected behavior is explicit fail-closed without discarding any
source reference, or legitimate no-atom structural accommodation.
"""
from __future__ import annotations

import copy
import unittest

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


if __name__=="__main__":
    unittest.main()
