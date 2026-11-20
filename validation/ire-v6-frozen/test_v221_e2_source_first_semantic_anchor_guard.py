"""Public code-only synthetic tests for V221; NO user owner SRT or gold data."""
from __future__ import annotations
import unittest,copy,json
from hashlib import sha256 as hashlib_sha
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from ire.v6.atomic_exchange import NUMBER,audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from v221_e2_source_first_semantic_anchor_guard import (
    audit_source_first_native_alignment,require_e2_release,
)

RAW=(
    "1\n00:00:01,000 --> 00:00:01,500\n자, 이제 설명을 시작합니다.\n\n"
    "2\n00:00:02,000 --> 00:00:02,500\nETF는 투자 상품입니다.\n\n"
    "3\n00:00:03,000 --> 00:00:03,500\n차트는 아직 확인하지 않았습니다.\n\n"
    "4\n00:00:04,000 --> 00:00:04,500\n감사합니다.\n"
).encode('utf8')


def encoded(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8')


def make_fixture():
    source,_=make_original_plan(RAW,'Synth123456',
        expected_source_sha256=sha256(RAW),window_size=2)
    cues=source.cues
    old={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1","video_id":source.video_id,
         "source_sha256":source.source_sha256,"manifest_sha256":source.manifest_sha256,
         "cue_dispositions":[],"atoms":[{
            "claim_id":"C00001","owner_window_id":source.owner(1),
            "proposition":"ETF는 투자 상품입니다.","kind":"FACT",
            "stance":"UNRESOLVED","speaker":"UNKNOWN",
            "source_refs":[{"cue_index":1,"quote":cues[0].text}],
            "context_cue_indices":[1,2],"condition_cue_indices":[],
            "exception_cue_indices":[],"numeric_references":[],"as_of":None,
         }]}
    for i,cue in enumerate(cues,1):
        old['cue_dispositions'].append({
            "cue_index":i,"cue_text_sha256":sha256(cue.text.encode('utf8')),
            "disposition":"CANDIDATES" if i==1 else "UNRESOLVED",
            "claim_ids":["C00001"] if i==1 else [],
            "numeric_tokens":NUMBER.findall(cue.text),
            "note":"이 발화는 출처 검증이 필요한 미승인 원자 후보입니다.",
        })
    new=copy.deepcopy(old)
    new['atoms'][0]['source_refs']=[{'cue_index':2,'quote':cues[1].text}]
    new['cue_dispositions'][0]['disposition']='UNRESOLVED'
    new['cue_dispositions'][0]['claim_ids']=[]
    new['cue_dispositions'][1]['disposition']='CANDIDATES'
    new['cue_dispositions'][1]['claim_ids']=['C00001']
    audit_host_atomic_exchange(source,old);audit_host_atomic_exchange(source,new)
    source_units=[]
    for i,(a,b,kind) in enumerate([(1,1,'NARRATIVE_NONCLAIM'),
                                  (2,2,'FACT_AS_SPOKEN'),
                                  (3,4,'NARRATIVE_NONCLAIM')],1):
        source_units.append({
            'source_only_id':f'SRC221-{i:03d}', 'cue_start':a,'cue_end':b,
            'source_refs':[{'cue_index':j,'quote':cues[j-1].text,
                   'source_text_sha256':sha256(cues[j-1].text.encode('utf8'))}
                   for j in range(a,b+1)],
            'proposition_from_original_unverified':
                 'ETF는 투자 상품입니다.' if i==2 else '감사 및 담화 전환입니다.',
            'discourse_kind':kind,'risk_tags':[],
            'source_review_status':'CHATGPT_SOURCE_FIRST_INTERNAL_NOT_BLIND_GOLD',
            'speaker_verified':False,'truth_certified':False,'e2_pass':False,
        })
    src={'schema':'IRE_V221_REAL_ETF_250_SOURCE_FIRST_INTERNAL_DISCOURSE_ATOM_REVIEW_DRAFT_V1',
         'video_id':source.video_id,'source_sha256':sha256(RAW),
         'original_cues_covered':4,'source_first_dispositions':3,
         'source_kinds':{'NARRATIVE_NONCLAIM':2,'FACT_AS_SPOKEN':1},
         'source_internal_review_not_independent_gold':True,
         'author_was_exposed_to_prior_engine_project_context':True,
         'not_a_blind_gold_dataset':True,
         'financial_facts_approved':False,'e2_final_pass':False,
         'claims':source_units}
    patch={'schema':'IRE_V221_PRIVATE_ETF_REAL_ATOM_SEMANTIC_PRIMARY_EVIDENCE_PATCH_V1',
           'source_sha256':sha256(RAW),
           'previous_native_sha256':sha256(encoded(old)),
           'corrected_native_sha256':sha256(encoded(new)),
           'reviewed_primary_corrections':1,'native_atoms_after':1,
           'speaker_verified':False,'independent_gold':False,'e2_pass':False,
           'corrections':[{
               'claim_id':'C00001','prior_primary_cue_index':1,
               'corrected_primary_cue_index':2,
               'prior_primary_source_text_sha256':sha256(cues[0].text.encode('utf8')),
               'new_primary_source_text_sha256':sha256(cues[1].text.encode('utf8')),
               'prior_primary_quote':cues[0].text,'new_primary_quote':cues[1].text,
               'prior_owner_window_id':source.owner(1),
               'corrected_owner_window_id':source.owner(2),
               'proposition':'ETF는 투자 상품입니다.',
               'financial_truth_approved':False,
            }]}
    rows=[]
    for i,kind in enumerate(['NONCLAIM_OR_TRANSITION_PROVISIONAL',
                              'NATIVE_DISCOURSE_OVERLAP_NOT_EQUIVALENCE',
                              'NONCLAIM_OR_TRANSITION_PROVISIONAL']):
        u=source_units[i];linked=['C00001'] if i==1 else []
        rows.append({'source_only_id':u['source_only_id'],
             'from_cue':u['cue_start'],'to_cue':u['cue_end'],
             'source_only_unit_kind':u['discourse_kind'],
             'matched_native_ids':linked,
             'native_old_primary_in_source_unit':[],
             'native_new_primary_in_source_unit':linked,
             'media_hold_packet_id':None,
             'source_first_review_disposition':kind,
             'one_to_one_exact_semantic_equivalence_certified':False,
             'separate_blind_external_gold':False,'financial_fact_approved':False})
    cross={'schema':'IRE_V221_ETF250_SOURCE_FIRST_TO_NATIVE_MEANING_ANCHOR_ALIGNMENT_INTERNAL_HOLD_V1',
        'source_sha256':sha256(RAW),
        'source_first_review_sha256':sha256(encoded(src)),
        'previous_native_sha256':sha256(encoded(old)),
        'corrected_native_sha256':sha256(encoded(new)),
        'crosswalk_review_uses_native_candidates':True,
        'independent_gold_certified':False,'precision_recall_measured':False,
        'financial_fact_approved':False,'e2_final_pass':False,
        'source_units_reviewed':3,
        'native_claims_covered_by_any_source_unit':1,
        'old_native_primary_in_at_least_one_source_unit':0,
        'new_native_primary_in_at_least_one_source_unit':1,
        'additional_unverified_screen_speech_claims':0,
        'rows':rows}
    return {'source':RAW,'source_docket':src,'old_native':old,'new_native':new,
            'patch':patch,'crosswalk':cross}


class TestV221E2SourceFirstAnchorGuard(unittest.TestCase):
    def setUp(self):self.data=make_fixture()
    def audit(self,*,original_sha_override=None):
        b={k:(v if k=='source' else encoded(v)) for k,v in self.data.items()}
        h={k:sha256(v) for k,v in b.items()}
        if original_sha_override is not None:h['source']=original_sha_override
        return audit_source_first_native_alignment(
            b['source'],self.data['source_docket'],b['source_docket'],
            self.data['old_native'],b['old_native'],
            self.data['new_native'],b['new_native'],
            self.data['patch'],b['patch'],
            self.data['crosswalk'],b['crosswalk'],
            expected_hashes=h,window_size=2)

    def test_01_synthetic_old_misanchor_reanchored_without_gold(self):
        r=self.audit()
        self.assertEqual((r['old_native_anchors_in_corresponding_source_unit'],
                          r['new_native_anchors_in_corresponding_source_unit']),(0,1))
        self.assertEqual((r['primary_source_anchor_replacements'],r['native_provisional_claims']),(1,1))
        self.assertFalse(r['independent_precision_recall_measured'])
        self.assertFalse(r['e2_final_pass'])

    def test_02_release_is_fail_closed(self):
        with self.assertRaisesRegex(InvalidInput,'INDEPENDENT_GOLD_AND_AUDIO_NOT_ESTABLISHED'):
            require_e2_release(self.audit())

    def test_03_wrong_source_bytes_rejected(self):
        orig=sha256(self.data['source']);self.data['source']+=b' '
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SOURCE_SHA_DRIFT'):
            self.audit(original_sha_override=orig)

    def test_04_source_only_quote_mismatch(self):
        self.data['source_docket']['claims'][1]['source_refs'][0]['quote']='원금 보장'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_UNIT_QUOTE_AND_CUE_CHANGED'):self.audit()

    def test_05_source_first_cue_missing_fails(self):
        self.data['source_docket']['claims'][2]['source_refs'].pop()
        with self.assertRaisesRegex(InvalidInput,'SOURCE_UNIT_SCHEMA_OR_FALSE_CERTIFICATION'):self.audit()

    def test_06_deceptive_blind_gold_label_fails(self):
        self.data['source_docket']['not_a_blind_gold_dataset']=False
        with self.assertRaisesRegex(InvalidInput,'SOURCE_DOCKET_IDENTITY_OR_FALSE_GOLD'):self.audit()

    def test_07_speaker_promotion_without_audio_fails(self):
        self.data['new_native']['atoms'][0]['speaker']='NARRATOR'
        with self.assertRaisesRegex(InvalidInput,'NATIVE_CLAIMS_CHANGED_OR_SPEAKER_PROMOTED'):self.audit()

    def test_08_fake_native_fact_correction_rejected(self):
        self.data['new_native']['atoms'][0]['proposition']='ETF는 손실 없이 보장됩니다.'
        with self.assertRaisesRegex(InvalidInput,'UNAUTHORIZED_NATIVE_MEANING_FIELD_CHANGED'):self.audit()

    def test_09_wrong_owner_window_when_cue_moves(self):
        self.data['new_native']['atoms'][0]['owner_window_id']='W00002'
        with self.assertRaisesRegex(InvalidInput,'HOST_ATOM_PRIMARY_WINDOW_MISMATCH'):self.audit()

    def test_10_missing_primary_change_in_patch(self):
        self.data['patch']['corrections']=[]
        with self.assertRaisesRegex(InvalidInput,'PATCH_CUSTODY_OR_FALSE_APPROVAL'):self.audit()

    def test_11_patch_quote_changed_detected(self):
        self.data['patch']['corrections'][0]['new_primary_quote']='비공개 근거입니다.'
        with self.assertRaisesRegex(InvalidInput,'PATCH_ROW_SOURCE_OR_MEANING_MISMATCH'):self.audit()

    def test_12_patch_fake_gold_detected(self):
        self.data['patch']['independent_gold']=True
        with self.assertRaisesRegex(InvalidInput,'PATCH_CUSTODY_OR_FALSE_APPROVAL'):self.audit()

    def test_13_source_to_candidate_crosswalk_dropped_detected(self):
        self.data['crosswalk']['rows'][1]['matched_native_ids']=[]
        with self.assertRaisesRegex(InvalidInput,'CROSSWALK_PRIMARY_MISALIGNED_OR_SELF_REPORTED'):self.audit()

    def test_14_crosswalk_false_equivalence_detected(self):
        self.data['crosswalk']['rows'][1]['one_to_one_exact_semantic_equivalence_certified']=True
        with self.assertRaisesRegex(InvalidInput,'CROSSWALK_INVALID_ROW_OR_FAKE_EQUIVALENCE'):self.audit()

    def test_15_crosswalk_missing_cue_unit_detected(self):
        self.data['crosswalk']['rows'].pop()
        with self.assertRaisesRegex(InvalidInput,'CROSSWALK_ROW_INCOMPLETE'):self.audit()

    def test_16_source_gold_false_promotion_detected(self):
        self.data['crosswalk']['independent_gold_certified']=True
        with self.assertRaisesRegex(InvalidInput,'CROSSWALK_SOURCE_OR_FALSE_GOLD'):self.audit()

    def test_17_native_primary_wrong_original_quote_frozen_fails(self):
        self.data['new_native']['atoms'][0]['source_refs'][0]['quote']='ETF는 원금을 보장합니다.'
        with self.assertRaisesRegex(InvalidInput,'HOST_ATOM_QUOTE_NOT_IN_ORIGINAL'):self.audit()

    def test_18_unapproved_financial_numeric_change_rejected(self):
        self.data['new_native']['atoms'][0]['numeric_references']=[{'cue_index':2,'token':'100%'}]
        with self.assertRaises(InvalidInput):self.audit()

    def test_19_source_only_unit_unreviewed_hole_detected(self):
        u=self.data['source_docket']['claims'][2]
        u['cue_end']=3;u['source_refs']=u['source_refs'][:1]
        with self.assertRaisesRegex(InvalidInput,'SOURCE_FIRST_FULL_CUE_COVERAGE_INCOMPLETE'):self.audit()

    def test_20_extra_bogus_patch_claim(self):
        new=copy.deepcopy(self.data['patch']['corrections'][0])
        self.data['patch']['corrections'].append(new)
        with self.assertRaisesRegex(InvalidInput,'PATCH_CUSTODY_OR_FALSE_APPROVAL'):self.audit()

    def test_21_crosswalk_unlisted_native_id_rejected(self):
        self.data['crosswalk']['rows'][1]['matched_native_ids']=['C99999']
        with self.assertRaisesRegex(InvalidInput,'CROSSWALK_INVALID_ROW_OR_FAKE_EQUIVALENCE'):self.audit()

    def test_22_hash_pin_requires_exact_published_bytes(self):
        b={k:(v if k=='source' else encoded(v)) for k,v in self.data.items()}
        original_crosswalk_hash=sha256(b['crosswalk'])
        b['crosswalk']+=b' '
        hashes={k:sha256(v) for k,v in b.items()}
        hashes['crosswalk']=original_crosswalk_hash
        kwargs=dict(expected_hashes=hashes,window_size=2)
        with self.assertRaisesRegex(InvalidInput,'CROSSWALK_SOURCE_SHA_DRIFT'):
            audit_source_first_native_alignment(
                b['source'],self.data['source_docket'],b['source_docket'],
                self.data['old_native'],b['old_native'],
                self.data['new_native'],b['new_native'],
                self.data['patch'],b['patch'],self.data['crosswalk'],b['crosswalk'],**kwargs)

if __name__=='__main__':unittest.main()