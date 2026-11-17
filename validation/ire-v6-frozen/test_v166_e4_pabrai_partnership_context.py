"""Synthetic speaker vs actual Pabrai Fund issuer-rule type tests.

The first-party Pabrai site can attest only the fund's own operating
structure, not investment success caused by copying Buffett or exact source
audio. This unit's HTML and video are CREATED fixtures (not user SRT).
"""
from __future__ import annotations

import copy
import unittest
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from v166_e4_pabrai_partnership_context import (
    PABRAI_ABOUT_URL,_validate_url,
    audit_pabrai_fund_first_party_words,
    audit_first_party_buffett_partnership_structure)

BODY=(
    "<html><title>Pabrai Investment Funds (PIF)</title>"
    "<p>The Pabrai Investment Funds (PIF) were inspired by the original "
    "1950s Buffett Partnerships and are a close replica of the original "
    "Buffett Partnership Rules.</p>"
    "<p>This fake text is a policy unit fixture only. The financial "
    "performance and any account balances are not audited here.</p>"
    "</html>"
).encode("utf-8")*3


def owner_fixture():
    texts=[
        "버핏 파트너십의 구성을 소개하며",
        "비즈니스 모델을 참고했다고 주장합니다",
        "그 구조를 벤치마킹했다고 전해집니다",
        "그것이 성공에 기여했다고도 들었습니다",
    ]
    raw=make_srt(texts)
    m=make_manifest(raw)
    src=verify_source(raw,m,
        expected_source_sha256=sha256(raw),
        expected_manifest_sha256=json_digest(m))
    refs=[{"cue_index":i,"quote":t} for i,t in enumerate(texts,1)]
    atom={"claim_id":"C00011","kind":"FACT","stance":"UNRESOLVED",
          "source_refs":refs,"proposition":"모방이 성공에 기여했다는 발언",
          "owner_window_id":"W00001","numeric_references":[],
          "condition_cue_indices":[],"exception_cue_indices":[],
          "context_cue_indices":[1,2,3,4]}
    review={"claim_id":"C00011","atom_sha256":json_digest(atom),
            "status":"ACCEPT_FOR_RESEARCH"}
    return src,atom,review


class V166E4PabraiOriginalFundCustodyTests(unittest.TestCase):
    def test_01_original_pabrai_issuer_rules_yes_causal_success_not_proven(self):
        src,atom,review=owner_fixture()
        d=audit_first_party_buffett_partnership_structure(
            src,atom,review,BODY,original_cue_indices=[1,2,3,4])
        self.assertTrue(d["fund_rules_modeled_on_1950s_buffett_partnerships"])
        self.assertFalse(d["investment_success_causality_independently_verified"])
        self.assertFalse(d["investment_stock_selection_same_as_buffett_verified"])
        self.assertFalse(d["whole_video_chat_final_pass"])
        self.assertFalse(d["research_knowledge_release_authorized"])
        self.assertEqual(d["frozen_v123_status_before"],
                         d["frozen_v123_status_after"])

    def test_09_same_issuer_scope_different_raw_html_has_distinct_sha(self):
        first=audit_pabrai_fund_first_party_words(BODY)
        # Cosmetic website counters/cookies change HTTP bytes. The
        # first-party STRUCTURE words remain, but raw original does not.
        updated=BODY+b"<span>Dynamic server marker 2026-11-18</span>"
        newer=audit_pabrai_fund_first_party_words(updated)
        self.assertNotEqual(first["raw_body_sha256"],newer["raw_body_sha256"])
        self.assertEqual(first["normalised_issuer_claim_sha256"],
                         newer["normalised_issuer_claim_sha256"])
        self.assertTrue(first["normalised_issuer_claim_not_raw_body_substitute"])
        self.assertFalse(newer["causal_success_proven"])

    def test_10_changed_fund_issuer_claim_is_not_same_source_meaning(self):
        changed=BODY.replace(b"close replica",b"completely unrelated")
        with self.assertRaises(QualityNotProven):
            audit_pabrai_fund_first_party_words(changed)

    def test_02_original_fund_rules_missing_fails_closed(self):
        with self.assertRaises(QualityNotProven):
            audit_pabrai_fund_first_party_words(
                BODY.replace(b"close replica",b"not at all similar"))

    def test_03_unrelated_issuer_site_cannot_attest_structure(self):
        with self.assertRaises(QualityNotProven):
            audit_pabrai_fund_first_party_words(
                b"<html>another hedge fund makes an independent strategy</html>"*15)

    def test_04_atom_quote_mutation_cannot_borrow_fund_issuer(self):
        src,atom,review=owner_fixture()
        atom["source_refs"][1]["quote"]="비즈니스 모델에 대한 확인 불가 발언"
        review["atom_sha256"]=json_digest(atom)
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_VIDEO_QUOTES_NOT_BYTE_PINNED"):
            audit_first_party_buffett_partnership_structure(src,atom,review,BODY)

    def test_05_original_chat_open_not_pushed_to_accept(self):
        src,atom,review=owner_fixture()
        review["status"]="OPEN"
        with self.assertRaisesRegex(InvalidInput,"FROZEN_V123_VERDICT_CHANGED"):
            audit_first_party_buffett_partnership_structure(src,atom,review,BODY)

    def test_06_existing_chat_atom_digest_drift_rejected(self):
        src,atom,review=owner_fixture()
        atom["proposition"]="전혀 다른 주장"
        with self.assertRaisesRegex(InvalidInput,"FROZEN_V123_VERDICT_CHANGED"):
            audit_first_party_buffett_partnership_structure(src,atom,review,BODY)

    def test_07_permitted_https_is_exact_not_lookalike(self):
        self.assertEqual(_validate_url(PABRAI_ABOUT_URL),"pabraifunds.com")
        for url in (
            "http://pabraifunds.com/about/",
            "https://pabraifunds.com.evil.test/about/",
            "https://pabraifunds.com/about/?redirect=https://evil.test",
            "https://pabraifunds.com:444/about/",
            "https://user@pabraifunds.com/about/",
        ):
            with self.subTest(url=url),self.assertRaises(InvalidInput):
                _validate_url(url)

    def test_08_one_missing_video_cue_prevents_issuer_wholesale_promotion(self):
        src,atom,review=owner_fixture()
        atom["source_refs"].pop()
        review["atom_sha256"]=json_digest(atom)
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_VIDEO_CUE_CENSUS_CHANGED"):
            audit_first_party_buffett_partnership_structure(
                src,atom,review,BODY,original_cue_indices=[1,2,3,4])


if __name__=="__main__":
    unittest.main()
