"""Synthetic tranche custody regression; no financial truth claims."""
import unittest,copy
from ire.v6.tests.test_semantic_obligation_review import ObligationReviewTests
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.cumulative_review import append_review

class CumulativeReviewTests(unittest.TestCase):
    def setUp(self):
        self.f=ObligationReviewTests();self.f.setUp()
        self.prior=self.f.rows[:1];self.added=self.f.rows[1:]
        self.receipt=self.f.run_review(self.prior)
    def run_append(self,prior=None,added=None,receipt=None,pin=None):
        f=self.f
        return append_review(f.src,f.g,f.old,f.c,self.prior if prior is None else prior,
            self.added if added is None else added,self.receipt if receipt is None else receipt,
            expected_prior_receipt_sha256=json_digest(self.receipt) if pin is None else pin,**f.pins)
    def test_combined_replay_and_no_release(self):
        a=self.run_append();self.assertEqual(a,self.run_append())
        self.assertEqual(a['cumulative'],self.f.run_review(self.f.rows))
        self.assertFalse(a['publication_authorized'])
    def test_duplicate_old_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'OLD_ID'):
            self.run_append(added=self.added+self.prior)
    def test_modified_prior_rejected(self):
        p=copy.deepcopy(self.prior);p[0]['reason']='Changed original reason.'
        with self.assertRaisesRegex(InvalidInput,'PRIOR_REPLAY_DRIFT'):
            self.run_append(prior=p)
    def test_removed_prior_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'PRIOR_REPLAY_DRIFT'):
            self.run_append(prior=[])
    def test_wrong_pin_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'PRIOR_RECEIPT_PIN'):
            self.run_append(pin='f'*64)
