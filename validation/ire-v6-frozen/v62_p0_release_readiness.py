"""V62 P0 fail-closed progress/readiness; not independent evaluation.

Only evaluates pre-audited counts. Cannot authenticate independent gold reviewer
identities, restore historical database bytes, or authorize personalized advice.
"""
from __future__ import annotations

EXPECTED_CUES = 5129
EXPECTED_WINDOWS = 130
EXPECTED_PROVISIONAL = 1603


class InvalidReadinessInput(ValueError):
    pass


def evaluate_readiness(
    source_receipt: dict, *,
    external_evidence_open: int,
    missing_historical_v40_windows: int,
    historical_audio_proofs_missing: int,
    independent_gold_reviewer_attestation_verified: bool,
    independent_gold_claim_level_precision_recall_measured: bool,
):
    if (type(source_receipt) is not dict or source_receipt.get('schema') !=
            'IRE_V6_V62_FIRSTFIVE_P0_MANUAL_REVIEW_OVERLAY_50_OF_1603_SHA_ONLY'):
        raise InvalidReadinessInput('SOURCE_CUSTODY_RECEIPT_REQUIRED')
    keys = ('source_cues', 'source_windows', 'source_provisional_utterances',
            'reviewed_utterance_parents', 'unreviewed_source_utterances',
            'reviewer_semantic_subunits')
    if not all(type(source_receipt.get(k)) is int for k in keys):
        raise InvalidReadinessInput('SOURCE_CENSUS_INTEGER_REQUIRED')
    if (source_receipt['source_cues'] != EXPECTED_CUES or
        source_receipt['source_windows'] != EXPECTED_WINDOWS or
        source_receipt['source_provisional_utterances'] != EXPECTED_PROVISIONAL or
        source_receipt['reviewed_utterance_parents'] < 0 or
        source_receipt['unreviewed_source_utterances'] < 0 or
        source_receipt['reviewed_utterance_parents'] +
        source_receipt['unreviewed_source_utterances'] != EXPECTED_PROVISIONAL or
        source_receipt.get('semantics_independently_gold_verified') is not False or
        source_receipt.get('p0_go') is not False):
        raise InvalidReadinessInput('SOURCE_CENSUS_OR_FALSE_GO')
    unresolved = (external_evidence_open, missing_historical_v40_windows,
                  historical_audio_proofs_missing)
    if any(type(n) is not int or n < 0 for n in unresolved):
        raise InvalidReadinessInput('P0_UNRESOLVED_COUNTS_INVALID')
    if (type(independent_gold_reviewer_attestation_verified) is not bool or
        type(independent_gold_claim_level_precision_recall_measured) is not bool):
        raise InvalidReadinessInput('INDEPENDENCE_FLAGS_INVALID')
    blockers = []
    if source_receipt['unreviewed_source_utterances']:
        blockers.append('ATOMIZATION_OPEN')
    if external_evidence_open:
        blockers.append('FINANCIAL_SOURCE_EVIDENCE_OPEN')
    if missing_historical_v40_windows:
        blockers.append('HISTORICAL_V40_CUSTODY_BYTES_MISSING')
    if historical_audio_proofs_missing:
        blockers.append('HISTORICAL_ORIGINAL_AUDIO_ISSUER_PROOFS_OPEN')
    if not independent_gold_reviewer_attestation_verified:
        blockers.append('INDEPENDENT_REVIEWER_ATTESTATION_MISSING')
    if not independent_gold_claim_level_precision_recall_measured:
        blockers.append('INDEPENDENT_PRECISION_RECALL_UNMEASURED')
    # Not a GO oracle. External independently verified adjudication and
    # legal/applicability signoff are out of scope, even if all counts pass.
    if not blockers:
        blockers.append('EXTERNAL_INDEPENDENT_RELEASE_APPROVAL_REQUIRED')
    return {
        'status': 'P0_NO_GO', 'p0_go': False,
        'reviewed_candidate_parents': source_receipt['reviewed_utterance_parents'],
        'unreviewed_candidate_parents': source_receipt['unreviewed_source_utterances'],
        'external_evidence_open': external_evidence_open,
        'missing_historical_v40_windows': missing_historical_v40_windows,
        'historical_audio_proofs_missing': historical_audio_proofs_missing,
        'blockers': blockers,
        'automatic_personal_financial_advice_approved': False,
        'independent_semantic_truth_certified_by_this_gate': False,
    }
