#!/usr/bin/env python3
"""V4 evidence contracts: roster, schema, source provenance and promotion gates."""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
STAGES = ["INVENTORIED", "SOURCE_READY", "GROUNDED", "VERIFIED", "SYNTHESIZED", "DECISION_READY"]
DIRECT = {"YOUTUBE_TRANSCRIPT", "VIDEO_FRAME"}
CHECKED = {"PRIMARY_CONFIRMED", "CONTRADICTED", "SUPERSEDED"}

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def video_id_from_url(url):
    u = urlparse(url)
    ids = parse_qs(u.query).get("v", [])
    return ids[0] if u.scheme == "https" and u.netloc in ("www.youtube.com", "youtube.com") and u.path == "/watch" and len(ids) == 1 else None

def inventory(path):
    result = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        match = re.search(r"\|\s*\x60([A-Za-z0-9_-]{11})\x60\s*\|", line)
        if not match:
            raise ValueError("Roster row lacks exact ID: " + line[:100])
        vid = match.group(1)
        columns = re.split(r"(?<!\\)\|", line[match.end():])
        kind = columns[1].strip() if len(columns) > 1 else None
        if kind not in ("Long-form", "Short") or vid in result:
            raise ValueError("Invalid or duplicated roster ID: " + vid)
        result[vid] = kind
    return result

def schema_errors(obj, schema):
    return [str(e.message) for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(obj)]

def audit_manifest(doc, roster, schema):
    err = schema_errors(doc, schema)
    info = doc.get("roster", {})
    if info.get("unique_total") != len(roster):
        err.append("roster count mismatch")
    for kind, key in (("Long-form", "long_form"), ("Short", "shorts")):
        if info.get(key) != sum(k == kind for k in roster.values()):
            err.append(key + " count mismatch")
    seen = set()
    for p in doc.get("pilots", []):
        vid = p.get("video_id")
        if vid in seen or roster.get(vid) != "Long-form":
            err.append("duplicate or non-long-form pilot: " + str(vid))
        seen.add(vid)
    targets = doc.get("quality_targets", {})
    for k in ("direct_evidence_coverage", "time_sensitive_primary_verification", "video_id_match"):
        if targets.get(k) != 1:
            err.append("quality target must equal 1: " + k)
    if targets.get("human_review_for_decision_ready") is not True:
        err.append("human decision review is mandatory")
    return err

def audit_analysis(doc, roster, schema, filename=None):
    err = schema_errors(doc, schema)
    video = doc.get("video", {})
    vid = video.get("video_id")
    if filename and Path(filename).stem != vid:
        err.append("Filename != video_id")
    if roster.get(vid) != "Long-form":
        err.append("video_id missing from long-form roster")
    if video_id_from_url(video.get("watch_url", "")) != vid:
        err.append("YouTube URL video_id mismatch")
    sources = doc.get("sources", [])
    source_map = {s.get("source_id"): s for s in sources}
    if len(source_map) != len(sources):
        err.append("Duplicate source_id")
    claims = doc.get("claims", [])
    if len({c.get("claim_id") for c in claims}) != len(claims):
        err.append("Duplicate claim_id")
    stage = doc.get("stage")
    level = STAGES.index(stage) if stage in STAGES else -1
    quality = doc.get("quality", {})
    if level >= 1 and not any(s.get("kind") in DIRECT and s.get("coverage") in ("FULL", "PARTIAL") for s in sources):
        err.append("SOURCE_READY requires original source evidence")
    if level >= 2 and not claims:
        err.append("GROUNDED requires nonempty claims")
    checked = 0
    for c in claims:
        evs = c.get("evidence", [])
        if level >= 2 and not any(source_map.get(e.get("source_id"), {}).get("kind") in DIRECT for e in evs):
            err.append("claim lacks direct original evidence: " + str(c.get("claim_id")))
        for e in evs:
            if e.get("source_id") not in source_map:
                err.append("unknown source_id in evidence")
            a, b = e.get("start_seconds"), e.get("end_seconds")
            if (a is None) != (b is None):
                err.append("timestamps must both exist or both be null")
            if a is not None and b is not None and (a > b or (video.get("duration_seconds") is not None and b > video["duration_seconds"] + 2)):
                err.append("evidence timestamp exceeds duration or reverses start/end")
        ver = c.get("verification", {})
        refs = ver.get("official_source_ids", [])
        for sid in refs:
            if source_map.get(sid, {}).get("kind") != "OFFICIAL_DOCUMENT":
                err.append("official source reference not an OFFICIAL_DOCUMENT")
        if ver.get("status") in CHECKED:
            if not refs or not ver.get("checked_at"):
                err.append("checked claim missing dated primary source")
            else:
                checked += 1
        if level >= 5 and c.get("claim_type") in ("CURRENT_RULE", "PRODUCT_FEATURE") and ver.get("status") not in CHECKED:
            err.append("decision-ready current rule remains unverified")
    if level >= 3 and checked == 0:
        err.append("VERIFIED requires at least one dated primary-source check")
    if level >= 3:
        for c in claims:
            state = c.get("verification", {}).get("status")
            if state == "OPEN":
                err.append("VERIFIED cannot contain an OPEN claim: " + str(c.get("claim_id")))
            if state == "CONTEXT_CHECKED" and (not c.get("verification", {}).get("notes") or
                    c.get("claim_type") in ("CURRENT_RULE", "PRODUCT_FEATURE")):
                err.append("CONTEXT_CHECKED cannot approve current rule/product")
    if level >= 4 and not doc.get("relationships"):
        err.append("SYNTHESIZED requires prior-knowledge relationship")
    use = doc.get("decision_use", {})
    if bool(use.get("ready")) != (stage == "DECISION_READY"):
        err.append("decision_use.ready disagrees with stage")
    if stage == "DECISION_READY":
        if doc.get("status") != "APPROVED":
            err.append("DECISION_READY needs APPROVED status")
        if not use.get("scope") or not use.get("constraints") or not use.get("risks"):
            err.append("DECISION_READY requires scope, constraints, risks")
        if quality.get("requires_visual_review") and quality.get("visual_review") != "REVIEWED":
            err.append("required visual review incomplete")
    if quality.get("visual_review") == "REVIEWED" and not any(s.get("kind") == "VIDEO_FRAME" for s in sources):
        err.append("REVIEWED visual status requires VIDEO_FRAME evidence")
    if doc.get("status") == "APPROVED" and level < 2:
        err.append("APPROVED needs GROUNDED stage")
    return err

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    root = parser.parse_args().root
    pilot_schema = load(root / "schemas/v4_pilot_manifest.schema.json")
    analysis_schema = load(root / "schemas/v4_video_analysis.schema.json")
    Draft202012Validator.check_schema(pilot_schema)
    Draft202012Validator.check_schema(analysis_schema)
    roster = inventory(root / "VIDEO_INVENTORY_2026-10-07.md")
    errors = ["manifest: " + e for e in audit_manifest(load(root / "data/v4/pilot_manifest.json"), roster, pilot_schema)]
    documents = sorted((root / "data/v4/analyses").glob("*.json"))
    counts = {s: 0 for s in STAGES}
    for path in documents:
        doc = load(path)
        errors.extend(path.name + ": " + e for e in audit_analysis(doc, roster, analysis_schema, path.name))
        if doc.get("stage") in counts:
            counts[doc["stage"]] += 1
    print(f"Roster IDs={len(roster)}; long-form={sum(x=='Long-form' for x in roster.values())}; Shorts={sum(x=='Short' for x in roster.values())}")
    print(f"Pilot candidates=10; V4 analyses={len(documents)}; stages={counts}")
    if errors:
        for e in errors:
            print("FAIL: " + e, file=sys.stderr)
        return 1
    print("PASS: V4 JSON schemas, roster cross-check, evidence/verification safety gates")
    print("CAVEAT: passing static checks does not prove actual audiovisual review or link contents")
    return 0

if __name__ == "__main__":
    sys.exit(main())
