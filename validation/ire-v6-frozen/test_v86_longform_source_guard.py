"""Synthetic-only, no owner subtitles; false GO, source swapping and context mutation."""
import copy,unittest
from dataclasses import dataclass
from v86_longform_source_guard import (EXPECTED_CRITICAL,EXPECTED_PARENT,NO_GO_FIELDS,
 sha_bytes,digest,check_cue_review,check_parent_review,screen_windows,
 validate_screen,safe_false,VIDEO_ID)
@dataclass
class Cue:index:int;text:str

class V86SyntheticSourceGuardTests(unittest.TestCase):
 def setUp(self):
  self.source={'video_no':7,'video_id':VIDEO_ID,'cue_index':12,
   'cue_text_private':'가상 질문은 예시일 뿐입니다.',
   'start_ms':10000,'end_ms':11000,
   'adjacent_cues_private':[{'cue_index':11,'text_private':'앞 문맥'},{'cue_index':12,'text_private':'가상 질문은 예시일 뿐입니다.'},{'cue_index':13,'text_private':'뒤 문맥'}]}
  self.row={**self.source,'cue_text_sha256':sha_bytes(self.source['cue_text_private'].encode()),
   'adjacent_context_sha256':digest(self.source['adjacent_cues_private']),
   'semantic_kind':'QUESTION_AND_HYPOTHESIS','interpretation_private':'합성 질문의 문맥을 확인하여 질문을 사실로 만들지 않습니다.',
   'caution_private':'이것은 가상 재현용 설명이며 독립 정답이나 사실 증명이 아닙니다.',
   'status':'CHAT_CONTEXTUAL_SHADOW_NOT_GOLD',**{f:False for f in NO_GO_FIELDS}}
  self.parent_source={'window_id':'W00001','claim_id':'C00001',
   'cue_indices':[1,2],'source_excerpt_private':'가상 본문 한 줄 | 다음 줄',
   'start_ms':100,'end_ms':300,
   'adjacent_cues_private':[{'cue_index':1,'text_private':'가상 본문 한 줄'},{'cue_index':2,'text_private':'다음 줄'}]}
  self.parent={**self.parent_source,'video_no':7,'video_id':VIDEO_ID,
   'source_sha256':sha_bytes(self.parent_source['source_excerpt_private'].encode()),
   'adjacent_context_sha256':digest(self.parent_source['adjacent_cues_private']),
   'semantic_kind':'QUESTION_NOT_PORTFOLIO_RULE',
   'interpretation_private':'가상 질문이며 개인에게 추천하는 확정 자산배분은 아닙니다.',
   'caution_private':'기초 자료 없이 개인의 거래를 승인할 수 없고 사실보증도 아닙니다.',
   'scope_risk':'PERSONAL_ADVICE','status':'CHAT_CONTEXTUAL_SHADOW_NOT_GOLD',
   **{f:False for f in NO_GO_FIELDS}}

 def test_expected_18_unique(self):self.assertEqual(len(set(EXPECTED_CRITICAL)),18)
 def test_expected_16_unique(self):self.assertEqual(len(set(EXPECTED_PARENT)),16)
 def test_valid_cue_binding(self):self.assertEqual(len(check_cue_review(self.row,self.source,self.row['semantic_kind'])),64)
 def test_valid_parent_binding(self):self.assertEqual(len(check_parent_review(self.parent,self.parent_source,self.parent['semantic_kind'])),64)
 def _bad_cue(self,field,value):
  x=copy.deepcopy(self.row);x[field]=value
  with self.assertRaises(ValueError):check_cue_review(x,self.source,'QUESTION_AND_HYPOTHESIS')
 def _bad_parent(self,field,value):
  x=copy.deepcopy(self.parent);x[field]=value
  with self.assertRaises(ValueError):check_parent_review(x,self.parent_source,'QUESTION_NOT_PORTFOLIO_RULE')
 def test_cue_wrong_video(self):self._bad_cue('video_no',6)
 def test_cue_wrong_id(self):self._bad_cue('cue_index',77)
 def test_cue_prose_swap(self):self._bad_cue('cue_text_private','바뀐 다른 질문')
 def test_cue_sha_tamper(self):self._bad_cue('cue_text_sha256','f'*64)
 def test_cue_start_time(self):self._bad_cue('start_ms',7777)
 def test_cue_neighbor_changed(self):self._bad_cue('adjacent_cues_private',[])
 def test_cue_neighbor_hash_changed(self):self._bad_cue('adjacent_context_sha256','0'*64)
 def test_cue_semantic_type(self):self._bad_cue('semantic_kind','FACT_TRUE')
 def test_cue_not_gold_false_positive(self):self._bad_cue('independent_gold',True)
 def test_cue_no_fact_approval(self):self._bad_cue('fact_approved',True)
 def test_cue_no_personal_approval(self):self._bad_cue('personal_action_approved',True)
 def test_cue_no_v75_membership(self):self._bad_cue('v75_membership_verified',True)
 def test_cue_no_official_merge(self):self._bad_cue('official_parent_merged',True)
 def test_cue_status_cannot_change(self):self._bad_cue('status','FINANCE_APPROVED')
 def test_cue_empty_note(self):self._bad_cue('interpretation_private','')
 def test_cue_empty_caution(self):self._bad_cue('caution_private','')
 def test_parent_wrong_id(self):self._bad_parent('claim_id','C00002')
 def test_parent_wrong_window(self):self._bad_parent('window_id','W00002')
 def test_parent_source_excerpt(self):self._bad_parent('source_excerpt_private','바꿔치기')
 def test_parent_sha(self):self._bad_parent('source_sha256','e'*64)
 def test_parent_time(self):self._bad_parent('end_ms',500)
 def test_parent_cue_range(self):self._bad_parent('cue_indices',[1,3])
 def test_parent_context(self):self._bad_parent('adjacent_cues_private',[])
 def test_parent_context_sha(self):self._bad_parent('adjacent_context_sha256','e'*64)
 def test_parent_semantics(self):self._bad_parent('semantic_kind','TRADING_ADVICE_APPROVED')
 def test_parent_false_gold(self):self._bad_parent('independent_gold',True)
 def test_parent_no_fact_approval(self):self._bad_parent('fact_approved',True)
 def test_parent_no_action_approval(self):self._bad_parent('personal_action_approved',True)
 def test_parent_missing_risk(self):self._bad_parent('scope_risk','')
 def test_parent_short_review(self):self._bad_parent('interpretation_private','짧음')
 def test_parent_short_caution(self):self._bad_parent('caution_private','짧음')

 def _synthetic(self):
  cues=[Cue(i,('연금 수익률 5%가 보장되는 건 아니죠?' if i==1 else f'가상 자막 {i}')) for i in range(1,43)]
  p={'claim_id':'C00001','cue_indices':[1,2],
   'source_text_sha256':sha_bytes(' | '.join(c.text for c in cues[:2]).encode()),'numeric_tokens':1}
  return cues,{'W00001':[p],'W00002':[]}
 def test_screen_deterministic(self):
  c,r=self._synthetic();a=screen_windows(c,r);b=screen_windows(c,r)
  self.assertEqual(a,b);self.assertEqual(len(a),2)
  self.assertEqual(a[0]['draft_parent_count'],1)
  self.assertFalse(a[0]['manual_reviewed_all_parents'])
 def test_screen_handles_risk_as_heuristic(self):
  c,r=self._synthetic();s=screen_windows(c,r)
  self.assertGreater(s[0]['screen_hits']['PENSION_TAX'],0)
  self.assertFalse(s[0]['fact_approved'])
 def test_screen_detects_source_swap(self):
  c,r=self._synthetic();c[0].text='변조'
  with self.assertRaises(ValueError):screen_windows(c,r)
 def test_screen_reject_duplicate_candidate(self):
  c,r=self._synthetic();r['W00001'].append(copy.deepcopy(r['W00001'][0]))
  with self.assertRaises(ValueError):screen_windows(c,r)
 def test_screen_reject_missing_window(self):
  c,r=self._synthetic();r['W00003']=r.pop('W00002')
  with self.assertRaises(ValueError):screen_windows(c,r)
 def test_screen_reject_duplicate_source_indices(self):
  c,r=self._synthetic();r['W00001'][0]['cue_indices']=[1,1]
  with self.assertRaises(ValueError):screen_windows(c,r)
 def test_screen_reject_cross_window(self):
  c,r=self._synthetic();r['W00001'][0]['cue_indices']=[41]
  with self.assertRaises(ValueError):screen_windows(c,r)
 def test_screen_not_full269_certification(self):
  c,r=self._synthetic();s=screen_windows(c,r)
  with self.assertRaises(ValueError):validate_screen(s,c,r)
 def test_parent_no_v75_membership(self):self._bad_parent('v75_membership_verified',True)
 def test_parent_no_official_merge(self):self._bad_parent('official_parent_merged',True)

if __name__=='__main__':unittest.main()