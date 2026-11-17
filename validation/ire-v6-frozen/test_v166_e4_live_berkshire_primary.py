"""Live Berkshire issuer archive bytes for B0001 OPEN-context evidence only."""
import json
import unittest
from v166_e4_corporate_historical_primary import (
    fetch_official_berkshire_letters_index,audit_berkshire_letters_catalogue_only)

OWNER_SHA="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"

class V166E4LiveBerkshireOrigin(unittest.TestCase):
    def test_01_actual_bh_issuer_https_original_index_cannot_approve_owner_opinion(self):
        body=fetch_official_berkshire_letters_index()
        receipt=audit_berkshire_letters_catalogue_only(
            body,source_sha256=OWNER_SHA,
            b0001_statuses={"C00009":"OPEN","C00010":"OPEN"})
        receipt["actual_issuer_body_bytes"]=len(body)
        print(json.dumps(receipt,sort_keys=True))
        self.assertEqual(receipt["C00009_native_v123_status_after_context"],"OPEN")
        self.assertEqual(receipt["C00010_native_v123_status_after_context"],"OPEN")
        self.assertFalse(receipt["real_owner_knowledge_autoapproved"])

if __name__=="__main__":
    unittest.main()
