"""Owner-private #6/#8/#9 *remaining 65* low-keyword source-window semantic audit.

This is a second-pass source-meaning disposition, NOT an independently
blinded atom-by-atom semantic recall rate or final financial-law approval.
With --source-zip the 3,123 SRT cues and 175 windows, 97 prior-claim-linked
windows, 13 high-signal + 65 lower-signal windows and every source digest
are rebuilt. GitHub CI without ZIP verifies pinned reviewed metadata only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from .extra369_unanchored_window_gate import (
    audit as audit_13, load as load_13, score as lexical_risk_score,
    NUMBERS as PRIOR_RISK_COUNTS)
from .extra_video6_8_9_source_gate import (
    EXPECTED, SHA_ARCHIVE, load as load_36, rollup)
from .first_five_window_review_gate import source_windows
from .first_five_remnant_221_gate import cue_txt

P=Path("ire/v5/validation")
LEDGER=P/"extra369_65_low_keyword_windows_meaning_review_20261107.json"
CAUTIONS=P/"extra369_low65_19_financial_scope_cautions_20261107.json"
LEDGER_PIN="12cb98fa794c8e599d09e3e96731a4fa642ea112"
CAUTIONS_PIN="7f44a305fac0a467b45d94d320a9e01009b17db7"
ALLOWED_HOSTS={"www.jpx.co.jp"}
EXPECTED_LABELS={
    "HISTORICAL_OR_NUMERIC_OPEN", "NONFINANCIAL_CONTEXT",
    "BEHAVIORAL_EXPERIENCE", "PERSONAL_STRATEGY_CONDITIONAL",
    "GIFT_OWNERSHIP_OR_TAX_SCOPE_OPEN",
    "PRODUCT_OR_MARKET_MECHANICS_SCOPED",
}

class LowKeywordSourceError(ValueError):pass

def need(valid,code):
    if not valid:
        raise LowKeywordSourceError(code)

def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def pinned_json(root,path,pin):
    blob=(Path(root)/path).read_bytes()
    need(gitblob(blob)==pin,"LOW65_SOURCE_REVIEW_MANIFEST_CHANGED_"+path.stem)
    return json.loads(blob)

def load(root):
    root=Path(root)
    return (pinned_json(root,LEDGER,LEDGER_PIN),
            pinned_json(root,CAUTIONS,CAUTIONS_PIN))

def audit(root:Path,source_zip:Path|None=None):
    root=Path(root)
    prior_receipt=audit_13(root)
    low,cautions=load(root)
    need(low.get("schema")==
         "IRE_V5_EXTRA369_65_LOW_RISK_SCORE_WINDOWS_MEANING_REVIEW_V1"
         and low.get("as_of")=="2026-11-07"
         and low.get("original_private_zip_sha256")==SHA_ARCHIVE
         and low.get("prior_36_claim_anchor_overlapping_windows")==97
         and low.get("previously_unlinked_windows")==78
         and low.get("prior_13_high_signal_windows_preserved")==13
         and low.get("reviewed_below_threshold_windows")==65
         and low.get("untriaged_windows_among_previous_78")==0
         and low.get("source_cues_total")==3123
         and low.get("source_windows_total")==175
         and low.get("semantic_cue_window_reviewed") is True
         and low.get("all_atomic_claims_independently_recalled") is False
         and low.get("blind_independent_second_reviewer_done") is False
         and low.get("original_audio_verified") is False
         and low.get("zero_keyword_matches_can_still_contain_financial_statements") is True
         and low.get("official_2026_statutory_claim_approvals")==0
         and low.get("legacy_master116_unchanged") is True
         and low.get("p4_29_unchanged") is True
         and low.get("strict_equivalence_approvals")==0
         and low.get("release")==
           "ALL_78_PREVIOUSLY_UNLINKED_WINDOWS_MEANING_TRIAGED_13_HIGH_PLUS_65_LOW_NOT_FULL_ATOMIC_RECALL",
         "LOW65_UNEARNED_FINANCIAL_RESEARCH_CERTIFICATION")
    need(cautions.get("schema")==
         "IRE_V5_EXTRA369_19_LOW_KEYWORD_FINANCIAL_SCOPE_CAUTIONS_V1"
         and cautions.get("as_of")=="2026-11-07"
         and cautions.get("source_reviews_file")==LEDGER.name
         and cautions.get("caution_cases_total")==19
         and cautions.get("financetext_keyword_flag_false_negative_examples_detected") is True
         and cautions.get("source_audio_confirmed_for_ticker_or_nikkei") is False
         and cautions.get("independent_full_claim_recall_certified") is False
         and cautions.get("scope_caution_not_atomic_claim_approval") is True
         and cautions.get("strict_legacy_116_equivalence_approvals")==0
         and cautions.get("legal_fact_general_scope_promotions")==0
         and cautions.get("personalized_trading_authorizations")==0
         and cautions.get("previous_13_high_risk_cases_preserved") is True
         and cautions.get("previous_36_cases_preserved") is True
         and cautions.get("release")==
          "19_SOURCE_SCOPED_ADVICE_CAUTIONS_NOT_19_INDEPENDENTLY_CERTIFIED_NEW_ATOMIC_CLAIMS",
         "LOW65_UNAPPROVED_SCOPE_FACT")
    need(prior_receipt["source_windows"]==175
         and prior_receipt["windows_not_directly_anchored_by_prior36"]==78
         and prior_receipt["unlinked_high_signal_windows_reviewed"]==13
         and prior_receipt["provisional_master116_scope_crosswalk_rows"]==13,
         "LOW65_PRIOR_RESEARCH_CONTRACT_MISMATCH")
    by_meta=low.get("source_evidence_rollups",[])
    need(type(by_meta) is list and len(by_meta)==3
         and [r.get("video_number") for r in by_meta]==[6,8,9],
         "LOW65_THREE_SOURCE_VIDEOS_UNVERIFIED")
    for m in by_meta:
        vid,cues,nwindows,srtsha,window_sha=EXPECTED[m["video_number"]]
        need(m.get("video_id")==vid and m.get("original_cues")==cues
             and m.get("source_windows")==nwindows
             and m.get("sha_rollup")==window_sha,
             "LOW65_ORIGINAL_VIDEO_CUE_WINDOW_DIGEST_CHANGED")
    rows=low.get("records")
    need(type(rows) is list and len(rows)==65
         and len({x.get("review_id") for x in rows})==65,
         "LOW65_CUE_WINDOW_TRIAGE_NOT_65")
    by_id={}
    counts=Counter()
    type_count=Counter()
    previous_high=load_13(root)["priority_reviews"]
    high_ids={(x["video_no"],x["source_window_id"]) for x in previous_high}
    for row in rows:
        n=row.get("video_number");wid=row.get("source_window_id")
        need(type(n) is int and n in EXPECTED
             and type(wid) is str
             and re.fullmatch(r"W\d{5}",wid)
             and 1<=int(wid[1:])<=EXPECTED[n][2]
             and row.get("review_id")==f"LOW-{n}-{int(wid[1:]):02d}"
             and (n,wid) not in high_ids
             and row.get("meaning_category") in EXPECTED_LABELS
             and len(row.get("scoped_semantic_disposition",""))>=28
             and row.get("original_source_anchor_verified_on_owner_zip") is True
             and row.get("source_window_text_sha256_available_in_private_replay") is True
             and row.get("all_atomic_claims_in_window_certified") is False
             and row.get("financial_statute_fact_approved") is False
             and row.get("personal_trade_order_approved") is False
             and row.get("independent_blind_semantics_reviewed") is False,
             "LOW65_UNREVIEWED_SOURCE_OR_ILLEGAL_APPROVAL")
        counts[n]+=1;type_count[row["meaning_category"]]+=1
        by_id[row["review_id"]]=row
    need(counts=={6:15,8:25,9:25}
         and dict(type_count)==low.get("counts_by_meaning_class")
         and len(low.get("provisional_meaning_classes",{}))==6,
         "LOW65_DISPOSITION_COUNTS_NOT_REPRODUCIBLE")
    catalog=cautions.get("official_context",{})
    need(type(catalog) is dict and
         set(catalog)=={"JPX_TSE_HOURS","JPX_ETF_ISSUES"},
         "LOW65_OFFICIAL_JPX_REFERENCE_NOT_SCOPED")
    for context in catalog.values():
        u=urlsplit(context.get("url",""))
        need(u.scheme=="https" and u.hostname in ALLOWED_HOSTS
             and not u.username and not u.password
             and context.get("checked_date")=="2026-11-07"
             and len(context.get("scope",""))>=40
             and context.get("full_investment_fact_approval") is False,
             "LOW65_OFFICIAL_EVIDENCE_NOT_NARROW")
    warnings=cautions.get("caution_cases")
    need(type(warnings) is list and len(warnings)==19
         and len({x.get("caution_id") for x in warnings})==19
         and len({x.get("original_window_review_id") for x in warnings})==19,
         "LOW65_MISSING_19_SCOPED_FINANCIAL_CAUTIONS")
    for i,caution in enumerate(warnings,1):
        ref=caution.get("original_window_review_id")
        need(caution.get("caution_id")==f"V5-LOWC-{i:02d}"
             and ref in by_id and caution.get("video_no")==by_id[ref]["video_number"]
             and len(caution.get("meaning_topic",""))>=12
             and len(caution.get("scoped_caution",""))>=42
             and type(caution.get("query_phrases")) is list
             and len(caution["query_phrases"])==2
             and all(len(q)>=5 for q in caution["query_phrases"])
             and all(sid in catalog for sid in caution.get("official_context_ids",[]))
             and caution.get("source_examination_method")==
                 "PRIVATE_OWNER_SRT_CHAT_SOURCE_READ"
             and caution.get("independent_blind_semantic_match_certified") is False
             and caution.get("strict_equivalence_certified") is False
             and caution.get("formal_advice_rule_approved") is False,
             "LOW65_CAUTION_SOURCE_OR_LEGAL_STATUS_UNSUPPORTED")
    private_replayed=False
    if source_zip is not None:
        source_zip=Path(source_zip)
        need(source_zip.is_file(),"LOW65_OWNER_ORIGINAL_ARCHIVE_MISSING")
        need(sha(source_zip.read_bytes())==SHA_ARCHIVE,
             "LOW65_OWNER_ORIGINAL_ARCHIVE_CHANGED")
        prior=load_36(root)
        prior36={n:[] for n in EXPECTED}
        for row in prior["claim_candidates"]:
            prior36[row["video_number"]].append((row["start_cue"],row["end_cue"]))
        with zipfile.ZipFile(source_zip) as z:
            all_seen=0
            all_windows=0
            for n,(vid,ncues,nwindows,srtsha,window_sha) in EXPECTED.items():
                member=f"1-100/youtube-transcript-{vid}.srt"
                need(z.namelist().count(member)==1,
                     "LOW65_PRIVATE_SRT_SOURCE_MISSING")
                raw=z.read(member)
                cues=cue_txt(raw);windows=source_windows(raw)
                need(sha(raw)==srtsha and len(cues)==ncues
                     and len(windows)==nwindows and rollup(windows)==window_sha,
                     "LOW65_PRIVATE_175_SOURCE_WINDOW_REPLAY_FAIL")
                observed=[]
                for w in windows:
                    overlapping=any(a<=w["last_cue"] and b>=w["first_cue"]
                                    for a,b in prior36[n])
                    if overlapping:continue
                    phrase=" ".join(cues[w["first_cue"]-1:w["last_cue"]])
                    if lexical_risk_score(phrase)>=5:continue
                    observed.append(w)
                expected={x["source_window_id"] for x in rows
                          if x["video_number"]==n}
                need({w["window_id"] for w in observed}==expected,
                     "LOW65_CUE_GAPS_OR_LEXICAL_THRESHOLD_FALSE")
                all_seen+=len(observed);all_windows+=len(windows)
            need(all_seen==65 and all_windows==175,
                 "LOW65_PRIVATE_REPLAY_COVERAGE_INCOMPLETE")
        private_replayed=True
    return {
       "schema":"IRE_V5_EXTRA369_ALL78_UNLINKED_WINDOWS_MEANING_DISPOSITION_RECEIPT_V1",
       "source_video_numbers":[6,8,9],
       "source_cues":3123,
       "source_windows":175,
       "previous_36_claim_overlapping_windows":97,
       "previous_13_high_signal_reviews_preserved":13,
       "additional_low_keyword_windows_semantically_triaged":65,
       "all_78_previously_unlinked_windows_triaged":78,
       "untriaged_windows_in_original_78":0,
       "remaining_atomic_completeness_gaps_in_97_linked_windows":"UNKNOWN",
       "additional_low_keyword_financial_cautions":19,
       "private_owner_source_reopened_in_this_process":private_replayed,
       "source_windows_replayed_in_this_process":175 if private_replayed else 0,
       "source_cue_semantics_independently_blind_recalled":False,
       "formal_new_statutory_financial_fact_approvals":0,
       "strict_master_equivalence_approvals":0,
       "existing_116_master_and_29_education_nodes_intact":True,
       "personal_investment_orders_approved":False,
       "release":"ALL_UNLINKED_SOURCE_WINDOWS_MEANING_TRIAGED_NOT_INDEPENDENT_ATOMIC_EXHAUSTIVENESS",
    }

def retrieve(root:Path,question:str,*,limit:int=3):
    need(type(question) is str and question.strip()
         and type(limit) is int and 1<=limit<=19,
         "LOW65_INVALID_QUERY")
    audit(Path(root))
    low,caution_doc=load(root)
    ids={x["review_id"]:x for x in low["records"]}
    q=re.sub(r"\s+","",question.casefold())
    result=[]
    for c in caution_doc["caution_cases"]:
        if any(re.sub(r"\s+","",key.casefold()) in q
               for key in c["query_phrases"]):
            linked=ids[c["original_window_review_id"]]
            result.append({
               "caution_id":c["caution_id"],
               "video_number":linked["video_number"],
               "original_window_id":linked["source_window_id"],
               "scoped_risk":c["scoped_caution"],
               "financial_legal_status":"SOURCE_SCOPED_NOT_FORMAL_B04",
               "official_context_urls":[caution_doc["official_context"][sid]["url"]
                                        for sid in c["official_context_ids"]],
               "strict_new_atomic_claim_certified":False,
               "personal_financial_action_authorized":False,
            })
    return {"schema":"IRE_V5_EXTRA369_LOW65_SCOPED_RETRIEVAL_V1",
            "items":result[:limit],"match_count":min(len(result),limit),
            "independently_certified_financial_rules":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    a=p.parse_args()
    result=retrieve(a.root,a.question) if a.question else audit(a.root,a.source_zip)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
