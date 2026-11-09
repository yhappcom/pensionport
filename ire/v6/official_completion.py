"""V6 official-primary-source scoped completion validator, policy V2.

Conservative initial rule registry: only one tightly specified Korean legal fact
can be approved, against an already pinned first-party original law HTML response.
No claimed human independence, general semantic-recall measure or full-engine GO.
All other FACT propositions remain blocked, not waved through by keyword search.
"""
from __future__ import annotations

import json
from datetime import date
from html import unescape
from html.parser import HTMLParser

from .codec import json_digest, sha256
from .errors import DomainConflict, InvalidInput, LedgerCorrupted, QualityNotProven
from .proof import audit_model_anchors
from .receipt import _payload
from .trust import verify_owner_inventory

LAW_RULE_ID = "KR_INCOME_TAX_DECREE_ARTICLE_40_3_EXCLUDED_FIRST_2026"
LAW_SOURCE_SHA256 = "5540ac2a9ecfad76382580cf7f46c947e2e0f11469ac700f4855b3a16f9115c2"
LAW_ORIGINAL_URL = ("https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&"
                    "joBrNo=03&joNo=0040&lsiSeq=290841&urlMode=lsScJoRltInfoR")
LAW_EFFECTIVE = date(2026, 10, 1)
LAW_CAPTURED = date(2026, 11, 8)
CANONICAL_PROPOSITION = (
    "연금계좌에서 일부 금액을 인출하면 과세제외금액이 "
    "이연퇴직소득보다 먼저 인출된 것으로 본다.")
NONFACT_KINDS = {"QUESTION", "HYPOTHETICAL", "OPINION", "RECOMMENDATION"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script", "noscript"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value)


def _compact(value):
    return "".join(value.split())


def verify_pinned_law(raw, *, as_of):
    """Verify historical first-party raw bytes and bounded effective version."""
    if type(raw) is not bytes or sha256(raw) != LAW_SOURCE_SHA256:
        raise InvalidInput("OFFICIAL_ORIGINAL_BYTES_NOT_PINNED")
    try:
        on = date.fromisoformat(as_of)
    except (TypeError, ValueError) as exc:
        raise InvalidInput("OFFICIAL_AS_OF_DATE_INVALID") from exc
    if on < LAW_EFFECTIVE or on > LAW_CAPTURED:
        raise QualityNotProven("OFFICIAL_SOURCE_VERSION_NOT_ESTABLISHED_FOR_DATE")
    parser = _Text()
    parser.feed(raw.decode("utf-8-sig", errors="strict"))
    visible = _compact(unescape("".join(parser.parts)))
    if "[시행2026.10.1.]" not in visible or "대통령령제36737호" not in visible:
        raise InvalidInput("OFFICIAL_VERSION_TEXT_MISMATCH")
    anchor = "제40조의3(연금계좌의인출순서등)"
    if anchor not in visible:
        raise InvalidInput("OFFICIAL_ARTICLE_NOT_FOUND")
    article = visible[visible.index(anchor):][:9000]
    for token in ("연금계좌에서일부금액이인출되는경우에는",
                  "다음각호의금액이순서에따라인출되는것으로본다.",
                  "과세제외금액", "이연퇴직소득", "제201조의10",
                  "확인되는날부터과세제외금액으로본다."):
        if token not in article:
            raise InvalidInput("OFFICIAL_ARTICLE_REQUIRED_CONDITION_MISSING")
    if article.index("과세제외금액") >= article.index("이연퇴직소득"):
        raise InvalidInput("OFFICIAL_DEEMED_WITHDRAWAL_ORDER_CHANGED")
    return {
        "rule_id": LAW_RULE_ID, "url": LAW_ORIGINAL_URL,
        "raw_sha256": LAW_SOURCE_SHA256, "law_effective_from": "2026-10-01",
        "verified_as_of": as_of,
        "non_deducted_amount_requires_statutory_confirmation": True,
        "issuer_digital_signature_verified": False,
        "semantic_generalization_authorized": False,
    }


def audit_official_completion(con, scope_id, state, *,
                              raw, manifest, inventory_bytes,
                              expected_inventory_sha256,
                              finance_inputs, determinations,
                              official_document_raw, as_of):
    """Re-evaluate every *currently modelled* window against private source.

    This is a narrow exact-assertion verifier, not arbitrary LLM self approval.
    """
    if type(finance_inputs) is not dict or type(determinations) is not list:
        raise InvalidInput("OFFICIAL_SCOPE_INPUTS_INVALID")
    owner = state["owner_pin"]
    att = state["source_attestation"]
    if owner is None or att is None:
        raise QualityNotProven("OFFICIAL_OWNER_PIN_OR_SOURCE_ATTESTATION_MISSING")
    anchored = verify_owner_inventory(
        raw, manifest, inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256)
    src = anchored.source
    if (anchored.attestation() != {k:v for k,v in owner.items() if k != "event_sha256"}
            or src.attestation() != {k:v for k,v in att.items() if k != "event_sha256"}):
        raise DomainConflict("OFFICIAL_PRIVATE_SOURCE_OWNER_PIN_DRIFT")
    law = verify_pinned_law(official_document_raw, as_of=as_of)
    windows = [wid for wid, _, _ in src.primary_windows]
    if set(state["models"]) != set(windows) or not windows:
        raise QualityNotProven("OFFICIAL_ALL_SOURCE_WINDOWS_NOT_MODELLED")
    if len(determinations) == 0:
        raise QualityNotProven("OFFICIAL_DETERMINATIONS_EMPTY")
    if len(determinations) > 20000:
        raise InvalidInput("OFFICIAL_TOO_MANY_ATOMS")
    given = {}
    for item in determinations:
        if type(item) is not dict or set(item) != {
            "window_id", "claim_id", "verdict", "rule_id",
            "model_revision_event_sha256", "conditions_acknowledged"
        }:
            raise InvalidInput("OFFICIAL_DETERMINATION_SCHEMA_INVALID")
        key = item["window_id"] + ":" + item["claim_id"]
        if key in given:
            raise InvalidInput("OFFICIAL_DUPLICATE_DETERMINATION")
        given[key] = item
    all_claims = {}
    actual_models = {}
    verified = []
    nonfacts = []
    proof_set = []
    finance_set = []
    if set(finance_inputs) != set(state["finance_candidate_reviews"]):
        raise QualityNotProven("OFFICIAL_FINANCE_REPLAY_SCOPE_MISMATCH")
    from .finance import audit_official_candidate, audit_prior_relation
    for wid in windows:
        model = state["models"][wid]
        proof = state["structural_proofs"].get(wid)
        if proof is None or proof["model_revision_event_sha256"] != model["revision_event_sha256"]:
            raise QualityNotProven("OFFICIAL_CURRENT_STRUCTURAL_PROOF_REQUIRED")
        actual_model = _payload(con, scope_id, model["revision_event_sha256"],
                                "MODEL_RECORDED")["model"]
        actual_models[wid] = actual_model
        actual_proof = _payload(con, scope_id, proof["proof_event_sha256"],
                                "STRUCTURAL_PROOF_RECORDED")
        checked = audit_model_anchors(src, wid, actual_model, actual_proof["review"])
        if checked != actual_proof["audit"] or json_digest(checked) != proof["audit_sha256"]:
            raise LedgerCorrupted("OFFICIAL_STRUCTURAL_PROOF_REPLAY_DRIFT")
        proof_set.append(proof["proof_event_sha256"])
        for atom in actual_model["claims"]:
            key = wid + ":" + atom["claim_id"]
            if key in all_claims:
                raise InvalidInput("OFFICIAL_DUPLICATE_ATOM_IN_MODELS")
            all_claims[key] = atom
            if key not in given:
                raise QualityNotProven("OFFICIAL_SOURCE_CLAIM_NOT_CLASSIFIED")
            review = given[key]
            if review["model_revision_event_sha256"] != model["revision_event_sha256"]:
                raise DomainConflict("OFFICIAL_MODEL_REVISION_STALE")
            if atom["kind"] in NONFACT_KINDS:
                if (review["verdict"] != "NOT_FACT_CLAIM" or
                    review["rule_id"] is not None or
                    review["conditions_acknowledged"] != []):
                    raise QualityNotProven("OFFICIAL_NONFACT_MISCLASSIFIED")
                nonfacts.append(key)
                continue
            if atom["kind"] != "FACT":
                raise QualityNotProven("OFFICIAL_UNSUPPORTED_FACT_MODALITY")
            if review["verdict"] != "VERIFIED" or review["rule_id"] != LAW_RULE_ID:
                raise QualityNotProven("OFFICIAL_FACT_NOT_FIRST_PARTY_VERIFIED")
            if review["conditions_acknowledged"] != ["SECTION_201_10_CONFIRMATION_WHEN_APPLICABLE"]:
                raise QualityNotProven("OFFICIAL_MATERIAL_CONDITION_MISSING")
            if _compact(atom["proposition"]) != _compact(CANONICAL_PROPOSITION):
                raise QualityNotProven("OFFICIAL_FACT_NOT_EXACT_REGISTERED_RULE")
            # Stronger than quotes merely present in two unrelated documents:
            # the original cue itself must assert the exact registered sentence.
            if not any(_compact(CANONICAL_PROPOSITION) ==
                       _compact(src.cues[r["cue_index"]-1].text)
                       for r in atom["source_refs"]):
                raise QualityNotProven("OFFICIAL_ORIGINAL_SOURCE_DOES_NOT_ASSERT_RULE")
            current = state["finance_candidate_reviews"].get(key)
            if not current or current["model_revision_event_sha256"] != model["revision_event_sha256"]:
                raise QualityNotProven("OFFICIAL_CURRENT_FINANCE_CANDIDATE_REQUIRED")
            if key not in finance_inputs:
                raise QualityNotProven("OFFICIAL_FINANCE_BYTES_REPLAY_REQUIRED")
            supplied = finance_inputs[key]
            if type(supplied) is not dict or set(supplied) != {
                "official_document_raw","official_proposal","expected_official_sha256",
                "as_of","prior_baseline","prior_relation","expected_baseline_sha256"
            }:
                raise InvalidInput("OFFICIAL_FINANCE_INPUT_SCHEMA_INVALID")
            if (supplied["official_document_raw"] != official_document_raw
                    or supplied["expected_official_sha256"] != LAW_SOURCE_SHA256
                    or supplied["as_of"] != as_of):
                raise DomainConflict("OFFICIAL_CURRENT_FINANCE_SOURCE_OR_DATE_DRIFT")
            verified_official = audit_official_candidate(
                supplied["official_document_raw"], supplied["official_proposal"],
                expected_document_sha256=supplied["expected_official_sha256"],
                as_of=as_of)
            verified_prior = audit_prior_relation(
                supplied["prior_baseline"], supplied["prior_relation"],
                expected_baseline_sha256=supplied["expected_baseline_sha256"])
            saved = _payload(con, scope_id, current["finance_event_sha256"],
                             "FINANCE_CANDIDATE_RECORDED")
            if (saved["official_audit"] != verified_official
                    or saved["relation_audit"] != verified_prior
                    or verified_official["effective_at_as_of"] is not True
                    or verified_official["url_declared"] != LAW_ORIGINAL_URL
                    or verified_official["claim_id"] != atom["claim_id"]
                    or verified_prior["claim_id"] != atom["claim_id"]):
                raise DomainConflict("OFFICIAL_FINANCE_CANDIDATE_REPLAY_DRIFT")
            verified.append(key)
            finance_set.append(current["finance_event_sha256"])
    if set(given) != set(all_claims) or len(verified) == 0:
        raise QualityNotProven("OFFICIAL_INCOMPLETE_OR_ZERO_VERIFIED_FACT_CENSUS")
    if set(state["finance_candidate_reviews"]) != set(verified):
        raise QualityNotProven("OFFICIAL_UNREVIEWED_OR_HISTORICAL_FINANCE_CANDIDATE")
    from .claim_census import audit_source_first_residuals
    residuals = audit_source_first_residuals(src, actual_models)
    revisions = [{"window_id":wid,
                  "revision_event_sha256":state["models"][wid]["revision_event_sha256"]}
                 for wid in windows]
    return {
        "schema":"IRE_V6_OFFICIAL_SCOPE_TERMINAL_REPORT_V2",
        "source_sha256":src.source_sha256,
        "manifest_sha256":src.manifest_sha256,
        "owner_inventory_sha256":anchored.inventory_sha256,
        "rule_id":LAW_RULE_ID,
        "official_document_sha256":LAW_SOURCE_SHA256,
        "verified_as_of":as_of,
        "window_count":len(windows),
        "model_revision_set_sha256":json_digest(revisions),
        "reviewed_atom_count":len(all_claims),
        "officially_verified_fact_count":len(verified),
        "model_labelled_nonfact_count":len(nonfacts),
        "replayed_proof_set_sha256":json_digest(proof_set),
        "replayed_finance_set_sha256":json_digest(finance_set),
        "determination_sha256":json_digest(determinations),
        "scope_fully_modelled":True,
        "source_first_atomic_exhaustiveness_verified":False,
        "source_first_residual_census_sha256":residuals["cue_census_sha256"],
        "source_first_scope_cue_count":residuals["scope_cue_count"],
        "source_first_unanchored_financial_cue_count":residuals[
            "unanchored_financial_heuristic_cue_count"],
        "source_first_qualifier_cue_count":residuals[
            "qualifier_or_contradiction_cue_count"],
        "source_first_multi_atom_cue_count":residuals[
            "multi_atom_heuristic_cue_count"],
        "source_claim_census_independently_verified":False,
        "nonfact_roles_independently_verified":False,
        "all_registered_factual_assertions_verified":False,
        "source_speaker_meaning_verified":False,
        "official_statute_rule_text_verified":True,
        "independent_human_review_required":False,
        "historical_official_source_bytes_verified":True,
        "general_semantic_recall_certified":False,
        "legacy116_semantic_merge_approved":False,
        "outcome":"OFFICIAL_RULE_VERIFIED_RESEARCH_OPEN",
        "research_complete":False,
        "engine_quality_certified":False,
        "p0_go":False,
    }
