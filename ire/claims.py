"""Independently generated proposition frames and exhaustive source-coverage gate.

Annotations must be produced from original transcript/discourse context only.
Passing this validator proves traceability, NOT completeness or factual truth.
"""
from __future__ import annotations
import re
from .source import Cue, require, text_norm, parse_srt, sha256, DIGEST, VIDEO

CLAIM_ID = re.compile(r"^C\d{5,8}$")
CLAIM_TYPES = frozenset({
    "REGULATION", "PRODUCT", "NUMERIC", "STRATEGY", "EMPIRICAL",
    "MECHANISM", "OPINION", "OTHER"
})
MODALITIES = frozenset({
    "ASSERTION", "CONDITIONAL", "NEGATION", "HYPOTHESIS",
    "QUESTION", "PREFERENCE", "UNRESOLVED"
})
CUE_STATES = frozenset({"LINKED", "NONCLAIM_CANDIDATE", "UNRESOLVED"})


def _small_text(text, maximum=10000, permit_empty=False):
    return (type(text) is str and (permit_empty or bool(text.strip()))
            and len(text) <= maximum)


def validate_frame(frame: dict) -> dict:
    keys = {"subject", "product", "financial_event", "action", "object",
            "jurisdiction", "effective_date", "conditions", "exceptions",
            "measurements", "modality"}
    require(type(frame) is dict and set(frame) == keys, "FRAME_SCHEMA_MISMATCH")
    for key in ("subject", "product", "financial_event", "action", "object",
                "jurisdiction", "effective_date"):
        value=frame[key]
        require(value is None or _small_text(value,256), "FRAME_FIELD_NOT_TYPED_"+key)
    for key in ("conditions", "exceptions"):
        require(type(frame[key]) is list and len(frame[key]) <= 50
                and all(_small_text(v,512) for v in frame[key]),
                "INVALID_SCOPE_QUALIFIER_"+key)
    require(frame["modality"] in MODALITIES, "INVALID_FINANCIAL_MODALITY")
    require(type(frame["measurements"]) is list and
            len(frame["measurements"]) <= 30, "INVALID_MEASUREMENT_COUNT")
    for v in frame["measurements"]:
        require(type(v) is dict and set(v) ==
                {"value_text", "unit", "measure_kind", "reference_cue"},
                "INVALID_MEASUREMENT_SCHEMA")
        require(_small_text(v["value_text"],128) and
                _small_text(v["unit"],64) and
                _small_text(v["measure_kind"],128) and
                type(v["reference_cue"]) is int, "INVALID_MEASUREMENT")
    return frame


def validate_annotations(raw: bytes, expected_sha: str, video_id: str,
                         proposed: dict) -> dict:
    cues = parse_srt(raw, expected_sha)
    require(type(video_id) is str and VIDEO.fullmatch(video_id) is not None,
            "ANNOTATION_VIDEO_INVALID")
    require(type(proposed) is dict and proposed.get("schema") == "IRE_PROPOSALS_V1"
            and proposed.get("video_id") == video_id
            and proposed.get("source_sha256") == expected_sha,
            "ANNOTATION_SOURCE_IDENTITY_MISMATCH")
    generator=proposed.get("generator")
    require(type(generator) is dict and set(generator) ==
            {"origin", "model_sha256", "prompt_sha256"},
            "ANNOTATION_GENERATOR_MANIFEST_MISSING")
    require(generator["origin"] == "EXTERNAL_UNVERIFIED",
            "GENERATOR_CANNOT_ATTEST_INDEPENDENCE")
    require(all(type(generator[k]) is str and DIGEST.fullmatch(generator[k])
                for k in ("model_sha256","prompt_sha256")),
            "UNPINNED_ANNOTATION_MODEL")
    entries=proposed.get("claims")
    dispositions=proposed.get("cue_dispositions")
    require(type(entries) is list and type(dispositions) is list
            and len(dispositions)==len(cues) and
            len(entries)<=250000, "CLAIM_OR_CUE_CENSUS_INVALID")
    claims_by_id={}
    inferred_links={c.index:set() for c in cues}
    all_reference_quotes=0
    for claim in entries:
        require(type(claim) is dict and set(claim)=={
            "claim_id","proposition","claim_types","frame",
            "source_refs","annotation_status"},
            "CLAIM_PROPOSAL_SCHEMA_INVALID")
        cid=claim["claim_id"]
        require(type(cid) is str and CLAIM_ID.fullmatch(cid) is not None
                and cid not in claims_by_id, "DUPLICATED_OR_INVALID_CLAIM_ID")
        require(_small_text(claim["proposition"],10000)
                and type(claim["claim_types"]) is list
                and bool(claim["claim_types"])
                and len(claim["claim_types"])==len(set(claim["claim_types"]))
                and set(claim["claim_types"])<=CLAIM_TYPES,
                "INVALID_PROPOSED_ATOM_OR_TYPE")
        require(claim["annotation_status"]=="UNREVIEWED",
                "ANNOTATOR_MAY_NOT_APPROVE_FINANCIAL_CLAIM")
        validate_frame(claim["frame"])
        refs=claim["source_refs"]
        require(type(refs) is list and 1<=len(refs)<=80,
                "INVALID_SOURCE_REFERENCE_COUNT")
        indices=[]
        for r in refs:
            require(type(r) is dict and set(r)=={"cue_index","quote"},
                    "SOURCE_CITATION_SCHEMA_INVALID")
            ix=r["cue_index"]
            require(type(ix) is int and 1<=ix<=len(cues)
                    and _small_text(r["quote"],2000)
                    and text_norm(r["quote"]) in text_norm(cues[ix-1].text),
                    "UNTRACEABLE_QUOTED_SOURCE")
            indices.append(ix)
            inferred_links[ix].add(cid)
            all_reference_quotes+=1
        require(indices==sorted(set(indices)),
                "SOURCE_REFERENCES_REQUIRE_DISTINCT_ORDERED_CUES")
        for number in claim["frame"]["measurements"]:
            require(number["reference_cue"] in indices,
                    "MEASUREMENT_CUE_NOT_AMONG_SOURCES")
            require(number["value_text"] in
                    " ".join(cues[ix-1].text for ix in indices),
                    "NUMERIC_LITERAL_NOT_FOUND_IN_SOURCE")
        claims_by_id[cid]=claim
    incomplete=[]
    linked_cues=0
    for n, row in enumerate(dispositions,1):
        require(type(row) is dict and set(row)=={
            "cue_index","status","claim_ids","reason"},
            "CUE_DISPOSITION_SCHEMA_INVALID")
        require(type(row["cue_index"]) is int and row["cue_index"]==n
                and row["status"] in CUE_STATES
                and type(row["claim_ids"]) is list
                and all(type(x) is str for x in row["claim_ids"])
                and len(row["claim_ids"])==len(set(row["claim_ids"]))
                and set(row["claim_ids"])==inferred_links[n],
                "SOURCE_CUE_REVERSE_CLAIM_LINK_MISMATCH")
        if row["status"]=="LINKED":
            require(bool(row["claim_ids"]) and row["reason"] is None,
                    "LINKED_CUE_NEEDS_SOURCE_CLAIM")
            linked_cues+=1
        elif row["status"]=="NONCLAIM_CANDIDATE":
            require(not row["claim_ids"] and _small_text(row["reason"],512)
                    and len(row["reason"])>=8,
                    "NONCLAIM_CUE_MUST_EXPLAIN_OMISSION")
        else:
            require(row["reason"] is None or _small_text(row["reason"],512),
                    "UNRESOLVED_REASON_INVALID")
            incomplete.append(n)
        # A cue with a linked claim cannot be labeled as nonclaim/unresolved.
        require(not inferred_links[n] or row["status"]=="LINKED",
                "PROPOSED_ATOM_MARKED_UNRESOLVED")
    # This output intentionally never grants claim truth or source completeness:
    return {
        "schema":"IRE_ANNOTATION_VALIDATION_V1",
        "source_sha256":expected_sha,
        "video_id":video_id,
        "source_cues":len(cues),
        "proposed_atomic_claims":len(entries),
        "traceable_source_quotes":all_reference_quotes,
        "cue_dispositions_accounted_for":len(dispositions),
        "linked_cues":linked_cues,
        "unresolved_cues":len(incomplete),
        "unresolved_cue_ids":incomplete,
        "source_lineage_structurally_valid":True,
        "meaningful_atomization_independently_verified":False,
        "semantic_accuracy_certified":False,
        "evidence_verified":False,
        "human_review_accepted":False,
        "research_complete":False
    }


def obligations(claim: dict) -> list[str]:
    """Typed worklist: each obligation is an independent research task."""
    kind=set(claim["claim_types"])
    tasks={"SOURCE_MEANING_INDEPENDENT_REVIEW"}
    if kind & {"REGULATION", "PRODUCT", "MECHANISM"}:
        tasks.add("OFFICIAL_SOURCE_EFFECTIVE_SCOPE_EXCEPTIONS")
    if "NUMERIC" in kind or claim["frame"]["measurements"]:
        tasks.add("INDEPENDENT_DECIMAL_FORMULA_INPUT_AND_UNITS")
    if kind & {"EMPIRICAL","STRATEGY"}:
        tasks.add("REPRODUCIBLE_PUBLIC_DATA_COSTS_RISK_OUT_OF_SAMPLE")
    if "OPINION" in kind:
        tasks.add("OPINION_VS_FACT_INFERENCE_CHECK")
    if (claim["frame"]["effective_date"] is None and
            kind & {"REGULATION", "PRODUCT"}):
        tasks.add("UNRESOLVED_EFFECTIVE_DATE")
    if (claim["frame"]["jurisdiction"] is None and
            kind & {"REGULATION", "PRODUCT"}):
        tasks.add("UNRESOLVED_JURISDICTION")
    if claim["frame"]["modality"]=="UNRESOLVED":
        tasks.add("UNRESOLVED_MODALITY")
    return sorted(tasks)
