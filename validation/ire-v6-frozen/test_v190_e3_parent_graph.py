"""V190 E3 synthetic adversarial tests; no owner-private SRT or financial gold."""
import copy,os,sqlite3,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import _digest
from v183_e3_two_turn_audit import ANSWER_SCHEMA as SECOND_SCHEMA
from v189_e3_omission_repair_overlay import E3OmissionOverlay, ANSWER_SCHEMA as OMISSION_SCHEMA
from v189_e3_parent_alignment_screen import generate_packet, ANSWER_SCHEMA as SCREEN_SCHEMA
from v190_e3_parent_graph import E3ParentGraphReview, RESPONSE
import test_v184_e3_adjudication as base_fixture


class ParentGraphSynthetic(unittest.TestCase):
    def setUp(self):
        self.base=base_fixture.TestAdjudication('test_packet_has_first_and_second_with_original_context')
        self.base.setUp();self.addCleanup(self.base.doCleanups)
        # Complete entire four-cue source census (no owner-private video involved).
        p=self.base.audit.prepare(limit=1)
        self.base.audit.submit(p,{'schema':SECOND_SCHEMA,
          'challenge_sha256':p['challenge_sha256'],'review_executor':'CHATGPT_IN_CHAT',
          'responses':[{'cue_index':4,'source_text_sha256':p['target_cues'][0]['source_text_sha256'],
              'disposition':'NON_RESEARCH','speaker_role':'HOST','claims':[],
              'analysis':'합성 사례 마지막 문장이므로 금융 주장을 새로 생성하지 않습니다.',
              'limitations_checked':True}]})
        pa=self.base.reviewer.prepare(limit=2)
        ans=self.base.response(pa)
        ans['answers'][1]['category']='CLAIM_BOUNDARY_DISAGREEMENT'
        ans['answers'][1]['next_action']='PRESERVE_BOTH_WITH_PARENT_LINK'
        self.base.reviewer.submit(pa,ans)
        self.omission=E3OmissionOverlay(self.base.reviewer,Path(self.base.tmp.name)/'omission.sqlite',create=True)
        po=self.omission.prepare()
        claim=po['targets'][0]['first_nearby_claims'][0]
        ref={k:claim[k] for k in ('pass','cue_index','ordinal','claim_sha256')}
        self.omission.submit(po,{'schema':OMISSION_SCHEMA,'challenge_sha256':po['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','answers':[{
                'cue_index':1,'original_category':po['targets'][0]['original_category'],
                'resolution':'PROVISIONAL_NEW_CLAIM',
                'reviewed_source_quote':'ETF는 장점이 있습니다.',
                'source_quote_cue_index':1,'source_context_cue_indices':[1,2],
                'other_pass_claim_ref':ref,'covered_pass_claim_ref':None,
                'semantic_rationale':'합성 자막 원문과 두 판정을 대조한 결과 기존 원자에 연결되는 후보는 있지만, 이는 투자 사실 확정이나 안전성 승인을 의미하지 않습니다. 원장 기록만 보존합니다.',
                'claim_truth_certified':False,'independent_gold_certified':False,
                'e3_certified':False,'v123_approved':False,'e4_approved':False,'e5_published':False}]})
        self.packet=generate_packet(self.base.reviewer)
        self.assertEqual([(x['cue_index'],x['candidate_count']) for x in self.packet['cases']],[(2,0)])
        self.screen={'schema':SCREEN_SCHEMA,'packet_sha256':self.packet['packet_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','reviews':[{
                'cue_index':2,'assessment':'NO_CANDIDATE_UNRESOLVED',
                'source_quote':'하지만 조건에 따라 손실이 있을 수 있습니다.',
                'source_quote_cue_index':2,'pair_ref':None,
                'semantic_rationale':'독립적인 원본에 제시된 조건부 손실 가능성에 맞는 다른 자막의 원자 후보가 확인되지 않았으나, 그 사실만으로 새로운 정답 원자를 확정할 수 없습니다.',
                'semantic_equivalence_certified':False,'independent_gold_certified':False,
                'e3_certified':False,'e4_approved':False,'e5_published':False}]}
        self.path=Path(self.base.tmp.name)/'parent.sqlite'
        self.graph=E3ParentGraphReview(self.base.reviewer,self.omission,self.path,
            v189_screen_packet=self.packet,v189_screen_answer=self.screen,create=True)

    def response(self,p):
        return {'schema':RESPONSE,'challenge_sha256':p['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','answers':[{
                'cue_index':2,'decision':'NO_HEURISTIC_PAIR_KEEP_OPEN',
                'pair_ref':None,'first_quote':None,'first_quote_cue':None,
                'second_quote':None,'second_quote_cue':None,
                'semantic_rationale':'원문에는 조건부 손실 위험을 소개하지만 두 검토 원장 간 숫자와 자막 위치 비교에서 대응 원자 후보를 찾지 못했으므로 자동으로 누락이나 완전 동치를 확정하지 않습니다.',
                'independent_gold_certified':False,'e3_certified':False,
                'v123_approved':False,'e4_approved':False,'e5_published':False}]}

    def test_01_source_journal_event_append_only(self):
        prior=self.base.eng.progress()['checkpoint_head_sha256']
        q=self.graph.prepare();stat=self.graph.submit(q,self.response(q))
        self.assertEqual(stat['reviewed'],1);self.assertEqual(stat['pending'],0)
        self.assertFalse(stat['e3_certified'])
        self.assertEqual(self.base.eng.progress()['checkpoint_head_sha256'],prior)
        self.assertEqual(self.graph.provisional_new_claims()[0]['kind'],'OPINION')

    def test_02_reopened_process_consistency(self):
        q=self.graph.prepare();self.graph.submit(q,self.response(q))
        again=E3ParentGraphReview(self.base.reviewer,self.omission,self.path,
            v189_screen_packet=self.packet,v189_screen_answer=self.screen)
        self.assertEqual(again.status()['review_head'],self.graph.status()['review_head'])

    def test_03_forged_context_self_hash_rejected(self):
        q=self.graph.prepare();altered=copy.deepcopy(q)
        altered['source_context'][0]['text']='원금 100% 보장'
        altered['challenge_sha256']=_digest({k:v for k,v in altered.items() if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'CHALLENGE_NOT_ENGINE_ISSUED'):
            self.graph.submit(altered,self.response(altered))

    def test_04_unmatched_cannot_invent_pair(self):
        q=self.graph.prepare();ans=self.response(q)
        ans['answers'][0]['decision']='PROVISIONAL_SAME_PROPOSITION'
        with self.assertRaisesRegex(InvalidInput,'NO_HEURISTIC_PAIR_CANNOT_CREATE_A_PAIR'):
            self.graph.submit(q,ans)

    def test_05_authority_forgery_blocked(self):
        q=self.graph.prepare();ans=self.response(q)
        ans['answers'][0]['e4_approved']=True
        with self.assertRaisesRegex(InvalidInput,'VERDICT_SHAPE_AUTHORITY'):
            self.graph.submit(q,ans)

    def test_06_duplicate_submit_blocked(self):
        q=self.graph.prepare();self.graph.submit(q,self.response(q))
        with self.assertRaisesRegex(InvalidInput,'INVALID_SELECTION|CHALLENGE_NOT_ENGINE_ISSUED'):
            self.graph.submit(q,self.response(q))

    def test_07_forged_judgment_detected(self):
        q=self.graph.prepare();self.graph.submit(q,self.response(q))
        with sqlite3.connect(self.path) as db:db.execute("UPDATE judgments SET record='{}'")
        with self.assertRaisesRegex(InvalidInput,'RESULT_ROW_TAMPER'):
            self.graph.status()

    def test_08_private_db_permissions_required(self):
        os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,'EXISTING_PRIVATE_DB_REQUIRED'):
            E3ParentGraphReview(self.base.reviewer,self.omission,self.path,
                v189_screen_packet=self.packet,v189_screen_answer=self.screen)

    def test_09_v189_answer_different_pin_rejected(self):
        altered=copy.deepcopy(self.screen);altered['reviews'][0]['source_quote']='원금 무조건 보장'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_QUOTE_UNVERIFIED'):
            E3ParentGraphReview(self.base.reviewer,self.omission,Path(self.base.tmp.name)/'forged.sqlite',
                v189_screen_packet=self.packet,v189_screen_answer=altered,create=True)


class ParentPairEvidenceSynthetic(unittest.TestCase):
    def setUp(self):
        self.g=E3ParentGraphReview.__new__(E3ParentGraphReview)
        self.g.source=[SimpleNamespace(text='ETF 시장가격은 장중에 거래로 형성됩니다.'),
                       SimpleNamespace(text='ETF 순자산가치는 편입자산에 근거합니다.')]
        self.pair={'ref':{'first_anchor':1,'second_anchor':2,'first_claim_ordinal':1,'second_claim_ordinal':1},
                   'first_context_indices':[1],'second_context_indices':[2]}
        self.case={'cue_index':1,'candidate_pairs':[self.pair]}

    def item(self):
        return {'cue_index':1,'decision':'DISTINCT_PROPOSITIONS',
            'pair_ref':copy.deepcopy(self.pair['ref']),
            'first_quote':'ETF 시장가격은 장중에 거래로 형성됩니다.','first_quote_cue':1,
            'second_quote':'ETF 순자산가치는 편입자산에 근거합니다.','second_quote_cue':2,
            'semantic_rationale':'한 설명은 거래된 가격의 결정 과정이고 다른 설명은 펀드 순자산가치의 계산 기준입니다. 서로 다른 경제적 개념이므로 동일한 주장으로 병합하거나 승인하지 않습니다.',
            'independent_gold_certified':False,'e3_certified':False,'v123_approved':False,
            'e4_approved':False,'e5_published':False}

    def test_10_different_financial_concepts_recorded_without_merging(self):
        self.g._check_one(self.item(),self.case)

    def test_11_cross_cue_quote_forgery_rejected(self):
        a=self.item();a['first_quote']='원금 100% 보장됩니다.'
        with self.assertRaisesRegex(InvalidInput,'PAIR_EVIDENCE_NOT_SOURCE_PINN'):
            self.g._check_one(a,self.case)

    def test_12_wrong_cue_anchor_rejected(self):
        a=self.item();a['second_quote_cue']=1
        with self.assertRaisesRegex(InvalidInput,'PAIR_EVIDENCE_NOT_SOURCE_PINN'):
            self.g._check_one(a,self.case)

    def test_13_nonexistent_pair_rejected(self):
        a=self.item();a['pair_ref']['first_anchor']=2
        with self.assertRaisesRegex(InvalidInput,'PAIR_NOT_IN_FROZEN_CANDIDATES'):
            self.g._check_one(a,self.case)

    def test_14_ambiguous_must_not_pick_unverified_pair(self):
        a=self.item();a['decision']='MULTIPLE_POSSIBLE_KEEP_OPEN'
        with self.assertRaisesRegex(InvalidInput,'AMBIGUOUS_REVIEW_MUST_NOT_PICK_PAIR'):
            self.g._check_one(a,self.case)

if __name__=='__main__':unittest.main()