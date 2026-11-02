"""V3 P2 source-grounded advisory research dossier, NEVER auto trade advice.

Requires source-linked current knowledge and an evidence ledger; optional
separately sealed relation-review ledger. Records explicit suitability, legal
scope, freshness, contradiction and independent-review gates for every hit.
A chat model's own source assessment cannot grant investment-advice approval.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
import os

from .source import require,sha256
from .knowledge import validate_knowledge, advisory_research_context
from .v2_evidence import validate_evidence_ledger
from .v3_relation_review import validate_relation_reviews, relation_review_context
from .checkpoint import safe_private_directory
from .cli import private_file

PROFILE_FIELDS=("investment_horizon_years","risk_tolerance","tax_residency",
                "account_type","liquidity_needs")
RISK_VALUES=frozenset({"conservative","moderate","aggressive","low","high"})
MAX_FRESH_DAYS=90


def _date(s):
    require(type(s) is str and date.fromisoformat(s).isoformat()==s,
            "V3_ADVISORY_DATE_INVALID")
    return date.fromisoformat(s)


def _profile(profile):
    if profile is None:
        return PROFILE_FIELDS
    require(type(profile) is dict and set(profile)<=set(PROFILE_FIELDS),
            "V3_ADVISORY_PROFILE_SCHEMA_INVALID")
    for k,v in profile.items():
        if k=="investment_horizon_years":
            require(type(v) in (int,float) and 0<v<=100,
                    "V3_ADVISORY_HORIZON_INVALID")
        elif k=="risk_tolerance":
            require(type(v) is str and v in RISK_VALUES,"V3_ADVISORY_RISK_INVALID")
        else:
            require(type(v) is str and 1<=len(v.strip())<=128,
                    "V3_ADVISORY_PROFILE_FIELD_INVALID")
    return tuple(x for x in PROFILE_FIELDS if x not in profile)


def _fetch_date(row):
    stamp=row["fetched_at_utc"]
    try:
        result=datetime.fromisoformat(stamp.replace("Z","+00:00"))
        if result.tzinfo is None:
            return None
        return result.astimezone(timezone.utc).date()
    except (ValueError,AttributeError,TypeError):
        return None


def build_advisory_dossier(knowledge,evidence,question,as_of,
                           jurisdiction=None,investor_profile=None,
                           relations=None,top_k=8):
    validate_knowledge(knowledge)
    validate_evidence_ledger(evidence,knowledge)
    when=_date(as_of)
    missing=_profile(investor_profile)
    if relations is not None:
        validate_relation_reviews(relations,knowledge)
    context=advisory_research_context(
        knowledge,question,as_of,jurisdiction,investor_profile,top_k)
    hits=context["unverified_relevant_claims"]
    relevant_ids={x["global_claim_id"] for x in hits}
    evidences={key:[] for key in relevant_ids}
    for row in evidence["assessments"]:
        if row["global_claim_id"] in relevant_ids:
            evidences[row["global_claim_id"]].append(row)
    items=[]
    overall=[]
    for hit in hits:
        claim_id=hit["global_claim_id"]
        assessments=evidences[claim_id]
        cases=[]
        safe_candidates=0
        blockers=[]
        for row in assessments:
            fetched=_fetch_date(row)
            effective=(row["effective_from"] is not None and
                       row["effective_from"]<=as_of and
                       (row["effective_until"] is None or
                        as_of<=row["effective_until"]))
            fresh=(fetched is not None and fetched<=when and
                   (when-fetched).days<=MAX_FRESH_DAYS)
            scopes=all(x=="MATCH" for x in row["scope"].values())
            direct=row["actual_network_fetch"] is True
            cautious=(effective and fresh and scopes and direct and
                      row["verdict"]=="SUPPORTS")
            if cautious: safe_candidates+=1
            cases.append({
                "assessment_id":row["assessment_id"],
                "issuer_candidate_only":row["issuer_candidate"],
                "assessment_verdict_unverified":row["verdict"],
                "document_fetched_before_question": fetched is not None and fetched<=when,
                "official_capture_fresh_on_question_date":fresh,
                "declared_effective_date_covers_question":effective,
                "declared_scope_all_matches":scopes,
                "actual_network_fetched":direct,
                "source_corroboration_candidate_only":cautious,
                "independent_factual_truth_approved":False})
        if not assessments: blockers.append("NO_OFFICIAL_SOURCE_ASSESSMENT")
        if not any(c["actual_network_fetched"] for c in cases):
            blockers.append("NO_LIVE_OFFICIAL_SOURCE_CAPTURE")
        if not any(c["official_capture_fresh_on_question_date"] for c in cases):
            blockers.append("NO_FRESH_OFFICIAL_CAPTURE")
        if not any(c["declared_effective_date_covers_question"] for c in cases):
            blockers.append("EFFECTIVE_DATE_NOT_ESTABLISHED")
        if not any(c["declared_scope_all_matches"] for c in cases):
            blockers.append("SCOPE_CONDITIONS_OR_EXCEPTIONS_UNRESOLVED")
        if any(c["assessment_verdict_unverified"]=="CONTRADICTS" for c in cases):
            blockers.append("POSSIBLE_OFFICIAL_EVIDENCE_CONTRADICTION")
        if safe_candidates==0: blockers.append("NO_QUALIFYING_SUPPORT_CANDIDATE")
        blockers.append("SOURCE_CHAT_ASSESSMENT_NOT_INDEPENDENT_HUMAN_GOLD")
        items.append({
            "global_claim_id":claim_id,"original_video_id":hit["original_video_id"],
            "source_sha256":hit["original_source_sha256"],
            "cited_source_refs":hit["source_refs"],
            "proposition_unverified":hit["proposition_as_spoken_not_proven"],
            "document_assessments":cases,
            "source_corroboration_candidate_count":safe_candidates,
            "blockers":sorted(set(blockers)),
            "can_support_individual_investment_recommendation":False})
        overall.extend(blockers)
    if relations is not None:
        relation=relation_review_context(relations,knowledge,relevant_ids)
        relation_unreviewed=relation["unreviewed_relation_ids"]
        difference=[x["relation_id"] for x in relation["relevant_reviews"]
                    if x["relation_label"] in (
                        "POSSIBLE_CONTRADICTION","TEMPORAL_CHANGE",
                        "NUMERIC_DIFFERENCE","JURISDICTION_DIFFERENCE")]
    else:
        relation_unreviewed=[x["relation_id"] for x in
                            context["possible_cross_video_conflicts_or_updates"]]
        difference=[]
    if relation_unreviewed:
        overall.append("CROSS_VIDEO_RELATIONS_UNREVIEWED")
    if difference:
        overall.append("CROSS_VIDEO_CHANGE_OR_CONTRADICTION_NOT_INDEPENDENTLY_RESOLVED")
    if missing: overall.append("INVESTOR_SUITABILITY_PROFILE_INCOMPLETE")
    if not hits: overall.append("NO_RELEVANT_SOURCE_CLAIMS")
    overall.append("INDEPENDENT_CURRENT_REGULATORY_AND_HUMAN_ADJUDICATION_REQUIRED")
    return {
        "schema":"IRE_V3_ADVISORY_EVIDENCE_DOSSIER_V1",
        "as_of":as_of,"jurisdiction":jurisdiction,
        "question":question,"knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
        "evidence_snapshot_sha256":evidence["snapshot_sha256"],
        "relation_snapshot_sha256":relations["snapshot_sha256"] if relations else None,
        "relevant_provisional_claim_count":len(hits),
        "claim_dossiers":items,
        "profile_missing_fields":list(missing),
        "unreviewed_relation_ids":relation_unreviewed,
        "relation_change_conflict_ids":difference,
        "unresolved_advisory_requirements":sorted(set(overall)),
        "statutory_scope_independently_certified":False,
        "investor_suitability_independently_approved":False,
        "automatic_financial_fact_approvals":0,
        "actionable_recommendations":[],
        "individualized_advice_released":False,
        "status":"RESEARCH_DOSSIER_ONLY_NO_UNVERIFIED_ADVICE",
    }


def main():
    import argparse
    from .knowledge import read_private_snapshot
    parser=argparse.ArgumentParser(description="V3 no-API conservative advisory dossier")
    parser.add_argument("operation",choices=["dossier"])
    parser.add_argument("--private-knowledge-snapshot",required=True)
    parser.add_argument("--private-evidence-ledger",required=True)
    parser.add_argument("--private-relation-ledger")
    parser.add_argument("--private-profile")
    parser.add_argument("--question",required=True)
    parser.add_argument("--as-of",required=True)
    parser.add_argument("--jurisdiction")
    parser.add_argument("--private-report-dir",required=True)
    args=parser.parse_args()
    try:
        knowledge=read_private_snapshot(args.private_knowledge_snapshot)
        evidence=json.loads(private_file(args.private_evidence_ledger).read_text(encoding="utf-8"))
        relations=(json.loads(private_file(args.private_relation_ledger).read_text(encoding="utf-8"))
                   if args.private_relation_ledger else None)
        profile=(json.loads(private_file(args.private_profile).read_text(encoding="utf-8"))
                 if args.private_profile else None)
        result=build_advisory_dossier(
            knowledge,evidence,args.question,args.as_of,args.jurisdiction,
            profile,relations)
        encoded=json.dumps(result,ensure_ascii=False,sort_keys=True,
                           separators=(",",":"),allow_nan=False).encode("utf-8")
        digest=sha256(encoded)
        root=safe_private_directory(args.private_report_dir)
        target=root/("ire_v3_advisory_"+digest[:24]+".json")
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,"wb") as stream:
                stream.write(encoded);stream.flush();os.fsync(stream.fileno())
        except Exception:
            target.unlink(missing_ok=True)
            raise
        print(json.dumps({"schema":result["schema"],"status":result["status"],
                          "relevant_claim_count":result["relevant_provisional_claim_count"],
                          "open_gate_count":len(result["unresolved_advisory_requirements"]),
                          "private_report_path":str(target),
                          "report_sha256":digest,"actionable_recommendations":0},
                         sort_keys=True))
        return 2
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        print(json.dumps({"schema":"IRE_V3_ADVISORY_ERROR","status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())