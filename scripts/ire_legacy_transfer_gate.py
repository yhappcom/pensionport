#!/usr/bin/env python3
"""P0-0-05: verify complete legacy Git branch/PR/issue HANDOFF, not E1-E5 approval.

Every one of 11 maximal divergent branch heads is represented by the complete
Git blob path census (1103 rows) from the frozen 5939-row historical index.
Exactly 42 formerly-open closed/unmerged PRs and OPEN issues #48 and #50 have
explicit blocker IDs. CI is OFFLINE; live GitHub states were independently
checked when the register was captured. No private SRT bytes are opened.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
REGISTER = Path("docs/IRE_P0_0_05_LEGACY_TRANSFER_REGISTER_20261122.json")
PATH_CENSUS = Path("docs/IRE_P0_0_05_ALL_DIVERGENT_PATH_DECISIONS_20261122.json")
REGISTRY = Path("docs/BRANCH_HEADS_CONSOLIDATION_REGISTRY_20261122.json")
CATALOG = Path("docs/BRANCH_DIVERGENT_BLOB_CATALOG_20261122.tsv")
TRANSFER = Path("docs/BRANCH_LEGACY_PR_RESEARCH_TRANSFER_20261122.json")
CLOSEOUT = Path("docs/BRANCH_LEGACY_PR_CLOSEOUT_RESULT_20261122.json")
CHECKLIST = Path("docs/IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_20261122.json")
RESEARCH_STATE = Path("docs/IRE_CANONICAL_CURRENT_RESEARCH_STATUS_20261122.json")
SOURCE_HEAD = "dd9bf7fc8d6645ee4fac93e20e84cffb8d486358"
MAIN_HEAD = "d613fd201f4bb077f1ccc74d28dee937b11bfcb2"
DECISIONS = {"ADOPT", "TEST_ONLY", "ARCHIVE", "HOLD"}
COUNTS = {"ADOPT": 0, "TEST_ONLY": 95, "ARCHIVE": 95, "HOLD": 913}
ISSUE_IDS = {48, 50}


def load(root: Path, path: Path) -> dict:
    return json.loads((root / path).read_text(encoding="utf-8"))


def sha_git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def valid_hash(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch("[0-9a-f]{40}", value))


def verify(register: dict, census: dict, root: Path | None = ROOT) -> list[str]:
    errors = []
    def need(condition: bool, code: str):
        if not condition:
            errors.append(code)

    need(register.get("schema") == "IRE_P0_0_05_LEGACY_BRANCH_PR_ISSUE_CANONICAL_HANDOFF_V1", "P005_SCHEMA")
    need(census.get("schema") == "IRE_P0_0_05_MAXIMAL_BRANCH_PATH_CLASSIFICATION_V1", "P005_PATH_SCHEMA")
    need(register.get("source_snapshot_git_head") == SOURCE_HEAD
         and census.get("source_snapshot_git_head") == SOURCE_HEAD, "P005_SOURCE_HEAD_DRIFT")
    need(register.get("preserved_main_sha") == MAIN_HEAD, "P005_MAIN_SHA_DRIFT")
    need(register.get("branch") == "audit/full-repository-snapshot-20261122", "P005_TARGET_BRANCH")
    need(register.get("branch_count") == census.get("max_independent_branches") == 11, "P005_11_BRANCH_COUNT")
    need(census.get("original_divergent_catalog_rows") == 5939, "P005_5939_SOURCE_INDEX_TRUNCATED")
    need(census.get("divergent_rows_in_maximal_branches") == 1103, "P005_1103_CANDIDATES_TRUNCATED")
    need(register.get("pr_count") == 42, "P005_42_PR_COUNT")
    need(register.get("issue_count") == 2, "P005_2_ISSUE_COUNT")
    need(register.get("unverified_adoption_count") == 0, "P005_UNVERIFIED_ADOPTION")
    need(register.get("path_level_register") == str(PATH_CENSUS), "P005_PATHS_NOT_LINKED")
    need(register.get("decision_counts") == COUNTS and census.get("decisions") == COUNTS,
         "P005_DECISION_COUNT_MISMATCH")

    records = census.get("records", [])
    branches = register.get("branches", [])
    prs = register.get("pull_requests", [])
    issues = register.get("issues", [])
    if not all(isinstance(x, list) for x in (records, branches, prs, issues)):
        return errors + ["P005_INVALID_RECORD_LIST"]

    need(len(records) == 1103, "P005_ALL_PATHS_REQUIRED")
    need(len(branches) == 11, "P005_MISSING_MAXIMAL_BRANCH")
    need(len(prs) == 42, "P005_MISSING_PR")
    need(len(issues) == 2, "P005_MISSING_OPEN_ISSUE")
    count = Counter(x.get("decision") for x in records)
    need(all(key in DECISIONS for key in count), "P005_INVALID_PATH_DECISION")
    need(all(count.get(key, 0) == v for key, v in COUNTS.items()), "P005_PATH_DECISION_DRIFT")
    need(not any(x.get("approved_for_current_runtime") or x.get("released_financial_fact")
                 for x in records), "P005_FALSE_RUNTIME_ADOPT_OR_FINANCE_APPROVAL")
    need(all(valid_hash(x.get("original_blob_sha")) and
             x.get("change_status_vs_original_e1") in {"A", "M"} for x in records),
         "P005_PATH_ORIGINAL_BLOB_INVALID")
    need(len({(x.get("branch"), x.get("path")) for x in records}) == len(records),
         "P005_DUPLICATE_SOURCE_PATH")
    need(not any(x.get("decision") == "ADOPT" for x in records), "P005_UNPROVEN_ADOPT")
    need(len({x.get("branch") for x in records}) == 11, "P005_BRANCH_PATH_CENSUS_GAP")

    need(len({x.get("branch") for x in branches}) == 11, "P005_BRANCH_DUPLICATE")
    need(len({x.get("defect_id") for x in branches}) == 11, "P005_BRANCH_DEFECT_DUPLICATE")
    for b in branches:
        name = b.get("branch")
        relevant = [x for x in records if x.get("branch") == name]
        actual_counts = Counter(x.get("decision") for x in relevant)
        need(b.get("divergent_paths") == len(relevant)
             and all(b.get("decision_count", {}).get(k) == actual_counts.get(k, 0)
                     for k in DECISIONS), "P005_BRANCH_PATH_SPLIT:" + str(name))
        need(b.get("portfolio_decision") == "HOLD" and b.get("code_adoption_verified") is False
             and b.get("original_head_ancestry_preserved") is True, "P005_BRANCH_FALSE_GO:" + str(name))
        need(valid_hash(b.get("source_head_sha")) and str(b.get("defect_id", "")).startswith("P005-B"),
             "P005_BRANCH_HEAD_OR_ID:" + str(name))
        need(bool(b.get("workstream")) and bool(b.get("planned_action"))
             and bool(b.get("next_evaluation_stage")), "P005_BRANCH_NEXT_ACTION_MISSING:" + str(name))

    need(len({x.get("number") for x in prs}) == 42, "P005_PR_DUPLICATED")
    need(len({x.get("defect_id") for x in prs}) == 42, "P005_PR_DEFECT_DUPLICATED")
    for pr in prs:
        n = pr.get("number")
        need(isinstance(n, int) and 0 < n < 1000
             and str(pr.get("defect_id", "")) == f"P005-PR-{n:03d}", "P005_PR_DEFECT_ID:" + str(n))
        need(pr.get("disposition") == "HOLD"
             and pr.get("live_closed_verified") is True
             and pr.get("live_head_sha_matched") is True
             and pr.get("archive_head_preserved") is True
             and pr.get("live_merged_at") is None
             and pr.get("real_E3_approved") is False
             and pr.get("E4_owner_authorized") is False
             and pr.get("E5_published") is False,
             "P005_PR_FALSE_APPROVAL:" + str(n))
        need(valid_hash(pr.get("original_head_sha")) and bool(pr.get("review_required"))
             and pr.get("url") == f"https://github.com/yhappcom/pensionport/pull/{n}",
             "P005_PR_EVIDENCE_OR_URL:" + str(n))

    need({x.get("number") for x in issues} == ISSUE_IDS, "P005_ISSUE_48_50_REQUIRED")
    for x in issues:
        n = x.get("number")
        need(x.get("live_state") == "open"
             and x.get("disposition") == "HOLD"
             and x.get("next_release_allowed") is False
             and x.get("issue_url") == f"https://github.com/yhappcom/pensionport/issues/{n}",
             "P005_ISSUE_FALSE_CLOSED:" + str(n))
        need(len(x.get("risks", [])) >= (3 if n == 48 else 6)
             and all(str(y.get("id", "")).startswith(f"P005-I{n:03d}-")
                     and y.get("status") in ("HOLD", "SOFTWARE_MITIGATED_RESEARCH_HOLD")
                     and y.get("description") for y in x.get("risks", [])),
             "P005_ISSUE_RISK_CENSUS_GAP:" + str(n))
    need(register.get("verified_github", {}).get("prior_open_pr_closeout_cohort") == 42
         and register.get("verified_github", {}).get("prior_open_pr_all_live_head_shas_exact") is True
         and register.get("verified_github", {}).get("pr_other_previously_closed") == 32
         and register.get("verified_github", {}).get("pr_total_closed_live") == 74,
         "P005_PR_LIVE_SCOPE_LAUNDERED")
    need(register.get("verified_github", {}).get("issue_numbers_open") == [48, 50],
         "P005_ISSUES_NOT_ACTUALLY_OPEN")
    need(register.get("verified_github", {}).get("last_integrated_six_job_ci", {}).get("run_id") == 44982947486,
         "P005_UPSTREAM_CI_NOT_VERIFIED")
    need(len(register.get("globally_unresolved", [])) >= 6 and
         all(x.get("status") == "HOLD" for x in register.get("globally_unresolved", [])),
         "P005_OPEN_RISKS_SILENCED")

    if root is not None:
        try:
            pinned = register.get("referenced_sources", {})
            src = {REGISTRY:"registry_blob_sha", CATALOG:"source_catalog_blob_sha",
                   TRANSFER:None, CLOSEOUT:None}
            for path, marker in src.items():
                data = (root / path).read_bytes()
                expected = pinned.get(str(path))
                need(valid_hash(expected) and sha_git_blob(data) == expected,
                     "P005_FROZEN_UPSTREAM_BLOB_DRIFT:" + str(path))
                if marker:
                    need(census.get(marker) == expected,
                         "P005_PATH_CENSUS_SOURCE_PIN_DRIFT:" + str(path))
            old = load(root, REGISTRY)
            maximum = {x["name"]:x["sha"] for x in old["maximal_divergent_branches"]}
            need(len(maximum) == 11 and set(maximum) == {x.get("branch") for x in branches},
                 "P005_MAXIMAL_BRANCH_IDENTITY_DRIFT")
            for x in branches:
                need(maximum.get(x["branch"]) == x["source_head_sha"], "P005_BRANCH_HEAD_DRIFT:" + x["branch"])
            text = (root / CATALOG).read_text(encoding="utf-8").splitlines()
            need(len(text) == 5940, "P005_CATALOG_NOT_5939_LINES")
            source_rows = {}
            for line in text[1:]:
                row = line.split("\t")
                need(len(row) == 5, "P005_CATALOG_MALFORMED")
                if len(row) != 5:
                    continue
                name, status, path, blob, ancestor_blob = row
                if name in maximum:
                    source_rows[(name, path)] = (status, blob)
            need(len(source_rows) == 1103, "P005_ORIGINAL_1103_REGISTRY_WRONG")
            for row in records:
                need(source_rows.get((row["branch"], row["path"])) ==
                     (row["change_status_vs_original_e1"], row["original_blob_sha"]),
                     "P005_CANDIDATE_CHANGED:" + str(row["branch"]) + ":" + str(row["path"]))

            transfer = load(root, TRANSFER)
            closed = load(root, CLOSEOUT)
            originals = {x["number"]:x for x in transfer["items"]}
            receipts = {x["number"]:x for x in closed["items"]}
            need(len(originals) == len(receipts) == 42 and
                 {x["number"] for x in prs} == set(originals) == set(receipts),
                 "P005_PR_LIST_NOT_IDENTICAL")
            for p in prs:
                n=p["number"]
                oldp=originals[n]
                done=receipts[n]
                need(oldp["head_sha"] == done["head_sha"] == p["original_head_sha"]
                     and oldp["head_branch"] == p["original_head_branch"]
                     and oldp["base_branch"] == p["original_base_branch"]
                     and done["closed_confirmed"] is True
                     and done["merged_into_main"] is False,
                     "P005_PR_ORIGINAL_HEAD_OR_CLOSEOUT_CHANGED:" + str(n))
            state = load(root, CHECKLIST)
            stages = [x["status"] for x in state["items"][:6]]
            need(stages[:4] == ["PASS", "PASS", "PASS", "PASS"] and
                 (stages[4:] == ["READY", "BLOCKED"] or
                  stages[4:] == ["PASS", "READY"]) and
                 all(x["status"] == "BLOCKED" for x in state["items"][6:]),
                 "P005_OUT_OF_ORDER_CHECKLIST_OR_NOT_PASS")
            current = load(root, RESEARCH_STATE)
            need(all(x["official_stage_release"] == "HOLD" for x in current["stages"].values())
                 and current["reference_cohort"]["actual_formal_v123_child_approvals"] == 0
                 and current["reference_cohort"]["actual_e5_publications"] == 0
                 and current["advisory"]["official_release"] == "HOLD",
                 "P005_FALSE_RESEARCH_GO")
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            errors.append("P005_SOURCE_READ_OR_SCHEMA:"+str(exc))
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",nargs="?",choices=("verify","status"),default="verify")
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    root=args.root.resolve()
    errors=verify(load(root, REGISTER),load(root, PATH_CENSUS),root)
    if errors:
        for x in errors:
            print("P005_LEGACY_HANDOFF_FAIL",x,file=sys.stderr)
        return 1
    print("P005_LEGACY_HANDOFF_PASS original_heads=98 branches=11 path_rows=1103 "
          "ADOPT=0 TEST_ONLY=95 ARCHIVE=95 HOLD=913 prs_closed_unmerged=42 issues_open=48,50")
    if args.command=="status":
        print("P005_RESEARCH_HOLD_PRESERVED E3=0/13 E5=0 next=P0-0-06")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
