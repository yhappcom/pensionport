"""Reusable V5 source/temporal/knowledge gate for newly studied videos.

Semantic answers and official-document reads must be authored by the active
ChatGPT research host. CI has no private SRT and cannot certify source acoustics,
legal facts, blind human approval, or suitability for personalized advice.
Use --private-zip in the host to bind every claim window to original bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_STUDY = "ire/v5/new_video_studies/WIXWPJjhF50_20261105.json"
SCHEMA = "IRE_V5_INCREMENTAL_VIDEO_WITH_TEMPORAL_AND_LINEAGE_V2"
SHA = re.compile(r"[a-f0-9]{64}\Z")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
TIMESTAMP = re.compile(r"\d{2}:\d{2}:\d{2},\d{3}\Z")


class StudyGateError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise StudyGateError(code)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def parse_srt(data: bytes) -> dict:
    text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    cues = {}
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.splitlines()
        require(len(lines) >= 3 and lines[0].strip().isdigit(),
                "SOURCE_BAD_CUE")
        number = int(lines[0].strip())
        require(number == len(cues) + 1 and " --> " in lines[1],
                "SOURCE_CUES_NOT_CONTIGUOUS")
        cues[number] = {
            "cue": number, "time": lines[1].strip(),
            "text": " ".join(lines[2:]),
        }
    return cues


def verify(root: Path, study_path: str = DEFAULT_STUDY,
           review: dict | None = None,
           private_zip: Path | None = None) -> dict:
    root = Path(root)
    study = review if review is not None else read_json(root / study_path)
    v = study.get("video", {})
    vid = v.get("video_id")
    require(study.get("schema") == SCHEMA
            and study.get("research_run_date") == "2026-11-05"
            and isinstance(vid, str) and VIDEO_ID.fullmatch(vid)
            and type(v.get("roster_no")) is int
            and v.get("private_original_bytes_read_in_chat") is True
            and v.get("private_original_bytes_available_to_github_ci") is False
            and v.get("source_audio_independently_verified") is False
            and v.get("legacy_canonical_video_record_present") is False,
            "NEW_SOURCE_OR_PROVENANCE_FALSE")
    catalogue = read_json(root / "ire/v5/source_catalog/201-300.json")
    rows = [x for x in catalogue["files"] if x["video_id"] == vid]
    require(len(rows) == 1, "UNKNOWN_SOURCE_VIDEO")
    catalogued = rows[0]
    require(v.get("roster_no") == catalogued["roster_inventory_no"]
            and v.get("original_archive") == "201-300.zip"
            and v.get("original_zip_sha256") == catalogue["archives"][0]["sha256"]
            and v.get("original_srt_sha256") == catalogued["source_sha256"]
            and v.get("original_cue_count") == catalogued["cue_count"]
            and v.get("original_duration_end_ms") == catalogued["end_ms"]
            and catalogued["roster_video_type"] == "Long-form"
            and SHA.fullmatch(str(v.get("original_srt_sha256", "")))
            and SHA.fullmatch(str(v.get("original_zip_sha256", ""))),
            "VIDEO_ARCHIVE_ROSTER_HASH_MISMATCH")
    previous = [json.loads(line) for line in
                (root / "data/claims.jsonl").read_text("utf-8").splitlines()
                if line.strip()]
    legacy_ids = {row["claim_id"] for row in previous}
    graph = read_json(root / "ire/v5/advisory_knowledge/integrated_education13_20261104.json")
    graph_ids = {x["knowledge_id"] for x in graph["nodes"]}
    twenty = read_json(root / "ire/v5/advisory_knowledge/provisional_integrated_20_plus_5_20261104.json")
    twenty_ids = {x["claim_id"] for x in twenty["nodes"]}
    prior = study.get("reconciled_against_prior", {})
    require(len(previous) == len(legacy_ids) == 116
            and len(graph_ids) == graph["total_education_topics"] == 13
            and len(twenty_ids) == 20
            and prior.get("baseline_education_concepts") == 13
            and prior.get("previous_education_ids") == [x["knowledge_id"] for x in graph["nodes"]]
            and prior.get("baseline_legacy_core_claims") == 116
            and prior.get("baseline_v5_provisional_core_claims") == 20
            and prior.get("prior_13_unchanged") is True
            and prior.get("prior_116_unchanged") is True
            and prior.get("auto_education_approval_count") == 0
            and prior.get("personal_investment_advice_approved") is False,
            "KNOWLEDGE_SILENTLY_REPLACED")
    require(all(vid not in line for line in
                (root / "data/videos.jsonl").read_text("utf-8").splitlines()),
            "LEGACY_VIDEO_ALREADY_ANALYZED")
    sources = study.get("authoritative_sources", [])
    auth = {}
    for src in sources:
        identifier = src.get("id")
        url = urlparse(src.get("url", ""))
        require(identifier and identifier not in auth
                and url.scheme == "https" and bool(url.hostname)
                and src.get("source_independent") is True
                and src.get("original_bytes_sealed") is False
                and src.get("human_blind_attested") is False
                and len(src.get("content", "")) >= 18,
                "AUTHORITY_UNSUPPORTED_OR_FABRICATED")
        auth[identifier] = src
    require(len(auth) >= 2 and any(x["issuer"] == "한국거래소" for x in sources)
            and any(x["issuer"] == "금융위원회" for x in sources),
            "OFFICIAL_ISSUER_EVIDENCE_MISSING")
    covered = study.get("coverage_segments", [])
    end = v["original_cue_count"]
    require(isinstance(covered, list) and len(covered) >= 3,
            "CUE_COVERAGE_EMPTY")
    cursor = 1
    for row in covered:
        a, b = row.get("start"), row.get("end")
        require(type(a) is int and type(b) is int
                and a == cursor and a <= b <= end
                and len(row.get("kind", "")) >= 5,
                "CUE_COVERAGE_GAP_OR_OVERLAP")
        cursor = b + 1
    require(cursor == end + 1
            and covered[0]["kind"] == "NON_SUBSTANTIVE_OPENING"
            and covered[-1]["kind"] == "NON_SUBSTANTIVE_END_MUSIC",
            "CUE_TAIL_NOT_COVERED")
    claims = study.get("research_claims", [])
    require(type(claims) is list and len(claims) == len(covered)-2
            and len(claims) >= 1, "CLAIM_OR_COVERAGE_COUNT_BAD")
    claim_ids = set()
    proposed_ids = set()
    for i, (claim, segment) in enumerate(zip(claims, covered[1:-1]), 1):
        claim_id = claim.get("claim_id")
        require(claim_id == f"C{v['roster_no']}-{i:02}"
                and claim_id not in claim_ids and claim.get("video_id") == vid
                and (claim.get("cue_start"), claim.get("cue_end")) ==
                    (segment["start"], segment["end"])
                and SHA.fullmatch(str(claim.get("source_cue_span_sha256", "")))
                and TIMESTAMP.fullmatch(str(claim.get("first_cue_time", "")))
                and TIMESTAMP.fullmatch(str(claim.get("last_cue_time", "")))
                and len(claim.get("source_paraphrase", "")) >= 30
                and len(claim.get("authoritative_comparison", "")) >= 65
                and claim.get("verified_as_of") == "2026-11-05",
                "CLAIM_ANCHOR_OR_RESEARCH_MISSING")
        claim_ids.add(claim_id)
        require(claim.get("financial_fact_certified") is False
                and claim.get("external_human_blind_approved") is False
                and claim.get("original_audio_verified") is False
                and claim.get("personal_investment_advice_approved") is False,
                "FALSE_PERSONAL_ADVICE_OR_FACT_PROMOTION")
        ids = claim.get("authority_ids")
        require(isinstance(ids, list) and len(ids) == len(set(ids))
                and len(ids) > 0 and set(ids) <= set(auth)
                and claim.get("evidence_role") in {
                    "CURRENT_RULE_AND_HISTORICAL_COMPARISON",
                    "HISTORICAL_POLICY_CONTEXT",
                    "CONTEXT_ONLY_NOT_EVIDENCE_OF_NUMERIC_RETURN",
                    "CONTEXT_ONLY_NOT_EVIDENCE_OF_EXPECTED_RETURN",
                    "CONTEXT_ONLY_NOT_EVIDENCE_OF_CAUSALITY",
                    "GENERAL_RISK_EDUCATION",
                    "OFFICIAL_PROCESS_ONLY_SCHEDULE_UNVERIFIED",
                    "SOURCE_CASE_NOT_ALLOCATION_RULE",
                }, "CLAIM_AUTHORITIES_OR_EVIDENCE_ROLE_INVALID")
        if "CONTEXT_ONLY" in claim["evidence_role"]:
            require("UNVERIFIED" in claim["disposition"]
                    or "NOT_VERIFIED" in claim["disposition"],
                    "CONTEXT_REFERENCE_FALSLY_CERTIFIES_STATISTIC")
        concept = claim.get("new_provisional_concept_id")
        if concept is not None:
            require(concept not in graph_ids and concept not in proposed_ids,
                    "DUPLICATE_OR_APPROVED_CONCEPT")
            proposed_ids.add(concept)
    candidates = prior.get("new_provisional_concepts", [])
    require(set(x["knowledge_id"] for x in candidates) == proposed_ids
            and len(candidates) == len(proposed_ids)
            and all(x["source_claim_id"] in claim_ids
                    and x["approval"] is False
                    and x["status"].startswith("PROVISIONAL_")
                    for x in candidates),
            "NEW_CONCEPTS_UNSAFELY_PROMOTED")
    relationships = prior.get("legacy_claim_relationships", [])
    require(len(relationships) == len({
                (x["source_claim_id"], x["target_id"]) for x in relationships
            }) and all(x["source_claim_id"] in claim_ids
                      and x["target_id"] in legacy_ids | twenty_ids | graph_ids
                      and x["approval"] is False
                      for x in relationships)
            and not set(prior.get("direct_duplicate_education_ids", [])) - graph_ids,
            "INVALID_OR_DUPLICATE_PRIOR_RELATION")
    approval = study.get("approvals", {})
    require(approval == {
        "personalized_financial_advice": False,
        "human_blind_independent_review": False,
        "original_audio_authentication": False,
        "current_financial_fact_certification": False,
    }, "STUDY_PRETENDS_TO_HAVE_APPROVAL")
    numeric = study.get("numeric_rule_crosscheck")
    if numeric is not None:
        require(numeric.get("effective_date") == "2023-06-26"
                and numeric.get("current_official_source_id") in auth
                and numeric.get("historic_mode_source_id") in auth
                and (numeric.get("old_min_pct_of_offer"),
                     numeric.get("old_max_pct_of_offer"),
                     numeric.get("old_min_return_pct"),
                     numeric.get("old_max_return_pct")) == (63, 260, -37, 160)
                and (numeric.get("current_min_pct_of_offer"),
                     numeric.get("current_max_pct_of_offer"),
                     numeric.get("current_min_return_pct"),
                     numeric.get("current_max_return_pct")) == (60, 400, -40, 300)
                and numeric.get("source_video_legacy_max_return_claim_is_math_error") is True
                and any("2023-06-26" in c["authoritative_comparison"]
                        and "300%" in c["authoritative_comparison"]
                        for c in claims),
                "IPO_HISTORICAL_CURRENT_RULE_CONFUSED")
    summary = study.get("counts", {})
    require(summary.get("whole_source_cues_covered") == end
            and summary.get("material_claim_windows") == len(claims)
            and summary.get("independent_issuer_source_references") == len(auth)
            and summary.get("prior_education_nodes_compared") == 13
            and summary.get("legacy_core_claims_checked") == 116
            and summary.get("linked_existing_legacy_claims") == len(relationships)
            and summary.get("new_provisional_concepts") == len(candidates)
            and summary.get("formal_knowledge_approvals") == 0,
            "RUN_TOTALS_NOT_REPRODUCIBLE")
    private_checks = 0
    if private_zip is not None:
        require(hashlib.sha256(Path(private_zip).read_bytes()).hexdigest() ==
                v["original_zip_sha256"], "PRIVATE_ZIP_DIGEST_MISMATCH")
        with zipfile.ZipFile(private_zip) as archive:
            candidates = [name for name in archive.namelist()
                          if name.endswith(f"youtube-transcript-{vid}.srt")
                          and not name.startswith("__MACOSX")
                          and "/._" not in name]
            require(len(candidates) == 1, "PRIVATE_SRT_VIDEO_ID_MISSING")
            srt = archive.read(candidates[0])
        require(hashlib.sha256(srt).hexdigest() == v["original_srt_sha256"],
                "PRIVATE_SRT_DIGEST_MISMATCH")
        cues = parse_srt(srt)
        require(len(cues) == end, "PRIVATE_SRT_CUE_LENGTH_MISMATCH")
        for row in claims:
            segment = [cues[n] for n in
                       range(row["cue_start"], row["cue_end"] + 1)]
            data = json.dumps(segment, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")).encode("utf-8")
            require(hashlib.sha256(data).hexdigest() ==
                    row["source_cue_span_sha256"]
                    and segment[0]["time"].split(" --> ")[0] ==
                    row["first_cue_time"]
                    and segment[-1]["time"].split(" --> ")[-1] ==
                    row["last_cue_time"],
                    "PRIVATE_CLAIM_SPAN_MISMATCH")
            private_checks += 1
    return {
        "schema": "IRE_V5_GENERIC_NEW_VIDEO_GATE_RESULT_V2",
        "video_id": vid,
        "roster_no": v["roster_no"],
        "source_cues_covered": end,
        "anchored_material_claims": len(claims),
        "official_context_references": len(auth),
        "prior_education_nodes_preserved": 13,
        "prior_legacy_claims_preserved": 116,
        "legacy_context_links": len(relationships),
        "new_provisional_concepts_only": len(proposed_ids),
        "private_original_claim_spans_byte_rechecked_now": private_checks,
        "independent_financial_fact_approval": False,
        "human_blind_review_completed": False,
        "personal_advice_approved": False,
        "outcome": "RESEARCH_RECONCILED_NO_ADVISORY_PROMOTION",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--study", default=DEFAULT_STUDY)
    parser.add_argument("--private-zip", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.study, private_zip=args.private_zip),
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
