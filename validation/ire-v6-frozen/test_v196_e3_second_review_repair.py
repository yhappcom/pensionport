"""V196 synthetic fail-closed tests: never a real financial gold benchmark."""
import copy,os,sqlite3,tempfile,unittest
from pathlib import Path
import test_v195_e3_second_user_turn_audit as v195_fixture
from ire.v6.errors import InvalidInput
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay,ANSWER

class TestV196SecondTurnRepair(unittest.TestCase):
    def setUp(self):
        self.orig=v195_fixture.TestV195ActualSecondTurn('test_01_source_frozen_second_review_status_not_e3_approved')
        self.orig.setUp();self.addCleanup(self.orig.base.doCleanups)
        p=self.orig.packet()
        p['judgments'][0]['e3_disposition']='HOLD_SOURCE_MEANING_REPAIR'
        p['judgments'][0]['source_fidelity_flags']=['CONDITION_LOSS']
        self.orig.audit.submit(p['judgments'])
        self.head=self.orig.audit.status()['review_head_sha256']
        self.db=self.orig.base.d/'v196_repair.sqlite'
        self.repair=E3SecondReviewRepairOverlay(self.orig.audit,self.db,expected_second_head=self.head,create=True)
    def pkg(self,kind='SOURCE_REWRITE_PROPOSED'):
        pkt=self.repair.prepare([1]);q=pkt['targets'][0]
        patch={'serial':1,'first_claim_sha256':q['first_claim_sha256'],
           'prior_second_judgment_sha256':q['prior_second_judgment_sha256'],
           'repair_kind':kind,'source_quote_cue_index':2,
           'source_quote':'CMA is a cash management account.',
           'corrected_proposition':'The speaker describes the account type in the video, without guaranteeing principal.',
           'related_serial':None,
           'rationale':'The source contains a descriptive introduction and no issuer-authorized financial guarantee, so this remains a proposal only.',
           'remaining_evidence_task':'Issuer evidence and account-specific risks must be independently confirmed before financial use.',
           'original_quarantine_retained':True,'first_turn_unchanged':True,
           'second_turn_unchanged':True,'independent_gold':False,'finance_fact_approved':False,
           'e3_approved':False,'e4_approved':False,'e5_published':False}
        ans={'schema':ANSWER,'packet_sha256':pkt['packet_sha256'],
             'review_executor':'CHATGPT_IN_CHAT','independent_gold':False,
             'e3_approved':False,'e4_approved':False,'e5_published':False,
             'amendments':[patch]}
        return pkt,ans
    def test_01_source_rewrite_proposal_keeps_e3_hold(self):
        p,a=self.pkg();s=self.repair.submit(p,a)
        self.assertEqual(s['proposed_corrections'],1)
        self.assertFalse(s['e3_approved'])
        self.assertEqual(s['v195_second_review_head_sha256'],self.head)
    def test_02_restart_exact_stored_sha(self):
        p,a=self.pkg();s=self.repair.submit(p,a)
        z=E3SecondReviewRepairOverlay(self.orig.audit,self.db,expected_second_head=self.head)
        self.assertEqual(s['repair_overlay_head_sha256'],z.status()['repair_overlay_head_sha256'])
    def test_03_wrong_second_head_fails(self):
        with self.assertRaisesRegex(InvalidInput,'SECOND_REVIEW_NOT_FROZEN'):
            E3SecondReviewRepairOverlay(self.orig.audit,self.orig.base.d/'new.sqlite',expected_second_head='0'*64,create=True)
    def test_04_invented_quote_rejected(self):
        p,a=self.pkg();a['amendments'][0]['source_quote']='100% principal guaranteed.'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_QUOTE_FORGED_OR_WRONG_CUE'):
            self.repair.submit(p,a)
    def test_05_quote_wrong_cue_rejected(self):
        p,a=self.pkg();a['amendments'][0]['source_quote_cue_index']=3
        with self.assertRaisesRegex(InvalidInput,'SOURCE_QUOTE_FORGED_OR_WRONG_CUE'):
            self.repair.submit(p,a)
    def test_06_invented_number_rejected(self):
        p,a=self.pkg();a['amendments'][0]['corrected_proposition']+=' a guaranteed return of 9.99%.'
        with self.assertRaisesRegex(InvalidInput,'PROPOSED_NUMERIC_UNIT_NOT_IN_ORIGINAL'):
            self.repair.submit(p,a)
    def test_07_invented_always_rejected(self):
        p,a=self.pkg();a['amendments'][0]['corrected_proposition']+=' 항상.'
        with self.assertRaisesRegex(InvalidInput,'INVENTED_ABSOLUTE_QUALIFIER'):
            self.repair.submit(p,a)
    def test_08_fake_e3_approval_rejected(self):
        p,a=self.pkg();a['amendments'][0]['e3_approved']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL'):
            self.repair.submit(p,a)
    def test_09_duplicate_old_packet_rejected(self):
        p,a=self.pkg();self.repair.submit(p,a)
        with self.assertRaisesRegex(InvalidInput,'TARGET_NOT_HOLD_OR_ALREADY_REPAIRED'):
            self.repair.submit(p,a)
    def test_10_stored_event_modified_rejected(self):
        p,a=self.pkg();self.repair.submit(p,a)
        with sqlite3.connect(self.db) as db:db.execute("UPDATE events SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'EVENT_CHAIN_TAMPER'):
            self.repair.status()
    def test_11_stored_amendment_modified_rejected(self):
        p,a=self.pkg();self.repair.submit(p,a)
        with sqlite3.connect(self.db) as db:db.execute("UPDATE amendments SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'AMENDMENT_RECORD_TAMPER'):
            self.repair.status()
    def test_12_private_permissions_enforced(self):
        os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_DB_PERMISSION_OR_RESET'):
            E3SecondReviewRepairOverlay(self.orig.audit,self.db,expected_second_head=self.head)
    def test_13_wrong_first_claim_hash_rejected(self):
        p,a=self.pkg();a['amendments'][0]['first_claim_sha256']='f'*64
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_CLAIM_OR_VERDICT_FORGED'):
            self.repair.submit(p,a)
    def test_14_wrong_prior_verdict_hash_rejected(self):
        p,a=self.pkg();a['amendments'][0]['prior_second_judgment_sha256']='f'*64
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_CLAIM_OR_VERDICT_FORGED'):
            self.repair.submit(p,a)
    def test_15_nonatomic_delete_needs_nonatomic_old_verdict(self):
        p,a=self.pkg(kind='REMOVE_NONATOMIC_PROPOSED');a['amendments'][0]['corrected_proposition']=None
        with self.assertRaisesRegex(InvalidInput,'REMOVE_REQUIRES_OLD_NONATOM'):
            self.repair.submit(p,a)
    def test_16_forged_packet_self_hash_rejected(self):
        p,a=self.pkg();p['targets'][0]['first_proposition']='CMA always guarantees money.'
        from v196_e3_second_review_repair import _sha
        p['packet_sha256']=_sha({k:v for k,v in p.items() if k!='packet_sha256'})
        a['packet_sha256']=p['packet_sha256']
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_SOURCE_PACKET'):
            self.repair.submit(p,a)
    def test_17_invalid_parent_ref_rejected(self):
        p,a=self.pkg(kind='PARENT_RELATION_REVIEW_REQUIRED')
        a['amendments'][0]['related_serial']=12;a['amendments'][0]['corrected_proposition']=None
        with self.assertRaisesRegex(InvalidInput,'PARENT_RELATION_CANNOT_AUTOMERGE'):
            self.repair.submit(p,a)
    def test_18_missing_remaining_task_rejected(self):
        p,a=self.pkg();a['amendments'][0]['remaining_evidence_task']='none'
        with self.assertRaisesRegex(InvalidInput,'REPAIR_REASON_OR_REMAINING_TASK_MISSING'):
            self.repair.submit(p,a)
    def test_19_missing_original_hold_flag_rejected(self):
        p,a=self.pkg();a['amendments'][0]['original_quarantine_retained']=False
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL_OR_ORIGINAL_STATUS_MUTATION'):
            self.repair.submit(p,a)
    def test_20_second_turn_original_remains_immutable(self):
        old=self.orig.audit.status()['review_head_sha256']
        p,a=self.pkg();self.repair.submit(p,a)
        self.assertEqual(self.orig.audit.status()['review_head_sha256'],old)
        self.assertEqual(self.orig.audit.status()['first_turn_atomic_candidates'],1)
        self.assertEqual(self.repair.status()['original_quarantined_retained'],0)

if __name__=='__main__':unittest.main()