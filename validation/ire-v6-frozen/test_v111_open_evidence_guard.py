"""Public synthetic-only adversarial regression; never owner transcript or financial gold."""
from __future__ import annotations
import copy,unittest
from dataclasses import dataclass
from unittest.mock import patch
import v111_open_evidence_guard as v

@dataclass
class Cue:
 index:int
 start_ms:int
 end_ms:int
 text:str


def fixture():
 original=b'test source zip bytes';old=b'archived-older-private-zip' * 2500
 original_sha=v.sha(original)
 vids={f'vid{k}':[Cue(i,i*1000,i*1000+500,f'Synthetic cue {i} in video {k}') for i in range(1,53)] for k in range(1,5)}
 parents=[];prior=[];rows=[]
 states=['CLOSED_CONTEXT']*10+['OPEN_AUDIO']*7+['OPEN_VISUAL']*3+['OPEN_ACCOUNT_VISUAL']+['OPEN_ACCOUNT_SCOPE']
 for i in range(1,53):
  cue=vids['vid1'][i-1];uid=f'unit{i:03d}';src_sha=v.sha(v.sha(cue.text));cid=f'C{i:05d}'
  parents.append({'video_id':'vid1','draft_parent_id':cid,'units':[{'unit_id':uid,'source_cue_indices':[i], 'source_cues_digest_sha256':src_sha}]})
  if i>22:continue
  prior.append({'video_id':'vid1','window_id':'W00001','draft_parent_id':cid,'unit_id':uid,'source_cue_indices':[i],
    'role':'FACT_CANDIDATE','source_cues_digest_sha256':src_sha})
  st=states[i-1];dep=('SOURCE_CONTEXT' if st=='CLOSED_CONTEXT' else 'AUDIO_ORIGINAL' if st=='OPEN_AUDIO' else 'ACCOUNT_ORIGIN_AND_RECEIPT_TYPE' if st=='OPEN_ACCOUNT_SCOPE' else 'SCREEN_OR_ACCOUNT_LEDGER')
  row=dict(prior[-1]);row.update({'status':st,'context_first_cue':i,'context_last_cue':i,
   'context_sha256':v.digest([[i,v.sha(cue.text)]]),
   'contextual_interpretation_private':'Meaning is based on selected contiguous original speech source, not fact certification.',
   'remaining_limit_private':'This example contains no independent human gold or approved financial application.',
   'contextual_meaning_resolved':st=='CLOSED_CONTEXT', 'further_audio_required_for_exact_transcript':st=='OPEN_AUDIO',
   'remaining_visual_or_account_data_required':st in ('OPEN_VISUAL','OPEN_ACCOUNT_VISUAL','OPEN_ACCOUNT_SCOPE'),
   'next_evidence_dependency':dep,'external_evidence_ids':[],
   'official_finance_rule_personalized':False,'financial_rule_approved':False,
   'personal_advice_approved':False,'all_52_financial_claims_certified':False,'independent_gold':False,'p0_go':False})
  rows.append(row)
 evidence=[{'evidence_id':key,'issuer':key,'url':'https://example.org/verified-source','current_personal_finance_application_certified':False,'webpage_exact_byte_hash_saved':False}
           for key in sorted(v.ALLOWED_EXTERNAL)]
 overlay={'schema':'V111_PRIVATE_22_EVIDENCE_DISPOSITIONS_NO_GOLD_V1','source_archive_sha256':original_sha,'prior_private_zip_sha256':v.sha(old),
  'prior_open_docket_sha256':v.digest(prior),'rows':rows,'existing_v110_52_parent_85_units_modified':False,
  'finance_fact_approved':False,'independent_gold':False,'p0_go':False}
 return {'source_zip_bytes':original,'previous_zip_bytes':old,'previous_docket':prior,'previous_units':{'parents':parents},
   'cues_full_by_video':vids,'decisions':overlay,'evidence':evidence}

class V111EvidenceTests(unittest.TestCase):
 def setUp(self):self.data=fixture()
 def check(self, data=None):
  d=data or self.data
  with patch.object(v,'SOURCE_ZIP_SHA',v.sha(d['source_zip_bytes'])):
   return v.audit(**d)
 def must_reject(self,mutator):
  d=copy.deepcopy(self.data);mutator(d)
  with self.assertRaises(ValueError):
   self.check(d)
 def test_valid_synthetic(self):
  r=self.check();self.assertEqual((r['context_resolved_units'],r['still_open_units']), (10,12))
 def test_evidence_groups(self):
  r=self.check();self.assertEqual((r['open_audio'],r['open_visual_or_screen'],r['open_account_scope']),(7,4,1))
 def test_no_gold_score(self):
  r=self.check();self.assertIsNone(r['certified_precision']);self.assertFalse(r['human_independent_gold'])
 def test_public_receipt(self):
  r=self.check();self.assertTrue(v.compare_public_receipt(r,copy.deepcopy(r)))
 def test_public_changed_sha(self):
  r=self.check();r2=copy.deepcopy(r);r2['source_linked_disposition_digest_sha256']='0'*64
  with self.assertRaises(ValueError):v.compare_public_receipt(r,r2)
 def test_missing_source_archive(self):self.must_reject(lambda d:d.update(source_zip_bytes=b''))
 def test_wrong_previous_archive_sha(self):self.must_reject(lambda d:d['decisions'].__setitem__('prior_private_zip_sha256','0'*64))
 def test_wrong_prior_docket_hash(self):self.must_reject(lambda d:d['decisions'].__setitem__('prior_open_docket_sha256','0'*64))
 def test_missing_docket_record(self):self.must_reject(lambda d:d['previous_docket'].pop())
 def test_missing_disposition(self):self.must_reject(lambda d:d['decisions']['rows'].pop())
 def test_duplicate_disposition(self):self.must_reject(lambda d:d['decisions']['rows'].__setitem__(1,d['decisions']['rows'][0]))
 def test_changed_parent_id(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('draft_parent_id','C99999'))
 def test_changed_unit_id(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('unit_id','unit999'))
 def test_changed_role(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('role','APPROVED'))
 def test_changed_indices(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('source_cue_indices',[99]))
 def test_wrong_cue_hash(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('source_cues_digest_sha256','f'*64))
 def test_source_text_tampered(self):self.must_reject(lambda d:setattr(d['cues_full_by_video']['vid1'][0],'text','Changed source'))
 def test_original_order_broken(self):self.must_reject(lambda d:setattr(d['cues_full_by_video']['vid1'][0],'index',2))
 def test_context_sha_changed(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('context_sha256','f'*64))
 def test_context_beyond_cue(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('context_first_cue',2))
 def test_context_too_broad(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('context_last_cue',52))
 def test_missing_unit(self):self.must_reject(lambda d:d['previous_units']['parents'][0].__setitem__('units',[]))
 def test_missing_parent(self):self.must_reject(lambda d:d['previous_units']['parents'].pop())
 def test_status_unknown(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('status','CERTIFIED'))
 def test_false_closed_meaning(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('contextual_meaning_resolved',False))
 def test_false_audio_closed(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('further_audio_required_for_exact_transcript',True))
 def test_undisclosed_audio(self):self.must_reject(lambda d:d['decisions']['rows'][10].__setitem__('further_audio_required_for_exact_transcript',False))
 def test_audio_wrong_dependency(self):self.must_reject(lambda d:d['decisions']['rows'][10].__setitem__('next_evidence_dependency','SOURCE_CONTEXT'))
 def test_visual_wrong_dependency(self):self.must_reject(lambda d:d['decisions']['rows'][17].__setitem__('next_evidence_dependency','AUDIO_ORIGINAL'))
 def test_account_wrong_dependency(self):self.must_reject(lambda d:d['decisions']['rows'][21].__setitem__('next_evidence_dependency','SCREEN_OR_ACCOUNT_LEDGER'))
 def test_open_falsely_complete(self):self.must_reject(lambda d:d['decisions']['rows'][11].__setitem__('contextual_meaning_resolved',True))
 def test_open_false_no_screen(self):self.must_reject(lambda d:d['decisions']['rows'][17].__setitem__('remaining_visual_or_account_data_required',False))
 def test_no_interpretation(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('contextual_interpretation_private','short'))
 def test_no_limit(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('remaining_limit_private','short'))
 def test_external_unknown(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('external_evidence_ids',['FAKE']))
 def test_external_duplicate(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('external_evidence_ids',['BOOK_CATALOG','BOOK_CATALOG']))
 def test_missing_evidence(self):self.must_reject(lambda d:d['evidence'].pop())
 def test_false_snapshot(self):self.must_reject(lambda d:d['evidence'][0].__setitem__('webpage_exact_byte_hash_saved',True))
 def test_false_law_approval(self):self.must_reject(lambda d:d['evidence'][0].__setitem__('current_personal_finance_application_certified',True))
 def test_false_parent_approval(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('all_52_financial_claims_certified',True))
 def test_false_personal_advice(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('personal_advice_approved',True))
 def test_false_gold(self):self.must_reject(lambda d:d['decisions']['rows'][0].__setitem__('independent_gold',True))
 def test_false_p0_go(self):self.must_reject(lambda d:d['decisions'].__setitem__('p0_go',True))
 def test_false_global_approval(self):self.must_reject(lambda d:d['decisions'].__setitem__('finance_fact_approved',True))
 def test_changed_previous_archive(self):self.must_reject(lambda d:d.update(previous_zip_bytes=b'other'*13000))
 def test_wrong_open_census(self):
  def mutate(d):
   row=d['decisions']['rows'][0];row.update(status='OPEN_AUDIO',next_evidence_dependency='AUDIO_ORIGINAL',contextual_meaning_resolved=False,further_audio_required_for_exact_transcript=True)
  self.must_reject(mutate)
 def test_claim_all_52_modified(self):self.must_reject(lambda d:d['decisions'].__setitem__('existing_v110_52_parent_85_units_modified',True))

if __name__=='__main__':unittest.main()