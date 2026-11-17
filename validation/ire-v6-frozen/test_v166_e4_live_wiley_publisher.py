"""LIVE publisher TLS bytes for B0001 source bibliography (NOT finance law).

This is a network smoke check with exact first-party publisher evidence,
not a ChatGPT final verdict, not a true video publication.
"""
from __future__ import annotations
import json
import unittest
from v166_e4_bibliographic_primary import (
    fetch_wiley_publisher_bytes,audit_original_publisher_book_metadata)

class LiveWileyPublisherEvidenceTests(unittest.TestCase):
    def test_01_real_wiley_title_author_isbn_bytes(self):
        body=fetch_wiley_publisher_bytes()
        receipt=audit_original_publisher_book_metadata(body)
        receipt["publisher_original_body_bytes"]=len(body)
        print(json.dumps(receipt,sort_keys=True))
        self.assertGreater(receipt["publisher_original_body_bytes"],150)
        self.assertFalse(receipt["research_final_approval"])


if __name__=="__main__":
    unittest.main()
