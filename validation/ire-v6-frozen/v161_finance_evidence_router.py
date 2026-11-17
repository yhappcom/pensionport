"""V161 finance evidence work queues, NOT legal or factual approval.

The financial_claim flag and original V123 OPEN verdict remain unchanged.
Routing based on source-anchored strings only nominates evidence to collect.
Every category needs source-first ChatGPT review before any approval.
"""
from __future__ import annotations

import re
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput

AUDIO_SUSPECT = frozenset({307,390,522,622,717,797,849,850,852,943,947,965,1221})
LAW = re.compile(r"세법|세금|과세|절세|공제|소득세|ISA|IRP|국민연금|연금저축|퇴직연금|금융소득|조세|시행령|법령|금융감독원", re.I)
ISSUER = re.compile(r"삼성전자|하이닉스|SK하이닉스|SK 하이닉스|LG전자|LG반도체|인텔|HBM|디램|D램|DRAM|낸드|반도체|메모리|빅테크|엔비디아", re.I)
PUBLISHER = re.compile(r"파브라이|단도|파텔|모텔|버핏|책|도서|저자|출판|번역서|원제|구자라트|호텔", re.I)
NUMERICAL = re.compile(r"\d[\d,.]*\s*(?:%|원|만원|억원|조원|배|달러)|수익률|점유율|자산 규모|수치|가격", re.I)
EXPERIENCE = re.compile(r"회고|회상|직접 경험|당시|나의|자신의|제가|저는|유튜브 시작|촬영|마이크|장비|퇴사", re.I)

CLASSIFICATIONS = {
    "SOURCE_AUDIO_RECHECK": "원음·공식 1차 자료 확보 및 부정어/발화 귀속 검증",
    "CURRENT_LAW_EFFECTIVE_SCOPE": "현행 조세·금융규정 본문 바이트·시행일·적용범위 확인",
    "CORPORATE_ISSUER_FACT": "기업 공시/IR 원문·사건일·통계 시점 검증",
    "BOOK_OR_HISTORICAL_SOURCE": "출판사/원저자/역사 사료와 실제 인용 구분",
    "NUMERIC_ASSUMPTION_OR_EXTERNAL_FACT": "숫자·단위·가정/실적·세전/세후·산술 검증",
    "PERSONAL_RECOLLECTION": "원문에서의 회고·거래/장비비용 실제 사실 구분",
    "GENERAL_INVESTMENT_MEANING": "금융 의견·조언·가정·위험과 반박 의미 검문",
}


def triage_finance_open_claim(source, atom, verdict):
    """Return source-bound, nonauthoritative evidence work-queue ticket."""
    if (verdict.get("claim_id") != atom.get("claim_id") or
        verdict.get("atom_sha256") != json_digest(atom)):
        raise InvalidInput("V161_TRIAGE_SOURCE_ATOM_DIGEST_DRIFT")
    if verdict.get("status") != "OPEN" or verdict.get("financial_claim") is not True:
        raise InvalidInput("V161_TRIAGE_ONLY_FINANCE_OPEN")
    indices = atom.get("context_cue_indices")
    if (type(indices) is not list or not indices or any(
        type(i) is not int or i < source.scope_first_cue or i > source.scope_last_cue
        for i in indices)):
        raise InvalidInput("V161_TRIAGE_SOURCE_CONTEXT_REQUIRED")
    text = atom["proposition"]
    disputed = sorted(AUDIO_SUSPECT.intersection(indices))
    if disputed:
        category = "SOURCE_AUDIO_RECHECK"
    elif LAW.search(text):
        category = "CURRENT_LAW_EFFECTIVE_SCOPE"
    elif ISSUER.search(text):
        category = "CORPORATE_ISSUER_FACT"
    elif PUBLISHER.search(text):
        category = "BOOK_OR_HISTORICAL_SOURCE"
    elif atom.get("numeric_references") or NUMERICAL.search(text):
        category = "NUMERIC_ASSUMPTION_OR_EXTERNAL_FACT"
    elif EXPERIENCE.search(text):
        category = "PERSONAL_RECOLLECTION"
    else:
        category = "GENERAL_INVESTMENT_MEANING"
    return {
        "claim_id": atom["claim_id"],
        "atom_sha256": json_digest(atom),
        "original_source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "source_context_sha256": json_digest([
            {"cue_index": i, "cue_text_sha256": sha256(source.cues[i-1].text.encode("utf-8"))}
            for i in sorted(set(indices))
        ]),
        "evidence_work_queue": category,
        "required_evidence": CLASSIFICATIONS[category],
        "original_audio_suspect_indices": disputed,
        "original_verdict_remains": "OPEN",
        "finance_evidence_approved": False,
        "ChatGPT_meaning_review_required": True,
        "current_rule_applicability_verified": False,
        "personal_advice_approved": False,
    }
