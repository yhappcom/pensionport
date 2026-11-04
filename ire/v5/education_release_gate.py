"""Reconcile research-supported source decisions into deduplicated education entries.

A 5-to-4 merge is justified only when both new source analyses support the
same scoped fact. No human-blind financial or personalized advisory approval.
"""
from pathlib import Path
import json

class EducationReleaseError(ValueError): pass

def demand(value,code):
    if not value: raise EducationReleaseError(code)

def read(path):
    return json.loads(Path(path).read_text("utf-8"))

def verify(root,release=None):
    root=Path(root)
    base=root/"ire/v5/advisory_knowledge"
    source=read(base/"verification_20261104/adjudications.json")
    auth=read(base/"verification_20261104/external_authorities.json")
    approved={x["audit_id"]:x for x in source["rows"] if
              x["disposition"]=="EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"}
    rejected={x["audit_id"] for x in source["rows"] if
              x["disposition"]!="EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"}
    valid_refs={x["id"] for x in auth["sources"]}
    release=release if release is not None else read(
        base/"deduplicated_educational_knowledge_20261104.json")
    demand(release.get("schema")=="IRE_V5_DEDUPLICATED_EDUCATIONAL_KNOWLEDGE_V1"
           and release.get("as_of")=="2026-11-04"
           and release.get("status")=="CHATGPT_EVIDENCE_REVIEW_PASSED_NOT_HUMAN_BLIND_APPROVED",
           "EDUCATION_RELEASE_SCHEMA_INVALID")
    demand(release.get("original_ledger_unchanged") is True and
           release.get("external_blind_independent_approval") is False and
           release.get("financial_advice_go") is False,
           "EDUCATION_RELEASE_UNAUTHORIZED_ADVICE")
    entries=release.get("entries")
    demand(type(entries) is list and len(entries)==release.get("knowledge_count")==4,
           "EDUCATION_RELEASE_KNOWLEDGE_COUNT_INVALID")
    seen=set();ids=set()
    for item in entries:
        kid=item.get("knowledge_id")
        demand(type(kid) is str and kid not in ids,"EDUCATION_KNOWLEDGE_DUPLICATE_ID")
        ids.add(kid)
        scoped=item.get("source_audit_ids")
        demand(type(scoped) is list and scoped and len(scoped)==len(set(scoped))
               and set(scoped)<=set(approved) and not set(scoped)&rejected,
               "EDUCATION_BLOCKED_CLAIM_PROMOTED")
        demand(not seen.intersection(scoped),"EDUCATION_DUPLICATE_SOURCE_PROMOTION")
        seen.update(scoped)
        related={z for t in scoped for z in approved[t]["legacy_claim_ids"]}
        evidence={z for t in scoped for z in approved[t]["authority_ids"]}
        demand(set(item.get("legacy_claim_ids",[]))==related,
               "EDUCATION_DROPPED_OR_INVENTED_LEGACY_REFERENCE")
        demand(type(item.get("authority_ids")) is list and
               set(item["authority_ids"])<=valid_refs and
               set(item["authority_ids"])<=evidence and
               len(item["authority_ids"])>=2,
               "EDUCATION_DROPPED_INDEPENDENT_AUTHORITY")
        demand(type(item.get("educational_fact")) is str and
               len(item["educational_fact"])>=40 and
               type(item.get("critical_qualification")) is str and
               len(item["critical_qualification"])>=30,
               "EDUCATION_MISSING_CRITICAL_QUALIFICATION")
        demand(item.get("reviewed_as_of")=="2026-11-04" and
               item.get("usable_for")=="GENERAL_EDUCATION_WITH_SCOPE_AND_SOURCE_ONLY"
               and item.get("personalized_advice_approved") is False and
               item.get("blind_independent_human_approved") is False and
               item.get("legal_certification") is False and
               item.get("independent_human_review_required_for_formal_promotion") is True,
               "EDUCATION_FAKE_BLIND_OR_LEGAL_APPROVAL")
    demand(seen==set(approved) and
           release.get("source_audit_approvals_merged")==len(seen)==5,
           "EDUCATION_MISSING_SUPPORTED_SOURCE_CLAIM")
    demand(len(entries)==4 and
           sum(len(x["source_audit_ids"]) for x in entries)==5,
           "EDUCATION_DID_NOT_DEDUPLICATE")
    byid={e["knowledge_id"]:e for e in entries}
    isa=byid["EDU-KR-ISA-TO-PENSION-2026-01"]
    demand(set(isa["source_audit_ids"])=={
        "P03_ISA_PENSION_TRANSFER","P07_IRP_PENSION_TRANSFER"} and
           "추가" in isa["educational_fact"] and
           ("환급액" in isa["critical_qualification"] or "공제세액" in isa["critical_qualification"]),
           "EDUCATION_ISA_TAX_DEDUCTION_VS_REFUND_UNSAFE")
    pension=byid["EDU-KR-PRIVATE-PENSION-1500-2026-01"]
    demand("별개" in pension["educational_fact"] and
           "법적 상한" in pension["critical_qualification"],
           "EDUCATION_PENSION_TAX_VS_WITHDRAWAL_CONFUSED")
    dca=byid["EDU-GENERAL-DCA-ARITH-01"]
    demand("-46.67%" in dca["educational_fact"] and
           "보장하지" in dca["educational_fact"],
           "EDUCATION_DCA_FALSE_PROFIT_GUARANTEE")
    return {"schema":"IRE_V5_DEDUPLICATED_EDUCATION_GATE_RESULT_V1",
            "evidence_supported_source_cases":len(seen),
            "deduplicated_education_facts":len(entries),
            "excluded_non_education_cases":len(rejected),
            "original_legacy_claims_unchanged":True,
            "independent_human_blind_grade_present":False,
            "formal_financial_advice_go":False}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.root),ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
