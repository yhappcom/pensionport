"""Conservative Korean financial-term expansion for *candidate retrieval*.

No model, training data, historical research, embeddings, or factual labels are
loaded. These hand-written financial vocabulary aliases improve discovery only.
They are not a proof of semantic equivalence, contradictoriness or truth.
"""
from __future__ import annotations

import re

# High-specificity domain aliases. Generic words such as "투자", "연금",
# "세금" are deliberately excluded to reduce broad false associations.
PATTERNS = {
    "ACCOUNT_IRP": r"(?<![a-z])irp(?![a-z])|개인형\s*퇴직연금",
    "ACCOUNT_ISA": r"(?<![a-z])isa(?![a-z])|개인종합자산관리계좌",
    "PENSION_SAVINGS": r"연금저축",
    "NATIONAL_PENSION": r"국민연금",
    "RETIREMENT_BENEFIT": r"퇴직금|퇴직급여",
    "ETF": r"(?<![a-z])etf(?![a-z])|상장\s*지수\s*펀드",
    "KRX_GOLD": r"(?:krx|한국거래소|거래소)\s*금시장|금\s*현물\s*(?:시장|거래)",
    "TRADING_GAIN": r"매매\s*차익|매도\s*이익|거래\s*이익|양도\s*차익",
    "TAX_EXEMPT": r"비과세|세금\s*(?:없|안\s*붙|붙지\s*않)|과세하지\s*않",
    "TAX_DEFERRAL": r"과세\s*이연|세금(?:을|의)?\s*(?:나중에|뒤로)\s*(?:내|미루)",
    "INSTALLMENT_BUY": r"적립식\s*투자|분할\s*매수|분할\s*투자|정액\s*매수|매월\s*일정\s*금액",
    "PERIODIC_AUTO_BUY": r"자동\s*매수|정기\s*매수|매월\s*매수",
    "REBALANCE": r"리밸런싱|비중\s*(?:조정|재조정)|자산\s*재배분",
    "TDF": r"(?<![a-z])tdf(?![a-z])|타(?:깃|겟)\s*데이트\s*펀드",
    "PENSION_DEFERRAL": r"연기\s*연금|국민연금\s*(?:수령\s*)?연기|연금\s*수령\s*연기",
}
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}


def financial_concepts(text: str) -> frozenset[str]:
    if not isinstance(text, str) or not text:
        return frozenset()
    lowered = text.lower()
    return frozenset(key for key, pattern in COMPILED.items()
                     if pattern.search(lowered))


def _claim_text(atom: dict) -> str:
    frame = atom.get("frame") or {}
    parts = [atom.get("proposition") or ""]
    for key in ("product", "financial_event", "action", "object"):
        value = frame.get(key)
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts)


def claim_concepts(atom: dict) -> frozenset[str]:
    return financial_concepts(_claim_text(atom))


def semantic_candidate_score(left: dict, right: dict) -> float:
    """Additive score floor when multiple specific concepts overlap.

    A zero means no controlled-alias signal, *not* unrelated claims.
    At least two distinct specific concepts must match. Negation, exceptions,
    dates and numeric differences are NOT collapsed by this method.
    """
    common = claim_concepts(left) & claim_concepts(right)
    if len(common) < 2:
        return 0.0
    return round(min(0.87, 0.54 + 0.07 * (len(common) - 2)), 5)


def advisory_concept_overlap(question: str, atom: dict) -> int:
    """Supplement lexical retrieval; every hit remains unverified."""
    return len(financial_concepts(question) & claim_concepts(atom))
