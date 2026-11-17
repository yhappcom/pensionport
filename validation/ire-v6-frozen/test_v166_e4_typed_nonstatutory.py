"""Synthetic typed E4 non-statutory primary provenance, NOT genuine factual approval.

A genuine first-party book title or Berkshire chronology can back its narrow
fact type; neither can prove investment returns, historical opinions, current
tax law or someone else's unknown audio. Every test uses invented cues.
"""
from __future__ import annotations

import copy
import io
import unittest
from reportlab.pdfgen import canvas
from v166_e4_wiley_author_chapter import (
    CHAPTER_URL,audit_author_original_chapter)
from unittest.mock import patch

from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from v166_e4_typed_authority import (
    SCHEMA as TYPE_SCHEMA,CLASS_TO_KIND,audit_e4_source_type_inventory)
from v166_e4_typed_nonstatutory import (
    SCHEMA as NONSTAT_SCHEMA,audit_typed_nonstatutory_research)
from v166_e4_bibliographic_primary import WILEY_ORIGINAL
from v166_e4_corporate_historical_primary import URL as BERKSHIRE_URL
from test_v166_e4_bibliographic_primary import BOOK
from test_v166_e4_corporate_historical_primary import FAKE as BERKSHIRE_FAKE

NOTE=("합성 화자 주장의 근거 유형을 자막 원문에 직접 고정하였습니다. "
      "출판사 서지나 회사 연혁을 투자수익의 증거로 확대하지 않으며, "
      "법령이나 세금·투자 효과에 관한 사실 주장은 별도의 공식 원문·"
      "시행일·조건 검증 없이는 승인하지 않습니다. 독립 정답 인증이나 "
      "개인 투자자문도 승인하지 않습니다.")

def synthetic_wiley_chapter(*,include_caveat=True):
    """Generated original text FIXTURE, absolutely not real Wiley content."""
    buf=io.BytesIO()
    pdf=canvas.Canvas(buf,pagesize=(432,648),pageCompression=0)
    for i in range(17):
        pdf.drawString(22,626,"SYNTHETIC: NOT WILEY ORIGINAL CHAPTER "+str(i))
        pdf.drawString(22,603,"Patel Motel Dhandho")
        pdf.drawString(22,582,"Dhandho (pronounced dhun-doe) is a Gujarati word.")
        pdf.drawString(22,560,"Heads, I win; tails, I don't lose much!")
        if include_caveat:
            pdf.drawString(22,535,"This is not a risk-free bet.")
            pdf.drawString(22,518,"The possibility of going broke must be considered.")
        for j in range(18):
            pdf.drawString(22,490-j*22,
                "Synthetic filler line %d / %d: ONLY CODE UNIT TEST" % (i,j))
        pdf.showPage()
    pdf.save()
    return buf.getvalue()


def case_with_type(quote,kind,stance,category,body=None,status="ACCEPT_FOR_RESEARCH",
                   claim_id=claim_id):
    raw=make_srt([quote,"후속 발언은 검토자 주장과 분리합니다."])
    manifest=make_manifest(raw)
    source=verify_source(raw,manifest,
        expected_source_sha256=sha256(raw),
        expected_manifest_sha256=json_digest(manifest))
    atom={"claim_id":claim_id,"kind":kind,"stance":stance,
          "speaker":"NARRATOR",
          "context_cue_indices":[1],
          "source_refs":[{"cue_index":1,"quote":quote}],
          "condition_cue_indices":[],"exception_cue_indices":[],
          "numeric_references":[],
          "proposition":quote,"owner_window_id":source.owner(1),"as_of":None}
    review_verdict={
        "claim_id":claim_id,"atom_sha256":json_digest(atom),
        "status":status,"private_review_note_sha256":sha256(b"synthetic ChatGPT"),
        "high_risk":True,"financial_claim":True,
        "official_body_sha256":sha256(body) if body else None,
    }
    review={"as_of":"2026-11-17","atom_verdicts":[review_verdict]}
    c={"source":source,"exchange":{"atoms":[atom]},
       "chat_review":review,
       "official_evidence_bodies":{claim_id:body} if body else {}}
    type_row={
        "claim_id":claim_id,"atom_sha256":json_digest(atom),
        "original_cue_index":1,"original_cue_quote":quote,
        "original_cue_quote_sha256":sha256(quote.encode("utf-8")),
        "evidence_class":category,"authority_route":CLASS_TO_KIND[category][1],
        "source_evidence_scope_note":NOTE,
        "source_evidence_scope_note_sha256":sha256(NOTE.encode("utf-8")),
        "v123_original_status":status,
        "unchanged_v123_review_note_sha256":review_verdict["private_review_note_sha256"],
        "financial_claim_flag_only_screening_not_legal_proof":True,
        "reviewer_not_speaker_quote":True,
        "primary_verification_complete":False,
        "independent_gold_certified":False,
        "personal_advice_approved":False,
    }
    type_inventory={
        "schema":TYPE_SCHEMA,
        "source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "chat_review_sha256":json_digest(review),
        "review_executor":"CHATGPT_IN_CHAT",
        "rows":[type_row],
        "private_reviewer_custody_sha256":sha256(b"synthetic primary type"),
        "any_v123_status_changed":False,"any_fact_autoapproved":False,
        "formal_current_law_certified":False,"personal_advice_approved":False,
    }
    evidence={
        "claim_id":claim_id,"evidence_class":category,
        "authority_route":CLASS_TO_KIND[category][1],
        "source_quote_sha256":sha256(quote.encode("utf-8")),
        "chat_meaning_note":NOTE,
        "chat_meaning_note_sha256":sha256(NOTE.encode("utf-8")),
        "primary_url":None,"primary_body_sha256":None,
        "verification_mode":"SOURCE_ONLY_SPEAKER_ATTRIBUTION",
        "original_speaker_audio_verified":False,
        "formal_financial_fact_certified":False,
        "personal_advice_approved":False,
    }
    if category=="PUBLISHER_BOOK_BIBLIOGRAPHY":
        evidence.update(
            primary_url=WILEY_ORIGINAL,
            primary_body_sha256=sha256(body) if body else None,
            verification_mode="PUBLISHER_ORIGINAL_ENGLISH_TITLE")
    elif category=="HISTORICAL_CORPORATE_FACT":
        evidence.update(
            primary_url=BERKSHIRE_URL,
            primary_body_sha256=sha256(body) if body else None,
            verification_mode="BERKSHIRE_ARCHIVE_START_YEAR_1977")
    nonlegal={
        "schema":NONSTAT_SCHEMA,
        "source_sha256":source.source_sha256,
        "chat_review_sha256":json_digest(review),
        "type_inventory_sha256":json_digest(type_inventory),
        "as_of":"2026-11-17",
        "rows":[evidence] if status=="ACCEPT_FOR_RESEARCH" else [],
        "formal_financial_fact_certified":False,
        "personal_advice_approved":False,
    }
    return c,type_inventory,nonlegal


class V166E4TypedNonStatutoryClaimSources(unittest.TestCase):
    def check(self,c,typed,manifest):
        audit_e4_source_type_inventory(
            c["source"],c["exchange"],c["chat_review"],typed)
        return audit_typed_nonstatutory_research(
            c,typed,manifest,as_of="2026-11-17")

    def test_01_real_component_publisher_bibliography_narrow_title_positive(self):
        c,t,m=case_with_type("단도 인베스터 원서 제목이 무엇인가요",
            "FACT","AFFIRMED","PUBLISHER_BOOK_BIBLIOGRAPHY",BOOK)
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_publisher_bytes",
                   return_value=BOOK):
            r=self.check(c,t,m)
        self.assertEqual(r["original_publisher_book_titles"],1)
        self.assertEqual(r["source_only_speaker_statements"],0)
        self.assertFalse(r["financial_truth_certified"])

    def test_02_same_wiley_domain_cannot_support_unrelated_book(self):
        c,t,m=case_with_type("단도 인베스터 원서 제목이 무엇인가요",
            "FACT","AFFIRMED","PUBLISHER_BOOK_BIBLIOGRAPHY",BOOK)
        unrelated=BOOK.replace(b"The Dhandho Investor",b"Other Book")
        m["rows"][0]["primary_body_sha256"]=sha256(unrelated)
        c["official_evidence_bodies"]["C00001"]=unrelated
        c["chat_review"]["atom_verdicts"][0]["official_body_sha256"]=sha256(unrelated)
        t["chat_review_sha256"]=json_digest(c["chat_review"])
        m["chat_review_sha256"]=json_digest(c["chat_review"])
        m["type_inventory_sha256"]=json_digest(t)
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_publisher_bytes",
                   return_value=unrelated):
            with self.assertRaises(QualityNotProven):
                self.check(c,t,m)

    def test_03_publisher_title_does_not_prove_author_pronunciation(self):
        c,t,m=case_with_type("작가는 모니시 바브라라고 들었습니다",
            "FACT","AFFIRMED","PUBLISHER_BOOK_BIBLIOGRAPHY",BOOK)
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_publisher_bytes",
                   return_value=BOOK):
            with self.assertRaisesRegex(InvalidInput,"PUBLISHER_TITLE_AND_VIDEO_QUOTE"):
                self.check(c,t,m)

    def test_04_non_numeric_speaker_opinion_is_source_only(self):
        c,t,m=case_with_type("개인적으로는 꾸준한 투자 습관이 더 중요하다고 생각합니다",
            "OPINION","AFFIRMED","PERSONAL_SUBJECTIVE_OPINION")
        r=self.check(c,t,m)
        self.assertEqual(r["source_only_speaker_statements"],1)
        self.assertFalse(r["financial_truth_certified"])

    def test_05_tax_statute_cannot_be_rebranded_source_only_opinion(self):
        c,t,m=case_with_type("세율과 세금 공제는 자동으로 확정된다고 생각합니다",
            "OPINION","AFFIRMED","INVESTMENT_STRATEGY_OPINION")
        with self.assertRaisesRegex(InvalidInput,"OBJECTIVE_FINANCIAL_RULE"):
            self.check(c,t,m)

    def test_06_hypothetical_question_remains_not_an_approved_answer(self):
        c,t,m=case_with_type("일정한 금액을 나누어서 투자하는 것이 좋을까요?",
            "QUESTION","QUESTION","HYPOTHETICAL_OR_QUESTION")
        self.assertEqual(self.check(c,t,m)["source_only_speaker_statements"],1)

    def test_07_unreviewed_investment_theory_holds_all_nonlegal_claims(self):
        c,t,m=case_with_type("이 책의 전략은 모든 시장에서 안전하다고 합니다",
            "OPINION","AFFIRMED","BOOK_ORIGINAL_AUTHOR_PRINCIPLE")
        with self.assertRaises((InvalidInput,QualityNotProven)):
            self.check(c,t,m)

    def test_08_1957_partnership_claim_cannot_borrow_company_letters(self):
        c,t,m=case_with_type("1957년 파트너십은 공격적인 전략이었습니다",
            "FACT","AFFIRMED","HISTORICAL_PARTNERSHIP_CLAIM")
        with self.assertRaisesRegex(QualityNotProven,"UNSUPPORTED_PRIMARY_KIND"):
            self.check(c,t,m)

    def test_09_bh_original_archive_year_supported_but_no_strategy_truth(self):
        c,t,m=case_with_type("버크셔 주주서한은 1977년에 있었습니다",
            "FACT","AFFIRMED","HISTORICAL_CORPORATE_FACT",BERKSHIRE_FAKE)
        with patch("v166_e4_typed_nonstatutory.fetch_official_berkshire_letters_index",
                   return_value=BERKSHIRE_FAKE):
            r=self.check(c,t,m)
        self.assertEqual(r["original_company_chronology_claims"],1)
        self.assertFalse(r["financial_truth_certified"])

    def test_10_bad_source_quote_digest_refused(self):
        c,t,m=case_with_type("개인적으로 장기 투자가 편합니다",
            "OPINION","AFFIRMED","PERSONAL_SUBJECTIVE_OPINION")
        m["rows"][0]["source_quote_sha256"]="1"*64
        with self.assertRaisesRegex(InvalidInput,"CLAIM_SPECIFIC_SOURCE_TYPE"):
            self.check(c,t,m)

    def test_11_missing_nonlegal_row_refuses_faux_legal_exemption(self):
        c,t,m=case_with_type("개인적으로 분할 투자가 편합니다",
            "OPINION","AFFIRMED","PERSONAL_SUBJECTIVE_OPINION")
        m["rows"]=[]
        with self.assertRaisesRegex(InvalidInput,"ALL_ACCEPTED_NONLEGAL"):
            self.check(c,t,m)

    def test_12_open_nonlegal_claim_may_not_be_exported_as_accept(self):
        c,t,m=case_with_type("단도 인베스터의 저자 발음을 정확히 모릅니다",
            "FACT","AFFIRMED","PUBLISHER_BOOK_BIBLIOGRAPHY",BOOK,
            status="OPEN")
        self.assertEqual(self.check(c,t,m)["nonstatutory_accepted_claims"],0)
        m["rows"]=[{
            "claim_id":"C00001",
            "evidence_class":"PUBLISHER_BOOK_BIBLIOGRAPHY",
            "authority_route":"ORIGINAL_PUBLISHER_PRIMARY",
            "source_quote_sha256":"0"*64,
            "chat_meaning_note":NOTE,
            "chat_meaning_note_sha256":sha256(NOTE.encode("utf-8")),
            "primary_url":WILEY_ORIGINAL,
            "primary_body_sha256":sha256(BOOK),
            "verification_mode":"PUBLISHER_ORIGINAL_ENGLISH_TITLE",
            "original_speaker_audio_verified":False,
            "formal_financial_fact_certified":False,
            "personal_advice_approved":False,
        }]
        with self.assertRaisesRegex(InvalidInput,"ALL_ACCEPTED_NONLEGAL"):
            self.check(c,t,m)

    def test_13_nonlegal_row_type_replay_across_atoms_refused(self):
        c,t,m=case_with_type("개인적으로 분할 투자가 편합니다",
            "OPINION","AFFIRMED","PERSONAL_SUBJECTIVE_OPINION")
        m["rows"][0]["claim_id"]="C99999"
        with self.assertRaisesRegex(InvalidInput,"NONLEGAL_ACCEPTANCE_CENSUS"):
            self.check(c,t,m)


    def test_14_wiley_original_pdf_word_used_by_author_not_dictionary(self):
        pdf=synthetic_wiley_chapter()
        self.assertGreaterEqual(len(pdf),10000)
        c,t,m=case_with_type("단도는 구자라트 지방의 표현이라고 들었습니다",
            "FACT","AFFIRMED","LINGUISTIC_ETYMLOGY",pdf)
        m["rows"][0].update(
            primary_url=CHAPTER_URL,
            primary_body_sha256=sha256(pdf),
            verification_mode="WILEY_BOOK_AUTHOR_GUJARATI_DESCRIPTION_NOT_DICTIONARY")
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_original_chapter_pdf",
                   return_value=pdf),patch(
                   "v166_e4_typed_nonstatutory.WILEY_APPROVED_CHAPTER_SHA256",
                   sha256(pdf)):
            result=self.check(c,t,m)
        self.assertEqual(result["original_author_chapter_word_descriptions"],1)
        self.assertFalse(result["financial_truth_certified"])
        book=audit_author_original_chapter(pdf,owner_source_sha256=c["source"].source_sha256)
        self.assertFalse(book["independent_linguistic_etymology_certified"])

    def test_15_original_author_risk_principle_is_not_loss_guarantee(self):
        pdf=synthetic_wiley_chapter()
        c,t,m=case_with_type("손실은 작게 보고 수익은 크게 본다는 저자의 말",
            "OPINION","QUOTED","BOOK_ORIGINAL_AUTHOR_PRINCIPLE",BOOK)
        note=NOTE+(" 저자가 책에서 말하는 저위험·고수익의 개념은 "
                   "원금 보장 계약이 아니며, 실제 투자에서는 손실 위험이 "
                   "항상 남아 있음을 공식 원문 1장에서 검문했습니다.")
        m["rows"][0].update(
            primary_url=WILEY_ORIGINAL,
            primary_body_sha256=sha256(BOOK),
            verification_mode="WILEY_BOOK_AUTHOR_ASYMMETRIC_RISK_NOT_GUARANTEED",
            chat_meaning_note=note,
            chat_meaning_note_sha256=sha256(note.encode("utf-8")))
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_publisher_bytes",
                   return_value=BOOK),patch(
                   "v166_e4_typed_nonstatutory.fetch_wiley_original_chapter_pdf",
                   return_value=pdf),patch(
                   "v166_e4_typed_nonstatutory.WILEY_APPROVED_CHAPTER_SHA256",
                   sha256(pdf)):
            r=self.check(c,t,m)
        self.assertEqual(r["original_author_asymmetric_risk_descriptions"],1)
        self.assertFalse(r["financial_truth_certified"])

    def test_16_chapter_missing_nonzero_risk_warning_cannot_be_accepted(self):
        bad=synthetic_wiley_chapter(include_caveat=False)
        with self.assertRaises(QualityNotProven):
            audit_author_original_chapter(bad,owner_source_sha256="b"*64)

    def test_17_gujarati_book_pdf_sha_mismatch_does_not_use_fake_primary(self):
        pdf=synthetic_wiley_chapter()
        c,t,m=case_with_type("단도는 구자라트 지방의 표현이라고 들었습니다",
            "FACT","AFFIRMED","LINGUISTIC_ETYMLOGY",pdf)
        m["rows"][0].update(
            primary_url=CHAPTER_URL,
            primary_body_sha256="0"*64,
            verification_mode="WILEY_BOOK_AUTHOR_GUJARATI_DESCRIPTION_NOT_DICTIONARY")
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_original_chapter_pdf",
                   return_value=pdf),patch(
                   "v166_e4_typed_nonstatutory.WILEY_APPROVED_CHAPTER_SHA256",
                   sha256(pdf)):
            with self.assertRaises(InvalidInput):
                self.check(c,t,m)

    def test_20_owner_title_reason_guess_is_attributed_not_publisher_verified(self):
        c,t,m=case_with_type(
            "단도라는 말이 낯설어 아마 번역 제목이 바뀐게 아닐까 생각합니다",
            "OPINION","UNRESOLVED","PERSONAL_SUBJECTIVE_OPINION",
            claim_id="C00284")
        note=(NOTE+" 해당 제목이 바뀐 이유에 관한 발언은 화자의 추측이며 "
              "출판사의 실제 번역제목 변경 사유는 확인되지 않았습니다. "
              "원문 직접 인용 외 사실 및 매매판단 근거로 사용하지 않습니다.")
        m["rows"][0].update(
            verification_mode="SPECULATIVE_TITLE_REASON_SOURCE_ONLY_NOT_PUBLISHER_FACT",
            chat_meaning_note=note,
            chat_meaning_note_sha256=sha256(note.encode("utf-8")))
        r=self.check(c,t,m)
        self.assertEqual(r["source_only_speaker_statements"],1)
        self.assertFalse(r["financial_truth_certified"])
        self.assertFalse(r["personal_advice_approved"])

    def test_21_broad_unresolved_opinion_no_explicit_guess_stays_blocked(self):
        c,t,m=case_with_type(
            "번역서 제목을 출판사가 실제 결정했다고 단정합니다",
            "OPINION","UNRESOLVED","PERSONAL_SUBJECTIVE_OPINION",
            claim_id="C00284")
        note=(NOTE+" 출판사 사유는 확인되지 않은 화자의 추측이라는 "
              "한계와 검토자 주의사항입니다.")
        m["rows"][0].update(
            verification_mode="SPECULATIVE_TITLE_REASON_SOURCE_ONLY_NOT_PUBLISHER_FACT",
            chat_meaning_note=note,
            chat_meaning_note_sha256=sha256(note.encode("utf-8")))
        with self.assertRaisesRegex(InvalidInput,"C00284_EXPLICIT_SPECULATION"):
            self.check(c,t,m)

    def test_22_other_unresolved_financial_opinion_cannot_borrow_title_exemption(self):
        c,t,m=case_with_type(
            "아마 이 주식의 수익률은 언제나 보장될 거라 생각합니다",
            "OPINION","UNRESOLVED","INVESTMENT_STRATEGY_OPINION",
            claim_id="C12345")
        m["rows"][0]["verification_mode"]=(
            "SPECULATIVE_TITLE_REASON_SOURCE_ONLY_NOT_PUBLISHER_FACT")
        with self.assertRaisesRegex(InvalidInput,"OPINION_OR_QUESTION_MUST_NOT_BORROW"):
            self.check(c,t,m)

    def test_23_title_guess_native_open_cannot_be_accepted_by_type_only(self):
        c,t,m=case_with_type(
            "아마 번역 제목이 바뀐 게 아닐까 생각합니다",
            "OPINION","UNRESOLVED","PERSONAL_SUBJECTIVE_OPINION",
            status="OPEN",claim_id="C00284")
        self.assertEqual(self.check(c,t,m)["nonstatutory_accepted_claims"],0)
        self.assertFalse(self.check(c,t,m)["financial_truth_certified"])

    def test_19_same_wiley_domain_chapter_changed_without_signed_revision_holds(self):
        pdf=synthetic_wiley_chapter()
        c,t,m=case_with_type("단도는 구자라트 지방의 표현이라고 들었습니다",
            "FACT","AFFIRMED","LINGUISTIC_ETYMLOGY",pdf)
        m["rows"][0].update(
            primary_url=CHAPTER_URL,
            primary_body_sha256=sha256(pdf),
            verification_mode="WILEY_BOOK_AUTHOR_GUJARATI_DESCRIPTION_NOT_DICTIONARY")
        # The mocked origin serves valid publisher-text bytes, but it is not
        # the PREVIOUSLY witnessed approved first-party chapter SHA.
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_original_chapter_pdf",
                   return_value=pdf):
            with self.assertRaisesRegex(InvalidInput,"SNAPSHOT_DIGEST_DRIFT"):
                self.check(c,t,m)

    def test_18_gujarati_claim_cannot_borrow_unrelated_bibliography(self):
        pdf=synthetic_wiley_chapter()
        c,t,m=case_with_type("기본적인 사업이라는 표현을 좋아합니다",
            "FACT","AFFIRMED","LINGUISTIC_ETYMLOGY",pdf)
        m["rows"][0].update(
            primary_url=CHAPTER_URL,
            primary_body_sha256=sha256(pdf),
            verification_mode="WILEY_BOOK_AUTHOR_GUJARATI_DESCRIPTION_NOT_DICTIONARY")
        with patch("v166_e4_typed_nonstatutory.fetch_wiley_original_chapter_pdf",
                   return_value=pdf):
            with self.assertRaisesRegex(InvalidInput,"GUJARATI_AUTHOR_WORD_ASSERTION"):
                self.check(c,t,m)

if __name__=="__main__":
    unittest.main()
