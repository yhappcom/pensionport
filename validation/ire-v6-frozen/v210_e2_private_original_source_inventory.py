"""V210: private REAL original SRT provisional E2 claim inventory audit.

This mechanically verifies source bytes, cue census, spans, exact source
quotes and explicit HOLD fields. No user transcripts or research note text
appear in returned receipts, CI artifacts or public repository content.
The independent semantic gold, speaker identity, financial truth and E2 PASS
are deliberately unsupported; ChatGPT authored this private working material.
"""
from __future__ import annotations

from collections import Counter

from ire.v6.codec import sha256
from ire.v6.source import parse_srt
from ire.v6.errors import InvalidInput

SCHEMA="IRE_V210_REAL_ETF_SOURCE_FIRST_UNAPPROVED_WORKING_REVIEW_V1"
KINDS={"FACT","OPINION","HYPOTHETICAL","RECOMMENDATION","MATH"}
DENIAL_KEYS={
    "financial_fact_approved":False,
    "gold_quality_certified":False,
    "e2_pass":False,
    "e3_e4_e5_authorized":False,
    "knowledge_written":False,
}


def ensure(predicate,reason):
    if not predicate:
        raise InvalidInput("V210_E2_PRIVATE_"+reason)


def audit_private_e2_source_first_inventory(raw_srt,inventory,*,
                                             expected_source_sha256):
    ensure(type(raw_srt) is bytes and
           type(expected_source_sha256) is str and
           sha256(raw_srt)==expected_source_sha256,
           "ORIGINAL_BYTES_CHANGED")
    cues=parse_srt(raw_srt)
    ensure(type(inventory) is dict and
           inventory.get("schema")==SCHEMA and
           inventory.get("source_sha256")==expected_source_sha256 and
           inventory.get("cue_count")==len(cues) and
           type(inventory.get("video_id")) is str and
           8<=len(inventory["video_id"])<=64 and
           inventory.get("review_method")==
              "CHATGPT_DIRECT_ORIGINAL_SRT_FIRST_PASS_NEW_HYPOTHESES_NOT_INDEPENDENT_GOLD" and
           inventory.get("current_turn_source_directly_read") is True and
           inventory.get("original_v179_prior_claims_used_as_source_of_labels") is False,
           "INVENTORY_SOURCE_OR_REVIEW_CUSTODY_INVALID")
    ensure(all(inventory.get(k) is v for k,v in DENIAL_KEYS.items()),
           "FALSE_E2_OR_FINANCIAL_TRUTH_APPROVAL")
    expected_cues=set(range(1,len(cues)+1))
    ensure(type(inventory.get("claims")) is list and
           len(inventory["claims"])>=1 and
           len(inventory["claims"])<=len(cues)*8 and
           inventory.get("submitted_claims_provisional")==
                len(inventory["claims"]),
           "CLAIM_RECORD_COUNT")
    seen_ids=set()
    types=Counter()
    seen_span=set()
    flagged=0
    for n,atom in enumerate(inventory["claims"],1):
        ensure(type(atom) is dict and set(atom)=={
            "provisional_id","start_cue","end_cue","kind",
            "proposition_unverified","anchors","condition_anchor_cues",
            "exception_anchor_cues","risks","financial_fact_approved",
            "speaker_verified","native_v6_claim_id","e2_pass",
            "e3_e4_e5_authorized"},
            "PROVISIONAL_CLAIM_SCHEMA")
        cid=atom["provisional_id"]
        start,end=atom["start_cue"],atom["end_cue"]
        ensure(type(cid) is str and cid==f"E2REAL-{n:03d}" and
               cid not in seen_ids and
               type(start) is int and type(end) is int and
               1<=start<=end<=len(cues) and
               type(atom["kind"]) is str and atom["kind"] in KINDS and
               type(atom["proposition_unverified"]) is str and
               len(atom["proposition_unverified"].strip())>=12 and
               type(atom["anchors"]) is list and atom["anchors"] and
               len(atom["anchors"])<=80 and
               type(atom["condition_anchor_cues"]) is list and
               type(atom["exception_anchor_cues"]) is list and
               type(atom["risks"]) is list and
               all(type(x) is str and 3<=len(x)<=100 for x in atom["risks"]) and
               atom["financial_fact_approved"] is False and
               atom["speaker_verified"] is False and
               atom["native_v6_claim_id"] is None and
               atom["e2_pass"] is False and
               atom["e3_e4_e5_authorized"] is False,
               "PROVISIONAL_CLAIM_NOT_SOURCE_ONLY")
        anchor_idx=[]
        for link in atom["anchors"]:
            ensure(type(link) is dict and set(link)=={
                "cue_index","quote","source_text_sha256"},
                "SOURCE_ANCHOR_FIELDS")
            i=link["cue_index"]
            ensure(type(i) is int and start<=i<=end and
                   type(link["quote"]) is str and
                   link["quote"]==cues[i-1].text and
                   type(link["source_text_sha256"]) is str and
                   link["source_text_sha256"]==
                       sha256(cues[i-1].text.encode("utf-8")),
                   "SOURCE_ANCHOR_QUOTE_OR_SHA_CHANGED")
            anchor_idx.append(i)
        ensure(anchor_idx==sorted(set(anchor_idx)),
               "DUPLICATE_OR_UNORDERED_ANCHOR_CUES")
        for key in ("condition_anchor_cues","exception_anchor_cues"):
            terms=atom[key]
            ensure(all(type(i) is int and i in anchor_idx for i in terms) and
                   terms==sorted(set(terms)),
                   "QUALIFIER_OR_EXCEPTION_SOURCE_ANCHOR_MISSING")
        seen_ids.add(cid)
        seen_span.update(range(start,end+1))
        types[atom["kind"]]+=1
        if atom["risks"]:
            flagged+=1
    uncovered=inventory.get("uncovered_original_cues")
    ensure(type(uncovered) is list and
           all(type(i) is int for i in uncovered) and
           uncovered==sorted(expected_cues-seen_span) and
           not (seen_span&set(uncovered)) and
           inventory.get("cues_in_any_hypothesis_span")==len(seen_span) and
           inventory.get("types")==dict(types),
           "ORIGINAL_250_CUE_COVERAGE_OR_CLAIM_TYPES_DRIFT")
    # No statement of semantic recall can follow from 1:1 mechanical
    # coverage; a span can contain unextracted meanings.
    return {
        "schema":"IRE_V210_E2_PRIVATE_SOURCE_MECHANICAL_RECEIPT_V1",
        "source_sha256":sha256(raw_srt),
        "video_id":inventory["video_id"],
        "original_cues_checked":len(cues),
        "source_anchored_provisional_claims":len(seen_ids),
        "source_spans_accounted_cues":len(seen_span),
        "nonclaim_or_connective_cues":len(uncovered),
        "candidates_with_explicit_caution_flags":flagged,
        "kinds":dict(types),
        "all_anchor_quotes_exactly_original":True,
        "all_cue_hashes_original":True,
        "e2_semantic_gold_verified":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "financial_fact_truth_certified":False,
        "native_v6_claims_created":False,
        "research_knowledge_published":False,
    }
