#!/usr/bin/env python3
"""Read-only, pre-push audit for a fully staged subtitle research batch.

Usage:
    git add <explicit reviewed research paths>
    python -B scripts/preflight_subtitle_batch.py
    git commit -m "research: approved batch"
    git push

Stages nothing, commits nothing, and never modifies the approval gate.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import audit_subtitle_review_gate as gate

CANONICAL = re.compile(r"^data/analysis_events/([A-Za-z0-9_-]{11})\.json$")
PILOT = re.compile(r"^data/subtitles/pilots/([A-Za-z0-9_-]{11})\.json$")


def private_source(path: str) -> bool:
    """Original subtitle text/archives must stay out of the Git history."""
    return path.casefold().endswith((".srt", ".zip"))


def git_paths(root: Path, *arguments: str) -> set[str]:
    proc = subprocess.run(
        ["git", *arguments], cwd=root, text=True, capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(f"Git index check failed: {proc.stderr.strip()}")
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def self_test() -> int:
    assert private_source("101-200/youtube-transcript-abc.srt")
    assert private_source("private/101-200.ZIP")
    assert not private_source("data/subtitles/registry_161_165.json")
    assert CANONICAL.fullmatch("data/analysis_events/GzazVJg1V1I.json")
    assert PILOT.fullmatch("data/subtitles/pilots/GzazVJg1V1I.json")
    assert gate.self_test() == 6
    print(json.dumps({"preflight_self_test": "PASS", "checks": 6}))
    return 0


def preflight(root: Path) -> int:
    errors: list[str] = []
    staged = git_paths(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    staged_new = git_paths(root, "diff", "--cached", "--name-only", "--diff-filter=A")
    unstaged = git_paths(root, "diff", "--name-only")
    if not staged:
        errors.append("NO_STAGED_CHANGES: stage the complete batch before preflight")
    overlap = staged & unstaged
    if overlap:
        errors.append("INDEX_WORKTREE_DIFFER: " + ", ".join(sorted(overlap)))
    raw = sorted(p for p in staged if private_source(p))
    if raw:
        errors.append("PRIVATE_SRT_OR_ZIP_STAGED: " + ", ".join(raw))

    for name in ("scripts/audit_subtitle_review_gate.py",
                 "scripts/ingest_subtitle_zip.py",
                 "scripts/recover_subtitle_sources.py"):
        try:
            ast.parse((root / name).read_text(encoding="utf-8"), filename=name)
        except (SyntaxError, OSError, UnicodeError) as exc:
            errors.append(f"PYTHON_SYNTAX: {name}: {exc}")

    try:
        roster = gate.actual_roster(root)
        registry = gate.registered_sources(root)
        report = gate.audit(root)
        errors.extend(str(e) for e in report["summary"]["errors"])
    except (KeyError, ValueError, OSError, TypeError) as exc:
        errors.append(f"SOURCE_REGISTRY_OR_QUEUE: {type(exc).__name__}: {exc}")
        roster, registry = {}, {}

    review_ids = set()
    for path in staged:
        candidate = CANONICAL.fullmatch(path)
        pilot = PILOT.fullmatch(path)
        if candidate or pilot:
            review_ids.add((candidate or pilot).group(1))

    checked = []
    for video_id in sorted(review_ids):
        final_path = root / "data/analysis_events" / (video_id + ".json")
        pilot_path = root / "data/subtitles/pilots" / (video_id + ".json")
        if not final_path.exists():
            # Draft-only updates must remain NOT_APPROVED until independently verified.
            if pilot_path.exists():
                try:
                    draft = gate.load(pilot_path)
                    if draft.get("approval") != "NOT_APPROVED":
                        errors.append(f"{video_id}: PILOT_MUST_STAY_NOT_APPROVED")
                except (ValueError, OSError, TypeError) as exc:
                    errors.append(f"{video_id}: INVALID_PILOT: {exc}")
            continue
        try:
            final = gate.load(final_path)
            pilot = gate.load(pilot_path) if pilot_path.exists() else None
        except (ValueError, OSError, TypeError) as exc:
            errors.append(f"{video_id}: INVALID_JSON: {exc}")
            continue
        if final.get("approval") == "APPROVED":
            decision = gate.linked_candidate_decision(final, pilot, registry, roster)
            if not decision["eligible"]:
                errors.append(f"{video_id}: " + ", ".join(decision["blockers"]))
            elif str(final_path.relative_to(root)) in staged_new and not pilot_path.exists():
                errors.append(f"{video_id}: MISSING_EVIDENCE_DRAFT")
            checked.append(video_id)
        elif final.get("analysis_status") == "COMPLETE":
            errors.append(f"{video_id}: COMPLETED_WITHOUT_APPROVAL_REVIEW")
    result = {
        "status": "FAIL" if errors else "PASS",
        "staged_files": len(staged),
        "reviewed_approved_candidates": checked,
        "registered_sources": len(registry),
        "errors": errors,
        "scope": "local pre-commit review; GitHub Actions remains the authoritative remote gate",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    return preflight(args.root.resolve())


if __name__ == "__main__":
    sys.exit(main())
