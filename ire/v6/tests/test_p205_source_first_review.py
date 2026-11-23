"""Synthetic adversarial tests for source-only candidate integrity and topic-only crosswalk.

No owner source SRT/claim wording stored here, no claim of independent gold.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source_first_review import (
    verify_source_first_draft, verify_diagnostic_topic_crosswalk,
)


def _encode(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf8')


def _source():
    source='''1
00:00:01,000 --> 00:00:01,800
ETF fees may exist.

2
00:00:02,000 --> 00:00:02,800
A specific condition matters.

3
00:00:03,000 --> 00:00:03,800
A hypothetical price is shown.

4
00:00:04,000 --> 00:00:04,800
It is only an example.'''
    return source.encode('utf8')


def _draft(source):
    blocks=re.split(r'\n\s*\n',source.decode('utf8').strip())
    cues=[' '.join(b.splitlines()[2:]) for b in blocks]
    def a(i,low,high,kind,risk):
        return {'candidate_id':f'P205-SRC-{i:03d}', 'kind':kind,
                'source_proposition':'Provisional cue-anchored explanation',
                'source_span':{'first_cue':low,'last_cue':high},
                'primary_quote':{'cue_index':low,'quote':cues[low-1],
                                 'quote_sha256':sha256(cues[low-1].encode('utf8')),
                                 'cue_block_sha256':sha256(blocks[low-1].encode('utf8'))},
                'risk_scope':risk, 'qualifier_or_unresolved_issue':'Synthetic claim with no external truth certification',
                'speaker_audio_authenticated':False,'source_semantic_provisional':True,
                'proposition_externally_financial_verified':False,'independent_blind_gold_certified':False}
    rows=[]
    for i,b in enumerate(blocks,1):
        ids=['P205-SRC-001'] if i<=2 else ['P205-SRC-002']
        rows.append({'cue_index':i,'cue_sha256':sha256(b.encode('utf8')),
                     'quote_sha256':sha256(cues[i-1].encode('utf8')),
                     'source_provisional_status':'CONTEXT_OR_PRIMARY_FOR_PROVISIONAL_ATOMS',
                     'status_reason':'Cue used for synthetic provisional proposition',
                     'provisional_candidate_ids':ids,
                     'independent_review_done':False,'no_unmodelled_claims_certified':False})
    return {'schema':'IRE_P205_SOURCE_ONLY_PROVISIONAL_ATOMS_UNBLINDED_CHAT_REVIEW_V1',
            'source_srt_sha256':sha256(source),'semantic_reviewer':'SAME_CHATGPT_CONVERSATION_NONINDEPENDENT',
            'gold_status':'PROVISIONAL_SOURCE_READING_NOT_INDEPENDENT_GOLD',
            'speaker_audio_authenticated':False,'fully_independent_source_blind':False,
            'second_blind_reviewer_verified':False,'owner_finance_truth_certified':False,
            'measured_atomic_precision':None,'measured_atomic_recall':None,'measured_high_risk_FN':None,
            'reviewed_original_cue_count':4,'source_provisional_atom_count':2,
            'source_provisional_high_risk_atom_count':1,
            'provisional_atoms':[a(1,1,2,'FACT','HIGH'),a(2,3,4,'HYPOTHETICAL','LOW')],
            'cue_coverage':rows,
            'source_cue_status_counts':{'CONTEXT_OR_PRIMARY_FOR_PROVISIONAL_ATOMS':4},
            'unlinked_cue_indices':[]}


def _native():
    return {'schema':'SYNTHETIC_NATIVE_V1','atoms':[
        {'claim_id':'C00001','kind':'FACT'},
        {'claim_id':'C00002','kind':'HYPOTHETICAL'}]}


def _crosswalk(d,n,nraw):
    return {'schema':'IRE_P205_SAME_CHAT_SOURCE71_NATIVE68_DIAGNOSTIC_RELATIONS_NON_GOLD_V1',
            'provisional_source_first_json_sha256':sha256(_encode(d)),
            'native_v228_json_sha256':sha256(nraw),
            'source_srt_sha256':d['source_srt_sha256'],
            'is_gold':False,'is_independent_review':False,
            'automatic_gold_matching_approved':False,
            'all_250_cue_atomic_exhaustiveness_proven':False,'metrics_must_remain_null':True,
            'source_to_native_related_review_only':[
                {'source_provisional_id':f'P205-SRC-{i:03d}',
                 'source_quote_cue':(1 if i==1 else 3),
                 'source_kind':('FACT' if i==1 else 'HYPOTHETICAL'),
                 'source_risk':('HIGH' if i==1 else 'LOW'),
                 'native_related_claim_ids_for_review_only':[f'C0000{i}'],
                 'source_new_candidate_missing_standalone_native':False,
                 'requires_one_to_many_candidate_split_review':False,
                 'same_kind_as_all_related':True,
                 'independently_gold_aligned':False,'true_positive_match':None}
                for i in [1,2]],
            'native_to_source_related_review_only':[
                {'native_claim_id':f'C0000{i}',
                 'source_provisional_related_ids':[f'P205-SRC-{i:03d}'],
                 'related_to_multiple_source_atoms':False,
                 'independent_atomic_alignment_complete':False,
                 'gold_truth_label':None} for i in [1,2]],
            'provisional_kind_disagreement_pairs':[],
            'summary':{'source_candidate_count':2,'original_frozen_native_count':2,
                       'source_candidate_without_separate_native_topic_link':0,
                       'unlinked_native_candidates':0,
                       'source_candidates_related_to_multiple_native_claims':0,
                       'native_candidates_related_to_multiple_source_candidates':0,
                       'provisional_source_native_kind_disagreements_in_related_pairs':0,
                       'actual_TP':None,'actual_FP':None,'actual_FN':None,
                       'actual_high_risk_FN':None,'precision':None,'recall':None}}


class ProvisionalSourceFirstTests(unittest.TestCase):
    def setUp(self):
        self.raw=_source()
        self.draft=_draft(self.raw)
        self.native=_native()

    def src(self,d=None,raw=None,**args):
        x=self.draft if d is None else d
        b=_encode(x)
        original=self.raw if raw is None else raw
        return verify_source_first_draft(original,b,expected_source_sha256=sha256(self.raw),
                      expected_candidate_sha256=sha256(b),
                      expected_cues=4,expected_candidates=2,**args)
    def cross(self,*,mutate=None,d=None,n=None):
        doc=self.draft if d is None else d
        original=self.native if n is None else n
        nbytes=_encode(original)
        c=_crosswalk(doc,original,nbytes)
        if mutate:mutate(c)
        cbytes=_encode(c)
        return verify_diagnostic_topic_crosswalk(nbytes,_encode(doc),cbytes,
               expected_native_sha256=sha256(nbytes),
               expected_candidate_sha256=sha256(_encode(doc)),
               expected_crosswalk_sha256=sha256(cbytes))
    def bad_draft(self,mutate,name='P205_SOURCE_FIRST_'):
        d=copy.deepcopy(self.draft);mutate(d)
        with self.assertRaisesRegex(InvalidInput,name):self.src(d)
    def bad_cross(self,mutate,name='P205_SOURCE_FIRST_'):
        with self.assertRaisesRegex(InvalidInput,name):self.cross(mutate=mutate)

    def test_01_positive_exact_source_and_quote_synthetic(self):
        r=self.src()
        self.assertEqual(r['provisional_candidate_quote_hashes_verified'],2)
        self.assertFalse(r['p0_go'])
        self.assertIsNone(r['independent_atomic_recall'])
    def test_02_original_source_byte_mutation_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_SRT_SHA'):
            self.src(raw=self.raw.replace(b'ETF',b'ETX'))
    def test_03_self_reported_gold_forbidden(self):
        self.bad_draft(lambda d:d.update(gold_status='INDEPENDENT_GOLD_CERTIFIED'))
    def test_04_same_session_is_not_independent(self):
        self.bad_draft(lambda d:d.update(fully_independent_source_blind=True))
    def test_05_fake_second_reviewer(self):
        self.bad_draft(lambda d:d.update(second_blind_reviewer_verified=True))
    def test_06_fake_financial_truth(self):
        self.bad_draft(lambda d:d.update(owner_finance_truth_certified=True))
    def test_07_fabricated_recall(self):
        self.bad_draft(lambda d:d.update(measured_atomic_recall=1))
    def test_08_fabricated_precision(self):
        self.bad_draft(lambda d:d.update(measured_atomic_precision=1))
    def test_09_fabricated_highrisk_zero(self):
        self.bad_draft(lambda d:d.update(measured_high_risk_FN=0))
    def test_10_missing_250_source_cue_analog(self):
        self.bad_draft(lambda d:d['cue_coverage'].pop())
    def test_11_extra_duplicate_cue(self):
        self.bad_draft(lambda d:d['cue_coverage'].insert(1,copy.deepcopy(d['cue_coverage'][0])))
    def test_12_fabricated_quote(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0]['primary_quote'].update(quote='not in source'))
    def test_13_corrupt_primary_quote_sha(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0]['primary_quote'].update(quote_sha256='0'*64))
    def test_14_corrupt_block_sha(self):
        self.bad_draft(lambda d:d['cue_coverage'][0].update(cue_sha256='0'*64))
    def test_15_unknown_cue_anchor(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0]['primary_quote'].update(cue_index=99))
    def test_16_missing_context_cue_links(self):
        self.bad_draft(lambda d:d['cue_coverage'][1].update(provisional_candidate_ids=[]))
    def test_17_fabricated_extra_context_atom(self):
        self.bad_draft(lambda d:d['cue_coverage'][0].update(provisional_candidate_ids=['P205-SRC-001','P205-SRC-002']))
    def test_18_duplicate_unchanged_claim_ids(self):
        self.bad_draft(lambda d:d['provisional_atoms'][1].update(candidate_id='P205-SRC-001'))
    def test_19_highrisk_census_hidden(self):
        self.bad_draft(lambda d:d.update(source_provisional_high_risk_atom_count=0))
    def test_20_change_source_claim_kind_to_wrong_label(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0].update(kind='UNREVIEWED'))
    def test_21_mark_primary_claim_cue_as_NONCLAIM(self):
        self.bad_draft(lambda d:d['cue_coverage'][0].update(source_provisional_status='NONCLAIM_DISCUSSION'))
    def test_22_forged_independent_cue_review(self):
        self.bad_draft(lambda d:d['cue_coverage'][0].update(independent_review_done=True))
    def test_23_forged_zero_missing_atoms(self):
        self.bad_draft(lambda d:d['cue_coverage'][0].update(no_unmodelled_claims_certified=True))
    def test_24_wrong_role_census(self):
        self.bad_draft(lambda d:d.update(source_cue_status_counts={'CONTEXT_OR_PRIMARY_FOR_PROVISIONAL_ATOMS':3}))
    def test_25_positive_topic_links_still_NOT_GOLD(self):
        r=self.cross()
        self.assertEqual(r['source_candidate_count'],2)
        self.assertIsNone(r['independent_precision'])
        self.assertFalse(r['crosswalk_is_independent_gold'])
    def test_26_forged_exact_TP(self):
        self.bad_cross(lambda c:c['source_to_native_related_review_only'][0].update(true_positive_match=True))
    def test_27_forged_gold_flag(self):
        self.bad_cross(lambda c:c.update(is_gold=True))
    def test_28_missed_native_reverse(self):
        self.bad_cross(lambda c:c['native_to_source_related_review_only'][0].update(source_provisional_related_ids=[]))
    def test_29_hidden_unlinked_relation(self):
        self.bad_cross(lambda c:c['source_to_native_related_review_only'][0].update(native_related_claim_ids_for_review_only=[]))
    def test_30_kind_disagreement_forged(self):
        self.bad_cross(lambda c:c['source_to_native_related_review_only'][0].update(source_kind='OPINION'))
    def test_31_native_duplicate_source_id(self):
        self.bad_cross(lambda c:c['source_to_native_related_review_only'][1].update(source_provisional_id='P205-SRC-001'))
    def test_32_forged_all_predictions_matched_as_true_gold(self):
        self.bad_cross(lambda c:c.update(metrics_must_remain_null=False))
    def test_33_fake_precision_from_topic_only(self):
        self.bad_cross(lambda c:c['summary'].update(precision=1))
    def test_34_fake_highrisk_FN_zero(self):
        self.bad_cross(lambda c:c['summary'].update(actual_high_risk_FN=0))
    def test_35_hidden_split_review(self):
        self.bad_cross(lambda c:c['source_to_native_related_review_only'][0].update(requires_one_to_many_candidate_split_review=True))
    def test_36_false_status_of_source_draft_independent(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0].update(independent_blind_gold_certified=True))
    def test_37_forged_candidate_quote_block(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0]['primary_quote'].update(cue_block_sha256='0'*64))
    def test_38_unlinked_source_claim_not_silenced(self):
        self.bad_draft(lambda d:d['provisional_atoms'][0]['source_span'].update(last_cue=1))


if __name__=='__main__':
    unittest.main()
