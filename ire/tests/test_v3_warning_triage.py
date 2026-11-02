"""Coded review queue coverage; original or real private text never in fixtures."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.source import sha256
from ire.v3_orchestrator import ChatBatchQueue
from ire.v3_warning_triage import (build_warning_triage,save_warning_triage,
                                    _match)
from test_engine import VID


class WarningTriageTests(unittest.TestCase):
    def test_product_and_period_matcher_with_synthetic_language(self):
        self.assertTrue(_match('UNSUPPORTED_SPECIFIC_PRODUCT_국민연금',
                               '우리는 국민연금 상담을 하겠습니다.'))
        self.assertFalse(_match('UNSUPPORTED_SPECIFIC_PRODUCT_연금저축',
                                '개인연금이라는 일반상품입니다.'))
        self.assertTrue(_match('UNSUPPORTED_MONTHLY_SOURCE_UNIT',
                               '매월 20만원이 생깁니다.'))

    def test_missing_current_quote_routes_to_primary_cue_without_auto_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            raw=('1\n00:00:00,000 --> 00:00:01,000\n'
                 '국민연금 수령액은 예시입니다.\n\n'
                 '2\n00:00:01,200 --> 00:00:02,000\n'
                 '이 상품은 설명 대상입니다.\n').encode('utf-8')
            source=root/'sample.srt';source.write_bytes(raw)
            manifest={'schema':'IRE_V2_CHAT_BATCH_V1',
                      'research_as_of':'2026-11-02',
                      'videos':[{'video_id':VID,'source_sha256':sha256(raw),
                                 'original_srt_path':str(source),
                                 'private_chat_sessions_path':str(root/'private')}]}
            q=ChatBatchQueue(manifest)
            self.assertEqual(q.status()['accepted_windows'],0)
            report=build_warning_triage(q)
            self.assertEqual(report['warning_count'],0)
            self.assertFalse(report['ready_for_financial_fact_approval'])
            path=save_warning_triage(report,str(root/'triage'))
            self.assertEqual(Path(path).stat().st_mode & 0o077,0)
            with self.assertRaises(FileExistsError):
                save_warning_triage(report,str(root/'triage'))
            loaded=json.loads(Path(path).read_text())
            self.assertEqual(loaded['report_sha256'],report['report_sha256'])

    def test_hash_tampering_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            report={'schema':'IRE_V3_PRIVATE_SEMANTIC_WARNING_TRIAGE_V1',
                    'warnings':[], 'report_sha256':'0'*64}
            with self.assertRaisesRegex(ValueError,'V3_TRIAGE_REPORT_INVALID'):
                save_warning_triage(report,temp)

    def test_no_model_generated_claims_in_output_without_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            raw=('1\n00:00:00,000 --> 00:00:01,000\n'
                 '매월 20만원 연금 사례\n').encode()
            source=root/'sample.srt';source.write_bytes(raw)
            q=ChatBatchQueue({'schema':'IRE_V2_CHAT_BATCH_V1',
                              'research_as_of':'2026-11-02',
                              'videos':[{'video_id':VID,
                                         'source_sha256':sha256(raw),
                                         'original_srt_path':str(source),
                                         'private_chat_sessions_path':str(root/'private')}]})
            result=build_warning_triage(q)
            self.assertEqual(result['warnings'],[])
            self.assertEqual(result['still_require_semantic_review'],0)
            self.assertTrue(result['model_self_review_not_independent_gold'])


if __name__=='__main__':unittest.main()