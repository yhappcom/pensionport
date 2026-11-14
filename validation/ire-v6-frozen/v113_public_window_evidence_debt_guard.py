"""V113 public-receipt-only scope reconciliation. NOT source-semantic certification.

Accepts only public SHA-only aggregate receipts from frozen V98/V101/V102/V109-
V112. Checks deduplicated window scope, evidence debt and no false promotions.
Cannot check original SRT bytes, non-public per-unit IDs, or historical V75 links.
"""
from __future__ import annotations
import json
from pathlib import Path

SOURCE_SHA = "00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
V109_WINDOWS = (
    ("sz5N9WJS310", "W00020"),
    ("OiDTNstaSpM", "W00008"),
    ("qtluAViPpsQ", "W00006"),
    ("4CQ4FjGT2gA", "W00065"),
)
FILENAMES = {
    "v98": "V98_FULL6_PUBLIC_SHA_ONLY_RESULT.json",
    "v101": "V101_PUBLIC_SHA_ONLY_240_CUE_CHAT_REVIEW_RECEIPT.json",
    "v102": "V102_PUBLIC_SHA_ONLY_320_CUE_OVERLAY_RECEIPT.json",
    "v109": "V109_CHAT_NATIVE_160_CUE_52_PARENT_19_SCOPE_SHA_ONLY_RECEIPT.json",
    "v110": "V110_SHA_ONLY_52_PARENT_85_UNITS_COVERAGE_RESULT.json",
    "v111": "V111_OPEN22_PUBLIC_SHA_ONLY_RESULT.json",
    "v112": "V112_SHA_ONLY_85_UNIT_STATUS_ACCOUNT_TAX_RECONCILIATION.json",
}

def require(condition, reason):
    if not condition:
        raise ValueError("V113_" + reason)

def load_receipts(directory=None):
    directory = Path(directory) if directory else Path(__file__).parent
    return {key: json.loads((directory / filename).read_text(encoding="utf-8"))
            for key, filename in FILENAMES.items()}

def audit(receipts):
    require(set(receipts) == set(FILENAMES), "INPUT_CENSUS")
    v98, v101, v102, v109, v110, v111, v112 = (
        receipts[k] for k in ("v98","v101","v102","v109","v110","v111","v112"))
    expected_schemas = {
        "v98": "V98_GENERIC_SOURCE_WIDE_ALL_CUE_PENDING_HYBRID_V1",
        "v101": "V101_6_SOURCE_WINDOWS_240_CUES_81_DRAFT_PARENTS_7_GAPS_10_SPLITS_CHAT_SHADOW_V1",
        "v102": "V102_V98_PENDING_NONMUTATING_V101_240_PLUS_V102_80_REVIEW_SHADOW_OVERLAY_V1",
        "v109": "V109_SOURCE_PINNED_CHAT_INTERNAL_QA_NO_GOLD_V1",
        "v110": "V110_SOURCE_CUE_PARENT_AND_SPEECH_ACT_COVERAGE_SHA_ONLY_NOT_SEMANTIC_GOLD_V1",
        "v111": "V111_OPEN22_SOURCE_CONTEXT_EVIDENCE_AUDIT_SHA_ONLY_NO_GOLD_V1",
        "v112": "V112_85_UNIT_ACCOUNT_TAX_SCOPE_PUBLIC_SHA_ONLY_NO_GOLD_V1",
    }
    for key, expected in expected_schemas.items():
        require(receipts[key].get("schema") == expected, "SCHEMA_" + key)
        require(receipts[key].get("p0_go") is False, "FALSE_GO_" + key)
        for score in ("certified_precision", "certified_recall", "certified_high_risk_recall"):
            if score in receipts[key]:
                require(receipts[key][score] is None, "FALSE_SCORE_" + key)
        if "independent_gold" in receipts[key]:
            require(receipts[key]["independent_gold"] is False, "FALSE_GOLD_" + key)
    for r, field in ((v98,"original_source_archive_sha256"),
                     (v109,"owner_source_sha256"),
                     (v110,"source_zip_sha256"),
                     (v111,"source_archive_sha256"),
                     (v112,"source_archive_sha256")):
        require(r.get(field) == SOURCE_SHA, "SOURCE_CUSTODY")
    require(v98["source_cues_routed"] == 15857 and v98["original_windows"] == 399
            and v98["videos"] == 6 and v98["source_first_full_semantic_review_completed"] is False,
            "V98_BASELINE")
    require(v98["priority_cues"] + v98["mandatory_fallback_cues"] == 15857,
            "V98_ROUTE_PARTITION")
    require(v98["draft_parents_pending"] == 4944 and v98["unassigned_cues_pending"] == 290,
            "V98_PARENT_BASELINE")
    require(v101["selected_windows"] == 6
            and v101["source_bound_cues_context_reviewed_chat"] == 240
            and len(v101["selected_window_summaries"]) == 6, "V101_SCOPE")
    require(v102["previous_v101_cues"] == 240 and v102["new_v102_cues_in_overlay"] == 80
            and v102["cumulative_shadow_reviewed_cues"] == 320
            and v102["still_pending_cues"] == 15537
            and len(v102["new_windows"]) == 2, "V102_SCOPE")
    require(sum(v102["pending_route_counts"].values()) == 15537
            and sum(v102["reviewed_route_counts"].values()) == 320,
            "V102_ROUTE_PARTITION")
    require(v109["source_windows_read"] == 4 and v109["source_cues_read"] == 160
            and v109["v33_draft_parent_meaning_annotations"] == 52
            and v109["independent_gold"] is False, "V109_SCOPE")
    require(v110["original_windows"] == 4 and v110["original_cues"] == 160
            and v110["v110_source_cues_accounted_including_gaps"] == 160
            and v110["parent_candidates"] == 52 and v110["v110_speech_act_units"] == 85
            and v110["unassigned_cues"] == 2, "V110_SCOPE")
    require(v111["original_open_units"] == 22
            and v111["context_resolved_units"] == 10
            and v111["still_open_units"] == 12 and v111["open_audio"] == 7
            and v111["open_visual_or_screen"] == 4 and v111["open_account_scope"] == 1,
            "V111_OPEN_CENSUS")
    require(v112["previously_open_units"] == 22 and v112["context_resolved_units"] == 10
            and v112["still_open_units"] == 12 and v112["open_audio"] == 7
            and v112["open_visual_or_account"] == 4 and v112["open_account_scope"] == 1
            and v112["no_v111_open_decision_units"] == 63 and v112["units"] == 85
            and v112["parents"] == 52, "V112_OPEN_CENSUS")
    require(v112["new_formally_approved_financial_claims"] == 0
            and v112["current_tax_personal_application_resolved"] is False
            and v112["personal_advice_approved"] is False, "FALSE_FINANCE_PROMOTION")
    require(v101["prior_v98_pending_mutated"] is False and v102["v98_baseline_mutated"] is False
            and v112["v110_v111_sources_untouched"] is True, "HISTORICAL_MUTATION")

    a = list(V109_WINDOWS)
    b = [(x["video_id"], x["window_id"]) for x in v101["selected_window_summaries"]]
    c = [tuple(x) for x in v102["new_windows"]]
    windows = a + b + c
    require(len(windows) == 12 and len(set(windows)) == 12, "WINDOW_OVERLAP")
    video_counts = v98["per_video"]
    for vid, win in windows:
        require(vid in video_counts and isinstance(win, str) and win.startswith("W")
                and win[1:].isdigit(), "WINDOW_KEY")
        window_number = int(win[1:])
        require(1 <= window_number <= video_counts[vid]["windows"], "WINDOW_OUT_OF_SCOPE")
        # A full 40-cue window is required for these selected historical cohorts.
        require(window_number * 40 <= video_counts[vid]["cue_count"], "SHORT_WINDOW_MISCOUNT")
    require(sum(s["priority_cues"] + s["fallback_cues"]
                for s in v101["selected_window_summaries"]) == 240, "V101_CUE_SUM")
    require(v102["cumulative_shadow_reviewed_cues"] + v109["source_cues_read"] == 480,
            "UNION_MISCOUNT")
    return {
        "schema": "V113_PUBLIC_RECEIPT_WINDOW_DEDUP_EVIDENCE_DEBT_NO_GOLD_V1",
        "source_archive_sha256": SOURCE_SHA,
        "scope": "V109(also V110-V112) four windows UNION V101/V102 eight windows ONLY",
        "v98_original_cues": 15857,
        "v98_original_pending_baseline_mutated": False,
        "window_footprints_nonoverlapping_in_named_three_cohorts": 12,
        "distinct_window_cues_in_named_three_cohorts": 480,
        "v102_existing_shadow_cues_not_new": 320,
        "v109_existing_reviewed_cues_not_new": 160,
        "not_in_these_12_windows": 15377,
        "prior_v92_v75_overlap_fully_reconciled": False,
        "unknown_external_original_audio_verified": False,
        "unknown_external_screen_account_sources_verified": False,
        "open_audio": 7,
        "open_visual_or_account": 4,
        "open_personal_tax_scope": 1,
        "still_open": 12,
        "independent_gold": False,
        "certified_precision": None,
        "certified_recall": None,
        "new_semantically_reviewed_cues_in_v113": 0,
        "new_formally_approved_financial_claims": 0,
        "p0_go": False
    }

def main():
    report = audit(load_receipts())
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
