"""#6/#8/#9 risk-scoped source review: 3,123 original cues, 175 planner
windows, 36 source-anchored candidate claim spans. This does NOT assert
full semantic atomic recall, independent review, or legal/personal approval.

Optional --source-zip performs true in-process private replay. Without it,
GitHub CI only attests the frozen derived source manifest and scope policy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit
from .first_five_window_review_gate import source_windows
from .first_five_remnant_221_gate import cue_txt

LEDGER=Path("ire/v5/validation/extra_video6_8_9_3123cue_36_atomic_scope_20261107.json")
PIN="f5fa5ef1e042205f6c07d1b4b5ce6e8ed4df9d07"
RELATION_LEDGER=Path("ire/v5/validation/extra6_8_9_eight_concept_relations_20261107.json")
RELATION_PIN="2b94480374362142af7e82c96530c80b983d4aa1"
RELATION_TYPES={
    "SCOPE_QUALIFIER","SEPARATE_LEGAL_DIMENSION",
    "CASHFLOW_TAX_SCOPE_CONFLICT_RISK","ACCOUNT_AND_PRODUCT_DISTINCTION",
    "DIFFERENT_FX_RETURN_COMPONENTS","JAPAN_LISTED_US_EQUITY_REFINES",
    "OVERSEAS_EQUITY_TAX_REFINES","GROSS_FX_RETURN_NET_OF_COSTS",
}
SHA_ARCHIVE="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
EXPECTED={
 6:("3MyhYE2jmuE",807,45,"493c52ea3e56cb9be756d70f4de90d3b069c40dff5743d69bd8a8770f32c1bcc",
    "249d7c7c992887fb31a69f4ae545055d8056859ad5bba407ebe62cd5a2d1cd4d"),
 8:("OfkY343OaNs",1039,59,"d97852825e0b09d58eb76957e22cd7ef41f5d8a59013795bc4c949c1e651c921",
    "f4264c5651a4eb2c8a0dcda47cece558e3099cd72ee983fb651077fa756d3b04"),
 9:("YNOSY15ppf8",1277,71,"b48c51ac62ddf27a0d667e018ad1fbf3717e2bb447a66d9c48ed114eeeb6c2ce",
    "4c8ce8c6fa08f47b2fe919ac5878fcab0c6ce266e07bdfc5eb2e6084a6609fae")}
HOSTS={"www.law.go.kr","taxlaw.nts.go.kr","www.nts.go.kr","nts.go.kr",
       "www.kiwoom.com","regulation.krx.co.kr","www.nabo.go.kr",
       "www.trueetn.com"}
STATES={
 "VIDEO_OPINION","LEGAL_SCOPE_REQUIRES_ACCOUNT_CONTRACT",
 "CONDITIONAL_GIFT_STRATEGY","NARROW_2026_STATUTORY_SCOPE",
 "NARROW_STOCK_VALUATION_AND_RETURN_OPEN",
 "CURRENT_2026_FILING_STATUTE_CORRECTED",
 "CASHFLOW_TAX_PRESENT_VALUE_OPEN","EDUCATION_OPINION_AND_ACCOUNT_SCOPE",
 "BENEFICIAL_OWNERSHIP_OPEN","CONDITIONAL_ASSET_ALLOCATION_OPINION",
 "HYPOTHETICAL_2026_STATUTORY_COMBINATION",
 "HYPOTHETICAL_LONG_TERM_RETURN_NOT_FACT",
 "NARROW_ETF_AND_WRAPPER_TAX_SCOPE","PRODUCT_PENSION_ELIGIBILITY_OPEN",
 "PRODUCT_DURATION_AND_TRACKING_RISK","INDEX_STRUCTURE_SCOPED",
 "EQUITY_AND_FX_DOUBLE_EXPOSURE","HEDGE_STRATEGY_CONDITIONAL",
 "THREE_CURRENCY_TAX_AND_MARKET_EXPOSURE",
 "OVERSEAS_EQUITY_TAX_SCOPED_PRODUCT_TERMS_OPEN",
 "TWO_LAYER_HEDGE_SCOPE","HEDGE_MARKET_TIMING_OPINION_ONLY",
 "HISTORICAL_FX_CONTEXT_NOT_FORECAST","STRATEGY_NOT_GUARANTEED",
 "CONSUMPTION_VS_SPECULATION_SCOPE","HISTORICAL_PERSONAL_COST_MODEL",
 "INDEPENDENT_ARITHMETIC_AND_RETURN_HYPOTHESIS",
 "HISTORICAL_FX_REFERENCE_NOT_FORECAST",
 "RATE_AND_MARKET_DATE_NEEDS_VERIFICATION",
 "FX_QUOTATION_AND_FEES_NARROW","FX_PRODUCT_FEE_TERMS_PENDING",
 "FX_QUOTE_UNIT_AND_ASR_RECHECK","FX_CROSS_RATE_IDENTITY_NOT_FORECAST",
 "MULTI_PRODUCT_ACCOUNT_RISK_SCOPE","CASH_RETURN_OPPORTUNITY_COST",
 "HISTORICAL_FX_RATE_PRODUCT_QUOTE"}
class ThreeVideoSourceError(ValueError):pass

def need(ok,code):
    if not ok:raise ThreeVideoSourceError(code)

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def gitblob(blob):
    return hashlib.sha1(b"blob "+str(len(blob)).encode("ascii")+b"\0"+blob).hexdigest()

def rollup(windows):
    return sha("".join(w["window_id"]+":"+w["primary_text_sha256"]+"\n"
                       for w in windows).encode())

def load(root:Path):
    raw=(Path(root)/LEDGER).read_bytes()
    need(gitblob(raw)==PIN,"EXTRA369_REVIEWED_SOURCE_MANIFEST_CHANGED")
    return json.loads(raw)

def audit(root:Path,source_zip:Path|None=None):
    root=Path(root);d=load(root)
    need(d.get("schema")=="IRE_V5_EXTRA6_8_9_ORIGINAL_3123_CUES_175_WINDOWS_AND_36_SCOPED_CANDIDATES_V1"
         and d.get("as_of")=="2026-11-07"
         and d.get("original_archive_sha256")==SHA_ARCHIVE
         and d.get("original_cues_total")==3123
         and d.get("source_windows_total")==175
         and d.get("source_byte_sha_replayed_by_chat_host") is True
         and d.get("source_bytes_replayed_in_github_ci") is False
         and d.get("private_srt_published") is False
         and d.get("window_index_is_not_atomic_recall_certificate") is True
         and d.get("original_36_spans_source_anchor_checked_in_chat") is True
         and d.get("scoped_claim_candidates_total")==36
         and d.get("fully_independent_blind_atomic_recall_proven") is False
         and d.get("novel_authoritative_financial_fact_approvals")==0
         and d.get("formal_B04_edges_created")==0
         and d.get("old_116_claims_unchanged") is True
         and d.get("old_29_p4_education_nodes_unchanged") is True
         and d.get("extra_7_compilation_still_not_holdout") is True
         and d.get("extra_video10_34_cues_preserved") is True
         and d.get("official_reference_context_not_universal_tax_approval") is True
         and d.get("release")==
           "SOURCE_INDEXED_175_WINDOWS_AND_36_SCOPED_ATOMIC_CANDIDATES_NOT_FULL_SEMANTIC_RECALL",
         "EXTRA369_FORGED_ATOMIC_OR_LEGAL_APPROVAL")
    vs=d.get("source_videos",[])
    need(type(vs) is list and len(vs)==3 and
         [x.get("video_number") for x in vs]==[6,8,9],
         "EXTRA369_MISSING_SOURCE_VIDEOS")
    for v in vs:
        vid,cues,windows,srt,roll=EXPECTED[v["video_number"]]
        need(v.get("video_id")==vid
             and v.get("original_cues")==cues
             and v.get("original_windows")==windows
             and v.get("srt_sha256")==srt
             and v.get("window_rollup_sha256")==roll,
             "EXTRA369_ORIGINAL_SOURCE_SHA_OR_COUNT_CHANGED")
    official=d.get("official_context")
    need(type(official) is dict and len(official)==9,
         "EXTRA369_OFFICIAL_SCOPE_CATALOG_CHANGED")
    for sid,context in official.items():
        url=urlsplit(context.get("url",""))
        need(url.scheme=="https" and url.hostname in HOSTS
             and not url.username and not url.password
             and type(context.get("as_of")) is str
             and len(context.get("scope",""))>=25
             and context.get("use") in {
               "2026_STATUTE_NARROW","NTS_GUIDANCE_SCOPED",
               "ISSUER_GUIDANCE_NOT_GOVERNMENT_SIGNED",
               "KRX_MARKET_GUIDANCE_NARROW",
               "2026_LEGISLATIVE_GUIDANCE_PDF_TEXT_NOT_GOVERNMENT_SIGNED",
               "ISSUER_PRODUCT_EXAMPLE"},
             "EXTRA369_INVALID_OFFICIAL_SCOPE_"+sid)
    old=json.loads((root/"ire/v5/validation/first_ten_original_crossvalidation_20261106.json").read_text("utf-8"))
    old_risk={r["case_id"] for r in old["risk_challenges"]
              if r["video_no"] in EXPECTED}
    need(len(old_risk)==9,"EXTRA369_PREVIOUS_9_RISK_CASES_CHANGED")
    candidates=d.get("claim_candidates",[])
    need(type(candidates) is list and len(candidates)==36
         and len({x.get("claim_id") for x in candidates})==36,
         "EXTRA369_NOT_ALL_36_SCOPED_CANDIDATES")
    counts={6:0,8:0,9:0}
    for c in candidates:
        n=c.get("video_number")
        need(type(n) is int and n in EXPECTED,
             "EXTRA369_CANDIDATE_MISATTRIBUTED_VIDEO")
        counts[n]+=1
        ident=f"V5X-{n}-{counts[n]:02d}"
        lo=c.get("start_cue");hi=c.get("end_cue")
        need(c.get("claim_id")==ident
             and c.get("video_id")==EXPECTED[n][0]
             and type(lo) is int and type(hi) is int
             and 1<=lo<=hi<=EXPECTED[n][1]
             and re.fullmatch("[0-9a-f]{64}",str(c.get("source_span_sha256","")))
             and len(c.get("scoped_interpretation",""))>=40
             and c.get("source_review_class") in STATES
             and len(c.get("query_phrases",[]))>=1
             and all(len(x)>=5 for x in c["query_phrases"])
             and c.get("source_semantic_author")=="SAME_CHAT_SESSION_NOT_INDEPENDENT_BLIND"
             and c.get("atomic_decomposition_completeness_proven") is False
             and c.get("statute_or_product_terms_formally_approved") is False
             and c.get("strict_legacy_equivalence_approved") is False
             and c.get("personal_order_or_tax_filing_approved") is False
             and all(sid in official for sid in c.get("official_scope_ids",[]))
             and all(sid in old_risk for sid in c.get("prior_14_risk_related_ids",[])),
             "EXTRA369_CANDIDATE_SOURCE_OR_APPROVAL_INVALID")
    need(counts=={6:12,8:12,9:12},
         "EXTRA369_SOURCE_CASE_BALANCE_CHANGED")
    raw_rel=(root/RELATION_LEDGER).read_bytes()
    need(gitblob(raw_rel)==RELATION_PIN,
         "EXTRA369_UNREVIEWED_CONCEPT_RELATIONS")
    relations_doc=json.loads(raw_rel)
    need(relations_doc.get("schema")==
         "IRE_V5_EXTRA6_8_9_EIGHT_SOURCE_SCOPED_CONCEPT_RELATIONS_V1"
         and relations_doc.get("as_of")=="2026-11-07"
         and relations_doc.get("basis")==LEDGER.name
         and relations_doc.get("source_scoped_candidate_ids_constrained_to_36") is True
         and relations_doc.get("concept_relation_total")==8
         and relations_doc.get("formal_116_master_claim_relations_approved")==0
         and relations_doc.get("new_29_education_nodes_inserted")==0
         and relations_doc.get("source_mutation_approved") is False
         and relations_doc.get("strict_semantic_duplicate_deletion")==0
         and relations_doc.get("personal_tax_advice_authorized") is False
         and relations_doc.get("release")==
           "PROVISIONAL_RELATION_NETWORK_ONLY_NOT_FORMAT_B04_FACT_APPROVAL",
         "EXTRA369_FALSE_FORMAL_CONCEPT_MERGE")
    relations=relations_doc.get("relations")
    candidate_ids={c["claim_id"] for c in candidates}
    need(type(relations) is list and len(relations)==8
         and len({(x.get("from"),x.get("to")) for x in relations})==8,
         "EXTRA369_EIGHT_RELATIONS_NOT_DISTINCT")
    for n,edge in enumerate(relations,1):
        need(edge.get("relation_id")==f"XREL-{n:02d}"
             and edge.get("from") in candidate_ids
             and edge.get("to") in candidate_ids
             and edge["from"]!=edge["to"]
             and edge.get("relation") in RELATION_TYPES
             and len(edge.get("meaning",""))>=30
             and edge.get("strict_atomic_equivalence_certified") is False
             and edge.get("formal_legacy_B04_edge_created") is False
             and edge.get("independent_expert_coherence_review_done") is False,
             "EXTRA369_UNAPPROVED_CONCEPT_EDGE")
    private_replayed=False
    if source_zip is not None:
        p=Path(source_zip)
        need(p.is_file(),"EXTRA369_ORIGINAL_ZIP_MISSING")
        need(sha(p.read_bytes())==SHA_ARCHIVE,
             "EXTRA369_ORIGINAL_ARCHIVE_SHA_CHANGED")
        by_video={}
        with zipfile.ZipFile(p) as z:
            for n,(vid,cues,wcount,srt,digestroll) in EXPECTED.items():
                filename=f"1-100/youtube-transcript-{vid}.srt"
                need(z.namelist().count(filename)==1,
                     "EXTRA369_ORIGINAL_SOURCE_NOT_UNIQUE")
                raw=z.read(filename)
                need(sha(raw)==srt,"EXTRA369_ORIGINAL_SRT_HASH_CHANGED")
                cue_text=cue_txt(raw);w=source_windows(raw)
                need(len(cue_text)==cues and len(w)==wcount
                     and rollup(w)==digestroll,
                     "EXTRA369_175_WINDOW_REPLAY_CHANGED")
                by_video[n]=cue_text
            for c in candidates:
                arr=by_video[c["video_number"]]
                snippet=" ".join(arr[c["start_cue"]-1:c["end_cue"]])
                need(sha(snippet.encode())==c["source_span_sha256"],
                     "EXTRA369_ORIGINAL_CUE_SPAN_HASH_MISMATCH")
        private_replayed=True
    return {
      "schema":"IRE_V5_VIDEO6_8_9_SOURCE_3123_CUES_36_CANDIDATES_RECEIPT_V1",
      "source_video_numbers":[6,8,9],
      "original_source_cues":3123,
      "original_planner_windows":175,
      "scoped_source_claim_candidates":36,
      "previous_crossvideo_risk_cases_checked":9,
      "provisional_crossvideo_concept_relations_checked":8,
      "private_owner_archive_replayed_this_process":private_replayed,
      "actual_source_windows_replayed_this_process":175 if private_replayed else 0,
      "actual_source_claim_spans_replayed_this_process":36 if private_replayed else 0,
      "independent_complete_atomic_recall_certified":False,
      "new_formally_approved_financial_law_facts":0,
      "formal_knowledge_master_edges_approved":0,
      "old_116_master_and_29_nodes_unchanged":True,
      "personal_advice_order_approved":False,
      "release":"PROVISIONAL_SCOPED_FINANCIAL_STUDY_PARTIAL_NOT_ALL_175_CLAIM_COMPLETE",
    }

def retrieve(root:Path,question:str,*,limit:int=3):
    need(type(question) is str and question.strip() and
         type(limit) is int and 1<=limit<=36,"EXTRA369_INVALID_QUERY")
    audit(root)
    q=re.sub(r"\s+","",question.casefold())
    matches=[]
    for c in load(root)["claim_candidates"]:
        if any(re.sub(r"\s+","",t.casefold()) in q
               for t in c["query_phrases"]):
            matches.append({
               "claim_id":c["claim_id"],
               "video_no":c["video_number"],
               "source_cues":[c["start_cue"],c["end_cue"]],
               "caveat":c["scoped_interpretation"],
               "status":c["source_review_class"],
               "prior_risk_ids":c["prior_14_risk_related_ids"],
               "approved_regulatory_fact":False})
    return {"schema":"IRE_V5_EXTRA369_SCOPED_CLAIM_RETRIEVAL_V1",
            "items":matches[:limit],
            "match_count":len(matches[:limit]),
            "released_for_personal_action":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    a=p.parse_args()
    d=retrieve(a.root,a.question) if a.question else audit(a.root,a.source_zip)
    print(json.dumps(d,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
