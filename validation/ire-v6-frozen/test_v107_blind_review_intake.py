"""V107 synthetic-only negative-control tests. No owner transcripts, no gold."""
import copy
import sys
import unittest
from unittest.mock import patch

import v107_blind_review_intake as g


class TestV107BlindHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.windows = [
            ('SYN_V1', 'W00001', 1),
            ('SYN_V2', 'W00002', 41),
            ('SYN_V3', 'W00003', 81),
            ('SYN_V4', 'W00004', 121),
        ]
        rows=[];sel=[]
        for v,win,start in cls.windows:
            r=[]
            for i in range(start,start+40):
                txt=f'Fake synthetic cue {i}, not an investment or law fact.'
                r.append({'video_id':v,'window_id':win,'cue_index':i,'start_ms':i*1000,'end_ms':i*1000+300,'text_private':txt,'cue_sha256':g.sha(txt)})
            rows.extend(r)
            sel.append({'video_id':v,'window_id':win,'first_cue':start,'last_cue':start+39,'cue_count':40,'source_window_sha256':g.sha(' '.join(x['text_private'] for x in r))})
        cls.rows=rows
        cls.packet_digest=g.digest([[r['video_id'],r['cue_index'],r['cue_sha256']] for r in rows])
        cls.lock={'schema':g.V105_LOCK_SCHEMA,'source_zip_sha256':g.SOURCE_ARCHIVE_SHA256,'cue_count':160,'selected':sel,'independent_gold':False,'p0_go':False}
        cls.packet={'schema':g.V105_PACKET_SCHEMA,'source_archive_sha256':g.SOURCE_ARCHIVE_SHA256,'owner_private_cues':rows,'packet_sha256':cls.packet_digest,'prediction_disclosed':False,'blind_view':True,'independent_gold':False,'p0_go':False}

    def verify(self, lock=None, packet=None, **kwargs):
        with patch.object(g,'V105_PACKET_SHA256',self.packet_digest):
            return g.verify_owner_source_packet(self.lock if lock is None else lock,self.packet if packet is None else packet,actual_owner_archive_sha256=kwargs.get('archive',g.SOURCE_ARCHIVE_SHA256))

    def materials(self,slot='REVIEWER_A',lock=None,packet=None):
        with patch.object(g,'V105_PACKET_SHA256',self.packet_digest):
            return g.build_blind_reviewer_materials(self.lock if lock is None else lock,self.packet if packet is None else packet,slot,actual_owner_archive_sha256=g.SOURCE_ARCHIVE_SHA256)

    def completed(self,slot='REVIEWER_A'):
        pack,form=self.materials(slot)
        form['cue_verdicts']=[{**x,'status':'NO_FINANCIAL_CLAIM'} for x in form['cue_verdicts']]
        return pack,form

    def add_claim(self,pack,form,idx=0):
        cue=pack['source_cues_private'][idx];v=cue['video_id'];i=cue['cue_index'];win=cue['window_id'];aid=f'SYN_{i}'
        form['cue_verdicts'][idx]['status']='CLAIM';form['cue_verdicts'][idx]['atomic_ids']=[aid]
        form['atomic_claims'].append({'atomic_id':aid,'video_id':v,'window_id':win,'cue_indices':[i],
          'cue_source_sha256':g.digest([[v,i,cue['cue_sha256']]]),'stance':'FACT_CANDIDATE','risk':'HIGH',
          'proposition_private':'Only an invented synthetic opinion about investing.',
          'reviewer_reason_private':'Synthetic source is not actual financial evidence.',
          'conditions':[],'exceptions':[],'amounts_periods':[]})

    def test_01_source_valid(self):
        self.assertEqual(self.verify()['source_cue_count'],160)
    def test_02_packet_A_and_B_blind(self):
        a,af=self.materials('REVIEWER_A');b,bf=self.materials('REVIEWER_B')
        self.assertEqual(a['source_cues_private'],b['source_cues_private']);self.assertNotEqual(a['review_slot'],b['review_slot'])
        self.assertEqual(len(af['cue_verdicts']),160);self.assertTrue(all(x['status']=='UNREVIEWED' for x in af['cue_verdicts']))
    def test_03_no_model_labels_in_packet(self):
        packet,_=self.materials();self.assertNotIn('v93_',g.canonical(packet));self.assertNotIn('risk_signal',g.canonical(packet));self.assertNotIn('engine_output',g.canonical(packet))
    def test_04_wrong_source_zip(self):
        with self.assertRaises(ValueError):self.verify(archive='0'*64)
    def test_05_wrong_scope_zip(self):
        lock=copy.deepcopy(self.lock);lock['source_zip_sha256']='0'*64
        with self.assertRaises(ValueError):self.verify(lock=lock)
    def test_06_source_cue_changed(self):
        packet=copy.deepcopy(self.packet);packet['owner_private_cues'][0]['text_private']='TAMPERED'
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_07_cue_hash_changed(self):
        packet=copy.deepcopy(self.packet);packet['owner_private_cues'][0]['cue_sha256']='0'*64
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_08_source_missing(self):
        packet=copy.deepcopy(self.packet);packet['owner_private_cues'].pop()
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_09_duplicate_cue(self):
        packet=copy.deepcopy(self.packet);packet['owner_private_cues'][1]=copy.deepcopy(packet['owner_private_cues'][0])
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_10_unsorted_cue(self):
        packet=copy.deepcopy(self.packet);packet['owner_private_cues'][0],packet['owner_private_cues'][1]=packet['owner_private_cues'][1],packet['owner_private_cues'][0]
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_11_not_blind(self):
        packet=copy.deepcopy(self.packet);packet['prediction_disclosed']=True
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_12_fake_gold(self):
        packet=copy.deepcopy(self.packet);packet['independent_gold']=True
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_13_wrong_packet_pin(self):
        packet=copy.deepcopy(self.packet);packet['packet_sha256']='f'*64
        with self.assertRaises(ValueError):self.verify(packet=packet)
    def test_14_invalid_role(self):
        with self.assertRaises(ValueError):self.materials('REVIEWER_Z')
    def test_15_blank_form_not_valid_submission(self):
        p,f=self.materials()
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_16_fake_complete_no_claim_still_no_gold(self):
        p,f=self.completed();r=g.validate_submitted_form(f,p)
        self.assertFalse(r['independent_gold']);self.assertIsNone(r['certified_recall']);self.assertFalse(r['independent_human_verified'])
    def test_17_missing_review_status(self):
        p,f=self.completed();f['cue_verdicts'][0]['status']='UNREVIEWED'
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_18_missing_verdict(self):
        p,f=self.completed();f['cue_verdicts'].pop()
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_19_duplicate_verdict(self):
        p,f=self.completed();f['cue_verdicts'][1]=copy.deepcopy(f['cue_verdicts'][0])
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_20_wrong_source_receipt(self):
        p,f=self.completed();f['source_packet_sha256']='0'*64
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_21_claim_without_id(self):
        p,f=self.completed();f['cue_verdicts'][0]['status']='CLAIM'
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_22_non_claim_with_atom(self):
        p,f=self.completed();f['cue_verdicts'][0]['atomic_ids']=['SYN_1']
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_23_one_valid_synthetic_claim_still_no_gold(self):
        p,f=self.completed();self.add_claim(p,f);r=g.validate_submitted_form(f,p)
        self.assertEqual(r['candidate_claim_count'],1);self.assertFalse(r['independent_gold'])
    def test_24_claim_source_hash_tamper(self):
        p,f=self.completed();self.add_claim(p,f);f['atomic_claims'][0]['cue_source_sha256']='0'*64
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_25_claim_wrong_cue(self):
        p,f=self.completed();self.add_claim(p,f);f['atomic_claims'][0]['cue_indices']=[1000]
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_26_claim_missing_exception_field(self):
        p,f=self.completed();self.add_claim(p,f);del f['atomic_claims'][0]['exceptions']
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_27_claim_invalid_stance(self):
        p,f=self.completed();self.add_claim(p,f);f['atomic_claims'][0]['stance']='APPROVED_FACT'
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_28_claim_id_mismatch(self):
        p,f=self.completed();self.add_claim(p,f);f['cue_verdicts'][0]['atomic_ids']=['BAD']
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_29_claim_invalid_risk(self):
        p,f=self.completed();self.add_claim(p,f);f['atomic_claims'][0]['risk']='CERTIFIED'
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_30_claim_duplicate(self):
        p,f=self.completed();self.add_claim(p,f);f['atomic_claims'].append(copy.deepcopy(f['atomic_claims'][0]))
        with self.assertRaises(ValueError):g.validate_submitted_form(f,p)
    def test_31_disagreement_same_verdict_not_semantic_gold(self):
        pa,a=self.completed('REVIEWER_A');pb,b=self.completed('REVIEWER_B')
        docket=g.create_disagreement_docket(a,b,pa,pb)
        self.assertEqual(docket['cue_status_agreement_only'],160);self.assertFalse(docket['atomic_claim_equivalence_independently_adjudicated'])
    def test_32_disagreement_one_status(self):
        pa,a=self.completed('REVIEWER_A');pb,b=self.completed('REVIEWER_B')
        b['cue_verdicts'][0]['status']='OPEN_SOURCE_AUDIO'
        docket=g.create_disagreement_docket(a,b,pa,pb)
        self.assertEqual(docket['cue_status_disagreement_count'],1);self.assertIsNone(docket['certified_precision'])
    def test_33_swapped_reviewers(self):
        pa,a=self.completed('REVIEWER_A');pb,b=self.completed('REVIEWER_B')
        with self.assertRaises(ValueError):g.create_disagreement_docket(b,a,pb,pa)
    def test_34_mismatched_cohort(self):
        pa,a=self.completed('REVIEWER_A');pb,b=self.completed('REVIEWER_B');pb['source_packet_sha256']='f'*64
        with self.assertRaises(ValueError):g.create_disagreement_docket(a,b,pa,pb)
    def test_35_unverified_identity_remains_no_score(self):
        r=g.require_external_identity_and_gold(review_a={'signed':True},review_b={'signed':True},adjudicator={'signed':True})
        self.assertFalse(r['independent_gold']);self.assertEqual(r['external_verified_roles'],0);self.assertIsNone(r['precision'])
    def test_36_external_self_attestation_rejected(self):
        with self.assertRaises(ValueError):g.require_external_identity_and_gold(external_trust_anchor={'owner_supplied_self_attestation':True})
    def test_37_no_reviewers_no_score(self):
        r=g.require_external_identity_and_gold()
        self.assertEqual(r['external_roles_submitted'],0);self.assertIsNone(r['high_risk_recall']);self.assertFalse(r['p0_go'])
    def test_38_v105_self_asserted_identity_registry_without_root_rejected(self):
        from v105_blind_gold_protocol import external_gold_gate
        fake={'verified_by_external_identity_authority':True,'verified_unique_people':['person-a','person-b','person-c']}
        a={'reviewer_id':'person-a'};b={'reviewer_id':'person-b'};c={'adjudicator_id':'person-c'}
        with self.assertRaisesRegex(ValueError,'NO_TRUSTED_AUTHORITY_ROOT'):
            external_gold_gate({}, {},a,b,c,trusted_registry=fake)
    def test_39_v105_arbitrary_root_pubkey_rejected(self):
        from v105_blind_gold_protocol import external_gold_gate
        fake={'verified_by_external_identity_authority':True,
              'identity_authority_root_public_key_hex':'f'*64,
              'verified_unique_people':['person-a','person-b','person-c']}
        a={'reviewer_id':'person-a'};b={'reviewer_id':'person-b'};c={'adjudicator_id':'person-c'}
        with self.assertRaisesRegex(ValueError,'SELF_ASSERTED_IDENTITY_AUTHORITY_BLOCKED'):
            external_gold_gate({}, {},a,b,c,trusted_registry=fake)
    def test_40_unverified_gate_cannot_report_real_precision(self):
        from v105_blind_gold_protocol import score_predictions, digest
        gold=[{'atomic_id':'G1','risk':'HIGH'}]
        pred=[{'atomic_id':'P1'}]
        gate={'independent_gold':True,'gold_locked':True,'gold_source_digest':digest(gold)}
        eq={'external_adjudication_verified':True,'gold_sha256':digest(gold),'prediction_sha256':digest(pred),
            'pairs':[{'gold_atomic_id':'G1','predicted_atomic_id':'P1','semantically_equivalent':True,
                'source_span_verified':True,'stance_preserved':True,
                'condition_exception_preserved':True,'adjudicator_attested':True}]}
        with self.assertRaises(ValueError):
            score_predictions(gold,pred,independent_gate_receipt=gate,equivalence_receipt=eq)
    def test_41_synthetic_arithmetic_cannot_be_misreported_as_gold(self):
        from v105_blind_gold_protocol import score_predictions, digest
        gold=[{'atomic_id':'G1','risk':'HIGH'}];pred=[{'atomic_id':'P1'}]
        gate={'independent_gold':True,'gold_locked':True,'gold_source_digest':digest(gold)}
        eq={'external_adjudication_verified':True,'gold_sha256':digest(gold),'prediction_sha256':digest(pred),
            'pairs':[{'gold_atomic_id':'G1','predicted_atomic_id':'P1','semantically_equivalent':True,
                'source_span_verified':True,'stance_preserved':True,
                'condition_exception_preserved':True,'adjudicator_attested':True}]}
        r=score_predictions(gold,pred,independent_gate_receipt=gate,equivalence_receipt=eq,synthetic_arithmetic_only=True)
        self.assertEqual((r['tp'],r['fp'],r['fn']),(1,0,0))
        self.assertIsNone(r['precision']);self.assertIsNone(r['high_risk_recall']);self.assertFalse(r['independent_gold_certified']);self.assertFalse(r['p0_go'])
    def test_42_forged_root_signature_does_not_overcome_missing_pin(self):
        from v105_blind_gold_protocol import verify_externally_pinned_signature
        p={'identity_authority_root_public_key_hex':'f'*64,
           'identity_authority_registry_signature_hex':'e'*128,
           'verified_by_external_identity_authority':True}
        with self.assertRaisesRegex(ValueError,'SELF_ASSERTED_IDENTITY_AUTHORITY_BLOCKED'):
            verify_externally_pinned_signature(p)

if __name__ == '__main__':
    unittest.main()