"""SYNTHETIC review callback fixtures; the native frozen V123 gate is REAL.

This is a transport+decision-custody test, not independent financial accuracy,
not a real ChatGPT session callback, and never an E4 or V128 release.
"""
from __future__ import annotations
import copy
import unittest
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from test_v123_chat_final_gate import ChatFinalGateTests
from v167_chat_research_loop import prepare_open_docket, execute_chat_review_round
from v168_chat_native_replay import compile_and_replay_native
from v166_e4_primary_approval_gate import assess_e4_primary_authority_gate


NOTE = ("CHATGPT_IN_CHAT 합성 전용 2차 의미 검문입니다. 원본 화자·조건·예외·숫자와 반례는 "
        "개별 원자에 귀속하였고 발행인 원본 출처의 적법성 및 개인 투자자문은 인증하지 않습니다.")


def proposal_reviewer(req, decision="CANDIDATE_NEEDS_NATIVE_REVIEW"):
    return {"claim_id":req["task"]["claim_id"],
        "atom_sha256":req["task"]["atom_sha256"],
        "request_sha256":req["request_sha256"],
        "decision":decision,
        "reason":"합성 시험 전용 ChatGPT 판정입니다. 원본 문맥과 반례를 검토했지만 별도 2차 native 승인과 공식 발행기관 인증이 필요합니다.",
        "conditions_checked":True,"exceptions_checked":True,
        "numbers_and_period_checked":True,"counterarguments_checked":True,
        "chat_reviewer_identity_attested":False,
        "financial_fact_certified":False,"personal_advice_approved":False}


class V168NativeBridgeTests(unittest.TestCase):
    def setUp(self):
        fx = ChatFinalGateTests("test_01_real_native_v6_batch_then_synthetic_chat_final_pass")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.case={"source":fx.source,"exchange":fx.exchange,
            "host_receipt":fx.host,"chat_review":copy.deepcopy(fx.review),
            "source_store":fx.parent.fx.store,
            "official_evidence_bodies":dict(fx.evidence_bodies)}
        self.original_approved=copy.deepcopy(fx.review["atom_verdicts"][0])
        old=self.case["chat_review"]["atom_verdicts"][0]
        old.update(status="OPEN",finance_evidence_status="OPEN",
                   official_body_sha256=None,official_effective_as_of=None,
                   financial_scope_checked=False)
        raw = fx.parent.fx.raw
        cue_map={cue.index:cue.text for cue in fx.source.cues}
        self.segments=[{
            "segment_id":"B0001", "plan":fx.parent.fx.manifest,
            "exchange":fx.exchange,"review":self.case["chat_review"],
            "host":{"event_sha256":fx.host["event_sha256"],
                    "bundle_sha256":fx.host["bundle_sha256"],
                    "atomic_batch_committed":True}}]
        self.docket=prepare_open_docket(raw,cue_map,self.segments,
            expected_source_sha256=sha256(raw),as_of="2026-11-18")
        self.claim=self.docket["items"][0]["claim_id"]
        self.backup=copy.deepcopy(self.case["chat_review"])

    def evidence(self,task):
        body=self.case["official_evidence_bodies"][task["claim_id"]]
        return [{"url":"https://www.nts.go.kr/example/synthetic",
            "body":body,"excerpt":"synthetic-only government text",
            "source_label":"SYNTHETIC ONLY - NOT REAL AUTHORITY",
            "retrieved_as_of":"2026-11-18"}]

    def proposal(self,decision="CANDIDATE_NEEDS_NATIVE_REVIEW"):
        return execute_chat_review_round(self.docket,
           evidence_retriever=self.evidence,
           chat_reviewer=lambda req:proposal_reviewer(req,decision))

    def secondary(self,proposal, status="ACCEPT_FOR_RESEARCH"):
        row=copy.deepcopy(self.original_approved)
        row["status"]=status
        row["private_review_note_sha256"]=sha256(NOTE.encode("utf-8"))
        if status == "REJECT":
            row["finance_evidence_status"]="OPEN"
            row["official_body_sha256"]=None
            row["official_effective_as_of"]=None
            row["financial_scope_checked"]=False
        return {"claim_id":self.claim,
            "atom_sha256":self.docket["items"][0]["atom_sha256"],
            "proposal_decision_sha256":proposal["proposals"][0]["chat_decision_sha256"],
            "source_sha256":self.docket["owner_source_sha256"],
            "prior_review_sha256":self.docket["items"][0]["prior_review_sha256"],
            "chat_review_note":NOTE,
            "conditions_checked":True,"exceptions_checked":True,
            "numbers_checked":True,"counterarguments_checked":True,
            "speaker_stance_checked":True,"not_personal_advice":True,
            "not_legal_certification":True,"native_row":row}

    def compile(self,proposal, secondary=None):
        return compile_and_replay_native(self.docket,proposal,
            cases_by_segment={"B0001":self.case},
            secondary_chat_reviews=secondary)

    def test_01_no_changes_replayed_real_native_v123_hold(self):
        p=self.proposal("KEEP_OPEN")
        r=self.compile(p)
        self.assertEqual(r["receipt"]["native_results"][0]["native_status"],
                         "CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(r["receipt"]["native_rows_changed"],0)
        self.assertFalse(r["receipt"]["e4_approved"])
        self.assertFalse(r["receipt"]["e5_authorized"])
        self.assertEqual(self.case["chat_review"],self.backup)

    def test_02_candidate_requires_second_chat_review(self):
        p=self.proposal()
        with self.assertRaisesRegex(InvalidInput,"SECONDARY_CHAT_REQUIRED"):
            self.compile(p)

    def test_03_native_v123_candidate_pass_never_e4_release(self):
        p=self.proposal()
        r=self.compile(p,{self.claim:self.secondary(p)})
        self.assertEqual(r["receipt"]["native_rows_changed"],1)
        self.assertEqual(r["receipt"]["native_results"][0]["native_status"],
                         "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertTrue(r["receipt"]["all_native_scopes_pass"])
        self.assertFalse(r["receipt"]["knowledge_publication_authorized"])
        case={**self.case,"chat_review":r["native_private_drafts"]["B0001"]["review"]}
        e4=assess_e4_primary_authority_gate(case,None,now_as_of="2026-11-18")
        self.assertEqual(e4["status"],"E4_HOLD_INELIGIBLE_APPROVAL")
        self.assertEqual(e4["reason_code"],"PRIMARY_PROVENANCE_MISSING")
        self.assertEqual(self.case["chat_review"],self.backup)

    def test_04_financial_original_body_missing_blocks(self):
        p=self.proposal(); sec=self.secondary(p)
        self.case["official_evidence_bodies"].pop(self.claim)
        with self.assertRaisesRegex(InvalidInput,"FINANCIAL_CANDIDATE_NOT_ORIGINAL_BYTES"):
            self.compile(p,{self.claim:sec})

    def test_05_forged_secondary_atom_or_review_hash_blocks(self):
        p=self.proposal();sec=self.secondary(p)
        sec["prior_review_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,"SECONDARY_SOURCE_OR_REVIEW_PIN"):
            self.compile(p,{self.claim:sec})

    def test_06_no_financial_flag_downgrade(self):
        p=self.proposal();sec=self.secondary(p)
        sec["native_row"]["financial_claim"]=False
        with self.assertRaisesRegex(InvalidInput,"SECONDARY_NATIVE_ROW_UNTRUSTED"):
            self.compile(p,{self.claim:sec})

    def test_07_risk_counter_disagreement_cannot_be_cleared(self):
        p=self.proposal("KEEP_OPEN")
        self.case["chat_review"]["unresolved_high_risk_omissions"]=1
        with self.assertRaisesRegex(InvalidInput,"NATIVE_OPEN_ATOM_OR_CONTEXT_DRIFT"):
            self.compile(p)

    def test_08_proposal_receipt_tampering_fails_closed(self):
        p=self.proposal("KEEP_OPEN")
        p["proposals"][0]["proposed_decision"]="CANDIDATE_NEEDS_NATIVE_REVIEW"
        with self.assertRaisesRegex(InvalidInput,"PROPOSAL_RECEIPT_TAMPER"):
            self.compile(p)

    def test_09_source_context_changed_even_rehashed_docket_blocked(self):
        p=self.proposal("KEEP_OPEN")
        self.docket["items"][0]["source_context"][0]["text"]="forged"
        self.docket["docket_sha256"]=json_digest({k:v for k,v in self.docket.items()
                                                 if k != "docket_sha256"})
        with self.assertRaises(InvalidInput): self.compile(p)

    def test_10_reject_is_native_reject_not_hold(self):
        p=self.proposal("REJECT_PROPOSAL")
        r=self.compile(p,{self.claim:self.secondary(p,"REJECT")})
        self.assertEqual(r["receipt"]["native_results"][0]["native_status"],
                         "CHAT_FINAL_REJECTED")
        self.assertFalse(r["receipt"]["all_native_scopes_pass"])
        self.assertFalse(r["receipt"]["e4_approved"])

    def test_11_quarantine_requires_v166_typed_compiler(self):
        p=self.proposal("QUARANTINE_PROPOSAL")
        r=self.compile(p)
        self.assertEqual(r["receipt"]["native_rows_changed"],0)
        self.assertEqual(r["receipt"]["native_results"][0]["native_status"],
                         "CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(r["receipt"]["quarantine_type_review_pending"][0]["claim_id"],
                         self.claim)

    def test_12_missing_chat_evaluation_flags_block(self):
        p=self.proposal(); sec=self.secondary(p)
        sec["counterarguments_checked"]=False
        with self.assertRaisesRegex(InvalidInput,"SECONDARY_MEANING_REVIEW_REQUIRED"):
            self.compile(p,{self.claim:sec})

class V168SingleTurnHostProtocolTests(unittest.TestCase):
    setUp = V168NativeBridgeTests.setUp
    evidence = V168NativeBridgeTests.evidence
    secondary = V168NativeBridgeTests.secondary

    """Only test doubles feed the callbacks. No actual LLM/issuer connection."""
    def single(self, decision="KEEP_OPEN", secondary=None, **kwargs):
        from v168_chat_native_replay import run_v168_one_turn_review
        return run_v168_one_turn_review(
            self.fx.parent.fx.raw,
            {c.index:c.text for c in self.case["source"].cues},self.segments,
            expected_source_sha256=self.case["source"].source_sha256,
            as_of="2026-11-18",cases_by_segment={"B0001":self.case},
            evidence_retriever=self.evidence,
            chat_reviewer=lambda req:proposal_reviewer(req,decision),
            secondary_chat_reviewer=secondary,**kwargs)

    def test_13_complete_host_calls_native_hold_and_e4_hold(self):
        out=self.single()
        r=out["receipt"]
        self.assertEqual(r["proposals_checked"],1)
        self.assertEqual(r["secondary_chat_reviews_received"],0)
        self.assertEqual(r["scope_receipts"][0]["native_v123_status"],
                         "CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(r["scope_receipts"][0]["e4_preflight_status"],
                         "E4_HOLD_INELIGIBLE_APPROVAL")
        self.assertFalse(r["research_knowledge_published"])

    def test_14_missing_secondary_host_is_explicit_failure(self):
        with self.assertRaisesRegex(InvalidInput,"SECONDARY_CHAT_HOST_NOT_CONNECTED"):
            self.single("CANDIDATE_NEEDS_NATIVE_REVIEW")

    def test_15_callback_receipt_not_a_native_or_e4_release(self):
        def sec(req):
            p={"proposals":[req["proposal"]]}
            return self.secondary(p)
        r=self.single("CANDIDATE_NEEDS_NATIVE_REVIEW",secondary=sec)["receipt"]
        self.assertEqual(r["native_rows_changed"],1)
        self.assertTrue(r["native_all_scopes_pass"])
        self.assertFalse(r["e4_preflight_all_scopes_pass"])
        self.assertEqual(r["status"],"E4_HOLD_NO_PUBLICATION")
        self.assertFalse(r["e5_authorized"])


if __name__ == "__main__": unittest.main()