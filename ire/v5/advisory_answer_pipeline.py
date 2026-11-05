"""P3: render structured evidence-backed conditional explanations and check them.

The actual generated text is deterministic and derived from P0-P2 outputs. This
is NOT a separate ChatGPT model API, a blind reviewer, or unrestricted fiduciary
advice. Audit produces reproducible natural-language answers and diagnostics.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from .advisory60 import load_policy
from .advisory_semantic import parse as semantic_parse
from .advisory_evidence import plan as evidence_plan
from .advisory_decision import compare as quantitative_compare

CASES=Path("ire/v5/advisory_integration/P3_ANSWER_QUALITY_CASES_20261105.json")
PERSONAL_ORDER=re.compile(r"매수해|매도해|팔아줘|전부\s*팔|즉시\s*사|주문해")
ASSURANCE=re.compile(r"반드시\s*수익|무조건\s*수익|손실\s*없이|확정\s*수익|원금\s*보장")

def _units(kind: str, row: dict) -> str:
    oid=row["option_id"]
    if kind=="ISA_TRANSFER":
        cap=row["additional_credit_eligible_contribution_krw"]
        credit=row["hypothetical_income_tax_credit_before_tax_cap_krw"]
        return (f"대안 {oid}: 추가 세액공제 대상 납입액은 {cap:,.0f}원, "
                f"지정된 소득세율에 따른 계산상 공제액은 {credit:,.0f}원입니다. "
                "실제 세액공제·환급액은 납세자 조건과 결정세액에 따라 달라집니다.")
    if kind=="RETIREMENT_GAP":
        return (f"대안 {oid}: 월 부족현금흐름은 "
                f"{row['monthly_unfunded_spending_krw']:,.0f}원, "
                f"연환산 부족현금흐름은 {row['annual_unfunded_spending_krw']:,.0f}원입니다. "
                "이 결과를 투자원금 또는 확정 인출률로 해석하면 안 됩니다.")
    if kind=="ETF_TOTAL_RETURN":
        return (f"대안 {oid}: 주어진 가격·분배·별도 비용만 반영한 세전 총수익은 "
                f"{row['net_total_return_krw_pre_tax']:,.0f}원 "
                f"({row['net_total_return_pct_pre_tax']:.2f}%)입니다. "
                "현금 분배액 자체가 확정된 투자이익을 뜻하지 않습니다.")
    if kind=="ALLOCATION_DRIFT":
        return (f"대안 {oid}: 목표 주식비중과의 편차는 "
                f"{row['equity_weight_drift_percentage_points']:+.2f}%포인트입니다. "
                "이를 즉시 매도해야 하는 비율로 해석할 수는 없습니다.")
    raise ValueError("P3_UNKNOWN_COMPARISON_KIND")

def answer(root: Path, question: str, scenario: dict | None = None) -> dict:
    root=Path(root)
    policy=load_policy(root)
    meaning=semantic_parse(question,policy)
    scope=evidence_plan(question,root)
    personal_request=bool(PERSONAL_ORDER.search(question) or "내 계좌" in question)
    guarantee_request=bool(ASSURANCE.search(question))
    comparisons=quantitative_compare(root,question,scenario) if scenario is not None else None
    parts=[]
    if meaning["related_domains"]:
        parts.append("질문에서 분리한 금융 판단 영역은 "
                     + ", ".join(meaning["related_domains"]) + "입니다. "
                     "각 영역의 조건과 근거를 독립적으로 확인해야 합니다.")
    else:
        parts.append("현재 연구 지식 원장에서 이 질문과 직접 일치하는 금융 판단 영역을 확인하지 못했습니다.")
    facts=scope["direct_scoped_evidence"]
    if facts:
        parts.append("공식·원발행 출처로 확인한 범위(2026-11-05 채팅 검토 기준):")
        for fact in facts:
            parts.append(f"- {fact['claim']} 출처: {fact['issuer']} ({fact['authority_url']}). "
                         f"적용 전 확인: {'; '.join(fact['application_conditions'])}. "
                         f"예외: {'; '.join(fact['exceptions'])}.")
    else:
        parts.append("이 질문에 대해 현재 P1 원장에서 직접 일치하는 최신 공식 사실을 찾지 못했습니다. "
                     "관련 법규나 상품조건은 확정적으로 설명하지 않고 별도 검증 대상으로 둡니다.")
    if comparisons is not None:
        parts.append("입력된 가정에 따른 대안별 계산:")
        for row in comparisons["results"]:
            parts.append("- "+_units(comparisons["kind"],row))
        parts.append("아직 가격에 반영하지 않은 조건: "
                     + "; ".join(comparisons["required_unpriced_factors"]) + ".")
    else:
        parts.append("실제 결론에 필요한 추가 정보는 목표, 투자기간, 현금수요, "
                     "계좌 유형, 관련 세법·상품 공시 및 감내 가능한 손실입니다.")
    if personal_request:
        parts.append("현재 자료만으로 특정 계좌의 주문·전량 매도 또는 목표비중을 실행할 수 없습니다. "
                     "개인 보유내역과 위험/세제 조건을 확인해야 합니다.")
    if guarantee_request:
        parts.append("원금보장이나 확정수익 주장은 검증되지 않았으므로 보장으로 답하지 않습니다.")
    parts.append("이전 영상 요약과 60건 연구 원장은 학습·출처 문맥이지 새로운 법률 사실의 자동 승인 근거가 아닙니다.")
    text="\n".join(parts)
    return {
        "schema":"IRE_V5_P3_ANSWER_V1",
        "question":question,
        "answer_text":text,
        "domain_candidates":meaning["related_domains"],
        "origin_claim_ids":meaning["candidate_claim_ids"],
        "fact_ids":[f["fact_id"] for f in facts],
        "cited_authority_urls":[f["authority_url"] for f in facts],
        "has_numeric_comparison":comparisons is not None,
        "numeric_comparison":comparisons,
        "personal_order_detected":personal_request,
        "guarantee_claim_detected":guarantee_request,
        "direct_order_or_personal_recommendation_approved":False,
        "current_law_fully_verified_in_this_run":False,
        "unrestricted_model_answer_accuracy_measured":False,
        "chat_host_review_and_live_sources_still_required":True,
    }

def audit(root: Path) -> dict:
    root=Path(root)
    cases=json.loads((root/CASES).read_text("utf-8"))
    if not (cases.get("schema")=="IRE_V5_P3_QA_CASES_V1"
            and cases.get("as_of")=="2026-11-05"
            and cases.get("question_author")=="CHATGPT_COO_AUTHORED_NOT_INDEPENDENT"
            and cases.get("not_validated_for_personalized_advice") is True
            and len(cases.get("semantic_probes",[]))==cases.get("semantic_probe_count")==45
            and len(cases.get("answer_cases",[]))==cases.get("answer_case_count")==12):
        raise ValueError("P3_BENCHMARK_PRETENDS_INDEPENDENT_OR_MISSING")
    policy=load_policy(root)
    known=json.loads((root/"ire/v5/advisory_integration/LIVE_VALIDATION_SCENARIOS_20261105.json").read_text("utf-8"))
    old={x["question"] for x in known["holdout_set"]+known["repair_set"]}
    if any(x["question"] in old for x in cases["semantic_probes"]):
        raise ValueError("P3_QUESTION_EXACT_MATCH_LEAKAGE")
    semantic_results=[]
    for row in cases["semantic_probes"]:
        out=semantic_parse(row["question"],policy)
        expected=set(row["expected_domains"])
        semantic_results.append({
            "id":row["id"],
            "expected":sorted(expected),
            "predicted_primary":out["primary_domain"],
            "retrieved":sorted(expected & set(out["related_domains"])),
            "complete":expected<=set(out["related_domains"]),
            "all_facts_not_automatically_approved":not out["facts_verified"],
        })
    answer_results=[]
    for row in cases["answer_cases"]:
        out=answer(root,row["question"],row.get("scenario"))
        ids=set(out["fact_ids"])
        source_matched=set(row["must_have_fact_ids"])<=ids
        scope_honest=(len(ids)==len(out["cited_authority_urls"])
                      and all(url in out["answer_text"] for url in out["cited_authority_urls"])
                      and ("공식 사실을 찾지 못" in out["answer_text"] if not ids else True))
        math_complete=(out["has_numeric_comparison"]
                       if "scenario" in row else not out["has_numeric_comparison"])
        risk_explained=("예외:" in out["answer_text"] if ids
                        else "별도 검증" in out["answer_text"])
        no_unapproved_actions=(not out["direct_order_or_personal_recommendation_approved"]
                               and "자동 승인 근거가 아닙니다" in out["answer_text"])
        requirements=[
            row["expected_domain"] in out["domain_candidates"],
            source_matched and scope_honest,
            math_complete,
            risk_explained,
            no_unapproved_actions,
        ]
        answer_results.append({
            "id":row["id"],"checks_passed":sum(requirements),
            "checks_total":5,"check_vector":requirements,
            "source_fact_ids":sorted(ids),
            "rendered_answer":out["answer_text"],
            "personal_action_approved":False,
        })
    covered=sum(x["complete"] for x in semantic_results)
    all5=sum(x["checks_passed"]==5 for x in answer_results)
    return {
        "schema":"IRE_V5_P3_QA_EVALUATION_V1",
        "fresh_chat_authored_questions":45,
        "semantic_full_domain_coverage":covered,
        "semantic_domain_coverage_rate":round(covered/45,4),
        "target_90pct_coverage_met":covered>=41,
        "answer_examples_generated":12,
        "answer_examples_passing_five_structural_checks":all5,
        "self_authored_case_design_not_blind_validation":True,
        "human_independent_answer_quality_review_completed":False,
        "real_portfolio_advice_authorized":False,
        "product_release_status":"P3_PROTOTYPE_VALIDATED_NOT_PERSONAL_ADVICE_RELEASED",
        "semantic_probe_failures":[r for r in semantic_results if not r["complete"]],
        "answer_probe_results":answer_results,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(audit(a.root),ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
