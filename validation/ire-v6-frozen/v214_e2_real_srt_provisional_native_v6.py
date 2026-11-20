"""V214 E2 — real-original source-first candidate -> exact native V6 audit.

A NEW, isolated reconstruction from V210 private reviewer hypotheses, never
the missing historical V179/V181 owner SQLite. It enumerates ALL original
cues, retains explicit unresolved status, and refuses derived/unspoken
numeric propositions. No question/quote/gold/speaker/financial approvals.
Inputs and full native exchange STAY PRIVATE; return only a redacted receipt.

For the ChatGPT-in-loop design this is an E2 candidate preflight, not V123
knowledge publication and not a substitute for verified V176 event replay.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import re

from ire.v6.atomic_exchange import NUMBER,audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from v210_e2_private_original_source_inventory import (
    audit_private_e2_source_first_inventory,
)

SCHEMA="IRE_V214_E2_REAL_ORIGINAL_NATIVE_V6_DRAFT_RECONSTRUCTION_V1"
BLOCK_RISKS={"COMPUTED_NOT_SPOKEN","DERIVED_MATH_NOT_SPOKEN"}


def require(ok,code):
    if not ok:
        raise InvalidInput("V214_E2_"+code)


def _missing_numbers(proposition,original_context):
    available=Counter()
    for cue in original_context:
        available.update(NUMBER.findall(cue))
    requested=Counter(NUMBER.findall(proposition))
    return [value for value,count in requested.items()
            if count>available[value]]


def construct_provisional_native_v6(raw_srt,private_v210_inventory,*,
                                    expected_source_sha256,window_size=20):
    """Return private exchange plus hash/count-only HOLD receipt.

    Never present the exchange as historical owner V176 or as an approved
    set of financial facts. A quote-bearing cue may still contain MORE
    meanings than the 57 hypotheses; all other cues stay UNRESOLVED.
    """
    require(type(window_size) is int and 1<=window_size<=1000,
            "WINDOW_SIZE")
    summary=audit_private_e2_source_first_inventory(
        raw_srt,private_v210_inventory,
        expected_source_sha256=expected_source_sha256)
    source,manifest=make_original_plan(
        raw_srt,private_v210_inventory["video_id"],
        expected_source_sha256=expected_source_sha256,
        window_size=window_size)
    require(source.source_sha256==summary["source_sha256"] and
            len(source.cues)==summary["original_cues_checked"],
            "SOURCE_PLAN_AND_INVENTORY_DIFFER")
    indexed=defaultdict(list)
    atoms=[]
    blocked=[]
    labels={}
    for ordinal,c in enumerate(private_v210_inventory["claims"],1):
        cid=f"C{ordinal:05d}"
        primary=c["anchors"][0]["cue_index"]
        context=sorted(set(x["cue_index"] for x in c["anchors"])|
                       set(c["condition_anchor_cues"])|
                       set(c["exception_anchor_cues"]))
        quotes=[source.cues[i-1].text for i in context]
        missing=_missing_numbers(c["proposition_unverified"],quotes)
        blockers=[]
        if missing:
            blockers.append("UNSPOKEN_PROPOSITION_NUMBER")
        if set(c["risks"]) & BLOCK_RISKS:
            blockers.append("DERIVED_OR_UNSPOKEN_MATH")
        if blockers:
            blocked.append({
                "provisional_id":c["provisional_id"],
                "reason_codes":sorted(set(blockers)),
                "source_primary_cue_index":primary,
            })
            continue
        # A source quote proves only that these ORIGINAL words exist;
        # it does NOT prove the ChatGPT proposition is semantically correct.
        refs=[{"cue_index":primary,
               "quote":source.cues[primary-1].text}]
        num_refs=[{"cue_index":i,"token":value}
                  for i in context
                  for value in NUMBER.findall(source.cues[i-1].text)]
        atom={
            "claim_id":cid,
            "owner_window_id":source.owner(primary),
            "proposition":c["proposition_unverified"],
            "kind":c["kind"],
            "stance":"UNRESOLVED",
            "speaker":"UNKNOWN",
            "source_refs":refs,
            "context_cue_indices":context,
            "condition_cue_indices":c["condition_anchor_cues"],
            "exception_cue_indices":c["exception_anchor_cues"],
            "numeric_references":num_refs,
            "as_of":None,
        }
        indexed[primary].append(cid)
        atoms.append(atom)
        labels[cid]=c["provisional_id"]
    cue_rows=[]
    for cue in source.cues:
        candidates=sorted(indexed[cue.index])
        cue_rows.append({
            "cue_index":cue.index,
            "cue_text_sha256":sha256(cue.text.encode("utf-8")),
            "disposition":"CANDIDATES" if candidates else "UNRESOLVED",
            "claim_ids":candidates,
            "numeric_tokens":NUMBER.findall(cue.text),
            "note":("V210 검토자의 원문 연결 후보이며 의미 승인 아님"
                    if candidates else
                    "원자 누락 여부가 아직 판정되지 않아 UNRESOLVED"),
        })
    exchange={
        "schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
        "video_id":source.video_id,
        "source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "cue_dispositions":cue_rows,
        "atoms":atoms,
    }
    native=audit_host_atomic_exchange(source,exchange)
    require(native["proposed_atomic_claims"]==len(atoms) and
            len(atoms)+len(blocked)==len(
                private_v210_inventory["claims"]) and
            all(a["stance"]=="UNRESOLVED" and
                a["speaker"]=="UNKNOWN" for a in atoms),
            "NATIVE_DRAFT_CENSUS_OR_AUTHORITY_DRIFT")
    # Original source is NOT a gold set, and no historical V176 event has
    # been submitted or revised by this source-only reconstruction.
    receipt={
        "schema":SCHEMA,
        "real_source_sha256":source.source_sha256,
        "v210_review_sha256":json_digest(private_v210_inventory),
        "manifest_sha256":source.manifest_sha256,
        "native_v6_atom_sha256":native["atom_candidate_digest"],
        "native_v6_cue_dispositions_sha256":
            native["cue_disposition_digest"],
        "actual_original_cues_audited":len(source.cues),
        "owner_windows":len(source.primary_windows),
        "v210_source_first_proposals":len(private_v210_inventory["claims"]),
        "native_v6_unapproved_proposals_staged":len(atoms),
        "blocked_unspoken_derived_proposals":len(blocked),
        "blocked_proposal_ids":[x["provisional_id"] for x in blocked],
        "blocked_proposal_reason_codes":[x["reason_codes"] for x in blocked],
        "cues_with_native_provisional_claims":
            sum(bool(r["claim_ids"]) for r in cue_rows),
        "cues_left_unresolved":sum(
            r["disposition"]=="UNRESOLVED" for r in cue_rows),
        "source_explicit_provisional_condition_cue_links":sum(
            len(a["condition_cue_indices"]) for a in atoms),
        "source_explicit_provisional_exception_cue_links":sum(
            len(a["exception_cue_indices"]) for a in atoms),
        "speaker_and_stance_source_finalized":False,
        "old_v179_v181_v176_private_owner_recovered":False,
        "original_v176_owner_journal_mutated":False,
        "independent_gold_or_real_recall_verified":False,
        "unresolved_cues_cannot_be_assumed_noatom":True,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "knowledge_written":False,
    }
    return exchange,receipt


def summarize_candidate_overlap(private_v210_inventory):
    """Flag overlapping candidate cue spans for explicit ChatGPT equivalence.

    Overlap is a RETRIEVAL cue, never an automatic dedup/ground-truth label.
    """
    cs=private_v210_inventory["claims"]
    pairs=[]
    for i,a in enumerate(cs):
        for b in cs[i+1:]:
            x=set(range(a["start_cue"],a["end_cue"]+1))
            y=set(range(b["start_cue"],b["end_cue"]+1))
            overlap=sorted(x&y)
            if overlap:
                pairs.append({"a":a["provisional_id"],"b":b["provisional_id"],
                              "overlap_cues":overlap,
                              "source_semantic_equivalence_verified":False})
    return {
        "schema":"IRE_V214_E2_PRIVATE_ATOM_OVERLAP_REVIEW_QUEUE_V1",
        "source_sha256":private_v210_inventory["source_sha256"],
        "candidate_claims":len(cs),
        "overlapping_cue_candidate_pairs":len(pairs),
        "pairs":pairs,
        "lexical_overlap_not_equivalence":True,
        "independent_gold":False,
        "no_atoms_merged_or_deleted":True,
        "e2_final_pass":False,
    }
