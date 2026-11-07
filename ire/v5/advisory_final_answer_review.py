"""Re-evaluate actual rendered final answer text, not merely route/JSON shape.

Baseline Q01-Q12 was read from prior full GitHub CI logs and four substantive
direct-answer defects were recorded *before* this fix. Repaired cases are tuned,
so their pass rate must never be presented as out-of-sample accuracy. A separate
8-question post-edit exploratory probe is reported with its misses unaltered.
No external model API, blind expert reviewer or personal advice authorization.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .advisory_answer_pipeline import answer

CASES=Path("ire/v5/advisory_integration/P3_FINAL_ANSWER_ACCEPTANCE_20261105.json")

class FinalAnswerReviewError(ValueError):
    pass

def require(ok: bool, error: str) -> None:
    if not ok:
        raise FinalAnswerReviewError(error)

def run(root: Path, data: dict | None=None) -> dict:
    root=Path(root)
    j=(json.loads((root/CASES).read_text("utf-8"))
       if data is None else data)
    require(j.get("schema")=="IRE_V5_P3_FINAL_ANSWER_ACCEPTANCE_CASES_V1"
        and j.get("as_of")=="2026-11-05"
        and j.get("baseline_head")=="30c28f95f6b030e7757d346e2688239ace4eba71"
        and j.get("baseline_run_id")==41981236469
        and j.get("baseline_structural_passed")==12
        and j.get("baseline_user_question_directness_sufficient")==8
        and j.get("baseline_user_question_directness_total")==12
        and j.get("baseline_directness_failure_case_ids")==["Q05","Q07","Q09","Q10"]
        and j.get("independent_human_or_blind_review") is False
        and j.get("reviewer_is_same_chat_model") is True
        and j.get("new_advice_action_authorized") is False,
        "FINAL_QA_BASELINE_HISTORY_OR_APPROVAL_FALSIFIED")
    cases=j.get("repaired_cases",[])
    probes=j.get("exploratory_after_code_edited_questions",[])
    require(len(cases)==12 and len(probes)==j.get("exploratory_question_count")==8,
            "FINAL_QA_CASE_COUNT_INVALID")
    results=[]
    for x in cases:
        a=answer(root,x["question"],x.get("scenario"))
        txt=a["answer_text"]
        passed={
            "direct_answer_in_first_sentence":txt.startswith(x["lead"]),
            "question_specific_information":all(s in txt for s in x["terms"]),
            "source_alignment":set(x["sources"])<=set(a["fact_ids"]) and
                all(z in txt for z in a["cited_authority_urls"]),
            "calculation_if_requested":a["has_numeric_comparison"]==bool(x.get("scenario")),
            "no_unapproved_investment_action":
                a["direct_order_or_personal_recommendation_approved"] is False
                and a["current_law_fully_verified_in_this_run"] is False,
        }
        results.append({"id":x["id"],"passed":all(passed.values()),
                        "checks":passed,"first_sentence":txt.split("\n")[0],
                        "fact_ids":a["fact_ids"],"answer":txt})
    failed=[r["id"] for r in results if not r["passed"]]
    require(not failed,"FINAL_QA_REPAIRED_ANSWER_DEFECT_"+",".join(failed))
    # Exploratory questions are not used as regression requirements and may
    # fail; never quietly edit their expected terms after reading predictions.
    probe_results=[]
    for x in probes:
        out=answer(root,x["question"])
        txt=out["answer_text"]
        domain=x["expected_domain"] in out["domain_candidates"]
        terms=all(s in txt for s in x["probe_terms"])
        probe_results.append({
            "id":x["id"],"domain_present":domain,
            "expected_answer_material_present":terms,
            "passed":domain and terms,
            "lead":txt.split("\n")[0],
            "fact_ids":out["fact_ids"],
            "needs_human_subject_matter_check":True,
        })
    return {
        "schema":"IRE_V5_P3_FINAL_ANSWER_ACCEPTANCE_REPORT_V1",
        "baseline_structural_checks_passed":12,
        "baseline_direct_answers_sufficient":8,
        "baseline_directness_failures":["Q05","Q07","Q09","Q10"],
        "tuned_repaired_answer_cases_passed":sum(x["passed"] for x in results),
        "tuned_repaired_answer_cases_total":12,
        "post_edit_exploratory_cases_passed":sum(x["passed"] for x in probe_results),
        "post_edit_exploratory_cases_total":8,
        "post_edit_exploratory_failures":[x for x in probe_results if not x["passed"]],
        "factual_judgment_independently_expert_validated":False,
        "verified_external_live_page_in_ci":False,
        "formal_personal_investment_advice_authorized":False,
        "same_author_self_evaluation":True,
        "product_release_status":"CONDITIONAL_ADVICE_ANSWER_BETA_NOT_PERSONAL_GO",
        "repaired_cases":results,
        "exploratory":probe_results,
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(run(a.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
