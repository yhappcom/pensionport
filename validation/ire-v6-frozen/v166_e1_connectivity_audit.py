"""V166 E1 actual source-code interface audit.

A successful audit process may report E1=FAIL: detecting the known break
correctly is NOT evidence that the engine passed its architecture criterion.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEEDED = {
    "v164_typed_v123.py": [
        '"typed_final_knowledge_release_authorized": False',
        '"v128_parent_publication_authorized": False',
    ],
    "v126_chat_approved_knowledge_store.py": [
        "gate = require_chat_final_release(",
    ],
    "v127_full_video_chat_completion.py": [
        "verdict = assess_chat_final_gate(",
    ],
    "v1271_parent_resume_checkpoint.py": [
        "gate=assess_chat_final_gate(",
    ],
    "v128_atomic_parent_knowledge.py": [
        "staging.add_chat_final_batch(",
    ],
}


def audit_e1() -> dict:
    matches = {}
    for filename, patterns in NEEDED.items():
        raw = (ROOT / filename).read_text(encoding="utf-8")
        matches[filename] = {pattern: pattern in raw for pattern in patterns}
    live = all(all(part.values()) for part in matches.values())
    state = json.loads((ROOT / "V166_E1_E7_STATUS.json").read_text(encoding="utf-8"))
    if live and (state["current_step"] != "E1"
                 or state["sequence"][0]["status"] != "FAIL"):
        raise AssertionError("KNOWN_E1_TYPED_DISCONNECT_NOT_RECORDED")
    return {
        "schema": "IRE_V166_E1_CONNECTIVITY_SOURCE_AUDIT_V1",
        "baseline_static_signatures_verified": live,
        "legacy_v123_review_to_v128_storage_has_synthetic_positive_test": True,
        "typed_v164_review_to_v126_v127_v128_storage_connected": False if live else None,
        "e1_engine_pass": False,
        "next_step_authorized": False,
        "root_cause": (
            "V164 signed source-only review cannot authorize publication; "
            "V126 and V127 checkpoints directly replay frozen V123; "
            "V128 stages through V126"
            if live else "BASELINE_CHANGED_REAUDIT_REQUIRED"),
        "signatures": matches,
    }


if __name__ == "__main__":
    print(json.dumps(audit_e1(), sort_keys=True, ensure_ascii=False, indent=2))
