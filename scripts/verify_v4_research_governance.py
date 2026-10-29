#!/usr/bin/env python3
"""Read-only V4 research governance regression gate; structural, not legal certification."""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTRL = "data/synthesis/investment_knowledge_v4/research_quality_controls_20261030.json"
MODEL = "data/synthesis/investment_knowledge_v4/models/decision_models_006_010_20261030.json"
MANIFEST = "data/synthesis/investment_knowledge_v4/reviews/v4_005_010_incremental_manifest_20261030.json"
BASE = "data/synthesis/investment_knowledge_v4/reviews"
REVIEW = re.compile(r"^v4_(\d{3})_.*(?:deep|decision|quantitative).*review.*\.json$", re.I)

class GateError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise GateError(message)

def load(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))

def nonempty(x):
    return isinstance(x, str) and bool(x.strip())

def future_gate(row, filename):
    """Validate per-video evidence/status separation for new V4 deep reviews."""
    claims = row.get("claims")
    require(isinstance(claims, list) and claims, f"{filename}: claims required")
    claim_ids = [c.get("id") for c in claims]
    require(all(nonempty(x) for x in claim_ids) and len(set(claim_ids)) == len(claim_ids), f"{filename}: duplicate or blank claim ID")
    gate = row.get("quality_gate")
    require(isinstance(gate, dict) and gate.get("policy_version") == "V4_RESEARCH_GOVERNANCE_20261030",
            f"{filename}: quality_gate policy_version required")
    for key in ("source_provenance", "claim_coverage", "model_scope", "knowledge_integration", "decision_status"):
        require(isinstance(gate.get(key), dict), f"{filename}: missing {key}")
    source = gate["source_provenance"]
    for key in ("source_kind", "scope_note"):
        require(nonempty(source.get(key)), f"{filename}: source {key} missing")
    for key in ("raw_hash_recomputed_this_cycle", "audio_checked", "frames_checked"):
        require(type(source.get(key)) is bool, f"{filename}: source {key} must be boolean")
    audit = gate["claim_coverage"]
    for key in ("rechecked_ids", "reused_ids", "contradicted_ids"):
        require(isinstance(audit.get(key), list), f"{filename}: {key} must be list")
        require(all(nonempty(x) for x in audit[key]) and len(audit[key]) == len(set(audit[key])),
                f"{filename}: {key} duplicated")
    checked, reused, contradicted = (set(audit[k]) for k in ("rechecked_ids", "reused_ids", "contradicted_ids"))
    require(not checked.intersection(reused) and checked.union(reused) == set(claim_ids),
            f"{filename}: independent review and V3 carryover must partition all claim IDs")
    legacy_contradicted = {c["id"] for c in claims if c.get("legacy_verdict") == "CONTRADICTED"}
    require(legacy_contradicted == contradicted, f"{filename}: CONTRADICTED misclassified")
    model = gate["model_scope"]
    require(isinstance(model.get("model_ids"), list) and len(set(model["model_ids"])) == len(model["model_ids"]),
            f"{filename}: model IDs missing/duplicated")
    for key, allowed in (
        ("arithmetic_status", {"PASS", "OPEN", "NOT_APPLICABLE"}),
        ("semantic_status", {"PASS", "OPEN", "NOT_APPLICABLE"}),
        ("legal_product_status", {"PASS", "OPEN", "NOT_APPLICABLE"}),
        ("tax_basis", {"SEGREGATED", "OPEN", "NOT_APPLICABLE"})):
        require(model.get(key) in allowed, f"{filename}: invalid {key}")
    require(nonempty(model.get("limits")), f"{filename}: model assumption limits missing")
    if model["model_ids"]:
        require(model["arithmetic_status"] != "NOT_APPLICABLE" and model["semantic_status"] != "NOT_APPLICABLE",
                f"{filename}: models need mathematical and economic review")
    knowledge = gate["knowledge_integration"]
    require(knowledge.get("relation") in {"NEW", "REINFORCE", "EXTEND", "CHANGE", "CONFLICT", "CORRECT", "NONE"},
            f"{filename}: invalid concept relation")
    for k in ("conflict_ids", "correction_ids"):
        require(isinstance(knowledge.get(k), list), f"{filename}: missing {k}")
    require(knowledge.get("contradicted_blocked") is True, f"{filename}: contradicted principle not quarantined")
    if contradicted:
        require(contradicted.issubset(set(knowledge["correction_ids"])),
                f"{filename}: contradicted claim needs explicit correction record")
    decision = gate["decision_status"]
    require(decision.get("research_status") in {"IN_PROGRESS", "CLOSED_WITH_SOURCE_LIMITATIONS", "EVIDENCE_BLOCKED"},
            f"{filename}: invalid research status")
    require(decision.get("evidence_status") in {"VERIFIED", "QUALIFIED", "OPEN"},
            f"{filename}: invalid evidence status")
    require(decision.get("max_use") in {"L1", "L2"} and
            decision.get("L3_approved") is False and decision.get("L4_approved") is False,
            f"{filename}: V4 may not auto-authorize personalized L3/L4")
    blockers = gate.get("open_blockers")
    require(isinstance(blockers, list), f"{filename}: open_blockers must be list")
    for item in blockers:
        require(isinstance(item, dict) and all(nonempty(item.get(k)) for k in
                    ("id", "needed", "blocked_use", "reopen_trigger")), f"{filename}: invalid OPEN item")
        require(isinstance(item.get("claim_ids"), list) and
                set(item["claim_ids"]).issubset(set(claim_ids)), f"{filename}: OPEN claim references invalid")
    require(len({b["id"] for b in blockers}) == len(blockers), f"{filename}: duplicate OPEN")
    if "external_open" in row:
        require({b["id"] for b in blockers} == {b["id"] for b in row["external_open"]},
                f"{filename}: external OPEN not carried to decision gate")
    if blockers:
        require(decision["evidence_status"] != "VERIFIED", f"{filename}: OPEN cannot imply fully verified")
    return len(claim_ids)

def legacy_gate(root, controls):
    require(controls.get("schema_version") == "V4_RESEARCH_GOVERNANCE_20261030", "control schema")
    require((root / controls["policy_document"]).is_file(), "policy doc missing")
    man = load(root, MANIFEST)
    model = load(root, MODEL)
    base = controls["legacy_006_010"]
    require(base["videos"] == [6, 7, 8, 9, 10], "legacy video IDs")
    require(base["ids"] == [x["id"] for x in man["review_files"]], "video identity change")
    require(base["reviewed_v3_claims"] == man["original_V3_claims_reused"] == 60, "V3 claim inflation")
    require(base["new_v3_approvals"] == man["new_V3_approvals"] == 0, "false V3 approval")
    require(base["synthetic_models"] == man["model_count"] == len(model["models"]) == 9, "model count drift")
    total, checked, opened = 0, 0, 0
    all_contradicted = set()
    for entry in man["review_files"]:
        rev = load(root, entry["path"])
        claims = rev["claims"]
        require(rev["video_id"] == entry["id"] and len(claims) == entry["claim_count"], "claim/video mismatch")
        total += len(claims)
        checked += sum(x["current_review"] == "RECHECKED_MATERIAL_PRIMARY_OR_MATH" for x in claims)
        opened += len(rev["external_open"])
        require(len(rev["external_open"]) == entry["open_count"], "OPEN drift")
        require(rev["decision_readiness"]["L3_approved"] is False and
                rev["decision_readiness"]["L4_approved"] is False, "unearned L3/L4")
        all_contradicted |= {x["id"] for x in claims if x["legacy_verdict"] == "CONTRADICTED"}
    require((total, checked, total-checked, opened) ==
            (base["reviewed_v3_claims"], base["rechecked_v4"],
             base["retained_v3_not_independently_rechecked"], base["external_open"]),
            "baseline coverage/OPEN mismatch")
    blocked = controls.get("blocked_positive_claims", [])
    require({x["claim_id"] for x in blocked} == all_contradicted, "CONTRADICTED quarantine incomplete")
    for x in blocked:
        require(x["status"] == "BLOCKED_AS_POSITIVE_PRINCIPLE" and
                x["knowledge_use"] == "CORRECTION_ONLY_NOT_SOURCE_OF_RECOMMENDATION" and
                nonempty(x.get("invalid_proposition")) and nonempty(x.get("corrected_scope")) and
                nonempty(x.get("release_trigger")), "CONTRADICTED not scoped")
        v3 = load(root, x["source_v3"])
        require(any(c["claim_id"] == x["claim_id"] and c["verification"] == "CONTRADICTED"
                    for c in v3["core_claims"]), "source contradiction changed")
    models = {m["id"] for m in model["models"]}
    for x in controls["restricted_models"]:
        require(x["id"] in models and x["scope"] == "L2_SYNTHETIC_SENSITIVITY_ONLY" and
                {"L3", "L4"}.issubset(set(x["blocked_conclusions"])) and
                x["required_on_revision"], "restricted model release unsupported")
    require(controls["L3_approved"] is False and controls["L4_approved"] is False and
            controls["current_max_use"] == "L2_SYNTHETIC", "global approval inflation")
    return {"claims":total, "rechecked":checked, "retained":total-checked, "external_open":opened,
            "contradicted":len(all_contradicted), "restricted_models":len(controls["restricted_models"])}

def verify(root, controls):
    out = legacy_gate(root, controls)
    new_count = 0
    dirpath = root / BASE
    for path in sorted(dirpath.glob("v4_*.json")):
        match = REVIEW.fullmatch(path.name)
        if not match or int(match.group(1)) < controls["future_quality_gate_min_video"]:
            continue
        row = load(root, path.relative_to(root))
        future_gate(row, str(path.relative_to(root)))
        new_count += 1
    out["future_reviews_checked"] = new_count
    return out

def self_test(root, controls):
    verify(root, controls)
    bad = copy.deepcopy(controls)
    bad["blocked_positive_claims"] = []
    try:
        legacy_gate(root, bad)
    except GateError:
        pass
    else:
        raise GateError("self-test: missing contradicted quarantine accepted")
    sample = {
        "claims": [{"id": "FAKE-01", "legacy_verdict": "CONTRADICTED"}],
        "quality_gate": {
            "policy_version": "V4_RESEARCH_GOVERNANCE_20261030",
            "source_provenance": {"source_kind": "PUBLIC_ASR", "scope_note": "Test fixture only",
                "raw_hash_recomputed_this_cycle": False, "audio_checked": False, "frames_checked": False},
            "claim_coverage": {"rechecked_ids": ["FAKE-01"], "reused_ids": [],
                "contradicted_ids": ["FAKE-01"]},
            "model_scope": {"model_ids": [], "arithmetic_status": "NOT_APPLICABLE",
                "semantic_status": "NOT_APPLICABLE", "legal_product_status": "OPEN",
                "tax_basis": "NOT_APPLICABLE", "limits": "No model"},
            "knowledge_integration": {"relation": "CORRECT", "conflict_ids": [],
                "correction_ids": ["FAKE-01"], "contradicted_blocked": True},
            "decision_status": {"research_status": "CLOSED_WITH_SOURCE_LIMITATIONS",
                "evidence_status": "OPEN", "max_use": "L1",
                "L3_approved": False, "L4_approved": False},
            "open_blockers": [{"id": "FAKE-OPEN", "claim_ids": ["FAKE-01"],
                "needed": "Audio", "blocked_use": "L3", "reopen_trigger": "Audio supplied"}]
        }
    }
    future_gate(sample, "test")
    for mutation in ("drop_gate", "false_approval", "lost_correction", "coverage_gap"):
        bad = copy.deepcopy(sample)
        if mutation == "drop_gate":
            del bad["quality_gate"]
        elif mutation == "false_approval":
            bad["quality_gate"]["decision_status"]["L3_approved"] = True
        elif mutation == "lost_correction":
            bad["quality_gate"]["knowledge_integration"]["correction_ids"] = []
        else:
            bad["quality_gate"]["claim_coverage"]["rechecked_ids"] = []
        try:
            future_gate(bad, "test_" + mutation)
        except GateError:
            pass
        else:
            raise GateError("self-test mutation accepted: " + mutation)
    return 5

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        root = args.root.resolve()
        controls = load(root, CTRL)
        result = verify(root, controls)
        if args.self_test:
            result["negative_mutations_rejected"] = self_test(root, controls)
        result["status"] = "PASS"
        result["scope"] = "research governance structure and known quarantines only; not legal or investment validation"
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as ex:
        print(json.dumps({"status": "FAIL", "reason": str(ex)}, ensure_ascii=False))
        return 1

if __name__ == "__main__":
    sys.exit(main())

