"""Synthetic-only V224 tests. Deliberately no private SRT, claims or reviewer notes in GitHub CI."""
import copy
import json
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from v224_e2_e3_inherited_scope_review_gate import (
    audit_exact_owner_source_and_review,require_e3_final_or_e4_e5_authorization)


def encode(obj):
    return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8')


def fixture():
    words=['ETF 강의의 비교 기준을 소개합니다.',
           '이번 여섯 가지 기준은 인덱스 ETF에 적용합니다.',
           '순자산이 높은 인덱스 ETF를 비교하자고 권고합니다.',
           '지금까지의 예시 설명을 마칩니다.']
    raw=('\n\n'.join('%d\n00:00:%02d,000 --> 00:00:%02d,500\n%s' %
                     (i,i,i,words[i-1]) for i in range(1,5))+'\n').encode('utf8')
    src,_=make_original_plan(raw,'Synth123456',expected_source_sha256=sha256(raw),window_size=2)
    quote=lambda i:src.cues[i-1].text
    dig=lambda i:sha256(quote(i).encode('utf8'))
    old={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':'Synth123456',
         'source_sha256':sha256(raw),'manifest_sha256':src.manifest_sha256,
         'atoms':[{'claim_id':'C00001','owner_window_id':'W00002',
                   'proposition':'순자산 높은 인덱스 ETF 비교를 제안하는 발언',
                   'kind':'RECOMMENDATION','stance':'UNRESOLVED','speaker':'UNKNOWN',
                   'source_refs':[{'cue_index':3,'quote':quote(3)}],
                   'context_cue_indices':[3],'condition_cue_indices':[],
                   'exception_cue_indices':[],'numeric_references':[],'as_of':None}],
         'cue_dispositions':[{'cue_index':i,'cue_text_sha256':dig(i),
             'disposition':'CANDIDATES' if i==3 else 'UNRESOLVED',
             'claim_ids':['C00001'] if i==3 else [],'numeric_tokens':[],
             'note':'원문이 제공한 미승인 발화 후보로 원음·정답 미확정'} for i in range(1,5)]}
    new=copy.deepcopy(old);new['atoms'][0]['context_cue_indices']=[2,3];new['atoms'][0]['condition_cue_indices']=[2]
    scope={'schema':'IRE_V224_REVIEWED_INHERITED_SPEECH_SCOPE_V1','video_id':'Synth123456',
           'original_source_sha256':sha256(raw),'scope_id':'SCOPE-SYNTH-INDEX-001',
           'scope_kind':'APPLICABILITY_OF_SIX_QUALITATIVE_SELECTION_CRITERIA',
           'scope_value':'PASSIVE_INDEX_ETF_FOCUS_NOT_ALL_ETFS',
           'source_cue_indices':[2],'source_cue_quotes':[quote(2)],'source_cue_sha256':[dig(2)],
           'source_first_semantic_explanation':'원문은 선택 기준이 인덱스 ETF용임을 직접 밝히므로 후속 추천 발화에 해당 범위를 연결한다.',
           'applicable_native_claim_ids':['C00001'],
           'reviewed_by':'CHATGPT_SOURCE_TEXT_SEMANTIC_JUDGMENT_NOT_EXTERNAL_GOLD',
           'inherited_source_scope_is_reviewer_judgment':True,
           'original_audio_verified':False,'independent_gold_verified':False,
           'no_financial_knowledge_approved':True}
    frow={'claim_id':'C00001','kind':'RECOMMENDATION','primary_cue_ids':[3],
          'primary_original_text_sha256':[dig(3)],'context_cue_indices':[3],
          'numeric_source_token_cue_pairs':[],'risk_tags':['ADVICE_NOT_PERSONAL_FINANCE'],
          'risk_review_status':'HOLD_REQUIRES_OFFICIAL_OR_MEDIA_REVIEW',
          'speaker_verified':False,'stance_confirmed':False,
          'financial_truth_certified':False,'semantically_gold_verified':False,
          'claim_approved':False}
    fbase={'schema':'PRIVATE_SYNTH_FINANCE_V1','video_id':'Synth123456',
           'source_sha256':sha256(raw),'native_exchange_sha256':sha256(encode(old)),
           'risk_tagged_atom_count':1,'e2_final_pass':False,'atoms':[frow]}
    fnew=copy.deepcopy(fbase);fnew['native_exchange_sha256']=sha256(encode(new));fnew['atoms'][0]['context_cue_indices']=[2,3]
    rows=[]
    for i in range(1,5):
        row={'cue_index':i,'cue_text_sha256':dig(i),'source_quote':quote(i),
             'classification':('SOURCE_ANCHORED_NATIVE_UNAPPROVED' if i==3 else
                               'DISCOURSE_OR_NONCLAIM_PROVISIONAL'),
             'source_anchor_claim_ids':['C00001'] if i==3 else [],
             'context_claim_ids':['C00001'] if i==3 else [],
             'original_audio_or_screen_review_required':False,
             'independent_omission_review_complete':False,
             'classification_is_chatgpt_source_review_not_external_gold':True,
             'financial_fact_approved':False,'e2_final_pass':False}
        if i!=3:row['nonclaim_or_discourse_explanation']='SOURCE_INCOMPLETE_DISCOURSE_UNIT_NOT_GOLD'
        rows.append(row)
    oldc={'schema':'SYNTH_CENSUS_V1','video_id':'Synth123456',
          'native_exchange_sha256':sha256(encode(old)),
          'original_source_sha256':sha256(raw),
          'classification_counts':dict(sorted({r['classification']:sum(x['classification']==r['classification'] for x in rows) for r in rows}.items())),
          'distinct_primary_claim_ids':1,'e2_final_pass':False,'rows':rows}
    newc=copy.deepcopy(oldc);newc['native_exchange_sha256']=sha256(encode(new))
    newc['rows'][1]['classification']='SOURCE_CONTEXT_ONLY_UNAPPROVED'
    newc['rows'][1]['context_claim_ids']=['C00001']
    newc['rows'][1].pop('nonclaim_or_discourse_explanation')
    newc['classification_counts']={
       'DISCOURSE_OR_NONCLAIM_PROVISIONAL':2,
       'SOURCE_ANCHORED_NATIVE_UNAPPROVED':1,
       'SOURCE_CONTEXT_ONLY_UNAPPROVED':1}
    reviewrow={'claim_id':'C00001','current_native_kind':'RECOMMENDATION',
         'existing_proposition':new['atoms'][0]['proposition'],
         'source_primary_cue_indices':[3], 'actual_source_quotes':[quote(3)],
         'actual_source_full_cue_quote_sha256':[dig(3)],
         'support_context_cue_indices':[2,3],
         'support_context_quotes':[quote(2),quote(3)],
         'review_disposition':'SOURCE_SUPPORTED_AS_SPOKEN_WITH_MATERIAL_QUALIFICATION',
         'review_explanation':'실제 자막에서 인덱스 ETF의 적용 범위를 먼저 밝히고 나서 순자산 비교를 권고하므로 조건이 필수이다.',
         'financial_evidence_disposition':'NORMATIVE_OR_EVALUATIVE_NOT_OBJECTIVE_FACT',
         'official_concept_context_ref_ids':['KRX'],
         'inherited_index_etf_scope_cue_indices':[2],
         'scope_inheritance_verified_from_source_text':True,
         'speaker_attribution':'PRESENTER_VOICE_INFERRED_FROM_CONTINUOUS_TRANSCRIPT_TEXT_ONLY',
         'speaker_audio_verified':False,'textual_discourse_stance':'RECOMMENDATION_TEXT_ONLY',
         'native_stance_still_unresolved':True,
         'hypothetical_or_fictional_not_current_market':False,
         'reviewer_proposed_numeric_derivation_not_source_quote':None,
         'chatgpt_text_only_meaning_review_complete':True,
         'independent_gold_adjudicated':False,'audio_video_evidence_verified':False,
         'financial_fact_approved':False,'e3_final_approved':False,
         'e4_approved':False,'e5_published':False}
    review={'schema':'IRE_V224_CHATGPT_ACTUAL_65_ATOM_SOURCE_AND_FINANCE_SEMANTIC_REVIEW_V1',
           'video_id':'Synth123456','original_source_sha256':sha256(raw),
           'prior_native_exchange_sha256':sha256(encode(old)),
           'corrected_native_exchange_sha256':sha256(encode(new)),
           'inherited_global_scope_review_sha256':sha256(encode(scope)),
           'reviewer':'CHATGPT_ORIGINAL_SOURCE_AND_V223_E3_PACKET_REVIEW_NOT_BLIND_GOLD',
           'source_seen_prior_model_outputs':True,'source_only_review_completed':True,
           'independent_external_truth_gold_available':False,
           'official_context_source_raw_bytes_not_verified':True,
           'official_context_sources':{'KRX':'https://www.krx.co.kr/contents/OPN/01/01030203/OPN01030203T2.jsp'},
           'speaker_audio_verified':False,'video_graphics_verified':False,
           'financial_knowledge_approved':0,
           'e3_semantic_review_dispositions_recorded':True,
           'e3_final_approved':False,'e4_approved':False,'e5_published':False,
           'claimed_atom_total':1,'manual_text_only_review_count':1,'rows':[reviewrow]}
    oldtask={'claim_id':'C00001','proposition':new['atoms'][0]['proposition'],
             'source_context':[{'cue_index':3,'quote':quote(3),'quote_sha256':dig(3)}],
             'primary_cue_ids':[3],'source_text_is_not_audio_verified':True,
             'inter_atom_discourse_dependencies':[],'financial_fact_approved':False}
    oldp={'source_sha256':sha256(raw),'native_sha256':sha256(encode(old)),
          'preserved_inter_atom_and_intra_atom_relations':0,
          'globally_unassigned_original_media_quarantines':[{'source_cue':4,
                                                             'financial_facts_approved':False}],
          'task_rows':[oldtask]}
    newp=copy.deepcopy(oldp)
    newp.update({'native_sha256':sha256(encode(new)),
                 'semantic_convergence_atom_digest':None,
                 'actual_chatgpt_review_completed_for_all_65_unapproved_claims':True,
                 'actual_chatgpt_review_sha256':sha256(encode(review)),
                 'global_index_only_scope_review_sha256':sha256(encode(scope)),
                 'external_independent_gold_provided':False,
                 'source_audio_video_verified':False,'tasks_are_not_approved':True,
                 'e3_final_approved':False,'e4_approved':False,'e5_published':False,
                 'financial_truth_corrected_before_knowledge_published':False})
    newtask=newp['task_rows'][0]
    newtask.update({'source_context':[
        {'cue_index':2,'quote':quote(2),'quote_sha256':dig(2)},
        {'cue_index':3,'quote':quote(3),'quote_sha256':dig(3)}],
       'condition_cue_indices':[2],
       'inherited_index_etf_scope_cue_indices':[2],
       'actual_chatgpt_text_review_disposition':reviewrow['review_disposition'],
       'actual_financial_evidence_disposition':reviewrow['financial_evidence_disposition'],
       'e3_final_approved':False})
    docs={'source':raw,'old_native':old,'new_native':new,'scope':scope,
          'old_finance':fbase,'new_finance':fnew,'old_census':oldc,'new_census':newc,
          'review':review,'old_packet':oldp,'new_packet':newp}
    return docs


def run(d,repin=True):
    b={k:(v if k=='source' else encode(v)) for k,v in d.items()}
    h={k:sha256(v) for k,v in b.items()}
    if repin:
        source,_=make_original_plan(b['source'],'Synth123456',expected_source_sha256=h['source'],window_size=2)
        from ire.v6.atomic_exchange import audit_host_atomic_exchange
        a=audit_host_atomic_exchange(source,d['new_native'])
        d['new_packet']['semantic_convergence_atom_digest']=a['atom_candidate_digest']
        d['new_packet']['actual_chatgpt_review_sha256']=h['review']
        b['new_packet']=encode(d['new_packet']);h['new_packet']=sha256(b['new_packet'])
    return audit_exact_owner_source_and_review(b,h,window_size=2)


class TestV224ScopeAndTrueSourceReview(unittest.TestCase):
    def setUp(self):self.d=fixture()
    def assertReject(self):
        with self.assertRaises(InvalidInput):run(self.d)
    def test_01_pass_one_complete_review_and_scope(self):
        r=run(self.d);self.assertEqual(r['scope_inherited_atoms'],1)
        self.assertEqual(r['text_only_claim_reviewed'],1)
        self.assertFalse(r['e3_final_approved'])
    def test_02_equal_replay_deterministic(self):self.assertEqual(run(self.d),run(self.d))
    def test_03_direct_publish_gate_fails(self):
        with self.assertRaisesRegex(InvalidInput,'NO_INDEPENDENT_GOLD'):
            require_e3_final_or_e4_e5_authorization(run(self.d))
    def test_04_reject_false_release_receipt(self):
        r=run(self.d);r['e2_final_pass']=True
        with self.assertRaises(InvalidInput):require_e3_final_or_e4_e5_authorization(r)
    def test_05_scope_cue_missing_from_native(self):
        self.d['new_native']['atoms'][0]['condition_cue_indices']=[];self.assertReject()
    def test_06_scope_cue_missing_from_context(self):
        self.d['new_native']['atoms'][0]['context_cue_indices']=[3];self.assertReject()
    def test_07_wrong_source_quote_in_scope_event(self):
        self.d['scope']['source_cue_quotes']=['가짜 발언입니다.'];self.assertReject()
    def test_08_wrong_source_hash_in_scope_event(self):
        self.d['scope']['source_cue_sha256']=['0'*64];self.assertReject()
    def test_09_unreviewed_proposition_must_not_change(self):
        self.d['new_native']['atoms'][0]['proposition']='모든 ETF는 원금이 보장됩니다.';self.assertReject()
    def test_10_unreviewed_kind_must_not_change(self):
        self.d['new_native']['atoms'][0]['kind']='FACT';self.assertReject()
    def test_11_wrong_primary_quote_rejected(self):
        self.d['new_native']['atoms'][0]['source_refs'][0]['quote']='다른 증거입니다';self.assertReject()
    def test_12_approved_native_speaker_rejected(self):
        self.d['new_native']['atoms'][0]['speaker']='NARRATOR';self.assertReject()
    def test_13_fake_audio_speaker_assertion_rejected(self):
        self.d['review']['rows'][0]['speaker_audio_verified']=True;self.assertReject()
    def test_14_goldticked_without_independent_data_rejected(self):
        self.d['review']['rows'][0]['independent_gold_adjudicated']=True;self.assertReject()
    def test_15_dropped_finance_risk_rejected(self):
        self.d['new_finance']['atoms'][0]['risk_tags']=[];self.assertReject()
    def test_16_unapproved_finance_claim_cannot_pass(self):
        self.d['new_finance']['atoms'][0]['claim_approved']=True;self.assertReject()
    def test_17_previous_native_hash_not_current_rejected(self):
        self.d['new_census']['native_exchange_sha256']='f'*64;self.assertReject()
    def test_18_context_census_omission_rejected(self):
        self.d['new_census']['rows'][1]['context_claim_ids']=[];self.assertReject()
    def test_19_cue_classification_wrong_rejected(self):
        self.d['new_census']['rows'][1]['classification']='DISCOURSE_OR_NONCLAIM_PROVISIONAL';self.assertReject()
    def test_20_visual_hold_dropped_from_packet_rejected(self):
        self.d['new_packet']['globally_unassigned_original_media_quarantines']=[];self.assertReject()
    def test_21_source_context_quote_changed_in_packet_rejected(self):
        self.d['new_packet']['task_rows'][0]['source_context'][0]['quote']='허위인용';self.assertReject()
    def test_22_review_unanchored_primary_rejected(self):
        self.d['review']['rows'][0]['source_primary_cue_indices']=[4];self.assertReject()
    def test_23_review_disposition_unknown_rejected(self):
        self.d['review']['rows'][0]['review_disposition']='REAL_GOLD_PASS';self.assertReject()
    def test_24_too_short_or_boilerplate_explanation_rejected(self):
        self.d['review']['rows'][0]['review_explanation']='PASS';self.assertReject()
    def test_25_unrecognized_external_context_domain_rejected(self):
        self.d['review']['official_context_sources']['KRX']='https://untrusted.example/guide';self.assertReject()
    def test_26_false_e3_approval_rejected(self):
        self.d['new_packet']['e3_final_approved']=True;self.assertReject()
    def test_27_scope_claim_list_mismatch_rejected(self):
        self.d['scope']['applicable_native_claim_ids']=['C99999'];self.assertReject()
    def test_28_source_bytes_mismatch_rejected(self):
        doc=self.d.copy();b={k:(v if k=='source' else encode(v)) for k,v in doc.items()}
        h={k:sha256(v) for k,v in b.items()}
        b['source']=b['source']+b'garbage'
        with self.assertRaises(InvalidInput):audit_exact_owner_source_and_review(b,h,2)
    def test_29_untracked_extra_in_native_rejected(self):
        self.d['new_native']['atoms'].append(copy.deepcopy(self.d['new_native']['atoms'][0]));self.assertReject()
    def test_30_no_fake_numeric_derivation(self):
        self.d['review']['rows'][0]['reviewer_proposed_numeric_derivation_not_source_quote']={
            'nav_won':17728,'market_won':17645,'price_minus_nav_won':-83,'discount_percent_approx':+0.4682}
        self.assertReject()
    def test_31_correct_reviewer_only_derivation_is_not_official_approval(self):
        self.d['review']['rows'][0]['reviewer_proposed_numeric_derivation_not_source_quote']={
            'nav_won':17728,'market_won':17645,'price_minus_nav_won':-83,'discount_percent_approx':-0.4682}
        r=run(self.d);self.assertFalse(r['e2_final_pass'])
    def test_32_omitted_media_cue_unrelated_to_scope_is_not_silently_accepted(self):
        self.d['new_census']['rows'][2]['classification']='DISCOURSE_OR_NONCLAIM_PROVISIONAL'
        self.assertReject()
    def test_33_new_reviewer_note_never_certifies_official_bytes(self):
        self.d['review']['official_context_source_raw_bytes_not_verified']=False;self.assertReject()
    def test_34_reviewed_scope_is_not_claimed_as_external_blind(self):
        self.d['scope']['independent_gold_verified']=True;self.assertReject()
    def test_35_new_e3_packet_cannot_omit_actual_review_ref(self):
        run(self.d)  # build the otherwise valid trusted packet first
        self.d['new_packet'].pop('actual_chatgpt_review_sha256')
        b={k:(v if k=='source' else encode(v)) for k,v in self.d.items()}
        h={k:sha256(v) for k,v in b.items()}
        with self.assertRaises(InvalidInput):
            audit_exact_owner_source_and_review(b,h,window_size=2)

if __name__=='__main__':unittest.main()