"""V193 current E3 operating contract: *two USER/ASSISTANT turns*, not two batches.

This is a source/checkpoint and process-claim guard, NOT a means of inspecting
ChatGPT host message IDs or independently proving a separate conversation turn.
No model API. Never authorizes E3 semantic success, V123/E4, or E5.
"""
from __future__ import annotations
from typing import Mapping, Any
from ire.v6.errors import InvalidInput

SCHEMA = 'IRE_V193_E3_TWO_USER_TURN_CONTRACT_V1'
_TURN_KEYS = frozenset({'phase', 'user_message_ref', 'user_message_sha256',
                        'source_sha256', 'owner_head_sha256'})
_TURN1_KEYS = _TURN_KEYS | {'research_frozen'}
_TURN2_KEYS = _TURN_KEYS | {'review_recorded', 'review_head_sha256'}
_PHASES = ('RESEARCH_AND_FREEZE', 'CHATGPT_FINAL_SEMANTIC_VERIFICATION')


def _need(ok: bool, code: str) -> None:
    if not ok:
        raise InvalidInput('V193_TWO_USER_TURN_' + code)


def _sha(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _user_ref(value: Any) -> bool:
    # Lexical guard only; a caller could still invent a user: ref.
    return type(value) is str and value.startswith("user:") and len(value) > 5 and not any(ch.isspace() for ch in value)


def validate_manual_turn_receipt(*, first: Mapping[str, Any],
                                 second: Mapping[str, Any] | None,
                                 source_sha256: str, owner_head_sha256: str,
                                 batch_count: int = 0,
                                 independent_gold_certified: bool = False,
                                 e3_approved: bool = False,
                                 v123_e4_approved: bool = False,
                                 e5_published: bool = False) -> dict[str, Any]:
    """Validate *claims* about user turns; never certify host-level provenance.

    `user_message_ref` must denote a USER command, not a model response, batch,
    subprocess, callback, CLI invocation, or archived review event. This field
    is caller-provided and is NOT checked against the ChatGPT host. A successful
    return means a coherent *manually supplied receipt*, not verified host turns.
    """
    _need(not any((independent_gold_certified, e3_approved,
                   v123_e4_approved, e5_published)), 'NO_AUTHORITY_TO_APPROVE')
    _need(_sha(source_sha256) and _sha(owner_head_sha256), 'SOURCE_OR_FREEZE_HASH_INVALID')
    _need(type(batch_count) is int and 0 <= batch_count <= 100_000, 'BATCH_COUNT_INVALID')
    _need(isinstance(first, dict) and set(first) == _TURN1_KEYS, 'FIRST_RECEIPT_SCHEMA')
    _need(first['phase'] == _PHASES[0] and first['research_frozen'] is True,
          'FIRST_PHASE_NOT_FROZEN')
    _need(first['source_sha256'] == source_sha256 and
          first['owner_head_sha256'] == owner_head_sha256, 'FIRST_SOURCE_OR_HEAD_MISMATCH')
    _need(_user_ref(first['user_message_ref']) and _sha(first['user_message_sha256']), 'FIRST_USER_MESSAGE_EVIDENCE_MISSING')
    if second is None:
        return {
            'schema': SCHEMA, 'phase': 'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND',
            'recorded_distinct_user_commands': 1, 'batch_count': batch_count,
            'host_separate_turns_verified': False,
            'two_user_turns_proven': False, 'e3_semantic_accuracy_certified': False,
            'v123_e4_approved': False, 'e5_published': False,
            'reason': 'A second user instruction and independent review result have not been recorded.'
        }
    _need(isinstance(second, dict) and set(second) == _TURN2_KEYS, 'SECOND_RECEIPT_SCHEMA')
    _need(second['phase'] == _PHASES[1] and second['review_recorded'] is True,
          'SECOND_NOT_FINAL_REVIEW')
    _need(second['source_sha256'] == source_sha256 and
          second['owner_head_sha256'] == owner_head_sha256,
          'SECOND_SOURCE_OR_FROZEN_HEAD_MISMATCH')
    _need(_user_ref(second['user_message_ref']) and _sha(second['user_message_sha256']) and _sha(second['review_head_sha256']),
          'SECOND_USER_OR_REVIEW_EVIDENCE_MISSING')
    _need(first['user_message_ref'] != second['user_message_ref'],
          'SAME_USER_COMMAND_IS_NOT_TWO_TURNS')
    # Identical user message text can be sent in two distinct real turns.
    # Distinct strings still do not attest ChatGPT platform origin, sequencing,
    # actual user authorship, or blind review. Do not escalate to quality PASS.
    return {
        'schema': SCHEMA, 'phase': 'TWO_DISTINCT_USER_COMMANDS_CLAIMED_UNVERIFIED',
        'recorded_distinct_user_commands': 2, 'batch_count': batch_count,
        'host_separate_turns_verified': False,
        'two_user_turns_proven': False, 'e3_semantic_accuracy_certified': False,
        'v123_e4_approved': False, 'e5_published': False,
        'reason': ('Two different caller-supplied message references were recorded, '
                   'but no trusted host message provenance was available.')
    }