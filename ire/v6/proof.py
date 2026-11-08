"""V6-3 structural source-anchor review. NOT semantic truth or blind recall.

Every quoted cue is checked against real private bytes. The current event
revision, not the model's content hash, is required for reuse. Proofs describe
source linkage only and cannot authorize research closure or financial facts.
"""
from __future__ import annotations

import re

from .codec import json_digest
from .errors import InvalidInput
from .source import VerifiedSource

CLAIM_ID = re.compile(r"C[0-9]{5,8}\Z")
TYPES = frozenset({"FACT", "HYPOTHETICAL", "QUESTION", "OPINION", "RECOMMENDATION", "MATH"})


def _norm(value: str) -> str:
    return " ".join(value.casefold().split())


def audit_model_anchors(source: VerifiedSource, window_id: str,
                        model: dict, review: dict) -> dict:
    if type(model) is not dict or set(model) != {"schema", "claims"} or \
       model["schema"] != "IRE_V6_ATOMIC_MODEL_V1":
        raise InvalidInput("STRUCTURAL_MODEL_SCHEMA_INVALID")
    claims = model["claims"]
    if type(claims) is not list or not 1 <= len(claims) <= 256:
        raise InvalidInput("STRUCTURAL_CLAIMS_REQUIRED")
    if type(review) is not dict or set(review) != {
        "schema", "review_scope", "reviewed_claim_ids", "independent_gold_verified"
    } or review["schema"] != "IRE_V6_STRUCTURAL_REVIEW_V1" or \
       review["review_scope"] != "SOURCE_ANCHORS_ONLY" or \
       review["independent_gold_verified"] is not False:
        raise InvalidInput("STRUCTURAL_REVIEW_SCHEMA_OR_AUTHORITY_INVALID")
    ids: list[str] = []
    cross_window = 0
    all_anchors = set()
    for claim in claims:
        if type(claim) is not dict or set(claim) != {
            "claim_id", "proposition", "kind", "owner_window_id",
            "source_refs", "context_first_cue", "context_last_cue"
        }:
            raise InvalidInput("STRUCTURAL_CLAIM_SHAPE_INVALID")
        cid = claim["claim_id"]
        if type(cid) is not str or not CLAIM_ID.fullmatch(cid) or cid in ids:
            raise InvalidInput("STRUCTURAL_CLAIM_ID_DUPLICATE_OR_INVALID")
        ids.append(cid)
        if type(claim["proposition"]) is not str or len(claim["proposition"].strip()) < 5:
            raise InvalidInput("STRUCTURAL_PROPOSITION_MISSING")
        if type(claim["kind"]) is not str or claim["kind"] not in TYPES or claim["owner_window_id"] != window_id:
            raise InvalidInput("STRUCTURAL_OWNER_OR_MODALITY_INVALID")
        refs = claim["source_refs"]
        if type(refs) is not list or not 1 <= len(refs) <= 80:
            raise InvalidInput("STRUCTURAL_ANCHORS_REQUIRED")
        indices = []
        for ref in refs:
            if type(ref) is not dict or set(ref) != {"cue_index", "quote"}:
                raise InvalidInput("STRUCTURAL_ANCHOR_SCHEMA_INVALID")
            i, quote = ref["cue_index"], ref["quote"]
            if type(i) is not int or not 1 <= i <= len(source.cues):
                raise InvalidInput("STRUCTURAL_CUE_INDEX_INVALID")
            if (type(quote) is not str or len(quote.strip()) < 2 or
                _norm(quote) not in _norm(source.cues[i-1].text)):
                raise InvalidInput("STRUCTURAL_QUOTE_NOT_IN_ORIGINAL")
            indices.append(i)
            all_anchors.add(i)
        if indices != sorted(set(indices)):
            raise InvalidInput("STRUCTURAL_ANCHORS_DUPLICATE_OR_UNSORTED")
        if source.owner(indices[0]) != window_id:
            raise InvalidInput("STRUCTURAL_PRIMARY_OWNER_INVALID")
        if (type(claim["context_first_cue"]) is not int or
            type(claim["context_last_cue"]) is not int or
            claim["context_first_cue"] != indices[0] or
            claim["context_last_cue"] != indices[-1]):
            raise InvalidInput("STRUCTURAL_CONTEXT_SPAN_INCOMPLETE")
        if source.owner(indices[-1]) != window_id:
            cross_window += 1
    if (type(review["reviewed_claim_ids"]) is not list or
        review["reviewed_claim_ids"] != sorted(ids)):
        raise InvalidInput("STRUCTURAL_REVIEW_CLAIM_SET_INCOMPLETE")
    return {
        "schema": "IRE_V6_SOURCE_ANCHOR_AUDIT_V1",
        "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "cue_census_sha256": source.cue_census_sha256,
        "window_id": window_id,
        "claim_count": len(ids),
        "distinct_anchored_cue_count": len(all_anchors),
        "cross_window_claim_count": cross_window,
        "model_sha256": json_digest(model),
        "review_sha256": json_digest(review),
        "structural_source_links_checked": True,
        "semantic_completeness_verified": False,
        "independent_gold_verified": False,
        "financial_facts_approved": False,
        "research_closed": False,
        "p0_go": False,
    }
