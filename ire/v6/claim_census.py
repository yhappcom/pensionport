"""Source-first cue frontier for V6: an auditable review queue, not semantic truth.

Every scoped original cue is accounted for before comparing *model-emitted*
claims. Financial/multi-assertion/negation cues without adequate model anchors
are flagged for review. A cue can contain arbitrarily many atomic propositions:
even 100% cue coverage NEVER certifies atomic exhaustiveness or true recall.
No source text or private owner SRT is returned.
"""
from __future__ import annotations

import re

from .codec import json_digest, sha256
from .errors import InvalidInput

FINANCIAL = re.compile(
    r"(?i)(?:\d[\d,.]*\s*(?:%|원|만원|억원|조원|퍼센트|달러|배)|"
    r"연금|국민연금|IRP|ISA|ETF|투자|수익|주식|채권|배당|분배|세금|과세|"
    r"공제|부채|대출|상환|환율|금리|손실|수수료|소득|자산|"
    r"retirement|tax|interest|yield|bond|stock|dividend|pension|loan)"
)
QUALIFIER = re.compile(
    r"(?i)(?:하지만|그러나|다만|아니라|아닙|틀리|반박|거짓|반대|"
    r"예외|조건|제외|무조건|보장|제한|unless|except|false|wrong|not\s+true)"
)
MULTI_CLAIM = re.compile(
    r"(?i)(?:그리고|또한|반면|동시에|한편|첫째|둘째|\b(?:and|but|whereas)\b)"
)


def audit_source_first_residuals(source, model_payloads: dict) -> dict:
    """Construct a complete source-first *cue* census, identify unresolved cues.

    A supplied model is NOT the authority defining what exists in the source.
    It merely adds candidate links to already enumerated original cues.
    """
    windows = {wid: (first, last) for wid, first, last in source.primary_windows}
    if type(model_payloads) is not dict or set(model_payloads) != set(windows):
        raise InvalidInput("SOURCE_FIRST_MODEL_SCOPE_INCOMPLETE")
    cue_claims = {idx: set()
                  for idx in range(source.scope_first_cue, source.scope_last_cue + 1)}
    for wid, model in sorted(model_payloads.items()):
        if type(model) is not dict or model.get("schema") != "IRE_V6_ATOMIC_MODEL_V1":
            raise InvalidInput("SOURCE_FIRST_MODEL_SCHEMA_INVALID")
        claims = model.get("claims")
        if type(claims) is not list:
            raise InvalidInput("SOURCE_FIRST_CLAIMS_INVALID")
        seen = set()
        for claim in claims:
            if type(claim) is not dict or claim.get("owner_window_id") != wid:
                raise InvalidInput("SOURCE_FIRST_MODEL_WINDOW_MISMATCH")
            cid = claim.get("claim_id")
            if type(cid) is not str or cid in seen:
                raise InvalidInput("SOURCE_FIRST_MODEL_DUPLICATE_ATOM")
            seen.add(cid)
            refs = claim.get("source_refs")
            if type(refs) is not list or not refs:
                raise InvalidInput("SOURCE_FIRST_ANCHOR_REQUIRED")
            for ref in refs:
                idx = ref.get("cue_index") if type(ref) is dict else None
                quote = ref.get("quote") if type(ref) is dict else None
                if (type(idx) is not int or idx not in cue_claims or
                    type(quote) is not str or not quote.strip() or
                    " ".join(quote.split()).casefold() not in
                    " ".join(source.cues[idx - 1].text.split()).casefold()):
                    raise InvalidInput("SOURCE_FIRST_ANCHOR_NOT_IN_ORIGINAL")
                cue_claims[idx].add(wid + ":" + cid)
    rows = []
    financial = 0
    unanchored_financial = 0
    qualified = 0
    multi = 0
    for idx in cue_claims:
        cue = source.cues[idx - 1]
        risky = bool(FINANCIAL.search(cue.text))
        qualifier = bool(QUALIFIER.search(cue.text))
        compound = bool(MULTI_CLAIM.search(cue.text))
        financial += int(risky)
        unanchored_financial += int(risky and not cue_claims[idx])
        qualified += int(qualifier)
        multi += int(compound)
        rows.append({"cue_index":idx, "cue_text_sha256":sha256(cue.text.encode("utf-8")),
                     "source_owner_window_id":source.owner(idx),
                     "model_anchor_count":len(cue_claims[idx]),
                     "financial_heuristic":risky,
                     "qualifier_or_contradiction_heuristic":qualifier,
                     "multi_atom_heuristic":compound})
    if len(rows) != source.scope_last_cue - source.scope_first_cue + 1:
        raise InvalidInput("SOURCE_FIRST_GAP_IN_CUE_CENSUS")
    return {"schema":"IRE_V6_SOURCE_FIRST_RESIDUAL_CENSUS_V1",
            "source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,
            "scope_cue_count":len(rows),
            "model_anchored_cue_count":sum(bool(cue_claims[i]) for i in cue_claims),
            "financial_heuristic_cue_count":financial,
            "unanchored_financial_heuristic_cue_count":unanchored_financial,
            "qualifier_or_contradiction_cue_count":qualified,
            "multi_atom_heuristic_cue_count":multi,
            "cue_census_sha256":json_digest(rows),
            "source_first_semantic_review_independently_done":False,
            "all_atomic_claims_exhausted":False,
            "independent_recall_measured":False,
            "research_complete":False,
            "status":"SOURCE_FIRST_SEMANTIC_RESIDUAL_OPEN"}
