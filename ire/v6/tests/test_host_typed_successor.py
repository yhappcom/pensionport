"""Additive typed custody is not semantic entailment or a release path."""
import copy
import unittest
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.host_quarantine_preflight import (
    audit_typed_staging_successor, audit_host_quarantine_preflight)
from ire.v6.semantic_authoring_protocol import compile_authoring
from ire.v6.tests.test_host_typed_premise_staging import fixture


class TypedSuccessorTests(unittest.TestCase):
    def setUp(self):
        self.source, exchange, ledger = fixture()
        self.old = {'exchange': exchange, 'ledger': ledger}
        self.head = 'a' * 64

    def check(self, new):
        return audit_typed_staging_successor(self.source, self.old, new, self.head)

    def rehash(self, new):
        e, l = new['exchange'], new['ledger']
        _, l['authoring_receipt'] = compile_authoring(self.source, l['authored'])
        l['exchange_sha256'] = json_digest(e)
        l['projection_rows'][0]['typed_sha256'] = json_digest(l['authored']['atoms'][0])
        l['projection_rows'][0]['native_sha256'] = json_digest(e['atoms'][0])
        audit_host_quarantine_preflight(self.source, e, l)

    def test_carry_keeps_exact_edge(self):
        r = self.check(copy.deepcopy(self.old))
        self.assertEqual(r['retained_typed_relations'], 1)
        self.assertEqual(r['predecessor_event_sha256'], self.head)
        self.assertFalse(r['formal_v123_input_authorized'])
        self.assertFalse(r['p0_go'])

    def test_joint_rehash_and_reclassify_cannot_delete_prior_edge(self):
        new = copy.deepcopy(self.old)
        e, l = new['exchange'], new['ledger']
        l['authored']['atoms'][0]['node']['context'] = [[1, 0, len(self.source.cues[0].text)]]
        l['authored']['atoms'][0]['relations'] = []
        n = e['atoms'][0]; n['condition_cue_indices'] = []; n['stance'] = 'UNRESOLVED'
        l['support_rows'] = []
        l['quarantine_cues'] = [dict(cue_index=1, cue_sha256=sha256(self.source.cues[0].text.encode()), reason='Conservative withheld premise.')]
        l['quarantine_atoms'] = [dict(claim_id='C00001', native_sha256=json_digest(n), reason='Conservative withheld claim.')]
        self.rehash(new)
        with self.assertRaisesRegex(InvalidInput, 'CONDITION_OR_EXCEPTION_LOSS'):
            self.check(new)

    def test_quarantine_cannot_be_released_even_if_new_record_valid(self):
        new = copy.deepcopy(self.old)
        l = self.old['ledger']
        l['support_rows'] = []
        l['quarantine_cues'] = [dict(cue_index=1, cue_sha256=sha256(self.source.cues[0].text.encode()), reason='Prior withheld premise.')]
        l['quarantine_atoms'] = [dict(claim_id='C00001', native_sha256=json_digest(self.old['exchange']['atoms'][0]), reason='Prior withheld claim.')]
        with self.assertRaisesRegex(InvalidInput, 'QUARANTINE_LOSS'):
            self.check(new)

    def test_rewritten_edge_reason_is_not_exact_carry(self):
        new = copy.deepcopy(self.old)
        new['ledger']['authored']['atoms'][0]['relations'][0]['reason'] = 'New reason after review.'
        self.rehash(new)
        with self.assertRaisesRegex(InvalidInput, 'CONDITION_OR_EXCEPTION_LOSS'):
            self.check(new)

    def test_bad_predecessor_pin_rejected(self):
        with self.assertRaises(InvalidInput):
            audit_typed_staging_successor(self.source, self.old, self.old, 'not-a-hash')
