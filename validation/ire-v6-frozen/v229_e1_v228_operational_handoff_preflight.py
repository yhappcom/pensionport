"""E1 V229: read-only, fail-closed V228 TURN1 -> V176/V203 native handoff preflight.

This does not generate a V176 SQLite journal or review, invoke V123, or publish.
The existing V203 native E1 positive path remains a SYNTHETIC architecture test.
Real owner E1 approval/store readiness needs a genuine independently pinned
V176 owner journal, matching parent checkpoint, and a later actual CHATGPT TURN2
receipt; a V228 ZIP cannot be passed as an EngineChatSession.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession
from v228_v193_actual_two_turn_runtime_gate import verify_turn1_frozen

SCHEMA = 'IRE_V229_E1_V228_REAL_OWNER_HANDOFF_PREFLIGHT_HOLD_V1'
SHA_PATTERN = re.compile(r'^[0-9a-f]{64}$')


def _need(condition: Any, label: str) -> None:
    if not condition:
        raise InvalidInput('V229_E1_HANDOFF_' + label)


def _sha(value: Any) -> bool:
    return type(value) is str and SHA_PATTERN.fullmatch(value) is not None


def check_v228_e1_owner_handoff(*,
    private_zip: Path, externally_pinned_zip_sha256: str,
    externally_pinned_manifest_sha256: str,
    externally_pinned_first_head_sha256: str,
    externally_pinned_source_sha256: str,
    v176_owner: EngineChatSession | None = None,
    parent_checkpoint: Any | None = None,
    externally_pinned_v176_owner_head_sha256: str | None = None,
    v193_second_turn_review_receipt: dict | None = None,
) -> dict:
    """Return owner E1 READINESS HOLD until actual owner-native facts are supplied.

    For operational safety, no branch in this function invokes real V203's
    storage or parent approval functions. This is preflight, not a new V203
    implementation and not a proof of the final E3 quality gate.
    """
    frozen = verify_turn1_frozen(
        private_zip=private_zip,
        externally_pinned_zip_sha256=externally_pinned_zip_sha256,
        externally_pinned_manifest_sha256=externally_pinned_manifest_sha256,
        externally_pinned_first_head_sha256=externally_pinned_first_head_sha256,
        externally_pinned_source_sha256=externally_pinned_source_sha256,
    )
    audit = frozen['audit']
    contents = frozen['content']
    native = json.loads(contents['native.json'])
    _need(frozen['phase'] == 'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND',
          'TURN1_MUST_BE_FROZEN_AWAITING_DISTINCT_COMMAND')
    _need(audit['source_sha256'] == externally_pinned_source_sha256,
          'SOURCE_DRIFT')
    _need(native['source_sha256'] == externally_pinned_source_sha256,
          'NATIVE_SOURCE_DRIFT')
    _need(v193_second_turn_review_receipt is None or
          isinstance(v193_second_turn_review_receipt, dict), 'TURN2_RECEIPT_TYPE')

    out = {
        'schema': SCHEMA,
        'owner_original_source_sha256': externally_pinned_source_sha256,
        'v228_owner_first_head_sha256': externally_pinned_first_head_sha256,
        'v228_original_cues_rechecked': audit['original_cues'],
        'v228_unapproved_atoms_rechecked': audit['unapproved_native_atoms'],
        'v228_lexical_pairs_rechecked': audit['source_claim_pairs'],
        'existing_v203_synthetic_architecture_pass_is_distinct': True,
        'read_only_preflight': True,
        'v228_zip_is_not_an_actual_v176_owner_journal': True,
        'native_owner_chain_verified': False,
        'v193_real_turn2_host_verified': False,
        'e1_real_owner_full_approval_store_path_proven': False,
        'e2_independent_gold_certified': False,
        'e3_final_approved': False,
        'e4_authorized': False,
        'e5_published': 0,
        'video_knowledge_written': 0,
    }
    if v176_owner is None or parent_checkpoint is None:
        _need(v176_owner is None and parent_checkpoint is None,
              'INCOMPLETE_OWNER_AND_PARENT_PAIR')
        _need(externally_pinned_v176_owner_head_sha256 is None,
              'ORPHAN_OWNER_HEAD_WITHOUT_JOURNAL')
        _need(v193_second_turn_review_receipt is None,
              'TURN2_RECEIPT_WITHOUT_NATIVE_OWNER')
        return {**out, 'status': 'HOLD_NO_GENUINE_V176_JOURNAL_OR_PARENT_CHECKPOINT',
                'missing': ['genuine_v176_owner_sqlite', 'source_identical_v127_parent_checkpoint',
                            'separate_user_turn2_semantic_review']}

    _need(type(v176_owner) is EngineChatSession, 'REAL_V176_OWNER_REQUIRED')
    _need(_sha(externally_pinned_v176_owner_head_sha256),
          'EXTERNAL_V176_HEAD_REQUIRED')
    progress = v176_owner.progress()  # rechecks actual V176 journal internally
    _need(v176_owner.raw == contents['source.srt'] and
          progress['source_sha256'] == externally_pinned_source_sha256 and
          progress['cue_total'] == audit['original_cues'],
          'REAL_V176_OWNER_SOURCE_AND_CUE_MISMATCH')
    _need(progress['checkpoint_head_sha256'] == externally_pinned_v176_owner_head_sha256,
          'ACTUAL_V176_HEAD_NOT_EXTERNALLY_PINNED')
    _need(getattr(parent_checkpoint, 'raw', None) == v176_owner.raw and
          getattr(parent_checkpoint, 'parent_manifest', None) == v176_owner.manifest,
          'REAL_PARENT_CHECKPOINT_MISSING_OR_DIFFERENT')
    _need(progress['source_first_review_complete'] is True and
          progress['cue_remaining'] == 0 and progress['unresolved_open_cues'] == 0,
          'ACTUAL_V176_SOURCE_REVIEW_NOT_COMPLETE')

    original_native, stage = v176_owner.compile_native_v6_stage()
    _need(stage['checkpoint_head_sha256'] == externally_pinned_v176_owner_head_sha256,
          'V176_NATIVE_STAGE_HEAD_CHANGED')
    _need(original_native['source_sha256'] == native['source_sha256'],
          'NATIVE_SOURCE_PIN_DRIFT')
    # The V228 bundle contains 68 REVISED unapproved candidate atoms. It is
    # NOT acceptable to silently assume a separate V176 journal has the same
    # claims, speaker/stance, context, qualifiers or numbers. Compare EXACTLY.
    _need(original_native['atoms'] == native['atoms'],
          'V176_AND_V228_ATOMIC_CUSTODY_MISMATCH_NO_SILENT_REBUILD')
    _need(v193_second_turn_review_receipt is not None,
          'SECOND_USER_TURN_VERDICT_REQUIRED')
    _need(v193_second_turn_review_receipt.get('source_sha256') ==
          externally_pinned_source_sha256 and
          v193_second_turn_review_receipt.get('owner_first_turn_head_sha256') ==
          externally_pinned_first_head_sha256 and
          v193_second_turn_review_receipt.get('e3_formal_approved') is False and
          v193_second_turn_review_receipt.get('e4_approved') is False and
          v193_second_turn_review_receipt.get('e5_published') is False,
          'TURN2_RECEIPT_OR_APPROVAL_NOT_SUPPORTED')
    # Even at this point, the distinct host turn has only MANUAL provenance.
    # Never set an approval here; V123/E4/E5 have their own separate gates.
    return {**out, 'status': 'SOURCE_CHAIN_MATCHED_BUT_E3_E4_E5_AUTHORITY_STILL_HOLD',
            'native_owner_chain_verified': True}