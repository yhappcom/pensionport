"""Synthetic only; source-first unseen holdout never uses cached model answers."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ire.source import sha256
from ire.v3_orchestrator import ChatBatchQueue
from ire.v3_blind_protocol import plan_blind_review,save_blind_review_plan,audit_blind_review_plan,_serialize
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

    def test_sealed_holdout_source_cues_recheck_and_no_gold_certification(self):
        plan=plan_blind_review(self.queue,1,"seed"*10)
        result=audit_blind_review_plan(self.queue,plan)
        self.assertEqual(result['verified_task_count'],1)
        self.assertEqual(result['now_has_cached_model_answers_count'],0)
        self.assertTrue(result['task_source_and_quotes_match'])
        self.assertFalse(result['certified_real_world_recall'])
        self.assertFalse(result['prior_chat_model_context_exposure_verified_absent'])

    def test_source_text_tamper_fails_even_with_all_recomputed_self_hashes(self):
        plan=plan_blind_review(self.queue,1,"seed"*10)
        task=plan['tasks'][0]
        task['primary_cues'][0]['text']='Forged model prediction substituted for original'
        core={k:v for k,v in task.items() if k!='task_sha256'}
        task['task_sha256']=sha256(_serialize(core))
        plan['plan_sha256']=sha256(_serialize({k:v for k,v in plan.items() if k!='plan_sha256'}))
        with self.assertRaisesRegex(ValueError,'SOURCE_DIVERGENCE'):
            audit_blind_review_plan(self.queue,plan)

    def test_duplicate_task_detected_even_if_plan_self_consistent(self):
        plan=plan_blind_review(self.queue,1,"seed"*10)
        plan['tasks'].append(plan['tasks'][0].copy())
        plan['task_count']=2
        plan['source_sampling'][0]['selected_unseen_windows']=2
        plan['plan_sha256']=sha256(_serialize({k:v for k,v in plan.items() if k!='plan_sha256'}))
        with self.assertRaisesRegex(ValueError,'DUPLICATE_TASK'):
            audit_blind_review_plan(self.queue,plan)

    def test_existing_model_answer_flags_contamination_not_independent_gold(self):
        from unittest.mock import patch
        plan=plan_blind_review(self.queue,1,"seed"*10)
        session=self.queue.sessions[0]
        with patch.object(session,'_answer',return_value={'claims':[]}):
            result=audit_blind_review_plan(self.queue,plan)
        self.assertEqual(result['now_has_cached_model_answers_count'],1)
        self.assertFalse(result['no_cached_model_answers_on_selected_windows'])
        self.assertFalse(result['actual_independent_gold_received'])

    def test_forged_completion_flag_is_refused(self):
        plan=plan_blind_review(self.queue,1,"q"*40)
        plan['actual_human_gold_received']=True
        with self.assertRaisesRegex(ValueError,'V3_BLIND_PLAN_INTEGRITY_INVALID'):
            save_blind_review_plan(plan,str(self.root/'blind'))


if __name__=='__main__':unittest.main()