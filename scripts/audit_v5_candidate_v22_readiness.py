#!/usr/bin/env python3
"""Independent pre-new-video audit for the already-frozen V2.2 engine.

Never reads #17 or later videos, never retrains V2.2, and never promotes a
candidate into verified financial knowledge. Tests include:
 - immutable engine/evaluator + all 4 original benchmark blobs
 - 180-claim provenance and 251-case previous developer regression
 - fresh synthetic metamorphic probes (NOT independent blinded human gold)
 - candidate flood concentration & source status risk across all 16,110 pairs
 - missing-verdict and over-wide retrieval API contract exposures
"""
import argparse
import collections
import itertools
import json
from pathlib import Path

from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from evaluate_v5_candidate_v22 import source_contract_v22,evaluate
from v5_candidate_engine_v22 import retrieve
from v5_candidate_engine_v21 import retrieve as old_retrieve

ROOT=Path(__file__).resolve().parents[1]
SNAP="v5/integration/v22_development_001_016_v1.json"
BASE="v5/integration/v21_development_001_014_v1.json"
AUDIT="v5/integration/v22_pre_new_video_audit_v1.json"

# Hypothesis-oriented synthetic cases, authored for AUDIT AFTER V2.2 freeze.
# Finance relation labels are reviewer assumptions, not independently blind.
# Pair texts are not from new or hidden videos.
PROBES=[
 ("N01_contribution_vs_income_tax",False,
  "연금저축의 연간 납입한도는 1,800만원이다",
  "연금소득 연 1,500만원 과세기준과 종합과세를 비교한다"),
 ("N02_account_budget_vs_asset_allocation",False,
  "청년 저축 50만원 ISA 40만원 연금저축 10만원을 매달 납입한다",
  "주식과 채권 자산군의 위험을 고려해 자산배분을 조정한다"),
 ("N03_dividend_vs_retirement_lump",False,
  "미국 배당주로 받은 배당금을 재투자하며 정기매수한다",
  "퇴직금 목돈을 과거 월급만큼 3년 동안 분할투자한다"),
 ("N04_dividend_cadence_vs_japan_tax",False,
  "국내 미국배당다우존스 ETF는 월분배하고 미국 SCHD는 분기배당한다",
  "일본 상장 미국주식 ETF의 배당과 국내 및 일본 현지 과세를 비교한다"),
 ("N05_index_membership_vs_yen_fx_route",False,
  "미국 배당주 지수는 기업의 배당이력 및 재무건전성을 기준으로 구성한다",
  "원화를 엔화로 환전한 뒤 일본 상장 ETF를 매수하는 투자 경로다"),
 ("N06_loan_rollover_vs_equity_concentration",False,
  "구독자가 연금담보대출을 상환·재대출하며 부채비율을 조절했다",
  "주식 ETF를 보유해도 상위 시총기업과 섹터 집중 위험이 있다"),
 ("N07_fixed_contribution_vs_equity_dividend",False,
  "월 30만원 연 7% 7년 적립의 잔고 계산은 기간과 금액이 불일치한다",
  "미국 배당 ETF 배당금 재투자로 장기 복리 효과를 기대한다"),
 ("N08_unrelated_cash_products",False,
  "은행 예금자보호한도는 해당 예금에 적용된다",
  "미국배당다우존스 ETF는 다수 배당기업 지수를 추종한다"),
 ("N09_bond_etf_vs_fx_spread",False,
  "일본 국채 ETF는 만기에 따라 금리 위험이 다르다",
  "일본 엔화 직접 환전 때 환전 스프레드 비용이 발생한다"),
 ("N10_dividend_tax_vs_ordinary_pension_tax",False,
  "일본상장 미국ETF의 배당은 현지와 국내 과세를 검토해야 한다",
  "퇴직연금계좌 연금수령 시 연금소득 과세 규칙을 적용한다"),
 ("N11_household_wages_vs_stock_distribution",False,
  "월 100만원 급여에서 ISA와 연금저축으로 예산을 나눠 납입한다",
  "주식 ETF는 배당을 월분배하여 현금흐름을 제공할 수 있다"),
 ("N12_share_vs_monthly_contributions",False,
  "배당 ETF의 소액 1주 매수 가격은 만원대일 수 있다",
  "국민연금 실효 수익률 7% 10년간 매월 30만원 적립 계산은 오류가 있다"),
 ("P01_all_weather_vs_allocation",True,
  "올웨더 전략은 거시환경 성장률과 물가에 맞춰 주식 채권 금 원자재의 위험을 배분한다",
  "채권과 금을 섞어 주식 집중 위험을 낮추는 자산배분 포트폴리오를 설명한다"),
 ("P02_equity_vs_cash_currency",True,
  "경제 상황에 따라 주식 채권 금 원자재의 위험 역할은 달라질 수 있다",
  "엔화라는 현금성 자산과 일본 주식의 가격 변동성은 서로 다르다"),
 ("P03_dividend_vs_cashflow",True,
  "배당주를 통해 월마다 안정적 현금흐름을 만들 수 있다고 제안한다",
  "은퇴 현금흐름을 분배금으로 설계할 때 지급 지속성과 위험을 검토한다"),
 ("P04_dividend_reinvest_vs_dca",True,
  "배당금 재투자와 배당주 정기매수를 통해 복리 수익을 추구한다",
  "주기적으로 배당금을 재투자하고 신규 저축으로 주식을 축적한다"),
 ("P05_ETF_overlap",True,
  "나스닥100 ETF와 배당 ETF의 구성종목 중복은 집중 위험을 만든다",
  "미국 대형주 지수 ETF는 상위 시총기업 편중과 섹터 위험을 포함한다"),
 ("P06_historical_average_vs_reality",True,
  "장기 연평균 수익률은 실제 개인 보유기간의 실현수익과 다를 수 있다",
  "주가지수 백테스트의 과거 수익률을 미래 ETF 성과로 보장할 수 없다"),
 ("P07_dividend_cadence_vs_income",True,
  "미국 SCHD 분기배당과 국내 배당 ETF 월분배 방식은 달라진다",
  "은퇴 월별 현금흐름을 위해 분배형 ETF의 지급 주기를 비교한다"),
 ("P08_drawdown_and_panic_sell",True,
  "시장 폭락 후 원금 회복에는 10년 이상 장기 침체가 이어질 수 있다",
  "하락장에서 주식을 매도하면 이후 반등을 놓칠 수도 있다"),
 ("P09_index_construction",True,
  "S&P 500 지수 ETF는 미국 대형주 시장에 간접투자한다",
  "미국 배당다우존스 ETF는 배당기업 100개로 지수를 구성한다"),
 ("P10_rebalance_vs_risk",True,
  "상관관계가 낮은 주식 채권 금 자산을 자산배분하면 변동성 위험이 줄 수 있다",
  "리스크패리티 포트폴리오의 채권 및 금 비중을 조절해 위험을 균형 배분한다"),
]

def source_freeze(root):
    snap=read(root/SNAP);prior=read(root/BASE)
    fixed=[
       ("V22 engine",snap["engine_path"],snap["engine_git_blob_sha"]),
       ("V22 evaluator",snap["evaluator_path"],snap["evaluator_git_blob_sha"]),
       ("V21 engine",prior["source_engine_path"],prior["source_engine_git_blob_sha"]),
       ("V21 evaluator",prior["evaluator_path"],prior["evaluator_git_blob_sha"]),
       ("V21 15-16 labels",snap["prior_15_16_preregistered_labels_path"],
                             snap["prior_15_16_labels_git_blob_sha"]),
       ("V21 15-16 first-use outcomes",snap["prior_failed_holdout_path"],
                             snap["prior_failed_holdout_git_blob_sha"]),
    ]
    for k,v in prior["benchmark_blobs"].items():
        maps={"baseline_001_010":"benchmark_001_010_v1.json",
              "baseline_011_012":"benchmark_011_012_holdout_v1.json",
              "baseline_013_014":"benchmark_013_014_v2_holdout_v1.json"}
        fixed.append((k,"v5/integration/"+maps[k],v))
    statuses=[]
    for name,path,expected in fixed:
        actual=git_blob_sha(root/path)
        need(actual==expected,f"frozen evidence mutated: {name} {path}")
        statuses.append({"name":name,"path":path,"git_blob_sha":actual,
                         "matched":True})
    return statuses

def synthetic_probe_check():
    outcomes=[]
    for name,expected,a,b in PROBES:
        got,trace=retrieve(a,b,
            left_verdict="QUALIFIED",right_verdict="QUALIFIED")
        reversed_result,reversed_trace=retrieve(b,a,
            left_verdict="QUALIFIED",right_verdict="QUALIFIED")
        need(got==reversed_result,"synthetic pair order changed "+name)
        need(trace["automatic_knowledge_approval"] is False and
             trace["semantic_relation_prediction"] is None and
             trace["candidate_is_evidence_of_claim_truth"] is False and
             trace["review_only"] and not trace["correction_only"],
             "synthetic candidate was unreviewedly auto-approved")
        outcomes.append({"id":name,"expected_candidate":expected,
         "actual_candidate":got,"matches_expectation":bool(got)==expected,
         "inherited_v21_positive":trace["v22_base_v21_candidate"],
         "v22_bridges":trace["v22_bridges"],
         "v22_scope_blocks":trace["v22_scope_blocks"],
         "inherited_scope_blocks":trace["inherited_v21_v2_scope_blocks"]})
    return outcomes

def whole_universe_audit(claims):
    candidate_count=0
    degree=collections.Counter(); bridge=collections.Counter()
    reason=collections.Counter();by_verdict=collections.Counter()
    unknown=0;refuted=0;hypothetical=0;inherited=0
    samples={"risk_positive":[],"no_explanation":[]}
    # Count 180-claim universe, not 251 selected diagnostic predictions.
    for aid,bid in itertools.combinations(sorted(claims),2):
        a,b=claims[aid],claims[bid]
        got,why=retrieve(a["text"],b["text"],
            left_verdict=a["verdict"],right_verdict=b["verdict"])
        if not got:continue
        candidate_count+=1;degree[aid]+=1;degree[bid]+=1
        prior=bool(why["v22_base_v21_candidate"])
        inherited+=int(prior)
        for k in why["v22_bridges"]:bridge[k]+=1
        if prior and not why["v22_bridges"]: reason["inherited_only"]+=1
        elif prior:reason["both"]+=1
        else:reason["v22_only"]+=1
        tags={a["verdict"],b["verdict"]}
        if "HYPOTHETICAL" in tags:
            hypothetical+=1
        if "CONTRADICTED" in tags:
            refuted+=1
            need(why["correction_only"],"refuted claim edge lacks correction-only flag")
        else:
            need(not why["correction_only"],"unrefuted claim incorrectly marked")
        need(why["semantic_relation_prediction"] is None and
             why["automatic_knowledge_approval"] is False and
             why["candidate_is_evidence_of_claim_truth"] is False,
             "whole-universe edge incorrectly approved")
        if not (why["v22_bridges"] or why.get("v21_bridges") or why.get("evidence")):
            if len(samples["no_explanation"])<8:
                samples["no_explanation"].append([aid,bid])
            unknown+=1
        if "HYPOTHETICAL" in tags and len(samples["risk_positive"])<8:
            samples["risk_positive"].append([aid,bid])
        by_verdict["+".join(sorted(tags))]+=1
    need(candidate_count==2211,"total frozen source candidate count drift")
    need(sum(degree.values())==candidate_count*2,
         "claim degree budget mismatch")
    return {"candidate_count":candidate_count,
      "candidate_pairs_not_individually_adjudicated_at_least":candidate_count-164,
      "inherited_v21_candidate_count":inherited,
      "source_hypothetical_involved_count":hypothetical,
      "source_contradicted_involved_count":refuted,
      "no_evidence_code_count":unknown,
      "top_hubs":[{"claim_id":k,"candidate_edges":v}
                  for k,v in degree.most_common(12)],
      "top_v22_bridges":[{"code":k,"candidate_edges":v}
                         for k,v in bridge.most_common(18)],
      "edge_origin_counts":dict(reason),
      "verdict_pair_distribution":dict(by_verdict),
      "small_example_id_pairs":samples}

def audit(root):
    statuses=source_freeze(root)
    claims,rows=source_contract_v22(root)
    need(len(claims)==180 and len(rows)==251,
         "frozen development source universe not intact")
    previous=evaluate(root,False)
    need(previous["total_confusion"]=={"TP":164,"FN":0,"FP":0,"TN":87}
         and previous["candidate_pairs_all"]==2211,
         "V2.2 development replay drift")
    actual=synthetic_probe_check()
    census=whole_universe_audit(claims)
    # A caller that omits original verdict cannot have the engine infer source
    # truth status. Record this API hazard rather than treating it as approved.
    sample="월 30만원 연 7% 7년 계산은 잘못된 수치였다"
    _,with_status=retrieve(sample,sample,
                    left_verdict="CONTRADICTED",right_verdict="QUALIFIED")
    _,without_status=retrieve(sample,sample)
    need(with_status["correction_only"] is True and
         without_status["correction_only"] is False,
         "source-verdict API behavior changed; audit impact")
    failures=[x for x in actual if not x["matches_expectation"]]
    return {"schema":"V5_V22_PRE_NEW_VIDEO_INDEPENDENT_CODE_REAUDIT_V1",
      "scope":"ONLY_FROZEN_1_TO_16_AND_SYNTHETIC_TEXT__NO_17_PLUS_ACCESS",
      "engine_sha":statuses[0]["git_blob_sha"],
      "files_verified":statuses,
      "baseline_development_cases":251,"baseline_confusion":previous["total_confusion"],
      "synthetic_probe_count":len(PROBES),
      "synthetic_probe_positive_expected":sum(x[1] for x in PROBES),
      "synthetic_probe_negative_expected":sum(not x[1] for x in PROBES),
      "synthetic_probe_failures":len(failures),
      "synthetic_probe_error_cases":failures,
      "synthetic_probe_cases":actual,
      "universe_census":census,
      "api_contract_probe":{"explicit_contradicted_correction_only":
                              with_status["correction_only"],
                            "missing_verdict_correction_only":
                              without_status["correction_only"],
                            "required_future_control":
                              "upstream must supply verified original source verdict"},
      "new_videos_used":0,
      "external_blind_gold":False,
      "semantic_approvals":0,
      "automatic_merges":0,
      "readiness":"BLOCKED_FOR_UNSEEN_VIDEO_DEPLOYMENT_PENDING_AUDIT_REVIEW"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    r=audit(args.root.resolve())
    if args.assert_snapshot:
        prior=read(args.root/AUDIT)
        # Never allow the audit to silently rewrite evidence of failures.
        need(prior==r,"frozen independent V2.2 pre-video audit changed")
    print(json.dumps(r,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as ex:
        print(json.dumps({"gate":"FAIL","error":str(ex)},ensure_ascii=False))
        raise SystemExit(1)
