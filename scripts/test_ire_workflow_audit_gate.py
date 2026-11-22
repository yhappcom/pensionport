"""P0-0-03 positive/negative checks for all-27 GitHub Actions safety inventory."""
from __future__ import annotations

import copy
import unittest

from scripts.ire_workflow_audit_gate import ROOT, INVENTORY, audit, load, ACTIVE, MANUAL

LEGACY_V5 = ".github/workflows/ire-v5-app-control.yml"
LEGACY_PR = ".github/workflows/ire-v5-p3-p4-one-turn.yml"
LEGACY_CLEAN = ".github/workflows/ire-cleanroom-gate.yml"


class WorkflowAuditGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load(ROOT / INVENTORY)

    def setUp(self):
        self.catalog = copy.deepcopy(self.base)

    def assert_bad(self, needle: str, overrides: dict | None = None):
        issues = audit(self.catalog, root=ROOT, overrides=overrides)
        self.assertTrue(any(needle in x for x in issues), issues)

    def replace(self, name: str, old: str, new: str) -> dict:
        content = (ROOT / name).read_text(encoding="utf-8")
        self.assertIn(old, content)
        return {name:content.replace(old, new, 1)}

    def test_baseline_all_27_pass(self):
        self.assertEqual([], audit(self.catalog, root=ROOT))

    def test_one_current_integration_push_only(self):
        self.assertEqual(1, len([x for x in self.catalog["items"] if x["classification"] == "ACTIVE_PUSH"]))
        self.assertEqual(ACTIVE, next(x["path"] for x in self.catalog["items"] if x["classification"] == "ACTIVE_PUSH"))

    def test_only_one_manual_nondefault_workflow(self):
        self.assertEqual(MANUAL, next(x["path"] for x in self.catalog["items"] if x["classification"] == "MANUAL_ONLY"))

    def test_detect_dropped_inventory_file(self):
        self.catalog["items"].pop()
        self.assert_bad("NOT_ALL_27_WORKFLOWS")

    def test_detect_duplicate_inventory_file(self):
        self.catalog["items"][4]["path"] = self.catalog["items"][3]["path"]
        self.assert_bad("DUPLICATE_WORKFLOW_PATH")

    def test_detect_unreviewed_legacy_mutation(self):
        over = self.replace(LEGACY_V5, "cancel-in-progress: false", "cancel-in-progress: true")
        self.assert_bad("UNREVIEWED_WORKFLOW_CHANGE", over)

    def test_detect_legacy_write_token(self):
        over = self.replace(LEGACY_V5, "contents: read", "contents: write")
        self.assert_bad("WRITE_OR_UNSPECIFIED_CONTENTS_PERMISSION", over)

    def test_detect_unfiltered_legacy_pull_request(self):
        over = self.replace(LEGACY_PR,
            "    branches:\n      - feat/ire-v5-vertical-slice-20261103\n",
            "")
        self.assert_bad("UNSCOPED_LEGACY_PULL_REQUEST", over)

    def test_detect_reopened_cleanroom_broad_pull_request(self):
        over = self.replace(LEGACY_CLEAN,
            "    branches:\n      - feat/ire-cleanroom-engine-20261101\n      - feat/ire-v3-chat-orchestration-20261102\n",
            "")
        self.assert_bad("UNSCOPED_LEGACY_PULL_REQUEST", over)

    def test_detect_unscoped_v169_legacy_pull_request_regression(self):
        path = ".github/workflows/ire-v169-chat-resume.yml"
        over = self.replace(path,
            "    branches:\n      - verify/ire-v6-v168-chat-native-replay-20261118\n",
            "")
        self.assert_bad("UNSCOPED_LEGACY_PULL_REQUEST", over)

    def test_detect_integration_legacy_push(self):
        over = self.replace(LEGACY_V5,
            "      - feat/ire-v5-vertical-slice-20261103",
            "      - audit/full-repository-snapshot-20261122")
        self.assert_bad("LEGACY_PUSH_REACTIVATED", over)

    def test_detect_main_legacy_push(self):
        over = self.replace(LEGACY_V5,
            "      - feat/ire-v5-vertical-slice-20261103",
            "      - main")
        self.assert_bad("LEGACY_MAIN_PUSH_REACTIVATED", over)

    def test_detect_main_pr_on_historic_workflow(self):
        over = self.replace(LEGACY_PR,
            "      - feat/ire-v5-vertical-slice-20261103",
            "      - main")
        self.assert_bad("LEGACY_PR_TO_ACTIVE_BRANCH", over)

    def test_detect_active_governance_push_to_main(self):
        over = self.replace(ACTIVE,
            "branches: [audit/full-repository-snapshot-20261122]",
            "branches: [main]")
        self.assert_bad("GOVERNANCE_PUSH_SCOPE_VIOLATION", over)

    def test_detect_active_governance_unexpected_pr(self):
        over = self.replace(ACTIVE,
            "  workflow_dispatch:",
            "  pull_request:\n    branches: [main]\n  workflow_dispatch:")
        self.assert_bad("GOVERNANCE_UNEXPECTED_EVENTS", over)

    def test_detect_manual_workflow_auto_activation(self):
        over = self.replace(MANUAL,
            "  workflow_dispatch:",
            "  push:\n    branches: [audit/full-repository-snapshot-20261122]\n  workflow_dispatch:")
        self.assert_bad("MANUAL_SNAPSHOT_AUTOEXECUTION", over)

    def test_p006_manual_workflow_never_bulk_exports_tracked_bytes(self):
        raw = (ROOT / MANUAL).read_text(encoding="utf-8")
        self.assertIn("IRE_FULL_TRACKED_METADATA_ONLY_20261122", raw)
        self.assertNotIn("zipfile.ZipFile", raw)
        self.assertNotIn("writestr(", raw)
        self.assertNotIn("pensionport-full-tracked-audit.zip", raw)

    def test_p006_reject_reintroduced_raw_archive_upload(self):
        over = self.replace(MANUAL, "NO_RAW_FILE_EXPORT", "ALLOW_RAW_FILE_EXPORT")
        self.assert_bad("P006_MANUAL_RAW_ARTIFACT_EXPORT_FORBIDDEN", over)

    def test_detect_catalog_false_full_ci_claim(self):
        self.catalog["counts"]["full_v3_v5_v6_e1_e5_integration_ci"] = 1
        self.assert_bad("FULL_ENGINE_CI_FALSE_GO")

    def test_detect_inventory_unreviewed_trigger_event(self):
        self.catalog["items"][0]["expected_events"] = ["schedule"]
        self.assert_bad("EVENT_SET_CHANGED")

    def test_detect_lost_legacy_readonly_policy(self):
        self.catalog["items"][25]["read_only_required"] = False
        self.assert_bad("READ_ONLY_NOT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
