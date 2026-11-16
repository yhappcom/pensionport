"""Public conditional finance educational checks. Not issuer-byte authentication."""
import unittest
from v140_current_rule_safety import current_rule_preflight,advisory_route_acceptance,ScopeError
class V140CurrentRuleCases(unittest.TestCase):
 def test_01_isa_unknown_conditions_stays_open(self):
  x=current_rule_preflight({'kind':'ISA','as_of':'2026-11-16'})
  self.assertIsNone(x['statutory_exemption_cap_won']);self.assertFalse(x['personal_tax_or_investment_advice_approved'])
 def test_02_isa_verified_eligible_400man_is_not_500man(self):
  x=current_rule_preflight({'kind':'ISA','as_of':'2026-11-16','statutory_400man_condition_verified':True})
  self.assertEqual(x['statutory_exemption_cap_won'],4_000_000)
 def test_03_isa_general_200man(self):
  x=current_rule_preflight({'kind':'ISA','as_of':'2026-11-16','statutory_general_case_verified':True,'statutory_400man_condition_verified':False})
  self.assertEqual(x['statutory_exemption_cap_won'],2_000_000)
 def test_04_no_salary_only_auto_400man(self):
  x=current_rule_preflight({'kind':'ISA','as_of':'2026-11-16','salary_won':40_000_000})
  self.assertIsNone(x['statutory_exemption_cap_won'])
 def test_05_pension_600_900_combined_not_each(self):
  x=current_rule_preflight({'kind':'PENSION','as_of':'2026-11-16'})
  self.assertEqual((x['pension_savings_max_credit_base_won'],x['combined_account_max_credit_base_won']),(6_000_000,9_000_000))
  self.assertIsNone(x['statutory_credit_rate_percent'])
 def test_06_pension_credit_15pct_conditional(self):
  x=current_rule_preflight({'kind':'PENSION','as_of':'2026-11-16','income_threshold_15_percent_verified':True})
  self.assertEqual(x['statutory_credit_rate_percent'],15)
  self.assertFalse(x['personal_tax_or_investment_advice_approved'])
 def test_07_pension_credit_12pct_conditional(self):
  x=current_rule_preflight({'kind':'PENSION','as_of':'2026-11-16','income_threshold_15_percent_verified':False})
  self.assertEqual(x['statutory_credit_rate_percent'],12)
 def test_08_wrong_asof_rejected(self):
  with self.assertRaises(ScopeError): current_rule_preflight({'kind':'ISA','as_of':'2024-01-01'})
 def test_09_no_source_final_pass_means_no_e2e(self):
  flags={k:True for k in ('source_v123_passed','parent_knowledge_published','real_operational_db_attested','original_issuer_bytes_sha_verified','effective_law_and_issuer_scope_verified','v5_v23_live_current_law_run_executed','actual_user_facts_verified')}
  flags['source_v123_passed']=False
  x=advisory_route_acceptance(**flags)
  self.assertIn('source_v123_passed',x['unproven_gates']);self.assertFalse(x['p0_go'])
 def test_10_all_synthetic_flags_do_not_execute_personal_orders(self):
  flags={k:True for k in ('source_v123_passed','parent_knowledge_published','real_operational_db_attested','original_issuer_bytes_sha_verified','effective_law_and_issuer_scope_verified','v5_v23_live_current_law_run_executed','actual_user_facts_verified')}
  x=advisory_route_acceptance(**flags)
  self.assertFalse(x['full_real_e2e_certified']);self.assertFalse(x['personal_order_enabled'])
if __name__=='__main__':unittest.main(verbosity=2)
