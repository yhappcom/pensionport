"""Synthetic V195 source-pinned actual second-user-command E3 audit security checks.

These tests prove source/receipt and append-only integrity, never real finance accuracy
or authentic trusted ChatGPT platform message IDs. No owner-private CMA content here.
"""
import copy,hashlib,json,os,sqlite3,tempfile,unittest
from pathlib import Path
import test_v194_e3_turn1_freeze as fixture
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v195_e3_second_user_turn_audit import (
 E3ActualSecondUserAudit,verify_full_private_response,SCHEMA,_hash)

SECOND='user:observed_distinct_synthetic_validation_command_unverified'
SECOND_SHA=sha256('검증해 주세요'.encode())

class TestV195ActualSecondTurn(unittest.TestCase):
    def setUp(self):
        self.base=fixture.TestActualFirstUserCommandFreeze('test_01_real_native_pinned_synthetic')
        self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.receipt=self.base.frozen()
        self.db=self.base.d/'v195_second.sqlite'
        self.audit=self.make()
    def make(self,**kwargs):
        return E3ActualSecondUserAudit(
          frozen_archive=self.base.z,
          external_receipt=kwargs.get('receipt',self.receipt),
          private_db=kwargs.get('db',self.db),
          second_user_ref=kwargs.get('user_ref',SECOND),
          second_user_message_sha256=kwargs.get('msg_sha',SECOND_SHA),
          create=kwargs.get('create',not self.db.exists()))
    def packet(self):
        atom=self.base.study['claims'][0]
        return {
          'schema':SCHEMA,'phase':'CHATGPT_FINAL_SEMANTIC_VERIFICATION',
          'video_id':self.base.study['video_id'],
          'source_sha256':self.receipt['source_sha256'],
          'frozen_first_turn_owner_head_sha256':self.receipt['owner_head_sha256'],
          'frozen_first_turn_research_sha256':self.receipt['manifest_sha256'] if False else _hash(self.base.study),
          'first_turn_archive_sha256':self.receipt['archive_sha256'],
          'first_user_message_text_sha256':self.receipt['first_turn_text_sha256'],
          'second_user_message_text_sha256':SECOND_SHA,
          'manual_first_user_ref':self.receipt['untrusted_manual_first_user_ref'],
          'manual_second_user_ref':SECOND,
          'platform_user_turn_id_verification':'NOT_AVAILABLE_SELF_REPORTED_OBSERVATION',
          'original_cues_read':4,'first_claims_reviewed':1,'parent_units_inspected':1,
          'first_turn_issues_preserved':[{'cue_index':3,'first_turn_task':self.base.study['unresolved_cue_issues'][0]['task'],
                                         'turn2_status':'STILL_OPEN_NOT_AUTO_CLEARED','evidence_required':True}],
          'additional_turn2_source_tasks':[{'cue_index':2,'kind':'PRODUCT_SCOPE',
              'task':'The product needs an issuer-authored risk statement before any advisory use.'}],
          'judgments':[{'claim_serial':1,'cue_index':2,'parent_id':'P001',
             'first_turn_quote_sha256':sha256(atom['quote'].encode()),
             'first_turn_proposition_sha256':sha256(atom['proposition'].encode()),
             'first_turn_kind':atom['kind'],'first_turn_high_risk_flag':False,
             'review_uses_exact_original_cue_quote':True,
             'source_fidelity_flags':['SPOKEN_POSITION_RETAINED_PENDING_EVIDENCE'],
             'financial_problem':'SOURCE_QUOTE_ONLY_NOT_FACT_CERTIFIED',
             'source_specific_rationale':'The real source statement is present but an issuer-authorized financial truth review has not occurred.',
             'official_public_text_refs':[],'e3_disposition':'HOLD_SOURCE_SPOKEN_FINANCIAL_TRUTH_UNCERTIFIED',
             'independent_gold':False,'finance_fact_approved':False,
             'v123_approved':False,'e4_approved':False,'e5_published':False}],
          'official_primary_public_text':{'kofia_cma':{'issuer':'KOFIA',
             'url':'https://law.kofia.or.kr/example','verification':'PUBLIC_WEB_TEXT_READ_NO_ISSUER_RAW_SHA_OR_EFFECTIVE_DATE_CUSTODY'}},
          'nonclaim_cue_review':{'original_cues_covered':4,'completeness_independently_proven':False},
          'official_issuer_raw_bytes_sha256_verified':False,
          'financial_fact_accuracy_certified':False,
          'precision':None,'recall':None,'high_risk_miss_rate':None,
          'e3_approved':False,'v123_approved':False,'e4_approved':False,'e5_published':False,
          'decision':'E3_HOLD_WITH_HIGH_RISK_QUARANTINE_AND_SOURCE_REPAIR'}
    def test_01_source_frozen_second_review_status_not_e3_approved(self):
        q=self.packet();self.assertEqual(verify_full_private_response(q,self.audit)['validated_reviews'],1)
        s=self.audit.submit(q['judgments']);self.assertEqual(s['second_turn_claims_reviewed'],1)
        self.assertFalse(s['e3_accuracy_certified']);self.assertFalse(s['host_message_identity_verified'])
        self.assertEqual(s['manual_phase_receipt']['recorded_distinct_user_commands'],2)
        self.assertFalse(s['manual_phase_receipt']['two_user_turns_proven'])
    def test_02_second_turn_new_process_resume_and_owner_head_unchanged(self):
        q=self.packet();a=self.audit.submit(q['judgments']);b=self.make(create=False).status()
        self.assertEqual(a['review_head_sha256'],b['review_head_sha256'])
        self.assertEqual(b['first_turn_frozen_owner_head_sha256'],self.receipt['owner_head_sha256'])
    def test_03_same_user_ref_fails_even_with_two_sqlite(self):
        with self.assertRaisesRegex(InvalidInput,'SAME_USER_MESSAGE_REUSED'):
            self.make(db=self.base.d/'different.sqlite',
                      user_ref=self.receipt['untrusted_manual_first_user_ref'],create=True)
    def test_04_forged_quote_hash_is_rejected(self):
        q=self.packet();q['judgments'][0]['first_turn_quote_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ANCHOR_FORGED'):
            self.audit.submit(q['judgments'])
    def test_05_forged_proposition_hash_is_rejected(self):
        q=self.packet();q['judgments'][0]['first_turn_proposition_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ANCHOR_FORGED'):
            self.audit.submit(q['judgments'])
    def test_06_wrong_parent_anchor_rejected(self):
        q=self.packet();q['judgments'][0]['parent_id']='P999'
        with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ANCHOR_FORGED'):
            self.audit.submit(q['judgments'])
    def test_07_forged_e3_certification_rejected(self):
        q=self.packet();q['judgments'][0]['e4_approved']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL_IN_TURN2'):
            self.audit.submit(q['judgments'])
    def test_08_independent_gold_forgery_rejected(self):
        q=self.packet();q['judgments'][0]['independent_gold']=True
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_APPROVAL_IN_TURN2'):
            self.audit.submit(q['judgments'])
    def test_09_fake_official_raw_bytes_certification_rejected(self):
        q=self.packet();q['official_issuer_raw_bytes_sha256_verified']=True
        with self.assertRaisesRegex(InvalidInput,'E3_FINANCIAL_APPROVAL_FALSE_CLAIM'):
            verify_full_private_response(q,self.audit)
    def test_10_precision_recall_forgery_rejected(self):
        q=self.packet();q['precision']=0.99
        with self.assertRaisesRegex(InvalidInput,'E3_FINANCIAL_APPROVAL_FALSE_CLAIM'):
            verify_full_private_response(q,self.audit)
    def test_11_lost_first_open_task_rejected(self):
        q=self.packet();q['first_turn_issues_preserved']=[]
        with self.assertRaisesRegex(InvalidInput,'OPEN_FIRST_TURN_ISSUE_SILENTLY_ERASED'):
            verify_full_private_response(q,self.audit)
    def test_12_no_new_source_tasks_rejected(self):
        q=self.packet();q['additional_turn2_source_tasks']=[]
        with self.assertRaisesRegex(InvalidInput,'SECOND_TURN_SOURCE_REPAIR_TASKS_MISSING'):
            verify_full_private_response(q,self.audit)
    def test_13_unverified_issuer_ref_claiming_raw_cert_rejected(self):
        q=self.packet();q['official_primary_public_text']['kofia_cma']['verification']='FINANCE_APPROVED'
        with self.assertRaisesRegex(InvalidInput,'ISSUER_WEB_TEXT_FALSE_CUSTODY'):
            verify_full_private_response(q,self.audit)
    def test_14_duplicate_second_review_rejected(self):
        q=self.packet();self.audit.submit(q['judgments'])
        with self.assertRaisesRegex(InvalidInput,'STALE_DUPLICATE_OR_SKIPPED_REVIEWS'):
            self.audit.submit(q['judgments'])
    def test_15_audit_event_chain_tamper_detected(self):
        q=self.packet();self.audit.submit(q['judgments'])
        with sqlite3.connect(self.db) as con:con.execute("UPDATE events SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'EVENT_HASH_CHAIN_TAMPER'):
            self.audit.status()
    def test_16_stored_judgment_tamper_detected(self):
        q=self.packet();self.audit.submit(q['judgments'])
        with sqlite3.connect(self.db) as con:con.execute("UPDATE judgments SET payload='{}'")
        with self.assertRaisesRegex(InvalidInput,'JUDGMENT_RECORD_TAMPER'):
            self.audit.status()
    def test_17_private_permissions_enforced_on_resume(self):
        q=self.packet();self.audit.submit(q['judgments']);os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_DB_PERMISSIONS_OR_NO_OVERWRITE'):
            self.make(create=False)
    def test_18_changed_original_archive_hash_rejected(self):
        x=copy.deepcopy(self.receipt);x['archive_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'ARCHIVE_HASH_MISMATCH'):
            self.make(db=self.base.d/'fresh.sqlite',create=True,receipt=x)
    def test_19_gap_in_source_census_rejected(self):
        q=self.packet();q['original_cues_read']=3
        with self.assertRaisesRegex(InvalidInput,'NO_REAL_FULL_REVIEW_CENSUS'):
            verify_full_private_response(q,self.audit)
    def test_20_same_second_ref_different_message_sha_not_platform_proof(self):
        q=self.packet();self.audit.submit(q['judgments']);s=self.audit.status()
        self.assertEqual(s['manual_phase_receipt']['phase'],'TWO_DISTINCT_USER_COMMANDS_CLAIMED_UNVERIFIED')
        self.assertFalse(s['host_message_identity_verified'])

if __name__=='__main__':unittest.main()