#!/usr/bin/env python3
"""Incrementally check SRT ZIPs. Uses only Python standard library.

Reads ZIP members in-memory; never uploads/publishes complete subtitle texts.
Receipt of a valid SRT does NOT mean its claims have been verified.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

FILENAME = re.compile(r"^youtube-transcript-([A-Za-z0-9_-]{11})(?:\s*\(\d+\))?\.srt$", re.I)
TIMES = re.compile(r"(\d{2,}):(\d\d):(\d\d)[,.](\d{3})\s*-->\s*(\d{2,}):(\d\d):(\d\d)[,.](\d{3})(?:\s+.*)?$")
HEADERS = ["roster_no", "video_id", "filename", "classification",
           "sha256", "cue_count", "last_sec", "archive_copy_count", "errors"]

def parse_roster(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    result = {r["video_id"]: int(r["roster_no"]) for r in rows}
    if len(rows) != len(result):
        raise ValueError("Duplicate video IDs in roster")
    return result

def seconds(a):
    h, m, s, ms = [int(v) for v in a]
    return h * 3600 + m * 60 + s + ms / 1000

def validate_srt(raw):
    content = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    cues = 0
    last_start = -1.0
    last_end = None
    errors = []
    for section in re.split(r"\n\s*\n", content.strip()):
        lines = section.split("\n")
        if not lines or not any(line.strip() for line in lines):
            continue
        offset = 1 if lines[0].strip().isdigit() else 0
        if offset and int(lines[0]) != cues + 1:
            errors.append("sequence")
        if len(lines) < offset + 2 or not (match := TIMES.fullmatch(lines[offset].strip())):
            errors.append("bad_time")
            cues += 1
            continue
        start, end = seconds(match.groups()[:4]), seconds(match.groups()[4:])
        if end <= start:
            errors.append("inverted_time")
        if start < last_start:
            errors.append("time_order")
        if not "".join(lines[offset + 1:]).strip():
            errors.append("empty_text")
        cues += 1
        last_start, last_end = start, end
    if not cues:
        errors.append("no_cues")
    return cues, last_end, sorted(set(errors))

def inspect_archive(archive, roster, old_items):
    groups = collections.defaultdict(list)
    problems = []
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist()) > 10000:
            raise ValueError("ZIP has too many members")
        for member in z.infolist():
            if member.is_dir() or not member.filename.lower().endswith(".srt"):
                continue
            parts = member.filename.split("/")
            if "__MACOSX" in parts:
                continue
            name = parts[-1]
            match = FILENAME.fullmatch(name)
            if not match:
                problems.append({"filename": name, "reason": "bad_filename"})
                continue
            if member.file_size > 25_000_000:
                problems.append({"filename": name, "reason": "too_large"})
                continue
            try:
                raw = z.read(member)
                count, end, errors = validate_srt(raw)
            except (UnicodeError, RuntimeError, zipfile.BadZipFile) as exc:
                problems.append({"filename": name, "reason": type(exc).__name__})
                continue
            groups[match.group(1)].append({
                "filename": name, "sha256": hashlib.sha256(raw).hexdigest(),
                "cue_count": count, "last_sec": round(end, 3) if end is not None else None,
                "errors": errors
            })

    rows, pending, duplicate_copies = [], {}, 0
    for video_id, candidates in sorted(groups.items(), key=lambda p: roster.get(p[0], 9999)):
        hashes = {x["sha256"] for x in candidates}
        duplicate_copies += len(candidates) - len(hashes)
        first = candidates[0]
        if video_id not in roster:
            status = "OUTSIDE_ROSTER"
        elif len(hashes) > 1:
            status = "CONFLICT_IN_BATCH"
        elif first["errors"]:
            status = "INVALID_SRT"
        elif video_id not in old_items:
            status = "NEW"
        elif old_items[video_id]["sha256"] == first["sha256"]:
            status = "UNCHANGED"
        else:
            status = "REVISED_REVIEW"
        rows.append({
            "roster_no": roster.get(video_id), "video_id": video_id,
            "filename": first["filename"], "classification": status,
            "sha256": first["sha256"], "cue_count": first["cue_count"],
            "last_sec": first["last_sec"], "archive_copy_count": len(candidates),
            "errors": ",".join(first["errors"])
        })
        if status == "NEW":
            pending[video_id] = {
                "sha256": first["sha256"], "cue_count": first["cue_count"],
                "last_sec": first["last_sec"], "roster_no": roster[video_id],
                "srt_structure": "PASS", "intake_stage": "SRT_STRUCTURE_CHECKED",
                "content_stage": "NOT_INDEXED", "evidence_stage": "NOT_VERIFIED"
            }
    return rows, pending, problems, duplicate_copies

def main():
    p = argparse.ArgumentParser(description="SRT ZIP increment-only receipt ledger")
    p.add_argument("--roster", required=True, type=Path)
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--apply", action="store_true",
                   help="write NEW items only; revisions always require review")
    args = p.parse_args()
    roster = parse_roster(args.roster)
    if args.registry.exists():
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    else:
        registry = {"schema_version": 1, "roster_snapshot": "2026-10-07",
                    "purpose": "SRT structure receipt only", "items": {}}
    if registry.get("schema_version") != 1:
        raise ValueError("Unrecognized registry schema")
    original_items = registry["items"]
    rows, pending, problems, duplicate_copies = inspect_archive(
        args.archive, roster, original_items
    )
    new_registry = dict(registry)
    new_registry["items"] = {**original_items, **pending}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "batch_audit.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        w.writerows(rows)
    counts = dict(sorted(collections.Counter(r["classification"] for r in rows).items()))
    first70_missing = [n for vid, n in roster.items()
                       if n <= 70 and vid not in new_registry["items"]]
    report = {
        "zip_srt_files": sum(r["archive_copy_count"] for r in rows),
        "unique_video_ids": len(rows), "duplicate_copies": duplicate_copies,
        "classification_counts": counts,
        "registered_total_after_preview": len(new_registry["items"]),
        "missing_first_70": sorted(first70_missing), "issues": problems,
        "applied": bool(args.apply)
    }
    (args.out_dir / "intake_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.out_dir / "registry_preview.json").write_text(
        json.dumps(new_registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    if args.apply:
        tmp = args.registry.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(new_registry, ensure_ascii=False, indent=2,
                                  sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(args.registry)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if problems or any(s in counts for s in ("CONFLICT_IN_BATCH", "INVALID_SRT")) else 0

if __name__ == "__main__":
    sys.exit(main())
