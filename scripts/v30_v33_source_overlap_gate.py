#!/usr/bin/env python3
"""Non-semantic holdout overlap preflight. Never issues human blind gold or engine approval.

Reads original SRT bytes in ZIP archives; never extracts or serializes raw speech.
Only outputs file digests, structural counts, and normalized exact 7-token reuse.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

VIDEO_ID = re.compile(r"youtube-transcript-([A-Za-z0-9_-]{11})\.srt$")
CLOCK = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
TOKEN = re.compile(r"[가-힣A-Za-z]+|\d+(?:[.,]\d+)?")


def parse_srt(raw):
    """Match the frozen V3.3 parser's UTF8, contiguous indices, and time rules."""
    if not isinstance(raw, bytes) or not raw or len(raw) > 16_000_000:
        raise ValueError("BAD_SRT_BYTE_SIZE")
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").strip()
    out = []
    for block in re.split(r"\n\s*\n", text):
        lines = block.split("\n")
        if len(lines) < 3 or not lines[0].strip().isdigit() or int(lines[0]) != len(out) + 1:
            raise ValueError("NONCONTIGUOUS_OR_EMPTY_CUE")
        span = lines[1].split("-->")
        if len(span) != 2:
            raise ValueError("MISSING_SRT_SPAN")
        millis = []
        for value in span:
            m = CLOCK.fullmatch(value.strip())
            if not m:
                raise ValueError("INVALID_SRT_TIMESTAMP")
            h, minute, sec, ms = map(int, m.groups())
            if minute >= 60 or sec >= 60:
                raise ValueError("INVALID_SRT_CLOCK_RANGE")
            millis.append(((h * 60 + minute) * 60 + sec) * 1000 + ms)
        start, end = millis
        if start >= end or (out and start < out[-1][0]):
            raise ValueError("NONCHRONOLOGICAL_SRT")
        line = "\n".join(lines[2:]).strip()
        if not line:
            raise ValueError("BLANK_SRT_CUE")
        out.append((start, end, line))
    return out


def token_ngrams(cues, width=7):
    tokens = TOKEN.findall(" ".join(text for _, _, text in cues).lower())
    return {tuple(tokens[i:i+width]) for i in range(max(0, len(tokens)-width+1))}


def load_roster(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        columns = line.strip().split(",", 1)
        if len(columns) == 2 and columns[0].isdigit():
            n, video_id = int(columns[0]), columns[1].strip()
            if n in out and out[n] != video_id:
                raise ValueError("ROSTER_DUPLICATE_NUMBER")
            out[n] = video_id
    return out


def zip_srt_map(archive_paths):
    out = {}
    for path in archive_paths:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.startswith("__MACOSX/") or name.endswith("/"):
                    continue
                match = VIDEO_ID.search(name)
                if not match or not name.endswith(".srt"):
                    continue
                video_id = match.group(1)
                if video_id in out:
                    raise ValueError("AMBIGUOUS_DUPLICATED_VIDEO_SRT")
                out[video_id] = z.read(name)
    return out


def screen(roster, data, historical_end, candidates, duplicate_at=0.5, review_at=0.05):
    if historical_end < 1 or not (0 < review_at < duplicate_at <= 1):
        raise ValueError("BAD_PREDECLARED_CUTOFF")
    if len(set(candidates)) != len(candidates) or any(n <= historical_end for n in candidates):
        raise ValueError("HOLDOUT_AND_HISTORIC_ROSTER_MUST_BE_SEPARATE")
    missing = [n for n in range(1, historical_end+1)
               if n not in roster or roster[n] not in data]
    historic = {}
    for n in range(1, historical_end+1):
        if n not in missing:
            historic[n] = token_ngrams(parse_srt(data[roster[n]]))
    cases = []
    for n in candidates:
        video_id = roster.get(n)
        if not video_id or video_id not in data:
            cases.append({"number": n, "video_id": video_id, "status": "MISSING_SOURCE"})
            continue
        raw = data[video_id]
        cues = parse_srt(raw)
        q = token_ngrams(cues)
        scored = sorted(((len(q & v) / len(q) if q else 0, k, len(q & v))
                         for k, v in historic.items()), reverse=True)
        ratio, match_no, repeated = scored[0] if scored else (0, None, 0)
        status = ("EXCLUDE_HISTORICAL_REUSE" if ratio >= duplicate_at else
                  "MANUAL_REUSE_REVIEW" if ratio >= review_at else
                  "PROVISIONAL_LEXICAL_NOVELTY_ONLY")
        cases.append({"number": n, "video_id": video_id, "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest(),
                      "cue_count": len(cues), "max_7gram_containment": round(ratio, 6),
                      "most_similar_historic_number": match_no,
                      "shared_7grams": repeated, "status": status})
    return {"schema": "V33_READONLY_SOURCE_OVERLAP_PREFLIGHT_V1",
            "method": "exact normalized 7-token shingle containment; not semantic identity",
            "historical_end": historical_end, "historical_source_count": len(historic),
            "missing_historical_numbers": missing,
            "complete_historical_corpus": len(missing) == 0,
            "cases": cases,
            "external_source_identity_verified": False,
            "external_blind_gold_verified": False,
            "model_predictions_generated": False,
            "precision": None, "recall": None,
            "release": "BLOCKED_EXTERNAL_CUSTODY_GOLD_AND_NOVELTY_REVIEW"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--archive", type=Path, nargs="+", required=True)
    parser.add_argument("--historical-end", type=int, default=260)
    parser.add_argument("--candidates", type=int, nargs="+", required=True)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()
    result = screen(load_roster(args.roster), zip_srt_map(args.archive),
                    args.historical_end, args.candidates)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if args.report_out:
        if args.report_out.exists():
            raise ValueError("REFUSE_OVERWRITE_PRIOR_AUDIT")
        args.report_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
