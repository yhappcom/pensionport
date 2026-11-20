"""Synthetic V191 no-prior-verdict parent-first security tests, not a financial gold set."""
from __future__ import annotations
import copy,json,os,sqlite3,tempfile,unittest
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import _digest
from v183_e3_two_turn_audit import E3TwoTurnAudit,ANSWER_SCHEMA as SECOND_ANSWER
from v191_e3_parent_first import E3ParentFirst,ANSWER
import test_v184_e3_adjudication as v184fixture

class TestParentFirst(unittest.TestCase):
    def setUp(self):
        fix=v184fixture.TestAdjudication('test_packet_has_first_and_second_with_original_context')
        fix.setUp()
        self.addCleanup(fix.doCleanups)
        q=fix.audit.prepare(limit=1)
        assert q['cue_indices']==[4]
        fix.audit.submit(q,{'schema':SECOND_ANSWER,
            'challenge_sha256':q['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':[
              {'cue_index':4,'source_text_sha256':q['target_cues'][0]['source_text_sha256'],
               'disposition':'NON_RESEARCH','speaker_role':'HOST','claims':[],
               'analysis':'원본 마무리 발화로서 추가 주장은 없는 것을 확인했습니다.',
               'limitations_checked':True}]})
        self.owner=fix.eng;self.second=fix.audit
        self.db=Path(fix.tmp.name)/'parent_first.sqlite'
        self.engine=E3ParentFirst(self.owner,self.second,self.db,
                     expected_owner_head=self.owner.progress()['checkpoint_head_sha256'],
                     expected_second_head=self.second.status()['second_review_audit_head_sha256'],
                     create=True,max_span=4)

    def reply(self,packet):
        return {'schema':ANSWER,'challenge_sha256':packet['challenge_sha256'],
              'review_executor':'CHATGPT_IN_CHAT', 'parent':{
               'start_cue':1,'end_cue':2,'parent_intent':'EXPLANATION',
               'speaker_role':'HOST','parent_summary':'ETF의 투자 특성과 손실 조건을 설명하는 한 발화입니다.',
               'analysis':'ETF 장점 발화와 손실 가능성 발화가 인접하지만 서로 다른 주장임을 구분하여 저장합니다.',
               'claims':[
                {'kind':'OPINION','proposition':'화자는 ETF의 장점을 긍정적으로 평가합니다.',
                 'quote':'ETF는 장점이 있습니다.','quote_cue':1,'evidence_cues':[1],
                 'numbers':[],'spoken_conditions':[],'spoken_exceptions':[],
                 'reviewer_caveats':[],'high_risk':False,'needs_official_source':False,
                 'source_truth_certified':False},
                {'kind':'FACT','proposition':'화자는 조건에 따라 손실이 발생할 수 있다고 설명합니다.',
                 'quote':'손실이 있을 수 있습니다.','quote_cue':2,'evidence_cues':[2],
                 'numbers':[],'spoken_conditions':[{'cue_index':2,'quote':'조건에 따라',
                                'provenance':'SOURCE_SPOKEN'}],
                 'spoken_exceptions':[],'reviewer_caveats':['실제 금융상품의 적용 조건은 추가 검토가 필요합니다.'],
                 'high_risk':True,'needs_official_source':True,'source_truth_certified':False}],
               'claim_relations':[],'scope_links':[],'open_issues':[],
               'independent_gold_certified':False,'e3_certified':False,'v123_approved':False,
               'e4_approved':False,'e5_published':False}}

    def test_01_no_old_decisions_leak_and_multi_atoms(self):
        p=self.engine.prepare(2)
        self.assertFalse(p['previous_verdicts_or_atoms_exposed'])
        self.assertNotIn('first_pass',json.dumps(p))
        self.assertNotIn('ETF는 장점이 있다고 발언한다.',json.dumps(p,ensure_ascii=False))
        out=self.engine.submit(p,self.reply(p))
        self.assertEqual((out['reviewed_cues'],out['candidate_claims'],out['parent_count']),(2,2,1))
        self.assertFalse(out['e3_quality_certified'])
        self.assertEqual(self.engine.compare_unapproved()[0]['first_cue_local_candidates'],1)

    def test_02_second_process_reopen_exact_head_and_coverage(self):
        p=self.engine.prepare(2);self.engine.submit(p,self.reply(p))
        other=E3ParentFirst(self.owner,self.second,self.db,
            expected_owner_head=self.owner.progress()['checkpoint_head_sha256'],
            expected_second_head=self.second.status()['second_review_audit_head_sha256'],max_span=4)
        self.assertEqual(other.status()['parent_head'],self.engine.status()['parent_head'])
        self.assertEqual(other.prepare(4)['start_cue'],3)

    def test_03_self_hashed_packet_forgery_rejected(self):
        p=self.engine.prepare(2);fake=copy.deepcopy(p)
        fake['original_cues'][0]['text']='모든 ETF는 원금이 보장됩니다.'
        fake['challenge_sha256']=_digest({k:v for k,v in fake.items() if k!='challenge_sha256'})
        a=self.reply(fake)
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_CHALLENGE'):
            self.engine.submit(fake,a)
        self.assertEqual(self.engine.status()['reviewed_cues'],0)

    def test_04_source_quote_wrong_cue_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['claims'][0]['quote']='손실이 있을 수 있습니다.'
        with self.assertRaisesRegex(InvalidInput,'CLAIM_UNGROUNDED'):
            self.engine.submit(p,a)

    def test_05_fake_numeric_token_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['claims'][0]['numbers']=[{'cue_index':1,'token':'100%'}]
        with self.assertRaisesRegex(InvalidInput,'NUMBER_NOT_IN_SOURCE'):
            self.engine.submit(p,a)

    def test_06_reviewer_caveat_as_source_spoken_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['claims'][1]['spoken_exceptions']=[{'cue_index':1,
                   'quote':'원금 보장 적용 예외','provenance':'SOURCE_SPOKEN'}]
        a['parent']['claims'][1]['evidence_cues']=[1,2]
        with self.assertRaisesRegex(InvalidInput,'SPOKEN_QUALIFIER_NOT_IN_SOURCE'):
            self.engine.submit(p,a)

    def test_07_scope_link_from_future_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['scope_links']=[{'antecedent_cue':3,'antecedent_quote':'감사합니다.',
                                    'applies_to_claim_indices':[1],'relation':'HYPOTHETICAL_EXAMPLE'}]
        with self.assertRaisesRegex(InvalidInput,'UNSUPPORTED_UPSTREAM_SCOPE'):
            self.engine.submit(p,a)

    def test_08_out_of_sequence_and_span_overflow(self):
        with self.assertRaisesRegex(InvalidInput,'OUT_OF_ORDER_OR_TOO_LONG'):
            self.engine.prepare(5)
        with self.assertRaisesRegex(InvalidInput,'OUT_OF_ORDER_OR_TOO_LONG'):
            self.engine.prepare(0)

    def test_09_approval_forgery_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p);a['parent']['e3_certified']=True
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_SHAPE_OR_APPROVAL_FORGERY'):
            self.engine.submit(p,a)

    def test_10_duplicate_stale_packet_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p);self.engine.submit(p,a)
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_CHALLENGE'):
            self.engine.submit(p,a)

    def test_11_event_and_row_tamper_detected(self):
        p=self.engine.prepare(2);self.engine.submit(p,self.reply(p))
        with sqlite3.connect(self.db) as db:
            db.execute('UPDATE parent_units SET record=\'{}\' WHERE start_cue=1')
        with self.assertRaisesRegex(InvalidInput,'PARENT_RECORD_TAMPER'):
            self.engine.status()

    def test_12_private_mode_and_no_reset(self):
        os.chmod(self.db,0o644)
        with self.assertRaisesRegex(InvalidInput,'EXISTING_PRIVATE_DB_REQUIRED'):
            E3ParentFirst(self.owner,self.second,self.db,
                expected_owner_head=self.owner.progress()['checkpoint_head_sha256'],
                expected_second_head=self.second.status()['second_review_audit_head_sha256'])

    def test_13_no_prior_approval_even_if_full_census(self):
        p=self.engine.prepare(2);self.engine.submit(p,self.reply(p))
        q=self.engine.prepare(4)
        a={'schema':ANSWER,'challenge_sha256':q['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','parent':{
                'start_cue':3,'end_cue':4,'parent_intent':'SUMMARY','speaker_role':'HOST',
                'parent_summary':'투자 설명을 마친 뒤 인사로 끝내는 발화입니다.',
                'analysis':'원본에 있는 인사와 종료 안내에는 금융 사실이나 투자 판단의 독립적인 원자가 나타나지 않습니다.',
                'claims':[],'claim_relations':[],'scope_links':[],'open_issues':[],
                'independent_gold_certified':False,'e3_certified':False,
                'v123_approved':False,'e4_approved':False,'e5_published':False}}
        self.engine.submit(q,a)
        self.assertEqual(self.engine.status()['reviewed_cues'],4)
        self.assertFalse(self.engine.status()['e3_quality_certified'])
        self.assertTrue(self.engine.status()['parent_first_full_census'])

    def test_14_distinct_atomics_relation_source_bound(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['claim_relations']=[{'from_claim':1,'to_claim':2,'relation':'DISTINCT_FROM'}]
        status=self.engine.submit(p,a)
        self.assertEqual(status['candidate_claims'],2)
        self.assertEqual(self.engine.compare_unapproved()[0]['new_parent_atom_candidates'],2)
        self.assertEqual(len(self.engine.compare_unapproved()[0]['candidate_atom_ids']),2)

    def test_15_forged_claim_link_indices_rejected(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['claim_relations']=[{'from_claim':1,'to_claim':77,'relation':'DISTINCT_FROM'}]
        with self.assertRaisesRegex(InvalidInput,'CLAIM_RELATION_INVALID'):
            self.engine.submit(p,a)

    def test_16_unsupported_qualifier_cue_outside_parent(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['claims'][1]['evidence_cues']=[2,3]
        with self.assertRaisesRegex(InvalidInput,'CLAIM_UNGROUNDED_OR_BAD_SCHEMA'):
            self.engine.submit(p,a)

    def test_17_cannot_claim_independent_gold(self):
        p=self.engine.prepare(2);a=self.reply(p)
        a['parent']['independent_gold_certified']=True
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_SHAPE_OR_APPROVAL_FORGERY'):
            self.engine.submit(p,a)

if __name__=='__main__':unittest.main()