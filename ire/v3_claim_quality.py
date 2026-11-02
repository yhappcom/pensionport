"""Cross-window source/causal lineage quality audit for provisional V3 research.

Separates literal source citation from economic causal attribution. It does NOT
independently establish financial truth, outcome independence, author identity,
or semantic recall. A code-based match is a review obligation, not a verdict.
No original cues or detailed claims are emitted by the public CLI.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
import os
import re
from .checkpoint import safe_private_directory
from .cli import private_file
from .source import require, sha256

SCHEMA = "IRE_V3_CROSS_WINDOW_CLAIM_QUALITY_AUDIT_V1"
MONEY = re.compile(r"(?<![0-9,.])(\d[\d,]*(?:\.\d+)?)\s*(억|만)?\s*원(?![가-힣])")
FUTURE_CONTRIBUTION = re.compile(r"납부|보험료")
YEAR = re.compile(r"\d+\s*년")
INCREASE = re.compile(r"증가|늘어|추가|증분")
RETROACTIVE = re.compile(r"추\s*납|추후\s*납부|과거\s*납부")
UNKNOWN_UNIT = re.compile(r"단위\s*미\s*명시|단위\s*미\s*확정|지급\s*주기\s*미\s*확정")


def _canon(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",", ":"),allow_nan=False).encode("utf-8")


def _money_values(text):
    result=set()
    for m in MONEY.finditer(text):
        base=Decimal(m.group(1).replace(",", ""))
        factor={"억":100000000,"만":10000,None:1}[m.group(2)]
        result.add(int(base*factor))
    return result


def _claim_outcome_money(claim):
    """Only proposed *benefit* amounts, not invested principal or costs."""
    benefits=set()
    for row in claim["frame"].get("measurements",[]):
        label=row.get("measure_kind", "")
        if INCREASE.search(label) or re.search(r"연금액|수령액|현금흐름|월\s*배당",label):
            benefits |= _money_values(row.get("value_text", ""))
    if not benefits and INCREASE.search(claim["proposition"]):
        benefits |= _money_values(claim["proposition"])
    return benefits


def _claim_context(c, video_id,window_id,ordinal,packet_hash):
    quoted=" ".join(x["quote"] for x in c["source_refs"])
    return {"video_id":video_id,"window_id":window_id,
            "claim_ordinal":ordinal,"packet_sha256":packet_hash,
            "source_quotes_sha256":sha256(_canon(c["source_refs"])),
            "claim":c,"quoted":quoted,"outcomes":_claim_outcome_money(c)}


def audit_claim_quality(queue):
    require(type(getattr(queue,"sessions",None)) is list and
            callable(getattr(queue,"status",None)),
            "V3_QUALITY_QUEUE_REQUIRED")
    items=[]
    for session in queue.sessions:
        for window in session.windows:
            answer=session._answer(window["window_id"])
            if answer is None:
                continue
            packet=session.packet(window["window_id"])
            for ordinal,claim in enumerate(answer["claims"],1):
                items.append(_claim_context(claim,session.video_id,
                    window["window_id"],ordinal,packet["packet_sha256"]))
    issues=[];seen=set()
    def flag(code, item, upstream=None, severity="REQUIRES_SEPARATE_SOURCE_ADJUDICATION"):
        evidence={k:item[k] for k in ("video_id","window_id","claim_ordinal","packet_sha256","source_quotes_sha256")}
        if upstream is not None:
            evidence["conditional_source_window_id"]=upstream["window_id"]
            evidence["conditional_source_claim_ordinal"]=upstream["claim_ordinal"]
            evidence["conditional_source_quote_sha256"]=upstream["source_quotes_sha256"]
        key=(code,item["video_id"],item["window_id"],item["claim_ordinal"])
        if key in seen:return
        seen.add(key)
        issues.append({**evidence,"code":code,"severity":severity,
                       "semantic_error_proven":False,
                       "independent_human_gold_verified":False})
    # If a tax-like quantified statement is transcribed without a unit, it is
    # especially dangerous to treat it as a verified rate. This can be resolved
    # only from independent exact speech / primary legal evidence, not guesses.
    for item in items:
        c=item["claim"]
        if "REGULATION" in c["claim_types"] and "NUMERIC" in c["claim_types"]:
            if any(UNKNOWN_UNIT.search(str(row.get("unit", "")))
                   for row in c["frame"].get("measurements",[])):
                flag("REGULATORY_NUMERIC_UNIT_UNESTABLISHED",item)
    # A measured additional benefit conditional on more future contributions
    # must not silently become the marginal benefit of retroactive payments.
    # Same rounded outcome alone does not prove identical causal inputs.
    # Indexed by video/outcome rather than an O(N^2) scan: a collection of
    # hundreds of videos must remain bounded. A 12-window local horizon
    # avoids treating identical rounded amounts across unrelated topics as
    # automatically describing one continuous calculation.
    future_by_outcome={}
    for item in items:
        later=item["claim"]
        text=later["proposition"]
        if (RETROACTIVE.search(text) and INCREASE.search(text)
                and item["outcomes"]):
            for amount in item["outcomes"]:
                prior=future_by_outcome.get((item["video_id"],amount),[])
                for earlier in prior[-8:]:
                    difference=int(item["window_id"][1:])-int(earlier["window_id"][1:])
                    if not (0 < difference <= 12):continue
                    if (YEAR.search(item["quoted"]) and
                            FUTURE_CONTRIBUTION.search(item["quoted"])):
                        continue
                    flag("PENSION_INCREMENT_CAUSAL_BASIS_UNSEPARATED",item,earlier)
                    break
        if not (YEAR.search(text) and FUTURE_CONTRIBUTION.search(text)
                and INCREASE.search(text) and item["outcomes"]):
            continue
        if later["frame"].get("modality") not in ("CONDITIONAL","HYPOTHESIS","ASSERTION"):
            continue
        for amount in item["outcomes"]:
            future_by_outcome.setdefault((item["video_id"],amount),[]).append(item)
    issues.sort(key=lambda r:(r["video_id"],r["window_id"],r["claim_ordinal"],r["code"]))
    body={
        "schema":SCHEMA,
        "batch_fingerprint":queue.status()["batch_fingerprint"],
        "audited_windows":queue.status()["accepted_windows"],
        "audited_atomic_claims":len(items),
        "risk_count":len(issues),
        "material_unresolved_causal_count":sum(x["code"]=="PENSION_INCREMENT_CAUSAL_BASIS_UNSEPARATED" for x in issues),
        "regulatory_missing_unit_count":sum(x["code"]=="REGULATORY_NUMERIC_UNIT_UNESTABLISHED" for x in issues),
        "issues":issues,
        "independent_real_semantic_recall_certified":False,
        "actual_financial_truth_approved":False,
        "risk_based_review_checks_clear":len(issues)==0,
        "research_integration_quality_approved":False,
        "qualifying_independent_review_required":True,
    }
    return {**body,"report_sha256":sha256(_canon(body))}


def save_private_quality_report(report, directory):
    require(type(report) is dict and report.get("schema")==SCHEMA and
        report.get("report_sha256")==sha256(_canon({k:v for k,v in report.items() if k!="report_sha256"})),
        "V3_QUALITY_REPORT_HASH_MISMATCH")
    root=safe_private_directory(directory)
    path=root/("ire_v3_claim_quality_"+report["report_sha256"][:24]+".json")
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb") as out:
            out.write(_canon(report));out.flush();os.fsync(out.fileno())
    except Exception:
        path.unlink(missing_ok=True);raise
    return str(path)


def main():
    from .v3_orchestrator import ChatBatchQueue
    parser=argparse.ArgumentParser(description="Audit cited financial causal scope, no auto-certification")
    parser.add_argument("operation",choices=["audit"])
    parser.add_argument("--private-manifest",required=True)
    parser.add_argument("--private-report-dir",required=True)
    opts=parser.parse_args()
    try:
        queue=ChatBatchQueue(json.loads(private_file(opts.private_manifest).read_text(encoding="utf-8")))
        report=audit_claim_quality(queue)
        path=save_private_quality_report(report,opts.private_report_dir)
        print(json.dumps({"schema":SCHEMA,"audited_atomic_claims":report["audited_atomic_claims"],
                          "risk_count":report["risk_count"],"material_causal_review":report["material_unresolved_causal_count"],
                          "unknown_regulatory_unit":report["regulatory_missing_unit_count"],
                          "report_sha256":report["report_sha256"],"private_report":path,
                          "independent_gold_verified":False,"financial_truth_approved":False},sort_keys=True))
        return 0
    except (KeyError,ValueError,TypeError,OSError,UnicodeError):
        print(json.dumps({"schema":"IRE_V3_CLAIM_QUALITY_ERROR","status":"FAILED_CLOSED"}))
        return 3

if __name__=="__main__":raise SystemExit(main())