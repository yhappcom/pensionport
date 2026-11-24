"""Unified legacy review ledger contracts, not accuracy certification."""
import copy
import unittest
from ire.v6.errors import InvalidInput
from ire.v6.obligation_ledger import genesis, append, replay
from ire.v6.tests import test_shared_qualifier_review as fixtures


class ObligationLedgerTests(unittest.TestCase):
    def setUp(self):
        f = fixtures.SharedQualifierTests()
        f.setUp()
        self.f = f
        self.args = (f.s, f.packet, f.old, f.c)
        self.h0 = genesis(f.s, **f.pins)
        self.events, self.head = append(*self.args, [], 'SINGLE', f.prior,
                                        expected_head=self.h0, **f.pins)

    def shared(self):
        return append(*self.args, self.events, 'SHARED', self.f.rows,
                      expected_head=self.head, **self.f.pins)

    def test_shared_amendment_preserves_history_and_census(self):
        events, head = self.shared()
        self.assertEqual(events[0], self.events[0])
        result = replay(*self.args, events, expected_head=head, **self.f.pins)
        self.assertEqual(result['reviewed'], 1)
        self.assertEqual(result['effective_counts'], {'MULTI_TARGET': 1})
        self.assertFalse(result['ready_for_e3'])
        self.assertFalse(result['actual_two_turn_verified'])
        self.assertFalse(result['publication_authorized'])

    def test_cannot_drop_shared_amendment(self):
        events, head = self.shared()
        with self.assertRaisesRegex(InvalidInput, 'LEDGER_EXTERNAL_HEAD'):
            replay(*self.args, events[:1], expected_head=head, **self.f.pins)

    def test_cannot_rewrite_prior(self):
        events, head = self.shared()
        events[0]['rows'][0]['reason'] = 'Different original reason.'
        with self.assertRaisesRegex(InvalidInput, 'LEDGER_RECEIPT'):
            replay(*self.args, events, expected_head=head, **self.f.pins)

    def test_duplicate_shared_rejected(self):
        events, head = self.shared()
        with self.assertRaisesRegex(InvalidInput, 'LEDGER_SHARED_ALREADY_REVIEWED'):
            append(*self.args, events, 'SHARED', self.f.rows, expected_head=head, **self.f.pins)

    def test_duplicate_single_rejected_after_amendment(self):
        events, head = self.shared()
        with self.assertRaisesRegex(InvalidInput, 'LEDGER_ALREADY_REVIEWED'):
            append(*self.args, events, 'SINGLE', self.f.prior, expected_head=head, **self.f.pins)

    def test_wrong_previous_head_rejected(self):
        events, head = self.shared()
        wrong = copy.deepcopy(events)
        wrong[1]['previous'] = 'f'*64
        with self.assertRaisesRegex(InvalidInput, 'LEDGER_CHAIN'):
            replay(*self.args, wrong, expected_head=head, **self.f.pins)
