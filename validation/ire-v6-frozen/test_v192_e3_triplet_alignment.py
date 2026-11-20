"""V192 synthetic adversarial/source-pin tests; NOT independent gold or ETF truth."""
from __future__ import annotations
import copy,sqlite3,os,tempfile,unittest
from pathlib import Path
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import _digest
from v192_e3_triplet_alignment import E3TripletAlignment,ANSWER
import test_v191_e3_parent_first as v191fixture

class TestTripletAlignment(unittest.TestCase):
    def setUp(self):
        fix=v191fixture.TestParentFirst('test_01_no_old_decisions_leak_and_multi_atoms')
        fix.setUp();self.addCleanup(fix.doCleanups)
        self.fix=fix
        packet=fix.engine.prepare(2)
        fix.engine.submit(packet,fix.reply(packet))
        packet=fix.engine.prepare(4)
        fix.engine.submit(packet,{'schema':v191fixture.ANSWER,
              'challenge_sha256':packet['challenge_sha256'],
              'review_executor':'CHATGPT_IN_CHAT', 'parent':{
              'start_cue':3,'end_cue':4,'parent_intent':'SUMMARY','speaker_role':'HOST',
              'parent_summary':'마지막 발화에는 ETF 금융 주장이 나오지 않습니다.',
              'analysis':'두 자막은 인사와 종료 안내여서 독립적인 금융 원자 주장을 추가하지 않습니다.',
              'claims':[],'claim_relations':[],'scope_links':[],'open_issues':[],
              'independent_gold_certified':False,'e3_certified':False,
              'v123_approved':False,'e4_approved':False,'e5_published':False}})
        self.path=Path(fix.owner.path).parent/'triple.sqlite'
        self.init_args=dict(expected_owner_head=fix.owner.progress()['checkpoint_head_sha256'],
              expected_second_head=fix.second.status()['second_review_audit_head_sha256'],
              expected_parent_head=fix.engine.status()['parent_head'])
        self.a=E3TripletAlignment(fix.engine,self.path,create=True,**self.init_args)
    def answer(self,packet):
        records=[]
        for target in packet['target_parents']:
            a=[];mapped={'FIRST':set(),'SECOND':set()}
            for i,claim in enumerate(target['parent_claims']):
                first=target['older_claims']['FIRST'][:1] if i==0 else []
                s=[]
                for x in first:mapped['FIRST'].add(_digest(x['ref']))
                a.append({'parent_claim_ref':copy.deepcopy(claim['ref']),
                    'first_refs':[copy.deepcopy(x['ref']) for x in first], 'second_refs':s,
                    'first_relation':'EQUIVALENT_PROVISIONAL' if first else 'MISSING_IN_OLDER',
                    'second_relation':'MISSING_IN_OLDER',
                    'meaning_rationale':'첫 패스 원자가 실제 원문에 나타난 ETF 의견과 대응하지만, 다음 부모 주장의 손실 조건은 다른 독립 의미에 해당합니다.'})
            missing={}
            for which in ('FIRST','SECOND'):
                missing[which]=[x['ref'] for x in target['older_claims'][which]
                   if _digest(x['ref']) not in mapped[which]]
            records.append({'start_cue':target['start_cue'],'parent_id':target['parent_id'],
              'source_quote':next(x['text'] for x in target['original_cues'] if x['cue_index']==target['start_cue']),
              'source_quote_cue':target['start_cue'],
              'claim_alignments':a,'unmatched_older_refs':missing,
              'review_rationale':'두 번의 자막별 판정과 부모 발화에서 실제로 인용한 주장 범위를 비교하되 문맥을 넘어선 금융 사실 인증을 수행하지 않습니다.',
              'independent_gold_certified':False,'e3_certified':False,
              'v123_approved':False,'e4_approved':False,'e5_published':False})
        return {'schema':ANSWER,'challenge_sha256':packet['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT','reviews':records}
    def test_01_initial_pins_and_metadata(self):
        x=self.a.prepare(limit=1);self.assertEqual(len(x['target_parents']),1)
        self.assertEqual(x['target_parents'][0]['start_cue'],1)
        self.assertFalse(x['e3_certified']);self.assertEqual(x['target_parents'][0]['parent_claims'][0]['kind'],'OPINION')
    def test_02_submit_and_reopen(self):
        p=self.a.prepare(limit=1);out=self.a.submit(p,self.answer(p))
        self.assertEqual(out['reviewed_parents'],1)
        same=E3TripletAlignment(self.fix.engine,self.path,**self.init_args)
        self.assertEqual(same.status()['alignment_head'],out['alignment_head'])
        self.assertEqual(same.prepare()['target_parents'][0]['start_cue'],3)
    def test_03_stale_and_duplicate(self):
        p=self.a.prepare(limit=1);a=self.answer(p);self.a.submit(p,a)
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_CHALLENGE'):
            self.a.submit(p,a)
    def test_04_forged_packet_self_hash(self):
        p=self.a.prepare(limit=1);x=copy.deepcopy(p)
        x['target_parents'][0]['older_claims']['FIRST'][0]['proposition']='원금 무조건 보장'
        x['challenge_sha256']=_digest({k:v for k,v in x.items() if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_CHALLENGE'):
            self.a.submit(x,self.answer(x))
    def test_05_forged_old_reference(self):
        p=self.a.prepare(limit=1);a=self.answer(p)
        a['reviews'][0]['claim_alignments'][0]['first_refs'][0]['claim_sha256']='a'*64
        with self.assertRaisesRegex(InvalidInput,'OLD_CLAIM_REF_FORGED'):
            self.a.submit(p,a)
    def test_06_parent_ref_forgery(self):
        p=self.a.prepare(limit=1);a=self.answer(p)
        a['reviews'][0]['claim_alignments'][0]['parent_claim_ref']['ordinal']=99
        with self.assertRaisesRegex(InvalidInput,'PARENT_CLAIM_ID_OR_MEANING'):
            self.a.submit(p,a)
    def test_07_missing_old_census_cannot_skip(self):
        p=self.a.prepare(limit=1);a=self.answer(p)
        a['reviews'][0]['claim_alignments'][0]['first_refs']=[]
        a['reviews'][0]['claim_alignments'][0]['first_relation']='MISSING_IN_OLDER'
        with self.assertRaisesRegex(InvalidInput,'OLDER_CLAIM_CENSUS_INCOMPLETE'):
            self.a.submit(p,a)
    def test_08_source_quote_wrong_cue(self):
        p=self.a.prepare(limit=1);a=self.answer(p)
        a['reviews'][0]['source_quote']='주식시장에서 언제든 거래됩니다'
        with self.assertRaisesRegex(InvalidInput,'REVIEW_FIELD_OR_AUTHORITY'):
            self.a.submit(p,a)
    def test_09_force_e3_rejected(self):
        p=self.a.prepare(limit=1);a=self.answer(p)
        a['reviews'][0]['e3_certified']=True
        with self.assertRaisesRegex(InvalidInput,'REVIEW_FIELD_OR_AUTHORITY'):
            self.a.submit(p,a)
    def test_10_source_ledger_untouched(self):
        before=self.fix.owner.progress()['checkpoint_head_sha256']
        p=self.a.prepare(limit=1);self.a.submit(p,self.answer(p))
        self.assertEqual(self.fix.owner.progress()['checkpoint_head_sha256'],before)
    def test_11_db_record_tamper(self):
        p=self.a.prepare(limit=1);self.a.submit(p,self.answer(p))
        with sqlite3.connect(self.path) as db:db.execute("UPDATE judgments SET record='{}'")
        with self.assertRaisesRegex(InvalidInput,'JUDGMENT_TAMPER'):
            self.a.status()
    def test_12_private_db_permissions(self):
        os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,'JOURNAL_PERMISSIONS_OR_RESUME'):
            E3TripletAlignment(self.fix.engine,self.path,**self.init_args)
    def test_13_no_gold_even_full_parent_census(self):
        p=self.a.prepare(limit=2);self.a.submit(p,self.answer(p))
        s=self.a.status();self.assertEqual(s['reviewed_parents'],2)
        self.assertEqual(s['unreviewed_parents'],0)
        self.assertIsNone(s['precision']);self.assertIsNone(s['recall'])
        self.assertFalse(s['e3_quality_certified'])
    def test_14_wrong_relation_reference_combination(self):
        p=self.a.prepare(limit=1);a=self.answer(p)
        a['reviews'][0]['claim_alignments'][0]['first_relation']='MISSING_IN_OLDER'
        with self.assertRaisesRegex(InvalidInput,'RELATION_REFERENCE_CONFLICT'):
            self.a.submit(p,a)
    def test_15_manual_same_parent_not_finance_truth(self):
        p=self.a.prepare(limit=1);self.a.submit(p,self.answer(p))
        s=self.a.status()
        self.assertEqual(s['relation_counts']['FIRST:EQUIVALENT_PROVISIONAL'],1)
        self.assertFalse(s['exact_parent_equality_or_financial_truth_certified'])

if __name__=='__main__':unittest.main()