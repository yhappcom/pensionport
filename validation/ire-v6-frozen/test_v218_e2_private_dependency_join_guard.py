"""V218 public CI uses synthetic ETF language only; no real owner SRT."""
from __future__ import annotations
import copy
import json
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from test_v217_e2_private_crosscue_discourse_guard import RAW
from v218_e2_private_dependency_join_guard import (
    audit_private_cross_atom_join,prepare_research_dependency_closure,
    require_approved_handoff,SCHEMA,
)


class TestV218PrivateDependencyJoinGuard(unittest.TestCase):
    @staticmethod
    def encode(value):
        return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

    def setUp(self):
        from test_v217_e2_private_crosscue_discourse_guard import TestV217CrossCueDiscourseGuard
        fixture=TestV217CrossCueDiscourseGuard()
        fixture.setUp()
        self.exchange=fixture.exchange
        self.ledger=fixture.ledger
        self.prior=fixture.audit()
        native_sha=sha256(self.encode(self.exchange))
        self.coverage={
            'source_sha256':sha256(RAW),
            'new_native_v6_exchange_sha256':native_sha,
            'full_original_cue_count':len(fixture.source.cues),
            'independent_gold_certified':False,'e2_final_pass':False,
            'cues':[
                {'cue_index':i,'original_text':c.text,
                 'cue_text_sha256':sha256(c.text.encode('utf-8')),
                 'needs_original_audio_or_screen':i==4}
                for i,c in enumerate(fixture.source.cues,1)]
        }
        rows=[]
        assignments=[('LINKED_UNAPPROVED','C00001','C00002'),
                     ('INTRA_ATOM_UNAPPROVED','C00001','C00001'),
                     ('QUARANTINE_VISUAL_UNVERIFIED',None,None)]
        for rel,(state,a,b) in zip(self.ledger['relations'],assignments):
            rows.append({'relation_id':rel['relation_id'],
              'source_cue':rel['from_cue'],'target_cue':rel['to_cue'],
              'relation_type':rel['relation_type'], 'review_state':state,
              'source_atom_id':a,'target_atom_id':b,
              'reviewer_note':'원문의 발언과 그 범위를 분리해 검토한 미승인 관계',
              'is_external_gold':False,'speaker_audio_verified':False,
              'video_frame_verified':False,'financial_fact_approved':False,
              'final_semantic_approval':False,
              'knowledge_publication_authorized':False})
        self.review={
            'schema':SCHEMA,'video_id':self.exchange['video_id'],
            'source_sha256':sha256(RAW),
            'native_exchange_sha256':native_sha,
            'original_relation_ledger_sha256':sha256(self.encode(self.ledger)),
            'prior_v217_relationship_receipt_sha256':sha256(self.encode(self.prior)),
            'coverage_sha256':sha256(self.encode(self.coverage)),
            'review_author':'CHATGPT_SOURCE_TEXT_ONLY_REVIEW',
            'total_original_relations':3,
            'cross_atom_edges_reviewed':1,'intra_atom_context_reviewed':1,
            'visual_quarantines_reviewed':1,
            'speaker_audio_available':False,'video_frames_available':False,
            'old_v176_owner_sqlite_available':False,
            'independent_gold_available':False,'e2_final_pass':False,
            'e3_e4_e5_authorized':False,
            'knowledge_publication_authorized':False,
            'rows':rows}

    def run_guard(self,ex=None,ledger=None,prior=None,coverage=None,review=None,
                  source=RAW, overrides=None):
        ex=self.exchange if ex is None else ex
        ledger=self.ledger if ledger is None else ledger
        prior=self.prior if prior is None else prior
        coverage=self.coverage if coverage is None else coverage
        review=self.review if review is None else review
        raw={k:self.encode(obj) for k,obj in (
          ('exchange',ex),('ledger',ledger),('prior',prior),
          ('coverage',coverage),('review',review))}
        sha={k:sha256(v) for k,v in raw.items()}
        if overrides:
            for k,v in overrides.items():sha[k]=v
        return audit_private_cross_atom_join(source,ex,raw['exchange'],
            ledger,raw['ledger'],prior,raw['prior'],coverage,raw['coverage'],
            review,raw['review'],expected_source_sha256=sha256(RAW),
            expected_exchange_sha256=sha['exchange'],
            expected_ledger_sha256=sha['ledger'],
            expected_prior_receipt_sha256=sha['prior'],
            expected_coverage_sha256=sha['coverage'],
            expected_review_sha256=sha['review'],window_size=2)

    def test_01_all_three_source_relations_have_explicit_fate(self):
        x=self.run_guard()
        self.assertEqual((x['relations_total'],x['cross_atom_linked_unapproved'],
                          x['same_atom_context_unapproved'],x['audio_video_quarantined']),
                         (3,1,1,1))
        self.assertEqual(x['unreviewed_relations'],0)
        self.assertFalse(x['e2_final_pass'])
        self.assertFalse(x['financial_facts_approved'])
        self.assertNotIn('ETF는 펀드',str(x))

    def test_02_unreviewed_row_dropped_fails_closed(self):
        d=copy.deepcopy(self.review);d['rows'].pop()
        with self.assertRaisesRegex(InvalidInput,'REVIEW_HEADER_OR_APPROVAL_FALSIFICATION'):
            self.run_guard(review=d)

    def test_03_cross_atom_endpoint_not_at_source_rejected(self):
        d=copy.deepcopy(self.review);d['rows'][0]['target_atom_id']='C00001'
        with self.assertRaisesRegex(InvalidInput,'CROSS_ATOM_ENDPOINT_NOT_SOURCE_LINKED'):
            self.run_guard(review=d)

    def test_04_wrong_single_atom_claim_id_rejected(self):
        d=copy.deepcopy(self.review);d['rows'][1]['source_atom_id']='C00002'
        d['rows'][1]['target_atom_id']='C00002'
        with self.assertRaisesRegex(InvalidInput,'INTRA_ATOM_CUE_NOT_SHARED'):
            self.run_guard(review=d)

    def test_05_visual_flag_removed_prevents_unverified_drop(self):
        c=copy.deepcopy(self.coverage)
        c['cues'][3]['needs_original_audio_or_screen']=False
        d=copy.deepcopy(self.review)
        d['coverage_sha256']=sha256(self.encode(c))
        with self.assertRaisesRegex(InvalidInput,'UNMAPPED_VISUAL_EVIDENCE_NOT_HELD'):
            self.run_guard(coverage=c,review=d)

    def test_06_visual_held_row_cannot_be_pretend_linked(self):
        d=copy.deepcopy(self.review);d['rows'][2]['review_state']='LINKED_UNAPPROVED'
        with self.assertRaisesRegex(InvalidInput,'REVIEW_STATE_CUSTODY_DRIFT'):
            self.run_guard(review=d)

    def test_07_owner_original_source_bytes_modified_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_SOURCE_BYTES_CHANGED'):
            self.run_guard(source=RAW+b' ')

    def test_08_changed_private_native_bytes_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'NATIVE_ORIGINAL_BYTES_CHANGED'):
            self.run_guard(overrides={'exchange':'f'*64})

    def test_09_changed_original_ledger_bytes_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'LEDGER_ORIGINAL_BYTES_CHANGED'):
            self.run_guard(overrides={'ledger':'f'*64})

    def test_10_changed_prior_receipt_bytes_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'PRIOR_ORIGINAL_BYTES_CHANGED'):
            self.run_guard(overrides={'prior':'f'*64})

    def test_11_changed_coverage_bytes_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'COVERAGE_ORIGINAL_BYTES_CHANGED'):
            self.run_guard(overrides={'coverage':'f'*64})

    def test_12_changed_review_bytes_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'REVIEW_ORIGINAL_BYTES_CHANGED'):
            self.run_guard(overrides={'review':'f'*64})

    def test_13_no_false_independent_gold_allowed(self):
        d=copy.deepcopy(self.review);d['independent_gold_available']=True
        with self.assertRaisesRegex(InvalidInput,'REVIEW_HEADER_OR_APPROVAL_FALSIFICATION'):
            self.run_guard(review=d)

    def test_14_source_video_approval_flag_cannot_be_forged(self):
        d=copy.deepcopy(self.review);d['rows'][2]['video_frame_verified']=True
        with self.assertRaisesRegex(InvalidInput,'REVIEW_RELATION_SOURCE_OR_FALSE_APPROVAL'):
            self.run_guard(review=d)

    def test_15_cross_atom_closure_requires_joined_context(self):
        result=prepare_research_dependency_closure(['C00002'],self.run_guard())
        self.assertEqual(result['mandatory_context_atom_ids'],['C00001','C00002'])
        self.assertEqual(result['media_evidence_quarantine_relation_ids'],['V217R-003'])
        self.assertEqual(result['intra_atom_relation_ids'],['V217R-002'])
        self.assertTrue(result['media_quarantine_present'])
        self.assertFalse(result['knowledge_approval_authorized'])

    def test_16_unknown_atom_cannot_get_context(self):
        with self.assertRaisesRegex(InvalidInput,'RESEARCH_UNKNOWN_ATOM_NO_PROVEN_CONTEXT'):
            prepare_research_dependency_closure(['C99999'],self.run_guard())

    def test_17_graph_receipt_never_automatically_approves(self):
        with self.assertRaisesRegex(InvalidInput,'INDEPENDENT_GOLD_AND_MEDIA_EVIDENCE_REQUIRED'):
            require_approved_handoff(self.run_guard())

    def test_18_extra_unknown_review_row_schema_rejected(self):
        d=copy.deepcopy(self.review)
        d['rows'][0]['experimental_allow_approval']=True
        with self.assertRaisesRegex(InvalidInput,'REVIEW_ROW_FIELDS'):
            self.run_guard(review=d)

    def test_19_wrong_source_cue_index_rejected(self):
        d=copy.deepcopy(self.review);d['rows'][0]['source_cue']=4
        with self.assertRaisesRegex(InvalidInput,'REVIEW_RELATION_SOURCE_OR_FALSE_APPROVAL'):
            self.run_guard(review=d)

    def test_20_repeat_same_original_input_same_receipt(self):
        self.assertEqual(self.run_guard(),self.run_guard())

    def test_21_visual_source_atom_lineage_not_silently_dropped(self):
        receipt=self.run_guard()
        self.assertEqual(receipt['evidence_quarantines'][0]['origin_atom_ids'],
                         ['C00002'])
        result=prepare_research_dependency_closure(['C00002'],receipt)
        self.assertIn('V217R-003',result['media_evidence_quarantine_relation_ids'])

    def test_22_unsafe_mutation_of_quarantine_origin_rejected_on_bundle(self):
        receipt=self.run_guard()
        receipt['evidence_quarantines'][0]['origin_atom_ids']=[777]
        with self.assertRaisesRegex(InvalidInput,'VISUAL_QUARANTINE_RECEIPT_UNTRUSTED'):
            prepare_research_dependency_closure(['C00002'],receipt)



if __name__=='__main__':
    unittest.main()