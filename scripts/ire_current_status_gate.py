#!/usr/bin/env python3
"""Validate a scoped canonical IRE research-status ledger without pretending to certify private sources.

GitHub Actions verifies reproducible public evidence references and denial of false GO.
The file does not itself create E3 TURN2, E4 owner seal, E5 publication or financial truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
LEDGER = Path("docs/IRE_CANONICAL_CURRENT_RESEARCH_STATUS_20261122.json")
INVENTORY_CONTROL = Path("data/inventory_control.json")
VIDEOS = Path("data/videos.jsonl")
CLAIMS = Path("data/claims.jsonl")
QUEUE = Path("data/learning_queue.jsonl")
ROSTER = Path("VIDEO_INVENTORY_2026-10-07.md")
ETFSOURCE = Path("validation/ire-v6-frozen/V242_E1_REAL_ETF250_B0013_CONDITION_LINKED_NATIVE_HOST_PASS_E3_E5_HOLD_20261122.md")
ACCURACY = Path("validation/ire-v6-frozen/V149_RESEARCH_ACCURACY_SHA_ONLY.json")
CHECKLIST_STATE = Path("docs/IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_20261122.json")
ALLOWED = {"PASS", "HOLD", "FAIL", "NOT_RUN", "UNMEASURABLE"}
CHECKED_STAGES = ("E1", "E2", "E3", "E4", "E5")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def row_count(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert all(json.loads(x) is not None for x in lines if x.strip())
    return sum(bool(x.strip()) for x in lines)


def validate(ledger: dict, root: Path | None = ROOT) -> list[str]:
    errors = []

    def require(ok: bool, code: str):
        if not ok:
            errors.append(code)

    require(ledger.get("schema") == "IRE_SINGLE_CANONICAL_RESEARCH_ENGINE_STATUS_V1", "SCHEMA_INVALID")
    require(ledger.get("as_of") == "2026-11-22", "STATUS_DATE_MISMATCH")
    require(ledger.get("provenance_kind") == "PUBLIC_SAFE_STATUS_RECONCILIATION_NOT_PRIVATE_ORIGINAL_BYTES", "SOURCE_SCOPE_LAUNDERED")
    require(re.fullmatch(r"[a-f0-9]{40}", str(ledger.get("evidence_snapshot_commit", ""))) is not None, "NO_FROZEN_REVIEW_COMMIT")
    require(ledger.get("branch") == "audit/full-repository-snapshot-20261122", "WRONG_TARGET_BRANCH")
    require(len(ledger.get("evidence_sources", {})) >= 14, "EVIDENCE_CENSUS_TRUNCATED")

    s = ledger.get("stages", {})
    require(set(s) == set(CHECKED_STAGES), "STAGE_SET_MISMATCH")
    for k in CHECKED_STAGES:
        d = s.get(k, {})
        require(d.get("official_stage_release") in ALLOWED, "BAD_STATUS_" + k)
        require(d.get("official_stage_release") == "HOLD", "UNSUPPORTED_ACTUAL_APPROVAL_" + k)
        require(bool(d.get("evidence_keys")), "MISSING_STAGE_SOURCES_" + k)
        require(all(key in ledger.get("evidence_sources", {}) for key in d.get("evidence_keys", [])), "UNRESOLVED_STAGE_EVIDENCE_" + k)

    etf = ledger.get("reference_cohort", {})
    require(etf.get("video_id") == "LVE7XN_esTc", "ETF_ID_CHANGED")
    require(etf.get("cue_count") == 250, "ETF_CUE_COUNT_MISREPRESENTED")
    require(etf.get("provisional_atom_candidates") == 68, "ETF_ATOM_CANDIDATES_MISREPRESENTED")
    require(etf.get("planned_child_scopes") == 13, "ETF_CHILD_SCOPE_COUNT_MISREPRESENTED")
    require(etf.get("staged_structural_child_hosts") == 13, "ETF_HOST_COUNT_MISREPRESENTED")
    require(etf.get("locally_complete_child_hosts") == 12, "ETF_NONPROVISIONAL_CHILD_COUNT_MISREPRESENTED")
    require(etf.get("parent_external_qualifier_provisional_child_hosts") == 1, "ETF_B0013_PROVISIONAL_LOST")
    require(etf.get("cross_parent_atoms_requiring_meaning_reconciliation") == 21, "ETF_PARENT_ATOMS_LOST")
    require(etf.get("cross_parent_qualifier_edges") == 49, "ETF_QUALIFIER_EDGES_LOST")
    require(etf.get("structural_events_reported") == 78, "STRUCTURAL_EVENT_SCOPE_MISREPRESENTED")
    require(len(str(etf.get("original_source_sha256", ""))) == 64, "ORIGINAL_SHA_UNPINNED")
    require(etf.get("original_private_srt_bytes_verified_in_this_turn") is False, "PRIVATE_SRT_REPLAY_FALSELY_CLAIMED")
    require(etf.get("complete_independent_gold_available") is False, "INDEPENDENT_GOLD_FALSELY_CLAIMED")
    require(etf.get("actual_user_etf_turn2_final_verdict_proven") is False, "ETFTURN2_FALSELY_CLAIMED")

    for key in ("actual_formal_v123_child_approvals", "actual_e4_authorized_child_count", "actual_e5_publications", "actual_e5_knowledge_rows"):
        require(type(etf.get(key)) is int and etf.get(key) == 0, "ETFTURN_FINAL_APPROVAL_OR_PUBLICATION_FALSE_GO_" + key)

    require(s.get("E1", {}).get("synthetic_software_route", {}).get("status") == "PASS", "SYNTHETIC_E1_BASELINE_LOST")
    require(s.get("E1", {}).get("actual_source_structural_host", {}).get("status") == "PASS", "REAL_STRUCTURAL_SCOPE_LOST")
    require(s.get("E1", {}).get("end_to_end_real_owner_approval_route", {}).get("status") == "HOLD", "E1_E2E5_REAL_FALSE_GO")
    require(s.get("E2", {}).get("independent_gold_status") == "UNMEASURABLE", "UNSUPPORTED_INDEPENDENT_GOLD")
    for k in ("independently_certified_precision", "independently_certified_recall", "independently_certified_high_risk_false_negative_count"):
        require(s.get("E2", {}).get(k) is None, "UNKNOWN_ACCURACY_REPLACED_WITH_NUMBER_" + k)
    require(s.get("E3", {}).get("actual_etf_final_v123_approved_children") == 0, "E3_FALSE_APPROVAL")
    require(s.get("E3", {}).get("actual_etf_planned_v123_children") == 13, "E3_WRONG_DENOMINATOR")
    require(s.get("E3", {}).get("host_cryptographic_two_turn_authenticity_verified") is False, "HOST_PROOF_UNAVAILABLE")
    require(s.get("E4", {}).get("actual_etf_owner_seal_verified") is False, "E4_FALSE_SEAL")
    require(s.get("E4", {}).get("actual_etf_official_primary_evidence_complete") is False, "E4_FALSE_OFFICIAL_COMPLIANCE")
    require(s.get("E4", {}).get("actual_etf_authorized_children") == 0, "E4_FALSE_AUTHORIZATION")
    require(s.get("E5", {}).get("actual_etf_parent_publications") == 0, "E5_FALSE_PUBLICATION")
    require(s.get("E5", {}).get("actual_etf_published_knowledge_rows") == 0, "E5_FALSE_KNOWLEDGE")
    require(s.get("E5", {}).get("actual_parent_pub_receipt_verified") is False, "E5_FALSE_RECEIPT")

    video = ledger.get("video_denominators", {})
    roster = video.get("canonical_roster", {})
    require(roster.get("denominator_kind") == "UNIQUE_VIDEO_ID_ROSTER_AS_OF_2026_10_07", "ROSTER_SCOPE_MIXED")
    require((roster.get("total"), roster.get("long_form"), roster.get("shorts")) == (791, 703, 88), "ROSTER_COUNTS_INCONSISTENT")
    require(roster.get("long_form", 0) + roster.get("shorts", 0) == roster.get("total"), "ROSTER_DOES_NOT_SUM")
    require(roster.get("unconfirmed_publication_metadata") == 155, "ROSTER_METADATA_LOST")
    legacy = video.get("legacy_records", {})
    require(legacy.get("denominator_kind") == "HISTORICAL_TRACKED_FILE_ROW_COUNT_NOT_E5", "LEGACY_RECORD_AS_E5")
    require((legacy.get("videos_jsonl_rows"), legacy.get("claims_jsonl_rows"), legacy.get("learning_queue_jsonl_rows")) == (157, 116, 211), "LEGACY_COUNTER_SCOPE_CHANGED")
    require(legacy.get("inventory_control_recorded_canonical_sequences_at_2026_10_07") == 156, "OLD_CONTROL_SNAPSHOT_DRIFT")
    require(legacy.get("non_e5_reconciliation_required") is True, "LEGACY_RECONCILIATION_FALSELY_CLOSED")
    for k in ("certified_e5_research_published_videos_total", "entire_roster_e2_semantically_verified_videos_total", "certified_791_video_completion_ratio"):
        require(video.get(k) is None, "UNKNOWN_ALL_ROSTER_APPROVAL_COUNT_FILLED_" + k)
    require(video.get("scoped_etf_real_e5_published_videos") == 0, "ETF_VIDEO_PUBLICATION_FALSE_GO")

    advisory = ledger.get("advisory", {})
    require(advisory.get("official_release") == "HOLD", "ADVISORY_FALSE_GO")
    for k in ("verified_e5_knowledge_used_for_advice", "updated_current_official_rule_per_answer_end_to_end_certified", "personal_eligibility_validated", "investor_portfolio_google_drive_connected_to_engine", "personalized_recommendation_authorized"):
        require(advisory.get(k) is False, "ADVISORY_SCOPE_FALSE_GO_" + k)
    a = ledger.get("accuracy_and_context", {})
    require(a.get("etf_source_first_gold", {}).get("status") == "UNMEASURABLE", "ETF_GOLD_FALSELY_CERTIFIED")
    require(all(a.get("etf_source_first_gold", {}).get(k) is None for k in ("precision", "recall", "high_risk_fn")), "ETF_ACCURACY_FAKE_NUMBER")
    other = a.get("historical_v149_internal_other_original", {})
    require(other.get("status") == "INTERNAL_ONLY_NOT_ETF" and other.get("independently_certified") is False, "OTHER_SCOPE_P_R_LAUNDERED")
    for key in ("current_official_financial_research_go", "current_complete_research_engine_go", "current_personal_investment_advisory_go", "portfolio_linkage_go"):
        require(a.get(key) is False, "RELEASE_GATE_FALSE_GO_" + key)

    pending = ledger.get("open_blockers", [])
    require(len(pending) >= 9, "OPEN_BLOCKERS_DROPPED")
    require(all(x.get("status") == "HOLD" and x.get("reason") for x in pending), "OPEN_BLOCKERS_LAUNDERED")
    require(len(set(x.get("id") for x in pending)) == len(pending), "OPEN_BLOCKER_IDS_DUPLICATE")
    dev = ledger.get("development_gate", {})
    require(dev.get("this_item") == "P0-0-02", "WRONG_CHECKLIST_ITEM")
    require(dev.get("not_a_checklist_pass_receipt") is True, "STATUS_DOCUMENT_AS_CI_PASS")
    require(dev.get("implementation_ci_has_full_pinned_python311_v3_v5_v6_e1e5_run") is False, "FULL_CI_FALSELY_CLAIMED")

    if root is not None:
        for path, source in ledger.get("evidence_sources", {}).items():
            p = (root / path).resolve()
            require(p.is_relative_to(root.resolve()) and p.is_file(), "SOURCE_PATH_MISSING_OR_ESCAPE_" + path)
            if p.is_file():
                require(git_blob_sha(p.read_bytes()) == source.get("git_blob_sha"), "EVIDENCE_BLOB_CHANGED_" + path)
        try:
            inventory = load(root / INVENTORY_CONTROL)
            inventory_counts = inventory["roster"]
            require((inventory_counts["total_unique_video_ids"], inventory_counts["long_form"], inventory_counts["shorts"]) == (roster["total"], roster["long_form"], roster["shorts"]), "CONTROL_ROSTER_COUNT_MISMATCH")
            require(inventory["current_state"]["canonical_sequences"] == legacy["inventory_control_recorded_canonical_sequences_at_2026_10_07"], "CONTROL_SNAPSHOT_MISMATCH")
            for path, key in ((VIDEOS, "videos_jsonl_rows"), (CLAIMS, "claims_jsonl_rows"), (QUEUE, "learning_queue_jsonl_rows")):
                require(row_count(root / path) == legacy[key], "ROW_COUNT_MISMATCH_" + key)
            roster_content = (root / ROSTER).read_text(encoding="utf-8")
            for expected in ("전체 고유 Video ID: **791**", "롱폼: **703**", "Shorts: **88**", "게시일 메타데이터 미확인: **155**"):
                require(expected in roster_content, "ROSTER_MARKDOWN_MISMATCH_" + expected)
            etf_doc = (root / ETFSOURCE).read_text(encoding="utf-8")
            require("13/13" in etf_doc and "78 events" in etf_doc and "0/13" in etf_doc, "ETF_STRUCTURAL_VS_RELEASE_EVIDENCE_MISSING")
            old_accuracy = load(root / ACCURACY)
            require(old_accuracy["original_cues"] == other["source_cue_count"] == 1481, "INTERNAL_OTHER_ORIGINAL_SCOPE_MISMATCH")
            require(old_accuracy["b0013_internal_atomic_score"]["precision"] == other["internal_precision"], "INTERNAL_PRECISION_SCOPE_MISMATCH")
            checklist = load(root / CHECKLIST_STATE)
            require(checklist["items"][0]["status"] == "PASS", "PRECEDING_CHECKLIST_NOT_PASS")
            require(checklist["items"][1]["id"] == "P0-0-02" and checklist["items"][1]["status"] in {"READY", "IN_PROGRESS", "FAIL", "HOLD", "PASS"}, "CHECKLIST_STATE_NOT_P0_0_02")
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
            errors.append("EVIDENCE_EXCEPTION_" + str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "status"), nargs="?", default="verify")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    ledger = load(args.root / LEDGER)
    errors = validate(ledger, args.root.resolve())
    if errors:
        for x in errors:
            print("CURRENT_STATUS_GATE_FAIL", x, file=sys.stderr)
        return 1
    etf = ledger["reference_cohort"]
    print("CURRENT_STATUS_GATE_PASS source_count=%d roster=%d/%d/%d cue=%d atoms=%d staged_children=%d approved_v123=%d e5_publications=%d" % (
        len(ledger["evidence_sources"]), ledger["video_denominators"]["canonical_roster"]["total"],
        ledger["video_denominators"]["canonical_roster"]["long_form"], ledger["video_denominators"]["canonical_roster"]["shorts"],
        etf["cue_count"], etf["provisional_atom_candidates"], etf["staged_structural_child_hosts"],
        etf["actual_formal_v123_child_approvals"], etf["actual_e5_publications"]))
    if args.command == "status":
        for name, detail in ledger["stages"].items():
            print(name, detail["official_stage_release"])
        print("ADVISORY", ledger["advisory"]["official_release"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
