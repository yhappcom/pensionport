"""Public synthetic tests only; no real owner's SRT or atom text."""
from __future__ import annotations
import copy
import unittest
from unittest.mock import patch

from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_manifest
from v164_typed_v123 import (
    ROW_SCHEMA,B0001_EXPECTED,_cue_pin, audit_typed_speech_row,
    assess_typed_chat_final_v164,
)


def sample_source():
    texts={
      3:'가상으로 들어가서 손해를 보면 어떻게 해야 하는 질문입니다.',
      5:'확신하고 매수했다는 말은 무슨 질문인가요?',
      42:'낯선 사례를 읽으니 꽤 어렵다고 느낀 주관적 감상입니다.',
      69:'사업 방법을 자산 투자에 적용해 보는 것은 어떨까요?',
      95:'저가에 매입하면 손실이 적을 것이라고 가정하는 조건부 설명입니다.',
    }
    cues=[]
    for i in range(1,121):
        sec=i*2;mm,ss=divmod(sec,60)
        stamp=f'00:{mm:02d}:{ss:02d},000'
        end=f'00:{mm:02d}:{ss:02d},700'
        cues.append(f'{i}\n{stamp} --> {end}\n{texts.get(i,"검증을 위한 완전히 합성된 일반 대화 내용입니다.")}')
    raw='\n\n'.join(cues).encode()
    m=make_manifest(raw,cut=120)
    return verify_source(raw,m,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(m))


class TypedReviewSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.source=sample_source()
        self.cues={i:'REVIEWED' for i in range(1,121)}
        ctx={
          'C00001':([3],'질문입니다.'),
          'C00003':([69],'적용해 보는 것은 어떨까요?'),
          'C00277':([95],'조건부 설명입니다.'),
          'C00285':([42],'주관적 감상입니다.'),
          'C00293':([5],'무슨 질문인가요?'),
        }
        extra={'C00002','C00009','C00010'}
        accept={'C00004','C00005','C00006','C00007','C00008','C00011','C00284'}
        self.atoms={};self.legacy={};self.rows=[]
        for cid in sorted(set(ctx)|extra|accept|{'C00012'}):
            kind=B0001_EXPECTED[cid][0] if cid in ctx else 'FACT'
            ids=ctx[cid][0] if cid in ctx else [10]
            a={
                'claim_id':cid,'kind':kind,'speaker':'UNKNOWN',
                'context_cue_indices':ids,'proposition':'완전히 합성된 검토 후보 문장입니다.',
                'numeric_references':[],
            }
            self.atoms[cid]=a
            self.legacy[cid]={
                'claim_id':cid,'atom_sha256':json_digest(a),
                'status':'OPEN' if cid in set(ctx)|extra else
                         'EXCLUDE_FROM_RESEARCH' if cid=='C00012' else 'ACCEPT_FOR_RESEARCH',
                'financial_claim':True,'high_risk':True,'finance_evidence_status':'OPEN',
            }
        notes={
           'C00001':'이것은 손해 위험을 묻는 질문이며 실제 답변이 아닙니다. 가정된 구매가 투자성과를 보장하지 않으며 문제의 의미만 원본으로 확인합니다.',
           'C00003':'책의 원리를 어떻게 활용할지 살펴보자는 제안일 뿐 개인 포트폴리오의 투자 적합성을 보장하지 않으며 사실 검증과 분리합니다.',
           'C00277':'가격이 낮고 가치가 높다는 조건의 상대적 수익 가능성에 대한 가설이며 절대 보장은 없습니다. 객관 시장 통계로 확인하지 않았습니다.',
           'C00285':'독서 난이도를 자신의 개인적 경험으로 설명하는 발언이며 외부 책의 객관적 품질이나 투자 효과를 확인한 것은 아닙니다.',
           'C00293':'해당 발언은 확신이라는 개념에 대한 질문이고 답변이 아닙니다. 특정 금융상품을 사라는 권유는 아닙니다. 영상 맥락만 확인했습니다.',
        }
        for cid,(indices,anchor) in ctx.items():
            a=self.atoms[cid];note=notes[cid]
            self.rows.append({
               'schema':ROW_SCHEMA,'claim_id':cid,'atom_sha256':json_digest(a),
               'source_sha256':self.source.source_sha256,'source_cue_indices':indices,
               'source_context_sha256':_cue_pin(self.source,indices),
               'speech_type':B0001_EXPECTED[cid][1],
               'verbatim_anchor_cue_index':indices[0], 'verbatim_anchor':anchor,
               'source_speaker_identity':'UNKNOWN_NOT_AUDIO_AUTHENTICATED',
               'chat_meaning_analysis':note,'chat_meaning_analysis_sha256':sha256(note.encode()),
               'conditions_checked':True,'exceptions_checked':True,
               'numeric_checked':True,'counterexample_checked':True,
               'speaker_stance_checked':True,
               'financial_factual_truth_certified':False,
               'strategy_effectiveness_verified':False,
               'individual_investment_advice_approved':False,
               'independent_gold_certified':False,
               'external_source_audio_authenticated':False,
               'research_knowledge_export_allowed':False,
               'source_only_attribution':True,
               'disclosure_restriction':'ORIGINAL_VIDEO_SPEECH_ONLY_NOT_FINANCIAL_TRUTH_OR_ADVICE'
            })
        self.rows.sort(key=lambda x:x['claim_id'])
    def test_01_all_five_synthetic_source_speech_rows_attested(self):
        for row in self.rows:
            got=audit_typed_speech_row(self.source,self.atoms[row['claim_id']],
                                       self.legacy[row['claim_id']],row,self.cues)
            self.assertFalse(got['research_knowledge_export_allowed'])
            self.assertFalse(got['investment_recommendation_approved'])

    def _change_reject(self,field,value,expected_code=None):
        r=copy.deepcopy(self.rows[0]);r[field]=value
        with self.assertRaises(InvalidInput) as cm:
            audit_typed_speech_row(self.source,self.atoms[r['claim_id']],
                                   self.legacy[r['claim_id']],r,self.cues)
        if expected_code:self.assertIn(expected_code,str(cm.exception))

    def test_02_source_original_sha_must_match(self):self._change_reject('source_sha256','0'*64,'SOURCE_OR_ATOM_DRIFT')
    def test_03_atom_sha_must_match(self):self._change_reject('atom_sha256','0'*64)
    def test_04_exact_cue_set_must_match(self):self._change_reject('source_cue_indices',[1,2])
    def test_05_original_cue_digest_must_match(self):self._change_reject('source_context_sha256','0'*64)
    def test_06_source_verbatim_must_be_exact(self):self._change_reject('verbatim_anchor','존재하지않는만든인용')
    def test_07_named_speaker_without_audio_forbidden(self):self._change_reject('source_speaker_identity','PRESENTER')
    def test_08_wrong_type_must_not_downgrade(self):self._change_reject('speech_type','PERSONAL_READING_IMPRESSION_ONLY')
    def test_09_market_fact_certificate_forbidden(self):self._change_reject('financial_factual_truth_certified',True)
    def test_10_strategy_effectiveness_certificate_forbidden(self):self._change_reject('strategy_effectiveness_verified',True)
    def test_11_personal_advice_certificate_forbidden(self):self._change_reject('individual_investment_advice_approved',True)
    def test_12_independent_gold_certificate_forbidden(self):self._change_reject('independent_gold_certified',True)
    def test_13_audio_certificate_forbidden(self):self._change_reject('external_source_audio_authenticated',True)
    def test_14_knowledge_export_forbidden(self):self._change_reject('research_knowledge_export_allowed',True)
    def test_15_review_text_digest_must_match(self):self._change_reject('chat_meaning_analysis_sha256','0'*64)
    def test_16_unreviewed_cue_cannot_attest(self):
        row=self.rows[0];c=dict(self.cues);c[row['source_cue_indices'][0]]='OPEN'
        with self.assertRaises(InvalidInput):
            audit_typed_speech_row(self.source,self.atoms[row['claim_id']],self.legacy[row['claim_id']],row,c)
    def test_17_not_native_open_cannot_attest(self):
        row=self.rows[0];original=dict(self.legacy[row['claim_id']]);original['status']='ACCEPT_FOR_RESEARCH'
        with self.assertRaises(InvalidInput):
            audit_typed_speech_row(self.source,self.atoms[row['claim_id']],original,row,self.cues)
    def test_18_non_highrisk_cannot_attest_as_risk(self):
        row=self.rows[0];original=dict(self.legacy[row['claim_id']]);original['high_risk']=False
        with self.assertRaises(InvalidInput):
            audit_typed_speech_row(self.source,self.atoms[row['claim_id']],original,row,self.cues)
    def test_19_cannot_hide_hypothesis_risk_disclosure(self):
        row=next(copy.deepcopy(x) for x in self.rows if x['claim_id']=='C00277')
        row['chat_meaning_analysis']='조건부 시나리오입니다. 객관적 사실이나 수익 예측 근거는 제공되지 않았습니다.'
        row['chat_meaning_analysis_sha256']=sha256(row['chat_meaning_analysis'].encode())
        with self.assertRaises(InvalidInput):
            audit_typed_speech_row(self.source,self.atoms['C00277'],self.legacy['C00277'],row,self.cues)
    def test_20_cannot_hide_advice_lack_of_suitability(self):
        row=next(copy.deepcopy(x) for x in self.rows if x['claim_id']=='C00003')
        row['chat_meaning_analysis']='책의 투자 내용을 따라 하자는 제안입니다. 어떤 상품을 다룰지는 미정입니다.'
        row['chat_meaning_analysis_sha256']=sha256(row['chat_meaning_analysis'].encode())
        with self.assertRaises(InvalidInput):
            audit_typed_speech_row(self.source,self.atoms['C00003'],self.legacy['C00003'],row,self.cues)
    def _full_gate(self,rows=None,native=None,review=None):
        rev={'atom_verdicts':list(self.legacy.values()),'source_cues':[
            {'cue_index':i,'status':'REVIEWED'} for i in range(1,121)],
            'unresolved_high_risk_omissions':12,'disagreements_adjudicated':False}
        if review:rev.update(review)
        n={'status':'CHAT_FINAL_HOLD_OPEN','atoms_accepted':7,'atoms_open':8,
            'finance_open':8,'research_candidate_export_allowed':False,
            'cues_reviewed':120,'atoms_excluded':1}
        if native:n.update(native)
        with patch('v164_typed_v123.audit_host_atomic_exchange',return_value={}),\
             patch('v164_typed_v123.assess_chat_final_gate',return_value=n):
            return assess_typed_chat_final_v164(
                self.source,{'atoms':list(self.atoms.values())},host_receipt={'event_sha256':'e'*64},
                store=object(),legacy_chat_review=rev,official_evidence_bodies={},
                typed_rows=self.rows if rows is None else rows)
    def test_21_typed_all_speech_does_not_override_v123_or_v128(self):
        x=self._full_gate()
        self.assertEqual(x['source_speech_act_only_typed_reviewed'],5)
        self.assertEqual(x['objective_historical_claims_unverified'],['C00002','C00009','C00010'])
        self.assertEqual(x['unresolved_high_risk_omissions'],12)
        self.assertFalse(x['disagreements_adjudicated'])
        self.assertFalse(x['typed_final_knowledge_release_authorized'])
        self.assertFalse(x['v128_parent_publication_authorized'])
    def test_22_missing_typed_speech_act_fails(self):
        with self.assertRaises(InvalidInput):self._full_gate(rows=self.rows[:-1])
    def test_23_duplicate_typed_speech_act_fails(self):
        with self.assertRaises(InvalidInput):self._full_gate(rows=self.rows+[self.rows[0]])
    def test_24_legacy_v123_false_pass_fails(self):
        with self.assertRaises(InvalidInput):self._full_gate(native={'status':'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY'})
    def test_25_historical_factual_claim_cannot_become_speech_only(self):
        row=copy.deepcopy(self.rows[0]);row['claim_id']='C00002';row['atom_sha256']=json_digest(self.atoms['C00002'])
        with self.assertRaises(InvalidInput):self._full_gate(rows=self.rows+[row])
    def test_26_false_zero_risk_counts_do_not_authorize_export(self):
        x=self._full_gate(review={'unresolved_high_risk_omissions':0,'disagreements_adjudicated':True})
        self.assertFalse(x['typed_full_scope_semantic_pass'])
        self.assertFalse(x['v128_parent_publication_authorized'])

if __name__=='__main__':unittest.main()
