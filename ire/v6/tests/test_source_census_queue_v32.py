"""V32 synthetic exact-cue registration and numeric interpretation controls."""
from __future__ import annotations
import copy
import tempfile
import unittest
import zipfile
from pathlib import Path
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.source_census_queue_v32 import (
 make_full_source_review_queue_v32,verify_five_pinned_originals_and_queue_v32,
 audit_contextual_allocation_v32)

def make_long_srt(lines):
 def clock(ms):
  hh, rem = divmod(ms, 3600000)
  mm, rem = divmod(rem, 60000)
  ss, rem = divmod(rem, 1000)
  return f'{hh:02d}:{mm:02d}:{ss:02d},{rem:03d}'
 return ('\n\n'.join(f'{i}\n{clock(i*1000)} --> {clock(i*1000+700)}\n{line}'
                    for i,line in enumerate(lines,1))).encode('utf-8')

class V32QueueAndNumbersTests(unittest.TestCase):
 def setUp(self):
  self.make_srt=make_long_srt
  self.lines=['IRP 조건이 언급됩니다.']*12+['ISA 위험을 비교합니다.']*9
  self.raw=self.make_srt(self.lines)
  self.src_hash=sha256(self.raw)

 def test_full_scope_all_source_cues_registered(self):
  r=make_full_source_review_queue_v32(self.raw,video_id='8Zh1q4Ziv4c',expected_srt_sha256=self.src_hash,window_size=10)
  self.assertEqual(r['original_cue_count'],21)
  self.assertEqual(r['queued_cue_count'],21)
  self.assertEqual(r['window_count'],3)
  self.assertEqual([x['cue_count'] for x in r['windows']],[10,10,1])
  self.assertFalse(r['source_wide_semantic_extraction_complete'])
  self.assertFalse(r['p0_go'])

 def test_all_windows_unreviewed_not_implied_gold(self):
  r=make_full_source_review_queue_v32(self.raw,video_id='8Zh1q4Ziv4c',expected_srt_sha256=self.src_hash,window_size=10)
  self.assertTrue(all(x['status']=='PENDING_CHAT_SEMANTIC_REVIEW' for x in r['windows']))
  self.assertIsNone(r['financial_meaning_atom_count'])
  self.assertEqual(r['reviewed_cue_count'],0)

 def test_source_srt_pin_mismatch_is_rejected(self):
  with self.assertRaisesRegex(InvalidInput,'V32_ORIGINAL_SRT_PIN_MISMATCH'):
   make_full_source_review_queue_v32(self.raw,video_id='8Zh1q4Ziv4c',expected_srt_sha256='0'*64)

 def test_window_size_bool_and_below_min_rejected(self):
  for x in [True,0,9,81]:
   with self.subTest(x=x),self.assertRaisesRegex(InvalidInput,'V32_WINDOW_SIZE_INVALID'):
    make_full_source_review_queue_v32(self.raw,video_id='8Zh1q4Ziv4c',expected_srt_sha256=self.src_hash,window_size=x)

 def test_tampered_source_invalidates_prior_source_sha(self):
  tamper=self.raw.replace(b'IRP',b'ETF',1)
  with self.assertRaisesRegex(InvalidInput,'V32_ORIGINAL_SRT_PIN_MISMATCH'):
   make_full_source_review_queue_v32(tamper,video_id='8Zh1q4Ziv4c',expected_srt_sha256=self.src_hash)

 def test_source_queue_is_deterministic(self):
  kw={'video_id':'8Zh1q4Ziv4c','expected_srt_sha256':self.src_hash,'window_size':10}
  self.assertEqual(make_full_source_review_queue_v32(self.raw,**kw),make_full_source_review_queue_v32(self.raw,**kw))

 def _archive(self):
  folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
  path=Path(folder.name)/'private-synthetic.zip'
  srt1=self.make_srt(['ISA 테스트 원문입니다.']*10)
  srt2=self.make_srt(['IRP 테스트 원문입니다.']*15)
  with zipfile.ZipFile(path,'w') as z:
   z.writestr('1-70/youtube-transcript-8Zh1q4Ziv4c.srt',srt1)
   z.writestr('1-70/youtube-transcript-6VEfKF7BzZU.srt',srt2)
  specs=[{'video_id':'8Zh1q4Ziv4c','member_name':'1-70/youtube-transcript-8Zh1q4Ziv4c.srt','srt_sha256':sha256(srt1),'cue_count':10},
         {'video_id':'6VEfKF7BzZU','member_name':'1-70/youtube-transcript-6VEfKF7BzZU.srt','srt_sha256':sha256(srt2),'cue_count':15}]
  return path,specs

 def test_private_zip_two_orig_census_replayed(self):
  path,specs=self._archive()
  result=verify_five_pinned_originals_and_queue_v32(path,archive_sha256=sha256(path.read_bytes()),sources=specs,window_size=10)
  self.assertEqual(result['original_video_count'],2)
  self.assertEqual(result['original_cues_registered'],25)
  self.assertEqual(result['window_count'],3)
  self.assertFalse(result['original_semantic_atom_recall_verified'])

 def test_wrong_archive_sha_refused(self):
  path,specs=self._archive()
  with self.assertRaisesRegex(InvalidInput,'V28_ORIGINAL_ARCHIVE_BYTES_MISMATCH'):
   verify_five_pinned_originals_and_queue_v32(path,archive_sha256='0'*64,sources=specs)

 def test_wrong_srt_sha_refused(self):
  path,specs=self._archive();specs[0]['srt_sha256']='0'*64
  with self.assertRaisesRegex(InvalidInput,'V28_ORIGINAL_SRT_BYTES_MISMATCH'):
   verify_five_pinned_originals_and_queue_v32(path,archive_sha256=sha256(path.read_bytes()),sources=specs)

 def test_duplicate_video_refused(self):
  path,specs=self._archive();specs=[specs[0],copy.deepcopy(specs[0])]
  with self.assertRaisesRegex(InvalidInput,'V32_DUPLICATE_SOURCE_ID'):
   verify_five_pinned_originals_and_queue_v32(path,archive_sha256=sha256(path.read_bytes()),sources=specs)

 def test_tampered_requested_cue_count_refused(self):
  path,specs=self._archive();specs[0]['cue_count']=11
  with self.assertRaisesRegex(InvalidInput,'V28_ORIGINAL_SRT_CUE_COUNT_MISMATCH'):
   verify_five_pinned_originals_and_queue_v32(path,archive_sha256=sha256(path.read_bytes()),sources=specs)

 def _unit_source(self,override=None):
  lines=['정보를 설명하는 자막입니다.']*181
  block={173:'연금 저축은 세액공제를 위한 계좌입니다.',
         174:'ISA가 있습니다.',175:'각각 준비할 수 있습니다.',
         176:'여기에 돈을 넣는 예시입니다.',
         177:'제가 50만 원 넣을 거면',178:'연금축에 10, ISA 40',
         179:'이런 식으로 얘기하죠. 100',180:'넣을 거면 ISA에 80,',
         181:'연금 저축에 20 이런 식으로 나눕니다.'}
  block.update(override or {})
  for n,txt in block.items(): lines[n-1]=txt
  raw=self.make_srt(lines)
  d=sha256(raw)
  plan={'schema':'IRE_V6_SOURCE_PLAN_V1','video_id':'6VEfKF7BzZU',
        'source_sha256':d,'cue_count':181,
        'scope':{'mode':'PARTIAL','first_cue':173,'last_cue':181},
        'windows':[{'window_id':'W00001','first_cue':173,'last_cue':181,
         'text_sha256':sha256(' '.join(lines[172:181]).encode())}]}
  return verify_source(raw,plan,expected_source_sha256=d,expected_manifest_sha256=json_digest(plan))

 def test_50_10_40_100_80_20_context_with_additive_integrity(self):
  r=audit_contextual_allocation_v32(self._unit_source())
  self.assertEqual(r['examples'][0]['budget_krw'],500000)
  self.assertEqual(r['examples'][1]['budget_krw'],1000000)
  self.assertTrue(r['numeric_addition_valid'])
  self.assertFalse(r['audio_transcript_independently_verified'])
  self.assertFalse(r['p0_go'])

 def test_contextual_unit_missing_is_rejected(self):
  with self.assertRaisesRegex(InvalidInput,'V32_ALLOCATION_NUMERIC_OR_PRODUCT_SOURCE_NOT_GROUNDED'):
   audit_contextual_allocation_v32(self._unit_source({177:'제가 50 넣으면'}))

 def test_missing_allocation_number_rejected(self):
  with self.assertRaisesRegex(InvalidInput,'V32_ALLOCATION_NUMERIC_OR_PRODUCT_SOURCE_NOT_GROUNDED'):
   audit_contextual_allocation_v32(self._unit_source({181:'연금 저축에 소액 나눕니다.'}))

 def test_foreign_video_context_rejected(self):
  src=self._unit_source()
  from dataclasses import replace
  bad=replace(src,video_id='8Zh1q4Ziv4c')
  with self.assertRaisesRegex(InvalidInput,'V32_ALLOCATION_SCOPE_OR_REVIEW_INVALID'):
   audit_contextual_allocation_v32(bad)

if __name__=='__main__': unittest.main()
