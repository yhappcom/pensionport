"""V126.2 actual V123 gate+V6 synthetic private knowledge -> ChatGPT answer guard.

The literal law.go.kr test HTML is a SYNTHETIC NEGATIVE-CONTROL FIXTURE,
not a real issuer response or approved legal fact.
"""
import copy
import sqlite3
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import QualityNotProven
import test_v126_chat_approved_knowledge_store as fixture
from v126_chat_research_answer_bridge import (
    prepare_question_packet,check_chat_research_answer,
)

class V126ChatEvidenceToAnswerBridgeTests(unittest.TestCase):
    def setUp(self):
        f=fixture.V126RealGatePrivateCumulativeKnowledgeTests(
            "test_real_chat_gate_synthetic_source_then_immutable_cumulative_store")
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f=f
        self.batch=f.push()
        with sqlite3.connect(f.db.path) as c:
            ids=sorted(k for (k,) in c.execute("SELECT knowledge_id FROM knowledge"))
        self.ids=ids
        self.packet=prepare_question_packet(f.db,"연금과 10% 세율은 어떻게 적용되나요?",
                                            selected_knowledge_ids=ids,as_of="2026-11-15")
        self.answer="이 영상의 주장에는 조건이 있으며, 최신 규정과 각 계좌의 적용 범위를 별도로 대조해야 합니다. 개인별 세금은 확정하지 않습니다."
        self.review={"schema":"IRE_V126_CHAT_RESEARCH_ANSWER_REVIEW_V1",
                     "review_executor":"CHATGPT_IN_CHAT",
                     "question_sha256":sha256(self.packet["question"].encode()),
                     "evidence_sha256":self.packet["evidence_sha256"],
                     "answer_sha256":sha256(self.answer.encode()),
                     "as_of":"2026-11-15","selected_knowledge_ids":ids,
                     "source_first_checked":True,"counterexamples_checked":True,
                     "no_personal_order_execution":True,
                     "no_formal_financial_fact_approval":True,
                     "chat_private_review_sha256":"a"*64}
        raw="<html><article>연금계좌 인출순서 과세제외금액을 구분하여 적용한다.</article></html>".encode()
        self.official={kid:{"url":"https://www.law.go.kr/LSW/synthetic-test.html",
                            "body":raw,"body_sha256":sha256(raw),
                            "effective_from":"2026-10-01","captured_on":"2026-11-08",
                            "literal_source_quote":"연금계좌 인출순서 과세제외금액",
                            "claim_scope_chat_reviewed":True} for kid in ids}

    def verify(self,**changes):
        args=dict(answer_text=self.answer,chat_answer_review=self.review,
                  primary_bodies=self.official)
        args.update(changes)
        return check_chat_research_answer(self.f.db,self.packet,**args)

    def test_real_v6_chat_gated_knowledge_then_private_chat_general_answer_receipt(self):
        result=self.verify()
        self.assertEqual(result["status"],"CHAT_RESEARCH_ANSWER_REVIEWED_NOT_PERSONAL_ADVICE")
        self.assertEqual(len(result["official_primary_sources_rehashed"]),3)
        self.assertEqual(result["answer_text"],self.answer)
        self.assertFalse(result["issuer_http_origination_independently_verified"])
        self.assertFalse(result["personal_account_or_trading_advice_approved"])
        self.assertFalse(result["p0_go"])

    def test_financial_original_body_absent_blocks_answer(self):
        with self.assertRaisesRegex(QualityNotProven,"FINANCE_CLAIM_BODY_CENSUS"):
            self.verify(primary_bodies={})

    def test_wrong_government_original_hash_or_quote_blocked(self):
        for name in ("body_sha256","literal_source_quote"):
            bad=copy.deepcopy(self.official)
            bad[self.ids[0]][name]="0"*64 if name=="body_sha256" else "완전히 다른 조문입니다"
            with self.subTest(name=name),self.assertRaises(QualityNotProven):
                self.verify(primary_bodies=bad)

    def test_unofficial_domain_and_future_law_denied(self):
        for field,val in (("url","https://example.com/fake-law"),
                          ("effective_from","2027-01-01"),
                          ("captured_on","2026-11-16")):
            bad=copy.deepcopy(self.official)
            bad[self.ids[0]][field]=val
            with self.subTest(field=field),self.assertRaises(QualityNotProven):
                self.verify(primary_bodies=bad)

    def test_chat_final_review_missing_or_answer_drift_blocked(self):
        with self.assertRaisesRegex(QualityNotProven,"CHAT_FINAL_ANSWER_REVIEW"):
            self.verify(chat_answer_review=None)
        with self.assertRaisesRegex(QualityNotProven,"CHAT_FINAL_ANSWER_REVIEW"):
            self.verify(answer_text=self.answer+" 추가 문구")

    def test_executable_trade_order_is_not_research_answer(self):
        with self.assertRaisesRegex(QualityNotProven,"ANSWER_NOT_SAFE"):
            self.verify(answer_text="지금 매수해주세요. "+self.answer)

    def test_knowledge_retraction_stales_prior_answer_packet(self):
        self.f.db.revoke(self.ids[0],chat_review_sha256="b"*64,
                         expected_knowledge_head=self.batch["knowledge_head_sha256"])
        with self.assertRaisesRegex(QualityNotProven,"HEAD_STALE"):
            self.verify()

    def test_no_approved_research_claims_denies_question(self):
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            empty=PrivateKnowledgeStore(Path(d)/"empty.db")
            with self.assertRaisesRegex(QualityNotProven,"NO_APPROVED_RESEARCH"):
                prepare_question_packet(empty,"금융 질문",selected_knowledge_ids=[],as_of="2026-11-15")

if __name__=="__main__":
    unittest.main()