"""One deterministic, fail-closed V5 preflight for local work and GitHub CI.

Use before pushing a research-engine change:
    python -m ire.v5.preflight --root .

Requires the same pinned dependencies as the V5 workflow. No external model
API and no network searches are performed. This is a software contract check,
not independent certification of financial claims or investment advice.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# These commands preserve every verification step in the former V5 standalone
# workflow. Keep the full unit-test discovery last, after the narrower gates.
_CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("compile_v5", ("-m", "compileall", "-q", "ire/v5")),
    ("video_id_reconciliation",
     ("-m", "ire.v5.continuous_integration", "--root", ".")),
    ("no_unreviewed_pilot_promotion",
     ("-m", "ire.v5.review_gate",
      "--review", "ire/v5/reviews/4TFtEQxSM38_20261104.json",
      "--prior", "data/claims.jsonl")),
    ("advisory_replay_safety",
     ("-m", "ire.v5.advisory_replay", "--root", ".")),
    ("twenty_plus_five_intake",
     ("-m", "ire.v5.knowledge_stage", "--root", ".")),
    ("five_original_source_studies",
     ("-m", "ire.v5.five_study_gate", "--root", ".")),
    ("provisional_knowledge_reconciliation",
     ("-m", "ire.v5.provisional_knowledge_gate", "--root", ".")),
    ("independent_authority_crosscheck",
     ("-m", "ire.v5.external_authority_recheck", "--root", ".")),
    ("deduplicated_education_safety",
     ("-m", "ire.v5.education_release_gate", "--root", ".")),
    ("all_v5_regression_tests",
     ("-m", "unittest", "discover", "-s", "ire/v5/tests",
      "-p", "test_*.py", "-v")),
)


def planned_checks() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return _CHECKS


def run(root: Path) -> int:
    root = root.resolve()
    if not (root / "data/claims.jsonl").is_file():
        print("PREFLIGHT_FAIL: repository root is invalid", file=sys.stderr)
        return 2
    for i, (label, argv) in enumerate(_CHECKS, 1):
        print(f"PREFLIGHT_START {i}/{len(_CHECKS)} {label}", flush=True)
        result = subprocess.run((sys.executable, *argv), cwd=root, check=False)
        if result.returncode:
            print(f"PREFLIGHT_FAIL {label} exit={result.returncode}",
                  file=sys.stderr, flush=True)
            return result.returncode
        print(f"PREFLIGHT_PASS {label}", flush=True)
    print(f"PREFLIGHT_ALL_PASS count={len(_CHECKS)}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--list", action="store_true",
                        help="Show exact checks without executing them.")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(
            [{"step": name, "argv": list(argv)} for name, argv in _CHECKS],
            ensure_ascii=False, indent=2))
        return 0
    return run(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
