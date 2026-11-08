"""V6 validation driver.

--isolated validates V6-1 through V6-7 synthetic software only; it is never a pre-push quality GO.
--strict refuses execution outside a COMPLETE real repository checkout, then
runs every mandatory cross-version prepush command. No remote actions.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE_GATES = [
    ("compile_all_ire", ["-m", "compileall", "-q", "ire"]),
    ("ire_unit", ["-m", "unittest", "discover", "-s", "ire/tests", "-v"]),
    ("v5_unit", ["-m", "unittest", "discover", "-s", "ire/v5/tests", "-p", "test_*.py", "-v"]),
    ("v5_app_unit", ["-m", "unittest", "discover", "-s", "ire/v5_app/tests", "-p", "test_*.py", "-v"]),
    ("v5_preflight", ["-m", "ire.v5.preflight", "--root", "."]),
    ("v5_one_turn", ["-m", "ire.v5.one_turn_run", "--root", "."]),
]
V6_GATES = [
    ("v6_syntax", ["-m", "compileall", "-q", "ire/v6"]),
    ("v6_adversarial", ["-m", "unittest", "discover", "-s", "ire/v6/tests", "-p", "test_*.py", "-v"]),
]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=False)


def _check_full_checkout(root: Path, expected_sha: str | None):
    reasons = []
    if expected_sha is None:
        reasons.append("EXACT_CANONICAL_HEAD_SHA_REQUIRED")
    elif not isinstance(expected_sha, str) or len(expected_sha) != 40 or any(
            c not in "0123456789abcdef" for c in expected_sha):
        reasons.append("EXPECTED_HEAD_SHA_FORMAT_INVALID")
    required = ("data/claims.jsonl", "ire/v5/engine.py",
                "ire/v5/one_turn_run.py", "ire/v5/preflight.py",
                ".github/workflows/ire-cleanroom-gate.yml")
    for name in required:
        if not (root/name).is_file():
            reasons.append("REQUIRED_REPO_FILE_MISSING:" + name)
    if sys.version_info[:2] != (3, 11):
        reasons.append("PYTHON_3_11_PIN_REQUIRED_CURRENT:" +
                       ".".join(map(str, sys.version_info[:2])))
    head = _git(root, "rev-parse", "HEAD")
    if head.returncode:
        reasons.append("GIT_CHECKOUT_REQUIRED")
        return reasons, None
    sha = head.stdout.strip()
    if expected_sha is not None and sha != expected_sha:
        reasons.append("EXPECTED_HEAD_MISMATCH")
    worktree = _git(root, "rev-parse", "--show-toplevel")
    if worktree.returncode or Path(worktree.stdout.strip()).resolve() != root.resolve():
        reasons.append("CHECKOUT_ROOT_MISMATCH")
    sparse = _git(root, "config", "--bool", "core.sparseCheckout")
    if sparse.returncode == 0 and sparse.stdout.strip() == "true":
        reasons.append("SPARSE_CHECKOUT_NOT_ALLOWED")
    tracked = _git(root, "ls-tree", "-r", "--name-only", "HEAD")
    if tracked.returncode:
        reasons.append("TRACKED_TREE_NOT_AVAILABLE")
    else:
        tracked_paths = [x for x in tracked.stdout.splitlines() if x]
        if not tracked_paths:
            reasons.append("EMPTY_GIT_TREE")
        missing = [p for p in tracked_paths if not (root/p).exists()]
        if missing:
            reasons.append("TRACKED_FILES_MISSING:"+str(len(missing))+
                           ":"+",".join(missing[:5]))
    # V6 is a wholly new namespace. This milestone must not silently ship
    # changes to older engines, approved master or research registries.
    dirty = _git(root,"status","--porcelain","--untracked-files=no","--",
                 "main", "data", "knowledge", "synthesis", "ire/v3", "ire/v4", "ire/v5")
    if dirty.returncode or dirty.stdout.strip():
        reasons.append("PROTECTED_LEGACY_PATHS_DIRTY")
    return reasons, sha


def run(root: Path, *, strict=False, expected_sha: str | None = None) -> dict:
    root = root.resolve()
    if not (root/"ire/v6/store.py").is_file():
        return {"mode":"strict" if strict else "isolated",
                "outcome":"BLOCKED", "reason":"V6_SOURCE_ROOT_INVALID",
                "checks":[], "engine_quality_certified":False}
    repo_sha = None
    if strict:
        reasons, repo_sha = _check_full_checkout(root, expected_sha)
        if reasons:
            return {"mode":"strict", "outcome":"BLOCKED_PREPUSH_VALIDATION",
                    "reason":";".join(reasons), "base_sha":repo_sha,
                    "checks":[],"engine_quality_certified":False}
    checks=[]
    for label, args in (V6_GATES + (BASE_GATES if strict else [])):
        result = subprocess.run([sys.executable, *args],cwd=root,
                                check=False, capture_output=True, text=True)
        checks.append({"label":label,"exit_code":result.returncode,
                       "status":"PASS" if result.returncode==0 else "FAIL",
                       "stdout_tail":result.stdout[-500:],
                       "stderr_tail":result.stderr[-750:]})
        if result.returncode:
            break
    return {"schema":"IRE_V6_VALIDATION_RUN_V1",
            "mode":"strict" if strict else "isolated",
            "base_sha":repo_sha,
            "outcome": ("ALL_MANDATORY_SOFTWARE_CHECKS_PASS_ENGINE_QUALITY_NOT_CERTIFIED"
                        if strict and len(checks)==len(V6_GATES+BASE_GATES)
                        and all(c["exit_code"]==0 for c in checks)
                        else "ISOLATED_V6_SUBSYSTEM_CHECKS_PASS_ENGINE_QUALITY_NOT_CERTIFIED"
                        if not strict and len(checks)==len(V6_GATES)
                        and all(c["exit_code"]==0 for c in checks)
                        else "VALIDATION_FAILED"),
            "checks":checks,
            "source_original_bytes_verified":False,
            "independent_semantic_recall_measured":False,
            "engine_quality_certified":False,
            "p0_go":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path("."))
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--strict",action="store_true")
    mode.add_argument("--isolated",action="store_true")
    parser.add_argument("--expected-sha",default=None)
    args=parser.parse_args()
    out=run(args.root,strict=args.strict,expected_sha=args.expected_sha)
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    return 0 if out["outcome"].startswith((
        "ALL_MANDATORY_SOFTWARE_CHECKS_PASS", "ISOLATED_V6_SUBSYSTEM_CHECKS_PASS")) else 2


if __name__=="__main__":
    raise SystemExit(main())
