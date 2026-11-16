"""V148 question-specific educational bridge, strictly below V123/V128 approval.

Runs the real, unchanged V5 P3 for lineage, but does not repeat its old-law
text. Distinct, scope-gated educational explanations clarify counterexamples,
math and official-page excerpts. No private video atoms, current-law byte
attestation, investor suitability, orders, or certified P0 quality is inferred.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import re

from ire.v5.advisory_answer_pipeline import answer as p3_answer

AS_OF = "2026-11-16"
ISA_URL = "https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1018255825"
PENSION_URL = "https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1030454707"
SEC_URL = "https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset"
_RULE_EXCERPT_WARNING = "법령 조문 웹 발췌에 근거한 일반적 설명이며, 이번 실행에서 발행기관 원문 HTTP 바이트와 개인별 자격을 인증하지 않았습니다."

ORDER = re.compile(r"(?:팔아\s*(?:줘|주세요)|(?:매수|매도|주문)해\s*(?:줘|주세요)|대신\s*(?:팔|사|매매)|(?:전량|전부).*?(?:팔아|매수해|매도해).*?(?:줘|주세요))")
ISA = re.compile(r"(?i)(?:ISA|개인종합자산관리).{0,45}(?:비과세|이자|배당|한도|500만원)|(?:비과세|이자|배당|한도).{0,45}(?:ISA|개인종합자산관리)")
PENSION = re.compile(r"(?:연금저축|연금계좌|IRP).{0,65}(?:세액공제|납입한도|공제한도|900만원|600만원)|(?:세액공제|납입한도).{0,65}(?:연금저축|연금계좌|IRP)",re.I)
CONCENTRATION = re.compile(r"(?:집중|분산|몰아넣|소수\s*종목|한\s*업종).{0,45}(?:종목|주식|안전|확신|위험|몰아넣)|(?:종목|확신|주식).{0,45}(?:집중|분산|안전|몰아넣)")
DIVIDEND = re.compile(r"(?:배당|배당수익률).{0,45}(?:안전마진|안전|원금|고배당)|(?:안전마진|원금).{0,45}(?:배당|배당수익률)")
DISTRESS = re.compile(r"(?:침체|부실|적자|손실|회복).{0,45}(?:기업|주식|기다|본전|성공|회복)|(?:기업|주식).{0,45}(?:침체|부실|적자|기다|회복)")
SUCCESS = re.compile(r"(?:신약|신기술|바이오|성공|확률|90\s*%).{0,60}(?:성공|확률|90\s*%|발표|투자|매수)|(?:결과\s*발표).{0,45}(?:투자|매수|성공)")
CYCLE = re.compile(r"(?:AI|인공지능|반도체|메모리|HBM).{0,60}(?:반도체|경기순환|경기\s*주기|재고|공급|사이클)|(?:경기순환|사이클|재고).{0,60}(?:AI|반도체|HBM)",re.I)
MATH = re.compile(r"(?P<principal>\d+(?:\.\d+)?)\s*억\s*원?.{0,35}?(?P<rate>\d+(?:\.\d+)?)\s*%")
MONTHLY = re.compile(r"(?:월급|월|한달|매월|매달)\s*(?:약\s*)?(?P<monthly>\d+(?:\.\d+)?)\s*만\s*원")


def _fmt_million(krw:Decimal)->str:
    man=krw/Decimal(10_000)
    if man==man.to_integral_value():
        return f"{int(man):,}만원"
    return f"{man:,.2f}만원"


def _math(q:str)->str|None:
    m=MATH.search(q)
    if m is None or not any(s in q for s in ("월", "생활비", "월급", "대체", "평생", "수익")):
        return None
    try:
        principal=Decimal(m.group('principal'))*Decimal(100_000_000)
        annual=principal*Decimal(m.group('rate'))/Decimal(100)
    except InvalidOperation:
        return None
    if not 0<principal<Decimal(10**15) or not 0<annual<Decimal(10**14):
        return None
    fragments=[f"{m.group('rate')}%가 **연간** 수익률이라는 별도 가정이면 투자원금 {m.group('principal')}억원 × {m.group('rate')}% = 세전 연 {_fmt_million(annual)}입니다."]
    monthly=MONTHLY.search(q)
    if monthly is not None:
        needed=Decimal(monthly.group('monthly'))*Decimal(10_000)*12
        fragments.append(f"{_fmt_million(Decimal(monthly.group('monthly'))*Decimal(10_000))} 매월 필요액은 연 {_fmt_million(needed)}입니다. "
                         "이는 위의 세전 예상 연 수익과 다른 숫자입니다.")
    fragments.append("수익률은 매년 일정하지 않으며 원금 손실·분배 중단·세금·물가·인출 순서 위험을 제외한 계산입니다. "
                     "평생 무세금 생활비를 보장하는 공식이 아닙니다.")
    return " ".join(fragments)


def _route(q:str, as_of:str):
    """Only route a recognized claim. No unrelated topic gets fabricated facts."""
    if ORDER.search(q):
        return "ORDER_DENIED", (
          "계좌의 매도·매수 주문은 실행하거나 자동 권고하지 않습니다. "
          "보유종목, 손실 허용 범위, 현금수요, 분산 여부와 근거를 확인하기 전 특정 종목·비중·거래 시점을 확정할 수 없습니다."), []
    if ISA.search(q):
        if as_of!=AS_OF:
            return "ISA_RULE_NEEDS_REFRESH", (
                "ISA 비과세 금액은 시행일과 계좌·가입자 요건에 따라 달라집니다. "
                "현재 기준일의 조문을 다시 확인하기 전 일반/우대 한도를 확정하지 않습니다."), [ISA_URL]
        return "ISA_RULE_CONDITIONAL", (
          "아닙니다. ISA의 모든 이자·배당수익 500만원이 누구에게나 비과세인 것은 아닙니다. "
          "2026-11-16 국가법령정보센터 조세특례제한법 제91조의18 웹 발췌에 따르면 일반 비과세 한도는 200만원, "
          "소득·농어민 등 법정 요건을 충족하는 우대 한도는 400만원입니다. "
          "가입·연장 시점, 거주자·소득 자격, 계좌의 적격성, 합산 기준과 초과분 과세를 각각 확인해야 합니다. "
          + _RULE_EXCERPT_WARNING), [ISA_URL]
    if PENSION.search(q):
        if as_of!=AS_OF:
            return "PENSION_RULE_NEEDS_REFRESH",(
                "연금저축과 IRP의 공제한도는 서로 독립된 두 개의 한도라는 가정이 잘못될 수 있습니다. "
                "조회 기준일의 소득세법 원문과 가입자 납입내역을 재확인해야 합니다."),[PENSION_URL]
        return "PENSION_RULE_CONDITIONAL",(
          "연금저축에 900만원을 넣었다고 900만원 전액이 세액공제 대상이 되는 것은 아닙니다. "
          "2026-11-16 소득세법 제59조의3 웹 발췌 기준 연금저축 납입 공제 한도는 연 600만원이고, "
          "IRP 등 퇴직연금 납입액까지 합산한 세액공제 대상은 연 900만원입니다. "
          "IRP가 별도로 900만원 추가되는 것이 아닙니다. 소득·산출세액·실제 납입액과 법정 제외납입을 확인하며 "
          "소득 조건에 따라 공제율은 소득세액 기준 12% 또는 15%입니다. "
          + _RULE_EXCERPT_WARNING),[PENSION_URL]
    result=_math(q)
    if result is not None:
        return "HYPOTHETICAL_MATH",result,[]
    if CONCENTRATION.search(q):
        return "CONCENTRATION_RISK",(
          "확신만으로 5개 이하 주식에 집중 투자하는 것이 안전해지는 것은 아닙니다. "
          "집중투자는 단일기업·업종 실패 시 손실 위험을 키우므로 일반 투자자에게는 분산투자 예외와 "
          "손실 감내 범위·투자 기간을 함께 평가해야 합니다. "
          "미국 SEC 투자자 교육 자료도 4~5개 개별 주식만으로는 충분한 분산이 이루어지지 않는다고 설명합니다. "
          "영상 속 특정 전략은 검증된 개인별 매수 권고가 아닙니다."),[SEC_URL]
    if DIVIDEND.search(q):
        return "DIVIDEND_NOT_MARGIN",(
          "높은 배당수익률 자체는 안전마진을 보장하지 않습니다. 주가 하락 때문에 수익률이 높아졌을 수 있고, "
          "배당 감액·중단과 기업의 현금흐름 악화가 발생할 수 있습니다. "
          "원금 위험을 따로 평가하고 배당의 지속가능성, 부채, 기업가치와 가격의 관계를 확인해야 합니다."),[]
    if DISTRESS.search(q):
        return "DISTRESS_NOT_GUARANTEE",(
          "침체 기업을 1~3년 기다린다고 회복이나 성공이 보장되지 않습니다. "
          "경쟁력 상실, 재무구조 악화, 증자·희석 또는 파산으로 투자원금의 영구손실이 발생할 가능성도 있습니다. "
          "산업 회복 가정과 개별 기업 생존·자금조달 능력은 별도로 검증해야 합니다."),[]
    if SUCCESS.search(q):
        pct=re.search(r"\b\d{1,3}\s*%",q)
        rate=pct.group(0).replace(' ','') if pct else '높은'
        return "SUCCESS_ODDS_UNVERIFIED",(
          f"신약·신기술의 성공확률 {rate}는 객관적 연구설계·검증자료가 없으면 가정이지 확정된 확률이 아닙니다. "
          "실패·승인 지연·발표 후 가격반응·자금조달 위험을 고려해야 하므로 결과 발표 전 매수나 투자 수익을 자동 권고하지 않습니다. "
          "공시·임상 단계·표본과 실패 가능성의 독립 근거가 필요합니다."),[]
    if CYCLE.search(q):
        return "SEMICONDUCTOR_CYCLE_CONDITIONAL",(
          "AI·인공지능 수요가 성장해도 반도체 경기순환이 없어졌다고 단정할 수 없습니다. "
          "메모리 공급 증설, 재고 조정, 판매가격, AI 이외 수요와 수급 시차가 경기 주기를 바꿉니다. "
          "과거 4년 주기는 역사적 경험칙이지 고정된 미래 예측 법칙이 아닙니다."),[]
    return "NO_DIRECT_FINANCIAL_DOMAIN",(
        "현재 승인된 연구 지식에서 질문과 직접 일치하는 금융 판단 영역을 확인하지 못했습니다. "
        "확인되지 않은 영상 주장이나 개인 계좌 정보를 근거로 투자 결론을 만들지 않습니다."),[]


def explain(root:Path, question:str, *, as_of:str=AS_OF)->dict:
    """Actual P3 call + fresh educational context; never automatically approved advice."""
    if type(question) is not str or not question.strip() or len(question)>4000:
        raise ValueError("V148_QUESTION_REQUIRED")
    if type(as_of) is not str or date.fromisoformat(as_of).isoformat()!=as_of:
        raise ValueError("V148_ASOF_DATE_REQUIRED")
    original=p3_answer(Path(root),question)
    if (original.get('schema')!='IRE_V5_P3_ANSWER_V1' or
        original.get('question')!=question or
        original.get('direct_order_or_personal_recommendation_approved') is not False or
        type(original.get('answer_text')) is not str):
        raise ValueError('V148_LEGACY_ANSWER_UNSAFE_OR_DRIFTED')
    route,body,urls=_route(question,as_of)
    body += "\n\n이 답변은 공식 조문 웹 발췌 또는 일반 위험 교육에 관한 설명입니다. " \
            "승인된 사용자 영상 연구 지식이나 투자자의 실제 계좌를 조회하지 않았습니다. " \
            "현행 법률·발행기관 원문 바이트 검증, 개인별 적용성 확인, 최종 ChatGPT 의미 검증은 별도입니다. " \
            "매매·주문·송금은 실행하지 않습니다."
    return {
      'schema':'IRE_V148_GUARDED_EDUCATIONAL_P3_BRIDGE_V1',
      'question':question, 'as_of':as_of,'answer_text':body,
      'matched_educational_route':route,
      'official_public_page_urls':urls,
      'legacy_v5_p3_executed':True,
      'legacy_v5_p3_answer_sha256':hashlib.sha256(original['answer_text'].encode()).hexdigest(),
      'legacy_v5_p3_text_rendered_as_current_law':False,
      'owner_approved_knowledge_db_attached':False,
      'v23_current_law_owner_e2e_executed':False,
      'issuer_original_http_body_authenticated':False,
      'personal_investor_eligibility_verified':False,
      'direct_order_or_personal_recommendation_approved':False,
      'automated_order_execution':False,
      'independently_adjudicated_answer_accuracy':False,
      'p0_e_go':False,'p0_go':False,
      'status':'EDUCATIONAL_CONTEXT_DIAGNOSTIC_ONLY_NO_OWNER_P0_APPROVAL',
    }
