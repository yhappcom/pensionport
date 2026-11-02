"""Source-only semantic omission risk audit for IRE V3.

This deterministic module does not interpret truth, infer missing claims, or
certify completeness. It flags high-signal financial nonclaim dispositions and
numeric atomization defects before storing immutable chat checkpoints.
Context/compound warnings are retained for later manual/model review.
"""
from __future__ import annotations

import re
from .source import require, text_norm
from .v3_semantic_candidates import financial_concepts

# Percent and currency tokens with no word boundary assumption in Korean.
MONEY_OR_RATE = re.compile(
    r"(?<![A-Za-z0-9])\d[\d,.]*\s*(?:%|퍼센트|"
    r"억\s*원|만\s*원|천\s*원|조\s*원|원|bp|bps)",
    re.IGNORECASE)
FINANCE = re.compile(
    r"isa|irp|etf|tdf|연금|퇴직|비과세|과세|세액|세금|"
    r"금리|수익률|수수료|이자|배당|매수|매도|주식|채권|"
    r"계좌|은행|증권|투자|금시장|대출|납입|상환|"
    r"월급|소득|자산배분|적립식|원금", re.IGNORECASE)
RULE = re.compile(
    r"세액\s*공제|비과세|과세\s*이연|납입\s*한도|"
    r"연금\s*개시|중도\s*인출|연금\s*수령\s*요건")
RULE_ASSERTION = re.compile(
    r"가능|적용|됩니다|된다|해야|의무|면제|받을\s*수|"
    r"수령|공제|과세|없다|않는다|늘어난|줄어든")
JOINERS = re.compile(r"하지만|반면|그러나|동시에|한편|또한|그리고|반대로")
NUMERIC_KIND = re.compile(r"\d[\d,.]*\s*(?:%|퍼센트|원)")

# Conservatively check that the *claim's own citations* contain the
# financial-specific information it asserts. Halo cues do not prove a claim.
# This prevents the two observed real-source W00003 failure modes without
# pretending to be a complete Korean-language semantic entailment model.
PERIODICITY = {
    "MONTHLY": re.compile(r"매\s*(?:월|달)|(?:한\s*)?달\s*(?:마다|에)|월\s*(?:별|마다|단위|수령|지급|연금|\d[\d,.]*\s*(?:만\s*원|억\s*원|원|까지|정도|씩|쯤|$))"),
    "ANNUAL": re.compile(r"매\s*년|매\s*해|연\s*(?:간|의\s*수익률|단위)|년\s*(?:마다|별)"),
}
PRODUCT_TERMS = {
    # Transcription ASR often confuses 저/제; this remains a review hint, not
    # a verified external financial term normalization.
    "연금저축": (r"연금\s*[저제]\s*축",),
    "국민연금": (r"국민\s*연금",),
    "퇴직연금": (r"퇴직\s*연금",),
    "IRP": (r"(?<![A-Za-z])IRP(?![A-Za-z])", r"개인형\s*퇴직\s*연금"),
    "ISA": (r"(?<![A-Za-z])ISA(?![A-Za-z])", r"개인\s*종합\s*자산\s*관리\s*계좌"),
    "ETF": (r"(?<![A-Za-z])ETF(?![A-Za-z])", r"상장\s*지수\s*펀드"),
}


def _unsupported_specificity(proposition: str, cited: str,
                             surrounding: str) -> list[tuple[str, bool]]:
    """Return (coded risk, hard failure?) based on source-side certainty.

    Contextual ellipsis and caption typos are warnings. A newly invented
    payment frequency with no support in the *current* source packet is a
    hard error. A narrower pension product substituted for a quoted generic
    pension is a hard error; other unnamed products require human review.
    Neither category proves full Korean semantic entailment.
    """
    issues = []
    for period, pattern in PERIODICITY.items():
        if not pattern.search(proposition) or pattern.search(cited):
            continue
        direct_context = pattern.search(surrounding) is not None
        # A source saying "맞추기/앞서/비교" is explicitly referring back
        # to a previously described case; flag it for human review rather
        # than silently forbidding legitimate cumulative source context.
        prior_case_reference = re.search(
            r"맞추|앞\s*서|앞선|비교|대조", cited) is not None
        issues.append(("UNSUPPORTED_" + period + "_SOURCE_UNIT",
                       period == "MONTHLY" and not direct_context and
                       not prior_case_reference))
    for product, aliases in PRODUCT_TERMS.items():
        if not any(re.search(p, proposition, re.I) for p in aliases):
            continue
        if any(re.search(p, cited, re.I) for p in aliases):
            continue
        # A source quote explicitly saying "개인연금" is not sufficient
        # evidence for the much narrower "연금저축" tax-account type.
        narrow_mismatch = (product == "연금저축" and
                           re.search(r"개인\s*연금", cited) is not None)
        issues.append(("UNSUPPORTED_SPECIFIC_PRODUCT_" + product,
                       narrow_mismatch))
    return issues


def _risk_for_nonclaim(text: str, neighbor_text: str) -> str | None:
    if MONEY_OR_RATE.search(text) and FINANCE.search(text):
        return "HIGH_SIGNAL_FINANCIAL_NUMERIC_NONCLAIM"
    if RULE.search(text) and RULE_ASSERTION.search(text):
        return "HIGH_SIGNAL_FINANCIAL_RULE_NONCLAIM"
    if MONEY_OR_RATE.search(text) and FINANCE.search(neighbor_text):
        return "CONTEXTUAL_FINANCIAL_NUMERIC_NONCLAIM"
    return None


def window_semantic_audit(packet: dict, response: dict) -> dict:
    """Report only coded IDs, not private source/claim text."""
    require(type(packet) is dict and
            type(packet.get("primary_cues")) is list and
            type(response) is dict and
            type(response.get("cue_dispositions")) is list and
            type(response.get("claims")) is list,
            "V3_SEMANTIC_AUDIT_INPUT_INVALID")
    cues = packet["primary_cues"]
    rows = response["cue_dispositions"]
    require(len(cues) == len(rows), "V3_SEMANTIC_AUDIT_CENSUS_INVALID")
    ordered = [c["cue_index"] for c in cues]
    require(ordered == [r["cue_index"] for r in rows],
            "V3_SEMANTIC_AUDIT_CUE_ORDER_MISMATCH")
    neighbor_text = " ".join(
        c["text"] for c in
        (packet.get("left_context_cues") or []) +
        (packet.get("right_context_cues") or []) + cues)
    critical = []
    warnings = []
    if packet.get("continuation_boundary_review_required") is True:
        warnings.append({
            "cue_index": cues[-1]["cue_index"],
            "code": "FORCED_WINDOW_BOUNDARY_SEMANTIC_REVIEW"
        })
    for cue, row in zip(cues, rows):
        if row["status"] != "NONCLAIM_CANDIDATE":
            continue
        kind = _risk_for_nonclaim(cue["text"], neighbor_text)
        if kind is None:
            continue
        issue = {"cue_index": cue["cue_index"], "code": kind}
        (critical if kind.startswith("HIGH_SIGNAL") else warnings).append(issue)
    for n, claim in enumerate(response["claims"], 1):
        frame = claim["frame"]
        quoted = " ".join(r["quote"] for r in claim["source_refs"])
        if ("NUMERIC" in claim["claim_types"] and
                NUMERIC_KIND.search(quoted) and not frame["measurements"]):
            critical.append({
                "claim_ordinal": n,
                "code": "NUMERIC_CLAIM_WITHOUT_MEASUREMENT_FRAME"
            })
        # A full primary/left context can explain an ellipsis, but is not an
        # exact quote. Preserve a coded review warning instead of auto-pass.
        prior_context = " ".join(
            c["text"] for c in (packet.get("left_context_cues") or []) + cues)
        for issue, blocking in _unsupported_specificity(
                claim["proposition"], quoted, prior_context):
            (critical if blocking else warnings).append({
                "claim_ordinal": n,
                "code": issue,
            })
        concepts = financial_concepts(claim["proposition"] + " " + quoted)
        if JOINERS.search(claim["proposition"]) and (
                len(concepts) >= 2 or
                len(NUMERIC_KIND.findall(quoted)) >= 2):
            warnings.append({
                "claim_ordinal": n,
                "code": "POSSIBLE_COMPOUND_FINANCIAL_ATOM"
            })
    return {
        "schema": "IRE_V3_WINDOW_SEMANTIC_RISK_AUDIT",
        "video_id": packet["video_id"],
        "window_id": packet["window_id"],
        "critical": critical,
        "warnings": warnings,
        "financial_truth_certified": False,
        "atomization_completeness_certified": False,
    }


def review_clusters(rows: list[dict]) -> list[dict]:
    """Adaptively group *existing* immutable V2 primary windows for review.

    This changes only packet presentation hints, never V2 source ownership,
    window SHA, cue IDs, claim reference rules, or stored checkpoints.
    """
    require(type(rows) is list, "V3_REVIEW_CLUSTER_INPUT_INVALID")
    clusters = []
    active = []
    concepts = frozenset()
    prev_end = None
    prev_video = None
    for entry in rows:
        packet = entry["packet"]
        primary = packet["primary_cues"]
        require(primary, "V3_REVIEW_CLUSTER_EMPTY_PACKET")
        video = entry["video_id"]
        start = primary[0]["start_ms"]
        end = primary[-1]["end_ms"]
        now = financial_concepts(" ".join(c["text"] for c in primary))
        close = (active and video == prev_video and
                 prev_end is not None and
                 0 <= start - prev_end <= 3000 and
                 bool(concepts & now) and len(active) < 3)
        if active and not close:
            clusters.append({
                "video_id": prev_video,
                "window_ids": active,
                "hint": "PRESERVE_INDIVIDUAL_WINDOW_ANSWER_IDENTITIES",
            })
            active = []
            concepts = frozenset()
        active.append(packet["window_id"])
        concepts = concepts | now
        prev_end = end
        prev_video = video
    if active:
        clusters.append({
            "video_id": prev_video, "window_ids": active,
            "hint": "PRESERVE_INDIVIDUAL_WINDOW_ANSWER_IDENTITIES",
        })
    return clusters