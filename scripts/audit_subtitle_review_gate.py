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
    # 2026-10-22: Independently verified single uploaded #130 original SRT.
    # Preserve all prior batch source-integrity totals and IDs.
    one30 = root / "data/subtitles/registry_130_20261022.json"
    if one30.is_file():
        extra = load(one30)
        items = extra.get("items", [])
        if (extra.get("uploaded_private_individual_srt_count") != 1
                or extra.get("raw_srt_bytes") != 132206
                or extra.get("total_cues") != 1697
                or extra.get("source_intake_sha256")
                != "2bb3202be49a167d04e61771a8a10039b228687b0341496fbc1545c9e3c5407b"
                or len(items) != 1):
            raise ValueError("VIDEO130_SOURCE_INTAKE_PROVENANCE_INVALID")
        row = items[0]
        vid, sha = row.get("video_id"), row.get("sha256")
        if (vid != "SaNok0umUQY" or row.get("roster_no") != 130
                or row.get("roster_no") != roster.get(vid)
                or sha != extra["source_intake_sha256"]
                or vid in registry
                or row.get("cue_count") != 1697
                or row.get("raw_srt_bytes") != 132206
                or row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                or row.get("v3_status") != "APPROVED"
                or row.get("full_transcript_reviewed") is not True
                or row.get("public_same_video_ko_normalized_chars") != 22900
                or row.get("private_dedup_ko_normalized_sha256") != row.get("public_ko_normalized_sha256")):
            raise ValueError("VIDEO130_UNTRUSTED_SOURCE_PROMOTION")
        registry[vid] = {"sha256": sha, "cue_count": row["cue_count"]}
    # 2026-10-26: #131-140 individually uploaded (no ZIP). Exact raw SRT fingerprints
    # are pinned independently of the user-supplied registry metadata.
    next10 = root / "data/subtitles/registry_131_140_20261026.json"
    if next10.is_file():
        batch = load(next10)
        pinned = {
            "AWULeF_xzFc": (131, "5d523ef48ff86420f7aaff5b3c38c715e7182d986eeb4b015e72f37ac2facd6d", 377, 30103),
            "S9W_Qe9JrlI": (132, "aa2af19a03c43d32f03950b1beafe7127caeff1b093be445cab09787cd152b85", 1673, 127045),
            "fhh23gVq4I0": (133, "bc5e12103e36365c59c2a4f160901f2959ac98d53df8f4ded8869f88aeaf9c93", 1369, 101759),
            "xKMPTIdMgI4": (134, "9717720dd8e7a068718a72f2fd0d484b06b14d6a1e0ce8a01474e85ee4d08ef2", 1573, 118632),
            "GmwmPKFY4PY": (135, "ed9a2089ee5732387e954b0f32192be3cca4cb583373abee180ab7fbef7369fb", 1907, 146238),
            "-71DQQIcTlc": (136, "808886ae6721f4085a14dd0ded770c1bdef1e773a6b99d4e3fed16ed69c4523e", 1423, 108892),
            "wnDrGtqH-yE": (137, "21153828423dd3a699e92c183121768d7291651f7c9131781a58cfd2fa3e0935", 1229, 93204),
            "ex2wK2N_9uo": (138, "95d159bfb59b3020672b7881fded81a22fbbfe58d44416f36c8616a388f38cf1", 4569, 320276),
            "h3_r0ZKykYY": (139, "090ef1a0cbb5e9a5d761644ebbdf34ac24ca736a15b5eb7f4a32cd5c005ffd2b", 788, 61729),
            "jMJbEelMgLA": (140, "1436621222d9184e3884dbf97d525dffdac623db042e87c8aa50fbc8733f6c4c", 1503, 116310),
        }
        rows = batch.get("items", [])
        if (len(rows) != 10
                or batch.get("total_srt_bytes") != 1224188
                or batch.get("total_cues") != 16411
                or set(x.get("video_id") for x in rows) != set(pinned)):
            raise ValueError("BATCH_131_140_SOURCE_INTAKE_INVALID")
        if (sum(x.get("cue_count", 0) for x in rows) != 16411
                or sum(x.get("raw_srt_bytes", 0) for x in rows) != 1224188):
            raise ValueError("BATCH_131_140_CUE_BYTE_SUM_INVALID")
        for row in rows:
            vid = row["video_id"]
            no, sha, cues, byte_len = pinned[vid]
            if (row.get("roster_no") != no
                    or roster.get(vid) != no
                    or row.get("sha256") != sha
                    or row.get("cue_count") != cues
                    or row.get("raw_srt_bytes") != byte_len
                    or row.get("full_transcript_reviewed") is not True
                    or row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                    or row.get("v3_status") != "APPROVED"
                    or vid in registry):
                raise ValueError("BATCH_131_140_UNTRUSTED_ENTRY")
            registry[vid] = {"sha256": sha, "cue_count": cues}
    # 2026-10-26: source evidence for #141-145 from the original user ZIP.
    # Ignore __MACOSX AppleDouble metadata and pin raw source SRT hashes.
    five = root / "data/subtitles/registry_141_145_20261026.json"
    if five.is_file():
        extra = load(five)
        expected = {
            "O8YUK1OugHs": (141, "fada8dc0d2572c31621ae09a39ef353b733d48910613866a33250561fb1e2811", 1260, 96513),
            "faqbdJ1C43Y": (142, "7505f16a7e74ad54033a1b7f5d6a48b0558e37bf90cdb678f59bcae4989318ed", 1026, 78567),
            "GFTYwKkZgoQ": (143, "4e7da21b940bee5b5f21895232559cf6d31a6bde762b3c788bf39b", 1067, 82637),
            "GvGNAsizyp8": (144, "d5f2f13cab031491d3f49e723d4adc790e04674fe7916be52d39f71e3242c376", 774, 60695),
            "sRadRD7qRu8": (145, "615ba53ec075ef2e19ed4f7cf4fe6cfb3ad0b32457bfc66ee01fa56297284562", 745, 57458),
        }
        entries = extra.get("items", [])
        if (extra.get("archive_sha256") != "ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e"
                or extra.get("total_videos") != 5
                or extra.get("total_raw_bytes") != 375870
                or extra.get("total_original_cues") != 4872
                or len(entries) != 5
                or {x.get("video_id") for x in entries} != set(expected)
                or sum(x.get("raw_srt_bytes", 0) for x in entries) != 375870
                or sum(x.get("cue_count", 0) for x in entries) != 4872):
            raise ValueError("BATCH_141_145_SOURCE_REGISTRY_INVALID")
        for row in entries:
            vid = row["video_id"]
            no, sha, cues, byte_len = expected[vid]
            if (vid in registry or roster.get(vid) != no
                    or row.get("roster_no") != no
                    or row.get("sha256") != sha
                    or row.get("cue_count") != cues
                    or row.get("raw_srt_bytes") != byte_len
                    or row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                    or row.get("full_transcript_reviewed") is not True
                    or row.get("v3_status") != "APPROVED"):
                raise ValueError("BATCH_141_145_UNTRUSTED_ENTRY")
            registry[vid] = {"sha256": sha, "cue_count": cues}
    # Source integrity gate for next five private originals (#146-150), 2026-10-26.
    batch_146_150 = root / "data/subtitles/registry_146_150_20261026.json"
    if batch_146_150.is_file():
        batch = load(batch_146_150)
        pinned = {
            "OzDgw9ZcWAQ": (146, "38050408405b322f03b5128d42be8c9a349f22168dea67ac295e153049059684", 1582, 122955),
            "O7-EBvOsTlg": (147, "6db23da5dfc94f31ed65a884c6961b22cc56babd14fd1ae815dbd2062098a433", 1286, 100238),
            "Q-zEc5IeQ50": (148, "14997b559c4403a551cf25503d3badd265caa6c1d8c307ff4cba096347bc039b", 999, 75633),
            "_y94r65G9_M": (149, "473b923faa1d6144768cb2800438a442e3e062dc3a69eb8b317458fcf3c4f76d", 48, 3640),
            "Q3OrWpOVS2E": (150, "66092d2d28be2e7f8ea4bc3313d0b7a04f5261a7432a68dbfa0b8e7a682be1c8", 1046, 80261),
        }
        records = batch.get("items", [])
        if (batch.get("archive_sha256") != "ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e"
                or batch.get("total_videos") != 5
                or batch.get("total_raw_bytes") != 382727
                or batch.get("total_original_cues") != 4961
                or len(records) != 5
                or {e.get("video_id") for e in records} != set(pinned)
                or sum(e.get("raw_srt_bytes", 0) for e in records) != 382727
                or sum(e.get("cue_count", 0) for e in records) != 4961):
            raise ValueError("BATCH_146_150_SOURCE_INTAKE_INVALID")
        for entry in records:
            vid = entry["video_id"]
            no, sha, cues, byte_len = pinned[vid]
            if (vid in registry or roster.get(vid) != no
                    or entry.get("roster_no") != no
                    or entry.get("sha256") != sha
                    or entry.get("cue_count") != cues
                    or entry.get("raw_srt_bytes") != byte_len
                    or entry.get("full_transcript_reviewed") is not True
                    or entry.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                    or entry.get("v3_status") != "APPROVED"):
                raise ValueError("BATCH_146_150_UNTRUSTED_SOURCE")
            registry[vid] = {"sha256": sha, "cue_count": cues}
    # Source integrity gate #151-155 (user uploaded 101-200.zip) 2026-10-26.
    batch_151_155 = root / "data/subtitles/registry_151_155_20261026.json"
    if batch_151_155.is_file():
        source = load(batch_151_155)
        expected = {
            "Cdf6LtiiD_o": (151, "b2e29d7d8573740a1e7ca918509036ead3ebc633d91f7e82d21117f9b44b458d", 1397, 110439),
            "Eim44cy1lkg": (152, "53f06b0bc97ace07a504dff18b203b5da8f2e77f181129f0f353c6614b485060", 485, 37161),
            "1bfGwu2ASx4": (153, "299c08fb9745485e3c966d103588198dec2dd065a0f9fb9a3ba89e82d95692eb", 1089, 83568),
            "Jl0rwMExTbg": (154, "edfe591d3eb6a42d3efe4017e9376702de2b2c7424a2395adb9e63ac09e5839d", 1252, 93689),
            "XsDB9nf57_A": (155, "84e51e4f1b8827c583cf207c963385e4ea62b7794d2e6577287c6cc1f8a1bcdc", 1124, 85621),
        }
        rows = source.get("items", [])
        if (source.get("archive_sha256") != "ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e"
                or source.get("videos") != 5 or source.get("bytes") != 410478
                or source.get("cues") != 5347 or len(rows) != 5
                or {r.get("video_id") for r in rows} != set(expected)
                or sum(r.get("raw_srt_bytes", 0) for r in rows) != 410478
                or sum(r.get("cue_count", 0) for r in rows) != 5347):
            raise ValueError("BATCH_151_155_SOURCE_REGISTRY_MISMATCH")
        for entry in rows:
            vid = entry["video_id"]
            no, sha, cues, size = expected[vid]
            if (vid in registry or roster.get(vid) != no
                    or entry.get("roster_no") != no or entry.get("sha256") != sha
                    or entry.get("cue_count") != cues or entry.get("raw_srt_bytes") != size
                    or entry.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                    or entry.get("full_transcript_reviewed") is not True
                    or entry.get("v3_status") != "APPROVED"):
                raise ValueError("BATCH_151_155_UNTRUSTED_SOURCE")
            registry[vid] = {"sha256": sha, "cue_count": cues}
    # Source custody: user-private original #156-160 auto SRTs (2026-10-26).
    batch_156_160 = root / "data/subtitles/registry_156_160_20261026.json"
    if batch_156_160.is_file():
        data = load(batch_156_160)
        pinned = {
            "bSJeaaeM6Pg": (156, "c4ec5db8a4a3343bc325179bd9b954c2269a90ca6fdbb0dca5113e77f8f3f4a7", 1177, 92622),
            "gPLpHoiR2x4": (157, "c5ac40ed073aeb01db7f9fccfd2031b6cbfe8aafb94678608214b2d9e9058e3d", 1065, 82148),
            "NOK_0zfF80Q": (158, "2c94cd808280477bd59c3d974f8fb47981ea1cdc34792ab0d5e50c6eef807baa", 821, 62370),
            "aRNULifoFKY": (159, "2f70305308e9fed548f2499d86e523d07240cf5d7121e3252471187870b204fe", 999, 77945),
            "SSZaZvwAuy0": (160, "bc6db130fe9f8a79a1b96afdec9373825ec35a737dd255be66962e80bbb38ede", 1409, 105629),
        }
        rows = data.get("items", [])
        if (data.get("archive_sha256") != "ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e"
                or data.get("total_videos") != 5 or data.get("total_raw_bytes") != 420714
                or data.get("total_original_cues") != 5471 or len(rows) != 5
                or {r.get("video_id") for r in rows} != set(pinned)
                or sum(r.get("raw_srt_bytes", 0) for r in rows) != 420714
                or sum(r.get("cue_count", 0) for r in rows) != 5471):
            raise ValueError("BATCH_156_160_INVALID_SOURCE_REGISTRY")
        for row in rows:
            vid = row["video_id"]
            no, digest, cues, nbytes = pinned[vid]
            if (vid in registry or roster.get(vid) != no
                    or row.get("roster_no") != no
                    or row.get("sha256") != digest
                    or row.get("cue_count") != cues
                    or row.get("raw_srt_bytes") != nbytes
                    or row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                    or row.get("full_transcript_reviewed") is not True
                    or row.get("v3_status") != "APPROVED"):
                raise ValueError("BATCH_156_160_UNTRUSTED_SOURCE")
            registry[vid] = {"sha256": digest, "cue_count": cues}
    # Extend immutable-source acceptance to #161-165 private originals (2026-10-26).
    # The full user ZIP was SHA-matched again after Drive upload. Require each
    # video's independent source fingerprint, official roster, original length,
    # verbatim cue count and reviewed status; never infer source provenance
    # from an unreviewed ZIP or the filename alone.
    batch_161_165 = root / "data/subtitles/registry_161_165_20261026.json"
    if batch_161_165.is_file():
        data = load(batch_161_165)
        pinned = {
            "GzazVJg1V1I": (161, "cef8db8d4220dfa87364ed8b2b5dcab4d5a44d4a10127d62f03df1efcec71c4d", 746, 57165),
            "myQ6i7AjmDY": (162, "f89240f19cad9b86f683732956ba2048b6a8cca9be48cf739b5693bb1f258ea6", 913, 69025),
            "PUWsNu9b3cc": (163, "6f5ec204d9c07ecaa1a83f3fc64f921c55a4ba9df85c21957e8f6e2eea960722", 270, 21193),
            "lvC7RFbNEx0": (164, "d3b563ae6e73263bdb986f701c99d6f548cdd3941bddf163d365a1f2fbd83b08", 1507, 113458),
            "EJajY-ZEliM": (165, "c0874fab8e6315a7f58065617d99b26a5b58e41f86cf34b0f6b6bf4cf6e519d8", 1102, 83625),
        }
        rows = data.get("items", [])
        if (data.get("archive_sha256") != "ea0dac242603af19678354f3dec0fa2d21ab68146a774ab0c50b9b0b5f10663e"
                or data.get("total_videos") != 5
                or data.get("total_raw_bytes") != 344466
                or data.get("total_original_cues") != 4538
                or data.get("v3_approval_count") != 5
                or len(rows) != 5
                or {r.get("video_id") for r in rows} != set(pinned)
                or sum(r.get("raw_srt_bytes", 0) for r in rows) != 344466
                or sum(r.get("cue_count", 0) for r in rows) != 4538):
            raise ValueError("BATCH_161_165_INVALID_SOURCE_REGISTRY")
        for row in rows:
            vid = row["video_id"]
            no, digest, cues, nbytes = pinned[vid]
            if (vid in registry or roster.get(vid) != no
                    or row.get("roster_no") != no
                    or row.get("sha256") != digest
                    or row.get("cue_count") != cues
                    or row.get("raw_srt_bytes") != nbytes
                    or row.get("source_status") != "PRIVATE_SRT_SHA_MATCHED_CLAIM_SCOPED_V3"
                    or row.get("full_transcript_reviewed") is not True
                    or row.get("v3_status") != "APPROVED"):
                raise ValueError("BATCH_161_165_UNTRUSTED_SOURCE")
            registry[vid] = {"sha256": digest, "cue_count": cues}
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
