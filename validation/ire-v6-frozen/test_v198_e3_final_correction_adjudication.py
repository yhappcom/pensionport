"""Synthetic adversarial regression ONLY. Real CMA source never committed."""
import copy, json, os, sqlite3, tempfile, unittest
from pathlib import Path
import test_v197_e3_repaired_source_projection as fixture
from ire.v6.errors import InvalidInput
from v198_e3_final_correction_adjudication import (E3CorrectionAdjudication,VERDICT,
    build_effective_unapproved_view,build_84_evidence_triage)
from v196_e3_second_review_repair import _sha

class TestV198SecondReviewCorrection(unittest.TestCase):
    def setUp(self):
        self.old=fixture.TestV197RepairedView('test_01_realistic_full_120_census_and_84_risk_holds')
        self.old.setUp();self.addCleanup(self.old.doCleanups)
        self.review=self.old.review;self.repair=self.old.repair
        for s,a in self.old.amends.items():
            a['source_quote_cue_index']=s
            a['source_quote']=self.review.cues[s]
            a['rationale']='The original source must be evaluated with its entire parent discourse, not merely count the atoms.'
            a['remaining_evidence_task']='Confirm product risk, original spoken scope, and separate official source before any approval.'
        self.db=Path(self.old.tmp.name)/'v198.sqlite'
        self.adj=E3CorrectionAdjudication(self.review,self.repair,self.db,
               expected_repair_head=fixture.REPAIR,risk_register=self.old.risk,create=True)
    def row(self,s,decision=None):
        a=self.old.amends[s]
        if decision is None:
            decision={'SOURCE_REWRITE_PROPOSED':'ACCEPT_SOURCE_FORM_ONLY',
               'PRESERVE_QUARANTINE_SOURCE_REPHRASE':'ACCEPT_SOURCE_FORM_ONLY',
               'PARENT_RELATION_REVIEW_REQUIRED':'HOLD_PARENT_EQUIVALENCE',
               'REMOVE_NONATOMIC_PROPOSED':'ACCEPT_NONATOMIC_EXCLUSION_FROM_PROVISIONAL_VIEW'}[a['repair_kind']]
        return {'schema':VERDICT,'serial':s,'first_claim_sha256':_sha(self.review.atoms[s-1]),
          'second_judgment_sha256':_sha(self.review.judgments[s]),'proposal_sha256':_sha(a),
          'source_quote_cue_index':s,'source_quote':self.review.cues[s],
          'decision':decision,'accepted_source_form_only':decision=='ACCEPT_SOURCE_FORM_ONLY',
          'review_rationale':'Reviewed the full original speech and only accept source-attributed text, not investment truth.',
          'next_evidence_task':'Issuer terms and applicable dates remain unverified pending a separate source search.',
          'old_quarantine_retained':True,'first_research_unchanged':True,
          'second_review_unchanged':True,'repair_proposal_unchanged':True,
          'financial_fact_approved':False,'independent_gold':False,
          'e3_approved':False,'e4_approved':False,'e5_published':False}
    def full(self):
        ss=sorted(self.old.amends)
        self.adj.submit(self.adj.packet(ss),[self.row(s) for s in ss])
    def test_01_full_16_source_only_adjudications(self):
        self.full();st=self.adj.status()
        self.assertEqual(st['reviewed'],16);self.assertEqual(st['unreviewed'],0)
        self.assertFalse(st['e3_approved']);self.assertEqual(st['quarantined_preserved'],28)
    def test_02_initially_unreviewed_and_no_gold(self):
        st=self.adj.status();self.assertEqual(st['reviewed'],0)
        self.assertIsNone(st['financial_gold_precision'])
    def test_03_read_model_preserves_all_84_and_28(self):
        self.full();x=build_effective_unapproved_view(self.adj)
        self.assertEqual((len(x['records']),x['all_original_high_risk_blocked'],x['old_quarantines_preserved']),
                         (120,84,28))
        self.assertEqual(x['effective_provisional_candidates_unapproved'],118)
    def test_04_no_finance_use_even_when_source_form_accepted(self):
        self.full();x=build_effective_unapproved_view(self.adj)
        self.assertFalse(any(a['safe_for_financial_answers'] for a in x['records']))
        self.assertFalse(any(a['financial_truth_approved'] for a in x['records']))
    def test_05_prior_source_quote_forgery(self):
        p=self.adj.packet([29]);v=self.row(29);v['source_quote']='Principal guaranteed for all CMA!'
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_QUOTE_OR_HASH_MISMATCH'):
            self.adj.submit(p,[v])
    def test_06_wrong_original_claim_sha(self):
        p=self.adj.packet([29]);v=self.row(29);v['first_claim_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_QUOTE_OR_HASH_MISMATCH'):
            self.adj.submit(p,[v])
    def test_07_second_verdict_changed(self):
        p=self.adj.packet([29]);v=self.row(29);v['second_judgment_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_QUOTE_OR_HASH_MISMATCH'):
            self.adj.submit(p,[v])
    def test_08_proposal_sha_tampered(self):
        p=self.adj.packet([29]);v=self.row(29);v['proposal_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_QUOTE_OR_HASH_MISMATCH'):
            self.adj.submit(p,[v])
    def test_09_forged_packet_self_hash_not_enough(self):
        p=self.adj.packet([29]);v=self.row(29)
        p['items'][0]['original_claim']='Invented guarantee.'
        from v196_e3_second_review_repair import _sha
        p['packet_sha256']=_sha({k:v for k,v in p.items() if k!='packet_sha256'})
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_SOURCE_PACKET'):
            self.adj.submit(p,[v])
    def test_10_duplicate_packet_rejected(self):
        p=self.adj.packet([29]);v=self.row(29);self.adj.submit(p,[v])
        with self.assertRaisesRegex(InvalidInput,'ALREADY_ADJUDICATED'):
            self.adj.submit(p,[v])
    def test_11_cannot_accept_parent_relation_as_source_rewrite(self):
        p=self.adj.packet([2]);v=self.row(2,'ACCEPT_SOURCE_FORM_ONLY');v['accepted_source_form_only']=True
        with self.assertRaisesRegex(InvalidInput,'DECISION_FOR_REPAIR_KIND_INVALID'):
            self.adj.submit(p,[v])
    def test_12_nonatomic_cannot_drop_high_risk(self):
        p=self.adj.packet([51]);v=self.row(51)
        self.review.atoms[50]['high_risk']=True
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS_OR_TAMPER|STALE_OR_TAMPERED_FROZEN_SOURCE|NONATOMIC_EXCLUSION|HIGH_RISK_HAS_NO_BLOCKING_VERDICT'):
            self.adj.submit(p,[v])
    def test_13_forged_approval_rejected(self):
        p=self.adj.packet([29]);v=self.row(29);v['e3_approved']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
            self.adj.submit(p,[v])
    def test_14_forged_independent_gold_rejected(self):
        p=self.adj.packet([29]);v=self.row(29);v['independent_gold']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
            self.adj.submit(p,[v])
    def test_15_replay_same_sha_and_counts(self):
        self.full();a=self.adj.status()
        b=E3CorrectionAdjudication(self.review,self.repair,self.db,
             expected_repair_head=fixture.REPAIR,risk_register=self.old.risk).status()
        self.assertEqual(a,b)
    def test_16_event_row_tamper(self):
        self.full()
        with sqlite3.connect(self.db) as con:con.execute("UPDATE events SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'EVENT_HASH_CHAIN_TAMPER'):
            self.adj.status()
    def test_17_verdict_row_tamper(self):
        self.full()
        with sqlite3.connect(self.db) as con:con.execute("UPDATE verdicts SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'VERDICT_TABLE_HASH_TAMPER'):
            self.adj.status()
    def test_18_permissions_restricted(self):
        os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'EXISTING_DB_PRIVATE_REQUIRED'):
            E3CorrectionAdjudication(self.review,self.repair,self.db,
             expected_repair_head=fixture.REPAIR,risk_register=self.old.risk)
    def test_19_separate_evidence_backlog_84(self):
        self.full();x=build_84_evidence_triage(self.adj)
        self.assertEqual(x['original_risk_total'],84)
        self.assertEqual(x['quarantines_retained'],28)
        self.assertTrue(all(not i['claim_correctness_verified'] for i in x['risk_cases']))
    def test_20_forged_risk_census_rejected(self):
        self.old.risk['risk_records'].pop()
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS_OR_TAMPER|COMPLETE_16_AND_84'):
            self.adj.status()
    def test_21_original_frozen_review_unchanged_after_adjudication(self):
        old=self.review.status()['review_head_sha256']
        self.full();self.assertEqual(self.review.status()['review_head_sha256'],old)
    def test_22_cannot_build_final_projection_without_16(self):
        p=self.adj.packet([29]);self.adj.submit(p,[self.row(29)])
        with self.assertRaisesRegex(InvalidInput,'ALL_16_DECISIONS_REQUIRED'):
            build_effective_unapproved_view(self.adj)
    def test_23_invalid_decision_for_kind(self):
        p=self.adj.packet([51]);v=self.row(51,'ACCEPT_SOURCE_FORM_ONLY');v['accepted_source_form_only']=True
        with self.assertRaisesRegex(InvalidInput,'DECISION_FOR_REPAIR_KIND_INVALID'):
            self.adj.submit(p,[v])

if __name__=='__main__':unittest.main()