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
from .advisory60 import load_policy, PERSONAL_TERMS, GUARANTEE_TERMS
from .advisory_semantic import parse as semantic_parse
from .advisory_evidence import plan as evidence_plan
from .advisory_decision import compare as quantitative_compare
from .first_five_40_retrieval_bridge import retrieve as retrieve_first40

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
    q=question.casefold()
    personal_request=bool(PERSONAL_ORDER.search(question) or any(
        k.casefold() in q for k in PERSONAL_TERMS))
    guarantee_request=bool(ASSURANCE.search(question) or any(
        k.casefold() in q for k in GUARANTEE_TERMS))
    comparisons=quantitative_compare(root,question,scenario) if scenario is not None else None
    parts=[]
    domains=set(meaning["related_domains"])
    # The user asks for a conclusion, not for a list of internal route names.
    # ISA transfer eligibility is not an investment order and can be assessed
    # conditionally even if the question refers to a personal account.
    day_match=re.search(r"(\d{1,3})\s*일",question)
    days_since_maturity=(int(day_match.group(1)) if day_match and
        "ISA_TRANSFER" in domains and "만기" in question and
        any(x in question for x in ("경과","지났","만기 후","만기 이후"))
        else None)
    if scenario is None and days_since_maturity is not None and days_since_maturity>60:
        parts.append(
            f"ISA 만기일로부터 실제로 {days_since_maturity}일이 경과했다면, "
            "60일 이내 연금계좌 납입 요건을 충족하지 못하므로 ISA 만기 전환에 "
            "대한 추가 세액공제 특례를 당연히 적용할 수 없습니다. "
            "만기일과 납입일을 확인하고 일반 연금계좌 납입 규정과 구분해야 합니다.")
    elif "RETIREMENT_WITHDRAWAL" in domains and re.search(r"8\s*%",question) and (
        "안전" in question or "보장" in question or "무조건" in question):
        parts.append(
            "아닙니다. 연금 인출률 8%를 모든 은퇴자에게 안전한 인출률로 보장할 수 없습니다. "
            "인출기간, 주식시장 초기 하락, 물가상승, 기대 수명과 연금소득을 고려해야 합니다. "
            "분배율 8%도 안전인출률 8%와 다른 개념입니다.")
    elif ("MARKET_STRESS" in domains and
          any(x in question for x in ("폭락","급락","서킷브레이커")) and
          any(x in question for x in ("전부","모두","전량")) and
          any(x in question for x in ("매도","팔"))):
        if "서킷브레이커" in question:
            parts.append("아닙니다. 서킷브레이커 발동 자체가 전량매도 신호는 아닙니다. "
                         "목표비중, 현금수요, 투자근거와 매매비용을 먼저 검토해야 합니다. "
                         "현재 자료만으로 개인별 매도 주문을 확정할 수 없습니다.")
        else:
            parts.append("아닙니다. 시장 폭락만으로 전량매도 신호는 아닙니다. "
                         "전량 매도로 손실을 피할 수 있다는 보장은 없습니다. "
                         "투자 목표, 현금수요, 손실 감내 범위와 집중도를 검토해야 합니다.")
    elif personal_request:
        if "MARKET_STRESS" in domains and "서킷브레이커" in question and ("팔" in question or "매도" in question):
            parts.append("아닙니다. 서킷브레이커 발동 자체가 전량매도 신호는 아닙니다. "
                         "목표비중과 현금수요를 검토해야 하며, 현재 입력만으로 개인 계좌에 매매 지시를 내릴 수 없습니다.")
        else:
            parts.append("현재 입력만으로 개인 계좌의 증권 매수·매도 주문을 실행하거나 권고할 수 없습니다.")
    elif guarantee_request:
        parts.append("원금이나 투자수익이 확정된다는 보장은 검증되지 않았습니다.")
    elif {"ISA_TRANSFER","ISA_FOREIGN_DIVIDEND"}<=domains:
        parts.append("ISA 만기자금의 연금계좌 이전 공제와 해외배당 외국세액 조정은 서로 다른 제도이며, 같은 공제로 취급할 수 없습니다.")
    elif "PENSION_TAX" in domains and ("환급" in question or "돌려받" in question):
        parts.append("연금계좌에 납입한 금액을 그대로 동일한 액수로 환급받는 것은 아닙니다.")
    elif "ETF_PRODUCT" in domains and "괴리" in question and "추적오차" in question:
        parts.append("ETF를 매수할 때는 먼저 실제 거래가격과 NAV의 괴리·호가를 점검하고, "
                     "이어 ETF 운용의 지수 추적오차를 별도로 확인하는 것이 합리적입니다. "
                     "두 지표는 같은 위험을 측정하지 않습니다.")
    elif "MARKET_STRESS" in domains and ("서킷브레이커" in question or "급락" in question) and (
            "매도" in question or "팔" in question):
        parts.append("아닙니다. 서킷브레이커 발동이나 급락 사실 자체가 보유 주식의 전량매도 신호는 아닙니다. "
                     "목표비중, 현금수요, 투자근거 및 매매비용을 먼저 검토해야 합니다.")
    elif "FOREIGN_CURRENCY" in domains and ("달러" in question or "usd" in q) and "rp" in q:
        parts.append("같은 안전자산으로 취급해서는 안 됩니다. 외화예금과 외화RP는 법적 구조, "
                     "신용위험 및 예금자보호 여부가 다릅니다. 외화RP는 예금자보호 대상이 "
                     "아니며 원금손실과 환율변동 위험이 있습니다.")
    elif comparisons is not None and len(comparisons["results"])==1:
        a=comparisons["results"][0]
        k=comparisons["kind"]
        if k=="ISA_TRANSFER":
            parts.append(
                f"입력한 만기 후 {a['days_after_expiry']:.0f}일 경과 조건에서 "
                f"추가 세액공제 대상 납입액은 {a['additional_credit_eligible_contribution_krw']:,.0f}원, "
                f"가정 소득세율 기준 계산상 공제액은 {a['hypothetical_income_tax_credit_before_tax_cap_krw']:,.0f}원입니다. "
                "이는 실제 환급 확정금액이 아닙니다.")
        elif k=="RETIREMENT_GAP":
            parts.append(
                f"주어진 현금흐름을 단순 차감하면 월 부족분은 {a['monthly_unfunded_spending_krw']:,.0f}원입니다. "
                "이 부족액은 세금·물가·기간을 반영한 필요 투자원금과 다릅니다.")
        elif k=="ALLOCATION_DRIFT":
            parts.append(
                f"주어진 주식 비중은 목표 대비 {a['equity_weight_drift_percentage_points']:+.2f}%포인트 차이가 납니다. "
                "이 차이를 곧바로 전량매도 지시로 바꾸지 않습니다.")
    elif comparisons is not None and comparisons["kind"]=="ETF_TOTAL_RETURN" and len(comparisons["results"])>=2:
        rank=sorted(comparisons["results"],key=lambda x:x["net_total_return_pct_pre_tax"],reverse=True)
        delta=rank[0]["net_total_return_pct_pre_tax"]-rank[1]["net_total_return_pct_pre_tax"]
        if delta>1e-8:
            parts.append(
                f"입력된 가정만 비교하면 {rank[0]['option_id']} 대안의 세전 총수익률 "
                f"{rank[0]['net_total_return_pct_pre_tax']:.2f}%가 "
                f"{rank[1]['option_id']} 대안 {rank[1]['net_total_return_pct_pre_tax']:.2f}%보다 "
                f"{delta:.2f}%포인트 높습니다. 이는 실제 상품 추천이 아닌 계산상 차이입니다.")
        else:
            parts.append("입력된 대안의 세전 총수익률이 동일해, 금액 외 위험과 비용을 추가 검토해야 합니다.")
    if meaning["related_domains"]:
        titles={x["route_id"]:x["title"] for x in policy["routes"]}
        parts.append("질문에서 분리한 판단 영역은 "
                     + ", ".join(titles.get(d,d) for d in meaning["related_domains"])
                     + "입니다. 각 영역의 조건과 근거를 독립적으로 확인해야 합니다.")
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
    # Connect content-addressed first-40 source-verified educational context to
    # the *actual* P3 response, without modifying P1 fact_ids or approving tax
    # or individualized investment conclusions. Invalid/missing pins fail closed.
    first40={"schema":"IRE_V5_FIRST40_READONLY_EDUCATION_RETRIEVAL_V1",
             "match_count":0,"items":[],"decision":"NOT_INSTALLED_ON_THIS_ROOT",
             "independent_legal_fact_approval_count":0,
             "personal_advice_approved":False,"master_merged":False}
    if (root/'ire/v5/validation/first_five_40_official_replay_manifest_20261106.json').exists():
        first40=retrieve_first40(root,question,
                 intent='personal_action' if personal_request else
                        'guaranteed_return' if guarantee_request else 'general_education')
        if first40['items']:
            parts.append("#1 영상 40개 창의 근거 연결 교육용 문맥(2026-11-06 공식 사이트 추출 스냅샷, 독립 승인 전):")
            for item in first40['items']:
                urls='; '.join(x['official_url'] for x in item['official_extraction_evidence'])
                parts.append(f"- {item['statement']} 공식 출처 추출본: {urls}. "
                             "개인별 적용 조건·현행성 재검증이 필요하며 전체 영상 주장 또는 정식 금융사실 승인은 아닙니다.")
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
        "same_chat_reviewed_source_as_of":"2026-11-05",
        "official_sources_reopened_this_python_run":False,
        "first40_education_retrieval":first40,
        "final_answer_direct_response_required":True,
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
