#!/usr/bin/env python3
"""Fail-closed, auditable, strictly sequential IRE development checklist gate.

This validates machine-readable bookkeeping, NOT independent financial truth,
the authenticity of a ChatGPT chat message, or the substance of submitted evidence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = pathlib.Path("docs/IRE_STRICT_SEQUENTIAL_CHECKLIST_CATALOG_20261122.json")
STATE = pathlib.Path("docs/IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_20261122.json")
CHECKLIST = pathlib.Path("docs/IRE_STRICT_SEQUENTIAL_EXECUTION_CHECKLIST_20261122.md")
VALID = {"BLOCKED", "READY", "IN_PROGRESS", "FAIL", "HOLD", "PASS"}
ACTIVE = {"READY", "IN_PROGRESS", "FAIL", "HOLD"}
SHA = re.compile(r"^[a-fA-F0-9]{40}$")


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prefix_length(items: list[dict]) -> int:
    count = 0
    for item in items:
        if item.get("status") != "PASS":
            break
        count += 1
    return count


def good_report(report: object, task_id: str, verdict: str | None) -> bool:
    if not isinstance(report, dict):
        return False
    if report.get("task_id") != task_id:
        return False
    if report.get("declared_sent_to_user") is not True:
        return False
    if report.get("channel") != "USER_CHAT":
        return False
    if not all(isinstance(report.get(k), str) and report[k].strip()
               for k in ("reported_at", "user_visible_text", "baseline_sha")):
        return False
    if not SHA.fullmatch(report["baseline_sha"]):
        return False
    if verdict is not None and report.get("verdict") != verdict:
        return False
    return True


def valid_evidence(entry: object, expected_kind: str, root: pathlib.Path | None) -> bool:
    if not isinstance(entry, dict):
        return False
    for key in ("kind", "ref", "sha", "scope", "verified_by"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            return False
    if entry["kind"] != expected_kind or not SHA.fullmatch(entry["sha"]):
        return False
    uri = entry["ref"]
    if uri.startswith("https://"):
        if not (uri.startswith("https://github.com/yhappcom/pensionport/") or
                uri.startswith("https://api.github.com/repos/yhappcom/pensionport/")):
            return False
    elif uri.startswith("/") or ".." in pathlib.PurePosixPath(uri).parts:
        return False
    elif root is not None and not (root / uri).is_file():
        return False
    if entry.get("verdict") != "PASS":
        return False
    if expected_kind == "turn2":
        # A textual reference cannot be promoted to cryptographic host authentication.
        if not all(entry.get(k) for k in ("turn1_ref", "turn2_user_message_ref", "authentication_level")):
            return False
    if expected_kind == "publication":
        if not all(entry.get(k) for k in ("publication_id", "knowledge_head", "publication_delta")):
            return False
    return True


def validate(catalog: dict, state: dict,
             root: pathlib.Path | None = None,
             previous: dict | None = None) -> list[str]:
    errors: list[str] = []
    if catalog.get("schema") != "IRE_STRICT_SEQUENTIAL_CHECKLIST_CATALOG_V1":
        errors.append("INVALID_CATALOG_SCHEMA")
    if state.get("schema") != "IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_V1":
        errors.append("INVALID_STATE_SCHEMA")
    if state.get("catalog_path") != CATALOG.as_posix():
        errors.append("STATE_CATALOG_LINK_MISMATCH")
    if state.get("target_branch") != catalog.get("target_branch"):
        errors.append("BRANCH_MISMATCH")
    if state.get("protected_main_sha") != catalog.get("protected_main_sha"):
        errors.append("PINNED_MAIN_MISMATCH")
    if not SHA.fullmatch(str(catalog.get("protected_main_sha", ""))):
        errors.append("INVALID_PROTECTED_MAIN_SHA")
    cats = catalog.get("items", [])
    rows = state.get("items", [])
    if not isinstance(cats, list) or not isinstance(rows, list) or len(cats) != len(rows):
        return errors + ["ITEM_COUNT_MISMATCH"]
    if len(cats) != 60:
        errors.append("EXPECTED_60_ITEMS")
    seen = set()
    stages = []
    for n, (task, row) in enumerate(zip(cats, rows), 1):
        task_id = task.get("id")
        status = row.get("status")
        if task_id in seen or not isinstance(task_id, str):
            errors.append("DUPLICATED_OR_BAD_TASK_ID:" + str(task_id))
        seen.add(task_id)
        if task.get("sequence") != n or row.get("id") != task_id:
            errors.append("TASK_SEQUENCE_OR_ID_MISMATCH:" + str(task_id))
        if task.get("stage_id") not in stages:
            stages.append(task.get("stage_id"))
        if not all(task.get(k) for k in ("title", "acceptance", "required_evidence_kind")):
            errors.append("MISSING_CHECKLIST_CONTRACT:" + str(task_id))
        if status not in VALID:
            errors.append("INVALID_STATUS:" + str(task_id))
        if status == "PASS":
            if not good_report(row.get("start_report"), task_id, "START"):
                errors.append("PASS_MISSING_USER_START_REPORT:" + task_id)
            if not good_report(row.get("end_report"), task_id, "PASS"):
                errors.append("PASS_MISSING_USER_END_REPORT:" + task_id)
            evidence = row.get("evidence", [])
            if not isinstance(evidence, list) or not any(
                valid_evidence(e, task["required_evidence_kind"], root) for e in evidence
            ):
                errors.append("PASS_MISSING_VERIFIABLE_REQUIRED_EVIDENCE:" + task_id)
        elif status in {"FAIL", "HOLD"}:
            if not good_report(row.get("start_report"), task_id, "START"):
                errors.append("FAIL_HOLD_MISSING_USER_START_REPORT:" + task_id)
            if not good_report(row.get("end_report"), task_id, status):
                errors.append("FAIL_HOLD_MISSING_USER_END_REPORT:" + task_id)
            if not isinstance(row.get("failure_reason"), str) or not row["failure_reason"].strip():
                errors.append("FAIL_HOLD_MISSING_CAUSE:" + task_id)
            if not isinstance(row.get("remediation"), str) or not row["remediation"].strip():
                errors.append("FAIL_HOLD_MISSING_REMEDIATION:" + task_id)
        elif status == "IN_PROGRESS":
            if not good_report(row.get("start_report"), task_id, "START"):
                errors.append("IN_PROGRESS_MISSING_USER_START_REPORT:" + task_id)
        elif status in {"READY", "BLOCKED"}:
            if row.get("start_report") or row.get("end_report") or row.get("evidence"):
                errors.append("UNSTARTED_TASK_HAS_SPURIOUS_RECEIPT:" + task_id)
    if stages != catalog.get("stage_order"):
        errors.append("STAGE_ORDER_MISMATCH")
    if len(stages) != 12:
        errors.append("EXPECTED_12_STAGES")
    first_open = prefix_length(rows)
    if first_open < len(rows) and rows[first_open].get("status") not in ACTIVE:
        errors.append("NEXT_ITEM_NOT_ACTIVE:" + str(rows[first_open].get("id")))
    for n in range(first_open + 1, len(rows)):
        if rows[n].get("status") != "BLOCKED":
            errors.append("OUT_OF_ORDER_PROGRESS:" + str(rows[n].get("id")))
    if root is not None:
        checklist_path = root / CHECKLIST
        if not checklist_path.is_file():
            errors.append("HUMAN_CHECKLIST_FILE_MISSING")
        else:
            # Prevent stale [ ] boxes from disguising machine-recorded PASS.
            markdown = checklist_path.read_text(encoding="utf-8")
            observed = re.findall(r"(?m)^- \\[([ xX])\\] \\*\\*([A-Z0-9-]+) · ", markdown)
            if len(observed) != len(rows):
                errors.append("MARKDOWN_CHECKBOX_COUNT_MISMATCH")
            else:
                for i, (mark, ident) in enumerate(observed):
                    if ident != cats[i]["id"]:
                        errors.append("MARKDOWN_CHECKBOX_ORDER_MISMATCH:" + ident)
                    if (mark.lower() == "x") != (rows[i].get("status") == "PASS"):
                        errors.append("MARKDOWN_CHECKBOX_STATE_MISMATCH:" + ident)
    if previous is not None:
        old = previous.get("items")
        if not isinstance(old, list) or len(old) != len(rows):
            errors.append("PREVIOUS_STATE_MISMATCH")
        else:
            old_active = prefix_length(old)
            for n, (before, after) in enumerate(zip(old, rows)):
                if before.get("id") != after.get("id"):
                    errors.append("HISTORIC_ITEM_ID_DRIFT:" + str(n))
                if n < old_active and before != after:
                    errors.append("PREVIOUS_PASS_MUTATED:" + str(before.get("id")))
                if n > old_active + 1 and before != after:
                    errors.append("MULTIPLE_ITEMS_CHANGED_WITHOUT_SEQUENTIAL_REVIEW:" + str(after.get("id")))
                if n == old_active + 1 and before != after:
                    if not (old_active < len(rows) and
                            rows[old_active].get("status") == "PASS" and
                            before.get("status") == "BLOCKED" and
                            after.get("status") == "READY"):
                        errors.append("NEXT_UNLOCK_WITHOUT_PREVIOUS_PASS:" + str(after.get("id")))
                if before.get("status") in {"FAIL", "HOLD"} and after.get("status") != before.get("status"):
                    if not isinstance(after.get("remediation"), str) or not after["remediation"].strip():
                        errors.append("FAILED_ITEM_REOPENED_WITHOUT_REMEDIATION:" + str(after.get("id")))
    return errors


def parent_state(root: pathlib.Path) -> dict | None:
    cp = subprocess.run(
        ["git", "show", "HEAD^:" + STATE.as_posix()],
        cwd=root, capture_output=True, text=True, check=False
    )
    if cp.returncode != 0:
        return None
    return json.loads(cp.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "status", "next"))
    parser.add_argument("--compare-parent", action="store_true")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = load(root / CATALOG)
    state = load(root / STATE)
    prev = parent_state(root) if args.compare_parent else None
    errors = validate(catalog, state, root=root, previous=prev)
    if errors:
        for issue in errors:
            print("CHECKLIST_GATE_FAIL", issue, file=sys.stderr)
        return 1
    rows = state["items"]
    cursor = prefix_length(rows)
    if args.command == "verify":
        print("CHECKLIST_POLICY_PASS checked=%d passed=%d blocked=%d" %
              (len(rows), cursor, sum(x["status"] == "BLOCKED" for x in rows)))
        return 0
    if cursor == len(rows):
        print("ALL_60_ITEMS_PASSED; financial/research evidence still requires independent review")
        return 0
    item = rows[cursor]
    print("NEXT_ITEM", item["id"], "STATE", item["status"],
          "PASS", "%d/%d" % (cursor, len(rows)),
          "BLOCKED_FOLLOWING", len(rows)-cursor-1)
    if args.command == "next" and item["status"] in {"FAIL", "HOLD"}:
        print("WORK_BLOCKED: Correct and retest the SAME item to PASS before starting another")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
