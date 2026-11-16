"""Synthetic-only, public V110 regression; no owner's subtitles or annotations."""
from __future__ import annotations
import unittest, copy
from v110_52_parent_atomic_coverage_guard import audit,check_public_receipt,sha,digest,NUM,POLARITY,SCHEMA

PIN='a'*64

def fixture():
    raw=["다만 200을 납입하면","이자 2%로 늘어요","하지만 위험은 남아요","네"]
    rows=[{'video_id':'v','window_id':'W00001','cue_index':i+1,'cue_sha256':sha(t),'text_private':t,'start_ms':(i+1)*100,'end_ms':(i+2)*100} for i,t in enumerate(raw)]
    packet={'owner_private_cues':rows,'source_archive_sha256':PIN,'prediction_disclosed':False,'independent_gold':False}
    p1={'video_id':'v','window_id':'W00001','draft_parent_id':'C01','source_cue_indices':[1,2],
        'source_parent_sha256':sha(raw[0]+' | '+raw[1])}
    p2={'video_id':'v','window_id':'W00001','draft_parent_id':'C02','source_cue_indices':[3],
        'source_parent_sha256':sha(raw[2])}
    old_a={'source_archive_sha256':PIN,'parents':[p1,p2]}
    old_atoms={'source_archive_sha256':PIN,'source_atoms_provisional':[{'video_id':'v','source_cue_indices':[1],
        'source_cues_digest_sha256':sha(rows[0]['cue_sha256'])}]}
    old_b={'source_archive_sha256':PIN,'issues':[]}
    def U(i,role,meaning,conditions='',exc='',reb='',limits='',open_reason=''):
        sub=[rows[x-1] for x in i]
        return {'unit_id':'T'+str(i[0]),'source_cue_indices':i,'source_cues_digest_sha256':sha(''.join(x['cue_sha256'] for x in sub)),
            'role':role,'meaning_private':meaning,'contextual_conditions_private':conditions,
            'spoken_exceptions':exc,'spoken_rebuttal':reb,'reviewer_limits':limits,'open_reason':open_reason,
            'numeric_surface_forms':[n for c in sub for n in NUM.findall(c['text_private'])],
            'source_polarity_surface_forms':[n for c in sub for n in POLARITY.findall(c['text_private'])],
            'approved_financial_fact':False,'independent_gold':False,'personal_advice_approved':False}
    p1n={**p1,'units':[U([1],'CONDITION','입금 조건 제시입니다','입금 200 이라면',exc='다만'),U([2],'HYPOTHESIS','금리 2% 가정입니다')]}
    p2n={**p2,'units':[U([3],'REBUTTAL','위험이 남는다는 반박','',reb='하지만 위험은 남아요')]}
    decomp={'schema':SCHEMA,'source_archive_sha256':PIN,'v109_pass_a_digest_sha256':digest(old_a),
        'v109_28_atoms_digest_sha256':digest(old_atoms),'v109_19_counterexamples_digest_sha256':digest(old_b),
        'parents':[p1n,p2n], 'unassigned_cues':[{'video_id':'v','window_id':'W00001','cue_index':4,'cue_sha256':rows[3]['cue_sha256'],
           'role_private':'짧은 대화의 동의 반응','independent_gold':False,'claim_absence_certified':False}],
        'cross_parent_edges':[{'video_id':'v','source_parent_id':'C01','target_parent_id':'C02','type':'CONTRASTS_WITH',
            'reason_private':'조건에 대비되는 위험은 남아 있음'}],
        'all_financial_atomic_claims_certified':False,'independent_gold':False,'p0_go':False,'personal_advice_approved':False,
        'financial_law_application_certified':False,'new_financial_knowledge_approved':0}
    return {'packet':packet,'old_pass_a':old_a,'old_atoms':old_atoms,'old_counterexamples':old_b,
            'decomposition':decomp,'source_zip_sha':PIN,
            'expected_cues':4,'expected_parents':2,'expected_units':3,'expected_gaps':1}

class V110Tests(unittest.TestCase):
    def test_good_fixture(self):
        r=audit(**fixture());self.assertEqual(r['original_cues'],4);self.assertEqual(r['v110_speech_act_units'],3)
        self.assertEqual(r['v110_source_cues_accounted_including_gaps'],4)
    def test_v109_baseline_omission_reproduced(self):
        r=audit(**fixture());self.assertEqual(r['v109_cues_not_linked_to_atoms'],3)
        self.assertEqual(r['v109_parents_all_cues_in_atoms'],0)
    def test_source_role_counts(self):
        r=audit(**fixture());self.assertEqual(r['source_condition_units'],1);self.assertEqual(r['source_self_rebuttal_units'],1)
    def test_prior_issue_maintained(self):
        f=fixture();x=f['packet']['owner_private_cues'][0]
        issue={'issue_id':'SYN-001','video_id':'v','window_id':'W00001','first_cue':1,'last_cue':1,
               'source_span_sha256':sha(x['cue_sha256']),'linked_v33_parent_ids':['C01']}
        f['old_counterexamples']['issues']=[issue]
        f['decomposition']['v109_19_counterexamples_digest_sha256']=digest(f['old_counterexamples'])
        f['expected_counterexamples']=1
        r=audit(**f);self.assertEqual(r['v109_counterexample_spans_preserved'],1)
    def test_prior_issue_tampered_rejected(self):
        f=fixture();x=f['packet']['owner_private_cues'][0]
        issue={'issue_id':'SYN-001','video_id':'v','window_id':'W00001','first_cue':1,'last_cue':1,
               'source_span_sha256':'0'*64,'linked_v33_parent_ids':['C01']}
        f['old_counterexamples']['issues']=[issue]
        f['decomposition']['v109_19_counterexamples_digest_sha256']=digest(f['old_counterexamples'])
        f['expected_counterexamples']=1
        with self.assertRaises(ValueError):audit(**f)
    def test_no_independent_gold(self):
        r=audit(**fixture());self.assertFalse(r['independent_gold']);self.assertFalse(r['all_financial_atomic_claims_certified'])
        self.assertIsNone(r['certified_recall']);self.assertFalse(r['p0_go'])
    def test_public_receipt_ok(self):
        r=audit(**fixture());self.assertTrue(check_public_receipt(copy.deepcopy(r),r))
    def test_public_receipt_no_fake_gold(self):
        r=audit(**fixture());other=copy.deepcopy(r);other['independent_gold']=True
        with self.assertRaises(ValueError):check_public_receipt(other,r)
    def test_public_receipt_no_private_data(self):
        r=audit(**fixture());other=copy.deepcopy(r);other['private_notes']='secret'
        with self.assertRaises(ValueError):check_public_receipt(other,r)
    def test_wrong_expected_count(self):
        f=fixture();f['expected_units']=4
        with self.assertRaises(ValueError):audit(**f)
    def test_synthetic_source_no_owner_text(self):
        self.assertEqual(fixture()['packet']['owner_private_cues'][0]['text_private'],'다만 200을 납입하면')

MUTATORS={
  'source_pin':lambda f:f.__setitem__('source_zip_sha','b'*64),
  'source_sha_tamper':lambda f:f['packet']['owner_private_cues'][0].__setitem__('text_private','조작'),
  'source_duplicate':lambda f:f['packet']['owner_private_cues'][1].__setitem__('cue_index',1),
  'source_missing':lambda f:f['packet']['owner_private_cues'].pop(),
  'source_window_order':lambda f:f['packet']['owner_private_cues'][2].__setitem__('cue_index',5),
  'source_not_gold':lambda f:f['packet'].__setitem__('independent_gold',True),
  'source_predictions_leaked':lambda f:f['packet'].__setitem__('prediction_disclosed',True),
  'old_parent_drift':lambda f:f['old_pass_a']['parents'][0]['source_cue_indices'].append(3),
  'old_atoms_drift':lambda f:f['old_atoms']['source_atoms_provisional'][0].__setitem__('source_cues_digest_sha256','x'*64),
  'old_counterexample_drift':lambda f:f['old_counterexamples'].__setitem__('issues',[{'fake':True}]),
  'old_pass_a_digest':lambda f:f['decomposition'].__setitem__('v109_pass_a_digest_sha256','x'*64),
  'old_atoms_digest':lambda f:f['decomposition'].__setitem__('v109_28_atoms_digest_sha256','x'*64),
  'old_counterexamples_digest':lambda f:f['decomposition'].__setitem__('v109_19_counterexamples_digest_sha256','x'*64),
  'parent_deleted':lambda f:f['decomposition']['parents'].pop(),
  'parent_duplicate':lambda f:f['decomposition']['parents'].__setitem__(1,copy.deepcopy(f['decomposition']['parents'][0])),
  'parent_sha':lambda f:f['decomposition']['parents'][0].__setitem__('source_parent_sha256','x'*64),
  'parent_crosscue':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('source_cue_indices',[3]),
  'parent_unit_deleted':lambda f:f['decomposition']['parents'][0]['units'].pop(),
  'parent_unit_dup_id':lambda f:f['decomposition']['parents'][0]['units'][1].__setitem__('unit_id','T1'),
  'parent_unit_sha':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('source_cues_digest_sha256','x'*64),
  'parent_unit_exception_dropped':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('spoken_exceptions',''),
  'parent_unit_polarity_dropped':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('source_polarity_surface_forms',[]),
  'parent_unit_number_drift':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('numeric_surface_forms',['10']),
  'parent_unit_invalid_role':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('role','GOLD'),
  'parent_unit_missing_meaning':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('meaning_private',''),
  'parent_unit_condition_dropped':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('contextual_conditions_private',''),
  'parent_unit_rebuttal_dropped':lambda f:f['decomposition']['parents'][1]['units'][0].__setitem__('spoken_rebuttal',''),
  'parent_unit_gold':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('independent_gold',True),
  'parent_unit_approval':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('approved_financial_fact',True),
  'parent_unit_advice':lambda f:f['decomposition']['parents'][0]['units'][0].__setitem__('personal_advice_approved',True),
  'gap_missing':lambda f:f['decomposition']['unassigned_cues'].pop(),
  'gap_wrong_cue':lambda f:f['decomposition']['unassigned_cues'][0].__setitem__('cue_index',1),
  'gap_false_absence':lambda f:f['decomposition']['unassigned_cues'][0].__setitem__('claim_absence_certified',True),
  'edge_cross_parent':lambda f:f['decomposition']['cross_parent_edges'][0].__setitem__('target_parent_id','C999'),
  'edge_same_parent':lambda f:f['decomposition']['cross_parent_edges'][0].__setitem__('target_parent_id','C01'),
  'edge_no_evidence':lambda f:f['decomposition']['cross_parent_edges'][0].__setitem__('reason_private',''),
  'edge_illegal_type':lambda f:f['decomposition']['cross_parent_edges'][0].__setitem__('type','PROVEN_ACCURACY'),
  'fake_go':lambda f:f['decomposition'].__setitem__('p0_go',True),
  'fake_claim_completion':lambda f:f['decomposition'].__setitem__('all_financial_atomic_claims_certified',True),
  'fake_independent_gold':lambda f:f['decomposition'].__setitem__('independent_gold',True),
  'fake_law_certification':lambda f:f['decomposition'].__setitem__('financial_law_application_certified',True),
  'fake_knowledge_merge':lambda f:f['decomposition'].__setitem__('new_financial_knowledge_approved',1),
}

def make_test(name,mutate):
    def test(self):
        f=fixture();mutate(f)
        with self.assertRaises(ValueError):audit(**f)
    test.__name__='test_reject_'+name
    return test
for name,mutate in MUTATORS.items():
    setattr(V110Tests,'test_reject_'+name,make_test(name,mutate))

if __name__=='__main__':unittest.main()