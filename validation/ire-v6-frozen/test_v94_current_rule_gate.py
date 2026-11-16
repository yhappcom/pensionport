import unittest,copy
from v94_current_rule_gate import route_claim_to_rule,review_ledger,validate_rule
class T(unittest.TestCase):
 def setUp(self):
  self.rule={'rule_id':'ISA_TAX_91_18','source_url':'https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1033238719','effective_from':'2026-09-18','effective_to':None,'checked_at':'2026-11-14','source_status':'OFFICIAL_PAGE_CHECKED_SCOPE_ONLY','required_facts':['asset_type','opened_at'],**{x:False for x in ['financial_fact_certified','personalized_advice_approved','independent_gold']}}
  self.claim={'rule_id':'ISA_TAX_91_18','utterance_as_of':'2024-10-10','client_facts':{'asset_type':'ETF','opened_at':'2025-02-03'}}
 def check(self,rule=None,claim=None,today='2026-11-14'):return route_claim_to_rule(self.claim if claim is None else claim,self.rule if rule is None else rule,today=today)
 def test_scope_pass_not_approval(self):
  x=self.check();self.assertEqual(x['decision'],'CURRENT_SCOPE_REVIEW_ONLY');self.assertFalse(x['personal_advice_allowed'])
 def test_missing_personal_fact(self):
  c=copy.deepcopy(self.claim);del c['client_facts']['asset_type'];self.assertEqual(self.check(claim=c)['decision'],'CLIENT_APPLICABILITY_UNKNOWN')
 def test_old_statute(self):
  r=copy.deepcopy(self.rule);r['checked_at']='2025-12-31';r['source_status']='FUTURE_ENACTED_NOT_IN_FORCE'
  self.assertEqual(self.check(rule=r,today='2026-01-01')['decision'],'NOT_CURRENT_EFFECTIVE_RULE')
 def test_stale_source(self):self.assertEqual(self.check(today='2027-04-01')['decision'],'STALE_OFFICIAL_SOURCE_RECHECK')
 def test_future_claim(self):
  c=copy.deepcopy(self.claim);c['utterance_as_of']='2027-12-30'
  with self.assertRaises(ValueError):self.check(claim=c)
 def test_unofficial_domain(self):
  r=copy.deepcopy(self.rule);r['source_url']='https://not-law.go.kr.fake.example/a'
  with self.assertRaises(ValueError):self.check(rule=r)
 def test_impossible_date(self):
  r=copy.deepcopy(self.rule);r['effective_from']='2026-02-30'
  with self.assertRaises(ValueError):self.check(rule=r)
 def test_future_enacted(self):
  r=copy.deepcopy(self.rule);r['effective_from']='2027-01-01';r['source_status']='FUTURE_ENACTED_NOT_IN_FORCE';self.assertEqual(self.check(rule=r)['decision'],'NOT_CURRENT_EFFECTIVE_RULE')
 def test_fake_approval(self):
  r=copy.deepcopy(self.rule);r['financial_fact_certified']=True
  with self.assertRaises(ValueError):self.check(rule=r)
 def test_ledger(self):
  x=review_ledger([self.claim],[self.rule],today='2026-11-14');self.assertEqual(x['claims_checked'],1);self.assertEqual(x['new_financial_fact_approvals'],0)
 def test_duplicate_rules(self):
  with self.assertRaises(ValueError):review_ledger([self.claim],[self.rule,self.rule],today='2026-11-14')
if __name__=='__main__':unittest.main()