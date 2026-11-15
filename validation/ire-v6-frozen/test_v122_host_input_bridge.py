"""V122 real V6 source/atomic-exchange bridge tests; synthetic text only."""
from __future__ import annotations
import copy,json,unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
from ire.v6.source import verify_source,parse_srt
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput,QualityNotProven
from v121_source_atomic_repair_guard import source_sha
from v122_host_research_input_bridge import build_v6_host_exchange,submit_v122_refined_host_batch,UnsafeV122

class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        txt=['ISA 만기 자금을 확인합니다.','연금 계좌로 옮기면 과세를 미룹니다.',
             '다만 세금이 없어지는 건 아닙니다.','세액공제 한도가 늘어납니다.',
             '전환 금액의 10%입니다.','최대 300만 원까지 가능합니다.']
        s='\n\n'.join(f'{i}\n00:00:{i:02},000 --> 00:00:{i:02},900\n{x}' for i,x in enumerate(txt,1))
        cls.raw=s.encode('utf-8');cls.text=txt
        cls.manifest={'schema':'IRE_V6_SOURCE_PLAN_V1','video_id':'ABCDE123456',
          'source_sha256':sha256(cls.raw),'cue_count':6,
          'scope':{'mode':'FULL_VIDEO','first_cue':1,'last_cue':6},
          'windows':[{'window_id':'W00001','first_cue':1,'last_cue':6,
                      'text_sha256':sha256(' '.join(txt).encode())}]}
        cls.source=verify_source(cls.raw,cls.manifest,
                      expected_source_sha256=sha256(cls.raw),
                      expected_manifest_sha256=json_digest(cls.manifest))
    def setUp(self):
        p1=[1,2,3];p2=[4,5,6]
        self.proposals=[
          {'id':'X1','cue_indices':p1,'source_sha256':source_sha(self.text,p1),
           'speaker_assertion':'ISA 만기 자금을 연금 계좌로 옮기면 과세를 미룰 수 있습니다.'},
          {'id':'X2','cue_indices':p2,'source_sha256':source_sha(self.text,p2),
           'speaker_assertion':'전환 금액의 10%, 최대 300만 원까지 공제 한도가 늘어납니다.'}]
        self.operations=[{'source_id':'X1','operation':'SPLIT','children':[
           {'id':'X1.1','cue_indices':[1,2],'source_sha256':source_sha(self.text,[1,2]),
            'speaker_assertion':'ISA 만기 자금을 연금 계좌로 옮깁니다.',
            'reviewer_qualification':'적격 전환과 납입 요건 확인 필요',
            'speaker_scope_is_source_literal':True,'approval_status':'PENDING_REVIEW'},
           {'id':'X1.2','cue_indices':[2,3],'source_sha256':source_sha(self.text,[2,3]),
            'speaker_assertion':'연금 계좌로 옮기면 과세를 미룹니다.',
            'reviewer_qualification':'과세 이연이지 면세는 아니다',
            'speaker_scope_is_source_literal':True,'approval_status':'PENDING_REVIEW'}]}]
        self.frames={
         'X1.1':{'kind':'FACT','stance':'UNRESOLVED','speaker':'NARRATOR',
              'context_cue_indices':[1,2],'condition_cue_indices':[],
              'exception_cue_indices':[],'as_of':None},
         'X1.2':{'kind':'FACT','stance':'CONDITIONAL','speaker':'NARRATOR',
              'context_cue_indices':[2,3],'condition_cue_indices':[2],
              'exception_cue_indices':[3],'as_of':None},
         'X2':{'kind':'FACT','stance':'UNRESOLVED','speaker':'NARRATOR',
              'context_cue_indices':[4,5,6],'condition_cue_indices':[],
              'exception_cue_indices':[],'as_of':None}}
    def call(self,**kwargs):
        args=dict(raw_srt=self.raw,verified_source=self.source,
                  proposals=self.proposals,operations=self.operations,host_frames=self.frames)
        args.update(kwargs)
        return build_v6_host_exchange(**args)
    def bad(self,mutation,exc=(UnsafeV122,InvalidInput,ValueError)):
        x=copy.deepcopy({'proposals':self.proposals,'operations':self.operations,'host_frames':self.frames})
        mutation(x)
        with self.assertRaises(exc):self.call(**x)
    def test_01_actual_core_exchange_valid(self):
        z=self.call();self.assertEqual(z['audit']['proposed_atomic_claims'],3)
        self.assertEqual(z['audit']['original_scoped_cues_enumerated'],6)
        self.assertEqual(z['audit']['suspicious_no_atom_cues'],0)
        self.assertFalse(z['independent_gold'])
    def test_02_literal_cue_source_hash(self):
        self.assertEqual(self.call()['exchange']['atoms'][0]['source_refs'][0]['quote'],self.text[0])
    def test_03_finance_reviewer_note_not_in_speaker_atom(self):
        z=self.call()['exchange']
        self.assertFalse(any('면세는 아니다' in a['proposition'] for a in z['atoms']))
    def test_04_cue_gap_is_explicit(self):
        z=self.call()['exchange'];self.assertEqual(len(z['cue_dispositions']),6)
    def test_05_digits_originally_present(self):
        a=self.call()['exchange']['atoms'][2];self.assertIn('10%',[x['token'] for x in a['numeric_references']])
    def test_06_proposal_sha_tamper(self):
        self.bad(lambda x:x['proposals'][0].update(source_sha256='f'*64))
    def test_07_host_statement_drift(self):
        self.bad(lambda x:x['operations'][0]['children'][0].update(source_sha256='f'*64))
    def test_08_fake_finance_approval(self):
        self.bad(lambda x:x['operations'][0]['children'][0].update(approval_status='APPROVED'))
    def test_09_forge_reviewer_as_speaker(self):
        self.bad(lambda x:x['operations'][0]['children'][0].update(speaker_scope_is_source_literal=False))
    def test_10_drop_child_frame(self):
        self.bad(lambda x:x['host_frames'].pop('X1.2'))
    def test_11_new_unpinned_frame(self):
        self.bad(lambda x:x['host_frames'].update({'X9':x['host_frames']['X1.1']}))
    def test_12_private_field_in_proposals(self):
        self.bad(lambda x:x['proposals'][0].update(personal_account='000-00'))
    def test_13_private_field_in_frames(self):
        self.bad(lambda x:x['host_frames']['X2'].update(gold=True))
    def test_14_missing_frame_context(self):
        self.bad(lambda x:x['host_frames']['X1.2'].update(context_cue_indices=[2]))
    def test_15_missing_condition(self):
        self.bad(lambda x:x['host_frames']['X1.2'].update(condition_cue_indices=[]),exc=(UnsafeV122,InvalidInput))
    def test_16_extra_far_context(self):
        with self.assertRaises(UnsafeV122):self.call(context_extensions={'X1.1':[6]})
    def test_17_extra_near_context(self):
        self.frames['X1.1']['context_cue_indices'].append(3)
        z=self.call(context_extensions={'X1.1':[3]})
        self.assertEqual(z['extension_docket'][0]['extra_cue_indices'],[3])
    def test_18_duplicate_extension(self):
        self.bad(lambda x:x['host_frames']['X1.1'].update(context_cue_indices=[2,1]))
    def test_19_wrong_source_bytes(self):
        with self.assertRaises(UnsafeV122):self.call(raw_srt=self.raw+b'x')
    def test_20_non_full_scope(self):
        s=copy.copy(self.source);object.__setattr__(s,'scope_first_cue',2)
        with self.assertRaises(UnsafeV122):self.call(verified_source=s)
    def test_21_bad_asof(self):
        self.bad(lambda x:x['host_frames']['X1.1'].update(as_of='2026/11/15'))
    def test_22_invalid_stance_native_core(self):
        self.bad(lambda x:x['host_frames']['X1.1'].update(stance='APPROVED'),exc=(UnsafeV122,InvalidInput))
    def test_23_numeric_hallucination_denied(self):
        self.bad(lambda x:x['proposals'][1].update(speaker_assertion='전환 시 999만원입니다'),exc=(UnsafeV122,InvalidInput))
    def test_24_duplicate_source_id(self):
        self.bad(lambda x:x['proposals'].append(copy.deepcopy(x['proposals'][0])))
    def test_25_unknown_split_parent(self):
        self.bad(lambda x:x['operations'][0].update(source_id='X999'))
    def test_26_no_invented_claim_on_repeat(self):
        x=copy.deepcopy({'proposals':self.proposals,'operations':self.operations,'host_frames':self.frames})
        x['operations'].append({'source_id':'X2','operation':'REPEAT_AS_EVIDENCE',
              'duplicate_of':'X1','repeat_source_sha256':self.proposals[1]['source_sha256'],'children':[]})
        x['host_frames'].pop('X2')
        self.assertEqual(build_v6_host_exchange(raw_srt=self.raw,verified_source=self.source,
               proposals=x['proposals'],operations=x['operations'],host_frames=x['host_frames'])['audit']['proposed_atomic_claims'],2)
    def test_27_real_host_batch_wiring_mock_only(self):
        with patch('ire.v6.trust.verify_owner_inventory',return_value=SimpleNamespace(source=self.source)):
            with patch('ire.v6.host_batch.submit_host_atomic_batch',return_value={'accepted':True}) as real:
                ans=submit_v122_refined_host_batch(None,raw_srt=self.raw,manifest=self.manifest,
                 inventory_bytes=b'private',expected_inventory_sha256='0'*64,
                 proposals=self.proposals,operations=self.operations,host_frames=self.frames,
                 knowledge={},window_models={},window_reviews={},scope_id='S',run_id='R',expected_head='0'*64)
                self.assertTrue(ans['accepted']);self.assertEqual(real.call_args.kwargs['exchange']['schema'],'IRE_V6_HOST_ATOMIC_EXCHANGE_V1')
    def test_28_repeated_submit_cannot_approve_without_owner_pin(self):
        # Real host commit is intentionally NOT invoked with an unauthenticated inventory.
        with self.assertRaises(InvalidInput):submit_v122_refined_host_batch(None,raw_srt=self.raw,
         manifest=self.manifest,inventory_bytes=b'{}',expected_inventory_sha256='0'*64,
         proposals=self.proposals,operations=self.operations,host_frames=self.frames,
         knowledge={},window_models={},window_reviews={},scope_id='S',run_id='R',expected_head='0'*64)
    def test_29_no_external_gold_v122(self):
        z=self.call();self.assertFalse(z['automatically_invoked_chatgpt']);self.assertFalse(z['p0_go'])
    def test_30_baseline_lock_is_immutable_sha_only(self):
        p=Path(__file__).resolve().parent
        lock=json.loads((p/'V122_PRE_REFERENCE_SHA_ONLY.json').read_text(encoding='utf-8'))
        frm=json.loads((p/'V122_HOST_FRAMES_PRE_REFERENCE_SHA_ONLY.json').read_text(encoding='utf-8'))
        self.assertFalse(lock['reference_created']);self.assertEqual(frm['pre_reference'],'NO_REFERENCE_SEEN')
        self.assertEqual(lock['pre_reference_refined_predictions'],15)
    def test_31_public_receipt_false_go(self):
        obj=json.loads((Path(__file__).resolve().parent/'V122_PUBLIC_SHA_ONLY.json').read_text(encoding='utf-8'))
        self.assertFalse(obj['independent_gold']);self.assertFalse(obj['p0_go'])
        self.assertFalse(obj['production_atomic_host_batch_committed'])
    def test_32_scores_provisional(self):
        obj=json.loads((Path(__file__).resolve().parent/'V122_PUBLIC_SHA_ONLY.json').read_text(encoding='utf-8'))
        self.assertEqual(obj['same_chat_scoring_label'],'CHAT_INTERNAL_EXPLORATORY_SELF_CORRELATED')
        self.assertEqual(obj['baseline_tp_fp_fn'],[9,3,8]);self.assertEqual(obj['refined_tp_fp_fn'],[15,0,2])

if __name__=='__main__':unittest.main()
