"""60 synthetic V89 tests. Never reads raw owner SRT/private annotations.
Passing tests DO NOT certify semantic precision, recall or tax advice.
"""
from __future__ import annotations
import copy,unittest
from dataclasses import dataclass
from v89_isa_source_guard import (EXPECTED,FALSE_FLAGS,ISA_SCOPE_ASOF,scope_isa,
                                  check_one_parent,verify_batch,verify_source_screens,
                                  no_false_go_disposition,sha)
from v87_targeted_source_guard import expected_parent_source

@dataclass
class Cue:
    index:int
    start_ms:int
    end_ms:int
    text:str

LONG_MEANING='합성 테스트 발화 해석은 원래 화자의 조건과 질문을 보존하며 실제 투자상품의 수익이나 법적 판단을 인증하지 않는다는 의미입니다. 복합 발화의 화자별 맥락을 대조합니다.'
LONG_CAUTION='합성 테스트 위험 경고는 현행 제도와 역사적 사실 및 개인별 조건을 구분해야 한다는 뜻입니다. 세법 또는 투자상품의 안정성을 확정하지 않습니다.'

class V89SyntheticCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cues=[Cue(i,i*100,i*100+400,f'합성 자막 {i}번 투자금, 가정, 조건을 검증합니다') for i in range(1,10729)]
        cls.regs={};cls.all269=[]
        for n in range(1,270):
            wid=f'W{n:05d}'; fst=(n-1)*40+1;last=min(n*40,len(cls.cues))
            parents=[]
            keys=EXPECTED.get(wid,(f'C_FAKE_{n}',))
            for ix,cid in enumerate(keys):
                cue_idx=fst+ix*7
                text=cls.cues[cue_idx-1].text
                parents.append({'claim_id':cid,'cue_indices':[cue_idx],'source_text_sha256':sha(text.encode('utf-8'))})
            cls.regs[wid]=parents
            window_txt=' '.join(cls.cues[i-1].text for i in range(fst,last+1))
            cls.all269.append({'window_id':wid,'video_no':7,'video_id':'4CQ4FjGT2gA',
             'screen_status':'SOURCE_BOUND_AUTOMATED_SCREEN_NOT_GOLD',
             'first_cue':fst,'last_cue':last,'draft_parent_count':len(parents),
             'source_window_sha256':sha(window_txt.encode('utf-8')),
             'manual_reviewed_all_parents':False,'fact_approved':False,
             'personal_action_approved':False,'independent_gold':False})
        cls.selected=[r for r in cls.all269 if r['window_id'] in EXPECTED]
        cls.rows=[]
        for w,cs in EXPECTED.items():
            for c in cs:
                src=expected_parent_source(cls.cues,cls.regs,(w,c))
                rec={**src,'video_no':7,'video_id':'4CQ4FjGT2gA','status':'SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD',
                     'semantic_kind':'HISTORICAL_CASE','risk_domain':'SYNTHETIC_TESTING',
                     'speaker_meaning_private':LONG_MEANING,'scope_caution_private':LONG_CAUTION}
                rec.update({f:False for f in FALSE_FLAGS});cls.rows.append(rec)
        windows=[f'W{i:05d}' for i in range(250,270)]+[f'W{i:05d}' for i in range(30,51)]
        cls.prior={(windows[j%41],f'PREV_{j:05d}') for j in range(109)}
        assert len(cls.prior)==109 and len({w for w,c in cls.prior})==41

    def test_source_excerpt_forgery_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['source_excerpt_private']='forged excerpt'
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_context_forgery_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['adjacent_cues_private'][0]['text_private']='modified context'
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_audio_forgery_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['audio_verified']=True
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_financial_fact_approval_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['fact_approved']=True
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_gold_label_approval_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['independent_gold']=True
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_official_parent_merging_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['official_parent_merged']=True
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_personal_advice_approval_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['personalized_advice_approved']=True
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_v75_lineage_forgery_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['v75_membership_verified']=True
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_short_meaning_rejected(self):
        x=copy.deepcopy(self.rows[0]);x['speaker_meaning_private']='fine'
        with self.assertRaises(ValueError):check_one_parent(x,self.cues,self.regs)
    def test_48_batch_duplicate_rejected(self):
        rows=copy.deepcopy(self.rows);rows[-1]=rows[0]
        with self.assertRaises(ValueError):verify_batch(rows,self.cues,self.regs,self.prior,self.selected,self.all269)
    def test_12_window_previous_overlap_rejected(self):
        wrong=set(self.prior); wrong.remove(next(iter(wrong)));wrong.add(('W00012','OLD_PARENT'))
        with self.assertRaises(ValueError):verify_batch(self.rows,self.cues,self.regs,wrong,self.selected,self.all269)
    def test_isa_scope_and_no_false_p0(self):
        self.assertEqual(ISA_SCOPE_ASOF,'2026-11-13')
        self.assertEqual(scope_isa('DIRECT_DOMESTIC_LISTED_SHARE','REALIZED_TRADING_GAIN'),'NON_TAXABLE_GAIN_EXCLUDED')
        self.assertEqual(scope_isa('DIRECT_DOMESTIC_LISTED_SHARE','NET_REALIZED_TRADING_LOSS'),'POTENTIALLY_NETTABLE_IF_ELIGIBLE')
        self.assertEqual(scope_isa('DOMESTIC_EQUITY_FUND_ETF','EXEMPT_EQUITY_TRADING_LOSS'),'NON_TAXABLE_COMPONENT_EXCLUDED')
        self.assertEqual(scope_isa('FUND_OR_ETF','TAXABLE_BASIS_LOSS'),'POTENTIALLY_NETTABLE_BY_TAX_BASIS')
        self.assertEqual(scope_isa('UNVERIFIED_NEW_PRODUCT','UNKNOWN_COMPONENT'),'MANUAL_REVIEW_REQUIRED')
        r=no_false_go_disposition();self.assertFalse(r['p0_go']);self.assertEqual(r['audio_three_unresolved'],3)
        result=verify_batch(self.rows,self.cues,self.regs,self.prior,self.selected,self.all269)
        self.assertEqual(result['cumulative_video7_shadow_parents'],157)
        self.assertEqual(result['video7_windows_without_manual_parent'],216)

def _per_parent_method(w,c):
    def check(self):
        row=next(x for x in self.rows if x['window_id']==w and x['claim_id']==c)
        d=check_one_parent(row,self.cues,self.regs)
        self.assertEqual(len(d),64)
    return check
for wid,cs in EXPECTED.items():
    for cid in cs:
        setattr(V89SyntheticCases,f'test_source_bound_{wid}_{cid}',_per_parent_method(wid,cid))

if __name__=='__main__':unittest.main()