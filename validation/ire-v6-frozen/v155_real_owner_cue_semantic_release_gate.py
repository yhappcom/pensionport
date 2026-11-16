"""V155 public owner-original research custody; real owner replay is separate.

All reported real native host and ChatGPT review results are pinned by SHA
of the *private user Library packet*. Public CI cannot read owner-private SRT
and never certifies 95/98, zero high-risk false negatives, V123, V128, or
personalized advice. A private caller may additionally audit packet bytes.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
import re
import zipfile

SCHEMA="V155_REAL_OWNER_75_CUE_ADJUDICATION_284_ATOMS_V123_HOLD_PUBLIC_V1"
STATUS=("SOURCE_FIRST_75_RECHECK_COMPLETE_13_AUDIO_OR_FACT_HOLD__"
        "NATIVE_13_HOST_PASS__V123_V128_NO_GO")
SOURCE="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
HEX=re.compile(r"[a-f0-9]{64}\Z")
REMAINING=[307,390,522,622,717,797,849,850,852,943,947,965,1221]
SHA_FILES={
 "private_75_notes_sha256":"private/V155_PRIVATE_75_FINAL_SOURCE_FIRST_CONTEXT_DISPOSITIONS.json",
 "private_108_census_sha256":"private/V155_PRIVATE_108_TOTAL_DISPOSITIONS.json",
 "private_13_residual_details_sha256":"private/V155_PRIVATE_FINAL_13_HIGH_CONSEQUENCE_UNRESOLVED_CUES.json",
 "private_b0001_14_review_sha256":"private/V155_PRIVATE_B0001_13_ATOM_SEMANTIC_CHAT_REVIEW_HOLD.json",
 "private_13_v6_host_receipts_sha256":"private/V155_PRIVATE_REAL_13_NATIVE_HOST_RECEIPTS.json",
 "private_13_v123_hold_sha256":"private/V155_PRIVATE_REAL_V123_13_HOLD_SUMMARY.json",
 "private_v128_zero_release_sha256":"private/V155_PRIVATE_REAL_V128_NO_PARTIAL_PUBLISH.json"
}

class V155NoFalseRelease(ValueError):
    pass

def _req(ok,what):
    if not ok: raise V155NoFalseRelease("V155_"+what)

def _sha(content): return sha256(content).hexdigest()

def audit_v155_public_hold(p):
    _req(type(p) is dict and p.get("schema")==SCHEMA,"SCHEMA")
    _req(p.get("status")==STATUS and p.get("review_as_of")=="2026-11-17","STATUS")
    _req(p.get("video_id")=="5NvtBlmt93Y" and
         p.get("original_source_sha256")==SOURCE,"ORIGINAL_SOURCE")
    exact={
      "original_cues":1481,"parent_scopes":13,"v154_pending_cues":75,
      "v155_source_first_cues_examined":75,"v155_new_links_to_source_pinned_atoms":57,
      "v155_new_no_independent_atom_cues":5,"v155_still_unresolved_from_75":13,
      "original_108_queue_now_claim_linked":72,
      "original_108_queue_now_no_atom":23,
      "original_108_queue_now_unresolved":13,"original_108_total":108,
      "prior_v154_provisional_atoms":278,"revised_provisional_atoms":284,
      "newly_added_v155_atoms":6,"b0001_original_source_first_meaning_adjudications":14,
      "native_v6_host_committed_scopes":13,
      "native_v6_idempotent_replay_scopes":13,"native_v123_scope_checks_executed":13,
      "native_v123_approved_scopes":0,"v1271_child_hold_checkpoints":13,
      "actual_v128_parent_publications":0,
      "actual_v128_approved_knowledge_items":0,
      "finance_lexical_floor_unapproved_items":127,
    }
    for key,n in exact.items():
        _req(type(p.get(key)) is int and p[key]==n,"COUNT_"+key.upper())
    _req(p["v155_new_links_to_source_pinned_atoms"]+
         p["v155_new_no_independent_atom_cues"]+
         p["v155_still_unresolved_from_75"] == 75, "75_CUE_PARTITION")
    _req(p["original_108_queue_now_claim_linked"]+
         p["original_108_queue_now_no_atom"]+
         p["original_108_queue_now_unresolved"] == 108, "108_CUE_PARTITION")
    _req(p["prior_v154_provisional_atoms"]+
         p["newly_added_v155_atoms"]==p["revised_provisional_atoms"],
         "284_ATOM_CENSUS")
    _req(p.get("unresolved_source_cue_indices")==REMAINING,"13_CUE_INDEX_CENSUS")
    for key in ("b0001_formal_v123_pass",
        "blind_gold_whole_video_complete","precision95_recall98_proven",
        "high_risk_fn_zero_proven","verified_approved_knowledge_advice",
        "individual_2026_eligibility_verified",
        "owner_inventory_externally_authenticated","p0e_go"):
        _req(p.get(key) is False,"FALSE_RELEASE_"+key.upper())
    _req(p.get("no_independent_gold_measured") is True,"NO_GOLD_CERTIFICATION")
    for key in ("full_private_packet_sha256",)+tuple(SHA_FILES):
        s=p.get(key)
        _req(type(s) is str and HEX.fullmatch(s) is not None,
             "MISSING_PRIVATE_SHA_"+key.upper())
    return {
      "owner_original_scope":1481, "source_first_reexamined":75,
      "provisional_claims":284, "original_108_remaining_open":13,
      "private_native_v6_host":13,"v123_final_pass":0,
      "v128_published":0,"gold_precision_recall_certified":False,
      "personal_advice_approved":False,"p0e_go":False
    }

def audit_v155_actual_private_zip(p,raw_owner_packet_bytes):
    """Optional local proof; NOT executed using private owner data in CI."""
    audit_v155_public_hold(p)
    _req(type(raw_owner_packet_bytes) is bytes and
         _sha(raw_owner_packet_bytes)==p["full_private_packet_sha256"],
         "PRIVATE_ZIP_HASH")
    with zipfile.ZipFile(BytesIO(raw_owner_packet_bytes)) as z:
        _req(z.testzip() is None,"PRIVATE_ZIP_CRC")
        names=set(z.namelist())
        _req("private/owner_1481_original.srt" not in names,
             "DUPLICATED_PRIVATE_ORIGINAL_SRT")
        for key,path in SHA_FILES.items():
            _req(path in names and _sha(z.read(path))==p[key],
                 "PRIVATE_FILE_HASH_"+key.upper())
        source_rows=json.loads(z.read(SHA_FILES["private_75_notes_sha256"]))
        _req(type(source_rows) is list and len(source_rows)==75 and
             len({r["cue_index"] for r in source_rows})==75,
             "75_NOTES_DUPLICATED")
        _req(Counter(r["disposition"] for r in source_rows)=={
            "CANDIDATES":57,"NO_ATOM":5,"UNRESOLVED":13
        },"75_NOTES_PARTITION")
        _req({r["cue_index"] for r in source_rows if
              r["disposition"]=="UNRESOLVED"}==set(REMAINING),
              "UNRESOLVED_MASQUERADING")
        _req(all(r["chat_final_approved"] is False and
                 r["independent_gold_certified"] is False for r in source_rows),
                 "FALSE_75_APPROVAL")
        r108=json.loads(z.read(SHA_FILES["private_108_census_sha256"]))
        _req(len(r108)==108 and Counter(r["source_first_disposition"]
             for r in r108)=={"CANDIDATES":72,"NO_ATOM":23,"UNRESOLVED":13},
             "108_ORIGINAL_CUE_CENSUS")
        b1=json.loads(z.read(SHA_FILES["private_b0001_14_review_sha256"]))
        _req(len(b1)==14 and all(r["actual_v123_final_acceptance"] is False
             for r in b1),"B0001_FALSE_FINAL_APPROVAL")
        hosts=json.loads(z.read(SHA_FILES["private_13_v6_host_receipts_sha256"]))
        _req(len(hosts)==13 and
             len({x["segment_id"] for x in hosts})==13 and
             sum(x["candidate_atoms"] for x in hosts)==284 and
             all(x["V6_native_host_committed"] is True and
                 x["idempotence_replay_pass"] is True for x in hosts),
             "ACTUAL_PRIVATE_V6_CENSUS")
        v123=json.loads(z.read(SHA_FILES["private_13_v123_hold_sha256"]))
        v128=json.loads(z.read(SHA_FILES["private_v128_zero_release_sha256"]))
        _req(v123["v123_approved_scopes"]==0 and
             v123["atom_candidates_open"]==284 and
             v123["v123_release_attempts_rejected"]==13,"V123_APPROVAL_LAUNDERING")
        _req(v128["V128_actual_knowledge_publications"]==0 and
             v128["private_knowledge_entries"]==0 and
             v128["knowledge_ledger_events"]==0,"V128_PARTIAL_PUBLICATION")
    return {"private_packet_hash_verified":True,"real_v6_host_receipts":13,
            "open_original_cues":13,"research_approved_scopes":0,
            "research_published":0,"p0e_go":False}
