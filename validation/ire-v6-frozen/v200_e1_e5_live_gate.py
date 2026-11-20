"""V200: read-only, VIDEO-AGNOSTIC live E1-E5 readiness interrogation.

A passing synthetic CI is not a semantic accuracy result or authorization to
approve or publish. The active chat must produce real source interpretations;
this module validates the unmodified native V176 stage and never infers E4/E5.
Only pinned private SRT/SQLite/validated E3 review objects may be supplied.
No owner transcript or portfolio information is included in returned status.
"""
from __future__ import annotations

from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession

SCHEMA = "IRE_V200_E1_E5_NATIVE_READINESS_AUDIT_V1"


def _need(ok, code):
    if not ok:
        raise InvalidInput("V200_E1_E5_" + code)


def evaluate_live(engine: EngineChatSession, *, v199=None):
    """Read live V176/V6 state, without ever manufacturing authority.

    This is deliberately not a substitute for a native E3 gold-set review,
    V123/E4 decision, or E5 atomic transaction. E1 means the source-bound
    intake *substep* only. Neither 'source complete' nor 373 CI tests is
    sufficient to turn the whole end-to-end chain into PASS.
    """
    _need(type(engine) is EngineChatSession, "REAL_V176_SESSION_REQUIRED")
    progress = engine.progress()               # Re-audits private event hashes.
    exchange, native = engine.compile_native_v6_stage()  # Frozen V6 audit.
    _need(exchange["source_sha256"] == progress["source_sha256"] ==
          native["source_sha256"], "SOURCE_PIN_DRIFT")
    _need(native["checkpoint_head_sha256"] ==
          progress["checkpoint_head_sha256"], "HEAD_DRIFT")
    _need(len(exchange["cue_dispositions"]) == progress["cue_total"],
          "ORIGINAL_CUE_CENSUS_DRIFT")

    semantic = native["semantic_projection_gate"]
    _need(semantic["staged_atoms"] == len(exchange["atoms"]), "ATOM_CENSUS_DRIFT")
    _need(semantic["unresolved_stance_atoms"] ==
          sum(a["stance"] == "UNRESOLVED" for a in exchange["atoms"]),
          "STANCE_CENSUS_DRIFT")
    _need(semantic["unknown_speaker_atoms"] ==
          sum(a["speaker"] == "UNKNOWN" for a in exchange["atoms"]),
          "SPEAKER_CENSUS_DRIFT")
    _need(native["v123_invoked"] is False and native["e4_invoked"] is False
          and native["e5_invoked"] is False and native["final_approval"] is False,
          "STAGED_DATA_CANNOT_CLAIM_APPROVAL")

    e3_context = None
    if v199 is not None:
        # A previous CMA case can be audited in the same framework, but its
        # six-case review or 12 web-text comparisons are NOT an E3 approval.
        from v199_e3_residual_source_verdict import E3SixResidualVerdicts
        _need(type(v199) is E3SixResidualVerdicts, "PINNED_E3_OBJECT_REQUIRED")
        _need(v199.config["source_sha256"] == progress["source_sha256"] and
              v199.config["v194_first_head_sha256"] ==
                progress["checkpoint_head_sha256"], "E3_SOURCE_OR_OWNER_HEAD_MISMATCH")
        e3_status = v199.status()  # Audits previous E3/repair verdict journals.
        _need(e3_status["e3_approved"] is False, "REVIEW_IS_NOT_E3_APPROVAL")
        e3_context = {
            "reviewed_residuals": e3_status["reviewed"],
            "review_head_sha256": e3_status["v199_head_sha256"],
            "financial_fact_certified": False
        }

    source_complete = (
        progress["cue_remaining"] == 0 and
        progress["cue_reviewed"] == progress["cue_total"] and
        all(x["complete"] for x in progress["segment_progress"])
    )
    blockers = []
    if not source_complete:
        blockers.append("E1_ORIGINAL_CUE_REVIEW_INCOMPLETE")
    # V176 is a source-first stage. It does not provide a verified semantic
    # stance/speaker/qualifier projection even when all cues were examined.
    if not semantic["full_semantic_projection_verified"]:
        blockers.append("E2_COMPLETE_SEMANTIC_PROJECTION_NOT_CERTIFIED")
    if semantic["unprojected_claims"]:
        blockers.append("E2_SOURCE_CONDITIONS_EXCEPTIONS_UNMAPPED")
    if semantic["unresolved_stance_atoms"] or semantic["unknown_speaker_atoms"]:
        blockers.append("E2_SPEAKER_STANCE_UNRESOLVED")
    if not exchange["atoms"]:
        blockers.append("E2_NO_APPROVABLE_ATOMS")
    blockers += [
        "E3_INDEPENDENT_SEMANTIC_GOLD_AND_TWO_TURN_PROOF_MISSING",
        "E4_NATIVE_V123_APPROVAL_NOT_INVOKED",
        "E5_ATOMIC_KNOWLEDGE_COMMIT_NOT_INVOKED",
    ]

    return {
        "schema": SCHEMA,
        "owner_source_sha256": progress["source_sha256"],
        "owner_head_sha256": progress["checkpoint_head_sha256"],
        "e1": {
            "status": "HOLD_END_TO_END_NOT_WIRED",
            "source_first_pass": "COMPLETE" if source_complete else "INCOMPLETE",
            "cue_total": progress["cue_total"],
            "cue_reviewed": progress["cue_reviewed"],
            "segments_reviewed": sum(x["complete"] for x in progress["segment_progress"]),
            "segments_total": len(progress["segment_progress"]),
        },
        "e2": {
            "status": "HOLD",
            "staged_atoms": len(exchange["atoms"]),
            "unprojected_claims": semantic["unprojected_claims"],
            "unmapped_condition_terms": semantic["unprojected_condition_terms"],
            "unmapped_exception_terms": semantic["unprojected_exception_terms"],
            "unresolved_stance_atoms": semantic["unresolved_stance_atoms"],
            "unknown_speaker_atoms": semantic["unknown_speaker_atoms"],
        },
        "e3": {
            "status": "HOLD_NOT_INDEPENDENT_GOLD_CERTIFIED",
            "pinned_case_context": e3_context,
            "host_two_turns_independently_attested": False,
            "precision": None, "recall": None, "high_risk_omissions": None,
        },
        "e4": {
            "status": "NOT_RUN",
            "native_v123_approved": False,
            "bad_input_rejection_test_not_equivalent_to_valid_approval": True,
        },
        "e5": {
            "status": "NOT_RUN",
            "knowledge_published": 0,
            "atomic_commit_proven": False,
        },
        "blockers": list(dict.fromkeys(blockers)),
        "all_stages_passed": False,
        "ready_for_financial_advice": False,
    }
