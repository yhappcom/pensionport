import copy, unittest
from v108_internal_two_pass_guard import validate_two_pass,sha,digest,SRC_SHA

class V108HybridTwoPassSyntheticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lock={'schema':'V108_INTERNAL_NONINDEPENDENT_TWO_PASS_SCOPE_LOCK_V1','source_zip_sha256':SRC_SHA,'source_window_count':4,'source_cues':160,'v105_external_private_packets_accessed':False,'labeling_not_started_at_lock':True,'independent_gold':False,'p0_go':False,'selected':[]}
  cls.cues=[];cls.parents=[];cls.gaps=[];cls.first=[];cls.revisions=[]
  for widx,(vid,nparents,missing) in enumerate([('v1',17,[38,39]),('v2',12,[]),('v3',17,[37,38,39]),('v4',17,[38,39])],1):
   wid=f'W{widx:05d}';first=(widx-1)*40+1
   text_byidx={i:f'Original-style synthetic cue {vid} {i} with financial conditions' for i in range(first,first+40)}
   for i,t in text_byidx.items():cls.cues.append({'video_id':vid,'window_id':wid,'cue_index':i,'start_ms':i*100,'end_ms':i*100+50,'text_private':t,'cue_sha256':sha(t)})
   cls.lock['selected'].append({'video_id':vid,'window_id':wid,'first_cue':first,'last_cue':first+39,'source_window_sha256':sha(' '.join(text_byidx.values())),'draft_parents':nparents})
   valid=[i for i in text_byidx if i-first not in missing]
   groups=[[i] for i in valid[:nparents-1]]+[valid[nparents-1:]]
   for ids in groups:
    cid=f'C{len(cls.parents)+1:05d}'
    parent={'video_id':vid,'window_id':wid,'claim_id':cid,'cue_indices':ids,'source_text_sha256':sha(' | '.join(text_byidx[i] for i in ids))}
    cls.parents.append(parent)
    cls.first.append({**parent,'stance':'HYPOTHESIS','meaning_private':'Synthetic example assumption explained','scope_limit_private':'Not a financial fact certified by any human reviewer','independent_gold':False,'fact_approved':False})
   for i in text_byidx:
    if i-first in missing:cls.gaps.append({'video_id':vid,'window_id':wid,'cue_index':i,'cue_sha256':sha(text_byidx[i]),'discourse_note_private':'No source-backed standalone claim in synthetic example'})
  for a in cls.first[:18]:cls.revisions.append({'video_id':a['video_id'],'window_id':a['window_id'],'claim_id':a['claim_id'],'pass_a_record_sha256':digest(a),'after_stance':'SOURCE_AUDIO_OPEN','adversarial_reason_private':'Synthetic revision identifies unresolved context and original audio limits','independent_reviewer':False,'independent_gold':False,'certified_error':False})
  cls.blind={'source_zip_sha256':SRC_SHA,'cue_count':160,'selected':[{'video_id':f'external-v{i}','window_id':'W00100'} for i in range(4)]}
 def evaluate(self,**overrides):
  d={'lock':copy.deepcopy(self.lock),'blind_scope':copy.deepcopy(self.blind),'cues':copy.deepcopy(self.cues),'parents':copy.deepcopy(self.parents),'first':copy.deepcopy(self.first),'revisions':copy.deepcopy(self.revisions),'gaps':copy.deepcopy(self.gaps),'owner_source_sha':SRC_SHA,'forbidden_prior_windows':set()}
  d.update(overrides);return validate_two_pass(**d)
 def rejects(self,alter):
  d={'lock':copy.deepcopy(self.lock),'blind_scope':copy.deepcopy(self.blind),'cues':copy.deepcopy(self.cues),'parents':copy.deepcopy(self.parents),'first':copy.deepcopy(self.first),'revisions':copy.deepcopy(self.revisions),'gaps':copy.deepcopy(self.gaps),'owner_source_sha':SRC_SHA,'forbidden_prior_windows':set()}
  alter(d)
  with self.assertRaises(ValueError):validate_two_pass(**d)
 def test_success(self):
  r=self.evaluate();self.assertEqual((r['source_cues'],r['draft_parent_candidates'],r['original_cues_without_parent'],r['pass_b_self_revision_candidates']),(160,63,7,18));self.assertFalse(r['p0_go'])
 def test_certification_unavailable(self):
  r=self.evaluate();self.assertIsNone(r['certified_precision']);self.assertFalse(r['independent_gold']);self.assertEqual(r['blind_external_reviewer_submissions_received'],0)
 def test_wrong_owner_archive(self):self.rejects(lambda x:x.update(owner_source_sha='0'*64))
 def test_fake_gold_lock(self):self.rejects(lambda x:x['lock'].update(independent_gold=True))
 def test_fake_v105_access(self):self.rejects(lambda x:x['lock'].update(v105_external_private_packets_accessed=True))
 def test_prior_window_overlap(self):self.rejects(lambda x:x.update(forbidden_prior_windows={('v1','W00001')}))
 def test_blind_window_overlap(self):self.rejects(lambda x:x['blind_scope']['selected'][0].update(video_id='v1',window_id='W00001'))
 def test_source_missing(self):self.rejects(lambda x:x['cues'].pop())
 def test_source_repeated(self):self.rejects(lambda x:x['cues'].__setitem__(0,x['cues'][1]))
 def test_source_text_tamper(self):self.rejects(lambda x:x['cues'][0].update(text_private='spoof'))
 def test_source_hash_tamper(self):self.rejects(lambda x:x['cues'][0].update(cue_sha256='f'*64))
 def test_source_time_invalid(self):self.rejects(lambda x:x['cues'][0].update(start_ms=1000,end_ms=200))
 def test_window_sha_tamper(self):self.rejects(lambda x:x['lock']['selected'][0].update(source_window_sha256='a'*64))
 def test_parent_missing(self):self.rejects(lambda x:x['parents'].pop())
 def test_parent_duplicate(self):self.rejects(lambda x:x['parents'].__setitem__(0,x['parents'][1]))
 def test_parent_overlap(self):self.rejects(lambda x:x['parents'][0].update(cue_indices=x['parents'][1]['cue_indices']))
 def test_parent_sha_tamper(self):self.rejects(lambda x:x['parents'][0].update(source_text_sha256='0'*64))
 def test_gap_missing(self):self.rejects(lambda x:x['gaps'].pop())
 def test_gap_fake_sha(self):self.rejects(lambda x:x['gaps'][0].update(cue_sha256='0'*64))
 def test_gap_unverified_note(self):self.rejects(lambda x:x['gaps'][0].update(discourse_note_private='bad'))
 def test_first_missing(self):self.rejects(lambda x:x['first'].pop())
 def test_first_fake_gold(self):self.rejects(lambda x:x['first'][0].update(independent_gold=True))
 def test_first_no_reason(self):self.rejects(lambda x:x['first'][0].update(meaning_private='x'))
 def test_first_fabricated_source(self):self.rejects(lambda x:x['first'][0].update(source_text_sha256='0'*64))
 def test_first_illegal_stance(self):self.rejects(lambda x:x['first'][0].update(stance='GUARANTEED_RETURN'))
 def test_revisions_missing(self):self.rejects(lambda x:x['revisions'].pop())
 def test_revisions_duplicate(self):self.rejects(lambda x:x['revisions'].__setitem__(0,x['revisions'][1]))
 def test_revisions_fake_independent(self):self.rejects(lambda x:x['revisions'][0].update(independent_reviewer=True))
 def test_revisions_false_error(self):self.rejects(lambda x:x['revisions'][0].update(certified_error=True))
 def test_revisions_no_change(self):self.rejects(lambda x:x['revisions'][0].update(after_stance='HYPOTHESIS'))
 def test_revisions_first_hash_tamper(self):self.rejects(lambda x:x['revisions'][0].update(pass_a_record_sha256='a'*64))
 def test_revisions_short_note(self):self.rejects(lambda x:x['revisions'][0].update(adversarial_reason_private='short'))
 def test_blind_scope_wrong_sha(self):self.rejects(lambda x:x['blind_scope'].update(source_zip_sha256='a'*64))
 def test_duplicate_window_selection(self):self.rejects(lambda x:x['lock']['selected'].__setitem__(1,x['lock']['selected'][0]))
 def test_window_index_conflict(self):self.rejects(lambda x:x['cues'][0].update(cue_index=4))
if __name__=='__main__':unittest.main()