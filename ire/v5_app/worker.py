"""GitHub Actions control-plane worker — never reads private source material.

A GitHub repository is durable code and metadata, not a persistent daemon.
Every request commit triggers a short-lived Actions worker that publishes the
next *ChatGPT* task. The host chat does inference and official-source research;
GitHub never invents source, evidence, verification, or advisor authorization.

The repository may be public, so strictly allow-list all public input fields.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

SCHEMA = "IRE_V5_APP_PUBLIC_COMMAND_V1"
STATE_SCHEMA = "IRE_V5_APP_PUBLIC_STATE_V1"
ID = re.compile(r"^v5-[a-z0-9][a-z0-9-]{1,50}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
VIDEO = re.compile(r"^[A-Za-z0-9_-]{11}$")
REQUEST_FILE = re.compile(r"^(\d{6})\.json$")
START_KEYS = {"schema", "job_id", "sequence", "operation", "video_id", "source_cues", "total_windows", "source_sha256"}
UPDATE_KEYS = {"schema", "job_id", "sequence", "operation", "reported_windows", "reported_claims", "reported_evidence_reviews", "reported_relation_reviews", "reported_event_receipts", "encrypted_checkpoint_sha256", "receipt_chain_sha256"}

class ControlError(ValueError):
    pass


def check(value: bool, code: str) -> None:
    if not value:
        raise ControlError(code)


def positive_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def parse_command(document: dict) -> dict:
    check(type(document) is dict, "COMMAND_NOT_OBJECT")
    op = document.get("operation")
    check(op in {"OPEN", "CHECKPOINT"}, "COMMAND_OPERATION_INVALID")
    check(set(document) == (START_KEYS if op == "OPEN" else UPDATE_KEYS), "COMMAND_EXACT_FIELD_SET_INVALID")
    check(document["schema"] == SCHEMA and type(document["job_id"]) is str and
          ID.fullmatch(document["job_id"]) is not None, "COMMAND_ID_INVALID")
    check(type(document["sequence"]) is int and document["sequence"] >= 1,
          "COMMAND_SEQUENCE_INVALID")
    if op == "OPEN":
        check(document["sequence"] == 1, "OPEN_MUST_BE_FIRST")
        check(type(document["video_id"]) is str and VIDEO.fullmatch(document["video_id"]) is not None,
              "SOURCE_VIDEO_ID_INVALID")
        check(positive_int(document["source_cues"]) and document["source_cues"] > 0 and
              positive_int(document["total_windows"]) and document["total_windows"] > 0 and
              document["total_windows"] <= document["source_cues"], "SOURCE_WINDOW_CENSUS_INVALID")
        check(type(document["source_sha256"]) is str and
              SHA256.fullmatch(document["source_sha256"]) is not None, "SOURCE_SHA_INVALID")
    else:
        for k in ("reported_windows", "reported_claims", "reported_evidence_reviews",
                  "reported_relation_reviews", "reported_event_receipts"):
            check(positive_int(document[k]), f"{k.upper()}_INVALID")
        for k in ("encrypted_checkpoint_sha256", "receipt_chain_sha256"):
            check(type(document[k]) is str and SHA256.fullmatch(document[k]) is not None,
                  f"{k.upper()}_INVALID")
        check(document["sequence"] > 1, "CHECKPOINT_REQUIRES_START")
        check(document["reported_evidence_reviews"] <= document["reported_claims"] and
              document["reported_relation_reviews"] <= document["reported_claims"],
              "REVIEWS_EXCEED_CLAIM_COUNT")
    return document


def reduce_commands(commands: list[dict]) -> dict:
    check(type(commands) is list and len(commands) > 0, "NO_COMMANDS")
    state = None
    for position, raw in enumerate(commands, 1):
        item = parse_command(raw)
        check(item["sequence"] == position, "MISSING_OR_REORDERED_SEQUENCE")
        if position == 1:
            check(item["operation"] == "OPEN", "OPEN_FIRST_REQUIRED")
            state = {
                "schema": STATE_SCHEMA,
                "job_id": item["job_id"],
                "video_id": item["video_id"],
                "source_cues_reported": item["source_cues"],
                "source_sha256_reported": item["source_sha256"],
                "total_windows_reported": item["total_windows"],
                "processed_windows_reported": 0,
                "claims_reported": 0,
                "evidence_reviews_reported": 0,
                "relation_reviews_reported": 0,
                "event_receipts_reported": 0,
                "last_encrypted_checkpoint_sha256": None,
                "last_receipt_chain_sha256": None,
                "last_sequence": 1,
            }
            continue
        check(item["operation"] == "CHECKPOINT" and
              item["job_id"] == state["job_id"], "COMMAND_JOB_OR_OPERATION_CHANGED")
        check(item["reported_windows"] >= state["processed_windows_reported"] and
              item["reported_windows"] <= state["total_windows_reported"],
              "CHECKPOINT_WINDOW_COUNT_DRIFT")
        for input_key, state_key in (
            ("reported_claims", "claims_reported"),
            ("reported_evidence_reviews", "evidence_reviews_reported"),
            ("reported_relation_reviews", "relation_reviews_reported"),
            ("reported_event_receipts", "event_receipts_reported"),
        ):
            check(item[input_key] >= state[state_key], "CHECKPOINT_METRIC_REWIND")
        check(item["reported_event_receipts"] >= item["reported_windows"],
              "CHECKPOINT_EVENTS_FEWER_THAN_WINDOWS")
        # Strict read-side, not a claim of independently executed research.
        state.update({
            "processed_windows_reported": item["reported_windows"],
            "claims_reported": item["reported_claims"],
            "evidence_reviews_reported": item["reported_evidence_reviews"],
            "relation_reviews_reported": item["reported_relation_reviews"],
            "event_receipts_reported": item["reported_event_receipts"],
            "last_encrypted_checkpoint_sha256": item["encrypted_checkpoint_sha256"],
            "last_receipt_chain_sha256": item["receipt_chain_sha256"],
            "last_sequence": position,
        })
    remaining = state["total_windows_reported"] - state["processed_windows_reported"]
    # GitHub Actions is not permitted to perform AI inference and cannot read
    # plaintext financial claims: status is NEVER a financial fact approval.
    return {
        **state,
        "remaining_windows_reported": remaining,
        "next_expected_window_hint": (f'W{state["processed_windows_reported"]+1:05d}' if remaining else None),
        "action_required": ("CHATGPT_ANALYZE_AND_VERIFY_NEXT_WINDOW" if remaining
                            else "PRIVATE_REPLAY_AND_RESEARCH_CLOSURE_AUDIT_REQUIRED"),
        "github_actions_executed_control_plane": True,
        "private_source_contents_accessible_to_github": False,
        "private_receipt_chain_verified_by_github": False,
        "official_evidence_independently_approved_by_github": False,
        "financial_advice_approved": False,
        "full_video_completed_and_verified": False,
        "public_state_verdict": "CONTROL_PLANE_READY_RESEARCH_NOT_VERIFIED",
        "no_external_llm_api_calls": True,
    }


def load_job(folder: Path) -> dict:
    check(folder.is_dir() and not folder.is_symlink() and ID.fullmatch(folder.name) is not None,
          "CONTROL_JOB_DIR_INVALID")
    contents = sorted(folder.iterdir())
    check(contents and all(p.is_file() and not p.is_symlink() and REQUEST_FILE.fullmatch(p.name) for p in contents),
          "CONTROL_JOB_FILES_INVALID")
    docs = []
    for i, path in enumerate(contents, 1):
        check(path.name == f"{i:06d}.json" and path.stat().st_size <= 16_384,
              "CONTROL_JOB_SEQUENCE_OR_SIZE_INVALID")
        doc = json.loads(path.read_text(encoding="utf-8"))
        check(doc.get("job_id") == folder.name, "CONTROL_JOB_NAME_MISMATCH")
        docs.append(doc)
    return reduce_commands(docs)


def emit_state(path: Path, state: dict) -> None:
    """Atomic state update; never write private contents to GitHub."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".v5state-", delete=False) as f:
        f.write(serialized)
        tmp = Path(f.name)
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Actions V5 public control worker")
    parser.add_argument("--requests", required=True)
    parser.add_argument("--states", required=True)
    opt = parser.parse_args()
    root, states = Path(opt.requests), Path(opt.states)
    check(root.is_dir(), "CONTROL_REQUESTS_ROOT_MISSING")
    jobs = 0
    for folder in sorted(root.iterdir()):
        check(folder.is_dir() and not folder.is_symlink() and ID.fullmatch(folder.name) is not None,
              "CONTROL_REQUEST_UNSAFE_PATH")
        status = load_job(folder)
        emit_state(states / (folder.name + ".json"), status)
        print(json.dumps({"job_id": status["job_id"],
                          "last_sequence": status["last_sequence"],
                          "next_action": status["action_required"],
                          "reported_remaining": status["remaining_windows_reported"],
                          "privacy_safe": True}, sort_keys=True))
        jobs += 1
    check(jobs > 0, "NO_CONTROL_JOBS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
