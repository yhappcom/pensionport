"""Real original Wiley chapter 1 HTTPS PDF: first-party publisher attribution only.

No private SRT, no external independent Gujarati lexicon, no guaranteed
investment returns, and no ChatGPT final B0001 V123 status promotion.
"""
from __future__ import annotations

import json
import unittest

from v166_e4_wiley_author_chapter import (
    fetch_wiley_original_chapter_pdf,audit_author_original_chapter)

SRT_SHA="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
ORIGINAL_PDF_SHA="870be11899036a19351d1ce8644f833748e9b9618d67233d6a0c162144397024"


class LiveWileyChapterAuthorScope(unittest.TestCase):
    def test_01_publisher_original_https_gujarati_and_nonzero_loss_caveat(self):
        body=fetch_wiley_original_chapter_pdf()
        proof=audit_author_original_chapter(body,owner_source_sha256=SRT_SHA)
        self.assertEqual(proof["official_original_pdf_body_sha256"],ORIGINAL_PDF_SHA)
        self.assertTrue(proof["original_author_also_discusses_nonzero_loss_risk"])
        self.assertFalse(proof["real_world_loss_or_return_limits_certified"])
        print(json.dumps({**proof,"original_body_bytes":len(body)},sort_keys=True))


if __name__=="__main__":
    unittest.main()
