"""V42 adversarial source-window cohort/replay tests; all synthetic, not gold."""
from __future__ import annotations
import copy
import io
import json
import unittest
import zipfile

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from ire.v6.host_semantic_custody_v39 import _v33_draft_registry
from ire.v6.full_original_risk_intake_v42 import audit_full_original_risk_intake_v42


def _make_srt(texts):
    chunks=[]
    for i,t in enumerate(texts,1):
        start=(i-1)*2;end=start+1
        chunks.append(f'{i}\n00:00:{start//60:02d}:{start%60:02d},000 --> '
                      f'00:00:{end//60:02d}:{end%60:02d},000\n{t}')
    return ('\n\n'.join(chunks)+'\n').encode('utf-8')


def _archive(raw,vid):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'1-100/youtube-transcript-{vid}.srt',raw)
    return buf.getvalue()


class OriginalRiskIntakeV42Tests(unittest.TestCase):
    def setUp(self):
        self.vid='sz5N9WJS310'
        self.raw=_make_srt(['ISA 만기 3년이라고 가정합니다.',
                            'IRP 연금의 5% 수익률은 보장 아닙니다.',
                            '배당수익은 언제 지급되나요?',
                            '예시일 뿐 확정 수익이 아닙니다.'])
        self.archive=_archive(self.raw,self.vid)
        self.sources=[{'video_no':1,'video_id':self.vid,
                      'original_srt_sha256':sha256(self.raw),'cue_count':4}]
        cues=parse_srt(self.raw)
        drafts=_v33_draft_registry(cues)
        self.rows=[{'video_no':1,'video_id':self.vid,'window_id':'W00001',
                    'cue_first':1,'cue_last':4,
                    'provisional_utterances':len(drafts['W00001']),
                    'source_window_text_sha256':sha256(' '.join(c.text for c in cues).encode('utf-8')),
                    'v37_candidate_list_sha256':json_digest(drafts['W00001'])}]
        self.cohort_hash=json_digest([[x['video_no'],x['window_id'],
               x['source_window_text_sha256'],x['v37_candidate_list_sha256']]
               for x in self.rows])

    def audit(self, **overrides):
        params=dict(archive_bytes=self.archive,
                    expected_archive_sha256=sha256(self.archive),
                    sources=self.sources,independently_pinned_v37_rows=self.rows,
                    expected_v37_cohort_sha256=self.cohort_hash,
                    previous_deep_window_keys=())
        params.update(overrides)
        archive=params.pop('archive_bytes')
        return audit_full_original_risk_intake_v42(archive,**params)

    def test_complete_source_replay_source_window_and_candidate_pins(self):
        r=self.audit()
        self.assertEqual((r['actual_original_cues'],r['actual_original_windows']), (4,1))
        self.assertEqual(r['v33_provisional_utterance_candidates'],self.rows[0]['provisional_utterances'])
        self.assertFalse(r['p0_go'])
        self.assertFalse(r['all_utterances_atomically_split'])

    def test_prior_deep_window_never_reapproved_by_triage(self):
        r=self.audit(previous_deep_window_keys={(1,'W00001')})
        self.assertEqual(r['prior_deep_reviewed_windows'],1)
        self.assertEqual(r['not_yet_deep_reviewed_windows'],0)
        self.assertFalse(r['human_gold_supplied'])
        self.assertFalse(r['independent_precision_recall_measured'])

    def test_wrong_zip_hash_fails(self):
        with self.assertRaisesRegex(InvalidInput,'ARCHIVE_SHA_PIN_MISMATCH'):
            self.audit(expected_archive_sha256='0'*64)

    def test_wrong_srt_hash_fails(self):
        rows=copy.deepcopy(self.sources)
        rows[0]['original_srt_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'SRT_SHA_PIN_DRIFT'):
            self.audit(sources=rows)

    def test_unpinned_v37_cohort_fails(self):
        with self.assertRaisesRegex(InvalidInput,'COHORT_HASH_DRIFT'):
            self.audit(expected_v37_cohort_sha256='0'*64)

    def test_changed_original_window_hash_fails(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['source_window_text_sha256']='0'*64
        self._wrong_pin(rows)

    def test_changed_draft_candidate_digest_fails(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['v37_candidate_list_sha256']='0'*64
        self._wrong_pin(rows)

    def _wrong_pin(self,rows):
        changed=json_digest([[x['video_no'],x['window_id'],
               x['source_window_text_sha256'],x['v37_candidate_list_sha256']]
               for x in rows])
        with self.assertRaisesRegex(InvalidInput,'PIN_MISMATCH'):
            self.audit(independently_pinned_v37_rows=rows,
                       expected_v37_cohort_sha256=changed)

    def test_duplicate_v37_window_fails(self):
        rows=self.rows+self.rows
        h=json_digest([[x['video_no'],x['window_id'],
                        x['source_window_text_sha256'],x['v37_candidate_list_sha256']]
                       for x in rows])
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE'):
            self.audit(independently_pinned_v37_rows=rows,expected_v37_cohort_sha256=h)

    def test_extra_v37_window_fails(self):
        rows=copy.deepcopy(self.rows)
        x=copy.deepcopy(rows[0]);x['window_id']='W00002';x['cue_first']=41;x['cue_last']=80
        rows.append(x)
        h=json_digest([[y['video_no'],y['window_id'],
                        y['source_window_text_sha256'],y['v37_candidate_list_sha256']]
                       for y in rows])
        with self.assertRaisesRegex(InvalidInput,'COHORT'):
            self.audit(independently_pinned_v37_rows=rows,expected_v37_cohort_sha256=h)

    def test_missing_v37_window_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V37_PINS_REQUIRED'):
            self.audit(independently_pinned_v37_rows=[])

    def test_unknown_previous_deep_window_fails(self):
        with self.assertRaisesRegex(InvalidInput,'UNKNOWN_PRIOR_DEEP_REVIEW'):
            self.audit(previous_deep_window_keys={(1,'W00002')})

    def test_duplicate_deep_window_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE_OR_INVALID'):
            self.audit(previous_deep_window_keys=[(1,'W00001'),(1,'W00001')])

    def test_wrong_cue_census_fails(self):
        sources=copy.deepcopy(self.sources)
        sources[0]['cue_count']=5
        with self.assertRaisesRegex(InvalidInput,'CUE_CENSUS_CHANGED'):
            self.audit(sources=sources)

    def test_archive_without_expected_srt_member_fails(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('other-name.srt',self.raw)
        raw=b.getvalue()
        with self.assertRaisesRegex(InvalidInput,'OWNER_SRT_MISSING'):
            self.audit(archive_bytes=raw,expected_archive_sha256=sha256(raw))

    def test_raw_source_utterance_text_does_not_leak_in_receipt(self):
        r=self.audit()
        enc=json.dumps(r,ensure_ascii=False)
        for c in parse_srt(self.raw):
            self.assertNotIn(c.text,enc)
        self.assertFalse(r['raw_owner_srt_or_claim_prose_in_public_receipt'])

    def test_lexical_risk_not_a_finance_truth_label(self):
        r=self.audit()
        p=r['ranked_windows'][0]
        self.assertTrue(p['lexical_priority_score_noncertified']>0)
        self.assertFalse(p['actual_claim_meaning_truth_certified'])
        self.assertFalse(r['lexical_risk_rank_is_independent_semantic_truth'])

    def test_historical_eight_cases_never_auto_closed(self):
        self.assertFalse(self.audit()['historical_eight_audio_issuer_cases_closed'])

    def test_no_independent_gold_claim(self):
        r=self.audit()
        self.assertFalse(r['independent_precision_recall_measured'])
        self.assertFalse(r['current_user_personal_tax_trade_authorized'])


if __name__=='__main__':unittest.main()
