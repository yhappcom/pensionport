"""V5 verification decision and source-readiness gate for original videos #1-#5.

No raw SRT text enters public Git. GitHub CI checks honest recorded state.
When a private --source-zip is supplied, *actual bytes* of 5 original SRTs,
their SHA256, timecodes and cue continuity are verified. This still does not
claim semantic/financial-research completion or personal-advice approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ASSESSMENT = Path("ire/v5/validation/engine_research_readiness_20261105.json")
MANIFEST = Path("ire/v5/validation/first_five_source_manifest_20261105.json")
PUBLIC_STATE = Path("ire/v5_app/batch_states/v5-gomhee-001-005-batch.json")
_TIMELINE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})(?:\s+.*)?$"
)

class ResearchReadinessError(ValueError):
    pass

def require(ok: bool, code: str) -> None:
    if not ok:
        raise ResearchReadinessError(code)

def _load(root: Path, p: Path) -> dict:
    return json.loads((root / p).read_text(encoding="utf-8"))

def _millis(pieces: tuple[str, ...]) -> int:
    h, m, s, ms = [int(v) for v in pieces]
    require(m < 60 and s < 60, "SOURCE_TIMESTAMP_MALFORMED")
    return ((h * 60 + m) * 60 + s) * 1000 + ms

def _validate_cues(data: bytes, count: int) -> None:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ResearchReadinessError("SOURCE_UTF8_UNREADABLE") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = re.split(r"\n[ \t]*\n", text)
    require(len(blocks) == count, "SOURCE_CUE_COUNT_MISMATCH")
    previous_start = -1
    for expected, block in enumerate(blocks, 1):
        lines = [z.strip() for z in block.split("\n") if z.strip()]
        require(len(lines) >= 3 and lines[0].isdigit()
                and int(lines[0]) == expected,
                "SOURCE_CUE_SEQUENCE_GAP_OR_CONTENT_MISSING")
        match = _TIMELINE.fullmatch(lines[1])
        require(match is not None, "SOURCE_CUE_TIMECODE_MISSING")
        parts = match.groups()
        start = _millis(parts[:4])
        end = _millis(parts[4:])
        require(end > start and start >= previous_start,
                "SOURCE_TIMING_NONMONOTONIC_OR_NEGATIVE")
        previous_start = start

def inspect_source_zip(zip_path: Path, expected_rows: list[dict]) -> dict:
    zip_path = Path(zip_path)
    require(zip_path.is_file(), "FIRST_FIVE_SOURCE_ZIP_NOT_FOUND")
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            results = []
            for row in expected_rows:
                video_id = row["video_id"]
                # Match the whole YouTube ID in the SRT basename, not a partial
                # ID, folder, macOS resource fork or same-topic transcript.
                candidates = [
                    n for n in names if not n.startswith("__MACOSX/")
                    and not Path(n).name.startswith("._")
                    and Path(n).name.lower().endswith(".srt")
                    and re.fullmatch(
                        rf"(?:youtube-transcript-)?{re.escape(video_id)}\.srt",
                        Path(n).name, flags=re.IGNORECASE)
                ]
                require(len(candidates) == 1,
                        "FIRST_FIVE_SRT_NOT_FOUND_OR_DUPLICATED_" + video_id)
                data = z.read(candidates[0])
                sha = hashlib.sha256(data).hexdigest()
                require(sha == row["source_sha256"],
                        "FIRST_FIVE_SRT_SHA256_MISMATCH_" + video_id)
                _validate_cues(data, row["expected_cues"])
                results.append({
                    "sequence": row["sequence"],
                    "video_id": video_id,
                    "sha256": sha,
                    "cue_count": row["expected_cues"],
                    "original_bytes_checked": True,
                    "semantic_research_complete": False
                })
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ResearchReadinessError("FIRST_FIVE_SOURCE_ZIP_UNREADABLE") from exc
    require(len(results) == 5
            and sum(row["cue_count"] for row in results) == 5129,
            "FIRST_FIVE_SOURCE_TOTAL_MISMATCH")
    return {
        "source_archive_file_supplied": True,
        "all_five_original_srt_byte_integrity_verified": True,
        "verified_srt_files": 5,
        "verified_cues": sum(row["cue_count"] for row in results),
        "full_semantic_extraction_completed": False,
        "research_knowledge_merge_approved": False,
        "videos": results
    }

def verify(root: Path, assessment: dict | None = None,
           manifest: dict | None = None,
           source_zip: Path | None = None) -> dict:
    root = Path(root)
    assess = _load(root, ASSESSMENT) if assessment is None else assessment
    source = _load(root, MANIFEST) if manifest is None else manifest
    public = _load(root, PUBLIC_STATE)
    sw = assess.get("software_ci", {})
    research = assess.get("research", {})
    decision = assess.get("workflow_decision", {})
    must_zip_missing = source_zip is None
    require(
        assess.get("schema") == "IRE_V5_ENGINE_RESEARCH_READINESS_ASSESSMENT_V1"
        and assess.get("assessment_date") == "2026-11-05"
        and assess.get("basis_head_sha") ==
            "84b03a38ed6a959a10b036b535e936f29df0e9c1"
        and sw.get("both_runs_completed_success_at_basis_head") is True
        and sw.get("workflow_run_ids") == [41985750452, 41985755493]
        and sw.get("preflight_gates_passed") == 29
        and sw.get("regression_tests_run") == 415
        and sw.get("tests_failed") == 0
        and sw.get("semantic_research_accuracy_proven_by_ci") is False,
        "ENGINE_VALIDATION_SOFTWARE_EVIDENCE_INVALID")
    require(
        research.get("full_engine_factual_validation_completed") is False
        and research.get("phase1_first_five_original_cue_completeness_proven") is False
        and research.get("source_zip_for_first_five_currently_available") is False
        and research.get("source_srt_text_currently_read_this_turn") is False
        and research.get("personal_investment_advice_approved") is False
        and decision.get("engine_fully_verified") is False
        and decision.get("broad_corpus_expansion") == "NO_GO"
        and decision.get("pilot_semantic_research") ==
            "NO_GO_UNTIL_PRIVATE_RAW_SOURCE_REVERIFIED"
        and decision.get("pilot_first_five_source_intake") ==
            "CONDITIONAL_GO_SOURCE_ZIP_REQUIRED",
        "ENGINE_FALSE_FULL_RESEARCH_APPROVAL")
    require(
        public.get("schema") == "IRE_V5_APP_FIVE_VIDEO_PUBLIC_STATE_V1"
        and public.get("all_five_videos_research_complete") is False
        and public.get("single_chat_turn_five_video_research_proven") is False
        and public.get("source_and_receipts_readable_by_github") is False
        and public.get("public_state_verdict") ==
            "BATCH_CONTROL_READY_RESEARCH_UNVERIFIED"
        and public.get("total_cues_reported") == 5129
        and public.get("windows_total_reported") == 288
        and public.get("windows_processed_reported") == 5
        and public.get("windows_remaining_reported") == 283,
        "ENGINE_FIRST_FIVE_PUBLIC_STATE_NOT_FULLY_VERIFIED")
    require(
        research.get("reported_total_cues") == public["total_cues_reported"]
        and research.get("reported_total_windows") == public["windows_total_reported"]
        and research.get("processed_windows_public_state") ==
            public["windows_processed_reported"]
        and research.get("windows_not_confirmed_processed") ==
            public["windows_remaining_reported"]
        and research.get("legacy_claims_indexed") == 116
        and research.get("legacy_claims_detailed_source_document_triaged") == 60
        and research.get("legacy_claims_not_yet_detailed_triaged") == 56
        and research.get("education_knowledge_topics") == 13,
        "ENGINE_RESEARCH_PROGRESS_MISSTATED")
    require(
        source.get("schema") == "IRE_V5_FIRST_FIVE_SOURCE_REENTRY_V1"
        and source.get("archive_expected") == "1-100.zip"
        and source.get("original_source_available_in_this_turn") is False
        and source.get("allow_existing_encrypted_git_backups_as_plaintext") is False
        and source.get("raw_original_text_stored_in_public_repo") is False
        and source.get("archived_sha256_for_1_100_zip_known") is False
        and source.get("expected_total_video_count") == 5
        and source.get("expected_total_cues") == 5129
        and source.get("expected_total_windows") == 288
        and source.get("public_state_windows_processed") == 5,
        "ENGINE_SOURCE_PROVENANCE_UNTRUSTWORTHY")
    items = source.get("videos", [])
    original = public.get("videos", [])
    require(len(items) == len(original) == 5,
            "ENGINE_FIRST_FIVE_ROSTER_COUNT_CHANGED")
    for i, (row, prev) in enumerate(zip(items, original), 1):
        require(
            row.get("sequence") == i
            and row.get("video_id") == prev.get("video_id")
            and row.get("source_sha256") == prev.get("source_sha256")
            and row.get("expected_cues") == prev.get("source_cues")
            and row.get("source_windows_expected") == prev.get("windows_total")
            and row.get("source_windows_processed_in_public_state") ==
                prev.get("processed_windows_reported")
            and row.get("source_windows_not_confirmed_as_processed") ==
                prev["windows_total"] - prev["processed_windows_reported"]
            and row.get("archive_currently_available_in_active_chat") is False
            and row.get("content_independently_reverified_in_this_turn") is False,
            "ENGINE_SOURCE_VIDEO_OR_HASH_FORGED")
    require(sum(x["expected_cues"] for x in items) == 5129
            and sum(x["source_windows_expected"] for x in items) == 288
            and sum(x["source_windows_processed_in_public_state"]
                    for x in items) == 5,
            "ENGINE_SOURCE_TOTALS_MISMATCH")
    checked = inspect_source_zip(source_zip, items) if not must_zip_missing else {
        "source_archive_file_supplied": False,
        "all_five_original_srt_byte_integrity_verified": False,
        "verified_srt_files": 0,
        "verified_cues": 0,
        "full_semantic_extraction_completed": False,
        "research_knowledge_merge_approved": False,
        "blocking_input": "PRIVATE_1-100_ZIP_WITH_FIVE_SOURCE_SRT_REQUIRED"
    }
    return {
        "schema": "IRE_V5_ENGINE_QUALITY_GATE_V1",
        "basis_head_sha": assess["basis_head_sha"],
        "software_ci_verified_at_basis_head": True,
        "software_preflight_gates_at_basis_head": 29,
        "full_research_engine_validation_completed": False,
        "first_five_public_processed_windows": 5,
        "first_five_total_windows": 288,
        "first_five_unconfirmed_windows": 283,
        "advisory_approval": False,
        "broad_corpus_research_go": False,
        "first_five_original_source_check": checked,
        "next_permitted_stage": (
            "FIRST_FIVE_FULL_SOURCE_SEMANTIC_REVIEW"
            if checked["all_five_original_srt_byte_integrity_verified"]
            else "FIRST_FIVE_SOURCE_REACQUISITION"
        ),
        "private_source_bytes_persisted_to_git": False
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source-zip", type=Path, default=None)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, source_zip=args.source_zip),
                     ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
