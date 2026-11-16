"""Synthetic-only V112 tests. No user transcript or private annotations here."""
from __future__ import annotations
import copy,json,sys,unittest
from collections import Counter
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import v112_shadow_scope_reconciliation_guard as v


def create_fixture():
 vids=['SYNTH_VIDEO_A','SYNTH_VIDEO_B','SYNTH_VIDEO_C','SYNTH_VIDEO_D']
 lengths=[40,40,39,39];unit_counts=[22,21,21,21]
 lengths_by_video=[]
 for n,u in zip(lengths,unit_counts):
  doubles=n-u; singles=u-doubles
  lengths_by_video.append([2]*doubles+[1]*singles)
 source={video:{i:v.sha(f'SYNTHETIC_{video}_CUE_{i}') for i in range(1,41)} for video in vids}
 parents=[];all_uids=[];index=0
 for vid,atom_lens in zip(vids,lengths_by_video):
  units=[];start=1
  for length in atom_lens:
   idx=list(range(start,start+length));start+=length
   units.append(idx)
  for pidx in range(13):
   global_parent=index+1;index+=1
   # Allocate at least one atomic unit per parent, remainder to earlier parent IDs.
   n=2 if pidx<len(units)-13 else 1
   if pidx==0:pos=0
   else:pos=sum(2 if k<len(units)-13 else 1 for k in range(pidx))
   pu=[]
   for ix,indices in enumerate(units[pos:pos+n],1):
    uid=f'V110_P{global_parent:02d}_U{ix:02d}'
    pu.append({'unit_id':uid,'role':'HYPOTHESIS','source_cue_indices':indices,
      'source_cues_digest_sha256':v.sha(''.join(source[vid][i] for i in indices))})
    all_uids.append(uid)
   parents.append({'video_id':vid,'window_id':'W00020','draft_parent_id':f'C{global_parent:05d}','units':pu})
 assert len(parents)==52 and len(all_uids)==85
 gaps=[{'video_id':vids[i],'window_id':'W00020','cue_index':40,'cue_sha256':source[vids[i]][40],
        'claim_absence_certified':False,'independent_gold':False} for i in (2,3)]
 ledger={'parents':parents,'unassigned_cues':gaps,'cross_parent_edges':[{'synthetic':i} for i in range(25)]}
 sample=[x for x in all_uids if x!='V110_P10_U01'][:21]+['V110_P10_U01']
 expected_statuses=['CLOSED_CONTEXT']*10+['OPEN_AUDIO']*7+['OPEN_VISUAL']*3+['OPEN_ACCOUNT_VISUAL','OPEN_ACCOUNT_SCOPE']
 umap={u['unit_id']:(p,u) for p in parents for u in p['units']}
 docket=[];decisions=[]
 for uid,status in zip(sample,expected_statuses):
  p,u=umap[uid]
  docket.append({'unit_id':uid,'video_id':p['video_id'],'window_id':p['window_id'],
   'draft_parent_id':p['draft_parent_id'],'source_cue_indices':u['source_cue_indices']})
  decisions.append({'unit_id':uid,'status':status,'source_span_sha256':u['source_cues_digest_sha256']})
 v111={'rows':decisions,'prior_private_zip_sha256':v.V110_ZIP_SHA}
 statusmap={row['unit_id']:row for row in decisions}
 rows=[]
 for p in parents:
  for u in p['units']:
   d=statusmap.get(u['unit_id'])
   st='CONTEXT_RESOLVED' if d is not None and d['status']=='CLOSED_CONTEXT' else d['status'] if d is not None else 'NOT_IN_V111_OPEN'
   rows.append({'unit_id':u['unit_id'],'video_id':p['video_id'],'window_id':p['window_id'],
    'draft_parent_id':p['draft_parent_id'],'unit_role':u['role'],'source_cue_indices':u['source_cue_indices'],
    'source_cues_digest_sha256':u['source_cues_digest_sha256'],
    'original_v111_disposition_sha256':v.digest(d) if d else None,
    'shadow_status':st,'v111_context_reconciled':bool(d),
    'source_gap_remains_open':(st in v.PENDING) if d else None,
    'finance_semantic_certified':False,'personal_advice_approved':False,'p0_go':False,'independent_gold':False})
 overlay={'schema':'V112_85_UNIT_NONMUTATING_V111_DISPOSITION_SHADOW_V1',
  'original_owner_source_sha256':v.SOURCE_SHA,'v110_owner_zip_sha256':v.V110_ZIP_SHA,
  'v111_owner_zip_sha256':v.V111_ZIP_SHA,'v110_ledger_frozen_sha256':v.digest(ledger),
  'v110_open22_frozen_sha256':v.digest(docket),'v111_dispositions_frozen_sha256':v.digest(v111),
  'rows':rows,'v110_underlying_ledger_modified':False,'v111_underlying_decisions_modified':False,
  'formal_knowledge_approved_count':0,'independent_gold':False,'p0_go':False,'certified_precision':None,'certified_recall':None}
 cases=[('TAX_EXCLUDED','PENSION',True),('DEFERRED_RETIREMENT','PENSION',False),('TAX_CREDITED_CONTRIBUTION','PENSION',False),('ACCOUNT_EARNINGS','PENSION',False),('PUBLIC_PENSION','PENSION',False),('OTHER_NON_PENSION_INCOME','NON_PENSION',False),('UNKNOWN_SOURCE','UNKNOWN',False)]
 review={'schema':'V112_PRIVATE_PENSION_ACCOUNT_TAX_SCOPE_NO_GOLD_V1','linked_open_unit_id':'V110_P10_U01',
  'status':'OPEN_ACCOUNT_SCOPE','original_v111_status':'OPEN_ACCOUNT_SCOPE',
  'tax_due':None,'personal_threshold_applicable':None,'pension_account_balances_known':None,
  'personal_tax_approved':False,'financial_fact_auto_approved':False,'p0_go':False,'independent_gold':False,
  'speaker_claim_corrected_as_universal':True,'2026_nts_optional_15pct_separate_tax_noted':True,
  'account_withdrawal_order_not_user_selectable_within_one_account':True,
  'required_account_evidence':list(v.REQUIRED_FACT_FIELDS),
  'branch_examples':[{'source_category':k,'receipt_mode':m,'original_proof':pr,'branch':v.account_rule(k,receipt=m,original_proof=pr)['branch'],'tax_amount':None,'threshold_personally_applies':None} for k,m,pr in cases],
  'verifiable_rule_evidence':sorted(v.RULE_EVIDENCE_IDS),
  'official_sources':[{'evidence_id':k,'issuer':issuer,'url':url,'checked_2026_11_14':True,'html_bytes_pinned':False} for k,(issuer,url) in v.EXPECTED_EVIDENCE.items()],
  'reviewer_private_reasoning':'Synthetic reasoning placeholder only. Conditions and tax applicability must remain unknown; no actual taxpayer data was supplied.',
  'remaining_private_limitation':'Synthetic limitation placeholder. Cannot compute any personal tax without full account evidence, withdrawal type, and related history.'}
 return {'v110_zip_bytes':b'SYNTHETIC_V110_ARCHIVE','v111_zip_bytes':b'SYNTHETIC_V111_ARCHIVE',
 'owner_archive_sha':v.SOURCE_SHA,'unit_ledger':ledger,'v110_docket':docket,'v111_dispositions':v111,
 'overlay':overlay,'tax_review':review,'source_cue_sha_by_video':source}

class V112SyntheticTests(unittest.TestCase):
 def setUp(self):
  self.f=create_fixture()
  self.p1=patch.object(v,'V110_ZIP_SHA',v.sha(self.f['v110_zip_bytes']))
  self.p2=patch.object(v,'V111_ZIP_SHA',v.sha(self.f['v111_zip_bytes']))
  self.p1.start();self.p2.start()
  self.addCleanup(self.p2.stop);self.addCleanup(self.p1.stop)
  self.f['overlay']['v110_owner_zip_sha256']=v.V110_ZIP_SHA
  self.f['overlay']['v111_owner_zip_sha256']=v.V111_ZIP_SHA
  self.f['v111_dispositions']['prior_private_zip_sha256']=v.V110_ZIP_SHA
  self.pin()
 def pin(self):
  self.f['overlay']['v110_ledger_frozen_sha256']=v.digest(self.f['unit_ledger'])
  self.f['overlay']['v110_open22_frozen_sha256']=v.digest(self.f['v110_docket'])
  self.f['overlay']['v111_dispositions_frozen_sha256']=v.digest(self.f['v111_dispositions'])
  d={r['unit_id']:r for r in self.f['v111_dispositions']['rows']}
  for row in self.f['overlay']['rows']:
   old=d.get(row['unit_id']);row['original_v111_disposition_sha256']=v.digest(old) if old else None
 def valid(self):return v.audit_shadow(**self.f)
 def rejects(self):
  with self.assertRaises(ValueError):self.valid()
 def test_base_census(self):
  x=self.valid();self.assertEqual((x['parents'],x['units'],x['source_cues_in_parent_units']),(52,85,158))
 def test_open_backlog(self):
  a=self.valid();self.assertEqual((a['context_resolved_units'],a['still_open_units'],a['no_v111_open_decision_units']),(10,12,63))
 def test_public_receipt(self):self.assertTrue(v.verify_public(self.valid(),copy.deepcopy(self.valid())))
 def test_public_receipt_modified(self):
  actual=self.valid();p=copy.deepcopy(actual);p['still_open_units']=11
  with self.assertRaises(ValueError):v.verify_public(p,actual)
 def test_source_modes(self):
  for source in v.REQUIRED_SOURCES:
   with self.subTest(source=source):
    result=v.account_rule(source)
    self.assertFalse(result['eligible_for_finance_approval']);self.assertIsNone(result['tax_amount'])
 def test_unknown_source_stays_unknown(self):self.assertEqual(v.account_rule('UNKNOWN_SOURCE')['branch'],'UNKNOWN_ACCOUNT_SOURCE_HOLD')
 def test_nonpension_unqualified(self):self.assertEqual(v.account_rule('TAX_CREDITED_CONTRIBUTION',receipt='NON_PENSION')['branch'],'NON_PENSION_OR_UNDETERMINED_TAX')
 def test_unknown_receipt_unqualified(self):self.assertEqual(v.account_rule('ACCOUNT_EARNINGS')['branch'],'NON_PENSION_OR_UNDETERMINED_TAX')
 def test_pension_receipt_limited(self):self.assertEqual(v.account_rule('ACCOUNT_EARNINGS',receipt='PENSION')['branch'],'PRIVATE_PENSION_THRESHOLD_CONDITIONAL')
 def test_tax_exclusion_requires_proof(self):self.assertEqual(v.account_rule('TAX_EXCLUDED',original_proof=False)['branch'],'TAX_EXCLUSION_EVIDENCE_MISSING')
 def test_tax_exclusion_with_proof_not_approved(self):self.assertFalse(v.account_rule('TAX_EXCLUDED',original_proof=True)['eligible_for_finance_approval'])
 def test_deferred_retirement(self):self.assertEqual(v.account_rule('DEFERRED_RETIREMENT')['branch'],'DEFERRED_RETIREMENT_SEPARATE_RULE')
 def test_public_pension_not_private_threshold(self):self.assertEqual(v.account_rule('PUBLIC_PENSION')['branch'],'PUBLIC_PENSION_DIFFERENT_RULE')
 def test_income_other(self):self.assertEqual(v.account_rule('OTHER_NON_PENSION_INCOME')['branch'],'OTHER_INCOME_DIFFERENT_RULE')
 def test_invalid_source(self):
  with self.assertRaises(ValueError):v.account_rule('UNKNOWN_FAKE')
 def test_invalid_mode(self):
  with self.assertRaises(ValueError):v.account_rule('ACCOUNT_EARNINGS',receipt='TAX_FREE')


def generate_bad_mutation(name,mutate,repin=False):
 def test(self):
  mutate(self.f)
  if repin:self.pin()
  self.rejects()
 test.__name__='test_reject_'+name
 return test

BAD={
'v110_archive_mutated':lambda f:f.__setitem__('v110_zip_bytes',b'TAMPER_V110_ARCHIVE'),
'v111_archive_mutated':lambda f:f.__setitem__('v111_zip_bytes',b'TAMPER_V111_ARCHIVE'),
'owner_source_drift':lambda f:f.__setitem__('owner_archive_sha','0'*64),
'overlay_origin_drift':lambda f:f['overlay'].__setitem__('original_owner_source_sha256','0'*64),
'v110_parent_deleted':lambda f:f['unit_ledger']['parents'].pop(),
'v110_duplicate_parent_id':lambda f:f['unit_ledger']['parents'][1].__setitem__('draft_parent_id',f['unit_ledger']['parents'][0]['draft_parent_id']),
'v110_unit_deleted':lambda f:f['unit_ledger']['parents'][0]['units'].pop(),
'v110_unit_duplicate_id':lambda f:f['unit_ledger']['parents'][0]['units'][1].__setitem__('unit_id',f['unit_ledger']['parents'][0]['units'][0]['unit_id']),
'v110_edge_deleted':lambda f:f['unit_ledger']['cross_parent_edges'].pop(),
'v110_gap_deleted':lambda f:f['unit_ledger']['unassigned_cues'].pop(),
'v110_gap_sha_tampered':lambda f:f['unit_ledger']['unassigned_cues'][0].__setitem__('cue_sha256','f'*64),
'v110_gap_claim_absence_approved':lambda f:f['unit_ledger']['unassigned_cues'][0].__setitem__('claim_absence_certified',True),
'v111_decision_deleted':lambda f:f['v111_dispositions']['rows'].pop(),
'v111_decision_duplicate':lambda f:f['v111_dispositions']['rows'][1].__setitem__('unit_id',f['v111_dispositions']['rows'][0]['unit_id']),
'v111_status_altered':lambda f:f['v111_dispositions']['rows'][0].__setitem__('status','OPEN_AUDIO'),
'overlay_unit_deleted':lambda f:f['overlay']['rows'].pop(),
'overlay_unit_duplicated':lambda f:f['overlay']['rows'][1].__setitem__('unit_id',f['overlay']['rows'][0]['unit_id']),
'overlay_status_falsely_closed':lambda f:next(row for row in f['overlay']['rows'] if row['shadow_status']=='OPEN_ACCOUNT_SCOPE').__setitem__('shadow_status','CONTEXT_RESOLVED'),
'overlay_unreviewed_falsely_closed':lambda f:next(row for row in f['overlay']['rows'] if row['shadow_status']=='NOT_IN_V111_OPEN').__setitem__('shadow_status','CONTEXT_RESOLVED'),
'overlay_source_sha_wrong':lambda f:f['overlay']['rows'][0].__setitem__('source_cues_digest_sha256','0'*64),
'overlay_parent_mislinked':lambda f:f['overlay']['rows'][0].__setitem__('draft_parent_id','FAKE'),
'overlay_false_personal_advice':lambda f:f['overlay']['rows'][0].__setitem__('personal_advice_approved',True),
'overlay_false_gold':lambda f:f['overlay']['rows'][0].__setitem__('independent_gold',True),
'overlay_original_mutated':lambda f:f['overlay'].__setitem__('v111_underlying_decisions_modified',True),
'overlay_precision_forged':lambda f:f['overlay'].__setitem__('certified_precision',1.0),
'overlay_p0_forged':lambda f:f['overlay'].__setitem__('p0_go',True),
'overlay_false_approval_count':lambda f:f['overlay'].__setitem__('formal_knowledge_approved_count',1),
'original_source_cue_modified':lambda f:f['source_cue_sha_by_video']['SYNTH_VIDEO_A'].__setitem__(1,'0'*64),
'tax_false_personal_amount':lambda f:f['tax_review'].__setitem__('tax_due',150),
'tax_not_open':lambda f:f['tax_review'].__setitem__('status','CLOSED_CONTEXT'),
'tax_false_personal_approval':lambda f:f['tax_review'].__setitem__('personal_tax_approved',True),
'tax_missing_2026_option':lambda f:f['tax_review'].__setitem__('2026_nts_optional_15pct_separate_tax_noted',False),
'tax_missing_withdrawal_order':lambda f:f['tax_review'].__setitem__('account_withdrawal_order_not_user_selectable_within_one_account',False),
'tax_missing_required_account_evidence':lambda f:f['tax_review']['required_account_evidence'].pop(),
'tax_duplicate_required_account_evidence':lambda f:f['tax_review']['required_account_evidence'].append(f['tax_review']['required_account_evidence'][0]),
'tax_source_branch_missing':lambda f:f['tax_review']['branch_examples'].pop(),
'tax_source_branch_duplicate':lambda f:f['tax_review']['branch_examples'][1].__setitem__('source_category',f['tax_review']['branch_examples'][0]['source_category']),
'tax_branch_forged':lambda f:f['tax_review']['branch_examples'][0].__setitem__('branch','TAX_FREE_FOR_ALL'),
'tax_branch_personal_threshold':lambda f:f['tax_review']['branch_examples'][0].__setitem__('threshold_personally_applies',True),
'tax_official_url_spoof':lambda f:f['tax_review']['official_sources'][0].__setitem__('url','https://www.nts.go.kr.evil.example/x'),
'tax_official_source_missing':lambda f:f['tax_review']['official_sources'].pop(),
'tax_evidence_receipt_missing':lambda f:f['tax_review']['verifiable_rule_evidence'].pop(),
'tax_source_false_html_pin':lambda f:f['tax_review']['official_sources'][0].__setitem__('html_bytes_pinned',True),
'tax_reasoning_removed':lambda f:f['tax_review'].__setitem__('reviewer_private_reasoning',''),
}
for name,fn in BAD.items():
 setattr(V112SyntheticTests,'test_reject_'+name,generate_bad_mutation(name,fn,name in {'v110_parent_deleted','v110_duplicate_parent_id','v110_unit_deleted','v110_unit_duplicate_id','v110_edge_deleted','v110_gap_deleted','v110_gap_sha_tampered','v110_gap_claim_absence_approved','v111_decision_deleted','v111_decision_duplicate','v111_status_altered'}))

if __name__=='__main__':unittest.main(verbosity=1)