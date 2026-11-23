"""Synthetic host-attestation protocol. No owner SRT, reviewers or keys here."""
from __future__ import annotations
import base64,copy,unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from ire.v6.codec import canonical,json_digest,sha256
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.gold_release import evaluate_production_gold
import ire.v6.gold_release as release

class P205GoldReleaseTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_p205_atomic_gold import P205AtomicGoldTests
        fixture=P205AtomicGoldTests();fixture.setUp()
        self.plan=fixture.plan;self.source=fixture.source;self.native=fixture.pred_raw
        self.gold=fixture.gold;self.alignment=fixture.alignment
        self.signers={r:Ed25519PrivateKey.generate() for r in release.ROLES}
        self.keys={r:base64.b64encode(k.public_key().public_bytes(
             encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw
             )).decode() for r,k in self.signers.items()}
        self.registry={
           'schema':'IRE_P205_PINNED_REVIEW_REGISTRY_V1',
           'enrolled_at':'2026-11-22T00:00:00+00:00',
           'plan_sha256':json_digest(self.plan),
           'source_srt_sha256':sha256(self.source),
           'native_prediction_sha256':sha256(self.native),
           'source_only_packet_sha256':'3'*64,
           'public_keys':self.keys}
        self.reviews=[]
        for ix,role in enumerate(release.ROLES[:2],1):
            body={
              'schema':'IRE_P205_HOST_BLIND_REVIEW_SUBMISSION_V1',
              'role':role,'session_id':f'blind_host_session_0000{ix}',
              'source_srt_sha256':sha256(self.source),
              'source_only_packet_sha256':self.registry['source_only_packet_sha256'],
              'predictions_exposed':False,
              'began_at':f'2026-11-22T0{ix}:00:00+00:00',
              'submitted_at':f'2026-11-22T0{ix+2}:00:00+00:00',
              'draft_gold':copy.deepcopy(self.gold)}
            self.reviews.append(self._signed_review(body))
        body={
          'schema':'IRE_P205_TWO_REVIEWER_ATOMIC_CONSENSUS_V1',
          'reviewer_submission_sha256':{r['body']['role']:json_digest(r['body']) for r in self.reviews},
          'gold_sha256':json_digest(self.gold),
          'disagreements_count':0,'resolved_disagreements_count':0,
          'gold_frozen_at':'2026-11-22T06:00:00+00:00',
          'disagreement_resolutions':[],
          'final_gold_provenance':[
            {'gold_id':gid,'reviewer_one_gold_ids':[gid],
             'reviewer_two_gold_ids':[gid],
             'disposition':'BOTH_SUPPORTED',
             'reason':'Both reviewers documented the same source-only claim'}
            for gid in ('G00001','G00002')],
          'excluded_draft_claims':[]}
        self.consensus={'body':body,'signatures':{r:self._sign(r,body) for r in release.ROLES}}
        body={'schema':'IRE_P205_POST_GOLD_ALIGNMENT_LOCK_V1',
              'gold_sha256':json_digest(self.gold),
              'alignment_sha256':json_digest(self.alignment),
              'aligned_at':'2026-11-22T07:00:00+00:00'}
        self.alignment_receipt={'body':body,'host_signature':self._sign('neutral_host',body)}

    def _sign(self,role,body):
        return base64.b64encode(self.signers[role].sign(canonical(body))).decode()

    def _signed_review(self,body):
        return {'body':body,'reviewer_signature':self._sign(body['role'],body),
                'neutral_host_signature':self._sign('neutral_host',body)}

    def _re_sign_consensus(self):
        self.consensus['body']['reviewer_submission_sha256']={r['body']['role']:json_digest(r['body']) for r in self.reviews}
        self.consensus['signatures']={r:self._sign(r,self.consensus['body']) for r in release.ROLES}

    def _eval(self,**overrides):
        args=dict(gold=self.gold,alignment=self.alignment,registry=self.registry,
                  reviewer_submissions=self.reviews,consensus=self.consensus,
                  alignment_receipt=self.alignment_receipt)
        args.update(overrides)
        return evaluate_production_gold(self.plan,self.source,self.native,**args)

    def _pinned(self):
        return patch.object(release,'PINNED_P205_HOST_REVIEW_REGISTRY_SHA256',json_digest(self.registry))

    def test_01_current_production_registry_unenrolled_holds(self):
        self.assertIsNone(release.PINNED_P205_HOST_REVIEW_REGISTRY_SHA256)
        r=self._eval()
        self.assertEqual(r['status'],'HOLD_NO_PRE_REVIEW_PRODUCTION_HOST_REGISTRY_PIN')
        self.assertIsNone(r['independent_precision'])

    def test_02_signed_caller_supplied_keys_do_not_self_certify(self):
        self.assertFalse(self._eval()['independent_gold_verified'])

    def test_03_pinned_synthetic_identity_can_activate_e2_only(self):
        with self._pinned():r=self._eval()
        self.assertTrue(r['independent_gold_verified'])
        self.assertEqual(r['independent_precision'],1)
        self.assertEqual(r['independent_recall'],1)
        self.assertEqual(r['independent_high_risk_false_negative_count'],0)
        self.assertTrue(r['ready_for_p0_2_06'])
        self.assertFalse(r['e3_e4_e5_knowledge_approved'])
        self.assertFalse(r['personalized_advice_authorized'])

    def test_04_registry_digest_tampered_holds(self):
        with patch.object(release,'PINNED_P205_HOST_REVIEW_REGISTRY_SHA256','0'*64):r=self._eval()
        self.assertFalse(r['production_trust_registry_verified'])

    def test_05_reviewer_got_prediction_holds(self):
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'predictions_exposed':True})
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_REVIEWER_NOT_SEPARATELY',r['status'])

    def test_06_repeated_session_id_holds(self):
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],
                                             'session_id':self.reviews[0]['body']['session_id']})
        with self._pinned():r=self._eval()
        self.assertFalse(r['two_blind_reviews_host_attested'])

    def test_07_review_before_enrolment_holds(self):
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'began_at':'2026-11-21T12:00:00+00:00'})
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_REVIEWS_NOT_AFTER',r['status'])

    def test_08_bad_reviewer_signature_holds(self):
        self.reviews[0]['reviewer_signature']='A'*88
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_NOT_AUTHENTICATED',r['status'])

    def test_09_bad_host_signature_holds(self):
        self.reviews[0]['neutral_host_signature']='A'*88
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_NOT_AUTHENTICATED',r['status'])

    def test_10_review_wrong_source_packet_holds(self):
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'source_only_packet_sha256':'1'*64})
        with self._pinned():r=self._eval()
        self.assertFalse(r['independent_gold_verified'])

    def test_11_draft_has_missing_cue_to_atom_holds(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['reviewed_cues'][0]['gold_atom_ids']=[]
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_DRAFT_ATOMIC_SOURCE_TRACE_INVALID',r['status'])

    def test_12_draft_has_open_cue_holds(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['reviewed_cues'][3]['status']='OPEN_UNCERTAIN'
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_DRAFT_NOT_FULLY_SOURCE_REVIEWED',r['status'])

    def test_13_draft_has_fabricated_quote_holds(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['atomic_gold_claims'][0]['source_refs'][0]['quote']='not part of source'
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_DRAFT_NON_SOURCE_ATOMIC_CLAIM',r['status'])

    def test_14_only_one_reviewer_holds(self):
        with self._pinned():r=self._eval(reviewer_submissions=self.reviews[:1])
        self.assertIn('HOLD_TWO_INDEPENDENT',r['status'])

    def test_15_consensus_signature_forged_holds(self):
        self.consensus['signatures']['neutral_host']='A'*88
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_DISAGREEMENTS_OR_CONSENSUS',r['status'])

    def test_16_not_all_disagreements_resolved_holds(self):
        self.consensus['body']['disagreements_count']=1
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_DISAGREEMENTS_OR_CONSENSUS',r['status'])

    def test_17_gold_frozen_before_reviews_holds(self):
        self.consensus['body']['gold_frozen_at']='2026-11-22T01:00:00+00:00'
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_GOLD_FROZEN_BEFORE',r['status'])

    def test_18_alignment_earlier_than_gold_holds(self):
        self.alignment_receipt['body']['aligned_at']='2026-11-22T05:00:00+00:00'
        self.alignment_receipt['host_signature']=self._sign('neutral_host',self.alignment_receipt['body'])
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_ALIGNMENT_PERFORMED',r['status'])

    def test_19_alignment_not_signed_holds(self):
        self.alignment_receipt['host_signature']='A'*88
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_GOLD_TO_PREDICTION',r['status'])

    def test_20_registry_plan_changed_holds(self):
        self.registry['plan_sha256']='0'*64
        with self._pinned():r=self._eval()
        self.assertIn('HOLD_WRONG_PINNED_SOURCE',r['status'])

    def test_21_partial_match_fails_financial_thresholds(self):
        self.alignment['pairs'][1]['match_dimensions']['conditions']=False
        self.alignment_receipt['body']['alignment_sha256']=json_digest(self.alignment)
        self.alignment_receipt['host_signature']=self._sign('neutral_host',self.alignment_receipt['body'])
        with self._pinned():r=self._eval()
        self.assertTrue(r['independent_gold_verified'])
        self.assertFalse(r['ready_for_p0_2_06'])
        self.assertEqual(r['independent_precision'],0.5)
        self.assertEqual(r['independent_recall'],0.5)

    def test_22_high_risk_false_negative_blocks_go(self):
        self.alignment['pairs']=self.alignment['pairs'][1:]
        self.alignment['unmatched_gold_ids']=['G00001']
        self.alignment['unmatched_prediction_ids']=['C00001']
        self.alignment_receipt['body']['alignment_sha256']=json_digest(self.alignment)
        self.alignment_receipt['host_signature']=self._sign('neutral_host',self.alignment_receipt['body'])
        with self._pinned():r=self._eval()
        self.assertEqual(r['independent_high_risk_false_negative_count'],1)
        self.assertFalse(r['ready_for_p0_2_06'])

    def test_23_divergent_review_drafts_without_adjudication_holds(self):
        draft=copy.deepcopy(self.reviews[1]['body']['draft_gold'])
        draft['atomic_gold_claims'][0]['proposition']='new contested proposition'
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')


    def test_24_false_positive_consensus_count_without_cue_resolution(self):
        draft=copy.deepcopy(self.reviews[1]['body']['draft_gold'])
        draft['atomic_gold_claims'][0]['proposition']='deliberately changed reviewer assertion'
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],'draft_gold':draft})
        self.consensus['body']['disagreements_count']=1
        self.consensus['body']['resolved_disagreements_count']=1
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_25_changed_final_gold_without_any_reviewer_support(self):
        self.gold['atomic_gold_claims'][0]['proposition']='unsourced consensus reinterpretation'
        self.consensus['body']['gold_sha256']=json_digest(self.gold)
        self._re_sign_consensus()
        self.alignment_receipt['body']['gold_sha256']=json_digest(self.gold)
        self.alignment_receipt['host_signature']=self._sign('neutral_host',self.alignment_receipt['body'])
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_26_empty_blind_reviewer_reason_not_a_completed_review(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['reviewed_cues'][0]['reason']=''
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        self.consensus['body']['disagreements_count']=1
        self.consensus['body']['resolved_disagreements_count']=1
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_27_reviewer_atom_silently_dropped_at_consensus(self):
        draft=copy.deepcopy(self.reviews[1]['body']['draft_gold'])
        extra=copy.deepcopy(draft['atomic_gold_claims'][0])
        extra['gold_id']='G00003'
        extra['source_refs']=[{'cue_index':3,'quote':'This example is not a confirmed ETF offer.'}]
        draft['atomic_gold_claims'].append(extra)
        draft['reviewed_cues'][2]['status']='REVIEWED_ATOM'
        draft['reviewed_cues'][2]['gold_atom_ids']=['G00003']
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],'draft_gold':draft})
        self.consensus['body']['disagreements_count']=1
        self.consensus['body']['resolved_disagreements_count']=1
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')


    def _dispute_with_explanation(self):
        draft=copy.deepcopy(self.reviews[1]['body']['draft_gold'])
        draft['atomic_gold_claims'][0]['proposition']='contradictory source-only second reviewer claim'
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],'draft_gold':draft})
        self.consensus['body']['disagreements_count']=1
        self.consensus['body']['resolved_disagreements_count']=1
        self.consensus['body']['disagreement_resolutions']=[{
          'cue_index':1,'reviewer_one_gold_ids':['G00001'],
          'reviewer_two_gold_ids':['G00001'],'final_gold_ids':['G00001'],
          'reason':'Reviewer wordings differ for original source cue one',
          'resolution':'Reviewers chose initial wording after checking the original source'}]
        self.consensus['body']['final_gold_provenance'][0]['disposition']='RECONCILED_VARIANT'
        self.consensus['body']['final_gold_provenance'][0]['reason']='Contradictory claims were reconciled against cue 1'
        self._re_sign_consensus()

    def _add_reviewer_two_extra_draft_claim(self):
        draft=copy.deepcopy(self.reviews[1]['body']['draft_gold'])
        extra=copy.deepcopy(draft['atomic_gold_claims'][0])
        extra['gold_id']='G00003'
        extra['source_refs']=[{'cue_index':3,'quote':'This example is not a confirmed ETF offer.'}]
        draft['atomic_gold_claims'].append(extra)
        draft['reviewed_cues'][2]['status']='REVIEWED_ATOM'
        draft['reviewed_cues'][2]['gold_atom_ids']=['G00003']
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],'draft_gold':draft})
        self.consensus['body']['disagreements_count']=1
        self.consensus['body']['resolved_disagreements_count']=1
        self.consensus['body']['disagreement_resolutions']=[{
          'cue_index':3,'reviewer_one_gold_ids':[],
          'reviewer_two_gold_ids':['G00003'],'final_gold_ids':[],
          'reason':'Only second reviewer found an extra synthetic claim at cue three',
          'resolution':'Evidence was reviewed and extra claim was excluded as non-atomic'}]
        self._re_sign_consensus()

    def test_28_signed_cue_by_cue_reconciliation_can_pass_synthetic_only(self):
        self._dispute_with_explanation()
        with self._pinned():r=self._eval()
        self.assertTrue(r['ready_for_p0_2_06'])
        self.assertEqual(r['cue_disagreements_individually_resolved'],1)
        self.assertEqual(r['final_gold_atoms_with_reviewer_lineage'],2)

    def test_29_disagreement_cue_index_falsification_holds(self):
        self._dispute_with_explanation()
        self.consensus['body']['disagreement_resolutions'][0]['cue_index']=2
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_30_signed_count_without_actual_cue_reconciliation_holds(self):
        self._dispute_with_explanation()
        self.consensus['body']['disagreement_resolutions']=[]
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_31_false_two_reviewer_unanimity_holds(self):
        self._dispute_with_explanation()
        self.consensus['body']['final_gold_provenance'][0]['disposition']='BOTH_SUPPORTED'
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_32_missing_final_gold_claim_lineage_holds(self):
        self.consensus['body']['final_gold_provenance'].pop()
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_33_unmentioned_reviewer_only_atom_silently_dropped_holds(self):
        self._add_reviewer_two_extra_draft_claim()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')

    def test_34_documented_reviewer_only_exclusion_can_pass_synthetic_only(self):
        self._add_reviewer_two_extra_draft_claim()
        self.consensus['body']['excluded_draft_claims']=[{
          'role':'reviewer_two','gold_id':'G00003',
          'reason':'Original source quote was not a separate atomic claim'}]
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertTrue(r['ready_for_p0_2_06'])
        self.assertEqual(r['cue_disagreements_individually_resolved'],1)

    def test_35_launder_disagreement_reason_as_empty_holds(self):
        self._dispute_with_explanation()
        self.consensus['body']['disagreement_resolutions'][0]['reason']=''
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_UNVERIFIED_GOLD_RESOLUTION_LINEAGE')


    def test_36_identical_atom_meanings_different_reviewer_notes_are_not_disagreements(self):
        draft=copy.deepcopy(self.reviews[1]['body']['draft_gold'])
        draft['reviewed_cues'][0]['reason']='Independent reviewer explained the same proposition with different words'
        self.reviews[1]=self._signed_review({**self.reviews[1]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertTrue(r['ready_for_p0_2_06'],r['status'])
        self.assertEqual(r['cue_disagreements_individually_resolved'],0)

    def test_37_both_reviewer_drafts_missing_gold_schema_must_hold(self):
        for i in range(2):
            draft=copy.deepcopy(self.reviews[i]['body']['draft_gold'])
            del draft['schema']
            self.reviews[i]=self._signed_review({**self.reviews[i]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_DRAFT_SOURCE_ONLY_GOLD_SCHEMA_INVALID')

    def test_38_reviewer_drafts_sneak_in_prior_predictions_must_hold(self):
        for i in range(2):
            draft=copy.deepcopy(self.reviews[i]['body']['draft_gold'])
            draft['frozen_native_predictions']=[{'claim_id':'SYNTHETIC_PREDICTION_LEAK'}]
            self.reviews[i]=self._signed_review({**self.reviews[i]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_DRAFT_SOURCE_ONLY_GOLD_SCHEMA_INVALID')


    def test_39_invalid_list_kind_in_review_draft_holds_without_crash(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['atomic_gold_claims'][0]['kind']=['FACT']
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_DRAFT_SOURCE_ONLY_GOLD_SCHEMA_INVALID')

    def test_40_prior_claim_injected_into_gold_atom_holds(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['atomic_gold_claims'][0]['previous_native_claim']={'claim_id':'SYNTHETIC_C00001'}
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_DRAFT_SOURCE_ONLY_GOLD_SCHEMA_INVALID')

    def test_41_prior_model_marker_injected_into_cue_disposition_holds(self):
        draft=copy.deepcopy(self.reviews[0]['body']['draft_gold'])
        draft['reviewed_cues'][0]['frozen_native_claim_id']='SYNTHETIC_C00001'
        self.reviews[0]=self._signed_review({**self.reviews[0]['body'],'draft_gold':draft})
        self._re_sign_consensus()
        with self._pinned():r=self._eval()
        self.assertEqual(r['status'],'HOLD_DRAFT_SOURCE_ONLY_GOLD_SCHEMA_INVALID')

if __name__=='__main__':unittest.main()
