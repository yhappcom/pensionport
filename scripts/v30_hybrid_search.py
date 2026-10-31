#!/usr/bin/env python3
"""V3.0 candidate-recall search using lexical, role and graph lanes.

Deliberately distinct from a certified entailment classifier. No model
accuracy claims without independently adjudicated held-out gold data.
An explicit development roster embargo is enforced on all corpus entries.
"""
import hashlib
import math
import re
from collections import Counter,defaultdict

from v30_verified_core import guard,VERDICTS,CLAIM_RE,ROLES,check_privacy

ALIASES={
 "연금":"연금 pension retirement pension plan",
 "공무원연금":"공무원연금 공적연금 pension public civil-service",
 "퇴직연금":"퇴직연금 pension retirement irp",
 "isa":"isa individual savings account 세제 계좌 만기",
 "irp":"irp 퇴직연금 연금계좌 retirement pension",
 "세액공제":"세액공제 tax credit 공제 납입",
 "분배금":"분배금 distribution dividend 지급",
 "배당":"배당 dividend distribution income",
 "공제회":"공제회 mutual-benefit retirement income",
 "듀레이션":"듀레이션 duration 채권 금리민감도",
 "채권":"채권 bond fixed-income 금리",
 "환율":"환율 foreign exchange fx 환전",
 "증여":"증여 gift 증여재산공제",
 "만기":"만기 maturity 종료 기간",
}
RELATED_ROLE_PAIRS={
 frozenset(("PENSION_INCOME_PAYOUT_TAX","PENSION_CONTRIBUTION_TAX_CREDIT")),
 frozenset(("ISA_TRANSFER_TAX_CREDIT","PENSION_CONTRIBUTION_TAX_CREDIT")),
 frozenset(("CIVIL_SERVICE_PENSION_CONTRIBUTION",
            "CIVIL_SERVICE_PENSION_BENEFIT")),
 frozenset(("RETIREMENT_INCOME_BRIDGE","RETIREMENT_PENSION_CASHFLOW")),
 frozenset(("BOND_DIRECT_MATURITY","BOND_ETF_MATURITY_RISK")),
 frozenset(("ETF_MINIMUM_TRADE_LOT","FINANCIAL_EDUCATION")),
 frozenset(("EQUITY_DIVERSIFICATION","GROUP_CONCENTRATION")),
 frozenset(("DIVIDEND_PAYOUT_MODEL","RETIREMENT_PENSION_CASHFLOW")),
}
TOKEN_RE=re.compile(r"[0-9A-Za-z가-힣_]+")
def feature_tokens(text):
    guard(isinstance(text,str) and len(text)<=16000,
          "SEARCH_INPUT_INVALID_OR_TOO_LONG")
    low=text.lower()
    expanded=low
    for term,other in ALIASES.items():
        if term in low:expanded+=" "+other
    chunks=TOKEN_RE.findall(expanded)
    lex=set(chunks)
    compact="".join(TOKEN_RE.findall(low))
    # Korean morphology-independent tokens; no pretrained model dependence.
    for n in (2,3,4):
        lex.update(compact[i:i+n] for i in range(max(0,len(compact)-n+1)))
    return frozenset(lex)

def checked_vector(values,model_sha=None):
    """Accept independently generated vectors only if model version pinned.

    This never downloads or trains a semantic model from unseen research data.
    """
    guard(isinstance(model_sha,str) and
          re.fullmatch(r"[a-f0-9]{64}",model_sha),
          "EMBEDDING_MODEL_GIT_OR_CONTENT_HASH_REQUIRED")
    guard(isinstance(values,list) and 2<=len(values)<=4096
          and all(type(x) in (float,int) and math.isfinite(x) for x in values),
          "INVALID_SEMANTIC_EMBEDDING_VECTOR")
    length=math.sqrt(sum(x*x for x in values))
    guard(length>0,"ZERO_SEMANTIC_EMBEDDING_VECTOR")
    return tuple(float(x)/length for x in values)

def make_index(records,development_max_video=20):
    """No #21+ claim body or metadata can enter DEVELOPMENT search index."""
    guard(type(development_max_video) is int
          and development_max_video==20,
          "POST20_DEVELOPMENT_HOLDOUT_EMBARGO")
    guard(isinstance(records,list),"EXPLICIT_CLAIM_INDEX_REQUIRED")
    seen=set();rows=[]
    for r in records:
        guard(isinstance(r,dict),"MALFORMED_SEARCH_RECORD")
        num=r.get("video_number")
        guard(type(num) is int and 1<=num<=development_max_video,
              "HOLDOUT_CLAIM_MUST_NOT_ENTER_DEVELOPMENT_INDEX")
        cid=r.get("claim_id")
        guard(isinstance(cid,str) and CLAIM_RE.fullmatch(cid)
              and cid not in seen and
              isinstance(r.get("text"),str) and r["text"].strip() and
              r.get("legacy_verdict") in VERDICTS,
              "SEARCH_CLAIM_ID_TEXT_OR_VERDICT_INVALID")
        seen.add(cid)
        role=r.get("financial_role")
        guard(role is None or role in ROLES,
              "SEARCH_FINANCIAL_ROLE_NOT_REGISTERED")
        family=r.get("topic_families",[])
        guard(isinstance(family,list) and
              len(family)==len(set(family))
              and all(isinstance(a,str) and a for a in family),
              "INVALID_TOPIC_FAMILY_LIST")
        check_privacy({k:v for k,v in r.items() if k!="embedding"})
        embedding=(checked_vector(r["embedding"],r.get("embedding_model_sha256"))
                   if "embedding" in r else None)
        rows.append({k:r[k] for k in ("claim_id","video_number","text","legacy_verdict")}|{
            "financial_role":role,"topic_families":tuple(family),
            "tokens":feature_tokens(r["text"]),
            "embedding":embedding,
            "embedding_model_sha256":r.get("embedding_model_sha256")})
    # Index ordering is independent of input insertion order.
    rows.sort(key=lambda x:x["claim_id"])
    return tuple(rows)

def search(query,corpus,limit=20,audit_non_candidates=10):
    guard(isinstance(query,dict) and isinstance(query.get("text"),str)
          and query["text"].strip() and
          query.get("financial_role") in ROLES|{None} and
          isinstance(query.get("topic_families",[]),list),
          "SEARCH_QUERY_NEEDS_EXPLICIT_VALID_METADATA")
    guard(type(limit) is int and 1<=limit<=100 and
          type(audit_non_candidates) is int and 0<=audit_non_candidates<=100,
          "BOUNDED_SEARCH_AND_NONCANDIDATE_AUDIT_REQUIRED")
    qt=feature_tokens(query["text"])
    topics=set(query.get("topic_families",[]))
    role=query.get("financial_role")
    query_emb=(checked_vector(query["embedding"],
                              query.get("embedding_model_sha256"))
               if "embedding" in query else None)
    if query_emb is not None:
        guard(all(r["embedding"] is not None and
                  len(r["embedding"])==len(query_emb) and
                  r["embedding_model_sha256"]==
                      query["embedding_model_sha256"] for r in corpus),
              "SEMANTIC_EMBEDDING_MODEL_OR_DIMENSION_DRIFT")
    n=len(corpus)
    termdf=Counter()
    for r in corpus:termdf.update(r["tokens"])
    ranked=[]
    for r in corpus:
        if query.get("claim_id")==r["claim_id"]:continue
        overlap=qt&r["tokens"]
        # Smoothed IDF sparse retrieval, with word-boundary and char ngrams.
        sparse=sum(math.log(1+(n+1)/(1+termdf[t]))
                   for t in overlap)/max(1,math.sqrt(len(qt)))
        ontology=(3.0 if role==r["financial_role"] and role else
                  1.4 if role and frozenset((role,r["financial_role"]))
                        in RELATED_ROLE_PAIRS else 0.0)
        families=3.0*len(topics&set(r["topic_families"]))
        # Coverage: no hard filters that prematurely drop near-synonyms.
        vector_score=(5*sum(a*b for a,b in zip(query_emb,r["embedding"]))
                      if query_emb is not None else 0.0)
        score=round(sparse+ontology+families+vector_score,6)
        ranked.append((score,r))
    ranked.sort(key=lambda x:(-x[0],x[1]["claim_id"]))
    hits=[]
    for score,r in ranked[:limit]:
        verdict=r["legacy_verdict"]
        hits.append({"claim_id":r["claim_id"],"video_number":r["video_number"],
                     "score":score,"source_risk":(
                        "CORRECTION_ONLY" if verdict=="CONTRADICTED" else
                        "UNREPLICATED_HYPOTHETICAL_SOURCE"
                        if verdict=="HYPOTHETICAL" else "HUMAN_REVIEW_ONLY"),
                     "relation":"UNRESOLVED_REQUIRES_TYPED_HUMAN_REVIEW",
                     "approved":False})
    rest=[r["claim_id"] for _,r in ranked[limit:]]
    # Reproducible uniform hash ordering for negative sampling; this samples
    # what retrieval did *not* produce, not independent ground-truth negatives.
    seed=str(query.get("claim_id",query["text"]))
    rest.sort(key=lambda cid:hashlib.sha256(
        (seed+"|"+cid).encode("utf-8")).hexdigest())
    return {
        "schema":"V30_HYBRID_CANDIDATE_REVIEW_QUEUE_V1",
        "search_lanes":["LEXICAL_TFIDF_KOREAN_CHARACTER_NGRAM",
                         "VERSIONED_FINANCIAL_ROLE_ONTOLOGY",
                         "MULTI_TOPIC_FAMILY"]+
                         (["PINNED_MODEL_VECTOR_COSINE"] if query_emb is not None
                          else []),
        "eligible_corpus_claims":len(corpus),
        "review_candidates":hits,
        "noncandidate_audit_sample":rest[:audit_non_candidates],
        "candidate_precision_claimed":None,
        "candidate_recall_claimed":None,
        "noncandidate_golden_labels_provided":False,
        "embedding_backend":"EXTERNALLY_SUPPLIED_VERSIONED_VECTORS"
                            if query_emb is not None else "NOT_SUPPLIED",
        "external_embedding_model_semantic_accuracy_proven":False,
        "development_embargo_up_to_video":20,
        "automatic_knowledge_merge":False,
    }

def build_development_history(root,video_ids):
    """Read ONLY IDs explicitly allowlisted by number <=20, not 4,120 crosswalk.

    For real content, source artifact hashes must be reviewed separately;
    this is a read-only broad recall aid and never a source certification.
    """
    import json
    from pathlib import Path
    root=Path(root)
    guard(type(video_ids) is dict and len(video_ids)<=20,
          "PREAUTHORIZED_SOURCE_ROSTER_REQUIRED")
    records=[]
    for number,id in sorted(video_ids.items()):
        guard(type(number) is int and 1<=number<=20 and
              isinstance(id,str) and re.fullmatch(r"[A-Za-z0-9_-]{11}",id),
              "POST20_HISTORICAL_SOURCE_ACCESS_BLOCKED")
        p=root/"data/analysis_events"/(id+".json")
        obj=json.loads(p.read_text())
        guard(obj["video_id"]==id and obj["approval"]=="APPROVED",
              "HISTORICAL_SOURCE_NOT_APPROVED")
        for atom in obj["core_claims"]:
            records.append({"claim_id":atom["claim_id"],
                            "video_number":number,
                            "text":atom["claim"],
                            "legacy_verdict":atom["verification"],
                            "financial_role":None,
                            "topic_families":[]})
    return make_index(records)
