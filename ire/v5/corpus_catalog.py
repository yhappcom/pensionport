"""SRT source census: identities/hashes only, never transcript text or financial claims.

Usage: python -m ire.v5.corpus_catalog 201-300.zip --roster VIDEO_INVENTORY_2026-10-07.md
No network access or LLM is used. A registered source is NOT an analyzed source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

ID = re.compile(r"(?:youtube-transcript-)?([A-Za-z0-9_-]{11})\.srt\Z", re.I)
SRT_TIME = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,\.](\d{3}) --> (\d{2}):(\d{2}):(\d{2})[,\.](\d{3})")
MAX_SRT_BYTES = 30_000_000


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _milliseconds(part: list[int]) -> int:
    h, m, s, ms = part
    if m >= 60 or s >= 60:
        raise ValueError("SRT_TIME_UNIT_INVALID")
    return ((h * 60 + m) * 60 + s) * 1000 + ms


def inspect_srt(raw: bytes) -> tuple[int, int]:
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"\n\s*\n", text.strip())
    if not parts or not text.strip():
        raise ValueError("SRT_EMPTY")
    final = 0
    for no, part in enumerate(parts, 1):
        lines = part.split("\n")
        if len(lines) < 3 or lines[0].strip() != str(no):
            raise ValueError("SRT_SEQUENCE_OR_BLOCK_INVALID")
        stamp = SRT_TIME.fullmatch(lines[1].strip())
        if stamp is None:
            raise ValueError("SRT_TIME_INVALID")
        times = list(map(int, stamp.groups()))
        start, end = _milliseconds(times[:4]), _milliseconds(times[4:])
        if start > end or not any(v.strip() for v in lines[2:]):
            raise ValueError("SRT_EMPTY_TEXT_OR_NEGATIVE_TIME")
        final = max(final, end)
    return len(parts), final


def load_roster_ids(path: Path) -> set[str]:
    """Reads the fixed 791-video Markdown register; IDs, not ordinal numbers."""
    text = path.read_text("utf-8")
    ids = set(re.findall(r"\|\s*`([A-Za-z0-9_-]{11})`\s*\|", text))
    if not ids:
        raise ValueError("ROSTER_VIDEO_IDS_NOT_FOUND")
    return ids


def catalog(archives: list[Path], roster_ids: set[str] | None = None) -> dict:
    """One row per actual SRT. Fail closed on malformed sources or conflicting IDs."""
    if not archives:
        raise ValueError("NO_SOURCE_ARCHIVES")
    result = {"schema":"IRE_V5_SRT_CORPUS_CENSUS_V1",
              "source_interpretation_completed":False,
              "independent_financial_facts_approved":0,
              "advisory_eligible":False,
              "archives":[], "files":[]}
    seen: dict[str, str] = {}
    duplicates = 0
    for archive in archives:
        archive = Path(archive)
        archived_hash = digest(archive.read_bytes())
        count = 0
        with zipfile.ZipFile(archive) as zipped:
            for info in zipped.infolist():
                name = info.filename
                if (info.is_dir() or name.startswith("__MACOSX/") or
                    PurePosixPath(name).name.startswith("._")):
                    continue
                if "\\" in name or name.startswith("/") or ".." in PurePosixPath(name).parts:
                    raise ValueError("UNSAFE_ZIP_MEMBER")
                if not name.lower().endswith(".srt"):
                    continue
                count += 1
                if info.file_size > MAX_SRT_BYTES or (info.compress_size == 0 and info.file_size):
                    raise ValueError("SRT_OVERSIZED_OR_ZIP_BOMB")
                if info.compress_size and info.file_size / info.compress_size > 400:
                    raise ValueError("SRT_ZIP_BOMB_RATIO")
                match = ID.fullmatch(PurePosixPath(name).name)
                if match is None:
                    raise ValueError("SRT_FILENAME_VIDEO_ID_UNRESOLVED")
                video_id = match.group(1)
                raw = zipped.read(info)
                if len(raw) != info.file_size:
                    raise ValueError("ZIP_UNCOMPRESSED_SIZE_MISMATCH")
                cues, end_ms = inspect_srt(raw)
                content_hash = digest(raw)
                if video_id in seen:
                    if seen[video_id] != content_hash:
                        raise ValueError("VIDEO_ID_CONFLICTING_ORIGINALS")
                    duplicates += 1
                    continue
                seen[video_id] = content_hash
                result["files"].append({
                    "video_id":video_id, "archive":archive.name,
                    "source_sha256":content_hash, "cue_count":cues,
                    "end_ms":end_ms,
                    "roster_matched":None if roster_ids is None else video_id in roster_ids,
                    "semantic_analysis_status":"NOT_ANALYZED_BY_THIS_CENSUS"})
        result["archives"].append({"archive":archive.name,
                                  "sha256":archived_hash,"srt_files":count})
    result["summary"] = {
        "srt_files":len(result["files"]),
        "distinct_video_ids":len(seen),
        "identical_duplicate_files_ignored":duplicates,
        "source_cues":sum(row["cue_count"] for row in result["files"]),
        "duration_end_ms_sum":sum(row["end_ms"] for row in result["files"]),
        "matched_to_roster":None if roster_ids is None else sum(
            row["roster_matched"] for row in result["files"]),
        "not_in_roster":None if roster_ids is None else sum(
            not row["roster_matched"] for row in result["files"])}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--roster", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = catalog(args.archives,
                     load_roster_ids(args.roster) if args.roster else None)
    body = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    print(json.dumps({"schema":result["schema"],"summary":result["summary"],
                      "advisory_eligible":False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
