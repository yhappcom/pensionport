"""P1/P3/P4: reconcile public/private research progress without fictitious release.

Source SHA and compact semantics are historical research pointers, not evidence
that the current process replayed private SRT bytes. The 116 legacy claims and
all historical receipts are read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from .first_five_window_review_gate import verify as verify_288_windows
from .first_five_phase1_third_twenty_gate import verify as verify_40_windows
from .first_five_40_retrieval_bridge import load_catalog
from .first_five_40_official_replay_approval_gate import MASTER_SHA

PUBLIC = Path("ire/v5_app/batch_states/v5-gomhee-001-005-batch.json")
COMPACT = Path("ire/v5/validation/v5_first_five_video_01_window_review_20261106.json")
FORTY = Path("ire/v5/validation/first_five_phase1_video1_21_40_cue_review_20261106.json")
MASTER = Path("data/claims.jsonl")
VIDEO1_ID = "sz5N9WJS310"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ProgressReviewError(ValueError):
    pass


def require(ok: bool, error: str) -> None:
    if not ok:
        raise ProgressReviewError(error)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def audit(root: Path, *, source_zip: Path | None = None,
          compact_override: dict | None = None,
          public_override: dict | None = None) -> dict:
    root = Path(root)
    # Existing fail-closed validators remain authoritative over immutable
    # historical evidence, including the 40-window event-chain hash.
    forty = verify_40_windows(root)
    all_windows = verify_288_windows(root, source_zip=source_zip)
    public = read(root / PUBLIC) if public_override is None else public_override
    compact = read(root / COMPACT) if compact_override is None else compact_override
    batch = read(root / FORTY)

    require(public.get("windows_total_reported") == 288
            and public.get("windows_processed_reported") == 5
            and public.get("windows_remaining_reported") == 283
            and public.get("source_and_receipts_readable_by_github") is False
            and public.get("all_five_videos_research_complete") is False,
            "P1_PUBLIC_CONTROL_PLANE_FALSE_CLOSURE")
    require(forty["source_video1_reviewed_windows"] == 40
            and forty["public_control_plane_status_unchanged"] == 5
            and forty["original_source_replayed_in_this_execution"] is False
            and batch["current_total_reviewed_windows"] == 40
            and batch["public_control_plane_processed_windows_unchanged"] == 5,
            "P1_PRIVATE_REVIEW_PUBLIC_COUNT_MISMATCH")
    require(compact.get("video_id") == VIDEO1_ID
            and compact.get("window_count") == 67
            and compact.get("expected_original_cues") == 1195
            and compact.get("source_window_full_review_pass") == "PROVISIONAL_WINDOW_MEANING_ONLY"
            and compact.get("current_law_fact_research_completed") is False
            and compact.get("legacy_knowledge_approved") is False
            and compact.get("independent_atomic_claim_recall_proven") is False
            and compact.get("personalized_advice_approved") is False,
            "P3_COMPACT_REVIEW_UNSAFE_STATUS")
    rows = compact.get("records", [])
    require(type(rows) is list and len(rows) == 67, "P3_VIDEO1_67_WINDOW_REGISTER_MISSING")
    for i, row in enumerate(rows, 1):
        require(row.get("window_id") == f"W{i:05d}"
                and type(row.get("first_cue")) is int
                and type(row.get("last_cue")) is int
                and HEX64.fullmatch(str(row.get("primary_text_sha256", ""))) is not None
                and row.get("fact_approved") is False
                and row.get("personal_action_approved") is False,
                "P3_PROVISIONAL_WINDOW_INTEGRITY_FAILURE")
        if i > 1:
            require(rows[i - 2]["last_cue"] + 1 == row["first_cue"],
                    "P3_CUE_GAP_OR_OVERLAP")
    require(rows[0]["first_cue"] == 1 and rows[-1]["last_cue"] == 1195,
            "P3_VIDEO1_CUE_BOUNDARY_MISMATCH")
    require([r["window_id"] for r in rows[:40]] ==
            [f"W{i:05d}" for i in range(1, 41)],
            "P1_FIRST40_WINDOW_ID_MISMATCH")
    require(git_blob_sha((root / MASTER).read_bytes()) == MASTER_SHA,
            "P4_LEGACY_116_MASTER_CHANGED")

    # New material is a queue of prior, chat-authored provisional window
    # meanings. A supplied private archive verifies hashes of all 288 source
    # windows but does not create claims, legal facts, or review event receipts.
    queue = [
        {
            "window_id": row["window_id"],
            "first_cue": row["first_cue"],
            "last_cue": row["last_cue"],
            "source_window_sha256": row["primary_text_sha256"],
            "prior_meaning_type": row["meaning_type"],
            "prior_semantic_summary": row["semantic_summary"],
            "source_evidence_replayed_this_execution":
                all_windows["exact_private_archive_reopened_and_288_hashes_verified"],
            "atomic_claim_extraction_reapproved": False,
            "official_law_currentness_rechecked": False,
            "formal_research_receipt_issued": False,
        }
        for row in rows[40:]
    ]
    require(len(queue) == 27
            and queue[0]["window_id"] == "W00041"
            and queue[-1]["window_id"] == "W00067",
            "P3_NEXT_27_SCOPE_DRIFT")

    nodes = load_catalog(root)
    expected_ids = {x["knowledge_id"] for x in nodes}
    require(len(nodes) == len(expected_ids) == 9
            and all(not x["independent_knowledge_approved"]
                    and not x["formal_master_merged"]
                    and not x["personal_advice_approved"] for x in nodes),
            "P4_UNAPPROVED_KNOWLEDGE_MERGE")
    proposed = [
        {
            "knowledge_id": n["knowledge_id"],
            "prior_claim_ids": n["prior_claim_ids"],
            "source_claim_ids": n["source_claim_ids"],
            "relation_status": "EXISTING_SCOPED_EDUCATION_REVIEW_ONLY",
            "master_merge_committed": False,
        }
        for n in nodes
    ]
    return {
        "schema": "IRE_V5_P1_P3_P4_SCOPED_PROGRESS_AUDIT_V1",
        "P1_public_private_receipt_reconciliation": {
            "public_formal_processed_windows": 5,
            "historical_private_reviewed_windows": 40,
            "differing_record_classification": "PRIVATE_REVIEW_NOT_PUBLIC_FORMAL_RECEIPT",
            "promoted_public_processed_windows": 0,
            "historical_event_chain_mutated": False,
            "actual_private_replay_this_execution":
                all_windows["exact_private_archive_reopened_and_288_hashes_verified"],
            "research_completion": False,
        },
        "P3_video1_next_batch": {
            "video_id": VIDEO1_ID,
            "window_ids": [x["window_id"] for x in queue],
            "windows_queued": 27,
            "source_cues_queued": rows[-1]["last_cue"] - rows[39]["last_cue"],
            "queue": queue,
            "replay_verified": all_windows["exact_private_archive_reopened_and_288_hashes_verified"],
            "meaning_extraction_complete_on_original_now": False,
            "formal_source_fact_approval": False,
            "processing_status": "PROVISIONAL_RECORDS_ONLY_NOT_RESEARCH_CLOSED",
        },
        "P4_incremental_knowledge_premerge": {
            "legacy_master_claims_preserved": 116,
            "existing_scoped_education_nodes": len(proposed),
            "candidate_links": proposed,
            "master_changed": False,
            "knowledge_graph_merged": False,
            "personal_advice_release": False,
            "status": "DRY_RUN_SOURCE_BOUND_RELATIONS_ONLY",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--source-zip", type=Path)
    args = p.parse_args()
    print(json.dumps(audit(args.root, source_zip=args.source_zip),
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
