"""Review 20 historical research claims without promoting unverified facts."""
from collections import Counter
from pathlib import Path
import json
import hashlib
from urllib.parse import urlparse

DOMAINS={"ISA","PENSION","IRP","ETF","ALLOCATION"}
HOSTS={"www.law.go.kr","g.nts.go.kr","www.fsc.go.kr","www.moel.go.kr",
       "regulation.krx.co.kr","m.krx.co.kr","www.investor.gov"}
KINDS={"LAW_TEXT","HISTORIC_EXPLANATION","ADMINISTRATIVE_GUIDANCE",
       "PROPOSAL_NOT_EFFECTIVE_LAW","EXCHANGE_RULE_GUIDANCE","INVESTOR_EDUCATION"}
LEVELS={"RELEVANT_RULE_SCOPE_CANDIDATE","GENERAL_INVESTOR_EDUCATION","PARTIAL_OR_GAP"}

class KnowledgeGateError(ValueError):
    pass

def require(predicate,code):
    if not predicate: raise KnowledgeGateError(code)

def read_json(file):
    return json.loads(Path(file).read_text("utf-8"))

def verify_core20(root, data=None):
    root=Path(root)
    data=data if data is not None else read_json(
        root/"ire/v5/advisory_knowledge/core20_candidates_20261104.json")
    require(data.get("schema")=="IRE_V5_CORE20_EVIDENCE_CANDIDATES_V1"
            and data.get("review_date")=="2026-11-04"
            and data.get("selected_count")==20,"CORE20_SCHEMA_INVALID")
    require(data.get("approved_independent_financial_facts")==0
            and data.get("approved_personalized_advice_items")==0
            and data.get("knowledge_rewrite_performed") is False,
            "CORE20_UNAUTHORIZED_APPROVAL")
    sources=data.get("sources")
    require(type(sources) is list and len(sources)>=8
            and len(sources)==data.get("source_count"),"EVIDENCE_CATALOG_INVALID")
    by_source={}
    for s in sources:
        sid=s.get("source_id")
        require(type(sid) is str and sid not in by_source
                and s.get("kind") in KINDS,"EVIDENCE_ID_OR_KIND_INVALID")
        u=urlparse(s.get("url",""))
        require(u.scheme=="https" and u.hostname in HOSTS,"EVIDENCE_UNTRUSTED_HOST")
        require(s.get("independent_attestation") is False and
                s.get("immutable_source_snapshot_sha256") is None,
                "UNATTESTED_SOURCE_AS_CERTIFIED")
        require(s.get("historical_or_proposed") is not None,"LAW_STATUS_UNKNOWN")
        if sid=="IRP-PROPOSAL":
            require(s["kind"]=="PROPOSAL_NOT_EFFECTIVE_LAW" and
                    s["historical_or_proposed"] is True,
                    "IRP_PROPOSAL_MISCLASSIFIED_AS_LAW")
        if sid=="ISA-FSC-HISTORY":
            require(s["kind"]=="HISTORIC_EXPLANATION" and
                    s["historical_or_proposed"] is True,
                    "HISTORIC_ISA_GUIDANCE_AS_CURRENT_RULE")
        by_source[sid]=s
    raw=(root/"data/claims.jsonl").read_bytes()
    git_blob_hash=hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\x00"+raw).hexdigest()
    require(data.get("legacy_ledger_blob_sha1")==git_blob_hash,
            "LEGACY_LEDGER_BLOB_MISMATCH")
    original={}
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            x=json.loads(line)
            require(x["claim_id"] not in original,"DUPLICATE_LEGACY_ID")
            original[x["claim_id"]]=x
    cats=Counter()
    seen=set()
    links=0
    for c in data.get("claims",[]):
        cid=c.get("claim_id")
        require(cid in original and cid not in seen,"BAD_OR_DUPLICATED_CLAIM")
        seen.add(cid)
        base=original[cid]
        require(c.get("legacy_claim")==base["claim"] and
                c.get("legacy_topic")==base["topic"] and
                c.get("original_supporting_video_ids")==base["supporting_videos"] and
                c.get("legacy_confidence_label_unverified")==base["confidence"] and
                c.get("legacy_status")==base["status"],
                "SOURCE_PROVENANCE_ORIGINAL_CLAIM_CHANGED")
        d=c.get("domain")
        require(d in DOMAINS,"UNKNOWN_FINANCE_DOMAIN")
        cats[d]+=1
        refs=c.get("evidence_source_ids")
        require(type(refs) is list and len(refs)>0
                and len(set(refs))==len(refs) and set(refs)<=set(by_source),
                "CLAIM_OFFICIAL_EVIDENCE_MISSING")
        require(c.get("evidence_relation") in LEVELS and
                c.get("review_state")=="SOURCE_CANDIDATE_REVIEW_REQUIRED",
                "CLAIM_REVIEW_STATE_INVALID")
        require(all(type(c.get(k)) is str and len(c[k])>10 for k in
                    ("candidate_scope_summary","condition","exception_or_risk","verification_gap")),
                "CONDITIONS_OR_EXCEPTIONS_MISSING")
        require(all(c.get(k) is False for k in
                    ("private_original_srt_rechecked_this_turn",
                     "source_text_snapshot_sealed","external_blind_human_verified",
                     "independent_financial_fact_approved",
                     "approved_for_personalized_advice",
                     "can_merge_into_approved_knowledge")),
                "UNVERIFIED_FINANCIAL_ADVICE_PROMOTED")
        links+=len(refs)
    require(len(seen)==20 and set(cats)==DOMAINS
            and all(cats[d]==4 for d in DOMAINS),"CORE20_DOMAIN_COVERAGE_INVALID")
    return {"claims_reviewed":len(seen),
            "by_domain":dict(sorted(cats.items())),
            "official_source_candidates":len(by_source),
            "claim_to_evidence_links":links,
            "independent_financial_fact_approvals":0,
            "advisory_items_approved":0,"release":"RESEARCH_ONLY"}
