"""V201 E1-only integration tests; synthetic SRT is NOT real E3 gold."""
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.codec import canonical, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT
from v201_e1_native_source_bridge import bridge_v176_to_v6, SCHEMA


def sample_srt():
    return (
        "1\n00:00:01,000 --> 00:00:01,900\n"
        "ETF는 투자 손실이 발생할 수 있습니다.\n\n"
        "2\n00:00:02,000 --> 00:00:02,900\n"
        "여기서 설명은 끝입니다."
    ).encode("utf-8")


class TestV201NativeE1Bridge(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.raw = sample_srt()
        self.owner = EngineChatSession(
            self.root / "owner.sqlite", self.raw, "AbCdEf12345",
            owner_source_sha256=sha256(self.raw),
            window_size=2, expected_window_count=1)
        self.ledger = TransactionStore(self.root / "native.sqlite")
        inventory = {
            "schema": "IRE_V6_OWNER_INVENTORY_V1",
            "entries": [{
                "video_id": self.owner.source.video_id,
                "source_sha256": self.owner.source.source_sha256,
                "manifest_sha256": self.owner.source.manifest_sha256,
                "cue_census_sha256": self.owner.source.cue_census_sha256,
            }]
        }
        self.inventory_bytes = canonical(inventory)
        self.inventory_sha = sha256(self.inventory_bytes)
        self.scope = "synthetic_e1_scope_001"

    def args(self, **extras):
        values = dict(
            engine=self.owner, ledger=self.ledger, scope_id=self.scope,
            inventory_bytes=self.inventory_bytes,
            expected_inventory_sha256=self.inventory_sha,
            expected_owner_head=self.owner.progress()["checkpoint_head_sha256"],
            new_scope=True)
        values.update(extras)
        return values

    def commit_source_review(self):
        challenge = self.owner.prepare(limit=2, source_first_only=True)
        records = []
        for cue in challenge["target_cues"]:
            index = cue["cue_index"]
            if index == 1:
                claims = [{
                    "proposition": "ETF는 투자 손실이 발생할 수 있다고 설명한다.",
                    "kind": "FACT",
                    "quote": "ETF는 투자 손실이 발생할 수 있습니다.",
                    "context_cue_indices": [1],
                    "conditions": [], "exceptions": [],
                    "numeric_tokens": [], "high_risk": True,
                    "needs_official_source": True,
                }]
            else:
                claims = []
            records.append({
                "cue_index": index,
                "source_text_sha256": cue["source_text_sha256"],
                "disposition": "ASSERTION" if claims else "NON_RESEARCH",
                "analysis": "원문을 확인한 잠정 발화 분석일 뿐 최종 금융 사실을 승인하지 않았습니다.",
                "speaker_role": "HOST", "limitations_checked": True,
                "claims": claims,
            })
        self.owner.submit(challenge, {
            "schema": COMMIT,
            "challenge_sha256": challenge["challenge_sha256"],
            "review_executor": "CHATGPT_IN_CHAT",
            "responses": records,
        })

    def test_01_private_original_native_stage_bridge(self):
        self.commit_source_review()
        before = self.owner.progress()
        out = bridge_v176_to_v6(**self.args())
        self.assertEqual(out["schema"], SCHEMA)
        self.assertEqual(out["source_cue_reviewed"], 2)
        self.assertTrue(out["source_first_review_complete"])
        self.assertTrue(out["native_read_snapshot_replayed"])
        self.assertEqual(self.owner.progress(), before)
        self.assertEqual(out["knowledge_published"], 0)
        self.assertEqual(out["e1_status"], "HOLD_APPROVAL_AND_STORAGE_PATH_NOT_CONNECTED")
        self.assertFalse(out["all_stages_passed"])

    def test_02_native_resume_does_not_recreate_scope(self):
        self.commit_source_review()
        first = bridge_v176_to_v6(**self.args())
        second = bridge_v176_to_v6(**self.args(new_scope=False))
        self.assertEqual(first, second)

    def test_03_cannot_use_false_owner_head(self):
        with self.assertRaisesRegex(InvalidInput, "EXTERNAL_OWNER_HEAD_DRIFT"):
            bridge_v176_to_v6(**self.args(expected_owner_head="0" * 64))

    def test_04_cannot_accept_unpinned_owner_inventory(self):
        with self.assertRaises(InvalidInput):
            bridge_v176_to_v6(**self.args(
                expected_inventory_sha256="0" * 64))

    def test_05_untrusted_dict_cannot_impersonate_actual_journal(self):
        with self.assertRaisesRegex(InvalidInput, "ACTUAL_V176_AND_V6_INSTANCES_REQUIRED"):
            bridge_v176_to_v6(**self.args(engine={"e3_approved": True}))

    def test_06_unreviewed_original_keeps_unresolved_and_e1_hold(self):
        out = bridge_v176_to_v6(**self.args())
        self.assertEqual(out["source_cue_reviewed"], 0)
        self.assertFalse(out["source_first_review_complete"])
        self.assertEqual(out["e1_status"], "HOLD_APPROVAL_AND_STORAGE_PATH_NOT_CONNECTED")
        self.assertEqual(out["e4_status"], "NOT_ENTERED")

    def test_07_cannot_reset_existing_native_scope_as_new(self):
        self.commit_source_review()
        bridge_v176_to_v6(**self.args())
        with self.assertRaises(Exception):
            bridge_v176_to_v6(**self.args(new_scope=True))

    def test_08_cannot_start_resume_without_native_scope(self):
        with self.assertRaises(Exception):
            bridge_v176_to_v6(**self.args(new_scope=False))

    def test_09_reopened_native_ledger_and_owner_reproduces_hashes(self):
        self.commit_source_review()
        first = bridge_v176_to_v6(**self.args())
        new_owner = EngineChatSession(
            self.root / "owner.sqlite", self.raw, "AbCdEf12345",
            owner_source_sha256=sha256(self.raw),
            window_size=2, expected_window_count=1)
        new_ledger = TransactionStore(self.root / "native.sqlite")
        second = bridge_v176_to_v6(
            new_owner, new_ledger, scope_id=self.scope,
            inventory_bytes=self.inventory_bytes,
            expected_inventory_sha256=self.inventory_sha,
            expected_owner_head=first["owner_head_sha256"],
            new_scope=False)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
