"""First-party corporate letters timing: factual scope only; C00009/C00010 OPEN."""
import unittest
from ire.v6.errors import InvalidInput,QualityNotProven
from v166_e4_corporate_historical_primary import (
    audit_berkshire_letters_catalogue_only,_validate_url,URL)

FAKE=("<html><title>BERKSHIRE HATHAWAY INC.</title>"
      "<h1>SHAREHOLDER LETTERS</h1><p>1977</p>"
      "<p>Full letters from 1965 through 2024</p></html>").encode("utf-8")*4
SRC="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
OPEN={"C00009":"OPEN","C00010":"OPEN"}

class V166E4BerkshireCorporateScopeTests(unittest.TestCase):
    def test_01_both_real_owner_open_verdicts_still_hold_with_corporate_archive(self):
        d=audit_berkshire_letters_catalogue_only(
            FAKE,source_sha256=SRC,b0001_statuses=OPEN)
        self.assertTrue(d["only_corporate_archive_range_supported"])
        self.assertEqual(d["C00009_native_v123_status_after_context"],"OPEN")
        self.assertEqual(d["C00010_native_v123_status_after_context"],"OPEN")
        self.assertFalse(d["third_party_book_volume_composition_authenticated"])
        self.assertFalse(d["early_partnership_investment_style_authenticated"])

    def test_02_issuer_letters_index_cannot_certify_partnership_1957(self):
        no_1965=FAKE.replace(b"1965",b"1957")
        with self.assertRaises(QualityNotProven):
            audit_berkshire_letters_catalogue_only(
                no_1965,source_sha256=SRC,b0001_statuses=OPEN)

    def test_03_subjective_owner_claim_autoapproved_rejected(self):
        with self.assertRaises(InvalidInput):
            audit_berkshire_letters_catalogue_only(
                FAKE,source_sha256=SRC,
                b0001_statuses={"C00009":"ACCEPT_FOR_RESEARCH","C00010":"OPEN"})

    def test_04_company_official_url_phishing_rejected(self):
        _validate_url(URL)
        for url in ("http://www.berkshirehathaway.com/letters/letters.html",
                    "https://www.berkshirehathaway.com.evil.test/letters/letters.html",
                    "https://www.berkshirehathaway.com:444/letters/letters.html"):
            with self.subTest(url=url),self.assertRaises(InvalidInput):
                _validate_url(url)

if __name__=="__main__":
    unittest.main()
