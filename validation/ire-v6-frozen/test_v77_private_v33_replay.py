"""Source-free synthetic regression controls for V77 V33/V39 reconstructed intake.

No private source is embedded in the public tests; never assert semantic accuracy.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
from v77_private_v33_replay import Cue, audit, clock, digest, parse_srt, registry, spans, sha


def synthetic_srt(rows):
    return '\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n{text}'
                      for i,text in enumerate(rows,1)).encode('utf-8')


class V77SourceReplayTests(unittest.TestCase):
    def test_canonical_digest_stable(self):
        self.assertEqual(digest([{'b':2,'a':'한글'}]),sha(b'[{"a":"\xed\x95\x9c\xea\xb8\x80","b":2}]'))

    def test_parser_normalizes_line_wrap(self):
        s=b'1\n00:00:01,000 --> 00:00:02,000\nfirst line\nsecond line'
        cues=parse_srt(s)
        self.assertEqual(len(cues),1)
        self.assertEqual(cues[0].text,'first line second line')

    def test_segment_7_cue_boundary(self):
        raw=synthetic_srt(['반복되는 발화와 어휘입니다']*9)
        cues=parse_srt(raw)
        self.assertEqual([len(x) for x in spans(cues,1,len(cues))],[7,2])
        rows=registry(cues)
        self.assertEqual(len(rows['W00001']),2)

    def test_filler_cue_is_not_atom(self):
        cues=parse_srt(synthetic_srt(['네','매수 조건을 확인해야 한다']))
        rows=registry(cues)
        self.assertEqual(len(rows['W00001']),1)
        self.assertEqual(rows['W00001'][0]['cue_indices'],[2])

    def test_candidate_id_continues_across_windows(self):
        cues=parse_srt(synthetic_srt(['반복되는 발화와 어휘입니다']*42))
        rows=registry(cues)
        self.assertEqual(len(rows['W00001']),6)
        self.assertEqual(len(rows['W00002']),1)
        self.assertEqual(rows['W00002'][0]['claim_id'],'C00007')

    def test_source_excerpt_tamper_changes_fingerprint(self):
        a=registry(parse_srt(synthetic_srt(['조건부로 살 수 있습니다','그런데 예외가 있습니다'])))
        b=registry(parse_srt(synthetic_srt(['무조건 살 수 있습니다','그런데 예외가 있습니다'])))
        self.assertNotEqual(digest(a),digest(b))

    def test_missing_cue_index_rejected(self):
        s=b'1\n00:00:01,000 --> 00:00:02,000\nhello\n\n3\n00:00:03,000 --> 00:00:04,000\nworld'
        with self.assertRaises(ValueError):parse_srt(s)

    def test_backward_clock_rejected(self):
        s=b'1\n00:00:05,000 --> 00:00:06,000\nhello\n\n2\n00:00:04,000 --> 00:00:05,000\nworld'
        with self.assertRaises(ValueError):parse_srt(s)

    def test_invalid_clock_unit_rejected(self):
        with self.assertRaises(ValueError):clock('00:61:00,000')

    def test_bad_archive_sha_rejected_before_interpretation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'owner.zip'
            with zipfile.ZipFile(path,'w') as z:z.writestr('f.srt',synthetic_srt(['test']))
            with self.assertRaisesRegex(ValueError,'OWNER_ZIP_MISMATCH'):audit(path)

    def test_synthetic_has_no_verified_claim_fields(self):
        cues=parse_srt(synthetic_srt(['매우 높은 수익을 보장합니다']))
        result=registry(cues)
        self.assertNotIn('fact_approved',str(result))
        self.assertNotIn('personalized_advice_approved',str(result))


if __name__=='__main__':unittest.main()