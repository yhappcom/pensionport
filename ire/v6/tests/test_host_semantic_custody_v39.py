"""V39 synthetic regression controls: no private video or human gold."""
import copy
import json
import unittest

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from ire.v6.host_semantic_custody_v39 import (
    _v33_draft_registry, audit_host_semantic_custody_v39,
)


def _srt(texts):
    blocks = []
    for idx, txt in enumerate(texts, 1):
        begin, end = idx * 2, idx * 2 + 1
        blocks.append(f'{idx}\n00:00:{begin:02d},000 --> 00:00:{end:02d},000\n{txt}')
    return ('\n\n'.join(blocks) + '\n').encode('utf-8')


class SourceBoundSemanticReviewV39Tests(unittest.TestCase):
    def setUp(self):
        self.vid = 'sz5N9WJS310'
        self.raw = _srt(['ISA 투자의 기간은 3년 예시입니다.',
                         '추정 수익률은 5%를 가정합니다.',
                         '>> 그 수익률이 보장됩니까?',
                         '수익은 보장되지 않습니다.'])
        cues = parse_srt(self.raw)
        drafts = _v33_draft_registry(cues)['W00001']
        self.raws = {self.vid: self.raw}
        self.sources = [{'video_id': self.vid,
                         'original_srt_sha256': sha256(self.raw),
                         'cue_count': len(cues)}]
        self.windows = [{'video_id': self.vid, 'window_id': 'W00001',
                         'cue_first': 1, 'cue_last': len(cues),
                         'original_window_text_sha256': sha256(' '.join(c.text for c in cues).encode()),
                         'v33_candidate_list_sha256': json_digest(drafts)}]
        self.rows = []
        for d in drafts:
            original = ' | '.join(cues[idx - 1].text for idx in d['cue_indices'])
            self.rows.append({
                'video_id': self.vid, 'window_id': 'W00001',
                'claim_id': d['claim_id'], 'cue_indices': d['cue_indices'],
                'source_excerpt': original,
                'source_excerpt_sha256': d['source_text_sha256'],
                'semantic_notes': [{'kind': 'H', 'meaning': '원문과 연결된 잠정 예시입니다.'}],
                'original_audio_verified': False,
                'issuer_terms_verified': False,
                'finance_fact_certified': False,
                'independent_gold': False,
            })

    def audit(self, raws=None, sources=None, windows=None, rows=None):
        return audit_host_semantic_custody_v39(
            self.raws if raws is None else raws,
            self.sources if sources is None else sources,
            self.windows if windows is None else windows,
            self.rows if rows is None else rows)

    def test_all_source_bound_candidates_and_notes_replayed(self):
        receipt = self.audit()
        self.assertEqual(receipt['exact_v33_candidates_source_pinned'], len(self.rows))
        self.assertEqual(receipt['host_reviewed_candidates'], len(self.rows))
        self.assertEqual(receipt['chat_review_items_including_questions'], len(self.rows))
        self.assertFalse(receipt['financial_fact_truth_certified'])
        self.assertFalse(receipt['p0_go'])
        self.assertNotIn('추정 수익률', json.dumps(receipt, ensure_ascii=False))

    def test_actual_note_count_not_hardcoded(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['semantic_notes'].append({'kind': 'Q', 'meaning': '두 번째 독립 질문에 대한 잠정 분류입니다.'})
        result = self.audit(rows=rows)
        self.assertEqual(result['chat_review_items_including_questions'], len(rows) + 1)

    def test_missing_candidate_fails(self):
        with self.assertRaisesRegex(InvalidInput, 'MISSING_CANDIDATE'):
            self.audit(rows=self.rows[:-1])

    def test_duplicate_candidate_fails(self):
        with self.assertRaisesRegex(InvalidInput, 'DUPLICATE_CANDIDATE'):
            self.audit(rows=self.rows + [copy.deepcopy(self.rows[0])])

    def test_wrong_original_source_sha_fails(self):
        sources = copy.deepcopy(self.sources)
        sources[0]['original_srt_sha256'] = '0' * 64
        with self.assertRaisesRegex(InvalidInput, 'ORIGINAL_SRT_SHA_DRIFT'):
            self.audit(sources=sources)

    def test_wrong_v37_draft_digest_fails(self):
        windows = copy.deepcopy(self.windows)
        windows[0]['v33_candidate_list_sha256'] = '0' * 64
        with self.assertRaisesRegex(InvalidInput, 'DIGEST_DRIFT'):
            self.audit(windows=windows)

    def test_wrong_candidate_cue_index_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['cue_indices'] = [2]
        with self.assertRaisesRegex(InvalidInput, 'REFERENCES_NOT_ORIGINAL_DRAFT'):
            self.audit(rows=rows)

    def test_forged_source_excerpt_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['source_excerpt'] = '보장수익률은 99%입니다.'
        with self.assertRaisesRegex(InvalidInput, 'EXCERPT_NOT_ORIGINAL_BYTES'):
            self.audit(rows=rows)

    def test_unsupported_gold_claim_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['independent_gold'] = True
        with self.assertRaisesRegex(InvalidInput, 'UNSUPPORTED_FACT_AUDIO_GOLD'):
            self.audit(rows=rows)

    def test_unsupported_finance_fact_approval_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['finance_fact_certified'] = True
        with self.assertRaisesRegex(InvalidInput, 'UNSUPPORTED_FACT_AUDIO_GOLD'):
            self.audit(rows=rows)

    def test_invalid_semantic_kind_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['semantic_notes'][0]['kind'] = 'CERTIFIED_CURRENT_LAW'
        with self.assertRaisesRegex(InvalidInput, 'KIND_OR_REASON_INVALID'):
            self.audit(rows=rows)

    def test_duplicate_semantic_note_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['semantic_notes'].append(copy.deepcopy(rows[0]['semantic_notes'][0]))
        with self.assertRaisesRegex(InvalidInput, 'DUPLICATE_MEANING_UNIT'):
            self.audit(rows=rows)

    def test_context_fragment_cannot_also_be_claim(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['semantic_notes'][0]['kind'] = 'F'
        rows[0]['semantic_notes'].append({'kind': 'C', 'meaning': '이 문장과 함께 확정 주장을 섞은 경우입니다.'})
        with self.assertRaisesRegex(InvalidInput, 'FRAGMENT_CANNOT_BE_CERTIFIED'):
            self.audit(rows=rows)

    def test_unknown_candidate_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['claim_id'] = 'C99999'
        with self.assertRaisesRegex(InvalidInput, 'UNKNOWN_CANDIDATE'):
            self.audit(rows=rows)

    def test_window_scope_tampering_fails(self):
        windows = copy.deepcopy(self.windows)
        windows[0]['cue_last'] = 3
        with self.assertRaisesRegex(InvalidInput, 'WINDOW_CUE_SCOPE_DRIFT'):
            self.audit(windows=windows)


if __name__ == '__main__':
    unittest.main()
