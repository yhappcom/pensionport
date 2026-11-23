"""Synthetic source-grounded kind disagreement custody negative tests, never accuracy proof."""
from __future__ import annotations
import copy
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source_first_review import verify_diagnostic_topic_crosswalk
from ire.v6.kind_triage import verify_kind_disagreement_triage
from ire.v6.tests.test_p205_source_first_review import _source,_draft,_native,_crosswalk,_encode


class KindTriageSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.raw=_source()
        self.draft=_draft(self.raw)
        self.native=_native()
        self.native['atoms'][0].update(kind='OPINION',proposition='A speaker claim with no external evidence',
                                       source_refs=[{'cue_index':1,'quote':'ETF fees may exist.'}])
        self.native['atoms'][1].update(proposition='An illustrative price',
                                      source_refs=[{'cue_index':3,'quote':'A hypothetical price is shown.'}])
        self.cross=_crosswalk(self.draft,self.native,_encode(self.native))
        self.cross['source_to_native_related_review_only'][0]['same_kind_as_all_related']=False
        self.cross['provisional_kind_disagreement_pairs']=[{
            'source_candidate_id':'P205-SRC-001','native_claim_id':'C00001',
            'source_kind':'FACT','native_kind':'OPINION','cue':1}]
        self.cross['summary']['provisional_source_native_kind_disagreements_in_related_pairs']=1
        self.cross['high_risk_issue_review_queue']=[]
        self.cross['source_only_separate_claim_missing_in_native']=[]
        self.triage={
            'schema':'IRE_P205_PRIVATE_11_KIND_DISAGREEMENT_SOURCE_GROUNDED_SAME_CHAT_DIAGNOSTIC_V1',
            'original_source_sha256':sha256(self.raw),
            'provisional_source_json_sha256':sha256(_encode(self.draft)),
            'native_json_sha256':sha256(_encode(self.native)),
            'crosswalk_json_sha256':sha256(_encode(self.cross)),
            'counts':{'EMPIRICAL_UTTERANCE_NOT_VERIFIED':1},
            'total_related_label_discrepancies':1,
            'truly_semantically_disagreeing_pairs_gold_verified':None,
            'provisional_11_pair_triage':[{
                'source_candidate_id':'P205-SRC-001','native_claim_id':'C00001',
                'source_kind':'FACT','native_kind':'OPINION',
                'source_quoted_cue':1,'source_quote':'ETF fees may exist.',
                'source_quote_sha256':sha256(b'ETF fees may exist.'),
                'native_quote_cue':1,'native_quote':'ETF fees may exist.',
                'native_quote_sha256':sha256(b'ETF fees may exist.'),
                'source_proposition':'Provisional cue-anchored explanation',
                'native_proposition':'A speaker claim with no external evidence',
                'provisional_reconciliation_kind':'EMPIRICAL_UTTERANCE_NOT_VERIFIED',
                'same_chat_reasoning':'Synthetic statement type and reliability must be split',
                'remain_open_risk':'Synthetic economic fact is not verified independently',
                'engine_repair_tag':'distinguish_claim_form_from_evidential_verification',
                'speaker_audio_verified':False,
                'meaning_match_verified_by_independent_gold':False,
                'native_label_is_proven_wrong':False,
                'source_label_is_proven_correct':False,
                'financial_truth_certified':False,'eligible_as_gold':False,
                'requires_independent_followup':True}],
            'high_risk_issue_queue':[],
            'source_candidates_without_separate_native_topic_link':[],
            'novel_critical_index_scope_candidate':'SYNTHETIC_UNVERIFIED',
            'reviewer_context':'SAME_CHATGPT_PRIOR_EVIDENCE_EXPOSED_NOT_INDEPENDENT',
            'independent_reviewer_sessions_authenticated':0,
            'crosswalk_means_atom_identity':False,
            'group_counts_are_accuracy_metrics':False,
            'precision':None,'recall':None,'high_risk_FN':None,
            'independent_gold_atom_count':0,
            'E2_release':False,'E3_E4_E5_release':False,
            'P205_status':'HOLD','P206_status':'BLOCKED',
            'no_owner_original_files_modified':True,
        }
        # Check the parent topic link cannot promote to a TP.
        rr=verify_diagnostic_topic_crosswalk(_encode(self.native),_encode(self.draft),_encode(self.cross),
            expected_native_sha256=sha256(_encode(self.native)),
            expected_candidate_sha256=sha256(_encode(self.draft)),
            expected_crosswalk_sha256=sha256(_encode(self.cross)))
        self.assertIsNone(rr['independent_precision'])

    def eval(self,t=None,*,original=None,draft=None,native=None,cross=None,expected_triage_hash=None):
        t=self.triage if t is None else t
        s=self.raw if original is None else original
        d=self.draft if draft is None else draft
        n=self.native if native is None else native
        x=self.cross if cross is None else cross
        return verify_kind_disagreement_triage(s,_encode(n),_encode(d),_encode(x),_encode(t),
            expected_source_sha256=sha256(self.raw),
            expected_native_sha256=sha256(_encode(self.native)),
            expected_source_first_sha256=sha256(_encode(self.draft)),
            expected_crosswalk_sha256=sha256(_encode(self.cross)),
            expected_triage_sha256=(sha256(_encode(t)) if expected_triage_hash is None else expected_triage_hash),
            expected_source_cues=4,expected_triaged_pairs=1)
    def bad(self,mutator,reason='P205_KIND_TRIAGE_'):
        t=copy.deepcopy(self.triage);mutator(t)
        with self.assertRaisesRegex(InvalidInput,reason):self.eval(t)

    def test_01_synthetic_quote_reconciled_but_not_gold(self):
        x=self.eval();self.assertEqual(x['raw_label_different_topic_pairs_reviewed'],1)
        self.assertFalse(x['same_chat_triage_is_independent'])
        self.assertIsNone(x['precision'])
        self.assertEqual(x['status'],'TRIAGE_INTEGRITY_PASS_SEMANTIC_GOLD_HOLD')
    def test_02_frozen_triage_digest_mismatch(self):
        with self.assertRaisesRegex(InvalidInput,'KIND_TRIAGE_SHA_MISMATCH'):
            self.eval(expected_triage_hash='0'*64)
    def test_03_mutated_original_srt(self):
        with self.assertRaises(InvalidInput):self.eval(original=self.raw.replace(b'fees',b'FAKE'))
    def test_04_mutated_native_predictions(self):
        n=copy.deepcopy(self.native);n['atoms'][0]['kind']='FACT'
        with self.assertRaises(InvalidInput):self.eval(native=n)
    def test_05_mutated_provisional_source(self):
        d=copy.deepcopy(self.draft);d['provisional_atoms'][0]['kind']='OPINION'
        with self.assertRaises(InvalidInput):self.eval(draft=d)
    def test_06_mutated_crosswalk(self):
        c=copy.deepcopy(self.cross);c['provisional_kind_disagreement_pairs']=[]
        with self.assertRaises(InvalidInput):self.eval(cross=c)
    def test_07_dropped_disagreement_pair(self):
        self.bad(lambda t:t['provisional_11_pair_triage'].clear())
    def test_08_duplicate_disagreement_pair(self):
        self.bad(lambda t:t['provisional_11_pair_triage'].append(copy.deepcopy(t['provisional_11_pair_triage'][0])))
    def test_09_invented_native_id(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_claim_id='C99999'))
    def test_10_forged_source_claim_type(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(source_kind='RECOMMENDATION'))
    def test_11_forged_native_claim_type(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_kind='FACT'))
    def test_12_source_quoted_cue_wrong(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(source_quoted_cue=2))
    def test_13_source_quote_changed(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(source_quote='a fake text'))
    def test_14_source_quote_hash_changed(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(source_quote_sha256='0'*64))
    def test_15_native_quote_wrong(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_quote='wrong'))
    def test_16_native_cue_wrong(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_quote_cue=2))
    def test_17_native_quote_hash_wrong(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_quote_sha256='0'*64))
    def test_18_source_proposition_changed(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(source_proposition='unrelated'))
    def test_19_native_proposition_changed(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_proposition='unrelated'))
    def test_20_kind_category_unknown(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(provisional_reconciliation_kind='CONFIRMED_FALSE_NEGATIVE'))
    def test_21_wrong_engine_repair_kind(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(engine_repair_tag='approve_e2'))
    def test_22_short_reviewer_rationale(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(same_chat_reasoning='yes'))
    def test_23_unresolved_risk_hidden(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(remain_open_risk='none'))
    def test_24_false_same_chat_as_independent(self):
        self.bad(lambda t:t.update(reviewer_context='DIFFERENT_INDEPENDENT_REVIEWER'))
    def test_25_forged_reviewer_session(self):
        self.bad(lambda t:t.update(independent_reviewer_sessions_authenticated=2))
    def test_26_forged_atomic_gold(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(eligible_as_gold=True))
    def test_27_forged_native_wrong_label(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(native_label_is_proven_wrong=True))
    def test_28_forged_source_right_label(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(source_label_is_proven_correct=True))
    def test_29_forged_semantic_match_verified(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(meaning_match_verified_by_independent_gold=True))
    def test_30_forged_precision(self):
        self.bad(lambda t:t.update(precision=1))
    def test_31_forged_recall(self):
        self.bad(lambda t:t.update(recall=1))
    def test_32_forged_zero_highrisk_FN(self):
        self.bad(lambda t:t.update(high_risk_FN=0))
    def test_33_Fake_E2_release(self):
        self.bad(lambda t:t.update(E2_release=True))
    def test_34_Fake_E3_E4_E5_release(self):
        self.bad(lambda t:t.update(E3_E4_E5_release=True))
    def test_35_forged_P206_open(self):
        self.bad(lambda t:t.update(P206_status='READY'))
    def test_36_altered_label_group_counts(self):
        self.bad(lambda t:t.update(counts={'EVALUATION_PLUS_GUIDANCE':1}))
    def test_37_changed_original_pair_total(self):
        self.bad(lambda t:t.update(total_related_label_discrepancies=0))
    def test_38_fabricated_complete_gold_claim(self):
        self.bad(lambda t:t.update(truly_semantically_disagreeing_pairs_gold_verified=0))
    def test_39_no_independent_followup(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(requires_independent_followup=False))
    def test_40_false_topic_relation_is_atomic_identity(self):
        self.bad(lambda t:t.update(crosswalk_means_atom_identity=True))
    def test_41_false_numeric_counts_are_accuracy_metrics(self):
        self.bad(lambda t:t.update(group_counts_are_accuracy_metrics=True))
    def test_42_false_work_is_complete_and_owner_SRT_mutated(self):
        self.bad(lambda t:t.update(no_owner_original_files_modified=False))
    def test_43_missing_source_only_candidates(self):
        self.bad(lambda t:t.update(source_candidates_without_separate_native_topic_link=['FAKE']))
    def test_44_forge_high_risk_queue(self):
        self.bad(lambda t:t.update(high_risk_issue_queue=[{'id':'forged','review_status':'OPEN'}]))
    def test_45_alter_schema(self):
        self.bad(lambda t:t.update(schema='IRE_P205_APPROVED_GOLD_V1'))
    def test_46_wrong_prediction_sha(self):
        self.bad(lambda t:t.update(native_json_sha256='0'*64))
    def test_47_source_spans_extra_claim_left_unchecked(self):
        self.bad(lambda t:t.update(independent_gold_atom_count=1))
    def test_48_forged_financial_truth(self):
        self.bad(lambda t:t['provisional_11_pair_triage'][0].update(financial_truth_certified=True))

if __name__ == '__main__':
    unittest.main()
