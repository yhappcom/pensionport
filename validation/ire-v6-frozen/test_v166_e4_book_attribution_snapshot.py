"""Synthetic scope/route tests only; real owner replay stays private."""
import copy
import unittest
from unittest.mock import patch
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from test_v166_e4_typed_nonstatutory import case_with_type
from v166_e4_attributed_book_snapshot import (
    MODE, HTML_URL, load_registry, body_scope, audit_book_attribution_snapshot,
    verify_live_book_attribution)
from v166_e4_typed_nonstatutory import audit_typed_nonstatutory_research
from v166_e4_typed_authority import audit_e4_source_type_inventory

BODY=(b"<html>The Dhandho Investor Mohnish Pabrai 9780470043899 "
      b"Invest in existing businesses. This is an attributed book topic, "
      b"not independently demonstrated investment performance or advice.</html>")

class BookSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.c,self.t,self.m=case_with_type(
            "기존 사업에 투자하라는 저자의 원칙입니다.",
            "OPINION","QUOTED","BOOK_ORIGINAL_AUTHOR_PRINCIPLE",BODY)
        self.s=self.c["source"]
        self.a=self.c["exchange"]["atoms"][0]
        self.v=self.c["chat_review"]["atom_verdicts"][0]
        self.r=self.m["rows"][0]
        self.cid=self.a["claim_id"]
        self.note={
            "schema":"V166_E4_P0_CHATGPT_ACTUAL_REVIEW_REVISION_V1",
            "claim_id":self.cid,"atom_sha256":json_digest(self.a),
            "source_sha256":self.s.source_sha256,
            "decision":"ACCEPT_FOR_RESEARCH",
            "scope":"ATTRIBUTED_ORIGINAL_BOOK_TEXT_ONLY_NOT_EMPIRICAL_TRUE_OR_ADVICE",
            "formal_investment_truth_certified":False,"personal_advice_approved":False,
            "actual_speaker_audio_verified":False,
            "original_cue_indices":self.a["context_cue_indices"],
            "source_context_sha256":json_digest([
                {"cue_index":i,"original_cue_text_sha256":sha256(self.s.cues[i-1].text.encode())}
                for i in self.a["context_cue_indices"]]),
            "source_refs_sha256":json_digest(self.a["source_refs"]),
            "financial_claim":True,"primary_kind":"html","primary_scope_key":"EXISTING",
            "primary_body_sha256":sha256(BODY),"primary_url":HTML_URL,
            "chat_meaning_note":"원문 출판사의 저서 목차에 나타난 저자의 투자 원칙으로만 제한하며 실제 성과, 미래 수익, 안전성, 개인별 적합성과 법적 적용은 검증하지 않습니다."
        }
        self.nt=canonical(self.note).decode()
        nh=sha256(self.nt.encode())
        self.v.update(private_review_note_sha256=nh,
                      finance_evidence_status="PRIMARY_BODY_AND_DATE_CHAT_CHECKED")
        self.t["rows"][0]["unchanged_v123_review_note_sha256"]=nh
        self.t["chat_review_sha256"]=json_digest(self.c["chat_review"])
        self.m["chat_review_sha256"]=json_digest(self.c["chat_review"])
        self.m["type_inventory_sha256"]=json_digest(self.t)
        self.r.update(chat_meaning_note=self.nt,chat_meaning_note_sha256=nh,
                      verification_mode=MODE,primary_url=HTML_URL,
                      primary_body_sha256=sha256(BODY))
        self.reg={"source_sha256":self.s.source_sha256,
                  "rows":{self.cid:[json_digest(self.a),nh,"EXISTING"]}}

    def proof(self):
        with patch("v166_e4_attributed_book_snapshot.load_registry",return_value=self.reg), \
             patch("v166_e4_attributed_book_snapshot.HTML_SHA",sha256(BODY)):
            return audit_book_attribution_snapshot(
                self.s,self.a,self.v,self.nt,BODY,self.r)

    def test_actual_registry_is_fixed_and_contains_23(self):
        self.assertEqual(len(load_registry()["rows"]),23)

    def test_synthetic_registered_scope_and_live_drift(self):
        p=self.proof()
        got=verify_live_book_attribution(p,BODY+b" ")
        self.assertNotEqual(got["live_primary_sha256"],got["archived_primary_sha256"])
        self.assertFalse(got["historical_bytes_replaced"])
        self.assertFalse(got["research_release_authorized"])

    def test_unregistered_owner_source_refused(self):
        with self.assertRaisesRegex(InvalidInput,"UNREGISTERED_OR_CHANGED_REVIEW"):
            audit_book_attribution_snapshot(self.s,self.a,self.v,self.nt,BODY,self.r)

    def test_changed_note_refused(self):
        self.nt=canonical(dict(self.note,chat_meaning_note="변조된 심사")).decode()
        with self.assertRaisesRegex(InvalidInput,"UNREGISTERED_OR_CHANGED_REVIEW"):
            self.proof()

    def test_native_open_refused_even_with_pin(self):
        self.v["status"]="OPEN"
        with self.assertRaisesRegex(InvalidInput,"NATIVE_AUTHOR_QUOTE_REVIEW"):
            self.proof()

    def test_wrong_live_scope_refused(self):
        with self.assertRaises(QualityNotProven):
            verify_live_book_attribution(self.proof(),
                BODY.replace(b"Invest in existing businesses",b"Unrelated topic"))

    def test_mandatory_nonstatutory_route(self):
        audit_e4_source_type_inventory(self.s,self.c["exchange"],self.c["chat_review"],self.t)
        with patch("v166_e4_attributed_book_snapshot.load_registry",return_value=self.reg), \
             patch("v166_e4_attributed_book_snapshot.HTML_SHA",sha256(BODY)), \
             patch("v166_e4_typed_nonstatutory.fetch_wiley_publisher_bytes",return_value=BODY+b" "):
            r=audit_typed_nonstatutory_research(self.c,self.t,self.m,as_of="2026-11-17")
        self.assertEqual(r["registered_attributed_book_claims"],1)
        self.assertEqual(r["nonstatutory_primary_checked"],1)
        self.assertFalse(r["financial_truth_certified"])

if __name__=="__main__":
    unittest.main()
