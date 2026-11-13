"""V90 public, synthetic-only custody/negative P0/ISA-NPS routing regression tests.
No real subtitles and no human-in-chat meaning appear in this test file.
These tests do not independently validate semantic precision or financial advice.
"""
from __future__ import annotations
import copy,unittest
from dataclasses import dataclass
from v90_source_advisory_gate import (VIDEO_ID,EXPECTED,FALSE_FLAGS,KINDS,ROUTING,
    check_review,check_screen,verify_batch,shadow_advice_gate,risk_route,no_false_p0,sha)
from v87_targeted_source_guard import expected_parent_source
@dataclass
class Cue:
    index:int
    start_ms:int
    end_ms:int
    text:str
LONG_MEANING='합성 시나리오에 있는 화자는 투자와 연금의 조건을 설명하고 있지만 아직 공식 증거로 승인된 주장은 아니며 질문과 회상이라는 해석 범위를 별도로 구분해야 합니다.'
LONG_RISK='합성 시나리오에서는 개인의 계좌형태와 금융법령 적용시점, 수익률과 현금흐름을 모르는 상태에서 투자 권고 또는 세무 결론을 자동적으로 생성하거나 승인해서는 안 됩니다.'

class V90SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cues=[Cue(i,100*i,100*i+90,f'합성 조건부 금융 자막 {i}번, 가정과 질문입니다') for i in range(1,10729)]
        cls.regs={};cls.all_screens=[]
        for n in range(1,270):
            w=f'W{n:05d}';fst=(n-1)*40+1;last=min(n*40,len(cls.cues))
            keys=EXPECTED.get(w,(f'FAKE_{n:05d}',));parents=[]
            for i,k in enumerate(keys):
                cue_idx=fst+i*7
                content=cls.cues[cue_idx-1].text
                parents.append({'claim_id':k,'cue_indices':[cue_idx],
                                'source_text_sha256':sha(content.encode('utf-8'))})
            cls.regs[w]=parents
            full=' '.join(cls.cues[i-1].text for i in range(fst,last+1))
            cls.all_screens.append({'window_id':w,'video_no':7,'video_id':VIDEO_ID,
               'first_cue':fst,'last_cue':last,'source_window_sha256':sha(full.encode('utf-8')),
               'draft_parent_count':len(parents),'manual_reviewed_all_parents':False,
               'fact_approved':False,'independent_gold':False,'personal_action_approved':False})
        cls.selected=[s for s in cls.all_screens if s['window_id'] in EXPECTED]
        cls.rows=[]
        for w,claims in EXPECTED.items():
            for c in claims:
                src=expected_parent_source(cls.cues,cls.regs,(w,c))
                rec={**src,'video_no':7,'video_id':VIDEO_ID,'status':'SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD',
                 'semantic_kind':'HISTORICAL_CASE','risk_domain':'SYNTHETIC_BOUNDARY',
                 'speaker_meaning_private':LONG_MEANING,'scope_caution_private':LONG_RISK,
                 **{f:False for f in FALSE_FLAGS}}
                cls.rows.append(rec)
        available=[f'W{i:05d}' for i in range(180,270) if f'W{i:05d}' not in EXPECTED]
        used=available[:53]
        cls.prior={(used[i%53],f'PREVIOUS_{i:05d}') for i in range(157)}
        if not (len(cls.prior)==157 and len({w for w,c in cls.prior})==53):
            raise ValueError('Synthetic fixture prior lineage invalid')

    def test_positive_complete_batch_preserves_no_go(self):
        result=verify_batch(self.rows,self.selected,self.all_screens,self.cues,self.regs,self.prior)
        self.assertEqual(result['new_manual_parents'],48)
        self.assertEqual(result['cumulative_shadow_parents'],205)
        self.assertEqual(result['cumulative_sampled_windows'],65)
        self.assertEqual(result['video7_windows_without_parent_sample'],204)
        self.assertFalse(result['p0_go'])
        self.assertFalse(result['independent_gold'])
    def test_no_gold_disposition_frozen(self):
        r=no_false_p0();self.assertEqual(r['v75_887_official_pending_unchanged'],887)
        self.assertEqual(r['audio_open_unchanged'],3)
        for k in ('v75_history_membership_verified','independent_precision_recall_certified','financial_fact_certified','master116_merged','personalized_advice_approved','p0_go'):
            self.assertFalse(r[k])
    def test_p3_promotion_explicitly_blocked(self):
        decision=shadow_advice_gate(self.rows[0]);self.assertEqual(decision,{'can_promote_to_p3_advice':False,'can_merge_into_master116':False,'can_count_as_gold':False})
    def test_source_excerpt_mutation_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['source_excerpt_private']='fake excerpt'
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_context_mutation_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['adjacent_cues_private'][0]['text_private']='invented'
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_source_hash_mutation_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['source_sha256']='0'*64
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_missing_meaning_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['speaker_meaning_private']='short'
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_missing_limit_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['scope_caution_private']='short'
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_parent_wrong_video_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['video_no']=6
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_parent_wrong_cues_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['cue_indices']=[10000]
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_wrong_category_rejected(self):
        row=copy.deepcopy(self.rows[0]);row['semantic_kind']='FACT_CERTIFIED'
        with self.assertRaises(ValueError):check_review(row,self.cues,self.regs)
    def test_window_wrong_source_hash_rejected(self):
        screen=copy.deepcopy(self.selected[0]);screen['source_window_sha256']='0'*64
        with self.assertRaises(ValueError):check_screen(screen,self.all_screens,self.cues,self.regs)
    def test_window_false_all_parents_rejected(self):
        screen=copy.deepcopy(self.selected[0]);screen['manual_reviewed_all_parents']=True
        with self.assertRaises(ValueError):check_screen(screen,self.all_screens,self.cues,self.regs)
    def test_selected_windows_exact_set(self):
        sel=copy.deepcopy(self.selected);sel[0]=copy.deepcopy(sel[1])
        with self.assertRaises(ValueError):verify_batch(self.rows,sel,self.all_screens,self.cues,self.regs,self.prior)
    def test_prior_count_not_157_rejected(self):
        wrong=set(self.prior);wrong.pop()
        with self.assertRaises(ValueError):verify_batch(self.rows,self.selected,self.all_screens,self.cues,self.regs,wrong)
    def test_prior_window_overlap_rejected(self):
        wrong=set(self.prior);wrong.remove(next(iter(wrong)));wrong.add(('W00142','PREVIOUS_OVERLAP'))
        with self.assertRaises(ValueError):verify_batch(self.rows,self.selected,self.all_screens,self.cues,self.regs,wrong)
    def test_duplicate_batch_rejected(self):
        rows=copy.deepcopy(self.rows);rows[-1]=rows[0]
        with self.assertRaises(ValueError):verify_batch(rows,self.selected,self.all_screens,self.cues,self.regs,self.prior)
    def test_missing_parent_rejected(self):
        rows=self.rows[:-1]
        with self.assertRaises(ValueError):verify_batch(rows,self.selected,self.all_screens,self.cues,self.regs,self.prior)
    def test_unknown_isa_asset_manual_gate(self):
        self.assertEqual(risk_route('ISA_NEW_ASSET','UNKNOWN_TAX'), 'MANUAL_REVIEW_REQUIRED')
    def test_route_non_string_rejected(self):
        with self.assertRaises(ValueError):risk_route(None,'UNKNOWN')
    def test_isa_direct_share_gain_vs_loss_different(self):
        self.assertNotEqual(risk_route('DIRECT_DOMESTIC_LISTED_SHARE','REALIZED_TRADING_GAIN'),risk_route('DIRECT_DOMESTIC_LISTED_SHARE','NET_REALIZED_TRADING_LOSS'))
    def test_isa_domestic_etf_not_direct_share(self):
        self.assertNotEqual(risk_route('DOMESTIC_EQUITY_FUND_ETF','EXEMPT_EQUITY_TRADING_LOSS'),risk_route('DIRECT_DOMESTIC_LISTED_SHARE','NET_REALIZED_TRADING_LOSS'))
    def test_isa_calendar_not_maturity(self):
        self.assertNotEqual(risk_route('ISA','CALENDAR_YEAR_ACCUMULATION'),risk_route('ISA','PENSION_MATURITY_TRANSFER'))
    def test_maturity_bond_not_principal_guaranteed(self):
        self.assertEqual(risk_route('BOND_MATURITY_ETF','PRINCIPAL_GUARANTEE'),'NOT_PRINCIPAL_GUARANTEED')
    def test_nps_credit_not_open_advice(self):
        self.assertEqual(risk_route('NPS','UNEMPLOYMENT_CREDIT'),'NEEDS_AGE_PRIOR_PAYMENTS_INCOME_PROPERTY')
    def test_reit_high_distribution_not_guaranteed(self):
        self.assertEqual(risk_route('REIT','HIGH_DISTRIBUTION_YIELD'),'NOT_GUARANTEED_DISTRIBUTION_OR_TOTAL_RETURN')
    def test_reit_averaging_down_needs_ledger(self):
        self.assertEqual(risk_route('PORTFOLIO','AVERAGING_DOWN_PROFIT'),'REQUIRE_CASHFLOW_LEDGER')
    def test_unknown_category_manual(self):
        self.assertEqual(risk_route('ETF','ANY_TAX'),'MANUAL_REVIEW_REQUIRED')

def make_source_test(w,c):
    def one(self):
        row=next(r for r in self.rows if r['window_id']==w and r['claim_id']==c)
        d=check_review(row,self.cues,self.regs)
        self.assertEqual(len(d),64)
    return one
for wid,keys in EXPECTED.items():
    for cid in keys:setattr(V90SyntheticTests,f'test_source_{wid}_{cid}',make_source_test(wid,cid))

def make_false_go_test(field):
    def bad(self):
        row=copy.deepcopy(self.rows[0]);row[field]=True
        with self.assertRaises(ValueError):shadow_advice_gate(row)
    return bad
for f in FALSE_FLAGS:setattr(V90SyntheticTests,f'test_prohibit_{f}',make_false_go_test(f))
if __name__=='__main__':unittest.main()