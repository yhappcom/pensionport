"""Policy gate: user accepts only source-matched facts researched in this chat.

Independent human/AI blind adjudication is optional and NOT a release gate.
This gate enforces provenance, narrow fact boundaries, and safe temporal use;
it does NOT itself fetch/evaluate an official page or prove the web claim true.
Those source/content judgments must have been made in the active ChatGPT turn.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

POLICY = Path("ire/v5/new_video_studies/WIXWPJjhF50_CHAT_EVIDENCE_FACT_ACCEPTANCE_20261105.json")
OVERLAY = Path("ire/v5/new_video_studies/WIXWPJjhF50_SEMANTIC_EVIDENCE_RECHECK_20261105.json")
POSITIVE = frozenset({
    "ACCEPTED_FACT", "ACCEPTED_HISTORICAL_FACT",
    "ACCEPTED_CORRECTED_FACT", "PARTIALLY_ACCEPTED_FACT",
})
NON_FACT = frozenset({"CONTEXT_ONLY", "UNVERIFIED", "HYPOTHESIS_UNVERIFIED"})
REQUIRED = frozenset({
    "original_source_anchor",
    "reliable_evidence_content_directly_supports_specific_fact",
    "jurisdiction_and_product_scope",
    "effective_date_and_as_of_date",
    "numeric_arithmetic_if_present",
    "known_contradictions_and_open_fragments",
    "fact_version_and_citation_provenance",
})
MUST_NOT_PROMOTE = frozenset({
    "S232-08", "S232-11", "S232-12", "S232-15",
    "S232-16", "S232-19", "S232-21", "S232-22",
})
MUST_CORRECT = frozenset({"S232-03", "S232-04", "S232-06", "S232-14", "S232-20"})


class AcceptanceGateError(ValueError):
    pass


def _require(valid: bool, reason: str) -> None:
    if not valid:
        raise AcceptanceGateError(reason)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(root: Path, policy: dict | None = None) -> dict:
    root = Path(root)
    p = _read(root / POLICY) if policy is None else policy
    overlay = _read(root / OVERLAY)
    _require(
        p.get("schema") == "IRE_V5_CHAT_EVIDENCE_FACT_ACCEPTANCE_V1"
        and p.get("policy_owner") == "USER_APPROVED_CURRENT_CHAT_EVIDENCE_ONLY"
        and p.get("independent_human_blind_evaluation_required") is False
        and p.get("independent_ai_blind_evaluation_required") is False
        and p.get("independent_human_blind_completed") is False
        and p.get("formal_external_financial_certification") is False
        and p.get("external_model_api_required") is False
        and p.get("subsequent_live_financial_action_requires_recheck") is True
        and p.get("not_automatically_authorized")
        == "PERSONALIZED_INVESTMENT_ADVICE_OR_REAL_TIME_TRADE_ORDER"
        and p.get("permitted_use")
        == "SOURCE_SCOPED_EDUCATIONAL_AND_FACT_RETRIEVAL_ONLY"
        and p.get("verification_basis")
        == "ACTIVE_CHAT_PRIMARY_OFFICIAL_OR_RELIABLE_CONTEMPORANEOUS_SEARCH_AND_CLAIM_SOURCE_MEANING_MATCH"
        and set(p.get("mandatory_checks", [])) == REQUIRED
        and "link_presence_alone" in p.get("never_approve_from", [])
        and "mere_ci_pass" in p.get("never_approve_from", []),
        "EVIDENCE_POLICY_MUST_BE_CLAIM_AND_SOURCE_SCOPED_NOT_BLIND_REQUIRED",
    )
    today = date.fromisoformat(p["reviewed_fact_date"])
    _require(
        p.get("policy_date") == p["reviewed_fact_date"] == "2026-11-05"
        and p.get("parent_source_video_id") == overlay["video_id"] == "WIXWPJjhF50"
        and p.get("semantic_overlay_path") == str(OVERLAY)
        and p.get("original_srt_sha256") == overlay["original_srt_sha256"]
        and p.get("release_result") == "FACTS_IN_ACCEPTED_SCOPE_ONLY_AND_ALL_UNSUPPORTED_FRAGMENTS_OPEN",
        "EVIDENCE_BASELINE_AND_SOURCE_INTEGRITY_MISMATCH",
    )
    refs = {x["id"]: x for x in overlay["external_references"]}
    semantic = {x["analysis_id"]: x for x in overlay["semantic_assertions"]}
    rows = p.get("claims", [])
    _require(len(rows) == len(semantic) == 22 and
             {x.get("claim_id") for x in rows} == set(semantic),
             "EVIDENCE_EACH_ATOMIC_CLAIM_MUST_BE_DISPOSITIONED_ONCE")
    counts: Counter[str] = Counter()
    for row in rows:
        claim_id = row["claim_id"]
        verdict = row["verdict"]
        counts[verdict] += 1
        _require(verdict in (POSITIVE | NON_FACT)
                 and row.get("evidence_verified_as_of") == "2026-11-05"
                 and row.get("external_blind_review") is False
                 and row.get("personal_advice_approved") is False
                 and len(row.get("source_to_claim_match", "")) >= 34
                 and len(row.get("temporal_scope", "")) >= 8,
                 "EVIDENCE_SCOPE_OR_APPROVAL_UNSAFE")
        ids = row.get("source_ids", [])
        _require(isinstance(ids, list)
                 and len(set(ids)) == len(ids)
                 and set(ids) <= set(refs)
                 and set(ids) <= set(semantic[claim_id]["source_ids"]),
                 "EVIDENCE_FACT_CITATION_NOT_LINKED_TO_ORIGINAL_RESEARCH")
        if verdict in POSITIVE:
            fact = row.get("accepted_fact")
            _require(isinstance(fact, str)
                     and len(fact) >= 38
                     and len(ids) > 0,
                     "EVIDENCE_FACT_CANNOT_PASS_WITH_LINK_ALONE_OR_NO_CLAIM")
            if verdict == "PARTIALLY_ACCEPTED_FACT":
                _require(len(row.get("narrow_exclusion", "")) >= 22,
                         "EVIDENCE_PARTIAL_SCOPE_MUST_REMAIN_OPEN")
            if row["temporal_scope"] == "CURRENT_RULE":
                _require(any(refs[i]["kind"].startswith("OFFICIAL")
                             for i in ids), "EVIDENCE_CURRENT_REGULATION_NEEDS_PRIMARY_SOURCE")
            if row["temporal_scope"] == "HISTORICAL_MARKET_PRICE":
                _require(any(refs[i]["kind"] == "CONTEMPORANEOUS_SECONDARY"
                             for i in ids),
                         "EVIDENCE_HISTORICAL_PRICE_PROVENANCE_UNDISCLOSED")
        else:
            _require(row.get("accepted_fact") is None and not ids
                     and not row.get("narrow_exclusion"),
                     "EVIDENCE_UNVERIFIED_FACT_INCORRECTLY_RELEASED")
        if claim_id in MUST_NOT_PROMOTE:
            _require(verdict in NON_FACT, "EVIDENCE_UNPROVEN_OR_ADVICE_PROMOTED")
        if claim_id in MUST_CORRECT:
            _require(verdict == "ACCEPTED_CORRECTED_FACT",
                     "EVIDENCE_CRITICAL_CORRECTION_LOST")
    by_id = {x["claim_id"]: x for x in rows}
    _require(
        "160%" in by_id["S232-03"]["accepted_fact"]
        and "63%" in by_id["S232-04"]["accepted_fact"]
        and "2023-06-26" in by_id["S232-06"]["accepted_fact"]
        and "+300%" in by_id["S232-06"]["accepted_fact"]
        and "종가" in by_id["S232-14"]["accepted_fact"]
        and "시가총액" in by_id["S232-20"]["accepted_fact"]
        and by_id["S232-10"]["verdict"] == "PARTIALLY_ACCEPTED_FACT"
        and "영상" in by_id["S232-10"]["narrow_exclusion"]
        and by_id["S232-09"]["verdict"] == "PARTIALLY_ACCEPTED_FACT"
        and by_id["S232-13"]["verdict"] == "PARTIALLY_ACCEPTED_FACT",
        "EVIDENCE_2023_RULE_OR_PRICE_CORRECTION_NOT_PROTECTED",
    )
    context = p.get("future_context_facts", [])
    _require(
        len(context) == 1
        and context[0].get("id") == "FUTURE-IPO-20261113"
        and context[0].get("status") == "APPROVED_NOT_YET_EFFECTIVE"
        and date.fromisoformat(context[0]["effective_on"]) > today
        and context[0]["effective_on"] == "2026-11-13"
        and context[0].get("not_equal_to") == "IPO-2023-FIRST-DAY"
        and set(context[0].get("source_ids", [])) == {"FSC-IPO-NOV26"}
        and context[0]["as_of"] == "2026-11-05",
        "EVIDENCE_FUTURE_RULE_PREMATURELY_TREATED_AS_CURRENT",
    )
    return {
        "schema": "IRE_V5_CHAT_EVIDENCE_FACT_ACCEPTANCE_GATE_V1",
        "video_id": p["parent_source_video_id"],
        "atomic_claims_adjudicated": len(rows),
        "fully_accepted_facts": sum(v for k, v in counts.items()
                                    if k in POSITIVE - {"PARTIALLY_ACCEPTED_FACT"}),
        "narrowly_accepted_partial_facts": counts["PARTIALLY_ACCEPTED_FACT"],
        "not_accepted_as_facts": sum(v for k, v in counts.items() if k in NON_FACT),
        "independent_blind_review_required": False,
        "claims_have_source_to_fact_scope": True,
        "online_sources_reopened_by_ci": False,
        "real_personalized_investment_advice_approved": False,
        "research_fact_use": "EVIDENCE_SCOPED_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(verify(args.root), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
