#!/usr/bin/env python3
"""Development-only #1-5 V3.1 semantic and rate-regression test.

All 44 labels were used in prior V3.0 diagnostics. Zero first-use claims.
Outputs are candidate-relevance diagnostics, never approved financial facts.
"""
import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from v30_verified_core import policy_gate,guard
from v30_semantic_v31 import development_from_original_history,pair_review,search_v31,derive_facets
from v30_finance_math_v31 import reproduce_v31
from v30_independent_evaluator import stats

ROOT=Path(__file__).resolve().parents[1]
ROSTER={1:"sz5N9WJS310",2:"6VEfKF7BzZU",3:"OiDTNstaSpM",
        4:"aNfGrcO6WPI",5:"qtluAViPpsQ"}
def fail(fn,reason):
    try:fn()
    except (ValueError,KeyError,TypeError):return
    raise ValueError("SECURITY_NEGATIVE_CASE_NOT_REJECTED_"+reason)
def run(root):
    policy_gate(root)
    reg=json.loads((root/"v30/validation/retro_001_005_diagnostic_cases_v1.json").read_text())
    guard(len(reg["cases"])==44,"DEVELOPMENT_CASE_UNIVERSE_CHANGED")
    corpus=development_from_original_history(root,ROSTER)
    guard(len(corpus)==62 and
          all(r["facets_review_state"]=="UNREVIEWED_RULE_BASED" for r in corpus),
          "HISTORICAL_FINANCE_ROLE_IMPROPERLY_PREAPPROVED")
    by={r["claim_id"]:r for r in corpus}
    domains=Counter()
    for r in corpus:domains.update(r["provisional_financial_facets"])
    results=[];direct=Counter();search_based=Counter()
    query_results={}
    for r in corpus:
        query_results[r["claim_id"]]=search_v31(r,corpus,top_k=10,
                                                  noncandidate_audit=10)
    for case in reg["cases"]:
        a=by[case["left"]];b=by[case["right"]]
        out=pair_review(a,b)
        relevant=case["review_relevant"]
        predicted=out["typed_review_candidate"]
        ab={x["claim_id"] for x in query_results[a["claim_id"]]["typed_review_queue"]}
        ba={x["claim_id"] for x in query_results[b["claim_id"]]["typed_review_queue"]}
        searched=b["claim_id"] in ab or a["claim_id"] in ba
        def cell(x):
            return ("TP" if relevant else "FP") if x else (
                    "FN" if relevant else "TN")
        direct[cell(predicted)]+=1
        search_based[cell(searched)]+=1
        results.append({"id":case["id"],"left":a["claim_id"],"right":b["claim_id"],
                        "human_development_gold":relevant,
                        "typed_event_review_candidate":predicted,
                        "typed_top10_either_direction":searched,
                        "shared_financial_events":out["shared_financial_events"],
                        "conflicts":out["conflicting_cross_scope_types"],
                        "source_risk":out["source_risk"]})
    # Test *unrelated* homonyms without fitting the 44 labels.
    def r(cid,text,status="QUALIFIED"):
        return {"claim_id":cid,"text":text,"legacy_verdict":status}
    contrasts=[
      (r("FIFAT000001-01","ISA 만기 3년 이후 계좌 해지 조건"),
       r("FIFAT000002-01","국채 만기 보유 시 원금 상환"),False),
      (r("FIFAT000001-02","한국은행 기준금리 3% 정책"),
       r("FIFAT000002-02","파킹형 ETF 연 3% 예상 수익률"),False),
      (r("FIFAT000001-03","사적 연금소득 과세와 비과세 인출"),
       r("FIFAT000002-03","IRP 세액공제 납입 한도"),False),
      (r("FIFAT000001-04","국민연금 수급 연기 연 7.2% 가산"),
       r("FIFAT000002-04","국민연금 연기연금과 재투자 비교"),True),
      (r("FIFAT000001-05","신용카드 할부 지출 통제"),
       r("FIFAT000002-05","과소비 내역을 다음달 예산으로 조정"),True),
      (r("FIFAT000001-06","퇴직금 장기투자와 분할투자"),
       r("FIFAT000002-06","퇴직금 월 500만원 분할 운용"),True),
    ]
    synthetic=0
    for left,right,expect in contrasts:
        got=pair_review(left,right)["typed_review_candidate"]
        guard(got==expect,"FINANCIAL_FACET_SYMPTOMATIC_CONTRAST_FAIL")
        synthetic+=1
    test=r("FIFAT000001-07","반박된 ISA 과세 주장","CONTRADICTED")
    out=pair_review(test,r("FIFAT000002-07","ISA 계좌 과세 검증"))
    guard(out["source_risk"]=="CORRECTION_ONLY"
          and out["automatic_knowledge_merge"] is False
          and out["approved_semantic_relation"] is False,
          "REFUTED_CLAIM_WAS_POSITIVELY_APPROVED")
    fail(lambda:pair_review(r("FIFAT000001-01","무효","PRIMARY_CONFIRMED"),
                            r("INVALIDCLAIM-01","ISA 과세")),"SOURCE_ID")
    fail(lambda:reproduce_v31({
         "model_type":"MONTHLY_SAVINGS_FUTURE_VALUE",
         "annual_rate":"0.07",
         "periods":84,
         "principal_or_monthly_contribution":"300000",
         "cashflow_timing":"END_OF_MONTH","currency":"KRW",
         "includes_fees_taxes":False
    }),"MISSING_RATE_CONVENTION")
    def math(years,conv):
        return reproduce_v31({
          "model_type":"MONTHLY_SAVINGS_FUTURE_VALUE",
          "annual_rate":"0.07","annual_rate_convention":conv,
          "periods":years*12,
          "principal_or_monthly_contribution":"300000",
          "cashflow_timing":"END_OF_MONTH","currency":"KRW",
          "includes_fees_taxes":False})
    rate_tests={}
    for years,expected_effective in ((7,Decimal("32141805.79")),
                                      (10,Decimal("51315519.38"))):
        a=math(years,"EFFECTIVE_ANNUAL")
        b=math(years,"NOMINAL_ANNUAL_DIVIDED_BY_12")
        guard(a["two_methods_agree"] and b["two_methods_agree"] and
              abs(Decimal(a["calculated_value"])-expected_effective)<=Decimal("2") and
              Decimal(b["calculated_value"])>Decimal(a["calculated_value"]),
              "EFFECTIVE_VS_NOMINAL_RATE_REPRODUCTION_FAILED")
        rate_tests[str(years)]={
          "effective_annual":a["calculated_value"],
          "nominal_over12":b["calculated_value"],
          "both_independent_methods_agree":True}
    zero=reproduce_v31({
         "model_type":"MONTHLY_SAVINGS_FUTURE_VALUE",
         "annual_rate":"0","annual_rate_convention":"EFFECTIVE_ANNUAL",
         "periods":12,"principal_or_monthly_contribution":"1000",
         "cashflow_timing":"BEGINNING_OF_MONTH",
         "currency":"KRW","includes_fees_taxes":False})
    guard(zero["calculated_value"]=="12000.00",
          "ZERO_INTEREST_BEGINNING_MONTH_EDGE_FAILED")
    return {
       "schema":"V31_001_005_DEVELOPMENT_DIAGNOSTIC_V1",
       "evaluation_class":"SEEN_DEVELOPMENT_NOT_BLIND",
       "source_claims":len(corpus),
       "labeled_historical_pairs":len(results),
       "provisional_auto_extracted_financial_facets_count":sum(domains.values()),
       "distinct_financial_event_facets":len(domains),
       "facets_provenance":"UNREVIEWED_PROVISIONAL_RULES_ONLY",
       "direct_typed_pair_diagnostic":stats({k:direct[k] for k in
                                             ("TP","FN","FP","TN")}),
       "typed_top10_either_direction_diagnostic":stats({
           k:search_based[k] for k in ("TP","FN","FP","TN")}),
       "synthetic_financial_homonym_contrasts":synthetic,
       "rate_tests":rate_tests,
       "cases":results,
       "real_financial_facts_independently_proven":0,
       "independent_unseen_first_use_cases":0,
       "automatic_research_certificates":0,
       "original_v30_v23_unchanged":True,
       "production_release":False,
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    try:
        res=run(args.root)
        if args.assert_snapshot:
            snap=args.root/"v30/validation/v31_001_005_dev_result_v1.json"
            guard(snap.is_file() and
                  json.loads(snap.read_text())==res,
                  "V31_DEVELOPMENT_CASE_SNAPSHOT_DRIFT")
        print(json.dumps(res,ensure_ascii=False,sort_keys=True))
    except (ValueError,KeyError,TypeError) as err:
        print(json.dumps({"gate":"FAIL","error":str(err)},ensure_ascii=False))
        raise SystemExit(1)
