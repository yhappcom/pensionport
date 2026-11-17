"""LIVE first-party Pabrai Funds issuer data, only fund RULES provenance.

A fund's own marketing claims of superior investment performance are NOT
independently certified by this test. The 1950s Buffett similarity only
concerns fund operational rules, not personal investing advice.
"""
from __future__ import annotations

import json
import unittest
from v166_e4_pabrai_partnership_context import (
    fetch_pabrai_fund_original_bytes,
    audit_pabrai_fund_first_party_words)

class V166E4LivePabraiFundIssuer(unittest.TestCase):
    def test_01_original_issuer_https_structure_only_no_success_causality(self):
        body=fetch_pabrai_fund_original_bytes()
        result=audit_pabrai_fund_first_party_words(body)
        result["original_raw_bytes"]=len(body)
        print(json.dumps(result,sort_keys=True))
        self.assertTrue(result["fund_management_rules_based_on_buffett_claimed_by_issuer"])
        self.assertFalse(result["actual_investment_performance_independently_audited"])
        self.assertFalse(result["causal_success_proven"])

if __name__=="__main__":
    unittest.main()
