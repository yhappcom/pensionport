"""Private source-first blind gold custody: cryptographic consistency, not identity.

Two separately keyed human reviewer submissions and a third adjudicator seal
are verified against pinned private source bytes and immutable public prereg.
The signatures prove only possession of keys and parentage of documents, NOT
real-world human identities, genuine review independence or calendar chronology.
Private original SRT, reviewer text, signatures and keys are never returned.
"""
from __future__ import annotations

import json
import re

from .codec import canonical, json_digest, require_hash, sha256
from .errors import InvalidInput, QualityNotProven
from .evaluation import _atoms, measure_blind
from .source import verify_source

PREREG_RAW_SHA256 = "77280d7f917a7f8a25437157b78081147d17088f0b269a90275bac8bc1cbe296"
ROLES = ("REVIEWER_A", "REVIEWER_B", "ADJUDICATOR")
SLOT = re.compile(r"S0[1-9]\Z")
PERSON = re.compile(r"[A-Za-z0-9_-]{3,80}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX128 = re.compile(r"[0-9a-f]{128}\Z")


def _keys(doc, required, error):
    if type(doc) is not dict or set(doc) != set(required):
        raise InvalidInput(error)
    return doc


def _verify(key, message, signature):
    if type(signature) is not str or not HEX128.fullmatch(signature):
        raise InvalidInput("BLIND_CUSTODY_SIGNATURE_FORMAT_INVALID")
    from cryptography.exceptions import InvalidSignature
    try:
        key.verify(bytes.fromhex(signature), canonical(message))
    except InvalidSignature as exc:
        raise QualityNotProven("BLIND_CUSTODY_SIGNATURE_MISMATCH") from exc


def verify_private_gold_custody(raw, manifest, *, expected_source_sha256,
                                expected_manifest_sha256, prereg_raw, slot,
                                trusted_roster, expected_roster_sha256,
                                reviewer_packets, gold, adjudication_packet):
    """Validate signed private gold custody; return SHA-only pending receipt."""
    require_hash(expected_source_sha256, "SOURCE_SHA256_PIN")
    require_hash(expected_manifest_sha256, "MANIFEST_SHA256_PIN")
    source = verify_source(raw, manifest,
                           expected_source_sha256=expected_source_sha256,
                           expected_manifest_sha256=expected_manifest_sha256)
    if type(prereg_raw) is not bytes or sha256(prereg_raw) != PREREG_RAW_SHA256:
        raise InvalidInput("BLIND_CUSTODY_PREREG_ORIGINAL_DRIFT")
    try:
        prereg = json.loads(prereg_raw)
    except (UnicodeError, ValueError) as exc:
        raise InvalidInput("BLIND_CUSTODY_PREREG_JSON") from exc
    if (prereg.get("schema") != "IRE_V6_PROSPECTIVE_SOURCE_BLIND_PREREGISTRATION_V1"
            or prereg.get("selected_video_count") != 9
            or prereg.get("selected_cue_count") != 6829
            or prereg.get("gold_commitment_sha256") is not None
            or prereg.get("p0_go") is not False):
        raise InvalidInput("BLIND_CUSTODY_PREREG_POLICY_DRIFT")
    if type(slot) is not str or not SLOT.fullmatch(slot):
        raise InvalidInput("BLIND_CUSTODY_SLOT_INVALID")
    require_hash(expected_roster_sha256, "EXTERNAL_ROSTER_SHA256")
    roster = _keys(trusted_roster, {
        "schema", "slot", "source_sha256", "manifest_sha256",
        "prereg_sha256", "roles"}, "BLIND_CUSTODY_ROSTER_SCHEMA")
    if (roster["schema"] != "IRE_V6_EXTERNALLY_PINNED_REVIEWER_ROSTER_V1"
            or roster["slot"] != slot
            or roster["source_sha256"] != source.source_sha256
            or roster["manifest_sha256"] != source.manifest_sha256
            or roster["prereg_sha256"] != PREREG_RAW_SHA256
            or json_digest(roster) != expected_roster_sha256):
        raise InvalidInput("BLIND_CUSTODY_ROSTER_SHA_OR_SCOPE_DRIFT")
    identities = roster["roles"]
    if type(identities) is not list or len(identities) != 3:
        raise InvalidInput("BLIND_CUSTODY_THREE_DISTINCT_ROLE_KEYS_REQUIRED")
    keys, persons, pubs = {}, [], []
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    for role in identities:
        _keys(role, {"role", "person_id", "ed25519_public_key_hex"},
              "BLIND_CUSTODY_ROLE_SCHEMA")
        name, person, public = (role["role"], role["person_id"],
                                role["ed25519_public_key_hex"])
        if (name not in ROLES or name in keys or type(person) is not str
                or not PERSON.fullmatch(person) or type(public) is not str
                or not HEX64.fullmatch(public)):
            raise InvalidInput("BLIND_CUSTODY_ROLE_DUPLICATED_OR_INVALID")
        keys[name] = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public))
        persons.append(person)
        pubs.append(public)
    if set(keys) != set(ROLES) or len(set(persons)) != 3 or len(set(pubs)) != 3:
        raise InvalidInput("BLIND_CUSTODY_REVIEWER_INDEPENDENCE_KEY_CONFLICT")
    _atoms(source, gold, gold=True)
    gold_sha = json_digest(gold)
    if type(reviewer_packets) is not list or len(reviewer_packets) != 2:
        raise InvalidInput("BLIND_CUSTODY_TWO_REVIEWS_REQUIRED")
    reviewer_roles, hashes, review_shas = set(), [], []
    for packet in reviewer_packets:
        _keys(packet, {"role", "review_document", "statement", "signature_hex"},
              "BLIND_CUSTODY_REVIEW_PACKET_SCHEMA")
        role = packet["role"]
        if role not in ROLES[:2] or role in reviewer_roles:
            raise InvalidInput("BLIND_CUSTODY_DUPLICATE_REVIEWER")
        reviewer_roles.add(role)
        if packet["statement"] != "SOURCE_FIRST_NO_MODEL_PREDICTIONS_SEEN_AT_SIGNING":
            raise InvalidInput("BLIND_CUSTODY_UNSAFE_REVIEW_STATEMENT")
        _atoms(source, packet["review_document"], gold=True)
        review_sha = json_digest(packet["review_document"])
        message = {
            "schema": "IRE_V6_REVIEWER_SIGNED_SOURCE_FIRST_V1",
            "role": role, "slot": slot, "source_sha256": source.source_sha256,
            "manifest_sha256": source.manifest_sha256,
            "prereg_sha256": PREREG_RAW_SHA256,
            "review_document_sha256": review_sha,
            "statement": packet["statement"]}
        _verify(keys[role], message, packet["signature_hex"])
        hashes.append(json_digest({"message": message,
                                   "signature_hex": packet["signature_hex"]}))
        review_shas.append(review_sha)
    if reviewer_roles != set(ROLES[:2]):
        raise InvalidInput("BLIND_CUSTODY_MISSING_REVIEWER")
    adj = _keys(adjudication_packet, {
        "role", "gold_sha256", "reviewer_signed_packet_sha256s",
        "statement", "signature_hex"}, "BLIND_CUSTODY_ADJUDICATION_SCHEMA")
    statement = "SOURCE_FIRST_REVIEWER_DISPUTES_ADJUDICATED_BEFORE_PREDICTIONS"
    if (adj["role"] != "ADJUDICATOR" or adj["gold_sha256"] != gold_sha
            or adj["reviewer_signed_packet_sha256s"] != sorted(hashes)
            or adj["statement"] != statement):
        raise InvalidInput("BLIND_CUSTODY_GOLD_PARENTAGE_OR_STATEMENT_DRIFT")
    message = {
        "schema": "IRE_V6_ADJUDICATOR_GOLD_SEAL_V1", "role": "ADJUDICATOR",
        "slot": slot, "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "prereg_sha256": PREREG_RAW_SHA256,
        "trusted_roster_sha256": expected_roster_sha256,
        "gold_sha256": gold_sha,
        "reviewer_signed_packet_sha256s": sorted(hashes),
        "statement": statement}
    _verify(keys["ADJUDICATOR"], message, adj["signature_hex"])
    return {
        "schema": "IRE_V6_PRIVATE_CRYPTOGRAPHIC_GOLD_CUSTODY_RECEIPT_V1",
        "slot": slot, "source_sha256": source.source_sha256,
        "manifest_sha256": source.manifest_sha256,
        "prereg_sha256": PREREG_RAW_SHA256,
        "trusted_roster_sha256": expected_roster_sha256,
        "adjudicated_gold_sha256": gold_sha,
        "reviewer_gold_sha256s": sorted(review_shas),
        "reviewer_packet_sha256s": sorted(hashes),
        "adjudicator_signed_packet_sha256": json_digest({
            "message": message, "signature_hex": adj["signature_hex"]}),
        "distinct_signature_keys_verified": 3,
        "cryptographic_source_scope_and_signatures_verified": True,
        "human_identity_independently_verified": False,
        "actual_review_independence_verified": False,
        "independent_gold_completeness_verified": False,
        "real_world_pre_prediction_chronology_verified": False,
        "pre_registered_cohort_membership_verified": False,
        "semantic_accuracy_certified": False, "engine_quality_certified": False,
        "research_complete": False, "p0_go": False,
        "status": "SIGNATURES_VALID_BUT_INDEPENDENT_GOLD_UNVERIFIED"}


def measure_with_private_gold_custody(raw, manifest, plan, gold,
                                       predictions, matching, *,
                                       expected_source_sha256,
                                       expected_manifest_sha256,
                                       prereg_raw, slot, trusted_roster,
                                       expected_roster_sha256, reviewer_packets,
                                       adjudication_packet):
    """Bind protected signed gold to existing exact arithmetic; never GO."""
    receipt = verify_private_gold_custody(
        raw, manifest, expected_source_sha256=expected_source_sha256,
        expected_manifest_sha256=expected_manifest_sha256,
        prereg_raw=prereg_raw, slot=slot, trusted_roster=trusted_roster,
        expected_roster_sha256=expected_roster_sha256,
        reviewer_packets=reviewer_packets, gold=gold,
        adjudication_packet=adjudication_packet)
    result = measure_blind(raw, manifest, plan, gold, predictions, matching)
    if (result["source_sha256"] != receipt["source_sha256"]
            or result["gold_sha256"] != receipt["adjudicated_gold_sha256"]):
        raise InvalidInput("BLIND_CUSTODY_MEASUREMENT_SCOPE_DRIFT")
    return dict(result,
        cryptographic_gold_custody_receipt_sha256=json_digest(receipt),
        verified_signed_reviewer_keys=3,
        actual_reviewer_identity_verified=False,
        actual_blindness_independently_verified=False,
        gold_completeness_independently_verified=False,
        semantic_accuracy_certified=False, engine_quality_certified=False,
        p0_go=False,
        status="SIGNED_GOLD_ARITHMETIC_INDEPENDENT_PROVENANCE_UNVERIFIED")
