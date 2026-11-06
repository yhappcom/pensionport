"""Quarantined #6-#10 cross-video risk signals in P3 advice; not new P4 facts.

This compact bridge reads 14 owner-source-anchored challenge records. It does
NOT elevate a compilation, the 2026 gift-tax rules, yen forecasts, or a short
video's overgeneralizations into the authoritative 116-claim master.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .six_stage_original_replay import audit as source_audit, read as read_source

# Only exact material user intent phrases, not generic term matches such as
# "연금", "ISA", "엔화", which would create unwarranted alarm.
TRIGGERS={
 "CV-006-GIFT-2000":("자녀에게 2천만원","자녀에게 2000만원","미성년자 증여공제",
                      "자녀 증여 2천","미성년 2천"),
 "CV-006-GIFT-STOCK-VALUATION":("자녀 주식증여 평가","증여 후 주가상승","증여주식 평가"),
 "CV-006-GIFT-240M":("2.4억 증여","2억4천 증여","30년 증여 비과세"),
 "CV-006-GIFT-RETURN":("자녀 증여 수익 3억","35년 후 3억 수익"),
 "CV-007-COMPILATION":("구독자사연 몰아보기","영상 7번 독립 검증","7번 영상 독립"),
 "CV-008-YEN-ETF-TAX":("엔화 ETF 과세","엔화ETF 과세","엔화 etf 세금"),
 "CV-008-JP-STOCK-TAX":("일본주식 양도세 22","일본 주식 양도소득세","해외주식 250만원 공제"),
 "CV-008-FX-HEDGE":("엔화 환헤지","엔저 환헤지","엔화 환노출"),
 "CV-009-YEN-10PCT":("엔화 10% 수익","엔화 10퍼센트","원엔 870 950"),
 "CV-009-FX-SPREAD":("환전 스프레드","엔화 환율 우대","원엔 환전 수수료"),
 "CV-010-PENSION-ALL-BETTER":("세액공제 안받아도 무조건","세액공제 안 받아도 무조건",
                              "연금저축 항상 유리","연금저축 무조건 유리"),
 "CV-010-ACCOUNT-TAX":("일반계좌 수익마다 세금","미국 ETF 수익마다 세금"),
 "CV-010-LOW-RATE":("연금수익 항상 3.3","연금수익 항상 5.5",
                      "연금 저율과세 무조건","연금 3.3~5.5"),
 "CV-010-WITHDRAW-ANYTIME":("세액공제 안 받은 원금 언제든","비공제 원금 언제든",
                            "연금저축 중도인출 자유"),
}


class CrossvideoGuardError(ValueError):pass


def verify(root:Path):
    root=Path(root)
    source=source_audit(root)
    d=read_source(root)
    rows=d["risk_challenges"]
    known={r["case_id"] for r in rows}
    if set(TRIGGERS)!=known or len(rows)!=14 or not all(
        all(isinstance(x,str) and len(x)>=5 for x in terms)
        for terms in TRIGGERS.values()):
        raise CrossvideoGuardError("CROSSVIDEO_TRIGGER_REGISTRY_NOT_FROZEN")
    if source["new_active_p4_nodes"]!=0 or source[
        "source_anchored_crossvideo_risk_challenges"]!=14:
        raise CrossvideoGuardError("CROSSVIDEO_FORMAL_PROMOTION_FORBIDDEN")
    return {"schema":"IRE_V5_CROSSVIDEO_14_RISK_QUARANTINE_V1",
            "scoped_risk_cases":14,"extra_videos":5,
            "new_education_nodes_from_unverified_videos":0,
            "formal_financial_facts_approved":0,
            "personal_investment_action_authorized":False}


def retrieve(root:Path,question:str,*,max_items:int=3):
    verify(root)
    if not isinstance(question,str) or not question.strip():
        raise CrossvideoGuardError("CROSSVIDEO_EMPTY_QUESTION")
    if type(max_items) is not int or not 1<=max_items<=14:
        raise CrossvideoGuardError("CROSSVIDEO_BAD_LIMIT")
    matched=[]
    q=question.casefold().replace(" ","")
    for row in read_source(Path(root))["risk_challenges"]:
        if any(term.casefold().replace(" ","") in q
               for term in TRIGGERS[row["case_id"]]):
            matched.append({
              "case_id":row["case_id"],"video_no":row["video_no"],
              "cue_range":row["cues"],"status":row["status"],
              "caveat":row["resolution"],
              "reference_id":row.get("reference"),
              "verified_new_financial_fact":False,
            })
    return {"schema":"IRE_V5_CROSSVIDEO_SCOPED_CAUTION_RETRIEVAL_V1",
            "items":matched[:max_items],"match_count":len(matched[:max_items]),
            "release":"QUARANTINED_RISK_CONTEXT_NOT_VERIFIED_FINANCIAL_FACT",
            "positive_legal_or_product_approval":False}


def audit(root:Path):
    v=verify(root)
    cases={
        "자녀에게 2천만원 증여하면 자동으로 비과세인가요?":"CV-006-GIFT-2000",
        "30년 증여 비과세 2.4억이 누구에게나 가능한가요?":"CV-006-GIFT-240M",
        "엔화 10% 수익을 확정할 수 있나요?":"CV-009-YEN-10PCT",
        "세액공제 안받아도 무조건 연금저축이 유리한가요?":
            "CV-010-PENSION-ALL-BETTER",
        "세액공제 안 받은 원금 언제든 출금 가능한가요?":
            "CV-010-WITHDRAW-ANYTIME",
    }
    for q,expected in cases.items():
        actual={x["case_id"] for x in retrieve(root,q)["items"]}
        if expected not in actual:
            raise CrossvideoGuardError("CROSSVIDEO_QUARANTINE_NOT_RETRIEVABLE")
    if retrieve(root,"영화관 주차권 안내")["match_count"]:
        raise CrossvideoGuardError("CROSSVIDEO_UNRELATED_FALSE_POSITIVE")
    v["live_risk_questions_checked"]=len(cases)
    return v


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--question")
    a=p.parse_args()
    d=retrieve(a.root,a.question) if a.question else audit(a.root)
    print(json.dumps(d,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
