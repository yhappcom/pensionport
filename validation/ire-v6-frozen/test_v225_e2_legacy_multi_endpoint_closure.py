"""V225 code-only synthetic 25+ adversarial tests, without private ETF originals."""
from __future__ import annotations
import copy,json,unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from v225_e2_legacy_multi_endpoint_closure import audit_v225_relation_closure

D=lambda obj:(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8')


def fake():
    words=['가상 ETF를 소개하는 화면입니다.','ETF 시장가격의 조건을 설명합니다.',
           '이 조건은 앞에서 언급했습니다.','이제는 화면을 보아야 합니다.']
    raw=('\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n{w}' for i,w in enumerate(words,1))+'\n').encode()
    source,_=make_original_plan(raw,'Synth123456',expected_source_sha256=sha256(raw),window_size=2)
    def q(i):return source.cues[i-1].text
    def sd(i):return sha256(q(i).encode('utf8'))
    atoms=[]
    for i in range(1,4):
        atoms.append({'claim_id':f'C{i:05d}','owner_window_id':'W00001' if i<=2 else 'W00002',
            'proposition':'원문 구간의 ETF에 관한 미승인 서술',
            'kind':'FACT','stance':'UNRESOLVED','speaker':'UNKNOWN',
            'source_refs':[{'cue_index':i,'quote':q(i)}],
            'context_cue_indices':[i],'condition_cue_indices':[],
            'exception_cue_indices':[],'numeric_references':[],'as_of':None})
    native={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':'Synth123456',
       'source_sha256':sha256(raw),'manifest_sha256':source.manifest_sha256,'atoms':atoms,
       'cue_dispositions':[{'cue_index':i,'cue_text_sha256':sd(i),
       'disposition':'CANDIDATES' if i<=3 else 'UNRESOLVED',
       'claim_ids':[f'C{i:05d}'] if i<=3 else [],'numeric_tokens':[],
       'note':'미승인 원문 근거로만 보존합니다.'} for i in range(1,5)]}
    v217={'source_sha256':sha256(raw),'relation_rows':[
      {'relation_id':'SYN-R001','source_cue':1,'target_cue':2,'relation_type':'CONDITION',
       'source_native_ids':['C00001','C00003'],'target_native_ids':['C00002']},
      {'relation_id':'SYN-R002','source_cue':2,'target_cue':4,'relation_type':'VISUAL_EVIDENCE_OPEN',
       'source_native_ids':['C00002'],'target_native_ids':[]}]}
    v218={'source_sha256':sha256(raw),'rows':[
      {'relation_id':'SYN-R001','source_cue':1,'target_cue':2,'relation_type':'CONDITION',
       'source_atom_id':'C00001','target_atom_id':'C00002','review_state':'LINKED_UNAPPROVED'},
      {'relation_id':'SYN-R002','source_cue':2,'target_cue':4,'relation_type':'VISUAL_EVIDENCE_OPEN',
       'source_atom_id':None,'target_atom_id':None,'review_state':'QUARANTINE_VISUAL_UNVERIFIED'}]}
    rs=[]
    for h,v in zip(v217['relation_rows'],v218['rows']):
        cs,ct=h['source_native_ids'],h['target_native_ids']
        sel_s=[v['source_atom_id']] if v['source_atom_id'] else []
        sel_t=[v['target_atom_id']] if v['target_atom_id'] else []
        extra_s=sorted(set(cs)-set(sel_s));extra_t=sorted(set(ct)-set(sel_t))
        er=[{'position':side,'claim_id':cid,
             'status':('MEDIA_DEPENDENCY_UNVERIFIED' if h['relation_id']=='SYN-R002' else
                       'TEXT_RELATION_CANDIDATE_NOT_INDEPENDENT_GOLD'),
             'source_first_reason':'원문에 인용된 미승인 후보에 관한 해석 근거를 표시하며 별도 독립 정답이 필요합니다.',
             'independent_gold_verified':False,'financial_fact_approved':False}
             for side,items in (('source',extra_s),('target',extra_t)) for cid in items]
        rs.append({'relation_id':h['relation_id'],'relation_type':h['relation_type'],
          'source_cue':h['source_cue'],'target_cue':h['target_cue'],
          'source_quote':q(h['source_cue']),'target_quote':q(h['target_cue']),
          'source_quote_sha256':sd(h['source_cue']),'target_quote_sha256':sd(h['target_cue']),
          'historical_review_state':v['review_state'],
          'candidate_source_atom_ids':cs,'candidate_target_atom_ids':ct,
          'v218_selected_source_atom_ids':sel_s,'v218_selected_target_atom_ids':sel_t,
          'extra_source_atom_ids':extra_s,'extra_target_atom_ids':extra_t,
          'extra_endpoint_reviews':er,'any_semantic_financial_approval':False,
          'relation_is_independent_gold':False,'original_audio_or_video_verified':False})
    graph={'schema':'IRE_V225_E2_FULL_CANDIDATE_RELATION_CLOSURE_V1',
       'source_sha256':sha256(raw),'native_sha256':sha256(D(native)),
       'v217_original_relation_sha256':sha256(D(v217)),
       'v218_selected_relation_review_sha256':sha256(D(v218)),
       'original_relation_count':2,'reviewed_v218_selected_relation_count':2,
       'historical_candidate_endpoints_preserved':True,'relation_rows_with_extra_endpoints':2,
       'extra_endpoint_occurrences_retained':2,'source_quote_byte_hash_verified':True,
       'independent_gold_certified':False,'financial_facts_approved':False,'e2_final_pass':False,'rows':rs}
    old_packet={'source_sha256':sha256(raw),'native_sha256':sha256(D(native)),
        'preserved_inter_atom_and_intra_atom_relations':1,
        'globally_unassigned_original_media_quarantines':[{'relation_id':'SYN-R002',
          'financial_facts_approved':False}],
        'e3_final_approved':False,'e4_approved':False,'e5_published':False,
        'task_rows':[{'claim_id':a['claim_id'],'proposition':a['proposition'],
        'inter_atom_discourse_dependencies':[],'financial_fact_approved':False,
        'e3_final_approved':False} for a in atoms]}
    packet=copy.deepcopy(old_packet)
    packet['v225_full_relation_rows_sha256']=sha256(D(graph))
    packet['v225_full_relation_count']=2
    packet['v225_full_legacy_candidate_endpoints_preserved']=True
    packet['v225_independent_gold_certified']=False
    packet['v225_e3_final_approved']=False
    packet['task_rows'][0]['v225_relation_candidate_ids']=['SYN-R001']
    packet['task_rows'][1]['v225_relation_candidate_ids']=['SYN-R001','SYN-R002']
    packet['task_rows'][2]['v225_relation_candidate_ids']=['SYN-R001']
    official={'schema':'IRE_V225_OFFICIAL_CONTEXT_PRIORITY_CONCEPT_MAP_V1',
      'source_sha256':sha256(raw),'native_sha256':sha256(D(native)),
      'official_original_response_bytes_certified':False,
      'legal_effective_version_approved':False,'per_claim_financial_approval':False,
      'independent_gold_certified':False,'rule_time_conflict_requires_live_version_check':True,
      'time_conflict_note':'공식 KRX 오래된 페이지에 옛 규정 기준이 남아 있어 금융위원회의 2026년 변경 기준과 별도 시점 조정 검토가 필요합니다.',
      'rows_reviewed':1,
      'rows':[{'claim_id':'C00001','claim_text':atoms[0]['proposition'],
          'status':'MATERIAL_LIMITATION_REQUIRED','reason':'원문에서 확인한 제약은 별도의 공식 근거와 함께 추가 확인되어야 한다.',
          'official_reference_urls':['https://www.krx.co.kr/contents/OPN/01/01030203/OPN01030203T1.jsp'],
          'source_audio_verified':False,'official_primary_regulation_bytes_verified':False,
          'financial_fact_approved':False,'e3_final_approved':False}]}
    packet['v225_official_concept_refs_sha256']=sha256(D(official))
    return {'srt':raw,'v217':v217,'v218':v218,'native':native,
         'old_packet':old_packet,'graph':graph,'packet':packet,'official':official}


def run(x,*,pinhash=None):
    docs={k:(v if k=='srt' else D(v)) for k,v in x.items()}
    hashes={k:sha256(v) for k,v in docs.items()}
    return audit_v225_relation_closure(docs,pinhash or hashes,window_size=2)


class TestV225CompleteCandidateEndpointClosure(unittest.TestCase):
    def setUp(self):self.x=fake()
    def should_fail(self):
        with self.assertRaises(InvalidInput):run(self.x)
    def test_01_source_native_full_closure(self):
        r=run(self.x)
        self.assertEqual((r['verified_cues'],r['verified_unapproved_native_atoms']), (4,3))
        self.assertEqual((r['original_relations_retained'],r['candidate_endpoint_occurrences_lost_before'],r['candidate_endpoint_occurrences_lost_now']), (2,2,0))
        self.assertFalse(r['e2_final_pass'])
    def test_02_deterministic(self):self.assertEqual(run(self.x),run(self.x))
    def test_03_pinned_byte_change_rejected(self):
        docs={k:(v if k=='srt' else D(v)) for k,v in self.x.items()}
        hashes={k:sha256(v) for k,v in docs.items()}
        docs['srt']+=b'TAMPER'
        with self.assertRaises(InvalidInput):audit_v225_relation_closure(docs,hashes,2)
    def test_04_candidate_source_dropped(self):
        self.x['graph']['rows'][0]['candidate_source_atom_ids']=['C00001'];self.should_fail()
    def test_05_candidate_target_dropped(self):
        self.x['graph']['rows'][0]['candidate_target_atom_ids']=[];self.should_fail()
    def test_06_selected_source_changed(self):
        self.x['graph']['rows'][0]['v218_selected_source_atom_ids']=['C00003'];self.should_fail()
    def test_07_selected_target_deleted(self):
        self.x['graph']['rows'][0]['v218_selected_target_atom_ids']=[];self.should_fail()
    def test_08_extra_cue_review_omitted(self):
        self.x['graph']['rows'][0]['extra_endpoint_reviews']=[];self.should_fail()
    def test_09_silent_media_candidate_loss(self):
        self.x['graph']['rows'][1]['extra_source_atom_ids']=[];self.should_fail()
    def test_10_source_quote_tampered(self):
        self.x['graph']['rows'][0]['source_quote']='조작';self.should_fail()
    def test_11_target_quote_hash_tampered(self):
        self.x['graph']['rows'][1]['target_quote_sha256']='0'*64;self.should_fail()
    def test_12_relation_row_deleted(self):
        self.x['graph']['rows'].pop();self.should_fail()
    def test_13_duplicate_relation_id(self):
        self.x['graph']['rows'][1]['relation_id']='SYN-R001';self.should_fail()
    def test_14_forbidden_financial_approval(self):
        self.x['graph']['rows'][0]['any_semantic_financial_approval']=True;self.should_fail()
    def test_15_false_audio_evidence(self):
        self.x['graph']['rows'][0]['original_audio_or_video_verified']=True;self.should_fail()
    def test_16_false_gold_on_candidate(self):
        self.x['graph']['rows'][0]['extra_endpoint_reviews'][0]['independent_gold_verified']=True;self.should_fail()
    def test_17_missing_candidate_explanation(self):
        self.x['graph']['rows'][0]['extra_endpoint_reviews'][0]['source_first_reason']='';self.should_fail()
    def test_18_wrong_candidate_review_status(self):
        self.x['graph']['rows'][0]['extra_endpoint_reviews'][0]['status']='APPROVED';self.should_fail()
    def test_19_task_candidate_id_dropped(self):
        self.x['packet']['task_rows'][2]['v225_relation_candidate_ids']=[];self.should_fail()
    def test_20_existing_task_rewritten(self):
        self.x['packet']['task_rows'][2]['proposition']='인용과 다른 뜻';self.should_fail()
    def test_21_old_e3_relation_count_changed(self):
        self.x['packet']['preserved_inter_atom_and_intra_atom_relations']=0;self.should_fail()
    def test_22_false_e3_approved(self):
        self.x['packet']['v225_e3_final_approved']=True;self.should_fail()
    def test_23_official_bad_native_hash(self):
        self.x['official']['native_sha256']='0'*64;self.should_fail()
    def test_24_official_untrusted_domain(self):
        self.x['official']['rows'][0]['official_reference_urls']=['https://example.com'];self.should_fail()
    def test_25_official_false_certification(self):
        self.x['official']['official_original_response_bytes_certified']=True;self.should_fail()
    def test_26_official_row_approved(self):
        self.x['official']['rows'][0]['financial_fact_approved']=True;self.should_fail()
    def test_27_official_wrong_claim_text(self):
        self.x['official']['rows'][0]['claim_text']='다른 제도';self.should_fail()
    def test_28_missing_policy_time_conflict(self):
        self.x['official']['rule_time_conflict_requires_live_version_check']=False;self.should_fail()
    def test_29_native_unauthorized_kind_change(self):
        self.x['native']['atoms'][0]['kind']='RECOMMENDATION';self.should_fail()
    def test_30_srt_cue_mismatch(self):
        self.x['srt']=self.x['srt'].replace(b'ETF',b'AAA',1);self.should_fail()
    def test_31_unverified_claim_unknown(self):
        self.x['graph']['rows'][0]['candidate_source_atom_ids'].append('C99999');self.should_fail()
    def test_32_row_status_count_drift(self):
        self.x['graph']['relation_rows_with_extra_endpoints']=1;self.should_fail()
    def test_33_malformed_list_no_traceback(self):
        self.x['graph']['rows'][0]['candidate_source_atom_ids']=None;self.should_fail()
    def test_34_historical_v217_digest_not_verified(self):
        self.x['graph']['v217_original_relation_sha256']='0'*64;self.should_fail()
    def test_35_historical_v218_digest_not_verified(self):
        self.x['graph']['v218_selected_relation_review_sha256']='0'*64;self.should_fail()
    def test_36_cannot_suppress_old_new_regulation_conflict_note(self):
        self.x['official']['time_conflict_note']='';self.should_fail()

if __name__=='__main__':unittest.main()