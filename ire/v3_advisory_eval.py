"""Question-level V3 P2 advisory safety and citation benchmark.

Manual source-first scenario judgments are required, not fabricated by the
current chat. These measurements prove only what submitted scenarios exercise;
reviewer identity/blindness and real-world legal/financial validity remain
unverified until an external process attests them.
"""
from __future__ import annotations

import json
import os
import re

from .knowledge import validate_knowledge
from .v2_evidence import validate_evidence_ledger
from .v3_relation_review import validate_relation_reviews
from .v3_advisory import build_advisory_dossier
from .checkpoint import safe_private_directory
from .cli import private_file
from .source import sha256,require,text_norm

SCHEMA="IRE_V3_ADVISORY_BLIND_CASES_V1"


def _canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def evaluate_advisory_cases(knowledge,evidence,scenarios,relations=None):
    validate_knowledge(knowledge)
    validate_evidence_ledger(evidence,knowledge)
    if relations is not None:
        validate_relation_reviews(relations,knowledge)
    require(type(scenarios) is dict and set(scenarios)=={
        "schema","knowledge_snapshot_sha256","evidence_snapshot_sha256",
        "relation_snapshot_sha256","source_first_manual_scenarios",
        "model_outputs_hidden_during_adjudication","reviewers",
        "adjudicator_id","cases"
    } and scenarios["schema"]==SCHEMA and
            scenarios["knowledge_snapshot_sha256"]==knowledge["snapshot_sha256"] and
            scenarios["evidence_snapshot_sha256"]==evidence["snapshot_sha256"] and
            scenarios["relation_snapshot_sha256"]==
                (relations["snapshot_sha256"] if relations else None) and
            scenarios["source_first_manual_scenarios"] is True and
            scenarios["model_outputs_hidden_during_adjudication"] is True,
            "V3_ADVISORY_GOLD_SCHEMA_OR_SOURCE_MISMATCH")
    reviewers=scenarios["reviewers"]
    require(type(reviewers) is list and len(reviewers)==2 and
            all(type(r) is dict and set(r)=={"reviewer_id","source_first_sha256"} and
                type(r["reviewer_id"]) is str and
                re.fullmatch(r"[A-Za-z0-9_-]{3,48}",r["reviewer_id"]) and
                type(r["source_first_sha256"]) is str and
                re.fullmatch(r"[0-9a-f]{64}",r["source_first_sha256"])
                for r in reviewers),"V3_ADVISORY_GOLD_REVIEWER_SCHEMA_INVALID")
    reviewers_ids={r["reviewer_id"] for r in reviewers}
    require(len(reviewers_ids)==2 and type(scenarios["adjudicator_id"]) is str and
            re.fullmatch(r"[A-Za-z0-9_-]{3,48}",scenarios["adjudicator_id"]) and
            scenarios["adjudicator_id"] not in reviewers_ids,
            "V3_ADVISORY_GOLD_REVIEWERS_NOT_INDEPENDENT")
    cases=scenarios["cases"]
    require(type(cases) is list and 1<=len(cases)<=2000,
            "V3_ADVISORY_GOLD_CASE_COUNT_INVALID")
    claims={x["global_claim_id"]:x for x in knowledge["claims"]}
    ids=set()
    totals={"unsafe_recommendation_releases":0,"required_blocker_misses":0,
            "expected_citation_hits":0,"expected_citation_total":0,
            "false_verified_claim_assertions":0,"official_freshness_gate_errors":0}
    results=[]
    for case in cases:
        require(type(case) is dict and set(case)=={
            "case_id","question","as_of","jurisdiction","investor_profile",
            "expected_blockers","expected_relevant_source_quotes",
            "must_not_release_advice"
        } and type(case["case_id"]) is str and
                re.fullmatch(r"A[0-9]{4,8}",case["case_id"]) and
                case["case_id"] not in ids and
                type(case["expected_blockers"]) is list and
                len(set(case["expected_blockers"]))==len(case["expected_blockers"]) and
                all(type(x) is str and 5<=len(x)<=128
                    for x in case["expected_blockers"]) and
                type(case["expected_relevant_source_quotes"]) is list and
                case["must_not_release_advice"] is True,
                "V3_ADVISORY_GOLD_CASE_INVALID")
        ids.add(case["case_id"])
        expected=set()
        for source in case["expected_relevant_source_quotes"]:
            require(type(source) is dict and set(source)=={
                "global_claim_id","original_source_quote"} and
                source["global_claim_id"] in claims and
                source["global_claim_id"] not in expected and
                type(source["original_source_quote"]) is str and
                any(text_norm(source["original_source_quote"]) in
                    text_norm(ref["quote"]) for ref in
                    claims[source["global_claim_id"]]["source_refs"]),
                "V3_ADVISORY_GOLD_QUOTE_OR_CLAIM_INVALID")
            expected.add(source["global_claim_id"])
        dossier=build_advisory_dossier(
            knowledge,evidence,case["question"],case["as_of"],
            case["jurisdiction"],case["investor_profile"],relations)
        actual={x["global_claim_id"] for x in dossier["claim_dossiers"]}
        hits=expected&actual
        missing=set(case["expected_blockers"])-set(dossier["unresolved_advisory_requirements"])
        unsafe=bool(dossier["actionable_recommendations"]) or dossier["individualized_advice_released"]
        false_verified=any(x["can_support_individual_investment_recommendation"]
                           for x in dossier["claim_dossiers"])
        freshness_errors=sum(
            r["source_corroboration_candidate_only"] and
            (not r["official_capture_fresh_on_question_date"] or
             not r["declared_effective_date_covers_question"] or
             not r["declared_scope_all_matches"])
            for x in dossier["claim_dossiers"] for r in x["document_assessments"])
        totals["unsafe_recommendation_releases"]+=bool(unsafe)
        totals["required_blocker_misses"]+=len(missing)
        totals["expected_citation_hits"]+=len(hits)
        totals["expected_citation_total"]+=len(expected)
        totals["false_verified_claim_assertions"]+=bool(false_verified)
        totals["official_freshness_gate_errors"]+=freshness_errors
        results.append({
            "case_id":case["case_id"],
            "source_quote_recall":round(len(hits)/len(expected),6) if expected else None,
            "expected_citations":len(expected),"retrieved_expected_citations":len(hits),
            "required_blockers_missed":sorted(missing),
            "unsafe_investment_advice_issued":bool(unsafe),
            "false_verified_claim_assertion":bool(false_verified),
            "official_freshness_gate_errors":freshness_errors,
        })
    return {
        "schema":"IRE_V3_ADVISORY_SAFETY_EVALUATION_V1",
        "scenarios_sha256":sha256(_canonical(scenarios)),
        "knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
        "scenario_count":len(cases),"results":results,
        **totals,
        "micro_source_quote_recall":round(
            totals["expected_citation_hits"]/totals["expected_citation_total"],6)
            if totals["expected_citation_total"] else None,
        "independent_reviewer_identities_certified":False,
        "gold_scenarios_genuinely_blinded_certified":False,
        "actual_investment_advice_quality_certified":False,
        "release_approved":False,
    }


def main():
    import argparse
    from .knowledge import read_private_snapshot
    parser=argparse.ArgumentParser(description="V3 advisory safety scenario evaluation")
    parser.add_argument("operation",choices=["evaluate"])
    parser.add_argument("--private-knowledge-snapshot",required=True)
    parser.add_argument("--private-evidence-ledger",required=True)
    parser.add_argument("--private-relation-ledger")
    parser.add_argument("--private-gold-cases",required=True)
    parser.add_argument("--private-report-dir",required=True)
    args=parser.parse_args()
    try:
        knowledge=read_private_snapshot(args.private_knowledge_snapshot)
        def read(filename):
            return json.loads(private_file(filename).read_text(encoding="utf-8")) if filename else None
        report=evaluate_advisory_cases(
            knowledge,read(args.private_evidence_ledger),
            read(args.private_gold_cases),read(args.private_relation_ledger))
        encoded=_canonical(report)
        digest=sha256(encoded)
        directory=safe_private_directory(args.private_report_dir)
        target=directory/("ire_v3_advisory_eval_"+digest[:24]+".json")
        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,"wb") as stream:
                stream.write(encoded);stream.flush();os.fsync(stream.fileno())
        except Exception:
            target.unlink(missing_ok=True)
            raise
        print(json.dumps({"schema":report["schema"],
                          "scenario_count":report["scenario_count"],
                          "unsafe_recommendation_releases":report["unsafe_recommendation_releases"],
                          "report_sha256":digest,"private_report_path":str(target),
                          "actual_investment_advice_quality_certified":False},sort_keys=True))
        return 2
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        print(json.dumps({"schema":"IRE_V3_ADVISORY_EVALUATION_ERROR",
                          "status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())