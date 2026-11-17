"""E4 OPEN partial-original fact custody, all source dialogue is SYNTHETIC.

Shows exact *narrow* issuer context while freezing native V123 OPEN, never
attempting V128 publication, no secret original SRT committed.
"""
from __future__ import annotations
import copy
import unittest

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from v166_e4_owner_open_partial_source import (
    OPEN_CLAIMS,assess_open_partial_claim,audit_partial_open_video_census)

NOTE=("ChatGPT 검토 범위: 이 별도 원전에서 확인되는 것은 문헌의 좁은 일부만입니다. "
      "영상 원문의 동일 화자·음역·실제 출판물 선정·수익 목표·성과 원인을 "
      "입증하는 것이 아니며, 원문 3건은 여전히 V123 OPEN입니다. "
      "서지 본문이나 비인증 전사본의 진술만으로 전체 원자 또는 "
      "13구간 부모 통합 지식을 승인하거나 개인 투자자문에 사용하지 않습니다.")
TEXTS={
    "C00002":[
        "이 책의 제목을 제가 투자를 어떻게 할 것인가라고 소개합니다",
        "작가를 언급하며 이름의 한국어 음역은 잘 들리지 않습니다",
        "자동전사에는 바브라라는 단어가 실려 있습니다"],
    "C00009":[
        "화자는 주주서한 선집을 읽었다고 말합니다",
        "주주서한 책의 시점을 설명합니다",
        "그때 이미 자본이 커진 상황이라고 이해합니다"],
    "C00010":[
        "초기 버핏 파트너십 이야기로 넘어갑니다",
        "그때 투자 방식을 공격적이라고 불렀습니다",
        "그 시점 수익 목표는 독립된 자료로 확인해야 합니다"],
}
BODY={
    "C00002":("<html><h1>The Dhandho Investor</h1><p>Mohnish Pabrai</p>"
              "<p>Test page for publisher-author narrow scope only, not speaker audio.</p>"
              "</html>").encode("utf-8"),
    "C00009":("<html><h2>Berkshire Hathaway SHAREHOLDER LETTERS</h2>"
              "<p>1977 1978 2024</p><p>1965 to 2024 complete unedited book</p>"
              "<p>Company archive is not all existing third-party anthologies.</p>"
              "</html>").encode("utf-8"),
    "C00010":("<html><h2>1957 Letter</h2><p>Primary attention to "
              "undervalued securities</p><p>general issues and work-outs</p>"
              "<p>This is a SECONDARY unauthenticated replica fixture, "
              "not an original certificate.</p></html>").encode("utf-8"),
}


def owner_fixture():
    flat=[s for cid in OPEN_CLAIMS for s in TEXTS[cid]]
    raw=make_srt(flat)
    m=make_manifest(raw)
    source=verify_source(raw,m,expected_source_sha256=sha256(raw),
                         expected_manifest_sha256=json_digest(m))
    atoms=[]
    verdicts=[]
    offset=0
    for cid,info in OPEN_CLAIMS.items():
        quotes=TEXTS[cid]
        ix=list(range(offset+1,offset+1+len(quotes)))
        refs=[{"cue_index":i,"quote":t} for i,t in zip(ix,quotes)]
        atom={
            "claim_id":cid,"kind":info["kind"],"stance":info["stance"],
            "source_refs":refs,"context_cue_indices":ix,
            "proposition":"합성 원자 "+cid,
        }
        atoms.append(atom)
        verdicts.append({
            "claim_id":cid,"status":"OPEN",
            "atom_sha256":json_digest(atom),
        })
        offset+=len(quotes)
    return source,atoms,verdicts


class V166E4PartialSourceNativeOpenTests(unittest.TestCase):
    def setUp(self):
        self.source,self.atoms,self.verdicts=owner_fixture()
        self.e={a["claim_id"]:a for a in self.atoms}
        self.v={v["claim_id"]:v for v in self.verdicts}

    def check(self,cid,**changes):
        args={
            "original_body":BODY[cid],
            "review_note":NOTE,
            "review_note_sha256":sha256(NOTE.encode("utf-8")),
            "evidence_source_role":OPEN_CLAIMS[cid]["role"],
            "body_origin_verified":True,
        }
        args.update(changes)
        return assess_open_partial_claim(
            self.source,self.e[cid],self.v[cid],**args)

    def test_01_three_partial_source_types_all_remain_native_open(self):
        docs=[self.check(c) for c in OPEN_CLAIMS]
        for doc in docs:
            self.assertEqual(doc["native_v123_status_after"],"OPEN")
            self.assertFalse(doc["whole_original_claim_supported"])
            self.assertFalse(doc["research_knowledge_release_authorized"])
            self.assertGreaterEqual(len(doc["still_unproven_components"]),2)
            self.assertFalse(doc["transport_origin_independently_verified_by_this_function"])
        report=audit_partial_open_video_census(
            self.source,{"atoms":self.atoms},
            {"atom_verdicts":self.verdicts},docs)
        self.assertEqual(report["n_open_unapproved"],3)
        self.assertEqual(report["e4_status"],"FAIL_ACTUAL_OWNER_PARENT_STILL_HOLD")
        self.assertFalse(report["e5_authorized"])

    def test_02_c00002_publisher_does_not_prove_audio_name(self):
        d=self.check("C00002")
        self.assertIn("SPEAKER_ORIGINAL_AUDIO_AUTHOR_PRONUNCIATION_NOT_VERIFIED",
                      d["still_unproven_components"])
        with self.assertRaisesRegex(InvalidInput,"ORIGIN_AUDIO_OR_SOURCE_ROLE"):
            self.check("C00002",own_audio_authenticated=True)

    def test_03_c00009_official_company_book_not_all_untitled_collections(self):
        d=self.check("C00009")
        self.assertIn("PARTICULAR_BOOK_OR_ANTHOLOGY_NOT_IDENTIFIED",
                      d["still_unproven_components"])
        self.assertIn("UNIVERSAL_ALL_COLLECTIONS_CLAIM_NOT_PROVEN",
                      d["still_unproven_components"])

    def test_04_c00010_secondary_1957_letter_is_never_authenticated_primary(self):
        d=self.check("C00010")
        self.assertEqual(d["caller_declared_source_role"],
                         "UNAUTHENTICATED_1957_SECONDARY_REPRODUCTION")
        self.assertIn("ISSUER_AUTHENTICATED_1957_ORIGINAL_LETTER_ABSENT",
                      d["still_unproven_components"])

    def test_05_change_original_srt_speaker_line_hash_refused(self):
        cid="C00009"
        atom=copy.deepcopy(self.e[cid])
        atom["source_refs"][0]["quote"]="이런 발언은 실제 원본에 없습니다"
        v=copy.deepcopy(self.v[cid])
        v["atom_sha256"]=json_digest(atom)
        with self.assertRaisesRegex(InvalidInput,"DIRECT_SOURCE_CUE"):
            assess_open_partial_claim(
                self.source,atom,v,original_body=BODY[cid],
                review_note=NOTE,review_note_sha256=sha256(NOTE.encode()),
                evidence_source_role=OPEN_CLAIMS[cid]["role"],
                body_origin_verified=True)

    def test_06_cannot_promote_one_open_to_accepted_by_supplemental_body(self):
        cid="C00002"
        self.v[cid]["status"]="ACCEPT_FOR_RESEARCH"
        with self.assertRaisesRegex(InvalidInput,"NATIVE_V123_OPEN_OR_ATOM_TYPE"):
            self.check(cid)

    def test_07_secondary_1957_cannot_claim_genuine_issuer(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGIN_AUDIO_OR_SOURCE_ROLE"):
            self.check("C00010",
                evidence_source_role="BERKSHIRE_ORIGINAL_SIGNED_PARTNERSHIP_LETTER")

    def test_08_wrong_issuer_page_year_or_title_cannot_support_any_atom(self):
        for cid in OPEN_CLAIMS:
            with self.subTest(cid=cid),self.assertRaisesRegex(
                InvalidInput,"ISSUER_TEXT_ONLY_PARTIAL_NOT_SUPPORTED"):
                self.check(cid,original_body=(b"<html>completely different origin</html>"*8))

    def test_09_missing_chat_review_digest_refused(self):
        with self.assertRaisesRegex(InvalidInput,"INDEPENDENT_CHAT_NOTE_NOT_PINNED"):
            self.check("C00009",review_note_sha256="0"*64)

    def test_10_claim_recycled_across_wrong_source_ref_disallowed(self):
        cid="C00010"
        atom=copy.deepcopy(self.e[cid])
        atom["source_refs"]=self.e["C00009"]["source_refs"]
        atom["context_cue_indices"]=self.e["C00009"]["context_cue_indices"]
        v=copy.deepcopy(self.v[cid])
        v["atom_sha256"]=json_digest(atom)
        with self.assertRaisesRegex(InvalidInput,"OPEN_FULL_CLAIM_CONTEXT_INCOMPLETE"):
            assess_open_partial_claim(self.source,atom,v,
                original_body=BODY[cid],review_note=NOTE,
                review_note_sha256=sha256(NOTE.encode()),
                evidence_source_role=OPEN_CLAIMS[cid]["role"],body_origin_verified=True)

    def test_11_missing_claim_or_duplicated_receipt_cannot_complete_census(self):
        docs=[self.check(c) for c in OPEN_CLAIMS]
        with self.assertRaisesRegex(InvalidInput,"MISSING_OPEN_EVIDENCE"):
            audit_partial_open_video_census(
                self.source,{"atoms":self.atoms},
                {"atom_verdicts":self.verdicts},docs[:-1])
        docs[1]=docs[0]
        with self.assertRaisesRegex(InvalidInput,"MISSING_OPEN_EVIDENCE"):
            audit_partial_open_video_census(
                self.source,{"atoms":self.atoms},
                {"atom_verdicts":self.verdicts},docs)

    def test_12_fake_full_v123_pass_receipt_cannot_ever_complete_census(self):
        docs=[self.check(c) for c in OPEN_CLAIMS]
        docs[2]["native_v123_status_after"]="ACCEPT_FOR_RESEARCH"
        with self.assertRaisesRegex(InvalidInput,"MISSING_OPEN_EVIDENCE"):
            audit_partial_open_video_census(
                self.source,{"atoms":self.atoms},
                {"atom_verdicts":self.verdicts},docs)

    def test_13_any_fake_first_party_origin_stays_unverified(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGIN_AUDIO_OR_SOURCE_ROLE"):
            self.check("C00002",body_origin_verified=False)


if __name__=="__main__":
    unittest.main()
