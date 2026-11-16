"""Public synthetic-only V109 regression suite; NO owner's SRT, no independent gold."""
import copy, json, unittest
from v109_chat_native_eval_gate import audit_chat_native, check_public_receipt, sha, digest, frozen_lexical_kinds, SOURCE_SHA

NAMES=[('synthetic-v0','W00020',761,13,True),('synthetic-v1','W00008',281,13,False),
       ('synthetic-v2','W00006',201,16,True),('synthetic-v3','W00065',2561,10,False)]

def fixture():
 cues=[]; lockwins=[]; parent_rows=[]; first_rows=[]; gaps=[]
 for v,w,fi,n,has_gap in NAMES:
  here=[]
  for i in range(fi,fi+40):
   t=f'Original-style synthetic ISA 연금 if 조건 투자 단어{i}. Do not infer truth.'
   here.append({'video_id':v,'window_id':w,'cue_index':i,'start_ms':i*1000,'end_ms':i*1000+500,'text_private':t,'cue_sha256':sha(t)})
  cues.extend(here)
  lockwins.append({'video_id':v,'window_id':w,'first_cue':fi,'last_cue':fi+39,
     'source_window_sha256':sha(' '.join(c['text_private'] for c in here))})
  avail=here[:-1] if has_gap else here
  for j in range(n):
   part=avail[(j*len(avail))//n:((j+1)*len(avail))//n]
   ix=[x['cue_index'] for x in part];p_sha=sha(' | '.join(x['text_private'] for x in part))
   p={'video_id':v,'window_id':w,'draft_parent_id':f'SYN{j:03}',
      'source_cue_indices':ix,'source_parent_sha256':p_sha}
   parent_rows.append(p)
   first_rows.append({**p,'stance':'HYPOTHESIS','speaker_meaning_private':'This is a synthetic draft parent meaning only.',
     'scope_and_risk_private':'Cannot assume source-specific truth without evidence.',
     'official_fact_approved':False,'independent_gold':False,'personal_advice_approved':False,
     'chat_pass':'A_FIRST_READING_NOT_GOLD'})
  if has_gap:
   x=here[-1]
   gaps.append({'video_id':v,'window_id':w,'cue_index':x['cue_index'],'cue_sha256':x['cue_sha256'],
     'role_private':'Synthetic parent-gap speech act OPEN, cannot certify absence.',
     'claim_absence_certified':False,'independent_gold':False})
 packetsha=digest([[r['video_id'],r['cue_index'],r['cue_sha256']] for r in cues])
 packet={'schema':'V105_EXTERNAL_BLIND_GOLD_NOT_CREATED_V1','source_archive_sha256':SOURCE_SHA,
    'owner_private_cues':cues,'prediction_disclosed':False,'independent_gold':False,
    'packet_sha256':packetsha}
 lock={'schema':'V105_UNSEEN_OWNER_SOURCE_PRE_REVIEW_LOCK_V1','source_zip_sha256':SOURCE_SHA,
       'cue_count':160,'selected':lockwins}
 pred=[]
 for c in cues:
  kinds=frozen_lexical_kinds(c['text_private'])
  pred.append({'video_id':c['video_id'],'window_id':c['window_id'],'cue_index':c['cue_index'],
     'cue_sha256':c['cue_sha256'],'lexical_kinds':kinds,'lexical_any':bool(kinds),'not_financial_accuracy_certified':True})
 fsha=digest(pred)
 forecast={'forecast':pred,'forecast_digest_sha256':fsha,'source_archive_sha256':SOURCE_SHA,
           'independent_gold':False,'p0_go':False}
 pre={'schema':'V109_PRE_INTERPRETATION_CHAT_NATIVE_LOCK_V1','source_archive_sha256':SOURCE_SHA,
      'source_packet_sha256':packetsha,'lexical_forecast_sha256':fsha,'source_cues':160,
      'lexical_any_cues':sum(x['lexical_any'] for x in pred),
      'lexical_none_cues':sum(not x['lexical_any'] for x in pred),
      'independent_gold':False,'certified_precision':None,'p0_go':False}
 pa={'schema':'V109_CHAT_FIRST_READING_52_V33_PARENTS_NOT_GOLD_V1','source_archive_sha256':SOURCE_SHA,
      'parents':first_rows,'unassigned_cues':gaps,'independent_gold':False,'precision':None,'recall':None,'p0_go':False}
 pab=(json.dumps(pa,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 official={'NTS_PENSION_1500_OPTION':{'issuer':'국세청','url':'https://www.nts.go.kr/synthetic','current_law_full_scope_certified':False},
      'NTS_PENSION_WITHHOLDING_2026':{'issuer':'국세청','url':'https://www.nts.go.kr/synthetic','current_law_full_scope_certified':False},
      'KRX_ETF_RISK':{'issuer':'한국거래소','url':'https://www.krx.co.kr/synthetic','current_law_full_scope_certified':False},
      'SK_HYNIX_HISTORY':{'issuer':'SK hynix','url':'https://www.skhynix.com/synthetic','current_law_full_scope_certified':False}}
 bycue={(r['video_id'],r['cue_index']):r for r in cues}
 issues=[]
 for j,p in enumerate(first_rows[:19],1):
  v=p['video_id'];i=p['source_cue_indices'][0]
  issues.append({'issue_id':f'SYNISS{j:03d}','video_id':v,'window_id':p['window_id'],
    'first_cue':i,'last_cue':i,'source_span_sha256':sha(bycue[(v,i)]['cue_sha256']),
    'linked_v33_parent_ids':[p['draft_parent_id']],'risk_level_provisional':'HIGH' if j<=6 else 'MEDIUM',
    'issue_kind':'SYNTHETIC_SCOPE','reviewer_counterexample_private':'Synthetic counterexample within the original source context, not gold.',
    'action_provisional':'RESTRICT_UNIVERSALIZATION', 'official_evidence_id':None,
    'lexical_prelock_direct_cue_inside_span':True,
    'same_chat_independent_gold':False,'certified_actual_error':False,'fact_approved':False,'p0_go':False})
 stats={'issue_spans':19,'issue_spans_lexical_any':19,'issue_spans_no_lexical_alert':0,
        'linked_affected_parents':19,'high_risk_provisional_spans':6}
 pb={'schema':'V109_CHAT_COUNTEREXAMPLE_REVIEW_NOT_GOLD_V1','source_archive_sha256':SOURCE_SHA,
     'pass_a_sha256':sha(pab),'frozen_forecast_digest_sha256':fsha,
     'issues':issues,'official_evidence':official,'stats':stats,'independent_gold':False,
     'p0_go':False,'independent_human_reviews':0,'formal_finance_knowledge_approvals':0,
     'certified_precision':None,'certified_recall':None,'certified_high_risk_recall':None}
 atoms=[]
 for j,p in enumerate(first_rows[:28],1):
  v=p['video_id'];ix=p['source_cue_indices'][:1]
  atoms.append({'atom_id':f'SYNATOM{j:03}','video_id':v,'window_id':p['window_id'],
    'source_cue_indices':ix,'source_cues_digest_sha256':sha(''.join(bycue[(v,i)]['cue_sha256'] for i in ix)),
    'stance_provisional':'HYPOTHESIS','speaker_atomic_meaning_private':'Synthetic atom proposition evidence bound.',
    'preserved_conditions_private':'Not real verified financial advice or gold.',
    'official_evidence_id':None,'source_semantic_truth_certified':False,'independent_gold':False,
    'personal_advice_approved':False,'p0_go':False})
 at={'schema':'V109_INTERNAL_CROSS_CUE_ATOMS_NOT_GOLD_V1','source_archive_sha256':SOURCE_SHA,
    'source_atoms_provisional':atoms,'all_52_draft_parents_completely_atomized':False,
    'independent_gold':False,'p0_go':False,'certified_precision':None,'certified_recall':None}
 return dict(lock=lock,packet=packet,forecast=forecast,prelock=pre,pass_a=pa,pass_a_bytes=pab,
             pass_b=pb,atomization=at,expected_parent_rows=parent_rows,
             actual_owner_zip_sha=SOURCE_SHA,expected_packet_sha=packetsha)

class TestV109Synthetic(unittest.TestCase):
 def test_complete_pipeline(self):
  a=audit_chat_native(**fixture())
  self.assertEqual((a['source_cues_read'],a['v33_draft_parent_meaning_annotations'],a['unassigned_cues_flagged_open'],a['internal_counterexample_spans'],a['provisional_cross_cue_atomic_parts']),(160,52,2,19,28))
  self.assertIsNone(a['certified_recall'])
  self.assertTrue(a['v105_external_unseen_cohort_repurposed_in_chat'])
  self.assertFalse(a['can_reuse_v105_as_future_unseen_independent_gold'])
 def test_receipt_valid(self):
  r=audit_chat_native(**fixture());self.assertTrue(check_public_receipt(r,r))
 def test_lexical_negative(self):
  self.assertEqual(frozen_lexical_kinds('일반적인 인생 이야기'),[])
 def test_lexical_positive(self):
  self.assertIn('LEXICAL_FINANCE',frozen_lexical_kinds('연금계좌 매수'))
 def test_no_public_precision_score(self):
  r=audit_chat_native(**fixture());bad=copy.deepcopy(r);bad['certified_precision']=1.0
  with self.assertRaises(ValueError):check_public_receipt(bad,r)
 def test_no_public_fake_go(self):
  r=audit_chat_native(**fixture());bad=copy.deepcopy(r);bad['p0_go']=True
  with self.assertRaises(ValueError):check_public_receipt(bad,r)
 def test_no_public_additional_private_prose(self):
  r=audit_chat_native(**fixture());bad=copy.deepcopy(r);bad['private_owner_text']='Original statement'
  with self.assertRaises(ValueError):check_public_receipt(bad,r)

# Each synthetic adversary must be rejected, even under python -O.
MUTATIONS={
 'owner_archive_drift':lambda d:d.update(actual_owner_zip_sha='f'*64),
 'lock_source_drift':lambda d:d['lock'].update(source_zip_sha256='a'*64),
 'source_packet_digest_drift':lambda d:d['packet'].update(packet_sha256='a'*64),
 'missing_source_cue':lambda d:d['packet']['owner_private_cues'].pop(),
 'duplicate_source_cue':lambda d:d['packet']['owner_private_cues'].__setitem__(1,copy.deepcopy(d['packet']['owner_private_cues'][0])),
 'original_cue_text_tamper':lambda d:d['packet']['owner_private_cues'][0].update(text_private='tampered'),
 'original_cue_sha_tamper':lambda d:d['packet']['owner_private_cues'][0].update(cue_sha256='a'*64),
 'original_cue_time_reversed':lambda d:d['packet']['owner_private_cues'][0].update(end_ms=-1),
 'source_window_hash_tamper':lambda d:d['lock']['selected'][0].update(source_window_sha256='a'*64),
 'source_window_missing':lambda d:d['lock']['selected'].pop(),
 'forecast_missing_cue':lambda d:d['forecast']['forecast'].pop(),
 'forecast_duplicate_cue':lambda d:d['forecast']['forecast'].__setitem__(1,copy.deepcopy(d['forecast']['forecast'][0])),
 'forecast_label_tamper':lambda d:d['forecast']['forecast'][0].update(lexical_kinds=[]),
 'forecast_wrong_sha':lambda d:d['forecast']['forecast'][0].update(cue_sha256='f'*64),
 'forecast_frozen_digest_tamper':lambda d:d['prelock'].update(lexical_forecast_sha256='a'*64),
 'forecast_fake_certified':lambda d:d['forecast'].update(independent_gold=True),
 'prelock_false_precision':lambda d:d['prelock'].update(certified_precision=0.99),
 'pass_a_missing_parent':lambda d:d['pass_a']['parents'].pop(),
 'pass_a_duplicate_parent':lambda d:d['pass_a']['parents'].__setitem__(1,copy.deepcopy(d['pass_a']['parents'][0])),
 'pass_a_fake_fact':lambda d:d['pass_a']['parents'][0].update(official_fact_approved=True),
 'pass_a_fake_independent':lambda d:d['pass_a'].update(independent_gold=True),
 'pass_a_wrong_stance':lambda d:d['pass_a']['parents'][0].update(stance='CERTIFIED_TRUTH'),
 'pass_a_parent_source_drift':lambda d:d['pass_a']['parents'][0].update(source_parent_sha256='f'*64),
 'pass_a_parent_index_drift':lambda d:d['pass_a']['parents'][0].update(source_cue_indices=[-1]),
 'pass_a_missing_gap':lambda d:d['pass_a']['unassigned_cues'].pop(),
 'pass_a_gap_fake_absence':lambda d:d['pass_a']['unassigned_cues'][0].update(claim_absence_certified=True),
 'pass_b_parent_sha_drift':lambda d:d['pass_b'].update(pass_a_sha256='a'*64),
 'pass_b_frozen_sha_drift':lambda d:d['pass_b'].update(frozen_forecast_digest_sha256='a'*64),
 'pass_b_missing_issue':lambda d:d['pass_b']['issues'].pop(),
 'pass_b_issue_duplicate_id':lambda d:d['pass_b']['issues'][1].update(issue_id=d['pass_b']['issues'][0]['issue_id']),
 'pass_b_span_sha_tamper':lambda d:d['pass_b']['issues'][0].update(source_span_sha256='a'*64),
 'pass_b_wrong_parent':lambda d:d['pass_b']['issues'][0].update(linked_v33_parent_ids=['SYN999']),
 'pass_b_lexical_mismatch':lambda d:d['pass_b']['issues'][0].update(lexical_prelock_direct_cue_inside_span=False),
 'pass_b_wrong_official_ref':lambda d:d['pass_b']['issues'][0].update(official_evidence_id='UNKNOWN'),
 'pass_b_fake_gold':lambda d:d['pass_b'].update(independent_gold=True),
 'pass_b_fake_true_error':lambda d:d['pass_b']['issues'][0].update(certified_actual_error=True),
 'pass_b_fake_recall':lambda d:d['pass_b'].update(certified_recall=0.9),
 'pass_b_fake_human':lambda d:d['pass_b'].update(independent_human_reviews=2),
 'pass_b_forged_source':lambda d:d['pass_b']['official_evidence']['KRX_ETF_RISK'].update(url='https://example.org/'),
 'pass_b_forged_legal_cert':lambda d:d['pass_b']['official_evidence']['KRX_ETF_RISK'].update(current_law_full_scope_certified=True),
 'pass_b_wrong_census':lambda d:d['pass_b']['stats'].update(linked_affected_parents=99),
 'atom_false_all_complete':lambda d:d['atomization'].update(all_52_draft_parents_completely_atomized=True),
 'atom_false_gold':lambda d:d['atomization'].update(independent_gold=True),
 'atom_false_fact':lambda d:d['atomization']['source_atoms_provisional'][0].update(source_semantic_truth_certified=True),
 'atom_unknown_cue':lambda d:d['atomization']['source_atoms_provisional'][0].update(source_cue_indices=[-2]),
 'atom_wrong_source_hash':lambda d:d['atomization']['source_atoms_provisional'][0].update(source_cues_digest_sha256='a'*64),
 'atom_duplicate_id':lambda d:d['atomization']['source_atoms_provisional'][1].update(atom_id=d['atomization']['source_atoms_provisional'][0]['atom_id']),
 'atom_fake_personal_advice':lambda d:d['atomization']['source_atoms_provisional'][0].update(personal_advice_approved=True),
 'atom_unsupported_official':lambda d:d['atomization']['source_atoms_provisional'][0].update(official_evidence_id='fake'),
 'atom_wrong_stance':lambda d:d['atomization']['source_atoms_provisional'][0].update(stance_provisional='CERTIFIED'),
}
for name,mutate in MUTATIONS.items():
 def make_test(m):
  def run(self):
   data=fixture();m(data)
   with self.assertRaises(ValueError):audit_chat_native(**data)
  return run
 setattr(TestV109Synthetic,'test_reject_'+name,make_test(mutate))
if __name__=='__main__':unittest.main()