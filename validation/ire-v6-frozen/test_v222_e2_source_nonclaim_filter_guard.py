"""Synthetic-only regressions: no private SRT and no independent gold in CI."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from test_v221_e2_source_first_semantic_anchor_guard import make_fixture, RAW
from v222_e2_source_nonclaim_filter_guard import (
    audit_source_first_nonclaim_filter, require_approved_e2_disposition,
)


def encode(d):
    return (json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def fixture():
    base=make_fixture()
    raw=base['source'];source,_=make_original_plan(raw,'Synth123456',
              expected_source_sha256=sha256(raw),window_size=2)
    old=copy.deepcopy(base['new_native'])
    old['atoms'].append({
        'claim_id':'C00002','owner_window_id':source.owner(1),
        'proposition':'ETF를 선택할 여섯 기준을 설명하겠습니다.',
        'kind':'RECOMMENDATION','stance':'UNRESOLVED','speaker':'UNKNOWN',
        'source_refs':[{'cue_index':1,'quote':source.cues[0].text}],
        'context_cue_indices':[1], 'condition_cue_indices':[],
        'exception_cue_indices':[],'numeric_references':[], 'as_of':None,
    })
    old['cue_dispositions'][0]['disposition']='CANDIDATES'
    old['cue_dispositions'][0]['claim_ids']=['C00002']
    audit_host_atomic_exchange(source,old)
    new=copy.deepcopy(old)
    new['atoms']=[a for a in new['atoms'] if a['claim_id']!='C00002']
    new['cue_dispositions'][0]['disposition']='NO_ATOM'
    new['cue_dispositions'][0]['claim_ids']=[]
    new['cue_dispositions'][0]['note']='원문은 다음 강의로 넘어가는 안내 발화로 독립 정답 확인 전까지 비주장 잠정'
    audit_host_atomic_exchange(source,new)
    dossier=copy.deepcopy(base['source_docket'])
    graph={
        'schema':'IRE_V218_E2_SOURCE_PINNED_UNAPPROVED_DEPENDENCY_GRAPH_V1',
        'source_sha256':sha256(raw),'cross_atom_edges':[],
        'same_atom_relations':[],'evidence_quarantines':[],
        'relations_total':0,'cross_atom_linked_unapproved':0,
        'same_atom_context_unapproved':0,'audio_video_quarantined':0,
        'source_relation_lineage_complete':True, 'unreviewed_relations':0,
        'same_source_quoted_semantic_gold_independent':False,
        'speaker_audio_verified':False,'video_screen_verified':False,
        'financial_facts_approved':False,'e2_final_pass':False,
    }
    oldclaim=next(a for a in old['atoms'] if a['claim_id']=='C00002')
    item={
        'claim_id':'C00002','source_only_id':'SRC221-001',
        'source_cue_start':1,'source_cue_end':1,
        'source_cues':[{'cue_index':1,'quote':source.cues[0].text,
                        'sha256':sha256(source.cues[0].text.encode())}],
        'previous_claim':copy.deepcopy(oldclaim),
        'previous_cue_disposition':copy.deepcopy(old['cue_dispositions'][0]),
        'corrected_cue_disposition':copy.deepcopy(new['cue_dispositions'][0]),
        'rejection_code':'NARRATIVE_INTRODUCTION_NOT_FINANCIAL_RECOMMENDATION',
        'reason':'원문이 예고나 안내라는 내부 판정이며 ETF 매매 권유는 포함되지 않는다.',
        'speaker_audio_verified':False,'financial_truth_approved':False,
        'independent_gold_verified':False,
    }
    review={
        'schema':'IRE_V222_PRIVATE_ETF_SOURCE_FIRST_NONCLAIM_NEGATIVE_ADJUDICATION_V1',
        'video_id':old['video_id'],'source_sha256':sha256(raw),
        'old_native_sha256':sha256(encode(old)),
        'new_native_sha256':sha256(encode(new)),
        'source_docket_sha256':sha256(encode(dossier)),
        'prior_cross_atom_graph_sha256':sha256(encode(graph)),
        'review_context':'SAME_CHATGPT_INTERNAL_SOURCE_FIRST_AFTER_PRIOR_ENGINE_EXPOSURE_NOT_INDEPENDENT_GOLD',
        'decisions':[item],'rejected_native_claim_count':1,
        'native_before':2,'native_after':1,
        'other_native_atoms_modified':False,'other_discourse_edges_modified':False,
        'independent_gold_certified':False,'claim_omission_gold_certified':False,
        'financial_facts_approved':False,'e2_final_pass':False,
        'e3_e4_e5_authorized':False,'knowledge_published':False,
    }
    return dict(source=raw,old_native=old,new_native=new,source_docket=dossier,
                negative_review=review,relation_graph=graph)


class TestV222SourceFirstNegativeClaim(unittest.TestCase):
    def setUp(self):
        self.x=fixture()

    def audit(self,hash_override=None):
        data={k:(v if k=='source' else encode(v)) for k,v in self.x.items()}
        h={k:sha256(v) for k,v in data.items()}
        if hash_override:h.update(hash_override)
        d=self.x
        return audit_source_first_nonclaim_filter(
            d['source'],d['old_native'],data['old_native'],
            d['new_native'],data['new_native'],
            d['source_docket'],data['source_docket'],
            d['negative_review'],data['negative_review'],
            d['relation_graph'],data['relation_graph'],
            expected_hashes=h,window_size=2)

    def test_01_valid_synthetic_drops_only_intro_not_gold(self):
        r=self.audit()
        self.assertEqual((r['previous_native_atom_count'],r['corrected_native_atom_count']),(2,1))
        self.assertEqual(r['removed_atom_ids'],['C00002'])
        self.assertFalse(r['e2_final_pass'])
        self.assertFalse(r['independent_gold_certified'])

    def test_02_noatom_keeps_suspicious_risk_for_review(self):
        r=self.audit()
        self.assertEqual(r['corrected_primary_cues'],1)
        self.assertFalse(r['knowledge_published'])

    def test_03_future_e3_release_requires_separate_gold(self):
        with self.assertRaisesRegex(InvalidInput,'GOLD_SPEAKER_AND_FINANCIAL_EVIDENCE_NOT_VERIFIED'):
            require_approved_e2_disposition(self.audit())

    def test_04_original_source_mutation_rejected(self):
        old=sha256(self.x['source']);self.x['source']+=b' '
        with self.assertRaisesRegex(InvalidInput,'PINNED_SOURCE_BYTES_CHANGED'):
            self.audit({'source':old})

    def test_05_original_quote_change_detected(self):
        self.x['source_docket']['claims'][0]['source_refs'][0]['quote']='원금 보장'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_UNIT_QUOTE_AND_SHA_MISMATCH'):
            self.audit()

    def test_06_rejected_intro_not_supported_if_source_unit_fact(self):
        self.x['source_docket']['claims'][0]['discourse_kind']='FACT_AS_SPOKEN'
        self.x['negative_review']['source_docket_sha256']=sha256(encode(self.x['source_docket']))
        with self.assertRaisesRegex(InvalidInput,'FINANCIAL_CLAIM_NOT_A_PURE_INTRODUCTION'):
            self.audit()

    def test_07_no_removal_without_specific_decision(self):
        self.x['negative_review']['decisions']=[]
        self.x['negative_review']['rejected_native_claim_count']=0
        with self.assertRaisesRegex(InvalidInput,'NEGATIVE_REVIEW_CENSUS'):
            self.audit()

    def test_08_duplicate_review_decision_fails(self):
        self.x['negative_review']['decisions'].append(copy.deepcopy(self.x['negative_review']['decisions'][0]))
        self.x['negative_review']['rejected_native_claim_count']=2
        with self.assertRaises(InvalidInput):self.audit()

    def test_09_surviving_fact_mutation_rejected(self):
        self.x['new_native']['atoms'][0]['proposition']='ETF가 반드시 원금을 보장합니다.'
        self.x['negative_review']['new_native_sha256']=sha256(encode(self.x['new_native']))
        with self.assertRaisesRegex(InvalidInput,'UNAPPROVED_NATIVE_ATOM_LOSS_OR_MUTATION'):
            self.audit()

    def test_10_multiple_native_atoms_removed_without_review_fails(self):
        self.x['new_native']['atoms']=[]
        with self.assertRaises(InvalidInput):self.audit()

    def test_11_rejected_candidate_wrong_kind(self):
        self.x['old_native']['atoms'][1]['kind']='FACT'
        self.x['negative_review']['old_native_sha256']=sha256(encode(self.x['old_native']))
        self.x['negative_review']['decisions'][0]['previous_claim']['kind']='FACT'
        with self.assertRaisesRegex(InvalidInput,'FINANCIAL_CLAIM_NOT_A_PURE_INTRODUCTION'):
            self.audit()

    def test_12_media_or_history_graph_edge_prevents_silent_removal(self):
        graph=self.x['relation_graph']
        graph['cross_atom_edges']=[{'from_atom_id':'C00002','to_atom_id':'C00001'}]
        graph['relations_total']=graph['cross_atom_linked_unapproved']=1
        self.x['negative_review']['prior_cross_atom_graph_sha256']=sha256(encode(graph))
        with self.assertRaisesRegex(InvalidInput,'REMOVED_ATOM_HAS_LIVE_DISCOURSE_EDGE'):
            self.audit()

    def test_13_graph_relation_census_missing_blocks(self):
        graph=self.x['relation_graph'];graph['evidence_quarantines']=[{'cue_index':3}]
        self.x['negative_review']['prior_cross_atom_graph_sha256']=sha256(encode(graph))
        with self.assertRaisesRegex(InvalidInput,'GRAPH_SOURCE_OR_FALSE_APPROVAL_OR_CENSUS'):
            self.audit()

    def test_14_noatom_cannot_be_silent_unresolved(self):
        self.x['new_native']['cue_dispositions'][0]['disposition']='UNRESOLVED'
        self.x['negative_review']['new_native_sha256']=sha256(encode(self.x['new_native']))
        self.x['negative_review']['decisions'][0]['corrected_cue_disposition']['disposition']='UNRESOLVED'
        with self.assertRaisesRegex(InvalidInput,'UNAUTHORIZED_NONCLAIM_CUE_REWRITE'):
            self.audit()

    def test_15_remove_original_number_census_no_silent_mutation(self):
        self.x['new_native']['cue_dispositions'][0]['numeric_tokens']=['1억원']
        self.x['negative_review']['new_native_sha256']=sha256(encode(self.x['new_native']))
        with self.assertRaises(InvalidInput):self.audit()

    def test_16_change_unrelated_cue_without_review(self):
        self.x['new_native']['cue_dispositions'][3]['note']='변조된 다른 원문 주석'
        self.x['negative_review']['new_native_sha256']=sha256(encode(self.x['new_native']))
        with self.assertRaisesRegex(InvalidInput,'UNREVIEWED_CUE_DISPOSITION_CHANGE'):
            self.audit()

    def test_17_docket_false_independent_gold(self):
        self.x['source_docket']['not_a_blind_gold_dataset']=False
        self.x['negative_review']['source_docket_sha256']=sha256(encode(self.x['source_docket']))
        with self.assertRaisesRegex(InvalidInput,'SOURCE_DOCKET_NOT_INDEPENDENT_OR_CHANGED'):
            self.audit()

    def test_18_negative_event_false_approval(self):
        self.x['negative_review']['e2_final_pass']=True
        with self.assertRaisesRegex(InvalidInput,'NEGATIVE_REVIEW_INVALID_OR_FALSE_GOLD'):
            self.audit()

    def test_19_negative_event_fake_gold_independence(self):
        self.x['negative_review']['independent_gold_certified']=True
        with self.assertRaisesRegex(InvalidInput,'NEGATIVE_REVIEW_INVALID_OR_FALSE_GOLD'):
            self.audit()

    def test_20_negative_decision_source_quote_modified(self):
        self.x['negative_review']['decisions'][0]['source_cues'][0]['quote']='불특정 가짜 발언'
        with self.assertRaisesRegex(InvalidInput,'REJECTION_SOURCE_QUOTE_CHANGED'):
            self.audit()

    def test_21_negative_decision_previous_claim_forged(self):
        self.x['negative_review']['decisions'][0]['previous_claim']['proposition']='허위 표시된 주장'
        with self.assertRaisesRegex(InvalidInput,'FINANCIAL_CLAIM_NOT_A_PURE_INTRODUCTION'):
            self.audit()

    def test_22_negative_decision_corrected_cue_forged(self):
        self.x['negative_review']['decisions'][0]['corrected_cue_disposition']['note']='변조'
        with self.assertRaisesRegex(InvalidInput,'UNAUTHORIZED_NONCLAIM_CUE_REWRITE'):
            self.audit()

    def test_23_wrong_source_unit_cue_index_detected(self):
        self.x['negative_review']['decisions'][0]['source_cue_start']=2
        with self.assertRaisesRegex(InvalidInput,'FINANCIAL_CLAIM_NOT_A_PURE_INTRODUCTION'):
            self.audit()

    def test_24_no_forced_speaker_or_stance_promotion(self):
        self.x['new_native']['atoms'][0]['speaker']='NARRATOR'
        self.x['negative_review']['new_native_sha256']=sha256(encode(self.x['new_native']))
        with self.assertRaises(InvalidInput):self.audit()

    def test_25_incomplete_source_unit_coverage_blocked(self):
        self.x['source_docket']['claims'][-1]['cue_end']=3
        self.x['source_docket']['claims'][-1]['source_refs']=self.x['source_docket']['claims'][-1]['source_refs'][:-1]
        self.x['negative_review']['source_docket_sha256']=sha256(encode(self.x['source_docket']))
        with self.assertRaisesRegex(InvalidInput,'SOURCE_UNIT_CUE_COVERAGE_GAP'):
            self.audit()

    def test_26_deterministic_replay_produces_same_digest(self):
        self.assertEqual(self.audit(),self.audit())

    def test_27_context_speaker_assertion_without_audio_never_passes(self):
        self.x['new_native']['atoms'][0]['stance']='AFFIRMED'
        self.x['negative_review']['new_native_sha256']=sha256(encode(self.x['new_native']))
        with self.assertRaises(InvalidInput):self.audit()


if __name__=='__main__':unittest.main()