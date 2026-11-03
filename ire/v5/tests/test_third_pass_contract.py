"""Synthetic third-pass reject tests; never require real private SRT in GitHub CI."""
import unittest,copy
from types import SimpleNamespace
from ire.v5.engine import sha256, canonical, RunError
from ire.v5.third_pass import FocusedReview64, SCHEMA, _official_url

NOW='2026-11-04T02:55:00+09:00'
B={'kind':'B','window_id':'W00001','left_cue':3,'right_cue':4,'left_quote':'연금 15%는','right_quote':'특정 조건입니다',
    'context':[{'cue_index':2,'text':'가정에 따라서'},{'cue_index':3,'text':'연금 15%는'},{'cue_index':4,'text':'특정 조건입니다'}]}
N={'kind':'N','cue_index':8,'quote':'15.4%인지 15%인지 혼재','context':[{'cue_index':8,'text':'15.4%인지 15%인지 혼재'}]}
E={'kind':'E','claim_id':'V5C0001','proposition':'연금에는 예외가 있습니다.'}

def fake():
    src={'B-W00001':B,'N-00008':N,'E-V5C0001':E}
    rev={k:{'decision':'SOURCE_TRANSCRIPTION_OPEN'} for k in src}
    x=object.__new__(FocusedReview64)
    x.ids=tuple(src)
    x.audit=SimpleNamespace(issues=src,reviews=rev)
    x.run=SimpleNamespace(_claims=lambda:{'V5C0001':{'source_refs':[{'cue_index':3,'quote':'연금 15%는'}]}})
    return x

def base(k,decision):
    x=fake();z=x.audit.issues[k]
    return x,{'schema':SCHEMA,'issue_id':k,'kind':z['kind'],
        'issue_sha256':sha256(canonical(z)),'prior_review_sha256':sha256(canonical(x.audit.reviews[k])),
        'reviewer':'CURRENT_CHATGPT_CONVERSATION','reviewed_at':NOW,
        'decision':decision,'explanation':'개별 자막과 공식자료를 연결했으나 개인 과세·법령 시점에 관한 별도의 독립 검증은 아직 끝나지 않았습니다.',
        'financial_fact_independently_approved':False,'investment_advice_approved':False,'old_events_rewritten':False}

class ThirdPassContractTests(unittest.TestCase):
    def test_issuer_domain_enforced(self):
        self.assertTrue(_official_url('https://law.go.kr/LSW/foo'))
        self.assertFalse(_official_url('https://law.go.kr.attack.tld/test'))
        self.assertFalse(_official_url('http://law.go.kr/unsafe'))
    def test_valid_boundary_without_truth_promotion(self):
        x,z=base('B-W00001','BOUNDARY_CONTEXT_RECONSTRUCTED_LIMITED')
        z.update({k:B[k] for k in ('left_cue','right_cue','left_quote','right_quote','context')})
        z['related_claim_ids']=['V5C0001']
        self.assertEqual(x.validate_row(z),'B-W00001')
    def test_boundary_halo_fabrication_rejected(self):
        x,z=base('B-W00001','BOUNDARY_CONTEXT_RECONSTRUCTED_LIMITED')
        z.update({k:B[k] for k in ('left_cue','right_cue','left_quote','right_quote','context')})
        z['related_claim_ids']=['V5C0001'];z['right_quote']='개인 최적의 세율이라고 합니다'
        with self.assertRaisesRegex(RunError,'THIRD_PASS_BOUNDARY_QUOTE_CHANGED'):x.validate_row(z)
    def test_no_financial_fact_self_approval(self):
        x,z=base('N-00008','AUDIO_TRANSCRIPT_REQUIRED')
        z.update({'cue_index':8,'exact_quote':N['quote'],'context':N['context'],'independent_audio_checked':False})
        z['financial_fact_independently_approved']=True
        with self.assertRaisesRegex(RunError,'THIRD_PASS_FALSE_APPROVAL'):x.validate_row(z)
    def test_numeric_must_be_audio_open(self):
        x,z=base('N-00008','AUDIO_TRANSCRIPT_REQUIRED')
        z.update({'cue_index':8,'exact_quote':N['quote'],'context':N['context'],'independent_audio_checked':True})
        with self.assertRaisesRegex(RunError,'THIRD_PASS_NUMERIC_NOT_AUDIO_VERIFIED'):x.validate_row(z)
    def test_official_candidate_must_have_exact_host_and_hash(self):
        x,z=base('E-V5C0001','PRIMARY_RULE_TEXT_FOUND_APPLICABILITY_OPEN')
        ev={'official_url':'https://law.go.kr/LSW/test','exact_excerpt':'과세제외금액을 먼저 인출','source_type':'WEB_TOOL_VISIBLE_PRIMARY_EXCERPT',
            'observed_at':NOW,'date_and_scope_limit':'법령 시행시점과 과세 원천을 가입자별로 확인해야 합니다.',
            'network_origin_independently_attested':False}
        z.update({'claim_id':E['claim_id'],'proposition':E['proposition'],'personal_or_effective_scope_approved':False,
                  'evidence':ev,'evidence_sha256':sha256(canonical(ev))})
        self.assertEqual(x.validate_row(z),'E-V5C0001')
        z['evidence_sha256']='0'*64
        with self.assertRaisesRegex(RunError,'THIRD_PASS_EVIDENCE_HASH_DRIFT'):x.validate_row(z)
    def test_official_rogue_host_rejected_even_with_consistent_hash(self):
        x,z=base('E-V5C0001','PRIMARY_RULE_TEXT_FOUND_APPLICABILITY_OPEN')
        ev={'official_url':'https://nts.go.kr.evil.invalid','exact_excerpt':'과세제외금액을 먼저 인출','source_type':'WEB_TOOL_VISIBLE_PRIMARY_EXCERPT',
            'observed_at':NOW,'date_and_scope_limit':'개인 별로 실제 세금 적용을 확인해야 합니다.',
            'network_origin_independently_attested':False}
        z.update({'claim_id':E['claim_id'],'proposition':E['proposition'],'personal_or_effective_scope_approved':False,
                  'evidence':ev,'evidence_sha256':sha256(canonical(ev))})
        with self.assertRaisesRegex(RunError,'THIRD_PASS_OFFICIAL_EVIDENCE_INCOMPLETE'):x.validate_row(z)
    def test_original_review_hash_changes_denied(self):
        x,z=base('E-V5C0001','PRIMARY_SOURCE_INSUFFICIENT_SCOPE_OPEN')
        z.update({'claim_id':E['claim_id'],'proposition':E['proposition'],'personal_or_effective_scope_approved':False,'evidence':None})
        z['prior_review_sha256']='f'*64
        with self.assertRaisesRegex(RunError,'THIRD_PASS_SOURCE_OR_PRIOR_REVIEW_CHANGED'):x.validate_row(z)

if __name__=='__main__':unittest.main()
