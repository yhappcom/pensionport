"""Private source-first provisional research audit; NO independent semantic gold.

This API verifies integrity of an original-SRT-grounded, non-blind first-pass
research candidate ledger and optional *topic-only* native crosswalk. It
cannot judge semantic entailment or the completeness of atomic claims and
must never emit independent precision, recall, FN or financial approval.

Pass previously pinned SOURCE/CANDIDATE/NATIVE/CROSSWALK SHA digests from an
independent owner receipt, not hashes recomputed from untrusted inputs alone.
Private quotes and source text are not returned or written to public logs.
"""
from __future__ import annotations

from collections import defaultdict
import json
import re

from .codec import require_hash, sha256
from .errors import InvalidInput
from .source import parse_srt

PROVISIONAL_SCHEMA = "IRE_P205_SOURCE_ONLY_PROVISIONAL_ATOMS_UNBLINDED_CHAT_REVIEW_V1"
CROSSWALK_SCHEMA = "IRE_P205_SAME_CHAT_SOURCE71_NATIVE68_DIAGNOSTIC_RELATIONS_NON_GOLD_V1"
ATOM_KINDS = {"FACT", "OPINION", "QUESTION", "HYPOTHETICAL", "RECOMMENDATION", "CALCULATION"}
RISK_KINDS = {"LOW", "FINANCE", "TEMPORAL", "HIGH"}
CUE_KINDS = {"CONTEXT_OR_PRIMARY_FOR_PROVISIONAL_ATOMS", "NONCLAIM_DISCUSSION",
             "SOURCE_CONTEXT_OPEN_NO_NEGATIVE_GOLD"}
CANDIDATE_ID = re.compile(r"P205-SRC-\d{3,6}\Z")


def _deny(code):
    raise InvalidInput("P205_SOURCE_FIRST_" + code)


def _raw_json(raw, *, expected_sha256, label):
    if type(raw) is not bytes or sha256(raw) != require_hash(expected_sha256, label):
        _deny(label + "_SHA_MISMATCH")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, ValueError, TypeError) as exc:
        raise InvalidInput("P205_SOURCE_FIRST_" + label + "_JSON_INVALID") from exc
    if type(value) is not dict:
        _deny(label + "_ROOT_NOT_OBJECT")
    return value


def _source_digest_cues(original_srt, *, expected_source_sha256):
    if type(original_srt) is not bytes or sha256(original_srt) != require_hash(expected_source_sha256,"ORIGINAL_SRT"):
        _deny("ORIGINAL_SRT_SHA_MISMATCH")
    cues = parse_srt(original_srt)
    blocks = re.split(r"\n\s*\n", original_srt.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").strip())
    if len(blocks) != len(cues):
        _deny("BLOCK_COUNT_DRIFT")
    return cues, [sha256(block.encode("utf8")) for block in blocks]


def verify_source_first_draft(original_srt: bytes, candidate_raw: bytes, *,
                              expected_source_sha256: str,
                              expected_candidate_sha256: str,
                              expected_cues: int | None = None,
                              expected_candidates: int | None = None):
    """Byte/quote/relation audit only, never an independent atomic truth review."""
    cues, blocks = _source_digest_cues(original_srt, expected_source_sha256=expected_source_sha256)
    document = _raw_json(candidate_raw,expected_sha256=expected_candidate_sha256,label="DRAFT")
    if (document.get("schema") != PROVISIONAL_SCHEMA or
        document.get("source_srt_sha256") != expected_source_sha256 or
        document.get("gold_status") != "PROVISIONAL_SOURCE_READING_NOT_INDEPENDENT_GOLD" or
        document.get("semantic_reviewer") != "SAME_CHATGPT_CONVERSATION_NONINDEPENDENT"):
        _deny("CANNOT_DECLARE_GOLD_OR_REVIEWER_INDEPENDENCE")
    for field in ("speaker_audio_authenticated", "fully_independent_source_blind",
                  "second_blind_reviewer_verified", "owner_finance_truth_certified"):
        if document.get(field) is not False:
            _deny("FORBIDDEN_FINANCIAL_OR_INDEPENDENCE_PROMOTION_" + field)
    for field in ("measured_atomic_precision", "measured_atomic_recall", "measured_high_risk_FN"):
        if document.get(field) is not None:
            _deny("FALSE_GOLD_METRIC_" + field)
    if expected_cues is not None and (type(expected_cues) is not int or len(cues) != expected_cues):
        _deny("EXPECTED_CUE_COUNT_DRIFT")
    atoms=document.get("provisional_atoms")
    rows=document.get("cue_coverage")
    if type(atoms) is not list or not atoms or type(rows) is not list:
        _deny("EMPTY_CANDIDATE_OR_CUE_LEDGER")
    if len(rows) != len(cues) or document.get("reviewed_original_cue_count") != len(cues):
        _deny("CUE_250_COVERAGE_NOT_COMPLETE")
    if expected_candidates is not None and (type(expected_candidates) is not int or
                                             len(atoms) != expected_candidates):
        _deny("EXPECTED_ATOMIC_CANDIDATE_COUNT_DRIFT")
    if document.get("source_provisional_atom_count") != len(atoms):
        _deny("CANDIDATE_CENSUS_DRIFT")
    expected_links=defaultdict(set)
    seen=set()
    high=0
    primary=set()
    for atom in atoms:
        if type(atom) is not dict:
            _deny("ATOMIC_CANDIDATE_NOT_OBJECT")
        cid=atom.get("candidate_id")
        if type(cid) is not str or CANDIDATE_ID.fullmatch(cid) is None or cid in seen:
            _deny("BAD_OR_DUPLICATE_CANDIDATE_ID")
        seen.add(cid)
        if atom.get("kind") not in ATOM_KINDS or atom.get("risk_scope") not in RISK_KINDS:
            _deny("CANDIDATE_KIND_OR_RISK_INVALID")
        if any(type(atom.get(k)) is not str or not atom[k].strip() for k in
               ("source_proposition", "qualifier_or_unresolved_issue")):
            _deny("MISSING_CLAIM_OR_CAVEAT")
        if (atom.get("speaker_audio_authenticated") is not False or
            atom.get("source_semantic_provisional") is not True or
            atom.get("proposition_externally_financial_verified") is not False or
            atom.get("independent_blind_gold_certified") is not False):
            _deny("FALSE_ATOMIC_PROVENANCE_OR_GOLD")
        span=atom.get("source_span",{})
        primary_ref=atom.get("primary_quote",{})
        if type(span) is not dict or type(primary_ref) is not dict:
            _deny("CLAIM_SPAN_OR_QUOTE_INVALID")
        low,high_idx=span.get("first_cue"),span.get("last_cue")
        idx=primary_ref.get("cue_index")
        if (type(low) is not int or type(high_idx) is not int or type(idx) is not int or
            not 1 <= low <= idx <= high_idx <= len(cues)):
            _deny("CLAIM_SPAN_OR_QUOTE_OUTSIDE_SOURCE")
        if (primary_ref.get("quote") != cues[idx-1].text or
            primary_ref.get("quote_sha256") != sha256(cues[idx-1].text.encode("utf8")) or
            primary_ref.get("cue_block_sha256") != blocks[idx-1]):
            _deny("QUOTE_CUE_BYTES_UNVERIFIED")
        primary.add(idx)
        high+= int(atom["risk_scope"] == "HIGH")
        for n in range(low,high_idx+1):
            expected_links[n].add(cid)
    if document.get("source_provisional_high_risk_atom_count") != high:
        _deny("HIGH_RISK_CENSUS_DRIFT")
    actual_counts=defaultdict(int)
    for j,row in enumerate(rows,1):
        if type(row) is not dict or type(row.get("cue_index")) is not int or row["cue_index"]!=j:
            _deny("CUE_INDEX_GAP_DUPLICATE_OR_ORDER_DRIFT")
        if (row.get("cue_sha256") != blocks[j-1] or
            row.get("quote_sha256") != sha256(cues[j-1].text.encode("utf8"))):
            _deny("CUE_RAW_BLOCK_OR_QUOTE_HASH_DRIFT")
        role=row.get("source_provisional_status")
        if role not in CUE_KINDS or not isinstance(row.get("status_reason"),str) or not row["status_reason"].strip():
            _deny("CUE_ROLE_OR_REASON_MISSING")
        links=row.get("provisional_candidate_ids")
        if (type(links) is not list or any(type(s) is not str for s in links) or
            len(links)!=len(set(links)) or set(links)!=expected_links[j]):
            _deny("CUE_CONTEXT_LINKS_LOST_OR_FABRICATED")
        if role == "CONTEXT_OR_PRIMARY_FOR_PROVISIONAL_ATOMS" and not links:
            _deny("UNMAPPED_CUE_SELF_DECLARED_COVERED")
        if role == "SOURCE_CONTEXT_OPEN_NO_NEGATIVE_GOLD" and links:
            _deny("SOURCE_CUE_INCONSISTENT_OPEN_CONTEXT")
        if role == "NONCLAIM_DISCUSSION" and j in primary:
            _deny("PRIMARY_FINANCIAL_CLAIM_SILENCED_AS_NONCLAIM")
        if row.get("independent_review_done") is not False or row.get("no_unmodelled_claims_certified") is not False:
            _deny("FALSE_REVIEW_COMPLETION_OR_RECALL")
        actual_counts[role]+=1
    if document.get("source_cue_status_counts")!=dict(actual_counts):
        _deny("CUE_ROLE_CENSUS_DRIFT")
    if document.get("unlinked_cue_indices")!=[
        i for i,row in enumerate(rows,1) if row["source_provisional_status"]=="SOURCE_CONTEXT_OPEN_NO_NEGATIVE_GOLD"]:
        _deny("UNLINKED_REVIEW_QUEUE_DRIFT")
    return {
        "schema":"IRE_V6_P205_SOURCE_FIRST_PROVISIONAL_REPLAY_RECEIPT_V1",
        "original_source_sha256":expected_source_sha256,
        "frozen_provisional_candidate_json_sha256":expected_candidate_sha256,
        "source_cue_hashes_verified":len(cues),
        "source_cue_roles_reconciled":len(rows),
        "provisional_candidate_quote_hashes_verified":len(atoms),
        "provisional_high_risk_candidate_count":high,
        "source_quote_and_context_hash_mismatch_count":0,
        "source_first_semantic_exhaustiveness_independently_verified":False,
        "provisional_claims_independently_verified":False,
        "true_atomic_gold_count":0,
        "independent_atomic_precision":None,
        "independent_atomic_recall":None,
        "independent_high_risk_false_negative_count":None,
        "e2_approved":False,"e3_e4_e5_approved":False,"p0_go":False,
        "outcome":"SOURCE_FIRST_QUOTE_AND_CUE_COVERAGE_PASS_MEANING_AND_GOLD_HOLD",
    }


def verify_diagnostic_topic_crosswalk(native_raw: bytes,candidate_raw: bytes,crosswalk_raw: bytes,*,
                                       expected_native_sha256: str,
                                       expected_candidate_sha256: str,
                                       expected_crosswalk_sha256: str):
    """Validate a frozen topic-link relation; do not interpret as gold TP."""
    draft=_raw_json(candidate_raw,expected_sha256=expected_candidate_sha256,label="DRAFT")
    c=_raw_json(crosswalk_raw,expected_sha256=expected_crosswalk_sha256,label="CROSSWALK")
    n=_raw_json(native_raw,expected_sha256=expected_native_sha256,label="ORIGINAL_NATIVE")
    if (c.get("schema")!=CROSSWALK_SCHEMA or
        c.get("provisional_source_first_json_sha256")!=expected_candidate_sha256 or
        c.get("native_v228_json_sha256")!=expected_native_sha256 or
        c.get("source_srt_sha256")!=draft.get("source_srt_sha256") or
        c.get("is_gold") is not False or
        c.get("is_independent_review") is not False or
        c.get("automatic_gold_matching_approved") is not False or
        c.get("all_250_cue_atomic_exhaustiveness_proven") is not False or
        c.get("metrics_must_remain_null") is not True):
        _deny("CROSSWALK_COULD_LAUNDER_GOLD")
    original=n.get("atoms");source=draft.get("provisional_atoms")
    bynative={a["claim_id"]:a for a in original} if type(original) is list else {}
    bysource={a["candidate_id"]:a for a in source} if type(source) is list else {}
    if (len(bynative)!=len(original) or len(bysource)!=len(source) or
        type(c.get("source_to_native_related_review_only")) is not list or
        type(c.get("native_to_source_related_review_only")) is not list or
        len(c["source_to_native_related_review_only"])!=len(bysource) or
        len(c["native_to_source_related_review_only"])!=len(bynative)):
        _deny("CROSSWALK_CARDINALITY_OR_DUPLICATE_ID_DRIFT")
    expected_inverse=defaultdict(set)
    seen_source=set()
    mismatches=[];more_than_one_natives=0;unlinked=0
    for row in c["source_to_native_related_review_only"]:
        cid=row.get("source_provisional_id")
        if cid not in bysource or cid in seen_source:
            _deny("CROSSWALK_SOURCE_CANDIDATE_DUPLICATED_OR_UNKNOWN")
        seen_source.add(cid)
        if row.get("source_kind")!=bysource[cid].get("kind") or row.get("source_risk")!=bysource[cid].get("risk_scope"):
            _deny("CROSSWALK_SOURCE_ID_KIND_OR_RISK_CHANGED")
        ids=row.get("native_related_claim_ids_for_review_only")
        if type(ids) is not list or len(set(ids))!=len(ids) or any(x not in bynative for x in ids):
            _deny("CROSSWALK_NATIVE_REFERENCE_INVALID")
        if row.get("independently_gold_aligned") is not False or row.get("true_positive_match") is not None:
            _deny("CROSSWALK_FALSE_TRUE_POSITIVE_OR_GOLD")
        if row.get("requires_one_to_many_candidate_split_review") != (len(ids)>1) or row.get("source_new_candidate_missing_standalone_native") != (len(ids)==0):
            _deny("CROSSWALK_SPLIT_OR_UNLINKED_FLAG_DRIFT")
        if row.get("source_quote_cue")!=bysource[cid]["primary_quote"]["cue_index"]:
            _deny("CROSSWALK_QUOTE_ANCHOR_CHANGED")
        if row.get("same_kind_as_all_related") != (all(bynative[x].get("kind")==bysource[cid].get("kind") for x in ids) if ids else None):
            _deny("CROSSWALK_KIND_COMPARISON_FALSIFIED")
        for dest in ids:
            expected_inverse[dest].add(cid)
            if bysource[cid]["kind"]!=bynative[dest].get("kind"):
                mismatches.append((cid,dest))
        more_than_one_natives += (len(ids)>1)
        unlinked += (len(ids)==0)
    seen_native=set()
    for row in c["native_to_source_related_review_only"]:
        cid=row.get("native_claim_id")
        if cid not in bynative or cid in seen_native:
            _deny("NATIVE_CLAIM_UNKNOWN_OR_DUPLICATED")
        seen_native.add(cid)
        if (set(row.get("source_provisional_related_ids",()))!=expected_inverse[cid] or
            row.get("related_to_multiple_source_atoms")!=(len(expected_inverse[cid])>1) or
            row.get("independent_atomic_alignment_complete") is not False or
            row.get("gold_truth_label") is not None):
            _deny("CROSSWALK_REVERSE_LINK_DRIFT_OR_GOLD_FORGERY")
    summaries=c.get("summary",{})
    if (summaries.get("source_candidate_count")!=len(bysource) or
        summaries.get("original_frozen_native_count")!=len(bynative) or
        summaries.get("source_candidate_without_separate_native_topic_link")!=unlinked or
        summaries.get("unlinked_native_candidates")!=len(set(bynative)-set(expected_inverse)) or
        summaries.get("source_candidates_related_to_multiple_native_claims")!=more_than_one_natives or
        summaries.get("native_candidates_related_to_multiple_source_candidates")!=sum(len(x)>1 for x in expected_inverse.values()) or
        summaries.get("provisional_source_native_kind_disagreements_in_related_pairs")!=len(mismatches) or
        any(summaries.get(key) is not None for key in ("actual_TP","actual_FP","actual_FN","actual_high_risk_FN","precision","recall"))):
        _deny("CROSSWALK_SUMMARY_OR_FALSE_METRIC")
    listed={(x.get("source_candidate_id"),x.get("native_claim_id")) for x in c.get("provisional_kind_disagreement_pairs",[])}
    if listed!=set(mismatches) or len(listed)!=len(c.get("provisional_kind_disagreement_pairs",[])):
        _deny("CROSSWALK_MISMATCHES_HIDDEN")
    return {"schema":"IRE_V6_P205_TOPIC_CROSSWALK_CONSISTENCY_V1",
            "source_candidate_count":len(bysource),"original_native_candidate_count":len(bynative),
            "source_candidates_without_native_topic_link":unlinked,
            "kind_disagreement_related_pairs":len(mismatches),
            "crosswalk_is_independent_gold":False,
            "independent_precision":None,"independent_recall":None,
            "independent_high_risk_false_negative_count":None,
            "p0_go":False,"status":"TOPIC_LINKS_REPLAYED_NOT_GOLD"}
