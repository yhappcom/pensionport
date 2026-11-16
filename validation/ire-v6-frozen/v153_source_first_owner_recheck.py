"""V153 owner-private source-first 202 review and 108 unresolved cue custody gate.

Public CI can ONLY verify the SHA-only manifest and synthetic negatives. A
separate private rerun must provide original bytes, V145 atom dictionary,
V152 UNRESOLVED cue rows, and the 160+108+42 source-first notes.

Review-note completion is NOT blind gold, not a corrected V6 atomic exchange,
not a native host receipt, and not an authorized V123/V128 research release.
"""
from __future__ import annotations

import hashlib
import json
import re

SHA64 = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = "V153_SOURCE_FIRST_160_AND_108_OWNER_PRIVATE_HOLD_V1"
REVIEW_SCHEMA = "V153_SOURCE_FIRST_CHAT_SEMANTIC_NONBLIND_ROW_V1"
CUE_SCHEMA = "V153_SOURCE_UNRESOLVED_CUE_TRIAGE_V1"
HOLD_STATUS = "SOURCE_FIRST_CHAT_CONTEXT_NOTES_COMPLETE_FOR_202_PENDING__V123_GOLD_HOST_HOLD"


class V153SourceReviewError(ValueError):
    pass


def _check(ok, why):
    if not ok:
        raise V153SourceReviewError("V153_" + why)


def digest(value):
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def audit_public_sha_only(manifest):
    """Count/hash/status consistency; does not open original SRT."""
    _check(type(manifest) is dict and manifest.get("schema") == SCHEMA, "SCHEMA")
    _check(manifest.get("original_video_id") == "5NvtBlmt93Y", "VIDEO")
    _check(manifest.get("original_source_sha256") ==
           "638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d",
           "SOURCE")
    for key, number in {
        "source_cue_count": 1481,
        "source_scopes": 13,
        "original_V146_meaning_pending": 202,
        "V1521_focused_meaning_notes": 42,
        "V153_additional_source_first_chat_notes": 160,
        "pending_claims_with_chat_risk_notes_total": 202,
        "unresolved_cue_source_triages": 108,
        "remaining_unresolved_cue_V6_dispositions": 108,
        "v145_atom_count": 274,
        "v152_provisional_atom_count": 276,
        "native_host_v6_commit_receipts_new": 0,
        "v123_chat_final_approved_scopes": 0,
        "v128_parent_published": 0,
    }.items():
        _check(type(manifest.get(key)) is int and manifest[key] == number,
               "FALSE_COUNT_" + key.upper())
    _check(manifest["V1521_focused_meaning_notes"] +
           manifest["V153_additional_source_first_chat_notes"] ==
           manifest["original_V146_meaning_pending"],
           "202_NOTE_PARTITION")
    for key in ("private_160_notes_sha256", "private_108_cues_sha256",
                "previous_42_notes_sha256", "combined_pending_202_notes_hash"):
        _check(type(manifest.get(key)) is str and SHA64.fullmatch(manifest[key]) is not None,
               "PRIVATE_DIGEST_" + key.upper())
    _check(manifest.get("no_independent_gold_scored") is True,
           "NOT_BLIND_GOLD")
    for key in ("full_atomic_precision_recall_certified",
                "high_risk_false_negative_zero_certified",
                "approved_video_knowledge_based_advice_tested",
                "individual_tax_eligibility_approved", "p0e_go", "p0_go"):
        _check(manifest.get(key) is False, "FALSE_APPROVAL_" + key.upper())
    _check(manifest.get("status") == HOLD_STATUS, "STATUS")
    return {
        "source_first_chat_pending_claim_notes": 202,
        "still_v123_final_pending_claims": 202,
        "private_unresolved_cue_recheck": 108,
        "native_host_receipts_new": 0,
        "gold_precision_or_recall_measured": False,
        "high_risk_false_negative_zero_proven": False,
        "v123_scopes_approved": 0, "v128_published": 0,
        "p0e_go": False,
        "status": "V153_SOURCE_FIRST_CONTEXT_COMPLETED_GOLD_AND_RELEASE_HOLD",
    }


def private_owner_source_recheck(manifest, original_srt_bytes, owner_cue_text_by_index,
                                 v145_atoms_by_id, v152_unresolved_cue_by_id,
                                 prior42, reviewed160, triaged108):
    """Verify original literal quotes, surrounding SHA and exact private set.

    Does not make a semantic verdict; ChatGPT has supplied those judgments in
    the private packet. The private owner must replay its actual source and
    assess, correct and finally sign V123 before any V128 publication.
    """
    audit_public_sha_only(manifest)
    _check(type(original_srt_bytes) is bytes and
           hashlib.sha256(original_srt_bytes).hexdigest() ==
           manifest["original_source_sha256"], "REAL_RAW_SRT_HASH_REQUIRED")
    try:
        blocks = re.split(r"\r?\n\r?\n",
                          original_srt_bytes.decode("utf-8-sig").strip())
        parsed = {}
        for block in blocks:
            rows = block.splitlines()
            i = int(rows[0])
            _check(i not in parsed and len(rows) >= 3, "SRT_DUP_OR_EMPTY_CUE")
            parsed[i] = " ".join(rows[2:])
    except (UnicodeError, ValueError, IndexError) as exc:
        raise V153SourceReviewError("V153_SRT_PARSE_ORIGINAL_FAILED") from exc
    _check(parsed == owner_cue_text_by_index and
           set(parsed) == set(range(1, 1482)), "RAW_SOURCE_CUE_TEXT_DRIFT")
    _check(type(owner_cue_text_by_index) is dict and
           set(owner_cue_text_by_index) == set(range(1,1482)), "OWNER_1481_CUES")
    _check(type(v145_atoms_by_id) is dict and len(v145_atoms_by_id) == 274,
           "V145_ATOMS")
    _check(type(v152_unresolved_cue_by_id) is dict and
           len(v152_unresolved_cue_by_id) == 108, "V152_UNRESOLVED")
    _check(type(prior42) is list and len(prior42) == 42 and
           type(reviewed160) is list and len(reviewed160) == 160 and
           type(triaged108) is list and len(triaged108) == 108,
           "PRIVATE_PACKET_CENSUS")
    _check(digest(prior42) == manifest["previous_42_notes_sha256"] and
           digest(reviewed160) == manifest["private_160_notes_sha256"] and
           digest(triaged108) == manifest["private_108_cues_sha256"],
           "OWNER_NOTE_DIGEST")
    previous_ids = [r["claim_id"] for r in prior42]
    ids = [r["claim_id"] for r in reviewed160]
    _check(len(set(previous_ids)) == 42 and len(set(ids)) == 160 and
           not set(previous_ids) & set(ids) and
           set(previous_ids + ids).issubset(v145_atoms_by_id) and
           digest(previous_ids + ids) == manifest["combined_pending_202_notes_hash"],
           "OWNER_PENDING_ID_PARTITION")
    for row in reviewed160:
        cid = row["claim_id"]
        _check(row.get("schema") == REVIEW_SCHEMA and
               row.get("source_sha256") == manifest["original_source_sha256"] and
               row.get("v145_atom_sha256") == digest(v145_atoms_by_id[cid]) and
               row.get("v123_final_approved") is False and
               row.get("externally_independent_gold") is False and
               row.get("official_financial_fact_approved") is False,
               "CLAIM_REVIEW_MASQUERADES_AS_FINAL")
        refs = row["source_context"]
        _check(type(refs) is list and refs and
               refs == v145_atoms_by_id[cid]["source_refs"],
               "CLAIM_QUOTES_CHANGED")
        for r in refs:
            i,quote = r["cue_index"],r["quote"]
            _check(i in owner_cue_text_by_index and quote in owner_cue_text_by_index[i],
                   "OWNER_QUOTE_NOT_PRESENT")
        surrounding = row["source_surrounding_cues"]
        _check(type(surrounding) is list and surrounding and
               digest(surrounding) == row["source_surrounding_sha256"],
               "OWNER_SURROUNDING_SHA")
        for cue in surrounding:
            i=cue["cue_index"]
            _check(owner_cue_text_by_index.get(i) == cue["original_text"] and
                   hashlib.sha256(cue["original_text"].encode()).hexdigest() ==
                   cue["source_sha256"], "OWNER_SURROUNDING_TEXT_TAMPERED")
    triaged_ids = set()
    for row in triaged108:
        i=row["cue_index"]
        _check(row.get("schema")==CUE_SCHEMA and
               i in v152_unresolved_cue_by_id and
               i not in triaged_ids, "UNRESOLVED_DUP_OR_NOT_IN_SOURCE")
        triaged_ids.add(i)
        _check(row.get("raw_cue")==owner_cue_text_by_index[i] and
               row.get("cue_text_sha256") == hashlib.sha256(
                   owner_cue_text_by_index[i].encode()).hexdigest() and
               row.get("cue_text_sha256") ==
               v152_unresolved_cue_by_id[i]["cue_text_sha256"],
               "UNRESOLVED_ORIGINAL_DRIFT")
        _check(row.get("candidate_final_disposition") ==
               "OPEN_SOURCE_FIRST_CHAT_REVIEW_PENDING_HOST" and
               row.get("genuinely_no_claim_certified") is False and
               row.get("high_risk_fn_absence_proven") is False,
               "UNRESOLVED_CUE_FALSE_CLOSED")
        adjoining = row["neighboring_cues"]
        _check(digest(adjoining) == row["neighboring_cues_sha256"], "CUE_ADJACENT_SHA")
        for neighbor in adjoining:
            j=neighbor["cue_index"]
            _check(owner_cue_text_by_index.get(j)==neighbor["original_text"] and
                   hashlib.sha256(neighbor["original_text"].encode()).hexdigest()==
                   neighbor["source_sha256"], "CUE_ADJACENT_TAMPERED")
    _check(triaged_ids == set(v152_unresolved_cue_by_id),
           "UNRESOLVED_QUEUE_INCOMPLETE")
    return {"owner_source_linked_claim_notes": 202,
            "source_unresolved_cue_context_verified": 108,
            "final_V123_approvals": 0, "full_gold": False, "p0e_go": False}
