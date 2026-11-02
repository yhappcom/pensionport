"""Synthetic only; source-first unseen holdout never uses cached model answers."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ire.source import sha256
from ire.v3_orchestrator import ChatBatchQueue
from ire.v3_blind_protocol import plan_blind_review,save_blind_review_plan
from test_engine import VID


class SourceBlindProtocolTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.raw=("1\n00:00:00,000 --> 00:00:01,000\n"
                  "국민연금 추납은 실제 조건을 확인해야 합니다.\n\n"
                  "2\n00:00:01,000 --> 00:00:02,000\n"
                  "금액은 25만 원 예시입니다.\n").encode("utf-8")
        source=self.root/'source.srt'
        source.write_bytes(self.raw)
        self.queue=ChatBatchQueue({"schema":"IRE_V2_CHAT_BATCH_V1",
                                    "research_as_of":"2026-11-02",
                                    "videos":[{"video_id":VID,
                                               "source_sha256":sha256(self.raw),
                                               "original_srt_path":str(source),
                                               "private_chat_sessions_path":str(self.root/'session')}]})

    def test_source_only_plan_has_no_propositions_or_old_gold(self):
        result=plan_blind_review(self.queue,1,"a"*40)
        self.assertEqual(result['task_count'],1)
        self.assertEqual(result['reviewer_task_slots'],['REVIEWER_A','REVIEWER_B'])
        self.assertFalse(result['model_answers_included'])
        self.assertFalse(result['actual_human_gold_received'])
        self.assertFalse(result['financial_semantic_recall_certified'])
        text=json.dumps(result,ensure_ascii=False)
        self.assertNotIn('cue_dispositions',text)
        self.assertNotIn('proposition',text)
        self.assertNotIn('claimed_relation',text)
        self.assertEqual(result['tasks'][0]['primary_cues'][0]['cue_index'],1)

    def test_deterministic_seed_for_reproducible_holdout(self):
        a=plan_blind_review(self.queue,1,"very-private-seed"*4)
        b=plan_blind_review(self.queue,1,"very-private-seed"*4)
        self.assertEqual(a['plan_sha256'],b['plan_sha256'])
        self.assertNotEqual(a['source_only_sampling_seed_sha256'],
                            "very-private-seed"*4)

    def test_private_files_are_immutable_and_not_public(self):
        plan=plan_blind_review(self.queue,1,"seed"*10)
        target=Path(save_blind_review_plan(plan,str(self.root/'blind')))
        self.assertEqual(target.stat().st_mode & 0o077,0)
        with self.assertRaises(FileExistsError):
            save_blind_review_plan(plan,str(self.root/'blind'))

    def test_forged_completion_flag_is_refused(self):
        plan=plan_blind_review(self.queue,1,"q"*40)
        plan['actual_human_gold_received']=True
        with self.assertRaisesRegex(ValueError,'V3_BLIND_PLAN_INTEGRITY_INVALID'):
            save_blind_review_plan(plan,str(self.root/'blind'))


if __name__=='__main__':unittest.main()