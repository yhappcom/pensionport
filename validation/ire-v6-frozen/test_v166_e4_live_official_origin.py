"""Live E4 official-origin smoke test: authentic website bytes, no mock.

Passing does NOT certify semantic applicability, current-law interpretation,
the source speech in B0001 or individualized investment advice.
Network outage results in an E4 origin-evidence BLOCK, not fake approval.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from urllib.error import HTTPError, URLError

from v166_e4_primary_approval_gate import _fetch_approved_primary_https

SOURCES=(
    ("NTS_PENSION_GUIDANCE",
     "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6449",
     (b"\xec\x97\xb0\xea\xb8\x88", b"\xec\x84\xb8\xec\x95\xa1\xea\xb3\xb5\xec\xa0\x9c")),
    ("MOLEG_LAW_SEARCH_PORTAL",
     "https://www.law.go.kr/lsSc.do?menuId=0",
     (b"\xeb\xb2\x95\xeb\xa0\xb9",)),
)


class V166LiveOfficialSourceOrigin(unittest.TestCase):
    def test_01_at_least_one_genuine_official_https_origin_retrievable(self):
        errors=[]
        for title,url,tokens in SOURCES:
            try:
                body=_fetch_approved_primary_https(url)
                matching=all(token in body for token in tokens)
                info={"source":title,"bytes":len(body),
                      "sha256":hashlib.sha256(body).hexdigest(),
                      "all_minimal_keyword_bytes_found":matching,
                      "real_official_source_received":True,
                      "legal_interpretation_certified":False,
                      "chatgpt_final_fact_approval":False}
                print(json.dumps(info,sort_keys=True))
                self.assertTrue(matching, "E4_ORIGIN_RECEIVED_BUT_TOPIC_TEXT_MISSING")
                return
            except (HTTPError,URLError,TimeoutError,ConnectionError,
                    AssertionError,ValueError) as exc:
                errors.append({"source":title,"type":type(exc).__name__,
                               "detail":str(exc)[:100]})
        self.fail("E4_NO_AUTHENTIC_REAL_OFFICIAL_PRIMARY_AVAILABLE:"+json.dumps(errors))


if __name__=="__main__":
    unittest.main(verbosity=2)
