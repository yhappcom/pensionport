"""Source-first, ChatGPT-hosted candidate atom exchange for pinned private SRT.

This module accepts a host-produced *proposal*, not human gold or verified
financial facts. No external model API. Every original cue requires an explicit
disposition; model self-assessment never certifies recall or semantic truth.
The output contains only counts and SHA digests, no private transcript text.
"""
from __future__ import annotations

import hashlib
import re

from .claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from .codec import WINDOW, canonical, require_hash, require_identifier, sha256
from .errors import InvalidInput

CLAIM = re.compile(r"C[0-9]{5,8}\Z")
# Preserve units even when Korean monetary expressions contain spaces.
# V16 real ISA source exposed "300만 원" -> prior regex counted only "300".
NUMBER = re.compile(
    r"(?<![0-9])(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)"
    r"(?:\.[0-9]+)?(?:\s*(?:%|퍼센트|(?:만|억|조)\s*원|"
    r"원|달러|배|년|개월|월|일))?"
)
KINDS = {"FACT", "HYPOTHETICAL", "QUESTION", "OPINION", "RECOMMENDATION", "MATH"}
STANCES = {"AFFIRMED", "NEGATED", "CORRECTED", "CONDITIONAL", "QUOTED", "UNRESOLVED"}
SPEAKERS = {"NARRATOR", "GUEST", "QUESTIONER", "QUOTED_SOURCE", "UNKNOWN"}
DISPOSITIONS = {"CANDIDATES", "NO_ATOM", "UNRESOLVED"}


def _indices(values, available, name, *, allow_empty=True):
    if type(values) is not list or (not allow_empty and not values):
        raise InvalidInput(name + "_INVALID")
    if (any(type(i) is not int or i not in available for i in values) or
            values != sorted(set(values))):
        raise InvalidInput(name + "_INVALID")
    return values


def _digest_rows(rows):
    """Stream canonical rows, avoiding the 1 MiB *event* serialization bound."""
    h = hashlib.sha256()
    h.update(b"[")
    for i, row in enumerate(rows):
        if i:
            h.update(b",")
        h.update(canonical(row))
    h.update(b"]")
    return h.hexdigest()


def audit_host_atomic_exchange(source, exchange: dict) -> dict:
    """Bind all cue dispositions and atomic candidate frames to original bytes.

    Exact cue coverage is a structural property. Claim count, polarity, role,
    conditions, quotation and all gold labels remain unverified semantics.
    """
    if (type(exchange) is not dict or set(exchange) != {
        "schema", "video_id", "source_sha256", "manifest_sha256",
        "cue_dispositions", "atoms"
    } or exchange["schema"] != "IRE_V6_HOST_ATOMIC_EXCHANGE_V1" or
        exchange["video_id"] != source.video_id or
        exchange["source_sha256"] != source.source_sha256 or
        exchange["manifest_sha256"] != source.manifest_sha256):
        raise InvalidInput("HOST_ATOMIC_SOURCE_IDENTITY_OR_SCHEMA_INVALID")
    records, atoms = exchange["cue_dispositions"], exchange["atoms"]
    allowed = set(range(source.scope_first_cue, source.scope_last_cue + 1))
    if (type(records) is not list or len(records) != len(allowed) or
        type(atoms) is not list or len(atoms) > 10000):
        raise InvalidInput("HOST_ATOMIC_CUE_CENSUS_INCOMPLETE")
    rowmap = {}
    rows = []
    suspicious_no_atom = 0
    unresolved = 0
    risky_context = 0
    for pos, row in enumerate(records):
        idx = source.scope_first_cue + pos
        if (type(row) is not dict or set(row) != {
            "cue_index", "cue_text_sha256", "disposition",
            "claim_ids", "numeric_tokens", "note"
        } or type(row["cue_index"]) is not int or
            row["cue_index"] != idx or
            row["cue_text_sha256"] != sha256(source.cues[idx-1].text.encode("utf-8"))):
            raise InvalidInput("HOST_ATOMIC_CUE_GAP_DUPLICATE_OR_SHA_DRIFT")
        status, ids = row["disposition"], row["claim_ids"]
        if status not in DISPOSITIONS or type(ids) is not list or (
            status == "CANDIDATES" and not ids) or (
            status != "CANDIDATES" and ids) or any(
                type(x) is not str or not CLAIM.fullmatch(x) for x in ids
            ) or ids != sorted(set(ids)):
            raise InvalidInput("HOST_ATOMIC_CUE_DISPOSITION_INVALID")
        if (type(row["note"]) is not str or len(row["note"]) > 256 or
            (status != "CANDIDATES" and len(row["note"].strip()) < 4)):
            raise InvalidInput("HOST_ATOMIC_DISPOSITION_REASON_MISSING")
        numerical = NUMBER.findall(source.cues[idx-1].text)
        if type(row["numeric_tokens"]) is not list or row["numeric_tokens"] != numerical:
            raise InvalidInput("HOST_ATOMIC_NUMERIC_CENSUS_MISMATCH")
        cue = source.cues[idx-1].text
        risky = bool(FINANCIAL.search(cue) or QUALIFIER.search(cue) or MULTI_CLAIM.search(cue))
        suspicious_no_atom += int(status == "NO_ATOM" and risky)
        unresolved += int(status == "UNRESOLVED")
        risky_context += int(bool(QUALIFIER.search(cue)))
        rowmap[idx] = row
        rows.append({
            "cue_index":idx, "cue_sha256":row["cue_text_sha256"],
            "disposition":status, "claim_ids":ids,
            "numeric_count":len(numerical), "risk":risky,
        })
    if len(atoms) > len(allowed) * 64:
        raise InvalidInput("HOST_ATOMIC_EXCESS_CANDIDATES")
    indexed = {}
    for atom in atoms:
        if (type(atom) is not dict or set(atom) != {
            "claim_id", "owner_window_id", "proposition", "kind", "stance",
            "speaker", "source_refs", "context_cue_indices",
            "condition_cue_indices", "exception_cue_indices",
            "numeric_references", "as_of"
        }):
            raise InvalidInput("HOST_ATOM_SCHEMA_INVALID")
        cid = atom["claim_id"]
        if type(cid) is not str or not CLAIM.fullmatch(cid) or cid in indexed:
            raise InvalidInput("HOST_ATOM_DUPLICATE_OR_INVALID_ID")
        indexed[cid] = atom
        if (type(atom["proposition"]) is not str or
            not 5 <= len(atom["proposition"].strip()) <= 3000 or
            atom["kind"] not in KINDS or atom["stance"] not in STANCES or
            atom["speaker"] not in SPEAKERS or
            (atom["as_of"] is not None and
             (type(atom["as_of"]) is not str or
              not re.fullmatch(r"\d{4}-\d{2}-\d{2}", atom["as_of"])))):
            raise InvalidInput("HOST_ATOM_FRAME_INVALID")
        refs = atom["source_refs"]
        if type(refs) is not list or not 1 <= len(refs) <= 80:
            raise InvalidInput("HOST_ATOM_SOURCE_REFS_REQUIRED")
        indices = []
        for ref in refs:
            if type(ref) is not dict or set(ref) != {"cue_index","quote"}:
                raise InvalidInput("HOST_ATOM_REF_SCHEMA_INVALID")
            idx, quote = ref["cue_index"], ref["quote"]
            if (type(idx) is not int or idx not in allowed or
                type(quote) is not str or len(quote.strip()) < 2 or
                " ".join(quote.casefold().split()) not in
                " ".join(source.cues[idx-1].text.casefold().split())):
                raise InvalidInput("HOST_ATOM_QUOTE_NOT_IN_ORIGINAL")
            indices.append(idx)
            if cid not in rowmap[idx]["claim_ids"]:
                raise InvalidInput("HOST_ATOM_DISPOSITION_REF_MISSING")
        if indices != sorted(set(indices)):
            raise InvalidInput("HOST_ATOM_REFS_NOT_SORTED")
        window_id = require_identifier(atom["owner_window_id"],WINDOW,"ATOM_OWNER")
        if source.owner(indices[0]) != window_id:
            raise InvalidInput("HOST_ATOM_PRIMARY_WINDOW_MISMATCH")
        context = _indices(atom["context_cue_indices"], allowed,"ATOM_CONTEXT",allow_empty=False)
        conditions = _indices(atom["condition_cue_indices"], allowed,"ATOM_CONDITIONS")
        exceptions = _indices(atom["exception_cue_indices"], allowed,"ATOM_EXCEPTIONS")
        if (not set(indices).issubset(context) or
            not set(conditions + exceptions).issubset(context) or
            (atom["stance"] == "CONDITIONAL" and not conditions)):
            raise InvalidInput("HOST_ATOM_CONDITION_OR_CONTEXT_INCOMPLETE")
        if atom["stance"] == "AFFIRMED" and any(
            QUALIFIER.search(source.cues[i-1].text) for i in context
        ):
            raise InvalidInput("HOST_ATOM_QUALIFIED_ASSERTION_REQUIRES_SEMANTIC_REVIEW")
        numbers = atom["numeric_references"]
        if type(numbers) is not list or len(numbers) > 80:
            raise InvalidInput("HOST_ATOM_NUMERIC_REFERENCES_INVALID")
        seen_numbers = []
        for item in numbers:
            if type(item) is not dict or set(item) != {"cue_index","token"}:
                raise InvalidInput("HOST_ATOM_NUMERIC_REF_SCHEMA_INVALID")
            idx, token = item["cue_index"], item["token"]
            if (type(idx) is not int or idx not in context or
                type(token) is not str or token not in rowmap[idx]["numeric_tokens"]):
                raise InvalidInput("HOST_ATOM_NUMERIC_REF_NOT_IN_SOURCE")
            seen_numbers.append(token)
        if any(re.sub(r"\s+", "", n) not in {re.sub(r"\s+", "", x) for x in seen_numbers}
               for n in NUMBER.findall(atom["proposition"])):
            raise InvalidInput("HOST_ATOM_PROPOSITION_NUMBER_UNGROUNDED")
    for idx, row in rowmap.items():
        expected = {a["claim_id"] for a in atoms if idx in [
            r["cue_index"] for r in a["source_refs"]]}
        if set(row["claim_ids"]) != expected:
            raise InvalidInput("HOST_ATOM_CUE_CLAIM_SET_MISMATCH")
    return {
        "schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_AUDIT_V1",
        "source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "cue_disposition_digest":_digest_rows(rows),
        "atom_candidate_digest":_digest_rows(atoms),
        "original_scoped_cues_enumerated":len(allowed),
        "cues_with_candidates":sum(r["disposition"] == "CANDIDATES" for r in rows),
        "proposed_atomic_claims":len(indexed),
        "unresolved_cues":unresolved,
        "suspicious_no_atom_cues":suspicious_no_atom,
        "cues_with_qualifiers":risky_context,
        "every_cue_has_explicit_disposition":True,
        "all_numeric_cue_tokens_reconciled":True,
        "semantic_claims_independently_verified":False,
        "independent_gold_recall_measured":False,
        "all_atomic_claims_exhausted":False,
        "research_complete":False,
        "p0_go":False,
        "status":"HOST_ATOM_EXCHANGE_STRUCTURAL_REVIEW_ONLY",
    }
