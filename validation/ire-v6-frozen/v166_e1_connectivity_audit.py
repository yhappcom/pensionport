"""V166 E1 source-path contract diagnostic.

Source signatures are not a test result. Actual E1 architecture PASS requires
the CI positive+negative typed->V123->V128 SQLite execution and the source-only
owner HOLD proof, referenced by the persistent ordered state ledger.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN_PATH = {
    "v164_typed_v123.py": [
        '"typed_final_knowledge_release_authorized": False',
        '"v128_parent_publication_authorized": False',
    ],
    "v126_chat_approved_knowledge_store.py": ["gate = require_chat_final_release("],
    "v127_full_video_chat_completion.py": ["verdict = assess_chat_final_gate("],
    "v1271_parent_resume_checkpoint.py": ["gate=assess_chat_final_gate("],
    "v128_atomic_parent_knowledge.py": ["staging.add_chat_final_batch("],
}
BRIDGE_PATH = {
    "v166_source_only_to_v123_quarantine.py": [
        "compile_attested_source_only_quarantine(", "audit_typed_speech_row(",
    ],
    "v166_shared_source_only_native_contract.py": [
        "compile_attested_source_only_quarantine(", "NON_RESEARCH_CONTENT",
        '"release_authorized_by_compiler":False',
    ],
    "test_v166_e1_same_typed_review_to_sqlite.py": [
        "compile_attested_source_only_quarantine(", "assess_chat_final_gate(",
        "self.fx.run_engine()", '"WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY"',
    ],
}


def _scan(source):
    return {p:{s:s in (ROOT/p).read_text(encoding="utf-8") for s in needles}
            for p,needles in source.items()}


def audit_e1():
    old = _scan(FROZEN_PATH)
    new = _scan(BRIDGE_PATH)
    base = all(all(x.values()) for x in old.values())
    bridge = all(all(x.values()) for x in new.values())
    state = json.loads((ROOT/"V166_E1_E7_STATUS.json").read_text(encoding="utf-8"))
    e1 = state["sequence"][0]
    pass_claim = e1["status"] == "PASS"
    proof_name = ("validation/ire-v6-frozen/"
                  "V166_E1_FINAL_SINGLE_INPUT_ACID_AND_OWNER_HOLD_PROOF_20261117.md")
    proof = proof_name in e1["evidence_paths"] and (ROOT/proof_name.split("/")[-1]).is_file()
    run_url = e1.get("final_connected_ci_run") or ""
    if not base or not bridge:
        raise AssertionError("V166_E1_PROTECTED_BASE_OR_SHARED_BRIDGE_CODE_MISSING")
    if pass_claim and not (proof and run_url.endswith("/44024787646") and
                           state["current_step"] == "E2" and
                           e1["retest_required"] is False and
                           not e1["blockers"]):
        raise AssertionError("V166_E1_PREMATURE_PASS_WITHOUT_BOTH_EVIDENCE_PATHS")
    if not pass_claim and state["current_step"] != "E1":
        raise AssertionError("V166_E1_NOT_PASSED_BUT_E2_STARTED")
    return {
        "schema": "IRE_V166_E1_CONNECTIVITY_SOURCE_AUDIT_V2",
        "frozen_v123_and_v128_original_path_unchanged": base,
        "legacy_direct_typed_release_still_false": True,
        "shared_adapter_structurally_present": bridge,
        "same_input_e1_test_and_owner_hold_report_present": proof,
        "linked_ci_execution": run_url if pass_claim else None,
        "e1_structural_pass_claim": pass_claim,
        "financial_fact_semantic_quality_certified": False,
        "video_1_all_13_children_published": False,
        "p0_go": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_e1(), sort_keys=True, ensure_ascii=False, indent=2))
