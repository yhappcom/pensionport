"""Issue #48/#50: cross-cue and cross-window speaker-stance attack fixtures.

All source subtitles are synthetic. Exact official statute byte pin is real,
but narrator meaning, completeness, independent quality and advice stay HOLD.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import QualityNotProven, DomainConflict
from ire.v6.official_completion import CANONICAL_PROPOSITION
from ire.v6.source import verify_source
from ire.v6.store import TransactionStore
from ire.v6.tests.test_official_completion import OfficialTerminalV2Tests, SCOPE
from ire.v6.tests.test_source_and_proof import (
    VIDEO, make_srt, make_manifest, make_model, make_review,
)


class Issue4850CrossCueTests(unittest.TestCase):
    setUp = OfficialTerminalV2Tests.setUp
    head = OfficialTerminalV2Tests.head
    setup_recorded = OfficialTerminalV2Tests.setup_recorded
    decision = OfficialTerminalV2Tests.decision
    args = OfficialTerminalV2Tests.args

    def rebase(self, texts, *, cut=4):
        self.raw = make_srt(texts)
        self.manifest = make_manifest(self.raw, cut=cut)
        source = verify_source(self.raw, self.manifest,
            expected_source_sha256=sha256(self.raw),
            expected_manifest_sha256=json_digest(self.manifest))
        inventory = {"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":VIDEO,"source_sha256":sha256(self.raw),
            "manifest_sha256":json_digest(self.manifest),
            "cue_census_sha256":source.cue_census_sha256}]}
        self.inv_bytes = canonical(inventory)
        self.inv_sha = sha256(self.inv_bytes)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.store = TransactionStore(Path(directory.name)/"private"/"cross_cue.db")
        self.store.create_scope(scope_id=SCOPE, video_id=VIDEO,
            source_sha256=sha256(self.raw),
            manifest_sha256=json_digest(self.manifest),
            command_id="cross_cue_genesis")

    def test_01_exact_rule_followed_by_explicit_rebuttal_is_blocked(self):
        self.rebase([CANONICAL_PROPOSITION,
            "방금 인용한 앞의 연금계좌 인출 순서 주장은 틀린 설명입니다.",
            "A neutral independent example.", "Another neutral cue."])
        self.setup_recorded()
        before = self.head()
        with self.assertRaisesRegex(QualityNotProven, "OFFICIAL_CROSS_CUE_REBUTTAL_UNRESOLVED"):
            self.store.issue_terminal_receipt(**self.args())
        self.assertEqual(self.head(), before)
        self.assertFalse(self.store.progress_receipt(SCOPE)["scoped_official_rule_verified"])

    def test_02_exact_rule_followed_by_quotation_disclaimer_is_blocked(self):
        self.rebase([CANONICAL_PROPOSITION,
            "앞의 문장은 잘못된 주장을 인용한 것이며 제 견해가 아닙니다.",
            "A neutral independent example.", "Another neutral cue."])
        self.setup_recorded()
        with self.assertRaisesRegex(QualityNotProven, "OFFICIAL_CROSS_CUE_REBUTTAL_UNRESOLVED"):
            self.store.issue_terminal_receipt(**self.args())

    def test_03_cross_window_rebuttal_without_model_exception_is_blocked(self):
        self.rebase([CANONICAL_PROPOSITION, "Neutral independent cue.",
            "앞의 주장은 사실이 아니므로 적용할 수 없습니다.", "Further neutral cue."],cut=2)
        self.setup_recorded()
        second = make_model(owner="W00002", first=4, last=4,
                            quote1="Further neutral cue.")
        self.store.submit(scope_id=SCOPE,command_id="second_window_model",
                          expected_head=self.head(),kind="MODEL_RECORDED",
                          payload={"window_id":"W00002","model":second})
        self.store.submit_structural_proof(
            scope_id=SCOPE,command_id="second_window_proof",
            expected_head=self.head(),window_id="W00002",
            raw=self.raw,manifest=self.manifest,review=make_review())
        determinations=self.decision()
        second_rev=self.store.snapshot(SCOPE)["state"]["models"]["W00002"]["revision_event_sha256"]
        determinations.append({"window_id":"W00002","claim_id":"C00001",
                               "model_revision_event_sha256":second_rev,
                               "verdict":"NOT_FACT_CLAIM","rule_id":None,
                               "conditions_acknowledged":[]})
        with self.assertRaisesRegex(QualityNotProven, "OFFICIAL_CROSS_CUE_REBUTTAL_UNRESOLVED"):
            self.store.issue_terminal_receipt(**self.args(determinations=determinations))
        self.assertFalse(self.store.progress_receipt(SCOPE)["research_complete"])

    def test_04_no_rebuttal_keeps_only_narrow_statute_verification(self):
        self.setup_recorded()
        result=self.store.issue_terminal_receipt(**self.args())
        self.assertTrue(result["scoped_official_rule_verified"])
        self.assertFalse(result["source_speaker_meaning_verified"])
        self.assertFalse(result["research_complete"])
        self.assertFalse(result["p0_go"])

    def test_05_interleaved_review_cannot_renew_same_rule(self):
        self.setup_recorded()
        first=self.store.issue_terminal_receipt(**self.args())
        model=self.store.snapshot(SCOPE)["state"]["models"]["W00001"]
        self.store.submit(scope_id=SCOPE,command_id="issue50_interleaved_review",
                          expected_head=self.head(),kind="REVIEW_PROPOSED",
                          payload={"window_id":"W00001",
                                   "model_revision_event_sha256":model["revision_event_sha256"],
                                   "review":{"other":"unapproved"}})
        self.assertTrue(self.store.progress_receipt(SCOPE)["scoped_official_rule_verified"])
        with self.assertRaisesRegex(DomainConflict,"OFFICIAL_RULE_ALREADY_VERIFIED_CURRENT"):
            self.store.issue_terminal_receipt(**self.args(command_id="issue50_repeat"))
        assert self.store.read_official_terminal_receipt(
            scope_id=SCOPE,terminal_event_sha256=first["event_sha256"])["is_current"]


if __name__=="__main__":
    unittest.main()
