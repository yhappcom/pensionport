"""IRE V2: cryptographically tied primary-source assessments and advisory guard.

The current ChatGPT conversation writes a structured *assessment* from a real
document, and deterministic code rechecks its exact quotation and scope.
This is not independent human review, statutory certification or a trade signal.
Only newly created IRE claim IDs can be associated with evidence assessments.
"""
from __future__ import annotations

from datetime import date
import json
import os
import re

from .source import require,sha256,text_norm,DIGEST
from .evidence import issuer_for
from .knowledge import validate_knowledge,advisory_research_context
from .checkpoint import safe_private_directory

SCHEMA="IRE_V2_EVIDENCE_LEDGER"
VERDICTS={"SUPPORTS","CONTRADICTS","CONDITIONALLY_SUPPORTS","INSUFFICIENT"}
SCOPE_VALUES={"MATCH","CONFLICT","UNRESOLVED","NOT_SPECIFIED"}
SCOPE_FIELDS=("jurisdiction","effective_date","conditions","exceptions","numbers")
REQUIRED_REVIEW={
    "schema","global_claim_id","document_url","document_sha256",
    "document_text_sha256","source_quote","verdict","scope",
    "effective_from","effective_until","chat_reviewer_mode"}
MAX_ASSESSMENTS=500_000


def _serialize(data) -> bytes:
    return json.dumps(data,ensure_ascii=False,sort_keys=True,
                      allow_nan=False,separators=(",",":")).encode("utf-8")


def _hash(data) -> str:
    return sha256(_serialize(data))


def _valid_date(value,nullable=False):
    if value is None and nullable:
        return True
    if type(value) is not str or len(value)!=10:
        return False
    try:
        return date.fromisoformat(value).isoformat()==value
    except ValueError:
        return False


def _seal(body):
    return {**body,"snapshot_sha256":_hash(body)}


def empty_evidence_ledger(knowledge:dict) -> dict:
    validate_knowledge(knowledge)
    return _seal({
        "schema":SCHEMA,
        "version":0,
        "parent_sha256":None,
        "knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
        "assessments":[],
        "current_chat_is_independent_human_reviewer":False,
        "independent_gold_copied_from_prior_study":False,
        "finance_truth_auto_approved":0,
    })


def validate_evidence_ledger(ledger:dict,knowledge:dict) -> None:
    validate_knowledge(knowledge)
    require(type(ledger) is dict and set(ledger)=={
        "schema","version","parent_sha256","knowledge_snapshot_sha256",
        "assessments","current_chat_is_independent_human_reviewer",
        "independent_gold_copied_from_prior_study",
        "finance_truth_auto_approved","snapshot_sha256"
    } and ledger["schema"]==SCHEMA,
            "V2_EVIDENCE_LEDGER_SCHEMA_INVALID")
    base={k:v for k,v in ledger.items() if k!="snapshot_sha256"}
    require(_hash(base)==ledger["snapshot_sha256"],
            "V2_EVIDENCE_LEDGER_TAMPERED")
    require(type(ledger["version"]) is int and ledger["version"]>=0
            and (ledger["parent_sha256"] is None or
                 (type(ledger["parent_sha256"]) is str
                  and DIGEST.fullmatch(ledger["parent_sha256"])))
            and ledger["knowledge_snapshot_sha256"]==
                knowledge["snapshot_sha256"],
            "V2_EVIDENCE_LEDGER_KNOWLEDGE_SNAPSHOT_MISMATCH")
    require(ledger["current_chat_is_independent_human_reviewer"] is False
            and ledger["independent_gold_copied_from_prior_study"] is False
            and ledger["finance_truth_auto_approved"]==0,
            "V2_EVIDENCE_FALSE_INDEPENDENT_APPROVAL")
    claims={c["global_claim_id"] for c in knowledge["claims"]}
    assessments=ledger["assessments"]
    require(type(assessments) is list and len(assessments)<=MAX_ASSESSMENTS
            and ledger["version"]==len(assessments),
            "V2_EVIDENCE_LEDGER_COUNT_INVALID")
    seen=set()
    for a in assessments:
        require(type(a) is dict and set(a)=={
            "assessment_id","global_claim_id","document_url",
            "document_sha256","document_text_sha256","source_quote",
            "quote_sha256","verdict","scope","effective_from",
            "effective_until","issuer_candidate","actual_network_fetch",
            "fetched_at_utc","assessment_label",
            "quotation_against_original_checked","finance_truth_approved",
            "independent_human_reviewed"
        },"V2_EVIDENCE_ASSESSMENT_SCHEMA_INVALID")
        require(a["global_claim_id"] in claims and
                type(a["assessment_id"]) is str and
                re.fullmatch(r"E[0-9a-f]{24}",a["assessment_id"]) and
                a["assessment_id"] not in seen,
                "V2_EVIDENCE_CLAIM_OR_ASSESSMENT_ID_INVALID")
        seen.add(a["assessment_id"])
        require(issuer_for(a["document_url"])==a["issuer_candidate"]
                and a["issuer_candidate"] is not None and
                type(a["document_sha256"]) is str
                and DIGEST.fullmatch(a["document_sha256"])
                and type(a["document_text_sha256"]) is str
                and DIGEST.fullmatch(a["document_text_sha256"]),
                "V2_EVIDENCE_UNTRUSTED_DOCUMENT_LINK")
        require(type(a["source_quote"]) is str and
                len(a["source_quote"])>=8 and
                sha256(a["source_quote"].encode("utf-8"))==a["quote_sha256"],
                "V2_EVIDENCE_QUOTE_TAMPERED")
        require(a["verdict"] in VERDICTS and type(a["scope"]) is dict
                and set(a["scope"])==set(SCOPE_FIELDS)
                and all(x in SCOPE_VALUES for x in a["scope"].values()),
                "V2_EVIDENCE_SCOPE_INVALID")
        require(_valid_date(a["effective_from"],True) and
                _valid_date(a["effective_until"],True) and
                (not a["effective_from"] or not a["effective_until"] or
                 a["effective_from"]<=a["effective_until"]),
                "V2_EVIDENCE_EFFECTIVE_DATE_INVALID")
        require(type(a["actual_network_fetch"]) is bool and
                type(a["fetched_at_utc"]) is str
                and a["assessment_label"] in {
                    "CHAT_ASSESSMENT_WITH_OFFICIAL_TEXT",
                    "CHAT_ASSESSMENT_WITH_SYNTHETIC_SOURCE",
                    "POSSIBLE_CONTRADICTION",
                    "INCONCLUSIVE_OFFICIAL_TEXT"
                } and
                a["quotation_against_original_checked"] is True
                and a["finance_truth_approved"] is False
                and a["independent_human_reviewed"] is False,
                "V2_EVIDENCE_CANNOT_AUTO_CERTIFY_TRUTH")
        digest=_hash({
            "claim_id":a["global_claim_id"],
            "document_sha256":a["document_sha256"],
            "quote_sha256":a["quote_sha256"],
            "verdict":a["verdict"],
            "scope":a["scope"],
            "effective_from":a["effective_from"],
            "effective_until":a["effective_until"]})
        require(a["assessment_id"]=="E"+digest[:24],
                "V2_EVIDENCE_ASSESSMENT_HASH_MISMATCH")


def apply_chat_evidence(ledger:dict,knowledge:dict,
                        document:dict,review:dict) -> dict:
    """Check evidence AGAINST independently captured document text.

    This step is read-only with respect to financial facts; no approval flag.
    It never accepts URL-only citations or inherited investment assertions.
    """
    validate_evidence_ledger(ledger,knowledge)
    require(type(document) is dict and
            document.get("schema")=="IRE_INDEPENDENT_DOCUMENT_V1"
            and type(document.get("visible_text")) is str and
            type(document.get("canonical_url")) is str,
            "V2_EVIDENCE_REQUIRES_INDEPENDENTLY_FETCHED_DOCUMENT")
    require(type(review) is dict and set(review)==REQUIRED_REVIEW
            and review["schema"]=="IRE_CHAT_EVIDENCE_REVIEW_V2",
            "V2_CHAT_EVIDENCE_REVIEW_SCHEMA_INVALID")
    claim_id=review["global_claim_id"]
    require(any(c["global_claim_id"]==claim_id for c in knowledge["claims"]),
            "V2_EVIDENCE_UNREGISTERED_NEW_IRE_CLAIM")
    require(review["document_url"]==document["canonical_url"]
            and review["document_sha256"]==document["raw_sha256"]
            and review["document_text_sha256"]==
                document["visible_text_sha256"]
            and issuer_for(review["document_url"]) is not None,
            "V2_EVIDENCE_DOCUMENT_ORIGIN_MISMATCH")
    require(review["chat_reviewer_mode"]=="CURRENT_CHATGPT_CONVERSATION",
            "V2_EVIDENCE_FALSE_REVIEWER_IDENTITY")
    quote=review["source_quote"]
    require(type(quote) is str and len(quote)>=8
            and len(quote)<=1500 and
            text_norm(quote) in text_norm(document["visible_text"]),
            "V2_EVIDENCE_QUOTE_NOT_IN_FETCHED_ORIGINAL")
    scopes=review["scope"]
    require(type(scopes) is dict and set(scopes)==set(SCOPE_FIELDS)
            and all(x in SCOPE_VALUES for x in scopes.values()),
            "V2_CHAT_SCOPE_INVALID")
    require(review["verdict"] in VERDICTS,
            "V2_CHAT_EVIDENCE_VERDICT_INVALID")
    start,end=review["effective_from"],review["effective_until"]
    require(_valid_date(start,True) and _valid_date(end,True)
            and (start is None or end is None or start<=end),
            "V2_EVIDENCE_DATE_INVALID")
    live=(document.get("source_read_mode")=="LIVE_NETWORK_FETCH")
    if review["verdict"]=="CONTRADICTS":
        label="POSSIBLE_CONTRADICTION"
    elif review["verdict"]=="INSUFFICIENT":
        label="INCONCLUSIVE_OFFICIAL_TEXT"
    else:
        label=("CHAT_ASSESSMENT_WITH_OFFICIAL_TEXT" if live else
               "CHAT_ASSESSMENT_WITH_SYNTHETIC_SOURCE")
    core={"claim_id":claim_id,
          "document_sha256":review["document_sha256"],
          "quote_sha256":sha256(quote.encode("utf-8")),
          "verdict":review["verdict"],
          "scope":scopes,
          "effective_from":start,
          "effective_until":end}
    event={
        "assessment_id":"E"+_hash(core)[:24],
        "global_claim_id":claim_id,
        "document_url":review["document_url"],
        "document_sha256":review["document_sha256"],
        "document_text_sha256":review["document_text_sha256"],
        "source_quote":quote,
        "quote_sha256":core["quote_sha256"],
        "verdict":review["verdict"],
        "scope":scopes,
        "effective_from":start,
        "effective_until":end,
        "issuer_candidate":issuer_for(review["document_url"]),
        "actual_network_fetch":live,
        "fetched_at_utc":document["retrieved_at_utc"],
        "assessment_label":label,
        "quotation_against_original_checked":True,
        "finance_truth_approved":False,
        "independent_human_reviewed":False
    }
    require(not any(x["assessment_id"]==event["assessment_id"]
                    for x in ledger["assessments"]),
            "V2_EVIDENCE_DUPLICATE_ASSESSMENT")
    content={k:v for k,v in ledger.items() if k!="snapshot_sha256"}
    content.update({
        "version":ledger["version"]+1,
        "parent_sha256":ledger["snapshot_sha256"],
        "assessments":ledger["assessments"]+[event]
    })
    next_ledger=_seal(content)
    validate_evidence_ledger(next_ledger,knowledge)
    return next_ledger


def reconcile_ledger_with_updated_knowledge(old:dict,old_knowledge:dict,
                                            new_knowledge:dict) -> dict:
    """Carry prior evidence without silently rewriting its claim citations."""
    validate_evidence_ledger(old,old_knowledge)
    validate_knowledge(new_knowledge)
    valid={c["global_claim_id"] for c in new_knowledge["claims"]}
    require({c["global_claim_id"] for c in old_knowledge["claims"]}<=valid,
            "V2_REBASE_REMOVED_EXISTING_SOURCE_CLAIMS")
    base={k:v for k,v in old.items() if k!="snapshot_sha256"}
    base.update({"knowledge_snapshot_sha256":new_knowledge["snapshot_sha256"],
                 "parent_sha256":old["snapshot_sha256"]})
    # Rebase is not a new evidence assertion. Version remains event count.
    newer=_seal(base)
    validate_evidence_ledger(newer,new_knowledge)
    return newer


def advisory_evidence_context(knowledge:dict,ledger:dict,
                              question:str,as_of:str,
                              jurisdiction:str|None=None,
                              investor_profile:dict|None=None,
                              top_k:int=8) -> dict:
    """Advisory-facing source dossier. Not an investment recommendation."""
    validate_evidence_ledger(ledger,knowledge)
    research=advisory_research_context(
        knowledge,question,as_of,jurisdiction,investor_profile,top_k)
    cited_ids={x["global_claim_id"]
               for x in research["unverified_relevant_claims"]}
    relevant=[]
    verified=0
    contradictions=0
    for assessment in ledger["assessments"]:
        if assessment["global_claim_id"] not in cited_ids:
            continue
        start=assessment["effective_from"]
        end=assessment["effective_until"]
        active=(start is not None and start<=as_of and
                (end is None or as_of<=end))
        unresolved=any(v in ("CONFLICT","UNRESOLVED","NOT_SPECIFIED")
                       for v in assessment["scope"].values())
        direct=assessment["actual_network_fetch"]
        potential=(active and not unresolved and direct and
                   assessment["verdict"]=="SUPPORTS")
        if potential:
            verified+=1
        if assessment["verdict"]=="CONTRADICTS":
            contradictions+=1
        relevant.append({
            **assessment,
            "effective_on_question_date":active,
            "all_scope_fields_explicitly_matched":not unresolved,
            "official_text_corrob_candidate":potential,
            "independent_truth_approved":False
        })
    required=["current_official_effective_law_and_exceptions",
              "all_relevant_claims_independently_adjudicated",
              "cross_video_conflicts_reviewed",
              "product_cost_risk_and_personal_suitability"]
    if not investor_profile:
        required.append("user_suitability_profile_missing")
    return {**research,
        "schema":"IRE_V2_ADVISORY_RESEARCH_CONTEXT",
        "evidence_snapshot_sha256":ledger["snapshot_sha256"],
        "evidence_assessments_for_hits":relevant,
        "plausibly_corroborated_official_text_count":verified,
        "possible_contradictory_evidence_count":contradictions,
        "source_evidence_followups_required":required,
        "certified_independent_financial_facts":0,
        "actionable_recommendations":[],
        "advisory_output_status":"GROUNDED_RESEARCH_CONTEXT_ONLY_NOT_APPROVED_TRADE",
        "advice_usable_without_latest_official_recheck":False,
        "chat_model_human_independence_certified":False
    }


def save_private_evidence(ledger:dict,knowledge:dict,directory:str) -> str:
    validate_evidence_ledger(ledger,knowledge)
    folder=safe_private_directory(directory)
    filename=("ire_evidence_v"+str(ledger["version"]).zfill(6)+"_"+
              ledger["snapshot_sha256"][:16]+".json")
    path=folder/filename
    require(not path.exists(),"V2_EVIDENCE_OVERWRITE_FORBIDDEN")
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb") as stream:
            stream.write(_serialize(ledger))
            stream.flush();os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return str(path)


def main() -> int:
    """No model API; current-chat reviews are accepted as explicit files.

    CLI fetches a real primary document independently, checks direct quote and
    writes an immutable evidence snapshot. Advisory mode never issues orders.
    """
    import argparse
    from .cli import private_file
    from .knowledge import read_private_snapshot
    from .evidence import independently_fetch_candidate

    parser=argparse.ArgumentParser(
        description="Official evidence and guarded finance advisory for current-chat IRE, no model API")
    parser.add_argument("operation",choices=["init","review","advisory","rebase"])
    parser.add_argument("--private-knowledge-snapshot",required=True)
    parser.add_argument("--private-ledger")
    parser.add_argument("--old-private-knowledge-snapshot")
    parser.add_argument("--private-evidence-dir")
    parser.add_argument("--private-original-document-dir")
    parser.add_argument("--private-chat-review")
    parser.add_argument("--question")
    parser.add_argument("--as-of")
    parser.add_argument("--jurisdiction")
    args=parser.parse_args()
    try:
        knowledge=read_private_snapshot(args.private_knowledge_snapshot)
        if args.operation=="init":
            require(args.private_evidence_dir and not args.private_ledger,
                    "V2_EVIDENCE_INIT_ARGS_INVALID")
            ledger=empty_evidence_ledger(knowledge)
            target=save_private_evidence(ledger,knowledge,args.private_evidence_dir)
            result={
                "schema":SCHEMA,
                "knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
                "evidence_snapshot_sha256":ledger["snapshot_sha256"],
                "event_count":0,
                "private_ledger_path":target,
                "financial_claims_approved":0
            }
        else:
            require(args.private_ledger,"V2_EVIDENCE_LEDGER_REQUIRED")
            ledger=json.loads(private_file(args.private_ledger).read_text(encoding="utf-8"))
            if args.operation=="rebase":
                require(args.old_private_knowledge_snapshot and args.private_evidence_dir,
                        "V2_EVIDENCE_REBASE_ARGUMENTS_REQUIRED")
                prior_knowledge=read_private_snapshot(
                    args.old_private_knowledge_snapshot)
                rebased=reconcile_ledger_with_updated_knowledge(
                    ledger,prior_knowledge,knowledge)
                where=save_private_evidence(
                    rebased,knowledge,args.private_evidence_dir)
                result={
                    "schema":SCHEMA,
                    "evidence_snapshot_sha256":rebased["snapshot_sha256"],
                    "knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
                    "event_count":len(rebased["assessments"]),
                    "private_ledger_path":where,
                    "financial_claims_approved":0
                }
            elif args.operation=="review":
                require(args.private_chat_review and args.private_evidence_dir
                        and args.private_original_document_dir,
                        "V2_EVIDENCE_REVIEW_ARGUMENTS_REQUIRED")
                current_review=json.loads(
                    private_file(args.private_chat_review).read_text(encoding="utf-8"))
                require(type(current_review) is dict and
                        type(current_review.get("document_url")) is str,
                        "V2_EVIDENCE_REVIEW_URL_REQUIRED")
                doc=independently_fetch_candidate(
                    current_review["document_url"],
                    private_evidence_dir=args.private_original_document_dir)
                updated=apply_chat_evidence(
                    ledger,knowledge,doc,current_review)
                where=save_private_evidence(
                    updated,knowledge,args.private_evidence_dir)
                result={
                    "schema":SCHEMA,
                    "knowledge_snapshot_sha256":knowledge["snapshot_sha256"],
                    "evidence_snapshot_sha256":updated["snapshot_sha256"],
                    "event_count":len(updated["assessments"]),
                    "private_ledger_path":where,
                    "original_document_sha256":doc["raw_sha256"],
                    "financial_claims_approved":0,
                    "reviewer_identity_independently_attested":False
                }
            else:
                require(args.question and args.as_of,
                        "V2_ADVISORY_QUESTION_DATE_REQUIRED")
                result=advisory_evidence_context(
                    knowledge,ledger,args.question,args.as_of,args.jurisdiction)
        # Public stdout avoids private source quotation and investor input.
        output={
            "schema":result["schema"],
            "evidence_snapshot_sha256":result.get(
                "evidence_snapshot_sha256"),
            "knowledge_snapshot_sha256":result.get(
                "knowledge_snapshot_sha256"),
            "event_count":result.get("event_count"),
            "financial_claims_approved":0,
            "advisory_output_status":result.get(
                "advisory_output_status"),
            "relevant_claims":len(result.get(
                "unverified_relevant_claims",[])),
            "possible_conflicts":len(result.get(
                "possible_cross_video_conflicts_or_updates",[])),
            "private_ledger_path":result.get("private_ledger_path")
        }
        print(json.dumps(output,ensure_ascii=False,sort_keys=True))
        return 2 if args.operation!="init" else 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError):
        print(json.dumps({"schema":"IRE_V2_EVIDENCE_ERROR",
                          "status":"FAILED_CLOSED"}))
        return 3


if __name__=="__main__":
    raise SystemExit(main())
