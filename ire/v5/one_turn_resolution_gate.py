"""One-turn finalization gate for V5 claim review (33 targeted / 53 original).

ChatGPT performs semantic research and official-source reading in the ACTIVE
user turn; GitHub stores immutable references and runs reproducible contract
checks. No external model API or automatic ChatGPT re-entry is implied.
The process TERMINATES with a scoped verdict or explicit blocked condition.
A completed research case is never automatically a personal-advice approval.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import re
from urllib.parse import urlparse

DIR = Path("ire/v5/advisory_knowledge")
FILE = DIR / "one_turn33_20261104/decisions.json"
TYPE_MAP = {
    "CONDITIONAL_RULE_OPEN":"RULE_SCOPED_PERSONAL_CHECK_REQUIRED",
    "ACCOUNT_OR_PRODUCT_OPEN":"PRODUCT_OR_BROKER_UNVERIFIED_PERSONAL_USE_BLOCKED",
    "PERSONAL_SUITABILITY_OPEN":"PERSONAL_SUITABILITY_UNASSESSED_ACTION_REFUSED",
    "NUMERIC_OR_ASR_OPEN":"NUMERIC_SOURCE_RECONCILED_AUDIO_UNVERIFIED",
    "EDUCATION_CANDIDATE":"INDEPENDENT_ISSUER_DOCUMENT_CROSSCHECKED_EDUCATION_ONLY",
}
EXPECTED = {
    "RULE_SCOPED_PERSONAL_CHECK_REQUIRED":7,
    "PRODUCT_OR_BROKER_UNVERIFIED_PERSONAL_USE_BLOCKED":7,
    "PERSONAL_SUITABILITY_UNASSESSED_ACTION_REFUSED":5,
    "NUMERIC_SOURCE_RECONCILED_AUDIO_UNVERIFIED":2,
    "INDEPENDENT_ISSUER_DOCUMENT_CROSSCHECKED_EDUCATION_ONLY":12,
}
EXCLUDED={"HISTORICAL_ONLY":8,"UNSAFE_GENERALIZATION_BLOCKED":1,"OUT_OF_SCOPE":2}
KNOWN_EXISTING={"EDU-KR-PRIVATE-PENSION-1500-2026-01","EDU-GENERAL-DCA-ARITH-01"}

class FinalizationError(ValueError):
    pass

def require(ok:bool,code:str):
    if not ok:raise FinalizationError(code)

def load(path):
    return json.loads(Path(path).read_text("utf-8"))

def compute_fnv64(rows):
    canonical="\n".join(sorted(
        r["claim_id"]+" "+r["original_cue_span_sha256"] for r in rows))
    h=0xcbf29ce484222325
    for char in canonical.encode("utf-8"):
        h=((h^char)*0x100000001b3)&0xffffffffffffffff
    return format(h,"016x")

def verify(root:Path,judgments:dict|None=None)->dict:
    root=Path(root)
    j=judgments if judgments is not None else load(root/FILE)
    t=load(root/DIR/"review44_20261104/triage.json")
    prev=load(root/DIR/"verification_20261104/adjudications.json")
    old4=load(root/DIR/"deduplicated_educational_knowledge_20261104.json")
    require(j.get("schema")=="IRE_V5_SINGLE_TURN_33_REVIEW_V1"
            and j.get("as_of")=="2026-11-04"
            and j.get("reviewed_count")==33,"SINGLE_TURN_SCHEMA_OR_COUNT_BAD")
    require(j.get("original_srt_zip_sha256")==t["archive_sha256"]
            and j.get("original_span_integrity_fnv64")=="98fff0509406a4fe",
            "SINGLE_TURN_SRT_PROVENANCE_TAMPERED")
    require(j.get("research_complete_for_all_33") is True
            and j.get("formal_financial_advice_go") is False
            and j.get("external_human_blind_review_completed") is False
            and j.get("source_audio_verification_completed") is False
            and j.get("source_content_immutable_official_capture") is False
            and j.get("eligible_for_general_education_only") is True,
            "SINGLE_TURN_FICTITIOUS_APPROVAL")
    approved_previously={c["source_study_claim_id"] for c in prev["rows"]}
    require(len(approved_previously)==9,"ORIGINAL_PRIOR_ASSESSMENT_COUNT_BAD")
    tri={x["claim_id"]:x for x in t["records"]}
    require(len(tri)==44,"ORIGINAL_44_TRIAGE_MISSING")
    pending={k:v for k,v in tri.items() if v["disposition"] in TYPE_MAP}
    require(len(pending)==33,"ORIGINAL_PENDING_33_MISMATCH")
    distinct_source={item["id"]:item for item in j.get("reference_catalog",[])}
    require(len(distinct_source)==len(j.get("reference_catalog",[]))>=20,
            "REFERENCE_CATALOG_DUPLICATED_OR_SHORT")
    for key,source in distinct_source.items():
        u=urlparse(source.get("url",""))
        require(u.scheme=="https" and bool(u.hostname)
                and source.get("checked_date")=="2026-11-04"
                and source.get("original_fulltext_snapshotted") is False
                and source.get("external_human_verified") is False,
                "UNTRUSTED_OR_FAKE_INDEPENDENT_SOURCE")
    seen=set()
    category=Counter()
    education_targets=defaultdict(list)
    for record in j.get("cases",[]):
        cid=record.get("claim_id")
        require(cid in pending and cid not in seen
                and cid not in approved_previously,
                "UNEXPECTED_DUPLICATE_OR_OLD_CLAIM")
        seen.add(cid)
        original=pending[cid]
        require(record.get("video_id")==original["video_id"]
                and record.get("source_sha256")==original["source_sha256"]
                and record.get("original_cue_range")==[
                    original["first_cue"],original["last_cue"]]
                and record.get("original_span_sha256")==original["original_cue_span_sha256"]
                and record.get("exact_source_claim")==original["source_paraphrase"],
                "ORIGINAL_CUE_OR_CLAIM_MISMATCH")
        require(record.get("old_status")==original["disposition"]
                and record.get("decision")==TYPE_MAP[original["disposition"]],
                "CLASSIFICATION_CHANGED_WITHOUT_SOURCE_REVIEW")
        require(record.get("review_date")=="2026-11-04"
                and record.get("all_review_rows_terminal") is True
                and record.get("personal_action_release") is False
                and record.get("formal_financial_fact_approval") is False
                and record.get("external_human_blind_review") is False,
                "UNREVIEWED_FACT_FALSELY_PROMOTED")
        require(isinstance(record.get("scoped_general_conclusion"),str)
                and len(record["scoped_general_conclusion"])>=25
                and isinstance(record.get("conditions_and_exceptions"),str)
                and len(record["conditions_and_exceptions"])>=25,
                "UNSAFE_SCOPE_OR_NO_INDIVIDUAL_DISPOSITION")
        references=record.get("official_reference_ids")
        require(isinstance(references,list) and len(references)>=2
                and len(set(references))==len(references)
                and set(references)<=set(distinct_source),
                "MISSING_OFFICIAL_REFERENCE")
        if original["disposition"]=="EDUCATION_CANDIDATE":
            kid=record.get("knowledge_target")
            require(isinstance(kid,str) and kid.startswith("EDU-"),
                    "EDUCATION_NO_KNOWLEDGE_TARGET")
            distinct_publishers={distinct_source[s]["issuer"] for s in references}
            require(len(distinct_publishers)>=2,
                    "EDUCATION_NOT_CHECKED_AGAINST_INDEPENDENT_PUBLISHERS")
            education_targets[kid].append(cid)
        elif original["disposition"]=="NUMERIC_OR_ASR_OPEN":
            require(record.get("math_reproduced") is True
                    and record.get("original_audio_authenticated") is False,
                    "NUMERIC_ASR_AUDIO_UNSUPPORTED_CERTIFICATION")
            a=record.get("arithmetic")
            require(isinstance(a,dict),"NUMERIC_NO_ARITHMETIC_PROOF")
            if cid=="P217-04":
                require(a["first_three_total_10k_krw"]==
                        a["yearly_first_three_10k_krw"]*3
                        and a["next_five_total_10k_krw"]==
                        a["yearly_next_five_10k_krw"]*5
                        and a["total_10k_krw"]==8400
                        and a["erroneous_asr_cue"]==177,
                        "PENSION_ASR_NOT_RECONCILED")
            if cid=="I255-06":
                require(a["principal_krw"]==a["initial_price_krw"]*a["shares"]
                        and a["assumed_next_value_krw"]==
                        a["assumed_next_price_krw"]*a["shares"]
                        and a["initial_dividend_krw"]==50000
                        and a["assumed_next_dividend_krw"]==100000,
                        "ISA_NUMERIC_SCENARIO_NOT_REPRODUCIBLE")
            require(record.get("knowledge_target") is None,
                    "NUMERIC_UNVERIFIED_AUDIO_PROMOTED_AS_KNOWLEDGE")
        else:
            require(record.get("knowledge_target") is None,
                    "PERSONAL_OR_PRODUCT_CLAIM_PROMOTED")
        category[record["decision"]]+=1
    require(seen==set(pending) and dict(category)==EXPECTED
            and j.get("counts")==dict(category),
            "RESEARCH_DID_NOT_COMPLETE_ALL_33")
    require(compute_fnv64(t["records"])!="98fff0509406a4fe",
            "INCORRECT_SOURCE_DIGEST_SCOPE")
    require(compute_fnv64([pending[c] for c in seen])=="98fff0509406a4fe",
            "SRT_33_SPAN_DIGEST_MISMATCH")
    hist=Counter(x["disposition"] for x in t["records"]
                 if x["claim_id"] not in pending)
    require(dict(hist)==EXCLUDED and set(tri).isdisjoint(approved_previously),
            "UNRESOLVED_OR_EXCLUDED_ITEMS_PROMOTED")
    old_ids={x["knowledge_id"] for x in old4["entries"]}
    overlapping=set(education_targets)&old_ids
    require(overlapping==KNOWN_EXISTING,
            "WRONG_PREVIOUS_EDUCATION_DEDUP")
    require(len(education_targets)==11
            and len(education_targets)-len(overlapping)==9
            and sum(len(x) for x in education_targets.values())==12,
            "INCORRECT_EDUCATION_KNOWLEDGE_DEDUP")
    return {
        "schema":"IRE_V5_ONE_TURN_FINALIZATION_RECEIPT_V1",
        "as_of":"2026-11-04",
        "original_new_claims":53,
        "prior_high_risk_claims":9,
        "this_turn_claims_terminated":33,
        "historical_or_excluded_claims":11,
        "claims_without_disposition":0,
        "conditional_product_personal_claims":19,
        "numeric_asr_claims_context_reconciled":2,
        "education_candidates_public_source_crosschecked":12,
        "new_nonduplicated_education_concepts":9,
        "existing_education_concepts_updated_by_source":2,
        "previous_education_concepts":len(old_ids),
        "total_provisional_scoped_education_concepts":len(old_ids)+9,
        "human_blind_independent_approvals":0,
        "source_audio_confirmations":0,
        "formal_personalized_financial_advice_go":False,
        "terminal_state":"RESEARCH_REVIEW_COMPLETED_ADVISORY_NO_GO",
    }

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(verify(a.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__": main()
