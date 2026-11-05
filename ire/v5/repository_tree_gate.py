"""Preflight source-tree preservation guard for V5 original and added artifacts.

This checks known required files and their expected structured types locally.
It complements (but does not replace) a full before/after Git tree file-path
comparison prior to moving the branch ref.
"""
from pathlib import Path
import argparse
import json

ESSENTIAL = (
    "data/claims.jsonl",
    "data/videos.jsonl",
    "ire/v5/AGENTS.md",
    "ire/v5/advisory_knowledge/integrated_education13_20261104.json",
    "ire/v5/legacy_consolidation/master_index_20261105.json",
    "ire/v5/legacy_consolidation/batch_B01_C001_C020_20261105.json",
    "ire/v5/legacy_consolidation/batch_B02_C021_C040_20261105.json",
    "ire/v5/legacy_consolidation/batch_B03_C041_C060_20261105.json",
    "ire/v5/advisory60.py",
    "ire/v5/tests/test_advisory60.py",
    "ire/v5/advisory_integration/REPORT_60_ADVISORY_20261105.md",
    "ire/v5/advisory_integration/question_scenarios_20261105.json",
    "ire/v5/advisory_integration/decision_routes_20261105.json",
    "ire/v5/advisory_integration/LIVE_VALIDATION_SCENARIOS_20261105.json",
    "ire/v5/advisory_integration/CHAT_FACT_CHECK_20261105.json",
    "ire/v5/advisory_integration/LIVE_QUESTION_VALIDATION_REPORT_20261105.md",
    "ire/v5/advisory60_validation.py",
    "ire/v5/tests/test_advisory60_validation.py",
    "ire/v5/validation/engine_research_readiness_20261105.json",
    "ire/v5/validation/first_five_source_manifest_20261105.json",
    "ire/v5/validation/ENGINE_VERIFICATION_DECISION_AND_PILOT_GATE_20261105.md",
    "ire/v5/first_five_source_readiness_gate.py",
    "ire/v5/tests/test_first_five_source_readiness_gate.py",
    "ire/v5/validation/first_five_raw_srt_integrity_receipt_20261105.json",
)

class RepositoryTreeError(ValueError):
    pass

def check(root: Path, apparent_paths: set[str] | None = None) -> dict:
    root = Path(root)
    actual = {x for x in ESSENTIAL if (root / x).is_file()}
    known = actual if apparent_paths is None else apparent_paths
    missing = [x for x in ESSENTIAL if x not in known or x not in actual]
    if missing:
        raise RepositoryTreeError("REQUIRED_RESEARCH_FILES_MISSING: " + ", ".join(missing))
    graph = json.loads((root / "ire/v5/advisory_knowledge/integrated_education13_20261104.json").read_text("utf-8"))
    old = json.loads((root / "ire/v5/advisory_integration/question_scenarios_20261105.json").read_text("utf-8"))
    current = json.loads((root / "ire/v5/advisory_integration/LIVE_VALIDATION_SCENARIOS_20261105.json").read_text("utf-8"))
    research = (root / "data/claims.jsonl").read_text("utf-8").splitlines()
    if (len(graph.get("nodes", [])) != 13 or len(old.get("cases", [])) != 20
        or len(current.get("repair_set", [])) != 20
        or len(current.get("holdout_set", [])) != 16
        or len([x for x in research if x.strip()]) != 116):
        raise RepositoryTreeError("REQUIRED_RESEARCH_FILE_CONTENT_CHANGED")
    return {
        "schema":"IRE_V5_REPOSITORY_TREE_GUARD_V1",
        "essential_original_and_new_files":len(ESSENTIAL),
        "original_20_scenarios_preserved":True,
        "new_20_and_holdout_16_scenarios_preserved":True,
        "original_116_claim_ledger_preserved":True,
        "old_13_education_graph_preserved":True,
        "historical_private_srt_required_in_public_git":False,
        "full_git_tree_diff_checked_inside_ci":False,
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(check(a.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
