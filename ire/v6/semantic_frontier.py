"""P0-1/2 source-first, conservative semantic review frontier.

A heuristic challenge *queue* for independent adjudication, not an NLP
entailment verifier. Every original cue is checked independently of claims.
No SRT text or user-private quotes are ever returned or written.
"""
from __future__ import annotations

import hashlib

from .atomic_exchange import NUMBER, audit_host_atomic_exchange
from .claim_census import FINANCIAL, MULTI_CLAIM, QUALIFIER
from .codec import canonical, sha256
from .errors import InvalidInput

KINDS = (
    "UNRESOLVED_CUE",
    "FINANCIAL_NO_ATOM",
    "COMPOUND_CUE_SINGLE_OR_NO_CANDIDATE",
    "MULTIPLE_NUMERIC_TOKENS_SINGLE_OR_NO_CANDIDATE",
    "QUALIFIER_OR_CORRECTION_CUE",
    "NEARBY_QUALIFIER_EXCLUDED_FROM_CONTEXT",
    "SPEAKER_OR_STANCE_AMBIGUITY",
    "FINANCIAL_FACT_DATE_SCOPE_UNKNOWN",
)


def _digest(items):
    h = hashlib.sha256(b"[")
    for pos, item in enumerate(items):
        if pos:
            h.update(b",")
        h.update(canonical(item))
    h.update(b"]")
    return h.hexdigest()


def source_first_semantic_frontier(source, exchange):
    """Derive an original-bound human review queue from source and host atoms.

    False positives are possible; no lexical pattern decides actual semantic
    entailment, facts, omissions, gold correctness or production release.
    """
    audit = audit_host_atomic_exchange(source, exchange)
    allowed = set(range(source.scope_first_cue, source.scope_last_cue + 1))
    rows = exchange["cue_dispositions"]
    mapped = {r["cue_index"]: r for r in rows}
    atoms = exchange["atoms"]
    cases = []
    seen_cases = set()

    def add(kind, cue, claim_id=None):
        # Source index, SHA identity and reason are safe metadata only.
        key = {"kind": kind, "cue_index": cue, "claim_id": claim_id}
        identity = (kind, cue, claim_id)
        # The same qualifier can neighbor multiple anchors of one claim.
        if identity in seen_cases:
            return
        seen_cases.add(identity)
        if len(cases) >= 100000:
            raise InvalidInput("SEMANTIC_FRONTIER_TOO_MANY_CASES")
        cases.append({"case_id": sha256(canonical({
                          "source_sha256": source.source_sha256,
                          "manifest_sha256": source.manifest_sha256, **key})),
                      **key})

    qualifiers = set()
    for idx in sorted(allowed):
        cue = source.cues[idx - 1].text
        row = mapped[idx]
        status, count = row["disposition"], len(row["claim_ids"])
        is_financial = bool(FINANCIAL.search(cue) or NUMBER.search(cue))
        is_qualifier = bool(QUALIFIER.search(cue))
        if status == "UNRESOLVED":
            add("UNRESOLVED_CUE", idx)
        if status == "NO_ATOM" and is_financial:
            add("FINANCIAL_NO_ATOM", idx)
        if MULTI_CLAIM.search(cue) and count <= 1:
            add("COMPOUND_CUE_SINGLE_OR_NO_CANDIDATE", idx)
        # Two or more grounded financial numeric tokens can encode distinct
        # claims even without lexical "and" or a previous host split-plan.
        # A *review prompt*, not proof of an omission: base+duration, two tax
        # thresholds, and examples can all be one legitimate atomic scenario.
        numbers = NUMBER.findall(cue)
        if (len(numbers) >= 2 and count <= 1 and
                (any("원" in token for token in numbers) or FINANCIAL.search(cue))):
            add("MULTIPLE_NUMERIC_TOKENS_SINGLE_OR_NO_CANDIDATE", idx)
        if is_qualifier:
            qualifiers.add(idx)
            add("QUALIFIER_OR_CORRECTION_CUE", idx)

    for atom in atoms:
        refs = [r["cue_index"] for r in atom["source_refs"]]
        ctx = set(atom["context_cue_indices"])
        for anchor in refs:
            # A qualifier immediately preceding/following an anchor is a
            # *review cue* even if the model did not include it in context.
            # It can belong to a different speaker/topic: human decides.
            # Four constant-time source probes rather than a scan across
            # potentially thousands of qualifiers for *each* source ref.
            for idx in (anchor - 2, anchor - 1, anchor + 1, anchor + 2):
                if idx in qualifiers and idx not in ctx:
                    add("NEARBY_QUALIFIER_EXCLUDED_FROM_CONTEXT", idx,
                        atom["claim_id"])
        if atom["speaker"] in {"UNKNOWN", "QUOTED_SOURCE"} or (
                atom["stance"] in {"QUOTED", "UNRESOLVED"}):
            add("SPEAKER_OR_STANCE_AMBIGUITY", refs[0], atom["claim_id"])
        if atom["kind"] == "FACT" and atom["as_of"] is None and any(
                FINANCIAL.search(source.cues[idx - 1].text) for idx in refs):
            add("FINANCIAL_FACT_DATE_SCOPE_UNKNOWN", refs[0], atom["claim_id"])

    # Bounded and unique case census. No omission is silently swallowed.
    if len(cases) > 100000:
        raise InvalidInput("SEMANTIC_FRONTIER_TOO_MANY_CASES")
    cases = sorted(cases, key=lambda c: (c["cue_index"],
                                         c["kind"], c["claim_id"] or ""))
    if len({c["case_id"] for c in cases}) != len(cases):
        raise InvalidInput("SEMANTIC_FRONTIER_CASE_ID_DUPLICATE")
    types = {kind: 0 for kind in KINDS}
    for case in cases:
        types[case["kind"]] += 1
    return {
        "schema": "IRE_V6_SOURCE_FIRST_SEMANTIC_FRONTIER_V1",
        "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "atom_candidate_digest": audit["atom_candidate_digest"],
        "cue_disposition_digest": audit["cue_disposition_digest"],
        "scoped_original_cues": audit["original_scoped_cues_enumerated"],
        "proposed_atomic_claims": audit["proposed_atomic_claims"],
        "review_cases": cases,
        "review_case_count": len(cases),
        "review_cases_by_kind": types,
        "review_case_census_sha256": _digest(cases),
        "independent_review_performed": False,
        "independent_semantic_accuracy_verified": False,
        "independent_gold_recall_measured": False,
        "semantic_exhaustiveness_verified": False,
        "engine_quality_certified": False,
        "research_complete": False,
        "p0_go": False,
        "status": "P0_SEMANTIC_FRONTIER_REVIEW_OPEN",
    }
