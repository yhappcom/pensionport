"""Regression tests for durable corrections to an unresolved source cue."""
from ire.v5.tests.test_engine import V5ContractTests, SRT, MAN
from ire.v5.engine import ResearchRun, RunError, sha256, canonical

class CorrectionTests(V5ContractTests):
    def unresolved(self):
        item=self.model(1)
        item["claims"][0]["source_refs"]=item["claims"][0]["source_refs"][1:]
        item["cue_dispositions"][0]={
            "cue_index":1,"status":"UNRESOLVED","claim_ids":[],
            "reason":"Insufficient context for this utterance."}
        return item

    def correction(self,old):
        return {"schema":"IRE_V5_MODEL_CORRECTION_V1",
                "window_id":"W00001","previous_model_sha256":sha256(canonical(old)),
                "reason":"The original text was reviewed in its full context.",
                "corrected_model":self.model(1)}

    def test_repair_and_reverify_same_immutable_ledger(self):
        old=self.unresolved()
        self.r.append("MODEL_ANALYSIS",old)
        for n in (2,3):self.r.append("MODEL_ANALYSIS",self.model(n))
        for n in (1,2,3):
            self.r.append("EVIDENCE_REVIEW",self.evidence(n))
            self.r.append("PRIOR_RELATION_REVIEW",self.relation(n))
        self.assertEqual(self.r.next_task()["phase"],"MODEL_CORRECTION_REQUIRED")
        with self.assertRaisesRegex(RunError,"HIGH_SIGNAL_SEMANTIC_UNRESOLVED"):
            self.r.close()
        self.r.append("MODEL_CORRECTION",self.correction(old))
        self.assertEqual(self.r.status()["evidence_cases_reviewed"],2)
        self.assertEqual(self.r.status()["relation_cases_reviewed"],2)
        self.assertEqual(self.r.next_task()["phase"],"OFFICIAL_EVIDENCE_REVIEW_REQUIRED")
        self.r.append("EVIDENCE_REVIEW",self.evidence(1))
        self.r.append("PRIOR_RELATION_REVIEW",self.relation(1))
        state=self.r.close()
        self.assertTrue(state["sealed"])
        self.assertEqual(ResearchRun(SRT,MAN,self.store).status()["model_corrections"],1)
        self.assertEqual(state["approved_financial_facts"],0)

    def test_stale_correction_does_not_mutate_chain(self):
        old=self.unresolved()
        self.r.append("MODEL_ANALYSIS",old)
        payload=self.correction(old)
        payload["previous_model_sha256"]="0"*64
        previous=self.r.seq
        with self.assertRaisesRegex(RunError,"MODEL_CORRECTION_STALE_PREVIOUS_MODEL"):
            self.r.append("MODEL_CORRECTION",payload)
        self.assertEqual(self.r.status()["receipt_count"],previous)
