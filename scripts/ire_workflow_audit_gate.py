#!/usr/bin/env python3
"""P0-0-03: fail-closed audit of ALL 27 current GitHub Actions definitions.

This is static event/permissions scope checking, not a GitHub branch ruleset,
not a complete Actions YAML interpreter, and not a full Python V3/V5/V6 CI.
Only parse the trigger/branch/permissions subset used in this repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INVENTORY = pathlib.Path("docs/IRE_P0_0_03_WORKFLOW_AUDIT_INVENTORY_20261122.json")
BRANCHES = pathlib.Path("docs/BRANCH_HEADS_CONSOLIDATION_REGISTRY_20261122.json")
EXPECTED_EVENTS = {"push", "pull_request", "workflow_dispatch", "schedule"}
TARGET = "audit/full-repository-snapshot-20261122"
ACTIVE = ".github/workflows/full-all-branch-history-audit-20261122.yml"
MANUAL = ".github/workflows/full-repository-snapshot-audit-20261122.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def events_and_targets(raw: str) -> dict[str, list[str]]:
    """Parse only top-level YAML on: events and branches; reject ambiguous forms."""
    lines = raw.splitlines()
    try:
        on_idx = next(i for i, line in enumerate(lines) if line == "on:")
    except StopIteration:
        return {}
    block = []
    for line in lines[on_idx + 1:]:
        if line.strip() and not line.startswith((" ", "\t", "#")):
            break
        block.append(line)
    result: dict[str, list[str]] = {}
    active_event = None
    in_branches = False
    for line in block:
        event = re.fullmatch(r"  (push|pull_request|workflow_dispatch|schedule):\s*(?:#.*)?", line)
        if event:
            active_event = event.group(1)
            result[active_event] = []
            in_branches = False
            continue
        if not active_event:
            continue
        if re.match(r"^    branches:\s*$", line):
            in_branches = True
            continue
        inline = re.fullmatch(r"    branches:\s*\[([^\]]+)\]\s*(?:#.*)?", line)
        if inline:
            result[active_event].extend(z.strip().strip("'\"") for z in inline.group(1).split(","))
            in_branches = False
            continue
        if in_branches:
            value = re.match(r"^      -\s*([^#]+?)(?:\s+#.*)?$", line)
            if value:
                result[active_event].append(value.group(1).strip().strip("'\""))
            elif line and not line.startswith(("      ", "#")):
                in_branches = False
    return result


def content_rights(raw: str) -> list[str]:
    return re.findall(r"(?m)^\s+contents:\s*(read|write|none)\s*(?:#.*)?$", raw)


def audit(catalog: dict, root: pathlib.Path | None = ROOT,
          overrides: dict[str, str] | None = None) -> list[str]:
    issues = []
    def require(ok: bool, error: str):
        if not ok:
            issues.append(error)

    require(catalog.get("schema") == "IRE_P0_0_03_ALL_27_GITHUB_ACTIONS_WORKFLOW_AUDIT_V1", "SCHEMA_INVALID")
    require(catalog.get("branch") == TARGET, "TARGET_BRANCH_MISMATCH")
    require(catalog.get("preserved_main") == "d613fd201f4bb077f1ccc74d28dee937b11bfcb2", "MAIN_SHA_NOT_PRESERVED")
    items = catalog.get("items", [])
    if not isinstance(items, list):
        return issues + ["CATALOG_ITEMS_NOT_LIST"]
    require(len(items) == 27, "NOT_ALL_27_WORKFLOWS")
    paths = [x.get("path") for x in items]
    require(len(set(paths)) == len(paths), "DUPLICATE_WORKFLOW_PATH")
    require(ACTIVE in paths and MANUAL in paths, "REQUIRED_WORKFLOW_MISSING")
    require(catalog.get("counts", {}).get("total") == 27, "COUNT_FALSE_TOTAL")
    expected_names = {p for p in paths if isinstance(p, str)}
    if root is not None:
        discovered = {p.relative_to(root).as_posix() for p in (root / ".github/workflows").glob("*.yml")}
        discovered |= {p.relative_to(root).as_posix() for p in (root / ".github/workflows").glob("*.yaml")}
        require(discovered == expected_names, "ACTUAL_WORKFLOW_FILE_SET_CHANGED")
    actual_counts = {"ACTIVE_PUSH":0, "MANUAL_ONLY":0, "LEGACY_RETIRED":0}
    original_names = set()
    if root is not None:
        orig = load(root / BRANCHES)
        original_names = {x["name"] for x in orig["branches"]}
        require(orig["branch_count"] == len(original_names) == 98, "BRANCH_REGISTRY_NOT_98")
    for item in items:
        path = item.get("path")
        if not isinstance(path, str) or not re.fullmatch(r"\.github/workflows/[-a-z0-9]+\.ya?ml", path):
            issues.append("UNSAFE_WORKFLOW_PATH:" + str(path)); continue
        typ = item.get("classification")
        if typ not in actual_counts:
            issues.append("INVALID_CLASSIFICATION:" + path); continue
        actual_counts[typ] += 1
        require(item.get("read_only_required") is True, "READ_ONLY_NOT_REQUIRED:" + path)
        if path == ACTIVE:
            require(typ == "ACTIVE_PUSH", "GOVERNANCE_NOT_ACTIVE")
        elif path == MANUAL:
            require(typ == "MANUAL_ONLY", "SNAPSHOT_NOT_MANUAL")
        else:
            require(typ == "LEGACY_RETIRED", "HISTORICAL_WORKFLOW_REACTIVATED:" + path)
        try:
            raw = overrides[path] if overrides and path in overrides else (root / path).read_text(encoding="utf-8") if root is not None else None
        except OSError:
            raw = None
        if raw is None:
            issues.append("WORKFLOW_CONTENT_MISSING:" + path); continue
        expected_sha = item.get("source_git_blob_sha")
        require(bool(re.fullmatch(r"[a-f0-9]{40}", str(expected_sha))), "INVALID_BLOB_PIN:" + path)
        # The active governance workflow updates itself to install this check.
        # Keep historic audited blob pin for provenance but do not self-pin it
        # (otherwise the workflow/catalog/check code forms a hash cycle).
        if path != ACTIVE:
            require(blob_sha(raw.encode()) == expected_sha, "UNREVIEWED_WORKFLOW_CHANGE:" + path)
        result = events_and_targets(raw)
        require(bool(result), "TOP_LEVEL_ON_MISSING_OR_UNKNOWN:" + path)
        require(set(result) <= EXPECTED_EVENTS, "UNRECOGNIZED_TRIGGER:" + path)
        require(set(result) == set(item.get("expected_events", [])), "EVENT_SET_CHANGED:" + path)
        rights = content_rights(raw)
        require(bool(rights) and all(r == "read" for r in rights), "WRITE_OR_UNSPECIFIED_CONTENTS_PERMISSION:" + path)
        if typ == "ACTIVE_PUSH":
            require(result.get("push") == [TARGET], "GOVERNANCE_PUSH_SCOPE_VIOLATION")
            require("pull_request" not in result and "schedule" not in result, "GOVERNANCE_UNEXPECTED_EVENTS")
        elif typ == "MANUAL_ONLY":
            require(result == {"workflow_dispatch":[]}, "MANUAL_SNAPSHOT_AUTOEXECUTION")
        else:
            require(TARGET not in result.get("push", []), "LEGACY_PUSH_REACTIVATED:" + path)
            require("main" not in result.get("push", []), "LEGACY_MAIN_PUSH_REACTIVATED:" + path)
            # Legacy push scope must reference explicit retired refs only, never all refs.
            if "push" in result:
                require(bool(result["push"]), "UNSCOPED_LEGACY_PUSH:" + path)
            if "pull_request" in result:
                require(bool(result["pull_request"]), "UNSCOPED_LEGACY_PULL_REQUEST:" + path)
                require(TARGET not in result["pull_request"] and "main" not in result["pull_request"], "LEGACY_PR_TO_ACTIVE_BRANCH:" + path)
            for event in ("push", "pull_request"):
                if root is not None:
                    for name in result.get(event, []):
                        require(name in original_names and name not in (TARGET, "main"), "UNKNOWN_OR_ACTIVE_LEGACY_TARGET:" + path + ":" + name)
    counts = catalog.get("counts", {})
    for k, v in (("ACTIVE_PUSH", 1), ("MANUAL_ONLY", 1), ("LEGACY_RETIRED", 25)):
        require(actual_counts[k] == v, "CLASSIFICATION_COUNT_"+k)
    require(counts.get("active_push") == 1 and counts.get("manual_only") == 1
            and counts.get("legacy_retired") == 25, "CATALOG_COUNTS_MISMATCH")
    require(counts.get("write_content_permission") == 0 and counts.get("unfiltered_pull_request") == 0
            and counts.get("legacy_active_integration_push") == 0, "CATALOG_SECURITY_FLAG_MISMATCH")
    require(counts.get("full_v3_v5_v6_e1_e5_integration_ci") == 0, "FULL_ENGINE_CI_FALSE_GO")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("verify", "status"), default="verify")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    d = load(root / INVENTORY)
    errors = audit(d, root=root)
    if errors:
        for error in errors:
            print("WORKFLOW_AUDIT_GATE_FAIL", error, file=sys.stderr)
        return 1
    print("WORKFLOW_AUDIT_GATE_PASS total=27 active_push=1 manual_nondefault=1 historic_dormant=25 contents_write=0 broad_pr=0 p0_0_03_historical_full_engine_ci=NOT_YET_current_integrated_CI=SEPARATE_SIX_JOB_GATE")
    if args.command == "status":
        print("NEXT_IRE_WORK: P0-0-04 unified pinned Python 3.11.18 CI, NOT proven by this workflow audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
