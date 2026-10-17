#!/usr/bin/env python3
"""Read-only audit of 박곰희TV subtitle reviews and canonical promotion gates.

Usage:
  python scripts/audit_subtitle_review_gate.py --root .
  python scripts/audit_subtitle_review_gate.py --root . --check-candidate my.json
  python scripts/audit_subtitle_review_gate.py --self-test

Never alters project files. Old V3 analysis records are grandfathered as
records, NOT retrospectively certified as claim-by-claim source-verified.
"""
import argparse
import csv
import json
import re
import sys
import tempfile
from pathlib import Path

YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL = re.compile(r"^https://(www\\.)?(youtube\\.com/watch\\?v=|youtu\\.be/)")
DYNAMIC = re.compile(
    r"세금|세율|세액|비과세|분리과세|연금|증여|ISA|IRP|과세|원금|보장|"
    r"금리|수익률|환율|법률|인출|공제|가입|한도|결제|상장폐지|수수료",
    flags=re.I,
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def actual_roster(root):
    with (root / "data/subtitles/roster_20261007.csv").open(
        encoding="utf-8-sig", newline=""
    ) as fh:
        rows = list(csv.DictReader(fh))
    return {x["video_id"]: int(x["roster_no"]) for x in rows}



def registered_sources(root):
    """Merge only independently preflighted, source-reviewed later SRT IDs.

    Existing 1-70 private registry remains unchanged. New 71-100 rows are
    eligible only when marked reviewed and source fingerprint/roster match.
    Unavailable #71 and mere CRC-validated future rows are never promoted.
    """
    registry = dict(load(root / "data/subtitles/registry.json")["items"])
    later = root / "data/subtitles/registry_71_100_20261013.json"
    if not later.is_file():
        return registry
    extension = load(later)
    if (extension.get("source_archive_sha256")
            != "69be8639162f8e00bfa09f0d4b8a6fe95db0a07054ad370709ce0d4e53628b5f"
            or extension.get("received_private_srt_count") != 29
            or extension.get("preflight_crc") != "PASS"):
        raise ValueError("LATER_SRT_REGISTRY_PROVENANCE_INVALID")
    roster = actual_roster(root)
    for row in extension.get("items", []):
        if row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3":
            continue
        video_id, sha = row.get("video_id"), row.get("sha256")
        if (not isinstance(video_id, str) or not YT_ID.fullmatch(video_id)
                or not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{64}", sha)
                or row.get("roster_no") != roster.get(video_id)
                or not isinstance(row.get("cue_count"), int)
                or row["cue_count"] <= 0 or video_id in registry):
            raise ValueError("LATER_SRT_REVIEWED_ROW_UNTRUSTED")
        registry[video_id] = {"sha256": sha, "cue_count": row["cue_count"]}
    # 2026-10-18: 29 freshly uploaded private SRT files (#101-129).
    # Only explicitly V3-reviewed rows with true raw-file SHA preflight are
    # registered; the other rows must remain source-intake only.
    additional = root / "data/subtitles/registry_101_129_20261018.json"
    if additional.is_file():
        a = load(additional)
        if (a.get("source_archive_sha256")
                != "3e3e7cbbccd95262ba43506ac642ff78d78afeb54de718bf574b4f78cb650951"
                or a.get("source_archive_bytes") != 477242
                or a.get("archive_crc") != "PASS_ALL"
                or len(a.get("items", [])) != 29
                or a.get("total_cues") != 17701
                or a.get("total_srt_bytes") != 1352355):
            raise ValueError("BATCH_101_129_SOURCE_INTEGRITY_MISMATCH")
        new_ids = set()
        for row in a["items"]:
            video_id, sha = row.get("video_id"), row.get("sha256")
            n = row.get("roster_no")
            if (not isinstance(video_id, str) or not YT_ID.fullmatch(video_id)
                    or n != roster.get(video_id) or n not in range(101, 130)
                    or video_id in new_ids or not isinstance(sha, str)
                    or not re.fullmatch(r"[a-f0-9]{64}", sha)
                    or not isinstance(row.get("cue_count"), int)
                    or row["cue_count"] < 1
                    or not isinstance(row.get("raw_srt_bytes"), int)
                    or row["raw_srt_bytes"] < 1):
                raise ValueError("BATCH_101_129_UNTRUSTED_ENTRY")
            new_ids.add(video_id)
            if row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3":
                continue
            if (row.get("full_transcript_reviewed") is not True
                    or row.get("v3_status") != "APPROVED"
                    or video_id in registry):
                raise ValueError("BATCH_101_129_UNTRUSTED_PROMOTION")
            registry[video_id] = {"sha256": sha, "cue_count": row["cue_count"]}
        if len(new_ids) != 29:
            raise ValueError("BATCH_101_129_MISSING_VIDEOS")
    return registry


def verified_video71_public_equivalence(pilot, video_id):
    """Exception ONLY for same-video first-party complete ASR matched to public timed cues.

    Does NOT assert original private SRT bytes, audio, or exact millisecond onset.
    """
    if video_id != "4vNF2fui5jc" or pilot.get("roster_no") != 71:
        return False
    a = pilot.get("source_audit") or {}
    return all((
        a.get("source_kind") == "INDEPENDENT_FULL_KOREAN_TRANSCRIPT",
        a.get("first_party_youtube_transcript_verified") is True,
        a.get("youtube_native_ko_asr_track_found") is True,
        a.get("full_text_exact_match") is True,
        a.get("full_transcript_reviewed") is True,
        a.get("video_id_matched") is True,
        a.get("timestamps_approximate") is True,
        a.get("third_party_timed_cues") == 1620,
        a.get("private_original_srt_available") is False,
        a.get("normalized_characters") == 21424,
        a.get("first_party_transcript_normalized_sha256")
           == "75c5344077f5ee0aacac242903f8b07ed523a1ba991fd80732a8ff8dc199736c",
        a.get("third_party_timed_normalized_sha256")
           == "75c5344077f5ee0aacac242903f8b07ed523a1ba991fd80732a8ff8dc199736c",
        a.get("first_party_source_url")
           == "https://www.youtube.com/watch?v=4vNF2fui5jc",
        a.get("timed_source_url")
           == "https://yoututranscript.com/transcript/4vNF2fui5jc",
    ))


def integrity(pilot, video_id, registry, roster):
    issues = []
    if pilot.get("video_id") != video_id:
        issues.append("VIDEO_ID_MISMATCH")
    if not YT_ID.fullmatch(video_id):
        issues.append("INVALID_VIDEO_ID")
    if pilot.get("roster_no") != roster.get(video_id):
        issues.append("ROSTER_MISMATCH")
    if video_id not in pilot.get("source_url", ""):
        issues.append("SOURCE_VIDEO_ID_MISMATCH")
    if pilot.get("stage") != "EVIDENCE_REVIEW_DRAFT" or pilot.get("approval") != "NOT_APPROVED":
        issues.append("PILOT_CLAIMS_APPROVAL")
    claims = pilot.get("claims", [])
    if not isinstance(claims, list) or not claims:
        issues.append("NO_CLAIMS")
        claims = []
    ids = [c.get("claim_id") for c in claims if isinstance(c, dict)]
    if any(not x for x in ids) or len(set(ids)) != len(claims):
        issues.append("CLAIM_IDS_INVALID_OR_DUPLICATE")
    for c in claims:
        if not isinstance(c, dict) or not all(c.get(k) for k in ("timecode", "source_paraphrase", "independent_check")):
            issues.append("CLAIM_CONTENT_INCOMPLETE")
            break
    ref = registry.get(video_id, {})
    expected_hash = ref.get("sha256")
    external = pilot.get("existing_registry_srt") or {}
    draft_hash = external.get("sha256") or pilot.get("subtitle_sha256")
    if expected_hash and draft_hash != expected_hash:
        issues.append("REGISTERED_SRT_HASH_MISMATCH")
    if not expected_hash and not verified_video71_public_equivalence(pilot, video_id):
        issues.append("NO_REGISTERED_SRT")
    return sorted(set(issues))


def source_gate(pilot):
    """Metadata hash is not the same as an independent transcript comparison."""
    s = pilot.get("source_audit", {})
    if s.get("full_transcript_reviewed") is not True:
        return "FULL_TRANSCRIPT_REVIEW_NOT_ATTESTED"
    if s.get("video_id_matched") is not True:
        return "TRANSCRIPT_VIDEO_ID_NOT_ATTESTED"
    if s.get("source_kind") not in ("ORIGINAL_SRT_RECONCILED", "INDEPENDENT_FULL_KOREAN_TRANSCRIPT"):
        return "SOURCE_KIND_NOT_ATTESTED"
    if not s.get("evidence_reference") or not s.get("limitations"):
        return "SOURCE_PROVENANCE_INCOMPLETE"
    if s["source_kind"] == "ORIGINAL_SRT_RECONCILED" and s.get("original_srt_sha256") != (pilot.get("existing_registry_srt") or {}).get("sha256", pilot.get("subtitle_sha256")):
        return "ORIGINAL_SRT_HASH_NOT_RECONCILED"
    if s["source_kind"] == "INDEPENDENT_FULL_KOREAN_TRANSCRIPT" and s.get("timestamps_approximate") is not True and s.get("precise_timing_verified") is not True:
        return "TIME_PRECISION_UNDECLARED"
    if pilot.get("video_id") == "4vNF2fui5jc" and not verified_video71_public_equivalence(pilot, pilot.get("video_id")):
        return "VIDEO71_PUBLIC_EQUIVALENCE_UNPROVEN"
    return None


def claim_evidence_gate(pilot):
    """A URL list / independent_check prose does NOT prove source verification."""
    missing = []
    for c in pilot.get("claims", []):
        e = c.get("verification_evidence")
        if not isinstance(e, dict) or e.get("verdict") not in (
            "PRIMARY_CONFIRMED", "QUALIFIED", "SPEAKER_OPINION", "HYPOTHETICAL", "CONTRADICTED"
        ):
            missing.append(c.get("claim_id", "MISSING_CLAIM_ID"))
            continue
        if e["verdict"] in ("PRIMARY_CONFIRMED", "QUALIFIED", "CONTRADICTED"):
            needed = ("primary_url", "checked_at", "source_finding", "effective_date_or_scope", "disposition")
            if any(not e.get(k) for k in needed):
                missing.append(c.get("claim_id", "MISSING_CLAIM_ID"))
            elif not DATE.fullmatch(str(e["checked_at"])):
                missing.append(c.get("claim_id", "MISSING_CLAIM_ID"))
        elif e["verdict"] in ("SPEAKER_OPINION", "HYPOTHETICAL"):
            if not e.get("disposition") or not e.get("basis"):
                missing.append(c.get("claim_id", "MISSING_CLAIM_ID"))
            if e["verdict"] == "SPEAKER_OPINION" and DYNAMIC.search(c.get("source_paraphrase", "")):
                # Tax and monetary specifics cannot be laundered into opinion.
                missing.append(c.get("claim_id", "MISSING_CLAIM_ID"))
    return sorted(set(missing))


def promotion_decision(pilot, video_id, registry, roster):
    problems = integrity(pilot, video_id, registry, roster)
    sg = source_gate(pilot)
    if sg:
        problems.append(sg)
    missing_evidence = claim_evidence_gate(pilot)
    if missing_evidence:
        problems.append("CLAIM_EVIDENCE_MISSING")
    if any(c.get("verification_evidence", {}).get("verdict") == "CONTRADICTED"
           and not c.get("verification_evidence", {}).get("correction")
           for c in pilot.get("claims", [])):
        problems.append("UNCORRECTED_CONTRADICTION")
    return {
        "eligible": not problems,
        "blockers": sorted(set(problems)),
        "claims_needing_evidence": missing_evidence,
    }


def candidate_decision(candidate):
    """New canonical V4 gate. Never grants approval to legacy files by default."""
    problems = []
    video_id = candidate.get("video_id", "")
    if not YT_ID.fullmatch(video_id) or video_id not in candidate.get("source_url", ""):
        problems.append("VIDEO_SOURCE_MISMATCH")
    if candidate.get("analysis_status") != "COMPLETE":
        problems.append("NOT_COMPLETE")
    if candidate.get("approval") != "APPROVED":
        problems.append("NOT_APPROVED")
    for key in ("source_level", "title", "core_claims", "actionable_guidance",
                "assumptions", "risks_and_exceptions", "quantitative_claims",
                "relations", "verification_status", "limitations"):
        if not candidate.get(key):
            problems.append("MISSING_" + key.upper())
    gate = candidate.get("evidence_gate", {})
    if gate.get("version") != 1 or gate.get("source_checked") is not True:
        problems.append("NO_SOURCE_GATE")
    if gate.get("all_material_claims_triaged") is not True:
        problems.append("MATERIAL_CLAIMS_UNTRIAGED")
    if not gate.get("source_audit_reference") or not gate.get("claim_evidence_reference"):
        problems.append("NO_EVIDENCE_REFERENCES")
    if candidate.get("pilot_video_id") and candidate["pilot_video_id"] != video_id:
        problems.append("PILOT_VIDEO_ID_MISMATCH")
    return {"eligible": not problems, "blockers": sorted(set(problems))}



def linked_candidate_decision(candidate, pilot, registry, roster):
    """Require new canonical claims to match a genuinely triaged pilot."""
    result = candidate_decision(candidate)
    errors = list(result["blockers"])
    video_id = candidate.get("video_id", "")
    if not video_id or candidate.get("pilot_video_id") != video_id:
        errors.append("PILOT_REFERENCE_REQUIRED")
    if not isinstance(pilot, dict) or pilot.get("video_id") != video_id:
        errors.append("LINKED_PILOT_NOT_FOUND_OR_WRONG_VIDEO")
        return {"eligible": False, "blockers": sorted(set(errors))}
    pilot_check = promotion_decision(pilot, video_id, registry, roster)
    if not pilot_check["eligible"]:
        errors.append("LINKED_PILOT_EVIDENCE_GATE_BLOCKED")
    expected = {c.get("claim_id") for c in pilot.get("claims", [])}
    core = candidate.get("core_claims", [])
    received = [c.get("claim_id") for c in core if isinstance(c, dict)]
    if len(received) != len(core) or set(received) != expected or len(set(received)) != len(received):
        errors.append("CANONICAL_CLAIM_SET_DIFFERS_FROM_REVIEWED_PILOT")
    p = "data/subtitles/pilots/" + video_id + ".json"
    g = candidate.get("evidence_gate", {})
    if not str(g.get("source_audit_reference", "")).startswith(p + "#source_audit"):
        errors.append("SOURCE_AUDIT_REFERENCE_NOT_LINKED")
    if not str(g.get("claim_evidence_reference", "")).startswith(p + "#claims"):
        errors.append("CLAIM_EVIDENCE_REFERENCE_NOT_LINKED")
    if candidate.get("source_url") != pilot.get("source_url"):
        errors.append("CANONICAL_SOURCE_DIFFERS_FROM_PILOT")
    return {"eligible": not errors, "blockers": sorted(set(errors))}


def audit(root):
    roster = actual_roster(root)
    registry = registered_sources(root)
    pilots_dir = root / "data/subtitles/pilots"
    canonical_dir = root / "data/analysis_events"
    results, errors = [], []
    for path in sorted(pilots_dir.glob("*.json")):
        vid = path.stem
        try:
            pilot = load(path)
            review = promotion_decision(pilot, vid, registry, roster)
            results.append({
                "video_id": vid, "roster_no": roster.get(vid),
                "claim_count": len(pilot.get("claims", [])),
                "source_kind": pilot.get("source_kind", "UNKNOWN"),
                "status": "PROMOTION_ELIGIBLE" if review["eligible"] else "BLOCKED_REVIEW_DRAFT",
                "blockers": review["blockers"],
                "claims_needing_evidence": len(review["claims_needing_evidence"]),
                "official_url_count": sum(len(c.get("official_sources", [])) for c in pilot.get("claims", [])),
                "canonical_file_exists": (canonical_dir / (vid + ".json")).exists(),
            })
        except (ValueError, TypeError, OSError, KeyError) as exc:
            errors.append(f"{path.name}: {type(exc).__name__}: {exc}")
    actual_claims = sum(x["claim_count"] for x in results)
    legacy = root / "data/subtitles/review_progress_001_070.json"
    snapshot = load(legacy) if legacy.exists() else {}
    first70 = {k for k, n in roster.items() if n <= 70}
    first70_reviewed = len(first70 & {x["video_id"] for x in results})
    analysis_files = list(canonical_dir.glob("*.json")) if canonical_dir.exists() else []
    summary = {
        "schema_version": 1,
        "metric_source": "computed_from_current_files_not_cached_progress",
        "roster_count": len(roster),
        "registered_srt_count": len(registry),
        "first70_pilot_reviewed": first70_reviewed,
        "first70_pilot_pending": len(first70) - first70_reviewed,
        "draft_video_count": len(results),
        "draft_claim_count": actual_claims,
        "pilot_promotion_eligible": sum(x["status"] == "PROMOTION_ELIGIBLE" for x in results),
        "analysis_event_files_existing": len(analysis_files),
        "analysis_events_not_automatically_approved": True,
        "historical_snapshot_draft_count": snapshot.get("deep_review_draft_videos"),
        "historical_snapshot_is_stale": snapshot.get("deep_review_draft_videos") != len(results)
            or snapshot.get("deep_review_draft_claims") != actual_claims,
        "errors": errors,
    }
    priorities = sorted(results, key=lambda x: (
        0 if x["source_kind"] == "USER_SUPPLIED_TIMECODED_AUTOMATIC_SRT" else 1,
        x["roster_no"] if x["roster_no"] is not None else 9999,
    ))
    return {"summary": summary, "priority_review_queue": priorities, "rules": {
        "draft_is_not_approval": True,
        "official_urls_are_not_verification": True,
        "registered_srt_sha_does_not_prove_text_was_compared": True,
        "do_not_mutate_legacy_snapshot": True,
        "canonical_completion_requires_independent_review": True,
    }}


def self_test():
    # Check that a fake official URL cannot satisfy the claim-evidence gate.
    example = {
        "video_id": "abcdefghijk", "roster_no": 1,
        "source_url": "https://www.youtube.com/watch?v=abcdefghijk",
        "stage": "EVIDENCE_REVIEW_DRAFT", "approval": "NOT_APPROVED",
        "subtitle_sha256": "abc",
        "claims": [{"claim_id": "abcdefghijk-01", "timecode": "00:01:00",
                    "source_paraphrase": "연금 세금 5%", "independent_check": "미확정",
                    "official_sources": ["https://example.com"]}],
    }
    d = promotion_decision(example, "abcdefghijk",
        {"abcdefghijk": {"sha256": "abc"}}, {"abcdefghijk": 1})
    assert not d["eligible"] and "CLAIM_EVIDENCE_MISSING" in d["blockers"]
    assert not candidate_decision({"video_id": "abcdefghijk",
        "source_url": example["source_url"], "analysis_status": "COMPLETE"})["eligible"]
    example["source_audit"] = {"full_transcript_reviewed": True,
        "video_id_matched": True, "source_kind": "INDEPENDENT_FULL_KOREAN_TRANSCRIPT",
        "evidence_reference": "provider + retrieved transcript", "limitations": "ASR",
        "timestamps_approximate": True}
    example["claims"][0]["verification_evidence"] = {
        "verdict": "QUALIFIED", "primary_url": "https://official.example",
        "checked_at": "2026-10-09", "source_finding": "특정 구간 검토",
        "effective_date_or_scope": "2026", "disposition": "세율 범위 수정"}
    d = promotion_decision(example, "abcdefghijk",
        {"abcdefghijk": {"sha256": "abc"}}, {"abcdefghijk": 1})
    assert d["eligible"], d
    draft_candidate = {
        "video_id": "abcdefghijk",
        "pilot_video_id": "abcdefghijk",
        "source_url": example["source_url"],
        "analysis_status": "COMPLETE",
        "approval": "APPROVED",
        "source_level": "full_asr",
        "title": "test",
        "core_claims": [{"claim_id": "abcdefghijk-01", "claim": "test"}],
        "actionable_guidance": ["review"],
        "assumptions": ["assumed"],
        "risks_and_exceptions": ["risk"],
        "quantitative_claims": ["test"],
        "relations": ["independent"],
        "verification_status": "reviewed",
        "limitations": ["auto transcript"],
        "evidence_gate": {
            "version": 1,
            "source_checked": True,
            "all_material_claims_triaged": True,
            "source_audit_reference": "data/subtitles/pilots/abcdefghijk.json#source_audit",
            "claim_evidence_reference": "data/subtitles/pilots/abcdefghijk.json#claims[*].verification_evidence",
        },
    }
    assert linked_candidate_decision(draft_candidate, example,
        {"abcdefghijk": {"sha256": "abc"}}, {"abcdefghijk": 1})["eligible"]
    draft_candidate["core_claims"][0]["claim_id"] = "different-id"
    assert "CANONICAL_CLAIM_SET_DIFFERS_FROM_REVIEWED_PILOT" in linked_candidate_decision(
        draft_candidate, example, {"abcdefghijk": {"sha256": "abc"}},
        {"abcdefghijk": 1}
    )["blockers"]
    example["claims"][0]["verification_evidence"].pop("source_finding")
    assert "CLAIM_EVIDENCE_MISSING" in promotion_decision(example, "abcdefghijk",
        {"abcdefghijk": {"sha256": "abc"}}, {"abcdefghijk": 1})["blockers"]
    return 6


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check-candidate", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--full-queue", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"self_test": "PASS", "checks": self_test()}, ensure_ascii=False))
        return 0
    data = audit(args.root)
    if not args.full_queue:
        data["priority_review_queue"] = data["priority_review_queue"][:8]
    if args.check_candidate:
        candidate = load(args.check_candidate)
        video_id = candidate.get("video_id", "")
        pilot_path = args.root / "data/subtitles/pilots" / (video_id + ".json")
        linked_pilot = load(pilot_path) if pilot_path.is_file() else None
        registry = registered_sources(args.root)
        data["canonical_candidate_decision"] = linked_candidate_decision(
            candidate, linked_pilot, registry, actual_roster(args.root)
        )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 1 if data["summary"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
