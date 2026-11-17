"""Live issuer evidence, not owner-video V123 approval."""
import json
import unittest
from v166_e4_buffett_retrospective_primary import (
    URL_2001,URL_2020,fetch_primary,audit_primary_retrospectives)

class E4BuffettLiveRetrospectives(unittest.TestCase):
    def test_01_official_retrospectives_preserve_both_return_goal_and_loss_caution(self):
        a=fetch_primary(URL_2001)
        b=fetch_primary(URL_2020)
        proof=audit_primary_retrospectives(a,b)
        self.assertTrue(proof["founding_1956_relative_benchmark_and_no_return_promise_attested"])
        self.assertTrue(proof["permanent_capital_loss_aversion_attested"])
        self.assertFalse(proof["six_percent_is_guaranteed_return"])
        self.assertFalse(proof["actual_1957_original_letter_authenticated"])
        self.assertFalse(proof["research_knowledge_release_authorized"])
        print(json.dumps(proof,sort_keys=True))

    def test_02_refuse_lookalike_OR_redirect_url(self):
        from ire.v6.errors import InvalidInput
        with self.assertRaises(InvalidInput):
            fetch_primary("https://berkshirehathaway.com.example.org/letters/2020ltr.pdf")

if __name__=="__main__":unittest.main()
