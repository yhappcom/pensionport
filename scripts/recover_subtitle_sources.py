#!/usr/bin/env python3
"""Restore *registered* SRT bytes into two private copies; never publish transcripts.

This tool intentionally does not fetch third-party captions as a substitute for
the historical uploaded SRT. A matching SHA-256 and cue structure are required.
It never updates canonical analyses, the public registry, or the main branch.

Examples:
 python scripts/recover_subtitle_sources.py --archive original.zip \
   --registry data/subtitles/registry.json --video-id keu5SvpD7KE \
   --vault-dir /private/srt-primary --backup-dir /other/private/srt-backup --apply
 python scripts/recover_subtitle_sources.py --registry data/subtitles/registry.json \
   --video-id keu5SvpD7KE --vault-dir /private/srt-primary \
   --backup-dir /other/private/srt-backup --verify-only
"""
import argparse
import collections
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

from ingest_subtitle_zip import validate_srt

NAME = re.compile(r"^youtube-transcript-([A-Za-z0-9_-]{11})(?:\s*\(\d+\))?\.srt$", re.I)
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
MAX_ITEM_BYTES = 25_000_000
MAX_MEMBERS = 10000


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def within(path, root):
    return path == root or root in path.parents


def validate_locations(primary, backup, repo_root):
    p, b, root = primary.resolve(), backup.resolve(), repo_root.resolve()
    if p == b or within(p, b) or within(b, p):
        raise ValueError("Private and backup vaults must be distinct, non-nested locations")
    if within(p, root) or within(b, root):
        raise ValueError("Never store SRT bytes inside the repository")
    if primary.is_symlink() or backup.is_symlink():
        raise ValueError("Vault directory symlinks are not accepted")
    return p, b


def parse_archive(paths):
    found = collections.defaultdict(dict)
    for archive in paths:
        with zipfile.ZipFile(archive) as z:
            if len(z.infolist()) > MAX_MEMBERS:
                raise ValueError("Too many ZIP members")
            for m in z.infolist():
                if m.is_dir() or not m.filename.lower().endswith(".srt"):
                    continue
                parts = m.filename.replace("\\", "/").split("/")
                if "__MACOSX" in parts:
                    continue
                match = NAME.fullmatch(parts[-1])
                if not match:
                    continue
                if m.file_size > MAX_ITEM_BYTES or m.file_size < 1:
                    raise ValueError("Invalid/oversized SRT member")
                raw = z.read(m)
                if len(raw) > MAX_ITEM_BYTES:
                    raise ValueError("Uncompressed SRT exceeds safe size")
                found[match.group(1)][sha(raw)] = raw
    return found


def source_status(video_id, raw, ref):
    if raw is None:
        return "MISSING_SOURCE"
    if sha(raw) != ref["sha256"]:
        return "REGISTERED_SHA_MISMATCH"
    try:
        count, last, errors = validate_srt(raw)
    except (UnicodeError, ValueError):
        return "INVALID_SRT"
    if errors or count != ref["cue_count"]:
        return "STRUCTURE_MISMATCH"
    if ref.get("last_sec") is not None and (last is None or abs(last - ref["last_sec"]) > 0.002):
        return "END_TIMESTAMP_MISMATCH"
    return "SHA_AND_STRUCTURE_VERIFIED"


def paths_for(video_id, primary, backup):
    filename = "youtube-transcript-" + video_id + ".srt"
    return primary / filename, backup / filename


def saved_status(video_id, ref, primary, backup):
    locations = paths_for(video_id, primary, backup)
    statuses = []
    for f in locations:
        if not f.is_file():
            statuses.append("MISSING")
            continue
        if f.is_symlink():
            statuses.append("SYMLINK_BLOCKED")
            continue
        statuses.append(source_status(video_id, f.read_bytes(), ref))
    if statuses == ["SHA_AND_STRUCTURE_VERIFIED"] * 2:
        return "TWO_COPIES_VERIFIED"
    if any(s not in ("MISSING", "SHA_AND_STRUCTURE_VERIFIED") for s in statuses):
        return "CUSTODY_CONFLICT"
    return "BACKUP_INCOMPLETE"


def safe_write(path, raw):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".subtitle-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def recover(registry, archives, selected, primary, backup, apply):
    group = parse_archive(archives)
    outcome, to_copy = {}, []
    for video_id in selected:
        ref = registry[video_id]
        versions = group.get(video_id, {})
        if not versions:
            outcome[video_id] = "MISSING_SOURCE"
            continue
        if len(versions) != 1:
            outcome[video_id] = "CONFLICT_IN_ARCHIVE"
            continue
        raw = next(iter(versions.values()))
        status = source_status(video_id, raw, ref)
        if status != "SHA_AND_STRUCTURE_VERIFIED":
            outcome[video_id] = status
            continue
        # Preflight both copies: no silent overwrite, even if one is corrupt.
        target = paths_for(video_id, primary, backup)
        conflicts = []
        for p in target:
            if p.exists() or p.is_symlink():
                if not p.is_file() or p.is_symlink() or p.read_bytes() != raw:
                    conflicts.append(str(p.name))
        if conflicts:
            outcome[video_id] = "CUSTODY_CONFLICT"
            continue
        outcome[video_id] = "READY_TO_COPY" if not apply else "PENDING_COPY"
        to_copy.append((video_id, raw))
    if apply:
        # Fail closed: never partially promote one incoming batch with missing
        # requested videos or an inconsistent registered hash.
        if any(outcome[vid] != "PENDING_COPY" for vid in selected):
            return outcome
        for video_id, raw in to_copy:
            for path in paths_for(video_id, primary, backup):
                if not path.exists():
                    safe_write(path, raw)
            outcome[video_id] = saved_status(video_id, registry[video_id], primary, backup)
    return outcome


def verify(registry, selected, primary, backup):
    return {vid: saved_status(vid, registry[vid], primary, backup) for vid in selected}


def self_test():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo = root / "repo"
        repo.mkdir()
        a, b = root / "private-vault", root / "separate-backup"
        raw = b"1\n00:00:00,000 --> 00:00:01,200\nTest caption\n\n"
        ref = {"abcdefghijk": {"sha256": sha(raw), "cue_count": 1, "last_sec": 1.2}}
        z = root / "one.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("youtube-transcript-abcdefghijk.srt", raw)
        p, q = validate_locations(a, b, repo)
        assert recover(ref, [z], ["abcdefghijk"], p, q, False) == {"abcdefghijk": "READY_TO_COPY"}
        assert recover(ref, [z], ["abcdefghijk"], p, q, True) == {"abcdefghijk": "TWO_COPIES_VERIFIED"}
        assert verify(ref, ["abcdefghijk"], p, q) == {"abcdefghijk": "TWO_COPIES_VERIFIED"}
        assert (a / "youtube-transcript-abcdefghijk.srt").read_bytes() == raw
        (b / "youtube-transcript-abcdefghijk.srt").write_bytes(b"tampered")
        assert verify(ref, ["abcdefghijk"], p, q) == {"abcdefghijk": "CUSTODY_CONFLICT"}
        assert recover(ref, [z], ["abcdefghijk"], p, q, True) == {"abcdefghijk": "CUSTODY_CONFLICT"}
        try:
            validate_locations(repo / "bad", b, repo)
        except ValueError:
            pass
        else:
            raise AssertionError("In-repository vault accepted")
        wrong = dict(ref)
        wrong["abcdefghijk"] = {**ref["abcdefghijk"], "sha256": "0" * 64}
        assert recover(wrong, [z], ["abcdefghijk"], p, q, False) == {"abcdefghijk": "REGISTERED_SHA_MISMATCH"}
        assert source_status("abcdefghijk", raw, {**ref["abcdefghijk"], "cue_count": 2}) == "STRUCTURE_MISMATCH"
    return 9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", type=Path)
    ap.add_argument("--archive", type=Path, action="append", default=[])
    ap.add_argument("--video-id", action="append", default=[])
    ap.add_argument("--vault-dir", type=Path)
    ap.add_argument("--backup-dir", type=Path)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps({"self_test": "PASS", "checks": self_test()}))
        return 0
    if not args.registry or not args.vault_dir or not args.backup_dir:
        ap.error("--registry, --vault-dir and --backup-dir are required")
    if args.apply and args.verify_only:
        ap.error("--apply and --verify-only are mutually exclusive")
    if not args.verify_only and not args.archive:
        ap.error("--archive is required unless --verify-only is set")
    with args.registry.open(encoding="utf-8-sig") as f:
        registry = json.load(f)["items"]
    selected = args.video_id or sorted(registry, key=lambda vid: registry[vid]["roster_no"])
    if len(selected) != len(set(selected)) or any(not VIDEO_ID.fullmatch(s) or s not in registry for s in selected):
        ap.error("Every --video-id must be a unique registered YouTube ID")
    primary, backup = validate_locations(args.vault_dir, args.backup_dir, args.repo_root)
    result = (verify(registry, selected, primary, backup) if args.verify_only
              else recover(registry, args.archive, selected, primary, backup, args.apply))
    print(json.dumps({
        "schema_version": 1, "operation": "VERIFY" if args.verify_only else ("RESTORE" if args.apply else "DRY_RUN"),
        "summary": dict(sorted(collections.Counter(result.values()).items())),
        "videos": result, "no_public_subtitles_written": True,
        "private_backup_durability_not_verified_by_tool": True
    }, indent=2, ensure_ascii=False))
    return 0 if all(x == ("TWO_COPIES_VERIFIED" if (args.verify_only or args.apply) else "READY_TO_COPY")
                    for x in result.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
