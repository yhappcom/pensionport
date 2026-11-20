"""V197 synthetic E3 projection tests. Never implies independently certified finance claims."""
import copy,json,os,tempfile,unittest
from contextlib import nullcontext
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay,_sha
from v197_e3_repaired_source_projection import (make_risk_register,validate_risk_register,
    build_review_view,seal_read_model,verify_seal)

H='f'*64
FIRST='a'*64
SECOND='b'*64
REPAIR='c'*64

class FakeReview:
    def __init__(self):
        self.config={'source_sha256':H,'frozen_first_study_sha256':FIRST}
        self.study={'video_id':'SYNTHETIC12','claim_count':120}
        self.cues={i:f'CMA cue {i} describes hypothetical financial risks.' for i in range(1,337)}
        self.atoms=[];self.judgments={}
        for i in range(1,121):
            if i<=28:st='QUARANTINE_UNSAFE_INVESTMENT_ADVICE';high=True
            elif i<=40:st='HOLD_SOURCE_MEANING_REPAIR';high=i<=38
            elif i<=50:st='HOLD_EXTERNAL_AUDIO_VISUAL_OR_PRODUCT_EVIDENCE';high=i<=49
            elif i<=52:st='HOLD_REMOVE_FALSE_ATOM_CANDIDATE';high=False
            else:st='HOLD_SOURCE_SPOKEN_FINANCIAL_TRUTH_UNCERTIFIED';high=i<=89
            self.atoms.append({'cue_index':i,'proposition':f'The source CMA cue {i} is hypothetical, not a guaranteed promise.',
                               'high_risk':high,'kind':'FACT','evidence_cues':[i]})
            self.judgments[i]={'e3_disposition':st,'financial_problem':'EXAGGERATED_SAFETY_OR_IGNORED_LOSS_RISK',
                               'first_turn_high_risk_flag':high,
                               'source_specific_rationale':f'The hypothetical source cue {i} requires independent financial and provider evidence, not a promise.'}
        assert sum(x['high_risk'] for x in self.atoms)==84
    def status(self):
        return {'source_sha256':H,'first_turn_frozen_owner_head_sha256':FIRST,'review_head_sha256':SECOND,
        'second_turn_claims_reviewed':120,'unreviewed_claims':0,'source_cue_count':336,
        'first_turn_open_cue_count':14,'first_turn_unresolved_tasks_count':34,
        'independent_gold':False,'e3_accuracy_certified':False,'v123_e4_authorized':False,
        'e5_published':False,'host_message_identity_verified':False,'video_id':'SYNTHETIC12'}
    def _db(self):return nullcontext(None)
    def _audit(self,db):return SECOND,self.judgments,6

class TestV197RepairedView(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'private.sealed.json'
        self.review=FakeReview();self.risk=make_risk_register(self.review,self.review.judgments)
        self.repair=object.__new__(E3SecondReviewRepairOverlay)
        self.repair.reviewer=self.review
        self.repair._original_pinned=lambda:None
        self.repair._db=lambda:nullcontext(None)
        self.amends={}
        for i in range(29,40):self._patch(i,'SOURCE_REWRITE_PROPOSED','Source-based unapproved wording. '+str(i))
        self._patch(1,'PRESERVE_QUARANTINE_SOURCE_REPHRASE','Safe attribution of speaker, but unsafe for finance.')
        self._patch(2,'PARENT_RELATION_REVIEW_REQUIRED',None,3)
        self._patch(40,'PARENT_RELATION_REVIEW_REQUIRED',None,39)
        self._patch(51,'REMOVE_NONATOMIC_PROPOSED',None)
        self._patch(52,'REMOVE_NONATOMIC_PROPOSED',None)
        self.repair._audit=lambda db:(REPAIR,self.amends,2)
        self.repair.status=lambda:{'source_sha256':H,'first_turn_owner_head_sha256':FIRST,
          'v195_second_review_head_sha256':SECOND,'repair_overlay_head_sha256':REPAIR,
          'proposed_corrections':16,'original_quarantined_retained':28,
          'original_open_cues_preserved':14,'original_source_tasks_preserved':34,
          'independent_gold':False,'accuracy_metrics_measured':False,
          'e3_approved':False,'e4_approved':False,'e5_published':False,
          'host_user_turn_ids_verified':False}
    def _patch(self,i,kind,word,relative=None):
        self.amends[i]={'repair_kind':kind,'corrected_proposition':word,'related_serial':relative,
          'first_claim_sha256':_sha(self.review.atoms[i-1]),
          'prior_second_judgment_sha256':_sha(self.review.judgments[i])}
    def view(self):return build_review_view(self.review,self.repair,expected_overlay_head=REPAIR,risk_register=self.risk)
    def test_01_realistic_full_120_census_and_84_risk_holds(self):
        z=self.view();self.assertEqual((len(z['records']),z['all_original_high_risk_blocked'],z['original_quarantines_enforced']),
                                   (120,84,28))
        self.assertEqual(z['other_high_risk_hold_blocked'],56)
    def test_02_16_proposals_not_accepted(self):
        z=self.view();self.assertEqual(z['v196_correction_proposals'],16)
        self.assertEqual(z['source_rewrite_proposals'],12)
        self.assertFalse(any(r['safe_for_financial_answers'] for r in z['records']))
        self.assertFalse(z['e3_approved'])
    def test_03_quarantine_cannot_be_downgraded_even_with_rewrite(self):
        z=self.view();r=z['records'][0];self.assertTrue(r['old_quarantine_enforced'])
        self.assertIsNotNone(r['source_fidelity_rewrite_proposal_only'])
        self.assertFalse(r['safe_for_financial_answers'])
    def test_04_nonatom_proposal_keeps_original(self):
        z=self.view();a=z['records'][50];self.assertTrue(a['proposed_nonatomic_exclusion_only'])
        self.assertTrue(a['original_still_in_record']);self.assertFalse(a['removed_or_merged_as_fact'])
    def test_05_parent_proposal_does_not_automerge(self):
        z=self.view();r=z['records'][1];self.assertEqual(r['proposed_parent_relation_serial_only'],3)
        self.assertFalse(r['removed_or_merged_as_fact'])
    def test_06_no_risk_can_be_missing(self):
        self.risk['risk_records'].pop()
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS_OR_TAMPER'):
            self.view()
    def test_07_quarantine_is_not_equivalent_to_false_claim(self):
        z=self.view();self.assertEqual(z['records'][0]['frozen_second_disposition'],'QUARANTINE_UNSAFE_INVESTMENT_ADVICE')
        self.assertFalse(z['records'][0]['finance_fact_approved'])
    def test_08_issuer_reference_cannot_be_passed_as_raw_bytes_custody(self):
        self.risk['risk_records'][0]['official_document_raw_bytes_verified']=True
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS_OR_TAMPER'):
            self.view()
    def test_09_source_quote_tamper_detected(self):
        self.risk['risk_records'][0]['source_quote']='fake guarantee from no source'
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS_OR_TAMPER'):
            self.view()
    def test_10_original_judgment_hash_tamper_detected(self):
        self.amends[29]['prior_second_judgment_sha256']='e'*64
        with self.assertRaisesRegex(InvalidInput,'WRONG_PATCH_SOURCE'):
            self.view()
    def test_11_wrong_previous_head_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'STALE_SOURCE_OR_REVIEW_OR_REPAIR_HEAD'):
            build_review_view(self.review,self.repair,expected_overlay_head='0'*64,risk_register=self.risk)
    def test_12_changed_first_turn_sha_rejected(self):
        st=self.review.status
        self.review.status=lambda:{**st(),'source_sha256':'0'*64}
        with self.assertRaisesRegex(InvalidInput,'STALE_SOURCE_OR_REVIEW_OR_REPAIR_HEAD'):
            self.view()
    def test_13_quality_forgery_rejected(self):
        st=self.review.status
        self.review.status=lambda:{**st(),'e3_accuracy_certified':True}
        with self.assertRaisesRegex(InvalidInput,'ILLEGAL_CLAIM_OF_QUALITY_OR_AUTHORITY'):
            self.view()
    def test_14_missing_proposal_rejected(self):
        del self.amends[40]
        with self.assertRaisesRegex(InvalidInput,'AUDITED_LEDGER_VS_REPAIR_MISMATCH|CURRENT_REAL_CMA_CENSUS_NOT_VERIFIED|PROPOSALS_SHOULD_REMAIN_16_AND_UNAPPROVED'):
            self.view()
    def test_15_risk_is_not_current_finance_truth(self):
        z=self.view();self.assertFalse(z['official_evidence_bytes_verified'])
        self.assertFalse(z['independent_gold']);self.assertFalse(z['accuracy_metrics_measured'])
    def test_16_seal_roundtrip_and_no_overwrite(self):
        v=self.view();s=seal_read_model(self.path,v)
        self.assertEqual(s,verify_seal(self.path,v))
        with self.assertRaisesRegex(InvalidInput,'NO_OVERWRITE_OR_SYMLINK'):
            seal_read_model(self.path,v)
    def test_17_sealed_view_tamper_detected(self):
        v=self.view();seal_read_model(self.path,v)
        j=json.loads(self.path.read_text());j['view']['records'][0]['safe_for_financial_answers']=True
        self.path.write_text(json.dumps(j))
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_SEAL_TAMPER_OR_WRONG_INPUT'):
            verify_seal(self.path,v)
    def test_18_seal_permissions_private(self):
        v=self.view();seal_read_model(self.path,v);os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_SEAL_MISSING_OR_UNSAFE_PERMISSION'):
            verify_seal(self.path,v)
    def test_19_historical_risk_ref_remains_only_web_lookup(self):
        a=self.risk['risk_records'][0]
        self.assertTrue(a['official_public_web_text_candidate_url'].startswith('https://law.kofia.or.kr/'))
        self.assertFalse(a['currently_applicable_fact_verified'])
    def test_20_applying_issuer_certification_to_register_rejected(self):
        self.risk['e3_approved']=True
        with self.assertRaisesRegex(InvalidInput,'RISK_REGISTER_FALSE_SOURCE_OR_CERTIFICATION'):
            self.view()
    def test_21_making_quarantine_old_review_ordinary_block_rejected(self):
        self.review.judgments[1]['e3_disposition']='HOLD_SOURCE_SPOKEN_FINANCIAL_TRUTH_UNCERTIFIED'
        with self.assertRaisesRegex(InvalidInput,'RISK_84_SOURCE_CENSUS_OR_TAMPER|WRONG_PATCH_SOURCE'):
            self.view()

if __name__=='__main__':unittest.main()