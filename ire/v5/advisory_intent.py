"""Separate personal financial decision analysis from account order execution.

Classification is a cautious lexical router, NOT proof of investor suitability.
An educational comparison remains possible; trade execution is never enabled.
"""
from __future__ import annotations
import re

ORDER = re.compile(
    r"(?:매수|매도|팔아|팔아치|사줘|사s*줘|주문|전량s*팔|모두s*팔|"
    r"이체|옮겨|송금|교체|처리).*?"
    r"(?:해s*줘|해주세요|해s*주세요|시켜줘|실행해|눌러줘|바꿔줘|줘\b)"
    r"|(?:지금|즉시).*?(?:주문|매수|매도).*?(?:실행|진행|처리)"
    r"|(?:대신|직접).*?(?:주문|매수|매도|매매|팔아).*(?:해|줘|주세요)"
)
GUARANTEED = re.compile(
    r"(?:반드시|무조건|확정|절대).*?(?:수익|이익|보장|손실\s*없)"
    r"|(?:원금\s*보장|손실\s*없이|수익\s*보장)"
)
PERSONAL = re.compile(
    r"(?:내|제|저의|제가|저는|우리|나의|저한테|나에게)\s*"
    r"(?:ISA|IRP|연금|계좌|포트폴리오|자산|돈|투자|보유|상황|월급|목표|은퇴|소득)"
    r"|(?:내게|저에게|제게)"
)
DECISION = re.compile(
    r"(?:유리|불리|할까요|해야\s*하|괜찮|비교|판단|추천|선택|"
    r"어떻게|얼마|비중|계획|옮기|바꾸|리밸런싱|매수|매도|인출)"
)


def classify(question: str) -> dict:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("INTENT_EMPTY_QUESTION")
    q = question.strip().casefold()
    order = bool(ORDER.search(q))
    guaranteed = bool(GUARANTEED.search(q))
    if order:
        kind = "ORDER_EXECUTION_REQUEST"
    elif guaranteed:
        kind = "GUARANTEED_RETURN_REQUEST"
    elif PERSONAL.search(q) and DECISION.search(q):
        kind = "PERSONAL_DECISION_SUPPORT"
    else:
        kind = "GENERAL_EDUCATION"
    return {
        "kind": kind,
        "order_execution_requested": order,
        "guaranteed_result_requested": guaranteed,
        "personal_decision_support_requested": kind == "PERSONAL_DECISION_SUPPORT",
        "order_execution_authorized": False,
        "personal_investment_suitability_verified": False,
        "source_currentness_verified": False,
    }
