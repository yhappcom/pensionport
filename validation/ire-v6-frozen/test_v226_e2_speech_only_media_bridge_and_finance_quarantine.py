"""Only original *synthetic* SRT in the public tests. No owner-private material."""
import copy
import hashlib
import json
import unittest
from ire.v6.atomic_exchange import audit_host_atomic_exchange, NUMBER
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import make_original_plan
from v226_e2_speech_only_media_bridge_and_finance_quarantine import audit_v226_original_kit


def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def digest(b):return hashlib.sha256(b).hexdigest()


def synthetic():
    # All phrases fictional and invented for failure tests, not any video.
    texts=[
        'ETF 거래소 상장 펀드라고 설명합니다.',
        'ETF만 괴리율이 있다고 잘못 주장합니다.',
        '추적차이와 추적오차는 같다고 말합니다.',
        '가상의 화면 예시를 보여준다고 말합니다.',
        '모의 화면에서 두 선이 가까워 보입니다.',
        '그러므로 추적차이가 적다고 설명합니다.',
        '마지막으로 인사하고 종료합니다.',
    ]
    raw='\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},800\n{t}' for i,t in enumerate(texts,1)).encode('utf-8')
    src,_=make_original_plan(raw,video_id='SYNTH000001',window_size=20,expected_source_sha256=digest(raw))
    def atom(cid,idx,prop,kind='FACT',context=None,conditions=None):
        return {'claim_id':cid,'owner_window_id':src.owner(idx),'proposition':prop,
         'kind':kind,'stance':'UNRESOLVED','speaker':'UNKNOWN',
         'source_refs':[{'cue_index':idx,'quote':texts[idx-1]}],
         'context_cue_indices':context or [idx],
         'condition_cue_indices':conditions or [],
         'exception_cue_indices':[],'numeric_references':[],'as_of':None}
    rows=[]
    for i,t in enumerate(texts,1):
        ids=[f'C{i:05d}'] if i<=3 else []
        rows.append({'cue_index':i,'cue_text_sha256':sha256(t.encode('utf-8')),
          'disposition':'CANDIDATES' if ids else ('NO_ATOM' if i==7 else 'UNRESOLVED'),
          'claim_ids':ids,'numeric_tokens':NUMBER.findall(t),
          'note':'인용된 모의 자막 후보' if ids else '모의 비주장 혹은 화면 보류'})
    old={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':src.video_id,
         'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
         'cue_dispositions':rows,'atoms':[
          atom('C00001',1,'ETF가 거래소 상장 펀드라는 설명'),
          atom('C00002',2,'ETF만 괴리율을 사용한다는 발언'),
          atom('C00003',3,'추적차이와 추적오차가 같다는 발언'),
         ]}
    audit_host_atomic_exchange(src,old)
    new=copy.deepcopy(old)
    newatom={'claim_id':'C00004','owner_window_id':src.owner(5),
       'proposition':'화자가 모의 화면의 두 선이 가깝고 추적차가 작다고 말한 사례(화면 미확인)',
       'kind':'HYPOTHETICAL','stance':'UNRESOLVED','speaker':'UNKNOWN',
       'source_refs':[{'cue_index':i,'quote':texts[i-1]} for i in (5,6)],
       'context_cue_indices':[4,5,6],'condition_cue_indices':[4],
       'exception_cue_indices':[],'numeric_references':[],'as_of':None}
    new['atoms'].append(newatom)
    for i in (5,6):
        new['cue_dispositions'][i-1].update({'disposition':'CANDIDATES','claim_ids':['C00004'],
              'note':'모의 화면 발언만 추출했으며 차트 근거는 여전히 미확인'})
    audit_host_atomic_exchange(src,new)
    media={'unapproved_speech_claims':[{'id':'M-SYNTH-001','source_refs':[
        {'cue_index':i,'quote':texts[i-1]} for i in (4,5,6)]}]}
    bridge={'schema':'IRE_V226_MEDIA_SPEECH_TO_V6_NATIVE_UNAPPROVED_V1',
        'source_sha256':src.source_sha256,
        'prior_native_sha256':digest(enc(old)),'new_native_sha256':digest(enc(new)),
        'original_media_evidence_resolved':False,'e2_gold_pass':False,
        'financial_facts_approved':False,'prior_legacy_media_claims_unapproved':1,
        'new_unapproved_native_draft_claims':1,'original_media_cue_ids':[4,5,6],
        'rows':[{'legacy_source_only_speech_id':'M-SYNTH-001',
          'new_unapproved_native_claim_id':'C00004','source_quote_cue_ids':[5,6],
          'all_original_speech_span':[4,5,6],
          'proposition_text_as_spoken_not_visual_fact':newatom['proposition'],
          'missing_evidence':'실제 차트의 선들이 가까운지 확인 불가능',
          'media_relation_ids_for_followup':['R-SYNTH-1'],
          'audio_visual_verified':False,'financial_truth_approved':False,
          'independent_gold_verified':False,'e3_approved':False,
          'release_gate':'HOLD_MEDIA_SOURCE_ONLY'}]}
    old_census={'original_source_sha256':src.source_sha256,
        'rows':[{'cue_index':i,'classification':('MEDIA_DEPENDENT_UNMAPPED_QUARANTINE' if i in (4,5,6) else 'OTHER'),
                 'original_audio_or_screen_review_required':i in (4,5,6),
                 'source_anchor_claim_ids':rows[i-1]['claim_ids'],
                 'context_claim_ids':[],'nonclaim_or_discourse_explanation':'모의 원문'} for i in range(1,8)]}
    new_census=copy.deepcopy(old_census)
    for i in (4,5,6):
        row=new_census['rows'][i-1]
        row['classification']=('MEDIA_SPEECH_SOURCE_ANCHORED_BUT_VISUAL_HOLD' if i in (5,6) else 'MEDIA_SPEECH_CONTEXT_STILL_VISUAL_HOLD')
        row['source_anchor_claim_ids']=['C00004'] if i in (5,6) else []
    new_census['classification_counts']=dict(__import__('collections').Counter(r['classification'] for r in new_census['rows']))
    new_census['media_evidence_cues_still_quarantined']=[4,5,6]
    new_census.update({'independent_gold_available':False,'financial_fact_approved':False,
                       'native_exchange_sha256':digest(enc(new))})
    finance={'rows':[{'claim_id':'C00002','status':'SPOKEN_CLAIM_CONTRADICTED_OR_TOO_BROAD'},
                     {'claim_id':'C00003','status':'TERMINOLOGY_NOT_RESOLVED'}]}
    def quarantine_row(cid,state):
        return {'claim_id':cid,'native_proposition_spoken_verbatim':next(x['proposition'] for x in old['atoms'] if x['claim_id']==cid),
          'disposition':state,'original_speaker_claim_retained_for_audit':True,
          'correction_is_not_source_atom':True,'official_primary_regulation_bytes_verified':False,
          'financial_fact_approved':False,'e3_final_approved':False,'e4_approved':False,'e5_published':False}
    quarantine={'schema':'IRE_V226_E3_FINANCE_CONTRADICTION_AND_UNRESOLVED_TERM_QUARANTINE_V1',
       'new_native_sha256':digest(enc(new)),'financial_facts_approved':0,
       'independent_gold_verified':False,'original_financial_false_or_overbroad_atoms':1,
       'tracking_terminology_unresolved_atoms':1,
       'rows':[quarantine_row('C00002','QUARANTINE_FINANCIAL_CONCEPT_CONTRADICTION'),
               quarantine_row('C00003','HOLD_TRACKING_TERMINOLOGY_ORIGINAL_AUDIO_REQUIRED')]}
    graph={'rows':[{'relation_id':'R-SYNTH-1','source_cue':5,'target_cue':6,'candidate_source_atom_ids':['C00004']}]}
    old_e3={'source_sha256':src.source_sha256,'native_sha256':digest(enc(old)),'source_claim_tasks':3,
        'task_rows':[{'claim_id':f'C{i:05d}','financial_fact_approved':False,
                      'e3_final_approved':False,'v225_relation_candidate_ids':[]} for i in range(1,4)],
        'v225_full_relation_count':1,'v225_full_legacy_candidate_endpoints_preserved':True,
        'v225_full_relation_rows_sha256':'0'*64,
        'globally_unassigned_original_media_quarantines':[{'relation_id':'R-SYNTH-1'}],
        'e3_final_approved':False,'e4_approved':False,'e5_published':False,
        'external_independent_gold_provided':False}
    new_e3=copy.deepcopy(old_e3)
    new_e3.update({'native_sha256':digest(enc(new)),'source_claim_tasks':4,
       'v226_media_to_native_review_sha256':digest(enc(bridge)),
       'v226_financial_contradiction_quarantine_sha256':digest(enc(quarantine))})
    for t in new_e3['task_rows']:
        t['v226_e3_financial_release_disposition']=('QUARANTINE_CONTRADICTED' if t['claim_id']=='C00002' else ('HOLD_TRACKING_TERMINOLOGY' if t['claim_id']=='C00003' else 'HOLD_UNVERIFIED'))
        t['v226_independent_gold_verified']=False
        t['v226_financial_facts_approved']=False
    new_e3['task_rows'].append({'claim_id':'C00004','primary_cue_ids':[5,6],
       'v225_relation_candidate_ids':['R-SYNTH-1'],'v226_e3_financial_release_disposition':'HOLD_MEDIA_UNVERIFIED',
       'e3_final_approved':False,'financial_fact_approved':False,'v226_financial_facts_approved':False,
       'v226_independent_gold_verified':False})
    metric={'not_an_independent_semantic_recall_measurement':True,
         'certified_gold_precision':None,'certified_gold_recall':None,
         'certified_high_risk_false_negatives':None,'e2_final_pass':False}
    kit={'srt':raw,'old_native':enc(old),'new_native':enc(new),'old_media':enc(media),
      'media_bridge':enc(bridge),'old_census':enc(old_census),'new_census':enc(new_census),
      'official21':enc(finance),'finance_quarantine':enc(quarantine),
      'old_e3':enc(old_e3),'new_e3':enc(new_e3),'relations32':enc(graph),'coverage_metric':enc(metric)}
    return kit


def alter(kit,part,fn):
    kit=copy.deepcopy(kit)
    d=json.loads(kit[part]);fn(d);kit[part]=enc(d)
    # Update the honest cross-document digests so the semantic gate, not a SHA mismatch, is exercised.
    for p,k in [('media_bridge','new_native_sha256'),('new_census','native_exchange_sha256'),
                ('finance_quarantine','new_native_sha256'),('new_e3','native_sha256')]:
        d=json.loads(kit[p]);d[k]=digest(kit['new_native']);kit[p]=enc(d)
    d=json.loads(kit['new_e3']);d['v226_media_to_native_review_sha256']=digest(kit['media_bridge'])
    d['v226_financial_contradiction_quarantine_sha256']=digest(kit['finance_quarantine']);kit['new_e3']=enc(d)
    return kit


class V226Synthetic(unittest.TestCase):
    def expect_bad(self,part,fn):
        kit=alter(synthetic(),part,fn)
        with self.assertRaises(InvalidInput): audit_v226_original_kit(kit,{k:digest(v) for k,v in kit.items()})

    def test_01_synthetic_full_route(self):
        kit=synthetic();r=audit_v226_original_kit(kit,{k:digest(v) for k,v in kit.items()})
        self.assertEqual((r['previous_native_atoms'],r['unapproved_native_atoms_after']), (3,4))
        self.assertEqual(r['media_speech_cue_refs_now_native'],2)
        self.assertFalse(r['independent_gold_recall_measured'])
        self.assertFalse(r['e3_e4_e5_authorized'])

    def test_02_original_srt_tamper(self):
        kit=synthetic();kit['srt']=kit['srt'].replace('ETF 거래소'.encode('utf-8'),'변조 거래소'.encode('utf-8'))
        with self.assertRaises(InvalidInput):audit_v226_original_kit(kit,{k:digest(v) for k,v in kit.items()})

    def test_03_wrong_manifest_sha(self): self.expect_bad('new_native',lambda d:d.__setitem__('manifest_sha256','0'*64))
    def test_04_surviving_claim_changed(self): self.expect_bad('new_native',lambda d:d['atoms'][0].__setitem__('proposition','수정했다 주장'))
    def test_05_surviving_kind_changed(self): self.expect_bad('new_native',lambda d:d['atoms'][0].__setitem__('kind','OPINION'))
    def test_06_surviving_speaker_forged(self): self.expect_bad('new_native',lambda d:d['atoms'][0].__setitem__('speaker','NARRATOR'))
    def test_07_media_kind_forged(self): self.expect_bad('new_native',lambda d:d['atoms'][-1].__setitem__('kind','FACT'))
    def test_08_media_stance_forged(self): self.expect_bad('new_native',lambda d:d['atoms'][-1].__setitem__('stance','AFFIRMED'))
    def test_09_media_speaker_forged(self): self.expect_bad('new_native',lambda d:d['atoms'][-1].__setitem__('speaker','NARRATOR'))
    def test_10_media_quote_changed(self): self.expect_bad('new_native',lambda d:d['atoms'][-1]['source_refs'][0].__setitem__('quote','실제 화면 확인 완료'))
    def test_11_media_draft_missing(self): self.expect_bad('new_native',lambda d:d['atoms'].pop())
    def test_12_duplicate_media_atom(self):self.expect_bad('new_native',lambda d:d['atoms'].append(copy.deepcopy(d['atoms'][-1])))
    def test_13_wrong_original_media_span(self):self.expect_bad('media_bridge',lambda d:d['rows'][0].__setitem__('all_original_speech_span',[5,6]))
    def test_14_missing_original_speech(self): self.expect_bad('old_media',lambda d:d['unapproved_speech_claims'].clear())
    def test_15_audio_verified_forged(self):self.expect_bad('media_bridge',lambda d:d['rows'][0].__setitem__('audio_visual_verified',True))
    def test_16_independent_gold_forged(self):self.expect_bad('media_bridge',lambda d:d['rows'][0].__setitem__('independent_gold_verified',True))
    def test_17_media_finance_approved(self):self.expect_bad('media_bridge',lambda d:d['rows'][0].__setitem__('financial_truth_approved',True))
    def test_18_media_e3_approved(self):self.expect_bad('media_bridge',lambda d:d['rows'][0].__setitem__('e3_approved',True))
    def test_19_non_media_cue_changed(self):self.expect_bad('new_native',lambda d:d['cue_dispositions'][6].__setitem__('note','내용을 바꿨음'))
    def test_20_media_quarantine_removed(self):self.expect_bad('new_census',lambda d:d['rows'][3].__setitem__('original_audio_or_screen_review_required',False))
    def test_21_visual_speech_reclassified_approved(self):self.expect_bad('new_census',lambda d:d['rows'][4].__setitem__('classification','FINANCIAL_FACT_APPROVED'))
    def test_22_census_missing_cue(self): self.expect_bad('new_census',lambda d:d['rows'].pop())
    def test_23_census_source_drift(self):self.expect_bad('new_census',lambda d:d.__setitem__('original_source_sha256','0'*64))
    def test_24_finance_contradiction_missing(self):self.expect_bad('finance_quarantine',lambda d:d['rows'].pop(0))
    def test_25_finance_contradiction_cleared(self):self.expect_bad('finance_quarantine',lambda d:d['rows'][0].__setitem__('disposition','HOLD_UNVERIFIED'))
    def test_26_correction_leaked_into_speaker(self):self.expect_bad('finance_quarantine',lambda d:d['rows'][0].__setitem__('native_proposition_spoken_verbatim','확정된 제도라고 쓰기'))
    def test_27_finance_approved(self): self.expect_bad('finance_quarantine',lambda d:d['rows'][0].__setitem__('financial_fact_approved',True))
    def test_28_regulation_bytes_forged(self):self.expect_bad('finance_quarantine',lambda d:d['rows'][0].__setitem__('official_primary_regulation_bytes_verified',True))
    def test_29_e3_media_task_dropped(self):self.expect_bad('new_e3',lambda d:d['task_rows'].pop())
    def test_30_e3_old_task_mangled(self):self.expect_bad('new_e3',lambda d:d['task_rows'][0].__setitem__('claim_id','C00097'))
    def test_31_e3_media_relation_missing(self):self.expect_bad('new_e3',lambda d:d['task_rows'][-1].__setitem__('v225_relation_candidate_ids',[]))
    def test_32_e3_old_relation_changed(self):self.expect_bad('new_e3',lambda d:d.__setitem__('v225_full_relation_rows_sha256','f'*64))
    def test_33_e3_quarantine_bypassed(self):self.expect_bad('new_e3',lambda d:d['task_rows'][1].__setitem__('v226_e3_financial_release_disposition','HOLD_UNVERIFIED'))
    def test_34_e3_formal_approval_forged(self):self.expect_bad('new_e3',lambda d:d.__setitem__('e3_final_approved',True))
    def test_35_e4_fake_approval(self):self.expect_bad('new_e3',lambda d:d.__setitem__('e4_approved',True))
    def test_36_e5_fake_publication(self):self.expect_bad('new_e3',lambda d:d.__setitem__('e5_published',True))
    def test_37_independent_recall_forged(self):self.expect_bad('coverage_metric',lambda d:d.__setitem__('certified_gold_recall',1.0))
    def test_38_independent_gold_flag_cleared(self):self.expect_bad('coverage_metric',lambda d:d.__setitem__('not_an_independent_semantic_recall_measurement',False))
    def test_39_graph_row_dropped(self):self.expect_bad('relations32',lambda d:d['rows'].pop())
    def test_40_cross_manifest_media_digest(self):
        kit=synthetic();d=json.loads(kit['new_e3']);d['v226_media_to_native_review_sha256']='0'*64;kit['new_e3']=enc(d)
        with self.assertRaises(InvalidInput):audit_v226_original_kit(kit,{k:digest(v) for k,v in kit.items()})
    def test_41_missing_manifest_input(self):
        kit=synthetic();kit.pop('new_native')
        with self.assertRaises(InvalidInput):audit_v226_original_kit(kit,{k:digest(v) for k,v in kit.items()})

if __name__=='__main__':unittest.main()