"""Synthetic-only V223 tests. No owner ETF transcript or private reviewer file in CI."""
from __future__ import annotations
import copy
import json
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from test_v222_postfilter_source_sidecars import synthetic_sidecars
from test_v221_e2_source_first_semantic_anchor_guard import make_fixture
from v223_e2_semantic_convergence_engine import (
  run_e2_convergence,require_certified_e2_for_approval,
  inspect_prior_relations,load_pinned_documents,prepare_chatgpt_e3_semantic_review_packet,
)

def encode(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8')

def fake():
  base=synthetic_sidecars();raw=base['source']
  source,_=make_original_plan(raw,base['native']['video_id'],
       expected_source_sha256=sha256(raw),window_size=2)
  after=copy.deepcopy(base['native']);before=copy.deepcopy(after)
  before['atoms'][0]['kind']='OPINION'
  fin_after=copy.deepcopy(base['finance']);fin_before=copy.deepcopy(fin_after)
  fin_before['atoms'][0]['kind']='OPINION'
  fin_before['atoms'][0]['risk_tags']=[]
  fin_before['atoms'][0]['risk_review_status']='SOURCE_ANCHORED_BUT_NOT_INDEPENDENT_GOLD'
  fin_before['risk_tag_types']=[]
  fin_before['risk_tagged_atom_count']=0
  fin_after['atoms'][0]['risk_tags']=['EMPIRICAL_BEHAVIOR_GENERALIZATION_UNVERIFIED']
  fin_after['risk_tag_types']=['EMPIRICAL_BEHAVIOR_GENERALIZATION_UNVERIFIED']
  fin_after['risk_tagged_atom_count']=1
  first_cue=after['atoms'][0]['source_refs'][0]['cue_index']
  src=copy.deepcopy(make_fixture()['source_docket'])
  mismatch={
    'coarse_kind_mismatch_count':1,'confirmed_new_kind_errors':0,
    'not_a_blind_gold':True,
    'rows':[{'claim_id':'C00001','native_kind':'OPINION',
      'source_primary':[{'cue_index':first_cue,'quote':source.cues[first_cue-1].text,
                         'sha256':sha256(source.cues[first_cue-1].text.encode())}],
      'source_unit_ids':['SRC221-002']}]
  }
  graph={'schema':'IRE_V218_E2_PRIVATE_CROSS_ATOM_REVIEW_BRIDGE_V1',
   'source_sha256':sha256(raw),'total_original_relations':0,
   'cross_atom_edges_reviewed':0,'intra_atom_context_reviewed':0,
   'visual_quarantines_reviewed':0,'independent_gold_available':False,
   'e2_final_pass':False,'rows':[]}
  review={'schema':'IRE_V223_E2_SOURCE_CLAIM_DUAL_AXIS_HOST_REVIEW_V1',
   'source_sha256':sha256(raw),'source_claims_reviewed':1,
   'discourse_kind_disagreements_reexamined':1,
   'source_roles_resolved_from_coarse_span':0,'native_kind_corrections':1,
   'remaining_coarse_conflicts':0,'source_review_has_seen_prior_engine':True,
   'independent_gold_supplied':False,'speaker_audio_available':False,
   'original_video_screen_available':False,'financial_truth_approved':0,
   'e2_final_pass':False,'e3_e4_e5_authorized':False,'knowledge_published':0,
   'rows':[{'claim_id':'C00001','original_legacy_kind':'OPINION',
    'reviewed_legacy_kind':'FACT',
    'textual_discourse_role':'EMPIRICAL_BEHAVIORAL_CLAIM',
    'epistemic_scope':'EDUCATIONAL_SOURCE_ASSERTION',
    'textual_stance_candidate':'ASSERTED_TEXT_ONLY',
    'original_native_stance':'UNRESOLVED','original_native_speaker':'UNKNOWN',
    'source_primary_cues':[first_cue],
    'source_primary_quote_sha256':[sha256(source.cues[first_cue-1].text.encode())],
    'source_primary_exact_quote':[source.cues[first_cue-1].text],
    'source_unit_ids_for_primary':['SRC221-002'],
    'source_kind_mismatch_resolution':'LEGACY_KIND_CORRECTED',
    'review_explanation':'예시 원문은 개인 취향이 아닌 확인되지 않은 경험적 사실 주장을 포함한다.',
    'source_support_status':'SOURCE_CONTENT_NOT_FINANCIAL_TRUTH_WITH_REVIEW_RISK',
    'source_risk_tags':['EMPIRICAL_BEHAVIOR_GENERALIZATION_UNVERIFIED'],
    'speaker_audio_verified':False,'financial_truth_verified':False,
    'independent_gold_verified':False,'atom_e2_approved':False}]
  }
  change={'claim_id':'C00001','before_kind':'OPINION','after_kind':'FACT',
    'reason':'원문이 호감의 선호라는 주관적 표현이 아니라 서술 형태로 쓰인 근거 미확정 주장이다.',
    'cue_index':first_cue,'cue_quote':source.cues[first_cue-1].text,
    'cue_quote_sha256':sha256(source.cues[first_cue-1].text.encode()),
    'original_sound_evidence_verified':False,'financial_truth_approved':False}
  patch={'source_sha256':sha256(raw),'original_atom_count':1,
    'corrected_atom_count':1,'changed_count':1,'changes':[change],
    'preserved_claims_and_context':True,'financial_truth_approved':False,
    'independent_gold_verified':False,'e2_final_pass':False}
  docs={'source':raw,'before_native':before,'after_native':after,
    'source_units':src,'mismatch':mismatch,'review':review,'patch':patch,
    'before_finance':fin_before,'after_finance':fin_after,
    'before_census':copy.deepcopy(base['census']),
    'after_census':copy.deepcopy(base['census']),
    'relation_graph':graph}
  return docs

def prepare(x,*,repair=True):
  if repair:
    x['before_finance']['native_exchange_sha256']=sha256(encode(x['before_native']))
    x['after_finance']['native_exchange_sha256']=sha256(encode(x['after_native']))
    x['before_census']['native_exchange_sha256']=sha256(encode(x['before_native']))
    x['after_census']['native_exchange_sha256']=sha256(encode(x['after_native']))
    rv=x['review'];rv['previous_native_sha256']=sha256(encode(x['before_native']))
    rv['reviewed_native_sha256']=sha256(encode(x['after_native']))
    rv['source_first_review_sha256']=sha256(encode(x['source_units']))
    rv['previous_coarse_mismatch_sha256']=sha256(encode(x['mismatch']))
    rv['financial_risk_sha256']=sha256(encode(x['after_finance']))
    rv['source_cue_census_sha256']=sha256(encode(x['after_census']))
    pt=x['patch'];pt['before_native_sha256']=sha256(encode(x['before_native']))
    pt['after_native_sha256']=sha256(encode(x['after_native']))
    pt['previous_kind_mismatch_sha256']=sha256(encode(x['mismatch']))
    pt['review_sha256']=sha256(encode(rv))
  b={k:(v if k=='source' else encode(v)) for k,v in x.items()}
  h={k:sha256(v) for k,v in b.items()}
  return b,h

class TestV223SemanticConvergence(unittest.TestCase):
  def setUp(self):self.x=fake()
  def run_case(self,*,repair=True):
    b,h=prepare(self.x,repair=repair)
    return run_e2_convergence(b,h,window_size=2)
  def test_01_valid_claim_level_workflow_is_executable(self):
    r=self.run_case();self.assertEqual(r['source_claim_level_roles_reviewed'],1)
    self.assertEqual(r['real_native_kind_corrections'],1)
    self.assertEqual(r['actual_financial_risk_tagged_atoms'],1)
    self.assertFalse(r['e2_final_semantic_accuracy_pass'])
  def test_02_deterministic_same_real_digest(self):self.assertEqual(self.run_case(),self.run_case())
  def test_03_final_release_cannot_be_self_certified(self):
    with self.assertRaisesRegex(InvalidInput,'INDEPENDENT_GOLD_AND_E3_E4_NOT_VERIFIED'):
      require_certified_e2_for_approval(self.run_case())
  def test_04_origin_sha_tamper_blocks(self):
    b,h=prepare(self.x);b['source']+=b' '
    with self.assertRaisesRegex(InvalidInput,'BYTE_PIN_SOURCE'):run_e2_convergence(b,h,window_size=2)
  def test_05_omitted_required_input_blocks(self):
    b,h=prepare(self.x);b.pop('review')
    with self.assertRaisesRegex(InvalidInput,'INPUT_CONTRACT'):run_e2_convergence(b,h,window_size=2)
  def test_06_unsigned_wrong_json_blocks(self):
    b,h=prepare(self.x);b['review']=b'{' ;h['review']=sha256(b['review'])
    with self.assertRaisesRegex(InvalidInput,'INVALID_JSON_REVIEW'):run_e2_convergence(b,h,window_size=2)
  def test_07_review_quote_not_original(self):
    self.x['review']['rows'][0]['source_primary_exact_quote']=['별도의 허위 진술입니다.']
    with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ROLE'):self.run_case()
  def test_08_cue_hash_not_original(self):
    self.x['review']['rows'][0]['source_primary_quote_sha256']=['f'*64]
    with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ROLE'):self.run_case()
  def test_09_native_unreviewed_proposition_mutation_rejected(self):
    self.x['after_native']['atoms'][0]['proposition']='ETF는 원금이 보장됩니다.'
    with self.assertRaises(InvalidInput):self.run_case()
  def test_10_unreviewed_speaker_promotion_rejected(self):
    self.x['after_native']['atoms'][0]['speaker']='NARRATOR'
    with self.assertRaises(InvalidInput):self.run_case()
  def test_11_review_fake_gold_blocks(self):
    self.x['review']['independent_gold_supplied']=True
    with self.assertRaisesRegex(InvalidInput,'REVIEW_FALSE_GOLD'):self.run_case()
  def test_12_claim_fake_financial_approval_blocks(self):
    self.x['review']['rows'][0]['atom_e2_approved']=True
    with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ROLE'):self.run_case()
  def test_13_same_review_cannot_forget_kind_correction(self):
    self.x['review']['rows'][0]['source_kind_mismatch_resolution']='COMPOUND_SPAN_ROLE_DIFFERENCE'
    with self.assertRaisesRegex(InvalidInput,'MISMATCH_NOT_ADJUDICATED'):self.run_case()
  def test_14_fake_multi_act_resolution_without_kind_change_blocks(self):
    self.x['patch']['changes']=[];self.x['patch']['changed_count']=0
    with self.assertRaises(InvalidInput):self.run_case()
  def test_15_risk_tags_not_downgraded(self):
    self.x['after_finance']['atoms'][0]['risk_tags']=[]
    with self.assertRaises(InvalidInput):self.run_case()
  def test_16_finance_empirical_risk_not_marked_approved(self):
    self.x['after_finance']['atoms'][0]['financial_truth_certified']=True
    with self.assertRaises(InvalidInput):self.run_case()
  def test_17_media_flag_mutation_prevents_cue_contract(self):
    self.x['after_census']['rows'][2]['original_audio_or_screen_review_required']=False
    with self.assertRaisesRegex(InvalidInput,'CUE_CLASS_DRIFT'):self.run_case()
  def test_18_new_census_old_native_sha_fails(self):
    b,h=prepare(self.x);raw=json.loads(b['after_census']);raw['native_exchange_sha256']='f'*64
    b['after_census']=encode(raw);h['after_census']=sha256(b['after_census'])
    with self.assertRaises(InvalidInput):run_e2_convergence(b,h,window_size=2)
  def test_19_missing_source_review_unit_blocks(self):
    self.x['source_units']['claims'][1]['source_refs']=[]
    with self.assertRaisesRegex(InvalidInput,'SOURCE_UNIT_RANGE'):self.run_case()
  def test_20_mismatch_still_open_blocks(self):
    self.x['review']['remaining_coarse_conflicts']=1
    with self.assertRaisesRegex(InvalidInput,'REVIEW_FALSE_GOLD'):self.run_case()
  def test_21_original_native_mutation_with_same_count_blocks(self):
    self.x['before_native']['atoms'][0]['context_cue_indices']=[1]
    with self.assertRaises(InvalidInput):self.run_case()
  def test_22_prior_relation_foreign_atom_ref_blocks(self):
    r=self.x['relation_graph'];r['rows']=[{'relation_id':'r1','source_cue':1,
      'target_cue':2,'source_atom_id':'C99999','target_atom_id':'C00001'}]
    r['total_original_relations']=r['cross_atom_edges_reviewed']=1
    with self.assertRaisesRegex(InvalidInput,'GRAPH_DANGLING_CLAIM'):self.run_case()
  def test_23_relation_coverage_declared_but_empty_blocks(self):
    self.x['relation_graph']['cross_atom_edges_reviewed']=1
    with self.assertRaisesRegex(InvalidInput,'GRAPH_RELATION_CENSUS_DRIFT'):self.run_case()
  def test_24_forged_gold_flag_in_finance_blocks(self):
    self.x['after_finance']['external_independent_gold']=True
    with self.assertRaisesRegex(InvalidInput,'FINANCE_CENSUS_OR_FALSE_GOLD'):self.run_case()
  def test_25_claim_disappears_from_native_blocks(self):
    self.x['after_native']['atoms']=[]
    with self.assertRaises(InvalidInput):self.run_case()
  def test_26_role_not_recognized_blocks(self):
    self.x['review']['rows'][0]['textual_discourse_role']='UNREVIEWED_MAGIC'
    with self.assertRaisesRegex(InvalidInput,'CLAIM_SOURCE_ROLE'):self.run_case()
  def test_27_speaker_audio_claims_are_not_assumed(self):
    self.x['review']['speaker_audio_available']=True
    with self.assertRaisesRegex(InvalidInput,'REVIEW_FALSE_GOLD'):self.run_case()
  def test_28_hypothetical_scope_deceptively_changed(self):
    self.x['after_native']['atoms'][0]['kind']='HYPOTHETICAL'
    self.x['after_finance']['atoms'][0]['kind']='HYPOTHETICAL'
    self.x['review']['rows'][0]['reviewed_legacy_kind']='HYPOTHETICAL'
    self.x['patch']['changes'][0]['after_kind']='HYPOTHETICAL'
    with self.assertRaisesRegex(InvalidInput,'HYPOTHETICAL_SCOPE_LOST'):self.run_case()
  def test_29_true_positive_without_gold_still_is_not_accuracy_score(self):
    r=self.run_case();self.assertFalse(r['precision_recall_real_video_measured'])
    self.assertFalse(r['independent_blind_gold_certified'])
  def test_30_census_all_4_cues_in_original(self):
    self.assertEqual(sum(self.run_case()['source_cue_classes'].values()),4)
  def test_31_original_e3_review_intake_has_exact_claim_count(self):
    b,h=prepare(self.x)
    receipt=run_e2_convergence(b,h,window_size=2)
    packet=prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
    self.assertEqual(packet['source_claim_tasks'],1)
    self.assertTrue(packet['chatgpt_e3_semantic_review_can_start_while_e2_gold_hold'])
    self.assertFalse(packet['e3_final_approved'])
  def test_32_preview_never_forged_e2_pass(self):
    b,h=prepare(self.x);receipt=run_e2_convergence(b,h,window_size=2)
    receipt['e2_final_semantic_accuracy_pass']=True
    with self.assertRaisesRegex(InvalidInput,'CHAT_REVIEW_PREVIEW_REQUIRES_ORIGINAL_REPLAY'):
      prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
  def test_33_private_packet_never_auto_finance_certifies(self):
    b,h=prepare(self.x);receipt=run_e2_convergence(b,h,window_size=2)
    p=prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
    self.assertFalse(p['task_rows'][0]['financial_fact_approved'])
    self.assertFalse(p['source_audio_video_verified'])
  def test_34_private_packet_carries_exact_original_quote(self):
    b,h=prepare(self.x);receipt=run_e2_convergence(b,h,window_size=2)
    p=prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
    self.assertEqual(p['task_rows'][0]['source_context'][0]['quote'],
                     '자, 이제 설명을 시작합니다.')
  def test_35_private_packet_modified_source_fails_closed(self):
    b,h=prepare(self.x);receipt=run_e2_convergence(b,h,window_size=2)
    b['source']+=b' '
    with self.assertRaises(InvalidInput):
      prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
  def test_36_global_original_media_holds_not_dropped_from_e3_packet(self):
    g=self.x['relation_graph']
    g['rows']=[{'relation_id':'s1','source_cue':2,'target_cue':3,
       'source_atom_id':None,'target_atom_id':None,
       'relation_type':'VISUAL_EVIDENCE_OPEN',
       'review_state':'QUARANTINE_VISUAL_UNVERIFIED',
       'is_external_gold':False,'speaker_audio_verified':False,
       'video_frame_verified':False,'financial_fact_approved':False,
       'final_semantic_approval':False,'knowledge_publication_authorized':False}]
    g['total_original_relations']=g['visual_quarantines_reviewed']=1
    b,h=prepare(self.x);receipt=run_e2_convergence(b,h,window_size=2)
    p=prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
    self.assertEqual(len(p['globally_unassigned_original_media_quarantines']),1)
    self.assertEqual(p['globally_unassigned_original_media_quarantines'][0]['target_cue'],3)
  def test_37_same_atom_discourse_deps_arrive_in_chat_review(self):
    g=self.x['relation_graph']
    g['rows']=[{'relation_id':'s2','source_cue':2,'target_cue':2,
       'source_atom_id':'C00001','target_atom_id':'C00001',
       'relation_type':'DEFINITION_SCOPE','review_state':'INTRA_ATOM_UNAPPROVED',
       'is_external_gold':False,'speaker_audio_verified':False,
       'video_frame_verified':False,'financial_fact_approved':False,
       'final_semantic_approval':False,'knowledge_publication_authorized':False}]
    g['total_original_relations']=g['intra_atom_context_reviewed']=1
    b,h=prepare(self.x);receipt=run_e2_convergence(b,h,window_size=2)
    p=prepare_chatgpt_e3_semantic_review_packet(b,h,receipt,window_size=2)
    self.assertEqual(len(p['task_rows'][0]['inter_atom_discourse_dependencies']),1)
  def test_38_media_not_silently_marked_verified(self):
    g=self.x['relation_graph']
    g['rows']=[{'relation_id':'s3','source_cue':2,'target_cue':3,
       'source_atom_id':None,'target_atom_id':None,
       'relation_type':'VISUAL_EVIDENCE_OPEN','review_state':'QUARANTINE_VISUAL_UNVERIFIED',
       'is_external_gold':False,'speaker_audio_verified':False,
       'video_frame_verified':True,'financial_fact_approved':False,
       'final_semantic_approval':False,'knowledge_publication_authorized':False}]
    g['total_original_relations']=g['visual_quarantines_reviewed']=1
    with self.assertRaisesRegex(InvalidInput,'GRAPH_FALSE_APPROVAL'):self.run_case()

if __name__=='__main__':unittest.main()