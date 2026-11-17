"""V166 E4 approval gate: mock HTTPS is SYNTHETIC, never genuine law.

Runs real frozen V123 checks and real V128/V126 SQLite paths. A monkeypatched
official fetch in unit tests is used only to exercise policy; NO test may
label fake source bytes legally authentic or an actual investment opinion.
"""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from ire.v6.codec import ZERO_SHA, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from test_v123_chat_final_gate import ChatFinalGateTests
from test_v166_e3_chat_decision_delivery import V166E3NativeDecisionDelivery
from v166_e4_primary_approval_gate import (
    SCHEMA, assess_e4_primary_authority_gate,
    run_e4_guarded_parent, _canonical_official_url,
    _fetch_approved_primary_https,
)

BODY=("<html><title>SYNTHETIC ONLY - NOT LAW</title><p>시행 2026-11-10</p>"
      "<p>가상의 금융 교육 문서: 납입 한도와 공제율은 "
      "사람별·과세기간별로 검토해야 한다는 시험용 텍스트. "
      "연금저축의 예상 수익은 10%입니다. "
      "하지만 실제로는 8%일 수 있습니다. "
      "다만 세금 조건은 소득에 따라 달라집니다.</p></html>").encode("utf-8")
EXCERPT="납입 한도와 공제율은 사람별·과세기간별로 검토"
NOTE=("ChatGPT의 합성 시험 확인: 본문 문서가 해당 투자계좌의 일반 정책설명이라는 "
      "문맥을 검문했으나 실제 법령 효력이나 사람별 적합성 판단은 인증하지 않는다. "
      "원문 조건·예외·적용일의 차이가 존재하면 결론을 보류해야 한다.")


def make_manifest(case, body=BODY):
    review=case["chat_review"]
    atoms={a["claim_id"]:a for a in case["exchange"]["atoms"]}
    rows=[]
    for v in review["atom_verdicts"]:
        if v["status"]!="ACCEPT_FOR_RESEARCH":
            continue
        a=atoms[v["claim_id"]]
        if not (v["financial_claim"] or v["high_risk"] or a["kind"]=="FACT"):
            continue
        index=a["context_cue_indices"][0]
        full=case["source"].cues[index-1].text
        rows.append({
            "claim_id":v["claim_id"],
            "official_url":"https://www.nts.go.kr/nts/cm/cntnts/"
                           "cntntsView.do?synthetic_approval_fixture="+v["claim_id"],
            "issuer_code":"NTS",
            "body_sha256":sha256(body),
            "effective_from":v["official_effective_as_of"],
            "effective_until":None,
            "primary_effective_date_excerpt":"시행 2026-11-10",
            "original_claim_cue_index":index,
            "original_claim_quote":full[:min(50,len(full))],
            "primary_scope_excerpt":EXCERPT,
            "chat_primary_scope_note":NOTE,
            "primary_claim_support_mode":"EXACT_PRIMARY_QUOTE",
            "chat_primary_scope_note_sha256":sha256(NOTE.encode("utf-8")),
            "chat_scope_conditions_reviewed":True,
            "chat_exceptions_reviewed":True,
            "chat_source_asof_reviewed":True,
            "general_education_only":True,
            "personal_applicability_confirmed":False,
            "formal_financial_truth_certified":False,
        })
    return {
        "schema":SCHEMA,
        "owner_source_sha256":case["source"].source_sha256,
        "host_event_sha256":case["host_receipt"]["event_sha256"],
        "chat_review_sha256":json_digest(review),
        "review_as_of":review["as_of"],
        "rows":rows,
        "private_chat_primary_applicability_note_sha256":
            sha256(b"SYNTHETIC ChatGPT scoped note; not law"),
        "formal_financial_fact_approved":False,
        "personal_advice_approved":False,
        "independent_gold_certified":False,
    }


def replace_synthetic_official_body(case):
    case["chat_review"]["as_of"]="2026-11-17"
    case["official_evidence_bodies"]={
        a["claim_id"]:BODY for a in case["exchange"]["atoms"]}
    for row in case["chat_review"]["atom_verdicts"]:
        if row["finance_evidence_status"]=="PRIMARY_BODY_AND_DATE_CHAT_CHECKED":
            row["official_body_sha256"]=sha256(BODY)


class V166E4NativeGatePolicyUnitTests(unittest.TestCase):
    def setUp(self):
        fx=ChatFinalGateTests(
            "test_01_real_native_v6_batch_then_synthetic_chat_final_pass")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.case={
            "source":fx.source,
            "exchange":fx.exchange,
            "host_receipt":fx.host,
            "chat_review":fx.review,
            "source_store":fx.parent.fx.store,
            "official_evidence_bodies":fx.evidence_bodies,
        }
        replace_synthetic_official_body(self.case)
        self.manifest=make_manifest(self.case)
        self.now="2026-11-17"

    def check(self,manifest=None):
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            return assess_e4_primary_authority_gate(
                self.case,self.manifest if manifest is None else manifest,
                now_as_of=self.now)

    def test_01_native_v123_accepts_fake_government_bytes_without_provenance(self):
        # This is the vulnerability E4 closes: frozen V123 is not changed.
        from v123_chat_final_gate import assess_chat_final_gate
        native=assess_chat_final_gate(
            self.case["source"],self.case["exchange"],
            host_receipt=self.case["host_receipt"],
            chat_review=self.case["chat_review"],store=self.case["source_store"],
            official_evidence_bodies=self.case["official_evidence_bodies"])
        self.assertEqual(native["status"],"CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        blocked=assess_e4_primary_authority_gate(
            self.case,None,now_as_of=self.now)
        self.assertEqual(blocked["status"],"E4_HOLD_INELIGIBLE_APPROVAL")
        self.assertEqual(blocked["reason_code"],"PRIMARY_PROVENANCE_MISSING")
        self.assertFalse(blocked["research_export_authorized"])

    def test_02_complete_synthetic_policy_approval_passes_research_only(self):
        r=self.check()
        self.assertEqual(r["status"],"E4_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertEqual(r["approved_research_candidate_claims"],3)
        self.assertEqual(r["official_primary_claims_replayed"],3)
        self.assertTrue(r["research_export_authorized"])
        self.assertFalse(r["formal_financial_fact_approved"])
        self.assertFalse(r["personal_advice_approved"])

    def test_03_no_untrusted_domains_or_scheme_or_subdomain_phishing(self):
        for url in ("http://www.nts.go.kr/a",
                    "https://www.nts.go.kr.attacker.tld/a",
                    "https://evil.nts.go.kr/a",
                    "https://www.nts.go.kr:8443/a",
                    "https://127.0.0.1/a",
                    "https://www.nts.go.kr@evil.example/a"):
            with self.subTest(url=url),self.assertRaises(InvalidInput):
                _canonical_official_url(url)

    def test_04_official_issuer_claim_must_match_canonical_domain(self):
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["issuer_code"]="FSC"
        with self.assertRaises(InvalidInput):
            self.check(doc)

    def test_05_forged_or_omitted_primary_body_cannot_approve(self):
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["body_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            self.check(doc)
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=b"Forged primary content"*20):
            with self.assertRaises(InvalidInput):
                assess_e4_primary_authority_gate(
                    self.case,self.manifest,now_as_of=self.now)

    def test_06_future_effective_law_and_wrong_asof_blocked(self):
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["effective_until"]="2026-01-01"
        with self.assertRaises(InvalidInput):
            self.check(doc)
        doc=copy.deepcopy(self.manifest)
        doc["review_as_of"]="2026-11-18"
        with self.assertRaises(InvalidInput):
            self.check(doc)

    def test_07_missing_primary_scope_quote_is_not_legal_evidence(self):
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["primary_scope_excerpt"]="이 문장은 이 원본 문서에 없습니다"
        with self.assertRaises(InvalidInput):
            self.check(doc)

    def test_08_missing_chat_conditions_and_personal_flags_rejected(self):
        for field,value in (("chat_exceptions_reviewed",False),
                            ("chat_scope_conditions_reviewed",False),
                            ("personal_applicability_confirmed",True),
                            ("formal_financial_truth_certified",True),
                            ("general_education_only",False)):
            doc=copy.deepcopy(self.manifest)
            doc["rows"][0][field]=value
            with self.subTest(field=field),self.assertRaises(InvalidInput):
                self.check(doc)

    def test_09_missing_or_extra_primary_claims_rejected(self):
        for mod in ("missing","extra"):
            doc=copy.deepcopy(self.manifest)
            if mod=="missing":
                doc["rows"].pop()
            else:
                doc["rows"].append(copy.deepcopy(doc["rows"][0]))
            with self.subTest(mod=mod),self.assertRaises(InvalidInput):
                self.check(doc)

    def test_10_fake_source_claim_quote_or_review_sha_rejected(self):
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["original_claim_quote"]="원본에서 찾을 수 없는 발화"
        with self.assertRaises(InvalidInput):self.check(doc)
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["chat_primary_scope_note_sha256"]="1"*64
        with self.assertRaises(InvalidInput):self.check(doc)

    def test_11_native_open_or_rejected_never_promoted_by_valid_manifest(self):
        case=self.case
        row=case["chat_review"]["atom_verdicts"][0]
        row.update(status="OPEN",finance_evidence_status="OPEN",
                   official_body_sha256=None,official_effective_as_of=None,
                   financial_scope_checked=False)
        blocked=self.check()
        self.assertEqual(blocked["status"],"E4_HOLD_INELIGIBLE_APPROVAL")
        self.assertEqual(blocked["reason_code"],"NATIVE_CHAT_NOT_PASS")
        row["status"]="REJECT"
        blocked=self.check()
        self.assertEqual(blocked["status"],"E4_HOLD_INELIGIBLE_APPROVAL")
        self.assertEqual(blocked["native_chat_decision"],"REJECTED")

    def test_12_fetch_failure_fails_closed(self):
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   side_effect=TimeoutError("simulated official timeout")):
            with self.assertRaises(QualityNotProven):
                assess_e4_primary_authority_gate(
                    self.case,self.manifest,now_as_of=self.now)

    def test_17_even_matching_official_https_bytes_cannot_support_unrelated_claim(self):
        # Strong negative: no digest, issuer, as-of or origin mismatch.
        # The official fixture text truly exists but does NOT contain the
        # original speaker's exact assertion. No borrowed authority allowed.
        unrelated=("<html>가상의 정부 사이트 교육 안내: 납입 한도와 공제율은 "
                   "사람별·과세기간별로 검토해야 하는 시험용 안내입니다.</html>").encode("utf-8")
        doc=copy.deepcopy(self.manifest)
        for row in self.case["chat_review"]["atom_verdicts"]:
            row["official_body_sha256"]=sha256(unrelated)
        for cid in self.case["official_evidence_bodies"]:
            self.case["official_evidence_bodies"][cid]=unrelated
        doc["chat_review_sha256"]=json_digest(self.case["chat_review"])
        for row in doc["rows"]:
            row["body_sha256"]=sha256(unrelated)
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=unrelated):
            with self.assertRaisesRegex(
                    InvalidInput,"OFFICIAL_ORIGINAL_DOES_NOT_SUPPORT_CLAIM_QUOTE"):
                assess_e4_primary_authority_gate(
                    self.case,doc,now_as_of=self.now)

    def test_19_effective_date_must_be_in_issuer_original_bytes(self):
        fake=("<html><p>납입 한도와 공제율은 사람별·과세기간별로 검토</p>"
              "<p>연금저축의 예상 수익은 10%입니다.</p></html>").encode("utf-8")
        # Changes to host/review SHA cannot disguise missing dated law text.
        doc=copy.deepcopy(self.manifest)
        for row in self.case["chat_review"]["atom_verdicts"]:
            row["official_body_sha256"]=sha256(fake)
        for cid in self.case["official_evidence_bodies"]:
            self.case["official_evidence_bodies"][cid]=fake
        doc["chat_review_sha256"]=json_digest(self.case["chat_review"])
        for row in doc["rows"]:
            row["body_sha256"]=sha256(fake)
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=fake):
            with self.assertRaises(InvalidInput):
                assess_e4_primary_authority_gate(self.case,doc,now_as_of=self.now)

    def test_18_unreviewed_paraphrase_cannot_replace_exact_authority_support(self):
        doc=copy.deepcopy(self.manifest)
        doc["rows"][0]["primary_claim_support_mode"]="UNREVIEWED_PARAPHRASE"
        with self.assertRaises(InvalidInput):
            self.check(doc)

    def test_13_source_or_host_review_pin_drift_fails_closed(self):
        doc=copy.deepcopy(self.manifest)
        doc["host_event_sha256"]="a"*64
        with self.assertRaises(InvalidInput):self.check(doc)
        doc=copy.deepcopy(self.manifest)
        doc["chat_review_sha256"]="b"*64
        with self.assertRaises(InvalidInput):self.check(doc)


class V166E4E3V128RealSQLiteIntegration(unittest.TestCase):
    def setUp(self):
        self.e3=V166E3NativeDecisionDelivery(
            "test_01_all_chat_approved_children_preserve_research_only_pass")
        self.e3.setUp()
        self.addCleanup(self.e3.doCleanups)
        self.fx=self.e3.fx
        for packet in self.fx.packets:
            replace_synthetic_official_body(packet["case"])
        self.manifests={
            segment_id:make_manifest(packet["case"])
            for segment_id,packet in zip(self.fx.checkpoint.child_ids,self.fx.packets)
        }

    def run_guarded(self):
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            return run_e4_guarded_parent(
                self.fx.checkpoint,self.fx.knowledge,
                review_or_load_child=self.fx.child,
                review_seams=self.fx.seams,
                review_parent=self.fx.parent_review,
                primary_manifest_for_child=lambda sid,case:self.manifests.get(sid),
                expected_knowledge_head=ZERO_SHA,
                now_as_of="2026-11-17")

    def test_14_both_valid_synthetic_children_do_publish_research_only(self):
        r=self.run_guarded()
        self.assertEqual(r["status"],"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED")
        self.assertEqual([x["e4_status"] for x in r["child_preflights"]],
                         ["E4_PASS_RESEARCH_CANDIDATES_ONLY"]*2)
        self.assertTrue(r["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts(),
                         {"events":3,"knowledge":3,"parent_publications":1})
        self.assertFalse(r["personal_advice_approved"])

    def test_15_one_child_missing_primary_blocks_entire_private_knowledge(self):
        sid=self.fx.checkpoint.child_ids[1]
        del self.manifests[sid]
        r=self.run_guarded()
        self.assertEqual(r["status"],"E4_HOLD_UNVERIFIED_CHILD")
        self.assertEqual(self.fx._counts().get("events",0),0)
        self.assertEqual(self.fx._counts().get("knowledge",0),0)
        self.assertEqual(self.fx._counts().get("parent_publications",0),0)

    def test_16_invalid_source_redirect_also_blocks_parent_approval(self):
        second=self.fx.checkpoint.child_ids[1]
        self.manifests[second]["rows"][0]["official_url"] = (
            "https://www.nts.go.kr.attacker.test/fake")
        with self.assertRaises(InvalidInput):
            self.run_guarded()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)


if __name__=="__main__":
    unittest.main()
