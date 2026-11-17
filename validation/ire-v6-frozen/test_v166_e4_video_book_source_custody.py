"""Synthetic owner-cue bibliography test, not live or finance-law approval."""
import copy
import unittest

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from v166_e4_video_book_source_custody import assess_book_citation_against_primary

NOTE=("원문 화자가 책의 한국어 제목 또는 음역 제목을 소개한 발언만 "
      "서지정보와 대조합니다. 자동 전사의 저자 이름이 다를 수 있으므로 "
      "음성 재검토 전 화자의 실제 이름 발음을 인증하지 않으며 투자 성과와 "
      "법령 적용성은 전혀 확인하지 않았습니다.")
BOOK=("<html><h1>The Dhandho Investor</h1><p>Mohnish Pabrai</p>"
      "<p>9780470043899</p></html>").encode("utf8")*3

class V166E4OwnerBookEvidenceCustodyTests(unittest.TestCase):
    def setUp(self):
        texts=["원래 제목 단도 인베스터입니다.",
               "투자를 어떻게 할 것인가입니다.",
               "작가는 모니시 바브라입니다.",
               "다른 문장입니다."]
        raw=make_srt(texts)
        m=make_manifest(raw)
        self.source=verify_source(raw,m,expected_source_sha256=sha256(raw),
                                  expected_manifest_sha256=json_digest(m))
        self.atom={"claim_id":"C00006","kind":"FACT","context_cue_indices":[1],
                   "source_refs":[{"cue_index":1,"quote":texts[0]}],
                   "speaker":"UNKNOWN","proposition":"원서 제목을 소개한다."}
        self.verdict={"claim_id":"C00006","atom_sha256":json_digest(self.atom),
                      "status":"ACCEPT_FOR_RESEARCH",
                      "official_body_sha256":sha256(BOOK),
                      "finance_evidence_status":"PRIMARY_BODY_AND_DATE_CHAT_CHECKED"}
        self.k={"source_quote_cue_index":1,"source_quote":texts[0],
                "chat_scope_note":NOTE,
                "chat_note_sha256":sha256(NOTE.encode("utf8"))}

    def check(self,**kw):
        args=dict(self.k);args.update(kw)
        return assess_book_citation_against_primary(
            self.source,self.atom,self.verdict,BOOK,**args)

    def test_01_accepted_original_title_has_source_and_publisher_but_not_release(self):
        r=self.check()
        self.assertTrue(r["bibliographic_primary_support"])
        self.assertEqual(r["v123_status_after_check"],"ACCEPT_FOR_RESEARCH")
        self.assertFalse(r["full_child_chat_final_pass"])
        self.assertFalse(r["research_knowledge_release_authorized"])

    def test_02_open_title_author_source_remains_open(self):
        self.atom["claim_id"]="C00002"
        self.verdict["claim_id"]="C00002"
        self.verdict["atom_sha256"]=json_digest(self.atom)
        self.verdict["status"]="OPEN"
        self.verdict["official_body_sha256"]=None
        r=self.check()
        self.assertEqual(r["v123_status_after_check"],"OPEN")
        self.assertEqual(r["classification"],
                         "PARTIAL_PRIMARY_SUPPORT_NATIVE_V123_OPEN")

    def test_03_fake_srt_quote_rejected(self):
        with self.assertRaises(InvalidInput):
            self.check(source_quote="원본에 없는 단도 인베스터입니다")

    def test_04_publisher_body_digest_drift_rejected(self):
        self.verdict["official_body_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            self.check()

    def test_05_false_audio_authentication_rejected(self):
        with self.assertRaises(InvalidInput):
            self.check(original_audio_authenticated=True)

    def test_06_rejected_chat_row_cannot_change_to_bibliographic_pass(self):
        self.verdict["status"]="REJECT"
        with self.assertRaises(InvalidInput):
            self.check()

    def test_07_unrelated_book_fails_factual_primary_custody(self):
        with self.assertRaises(QualityNotProven):
            assess_book_citation_against_primary(
                self.source,self.atom,self.verdict,
                BOOK.replace(b"The Dhandho Investor",b"Another Book"),**self.k)

    def test_08_review_note_digest_drift_rejected(self):
        with self.assertRaises(InvalidInput):
            self.check(chat_note_sha256="c"*64)


    def test_09_context_neighbor_cannot_replace_atom_direct_book_quote(self):
        self.atom["context_cue_indices"].append(2)
        # Same real source cue, but that cue was never referenced by the
        # original atom itself. The V123 atom hash is recomputed only to
        # exercise the material source_ref gate, not to impersonate V123.
        self.verdict["atom_sha256"]=json_digest(self.atom)
        with self.assertRaisesRegex(InvalidInput,"BOOK_SOURCE_QUOTE_NOT_PINNED"):
            self.check(source_quote_cue_index=2,
                       source_quote=self.source.cues[1].text)


if __name__=="__main__":
    unittest.main()
