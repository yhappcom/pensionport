"""Run 12 pre-frozen adversarial questions through the real V5 P3 answer API.

Only structural safety/known-risk routing is testable unattended. It cannot
stand in for independent human financial correctness/decision quality review.
"""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path

from .advisory_answer_pipeline import answer
from .six_stage_original_replay import audit as source_audit

CASES=Path("ire/v5/validation/six_stage_frozen_advisory12_20261106.json")
REVIEWED_BLOB_SHA1="6c90c83405d61a7ca47107c2d03774bf529d7c10"

class SixStageAdvisoryError(ValueError): pass

def load(root:Path):
    original=(root/CASES).read_bytes()
    if hashlib.sha1(b"blob "+str(len(original)).encode("ascii")+b"\0"+original).hexdigest()!=REVIEWED_BLOB_SHA1:
        raise SixStageAdvisoryError("SIX_STAGE_QUESTIONS_CHANGED_AFTER_FREEZE")
    d=json.loads((root/CASES).read_text("utf-8"))
    if not (d.get("schema")=="IRE_V5_SIX_STAGE_FROZEN_UNSEEN_12_QUESTIONS_V1"
            and d.get("as_of")=="2026-11-06"
            and d.get("frozen_before_evaluator_created") is True
            and d.get("frozen_model")=="V5_CONDITIONAL_ANSWER_PIPELINE"
            and d.get("independent_human_reviewer_completed") is False
            and d.get("independent_financial_legal_advice_approved") is False
            and d.get("self_authored_questions_not_blind") is True
            and d.get("unknown_customer_portfolio_case_inputs_not_used") is True
            and d.get("release")==
                "STRUCTURAL_NEGATIVE_CHECK_ONLY_NOT_INDEPENDENT_ADVISORY_QUALITY_CERTIFICATION"
            and len(d.get("cases",[]))==12
            and {r["id"] for r in d["cases"]}==
                {f"F{i:02d}" for i in range(1,13)}):
        raise SixStageAdvisoryError("SIX_STAGE_FROZEN_EVAL_CONTRACT_CHANGED")
    for c in d["cases"]:
        if not (c.get("author")=="CHATGPT_SAME_SESSION_NOT_BLIND"
                and c.get("requires_independent_human_final_answer_review") is True
                and c.get("prohibit_automated_trade") is True
                and bool(c.get("mandatory_quarantine_id"))!=
                    bool(c.get("mandatory_existing_p4_id"))):
            raise SixStageAdvisoryError("SIX_STAGE_BAD_EVAL_AUTHORSHIP_OR_EXPECTATION")
    return d

def run(root:Path):
    root=Path(root)
    source=source_audit(root)
    cases=load(root)["cases"]
    results=[]
    for row in cases:
        actual=answer(root,row["question"])
        q=actual["crossvideo_unverified_risk_retrieval"]
        k=actual["p4_p3_source_education_retrieval"]
        riskids={x["case_id"] for x in q["items"]}
        knowledgeids={x["knowledge_id"] for x in k["items"]}
        match=(row["mandatory_quarantine_id"] in riskids
               if row["mandatory_quarantine_id"] else
               row["mandatory_existing_p4_id"] in knowledgeids)
        warned=(not row["mandatory_quarantine_id"] or
                "정식 금융사실 승인 전" in actual["answer_text"])
        safe=(not actual["direct_order_or_personal_recommendation_approved"]
              and not q["positive_legal_or_product_approval"]
              and not k["personal_order_approved"])
        results.append({"case_id":row["id"],"expected_routing_found":match,
                        "risk_scope_warning_rendered":warned,
                        "no_unapproved_personal_action":safe,
                        "structural_pass":bool(match and warned and safe)})
    passed=sum(r["structural_pass"] for r in results)
    if passed!=12:
        raise SixStageAdvisoryError(
            "SIX_STAGE_FROZEN_ADVICE_STRUCTURAL_REPRODUCTION_FAILED "+
            ",".join(x["case_id"] for x in results if not x["structural_pass"]))
    # Pure arithmetic reference calculations are separate from personal
    # tax, return, and suitability assertions.
    fx_change=(950/870-1)*100
    gift_million_krw=20+20+50+50+100
    distribution_krw=800_000_000*.06/12
    if not (9.19<fx_change<9.20 and
            gift_million_krw==240 and
            distribution_krw==4_000_000):
        raise SixStageAdvisoryError("SIX_STAGE_INDEPENDENT_ARITHMETIC_FAILED")
    return {
      "schema":"IRE_V5_SIX_STAGE_FROZEN_P3_EVAL_RESULT_V1",
      "new_questions_executed_against_actual_p3_pipeline":len(results),
      "structural_routing_and_no_action_checks_passed":passed,
      "prior_29_education_nodes_preserved":True,
      "new_extra_video_education_node_approvals":0,
      "corrected_yen_870_to_950_pct":round(fx_change,4),
      "hypothetical_gift_sum_million_krw":gift_million_krw,
      "hypothetical_monthly_6pct_distribution_krw":int(distribution_krw),
      "source_anchored_risk_cases":source["source_anchored_crossvideo_risk_challenges"],
      "evaluated_questions_self_authored":True,
      "human_blind_fact_grade_completed":False,
      "investment_decision_usefulness_independently_measured":False,
      "overall_advisory_product_approval":False,
      "cases":results,
      "release":"SAFETY_REGRESSION_CHECK_NOT_BLIND_ADVISORY_GO",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(run(a.root),ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
