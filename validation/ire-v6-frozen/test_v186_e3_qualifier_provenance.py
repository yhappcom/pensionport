"""Synthetic adversarial qualifier provenance tests; not actual-source E3 gold."""
import copy
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT
from v186_e3_qualifier_provenance import (E3QualifierProvenance, ANSWER_SCHEMA)


def source():
    return ('1\n00:00:01,000 --> 00:00:01,500\n'
            '패시브 지수 ETF의 경우 비용을 확인해야 합니다.\n\n'
            '2\n00:00:02,000 --> 00:00:02,500\n'
            '다음 이야기는 단순한 예시입니다.').encode()


class TestE3QualifierProvenance(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw=source()
        self.owner=Path(self.tmp.name)/'owner.sqlite'
        self.db=Path(self.tmp.name)/'qualifiers.sqlite'
        self.engine=EngineChatSession(self.owner,self.raw,'AbCdEf12345',
            owner_source_sha256=sha256(self.raw),window_size=2,
            expected_window_count=1)
        c=self.engine.prepare(source_first_only=True,limit=2)
        out=[]
        for r in c['target_cues']:
            claims=[]
            if r['cue_index']==1:
                claims=[{'proposition':'패시브 지수 ETF라면 투자 비용을 확인하라고 설명한다.',
                    'kind':'RECOMMENDATION',
                    'quote':'패시브 지수 ETF의 경우 비용을 확인해야 합니다.',
                    'context_cue_indices':[1],
                    'conditions':['패시브 지수 ETF를 비교할 때'],
                    'exceptions':['개인의 위험 감내도와 수수료도 검토해야 함'],
                    'numeric_tokens':[],'high_risk':False,'needs_official_source':False}]
            out.append({'cue_index':r['cue_index'],
                'source_text_sha256':r['source_text_sha256'],
                'disposition':'ASSERTION' if claims else 'NON_RESEARCH',
                'speaker_role':'HOST','analysis':'원문을 근거로 초안만 검토하여 금융 사실을 자동 승인하지 않음.',
                'limitations_checked':True,'claims':claims})
        self.engine.submit(c,{'schema':COMMIT,'challenge_sha256':c['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':out})
        self.head=self.engine.progress()['checkpoint_head_sha256']
        self.custody=E3QualifierProvenance(self.engine,self.db,
            expected_owner_head=self.head,create=True)

    def answer(self,packet):
        answers=[]
        for term in packet['targets']:
            explicit=term['field']=='conditions'
            answers.append({'term_id':term['term_id'],
                'term_sha256':term['term_sha256'],
                'origin':'SOURCE_EXPLICIT' if explicit else 'REVIEWER_ADDED',
                'source_quote':'패시브 지수 ETF의 경우' if explicit else None,
                'source_cue_indices':[1] if explicit else [],
                'semantic_rationale':('화자가 직접 패시브 지수 ETF의 경우라는 제한을 두어 '
                                      '이 원칙이 적용되는 상품 범위를 명시적으로 진술했습니다.'
                                      if explicit else
                                      '위험 감내도와 수수료라는 문구는 화자 원문에 없으며 '
                                      '검토자가 위험관리를 위해 추후 덧붙인 주의사항입니다.'),
                'e3_certified':False,'v123_approved':False,'e4_approved':False,
                'e5_published':False})
        return {'schema':ANSWER_SCHEMA,'challenge_sha256':packet['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT','responses':answers}

    def test_a_direct_qualifier_mapped_and_review_caution_excluded(self):
        pkt=self.custody.prepare(limit=2)
        self.custody.submit(pkt,self.answer(pkt))
        exchange,summary=self.engine.compile_native_v6_stage(
            qualifier_provenance=self.custody)
        atom=exchange['atoms'][0]
        self.assertEqual(atom['condition_cue_indices'],[1])
        self.assertEqual(atom['exception_cue_indices'],[])
        self.assertEqual(summary['semantic_projection_gate'][
            'v186_source_qualifier_projection']['source_explicit_mapped_terms'],1)
        self.assertEqual(summary['semantic_projection_gate'][
            'v186_source_qualifier_projection']['reviewer_added_excluded_terms'],1)
        self.assertFalse(summary['semantic_projection_gate']['v123_e4_approval_permitted'])
        self.assertFalse(summary['final_approval'])
        with self.engine._connect() as db:
            _,rows=self.engine._audit(db)
        self.assertEqual(rows[1][1]['claims'][0]['exceptions'],
                         ['개인의 위험 감내도와 수수료도 검토해야 함'])

    def test_b_reopen_and_original_head_unchanged(self):
        packet=self.custody.prepare(limit=2)
        r=self.custody.submit(packet,self.answer(packet))
        self.assertEqual(self.engine.progress()['checkpoint_head_sha256'],self.head)
        restarted=E3QualifierProvenance(self.engine,self.db,
                   expected_owner_head=self.head)
        self.assertEqual(restarted.status()['reviewed_terms'],2)
        self.assertEqual(restarted.status()['journal_head_sha256'],r['journal_head_sha256'])
        with self.assertRaises(InvalidInput):
            restarted.submit(packet,self.answer(packet))

    def test_c_forged_quote_rejected(self):
        packet=self.custody.prepare(limit=2)
        answer=self.answer(packet)
        answer['responses'][0]['source_quote']='ETF만큼 유동성이 항상 보장됨'
        with self.assertRaisesRegex(InvalidInput,'QUALIFIER_SOURCE_OR_AUTHORITY_INVALID'):
            self.custody.submit(packet,answer)
        self.assertEqual(self.custody.status()['reviewed_terms'],0)

    def test_d_valid_other_cue_quote_cannot_be_pinned(self):
        packet=self.custody.prepare(limit=2)
        answer=self.answer(packet)
        answer['responses'][0]['source_quote']='다음 이야기는 단순한 예시입니다.'
        answer['responses'][0]['source_cue_indices']=[2]
        with self.assertRaisesRegex(InvalidInput,'QUALIFIER_SOURCE_OR_AUTHORITY_INVALID'):
            self.custody.submit(packet,answer)

    def test_e_original_review_admission_forgery_fails(self):
        pkt=self.custody.prepare(limit=2)
        a=self.answer(pkt)
        a['responses'][0]['e4_approved']=True
        with self.assertRaisesRegex(InvalidInput,'QUALIFIER_SOURCE_OR_AUTHORITY_INVALID'):
            self.custody.submit(pkt,a)

    def test_f_packet_self_hash_does_not_authorize(self):
        from v176_chat_engine_loop import _digest
        pkt=self.custody.prepare(limit=2)
        forged=copy.deepcopy(pkt)
        forged['original_context'][0]['text']='조작된 가짜 자막'
        forged['challenge_sha256']=_digest({k:v for k,v in forged.items()
                                            if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'QUALIFIER_PACKET_NOT_ENGINE_ISSUED_OR_STALE'):
            self.custody.submit(forged,self.answer(forged))

    def test_g_tampering_with_event_judgment_detected(self):
        pkt=self.custody.prepare(limit=2)
        self.custody.submit(pkt,self.answer(pkt))
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE judgments SET record='{}' WHERE term_id=?",(pkt['term_ids'][0],))
        with self.assertRaises(InvalidInput):
            self.custody.status()

    def test_h_private_permission_guard(self):
        pkt=self.custody.prepare(limit=2)
        self.custody.submit(pkt,self.answer(pkt))
        os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'QUALIFIER_DB_PRIVATE_PERMISSIONS'):
            E3QualifierProvenance(self.engine,self.db,expected_owner_head=self.head)

    def test_i_wrong_owner_head_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'OWNER_JOURNAL_CHANGED_OR_INCOMPLETE'):
            E3QualifierProvenance(self.engine,self.db,expected_owner_head='a'*64)

    def test_j_context_quote_kept_out_of_condition_slot(self):
        p=self.custody.prepare(limit=2)
        a=self.answer(p)
        a['responses'][0]['origin']='SOURCE_CONTEXT'
        self.custody.submit(p,a)
        exchange,summary=self.engine.compile_native_v6_stage(
            qualifier_provenance=self.custody)
        self.assertEqual(exchange['atoms'][0]['condition_cue_indices'],[])
        self.assertEqual(summary['semantic_projection_gate'][
            'v186_source_qualifier_projection']['source_context_not_source_condition_terms'],1)

    def test_k_source_explicit_cue_indices_must_be_sorted_adjacent(self):
        pkt=self.custody.prepare(limit=2)
        a=self.answer(pkt)
        a['responses'][0]['source_cue_indices']=[1,1]
        with self.assertRaises(InvalidInput):
            self.custody.submit(pkt,a)

    def test_l_partial_review_still_hold(self):
        p=self.custody.prepare(limit=1)
        a=self.answer(p)
        self.custody.submit(p,a)
        st=self.custody.status()
        self.assertEqual((st['total_terms'],st['reviewed_terms'],st['remaining_terms']),(2,1,1))
        self.assertFalse(st['e3_quality_certified'])
        ex,summary=self.engine.compile_native_v6_stage(qualifier_provenance=self.custody)
        self.assertFalse(summary['semantic_projection_gate']['full_semantic_projection_verified'])
        self.assertFalse(summary['final_approval'])

if __name__=='__main__':unittest.main()