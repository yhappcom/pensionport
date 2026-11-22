#!/usr/bin/env python3
"""P0-0-07 exact-scope closeout: governance PASS never implies ETF/E1-E5 financial approval."""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
from scripts.ire_checklist_gate import CATALOG, STATE, load, validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER, validate as status_validate

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECEIPT = pathlib.Path("docs/IRE_P0_0_07_STAGE_CLOSEOUT_RECEIPT_20261122.json")
AUDIT = pathlib.Path("docs/IRE_P0_0_01_06_INDEPENDENT_REVALIDATION_20261122.md")
EVIDENCE_SHA = "068f4097a2329a5c2b10f90435ca683f29f26f0c"
EVIDENCE_RUN = 44995407175
MAIN_SHA = "d613fd201f4bb077f1ccc74d28dee937b11bfcb2"

def verify(root: pathlib.Path = ROOT, *, receipt: dict | None = None, state: dict | None = None,
           ledger: dict | None = None) -> list[str]:
    errors: list[str] = []
    need = lambda ok, code: errors.append(code) if not ok else None
    root = root.resolve()
    receipt = receipt if receipt is not None else load(root / RECEIPT)
    state = state if state is not None else load(root / STATE)
    ledger = ledger if ledger is not None else load(root / LEDGER)
    catalog = load(root / CATALOG)
    need(receipt.get("schema") == "IRE_P0_0_07_P0_0_DEVELOPMENT_BASELINE_STAGE_CLOSEOUT_V1", "P007_RECEIPT_SCHEMA")
    need(receipt.get("source_exact_head") == EVIDENCE_SHA and receipt.get("source_exact_head_ci") ==
         {"run_id":EVIDENCE_RUN,"sha":EVIDENCE_SHA,"conclusion":"success",
          "total_jobs":6,"successful_jobs":6,"runner_python":"3.11.18",
          "url":f"https://github.com/yhappcom/pensionport/actions/runs/{EVIDENCE_RUN}"},
         "P007_EVIDENCE_RUN_OR_SHA_WRONG")
    need(receipt.get("unchanged_main_sha") == MAIN_SHA and
         receipt.get("active_branches") == ["main","audit/full-repository-snapshot-20261122"],
         "P007_BRANCH_MAIN_UNCHANGED_REQUIRED")
    need(receipt.get("stage_item_ids") == [f"P0-0-{i:02}" for i in range(1,8)] and
         receipt.get("stage_items_all_pass") is True,
         "P007_STAGE_IDS_OR_PASS_FALSE")
    need(receipt.get("source_independent_audit_path") == AUDIT.as_posix() and
         (root/AUDIT).is_file(), "P007_BASELINE_AUDIT_MISSING")
    need((receipt.get("checklist_pass_total_after_close"),receipt.get("checklist_total"),
          receipt.get("next_ready_item"),receipt.get("blocked_following")) ==
         (7,60,"P0-1-01",52), "P007_TASK_ORDER_INVALID")
    need(receipt.get("immutable_predecessors") is True and
         receipt.get("no_main_merge") is True and receipt.get("no_new_branch") is True,
         "P007_HISTORIC_IMMUTABILITY_INVALID")
    need(receipt.get("new_closeout_sha_ci_validation") ==
         "POST_COMMIT_GITHUB_ACTIONS_REQUIRED_TO_CONFIRM_FINAL_VERDICT__NOT_SELF_ATTESTED",
         "P007_UNJUSTIFIED_SELF_CI_PASS")
    evidence=receipt.get("evidence_digests",{})
    need((evidence.get("baseline_manifest_files"),evidence.get("original_heads"),
          evidence.get("workflow_total"),evidence.get("legacy_prs_closed_unmerged"),
          evidence.get("public_archive_inventory"),evidence.get("b64_reversible_files"),
          evidence.get("unrestored_historical_encrypted_archives")) ==
         (2364,98,27,42,42,6,36),"P007_STAGE_EVIDENCE_COUNTS")
    finance=receipt.get("financial_scope",{})
    need((finance.get("actual_etf_formal_v123_child_approvals"),
          finance.get("actual_etf_e4_owner_authorizations"),
          finance.get("actual_e5_parent_publications"))==(0,0,0) and
         finance.get("independent_etf_gold_verified") is False and
         finance.get("final_stages")==dict.fromkeys(("E1","E2","E3","E4","E5"),"HOLD") and
         finance.get("advisory")=="HOLD",
         "P007_FINANCIAL_RELEASE_FALSE_GO")
    rows=state.get("items",[])
    need(len(rows)==60 and all(x.get("status")=="PASS" for x in rows[:7]) and
         rows[7].get("id")=="P0-1-01" and rows[7].get("status") in {"READY","IN_PROGRESS","HOLD","FAIL"} and
         all(x.get("status")=="BLOCKED" for x in rows[8:]),
         "P007_CHECKLIST_SEQUENCE_FALSE_GO")
    need(not checklist_validate(catalog,state,root=root),"P007_STRICT_CHECKLIST_INVALID")
    need(not status_validate(ledger,root=root),"P007_CANONICAL_LEDGER_INVALID")
    return errors

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=["verify"],nargs="?",default="verify")
    p.add_argument("--root",type=pathlib.Path,default=ROOT)
    args=p.parse_args()
    try:
        failures=verify(args.root)
    except (KeyError,TypeError,ValueError,OSError,IndexError) as e:
        print("P007_CLOSEOUT_FAIL",type(e).__name__,file=sys.stderr)
        return 1
    for reason in failures:print("P007_CLOSEOUT_FAIL",reason,file=sys.stderr)
    if failures:return 1
    print("P007_STAGE_CLOSEOUT_PASS checked=7/60 next=P0-1-01 blockers=52 real_E3=0/13 E5=0 advisory=HOLD main_unchanged=True")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
