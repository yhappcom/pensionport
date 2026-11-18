"""V171 tests use frozen V6 auditor, source-first synthetic fixture only."""
import copy
import unittest
from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import json_digest,sha256
from v171_source_bound_reatomization import compile_split,digest,SCHEMA

NOTE=('동일한 자막에 검증 가능한 시장 주장과 화자의 개인적 체감이 함께 표시되어 있습니다. '
      '한 원자에 두 의미를 합치면 사실의 확정성·발화자의 의견을 혼동하게 됩니다. '
      '기존 원문 인용·숫자·시점·조건·예외·반박 문맥은 보존하고, 신규 사실 원자는 근거 없으면 OPEN으로 유지합니다.')

class V171NativeStructuralAndSemanticSplit(unittest.TestCase):
    def setUp(self):
        fx=HostAtomExchangeTests('test_all_cues_number_context_and_stance_bound_but_not_semantic_gold')
        fx.setUp();self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.exchange=copy.deepcopy(fx.exchange)
        self.old=self.exchange['atoms'][0]
        self.review={'source_sha256':fx.source.source_sha256,
                     'manifest_sha256':fx.source.manifest_sha256,
                     'atom_verdicts':[],'source_first_pass_completed':True,
                     'counterexample_pass_completed':True,
                     'disagreements_adjudicated':True}
        for atom in self.exchange['atoms']:
            self.review['atom_verdicts'].append({
                'claim_id':atom['claim_id'],'atom_sha256':json_digest(atom),
                'status':'OPEN' if atom['claim_id']=='C00001' else 'ACCEPT_FOR_RESEARCH',
                'speaker_stance_checked':False,'conditions_exceptions_checked':False,
                'numeric_period_checked':False,'counterexample_checked':False,
                'high_risk':True,'financial_claim':True,'finance_evidence_status':'OPEN',
                'official_body_sha256':None,'official_effective_as_of':None,
                'financial_scope_checked':False,
                'private_review_note_sha256':sha256(('synthetic '+atom['claim_id']).encode())})
        objective=copy.deepcopy(self.old)
        objective['proposition']='연금저축 예상 수익률 10%라는 검증 대상 주장을 별도로 보존합니다.'
        objective['kind']='FACT'
        subjective=copy.deepcopy(self.old)
        subjective['claim_id']='C00099'
        subjective['proposition']='연금저축 예상 수익을 긍정적으로 해석하는 개인적 체감 의견입니다.'
        subjective['kind']='OPINION'
        self.split={
            'schema':SCHEMA,'source_sha256':fx.source.source_sha256,
            'manifest_sha256':fx.source.manifest_sha256,
            'old_exchange_sha256':digest(self.exchange),
            'old_review_sha256':digest(self.review),
            'old_claim_id':'C00001','old_atom_sha256':digest(self.old),
            'new_atoms':[objective,subjective],
            'chat_semantic_note':NOTE,'chat_semantic_note_sha256':sha256(NOTE.encode()),
            'reviewer_source_first_checked':True,
            'reviewer_condition_exception_checked':True,
            'reviewer_counterexample_checked':True,
            'reviewer_rebuttal_context_checked':True,
            'audio_authenticated':False,'independent_gold_certified':False,
            'financial_truth_certified':False,'personal_advice_approved':False,
            'approved_knowledge_release':False,
        }
        self.previous=copy.deepcopy(self.exchange)
        self.before=copy.deepcopy(self.review)

    def compile(self,**overrides):
        return compile_split(self.fx.source,self.exchange,self.review,
                             overrides.get('split',self.split),
                             whole_video_claim_ids=overrides.get('ids',
                                 {'C00001','C00002','C00003','C00050'}),
                             native_audit=overrides.get('native',audit_host_atomic_exchange))
    def test_01_real_frozen_v6_native_validates_split_and_no_release(self):
        r=self.compile(); receipt=r['receipt']
        self.assertEqual((receipt['original_atom_count'],receipt['draft_atom_count']),(3,4))
        self.assertFalse(receipt['native_v123_final_approval'])
        self.assertFalse(receipt['knowledge_publication_authorized'])
        self.assertEqual([v['status'] for v in r['draft_review']['atom_verdicts'][:2]],['OPEN','OPEN'])
        self.assertEqual([v['claim_id'] for v in r['draft_review']['atom_verdicts'][:2]],['C00001','C00099'])
        self.assertEqual(r['draft_exchange']['cue_dispositions'][0]['claim_ids'],['C00001','C00099'])
        self.assertEqual(self.exchange,self.previous)
        self.assertEqual(self.review,self.before)
        self.assertEqual(audit_host_atomic_exchange(self.fx.source,r['draft_exchange'])['proposed_atomic_claims'],4)
    def test_02_reused_global_id_rejected(self):
        with self.assertRaisesRegex(ValueError,'NEW_GLOBAL_ID'):self.compile(ids={'C00001','C00002','C00003','C00099'})
    def test_03_old_must_be_open(self):
        self.review['atom_verdicts'][0]['status']='ACCEPT_FOR_RESEARCH'
        self.split['old_review_sha256']=digest(self.review)
        with self.assertRaisesRegex(ValueError,'ONLY_ORIGINAL_OPEN'):self.compile()
    def test_04_stale_review_rejected(self):
        self.review['atom_verdicts'][0]['status']='REJECT'
        with self.assertRaisesRegex(ValueError,'VERSION_DRIFT'):self.compile()
    def test_05_stale_exchange_rejected(self):
        self.exchange['atoms'][0]['proposition']='다른 주장'
        with self.assertRaisesRegex(ValueError,'VERSION_DRIFT'):self.compile()
    def test_06_forged_quote_rejected(self):
        changed=copy.deepcopy(self.split)
        changed['new_atoms'][1]['source_refs'][0]['quote']='가짜 원본 발언'
        with self.assertRaisesRegex(ValueError,'ORIGINAL_VERBATIM'):self.compile(split=changed)
    def test_07_missing_audio_certification_rejected(self):
        changed=copy.deepcopy(self.split);changed['audio_authenticated']=True
        with self.assertRaisesRegex(ValueError,'FALSE_AUTHORITY'):self.compile(split=changed)
    def test_08_duplicated_opinion_as_fact_rejected(self):
        changed=copy.deepcopy(self.split);changed['new_atoms'][1]['kind']='FACT'
        with self.assertRaisesRegex(ValueError,'FACTUAL_DEPENDENCY'):self.compile(split=changed)
    def test_09_source_context_mutation_rejected(self):
        changed=copy.deepcopy(self.split)
        changed['new_atoms'][1]['context_cue_indices']=[1,2]
        with self.assertRaisesRegex(ValueError,'CONDITIONS_EXCEPTIONS'):self.compile(split=changed)
    def test_10_forged_hash_of_chat_note_rejected(self):
        changed=copy.deepcopy(self.split);changed['chat_semantic_note_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'ACTUAL_CHAT_NOTE'):self.compile(split=changed)
    def test_11_untrusted_native_auditor_rejected(self):
        with self.assertRaisesRegex(ValueError,'FROZEN_NATIVE'):self.compile(native=lambda source,e:{})
    def test_12_existing_audio_independent_or_finance_approval_rejected(self):
        for field in ('independent_gold_certified','financial_truth_certified',
                      'personal_advice_approved','approved_knowledge_release'):
            with self.subTest(field=field):
                changed=copy.deepcopy(self.split);changed[field]=True
                with self.assertRaisesRegex(ValueError,'FALSE_AUTHORITY'):self.compile(split=changed)

if __name__=='__main__':unittest.main()