"""Fail-closed tests: classification source provenance cannot upgrade research receipts."""
from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path
from ire.v5.first_five_adjudication_receipt_gate import (
    verify, ResearchReceiptBlocked, A, E, L, R, BATCH, load)

ROOT=Path(__file__).resolve().parents[3]

class FocusedSourceAdjudicationReceiptTests(unittest.TestCase):
    def document(self,path):return load(ROOT,path)
    def expect_failure(self,path,mutate,part):
        d=copy.deepcopy(self.document(path));mutate(d)
        with self.assertRaisesRegex(ResearchReceiptBlocked,part):
            verify(ROOT,replacements={str(path):d})

    def test_13_cases_305_candidates_and_41_rule_scopes_are_not_promotion(self):
        a=verify(ROOT)
        self.assertEqual(a['source_classification_corrections_resolved'],13)
        self.assertEqual(a['source_anchor_propositions_adjudicated'],21)
        self.assertEqual(a['candidate_claims_scope_reviewed'],305)
        self.assertEqual(a['pairwise_topic_edges_reviewed'],359)
        self.assertEqual(a['unsafe_false_direct_links_blocked'],27)
        self.assertEqual(a['rule_claims_remaining_open'],34)
        self.assertEqual(a['formal_new_v5_engine_window_receipts'],0)
        self.assertEqual(a['public_v5_batch_processed_windows'],5)
        self.assertEqual(a['public_v5_batch_remaining_windows'],283)
        self.assertFalse(a['formal_288_window_research_closure_approved'])
        self.assertFalse(a['financial_advice_release_approved'])
        self.assertFalse(a['original_private_source']['private_original_reopened'])

    def test_no_false_assigned_formal_events(self):
        self.expect_failure(A,lambda d:d.__setitem__('formal_engine_events_created_from_this_public_ledger',13),
                            'RECEIPT_FORCED_FORMAL_OR_ADVICE_APPROVAL')

    def test_no_auto_promotion_of_adjudicated_claims(self):
        self.expect_failure(A,lambda d:d['cases'][0].__setitem__('financial_fact_personal_application_approved',True),
                            'RECEIPT_UNEARNED_CLAIM_OR_SOURCE_STATUS')

    def test_original_window_hash_drift_rejected(self):
        self.expect_failure(A,lambda d:d['cases'][0].__setitem__('source_window_sha256','0'*64),
                            'RECEIPT_UNEARNED_CLAIM_OR_SOURCE_STATUS')

    def test_unbound_or_misindexed_proposition_rejected(self):
        self.expect_failure(A,lambda d:d['cases'][0]['propositions'][0].__setitem__('anchor_cue',99999),
                            'RECEIPT_ANCHOR_MISSING_OR_CLAIM_PROMOTED')

    def test_authority_url_cannot_be_nonofficial(self):
        self.expect_failure(L,lambda d:d['authority_records'][0].__setitem__('url','https://not-official.example/safe'),
                            'RECEIPT_BAD_OFFICIAL_SOURCE_STATUS')

    def test_false_direct_source_evidence_cannot_be_reenabled(self):
        def attack(d):
            target=next(e for e in d['pair_edges'] if e['edge_type']=='FALSE_DIRECT_SEMANTIC_LINK_REJECTED')
            target['edge_type']='TOPIC_OVERLAP_ONLY_NO_DIRECT_SUPPORT'
        self.expect_failure(E,attack,'RECEIPT_FALSE_PRIOR_EVIDENCE_REENABLED')

    def test_no_claim_level_identity_certified_by_cluster_topic(self):
        self.expect_failure(E,lambda d:d['candidate_dispositions'][0].__setitem__('atomic_statement_equivalence_certified',True),
                            'RECEIPT_INVALID_CANDIDATE_DISPOSITION')

    def test_no_unreviewed_rule_treated_as_personal_approval(self):
        self.expect_failure(R,lambda d:d['rows'][0].__setitem__('auto_advisory_approval',True),
                            'RECEIPT_RULE_WITHOUT_TRUSTED_SCOPE')

    def test_public_batch_cannot_be_fabricated_from_draft(self):
        self.expect_failure(BATCH,lambda d:d.__setitem__('windows_processed_reported',288),
                            'RECEIPT_PUBLIC_STATUS_CHANGED_WITHOUT_REAL_EVENTS')

    def test_fabricated_private_zip_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'1-70.zip';f.write_bytes(b'fake zip')
            with self.assertRaisesRegex(ResearchReceiptBlocked,
                                        'RECEIPT_PRIVATE_ARCHIVE_SHA_MISMATCH'):
                verify(ROOT,source_zip=f)

if __name__=='__main__':unittest.main()
