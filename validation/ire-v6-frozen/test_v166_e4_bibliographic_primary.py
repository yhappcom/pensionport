"""Wiley first-party title/author proof, not a substitute for V123 ChatGPT."""
import unittest
from ire.v6.errors import InvalidInput,QualityNotProven
from v166_e4_bibliographic_primary import (
    EXPECTED,WILEY_ORIGINAL,_validate_publisher_url,
    audit_original_publisher_book_metadata)

BOOK=("<html><h1>The Dhandho Investor</h1><p>Mohnish Pabrai</p>"
      "<p>ISBN 978-0-470-04389-9</p></html>").encode("utf-8")*3


class V166E4BookPublisherSourceTests(unittest.TestCase):
    def test_01_original_publisher_book_metadata_exact_title_author_isbn(self):
        r=audit_original_publisher_book_metadata(BOOK)
        self.assertEqual(r["original_english_title"],EXPECTED["original_english_title"])
        self.assertFalse(r["korean_translation_publisher_verified"])
        self.assertFalse(r["historical_buffett_performance_verified"])
        self.assertFalse(r["research_final_approval"])

    def test_02_unrelated_book_in_wiley_domain_cannot_support_b0001(self):
        unrelated=BOOK.replace(b"The Dhandho Investor",b"Other Book")
        with self.assertRaises(QualityNotProven):
            audit_original_publisher_book_metadata(unrelated)

    def test_03_author_swap_does_not_inherit_publisher_approval(self):
        with self.assertRaises(QualityNotProven):
            audit_original_publisher_book_metadata(
                BOOK.replace(b"Mohnish Pabrai",b"Other Author"))

    def test_04_hostname_phishing_and_http_denied(self):
        _validate_publisher_url(WILEY_ORIGINAL)
        for url in ("http://www.wiley.com/en-us/book",
                    "https://www.wiley.com.evil.test/en-us/book",
                    "https://www.wiley.com:8080/en-us/book"):
            with self.subTest(url=url),self.assertRaises(InvalidInput):
                _validate_publisher_url(url)


if __name__=="__main__":
    unittest.main()
