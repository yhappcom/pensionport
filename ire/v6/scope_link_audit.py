"""Source-pinned context-scope inheritance checks for frozen V6 atomic candidates.

Scope rules are provisional review contracts, NOT independently established truth.
The audit detects missing *structural links* in real owner input.  It cannot
infer all source claims, verify audio/visual screens, or release E2/E3/E4/E5.
"""
from __future__ import annotations

import copy
import json

from .codec import sha256, json_digest
from .errors import InvalidInput
from .source import parse_srt


def _bad(code: str):
    raise InvalidInput("P205_SCOPE_" + code)


def _canon_text(value: str) -> str:
    return " ".join(value.split()).casefold()


def _check_source_refs(cues, claim):
    refs = claim.get("source_refs")
    if type(refs) is not list or not refs:
        _bad("MODEL_SOURCE_REFS_REQUIRED")
    indexes = set()
    for ref in refs:
        if type(ref) is not dict:
            _bad("MODEL_SOURCE_REF_SHAPE")
        idx, quote = ref.get("cue_index"), ref.get("quote")
        if (type(idx) is not int or idx < 1 or idx > len(cues)
                or type(quote) is not str or not quote.strip()
                or _canon_text(quote) not in _canon_text(cues[idx-1].text)):
            _bad("MODEL_QUOTE_NOT_VERBATIM")
        indexes.add(idx)
    return indexes


def _load(source_bytes: bytes, frozen_native_bytes: bytes, source_pin: str,
          native_pin: str):
    if type(source_bytes) is not bytes or sha256(source_bytes) != source_pin:
        _bad("ORIGINAL_SRT_SHA_DRIFT")
    if (type(frozen_native_bytes) is not bytes or
            sha256(frozen_native_bytes) != native_pin):
        _bad("FROZEN_PREDICTIONS_SHA_DRIFT")
    cues = parse_srt(source_bytes)
    try:
        native = json.loads(frozen_native_bytes)
    except (ValueError, UnicodeError) as exc:
        raise InvalidInput("P205_SCOPE_NATIVE_JSON_INVALID") from exc
    if (type(native) is not dict or native.get("source_sha256") != source_pin
            or type(native.get("atoms")) is not list):
        _bad("NATIVE_SOURCE_OR_ATOMS_INVALID")
    claims, refs = {}, {}
    for claim in native["atoms"]:
        if type(claim) is not dict or type(claim.get("claim_id")) is not str:
            _bad("NATIVE_CLAIM_SHAPE_INVALID")
        cid = claim["claim_id"]
        if cid in claims:
            _bad("NATIVE_DUPLICATE_CLAIM")
        for key in ("condition_cue_indices", "context_cue_indices", "exception_cue_indices"):
            v = claim.get(key)
            if (type(v) is not list or any(type(i) is not int or i not in range(1,len(cues)+1) for i in v)
                    or len(v) != len(set(v))):
                _bad("NATIVE_CUE_LINK_INVALID")
        claims[cid] = claim
        refs[cid] = _check_source_refs(cues, claim)
    return cues, claims, refs


def _validate_rule(rule, cues, claims, refs, seen):
    required = {"rule_id", "scope_type", "source_marker_cues", "target_claim_ids",
                "require_automatic_coverage", "target_source_span", "required_cue_links"}
    if type(rule) is not dict or set(rule) != required:
        _bad("RULE_SCHEMA_INVALID")
    rid = rule["rule_id"]
    if (type(rid) is not str or not 3 <= len(rid) <= 80 or rid in seen):
        _bad("RULE_ID_DUPLICATE_OR_INVALID")
    seen.add(rid)
    if rule["scope_type"] not in {"FICTIONAL_EXAMPLE", "INDEX_ONLY_COMPARISON"}:
        _bad("RULE_SCOPE_KIND_INVALID")
    src = rule["source_marker_cues"]
    if type(src) is not list or not src:
        _bad("RULE_MARKER_SOURCE_REQUIRED")
    marker_indices = set()
    for ref in src:
        if type(ref) is not dict:
            _bad("RULE_MARKER_SHAPE_INVALID")
        idx = ref.get("cue_index")
        quote = ref.get("quote")
        if (type(idx) is not int or idx not in range(1,len(cues)+1)
                or idx in marker_indices or type(quote) is not str
                or not quote.strip()
                or _canon_text(quote) not in _canon_text(cues[idx-1].text)):
            _bad("RULE_SOURCE_MARKER_MISSING_OR_FORGED")
        marker_indices.add(idx)
    links = rule["required_cue_links"]
    if (type(links) is not list or not links or
            any(type(i) is not int or i not in marker_indices for i in links)
            or len(set(links)) != len(links)):
        _bad("RULE_REQUIRED_ANCHORS_NOT_IN_SOURCE_MARKERS")
    targets = rule["target_claim_ids"]
    if (type(targets) is not list or not targets or
            len(targets) != len(set(targets)) or
            any(type(cid) is not str or cid not in claims for cid in targets)):
        _bad("RULE_TARGETS_MISSING_DUPLICATE_OR_UNRESOLVED")
    span = rule["target_source_span"]
    if rule["require_automatic_coverage"] is True:
        if (type(span) is not list or len(span) != 2
                or any(type(v) is not int for v in span)
                or not 1 <= span[0] <= span[1] <= len(cues)):
            _bad("RULE_AUTOMATIC_TARGET_SPAN_INVALID")
        # Never permit a caller to silently omit an impacted model claim.
        auto = {cid for cid,idxs in refs.items() if any(span[0] <= i <= span[1] for i in idxs)}
        if auto != set(targets):
            _bad("RULE_TARGETS_DO_NOT_COVER_ALL_SCOPED_PREDICTIONS")
    elif rule["require_automatic_coverage"] is not False or span is not None:
        _bad("RULE_EXPLICIT_TARGET_SCHEMA_INVALID")
    return rid,targets,links


def audit_source_scope_inheritance(original_srt: bytes, frozen_native: bytes,
                                   *, source_pin: str, native_pin: str,
                                   rules: list[dict]) -> dict:
    """Return no-claim-text diagnostic of structural inherited-scope references.

    A target claim anchoring the scope itself is not a dependent; all others
    must carry *both* condition and context cue indexes for each required cue.
    """
    cues,claims,refs = _load(original_srt,frozen_native,source_pin,native_pin)
    if type(rules) is not list or not rules:
        _bad("RULES_REQUIRED")
    seen = set()
    detail,missing,covered,anchored = [],[],0,0
    for rule in rules:
        rid,targets,links = _validate_rule(rule,cues,claims,refs,seen)
        for cid in targets:
            claim=claims[cid]
            is_anchor = bool(refs[cid].intersection(links))
            miss = []
            if not is_anchor:
                for link in links:
                    if (link not in claim["condition_cue_indices"] or
                            link not in claim["context_cue_indices"]):
                        miss.append(link)
            status=("SOURCE_MARKER_ANCHOR" if is_anchor else
                    "DEPENDENT_WITH_SCOPE_LINK" if not miss else
                    "DEPENDENT_SCOPE_LINK_MISSING")
            if is_anchor: anchored+=1
            elif not miss: covered+=1
            if miss:
                missing.append({"rule_id":rid,"claim_id":cid,"missing_cue_links":miss})
            detail.append({"rule_id":rid,"claim_id":cid,"scope_status":status,
                           "missing_cue_links":miss,"source_ref_cues":sorted(refs[cid]),
                           "source_kind":claim.get("kind")})
    # No claim truth or independent model accuracy is asserted, even when all
    # structural links are present. No E2 final approvals are possible here.
    return {
        "schema":"IRE_V6_P205_SCOPED_CONTEXT_LINK_AUDIT_V1",
        "source_sha256":source_pin,"native_sha256":native_pin,
        "source_cue_count":len(cues),"frozen_atom_count":len(claims),
        "scope_rule_count":len(rules),"scoped_claim_rows":len(detail),
        "scope_marker_atom_count":anchored,
        "dependent_scope_linked_count":covered,
        "missing_dependent_scope_link_count":len(missing),
        "scope_links_structurally_complete":len(missing)==0,
        "detail":detail,"missing":missing,
        "scope_rules_sha256":json_digest(rules),
        "confirmed_semantic_gold_accuracy":False,
        "independent_precision":None,"independent_recall":None,
        "independent_high_risk_fn":None,
        "e2_approved":False,"e3_e4_e5_approved":False,
        "ready_for_p0_2_06":False,
        "status":("HOLD_MISSING_STRUCTURAL_CONTEXT_SCOPE_LINKS" if missing
                  else "HOLD_LINKS_STRUCTURALLY_PRESENT_NOT_SEMANTICALLY_VERIFIED"),
    }


def propose_scoped_context_overlay(original_srt: bytes, frozen_native: bytes, *,
                                   source_pin: str, native_pin: str,
                                   rules: list[dict]) -> dict:
    """Produce review-only additive condition/link patch, never rewrite V228."""
    review=audit_source_scope_inheritance(original_srt,frozen_native,
                                          source_pin=source_pin,native_pin=native_pin,
                                          rules=rules)
    overlay={"schema":"IRE_V6_P205_UNAPPROVED_SCOPE_LINK_PROPOSAL_V1",
             "source_sha256":source_pin,"frozen_native_sha256":native_pin,
             "rule_sha256":review["scope_rules_sha256"],
             "changes":review["missing"],
             "original_frozen_native_unchanged":True,
             "owner_approved":False,"independent_semantic_gold_approved":False,
             "e2_e3_e4_e5_release":False,"checklist_p205_pass":False}
    return overlay


def simulate_unapproved_scope_overlay(original_srt: bytes, frozen_native: bytes, *,
                                      source_pin: str, native_pin: str,
                                      rules: list[dict], overlay: dict) -> dict:
    """In-memory RED->GREEN for structural links. Does NOT persist native data."""
    original=audit_source_scope_inheritance(original_srt,frozen_native,
                                            source_pin=source_pin,native_pin=native_pin,
                                            rules=rules)
    proposal=propose_scoped_context_overlay(original_srt,frozen_native,
                                            source_pin=source_pin,native_pin=native_pin,
                                            rules=rules)
    if overlay != proposal:
        _bad("OVERLAY_NOT_VERBATIM_ADDITIVE_PROPOSAL")
    native = json.loads(frozen_native)
    target={a["claim_id"]:a for a in native["atoms"]}
    for change in proposal["changes"]:
        atom=target[change["claim_id"]]
        for field in ("condition_cue_indices", "context_cue_indices"):
            atom[field]=sorted(set(atom[field])|set(change["missing_cue_links"]))
    # A new digest is expected; only the proposed original SHA and the exact
    # change set authorize a replay (does not mutate original bytes).
    new_native_bytes=json.dumps(native,ensure_ascii=False,sort_keys=True,
                                separators=(",",":"),allow_nan=False).encode("utf-8")
    green=audit_source_scope_inheritance(original_srt,new_native_bytes,
                                         source_pin=source_pin,
                                         native_pin=sha256(new_native_bytes),rules=rules)
    if green["missing_dependent_scope_link_count"] != 0:
        _bad("SIMULATED_PATCH_DID_NOT_RESOLVE_LINK_GAPS")
    return {
        "schema":"IRE_V6_P205_CONTEXT_LINK_DRY_RUN_RED_GREEN_V1",
        "original_native_sha256":native_pin,
        "source_sha256":source_pin,
        "proposed_overlay_sha256":json_digest(proposal),
        "pre_overlay_missing":original["missing_dependent_scope_link_count"],
        "post_overlay_missing":green["missing_dependent_scope_link_count"],
        "only_additive_link_mutations":True,
        "source_and_original_native_unmodified":True,
        "confirmed_real_source_meaning":False,
        "independent_gold":False,
        "e2_pass":False,
        "p205_pass":False,
        "p206_unlocked":False,
        "status":"DRY_RUN_STRUCTURAL_GREEN_APPROVAL_HOLD",
    }
