"""Synthetic cross-window quality regressions, independent of any real SRT."""
from __future__ import annotations
import unittest
from types import SimpleNamespace
from ire.source import sha256
from ire.v3_claim_quality import audit_claim_quality, save_private_quality_report

VID='TestVideo07'

def claim(text,modality='CONDITIONAL',types=('NUMERIC','MECHANISM'),amount='25만 원',unit='원'):
    return {
        'proposition':text,'claim_types':list(types),
        'frame':{'modality':modality,'measurements':[
            {'measure_kind':'추정 연금 증가액','unit':unit,'value_text':amount}]},
        'source_refs':[{'cue_index':1,'quote':'가상 연금 25만 원 증가'}]
    }

class FakeSession:
    def __init__(self, windows):
        self.windows=[{'window_id':w} for w in windows]
        self.by_window=windows
        self.video_id=VID
    def _answer(self,w):return self.by_window[w]
    def packet(self,w):return {'packet_sha256':sha256(w.encode()),'primary_cues':[]}

class FakeQueue:
    def __init__(self, windows):self.sessions=[FakeSession(windows)];self.windows=windows
    def status(self):return {'batch_fingerprint':sha256(b'synthetic'),
                              'accepted_windows':len(self.windows)}


def first():return claim('향후 7년 동안 보험료를 추가 납부하면 연금 증가분은 약 25만 원')
def later():return claim('추납으로 연금 증가분이 매월 25만 원 정도가 된다')

class CrossWindowClaimQualityTests(unittest.TestCase):
    def audit(self,first_claim=None,second_claim=None):
        a={'claims':([first_claim] if first_claim is not None else [])}
        b={'claims':([second_claim] if second_claim is not None else [])}
        return audit_claim_quality(FakeQueue({'W00001':a,'W00002':b}))
    def test_reused_benefit_with_different_contribution_cause_flagged(self):
        x=self.audit(first(),later())
        self.assertEqual(x['material_unresolved_causal_count'],1)
        self.assertEqual(x['risk_count'],1)
        self.assertEqual(x['issues'][0]['code'],'PENSION_INCREMENT_CAUSAL_BASIS_UNSEPARATED')
        self.assertEqual(x['issues'][0]['conditional_source_claim_ordinal'],1)
        self.assertFalse(x['research_integration_quality_approved'])
    def test_different_benefit_does_not_match(self):
        c=later();c['proposition']='추납으로 연금 증가분이 32만 원 정도가 된다'
        c['frame']['measurements'][0]['value_text']='32만 원'
        self.assertEqual(self.audit(first(),c)['risk_count'],0)
    def test_same_cause_stated_in_both_quotes_can_be_reviewed_directly(self):
        c=later();c['source_refs'][0]['quote']='앞서 7년 추가 납부한 뒤 연금 증가분이 25만 원'
        self.assertEqual(self.audit(first(),c)['risk_count'],0)
    def test_no_future_contribution_condition_means_no_cross_cause(self):
        c=first();c['proposition']='추납액 1,800만 원이면 증가분은 25만 원'
        self.assertEqual(self.audit(c,later())['risk_count'],0)
    def test_never_crosses_two_distinct_video_ids(self):
        q=FakeQueue({'W00001':{'claims':[first()]}})
        other=FakeSession({'W00002':{'claims':[later()]}})
        other.video_id='AnotherVideo07'
        q.sessions.append(other)
        self.assertEqual(audit_claim_quality(q)['risk_count'],0)
    def test_unknown_legal_rate_unit_requires_external_review(self):
        c=claim('연금소득 세율 후보 수치 5.5와 4.4를 언급',
                types=('REGULATION','NUMERIC'),amount='5.5',unit='단위 미명시')
        x=self.audit(c,None)
        self.assertEqual(x['regulatory_missing_unit_count'],1)
        self.assertEqual(x['issues'][0]['code'],'REGULATORY_NUMERIC_UNIT_UNESTABLISHED')
    def test_explicit_legal_rate_percent_unit_not_auto_verified(self):
        c=claim('연금소득 세율 후보 수치 5.5%를 언급',
                types=('REGULATION','NUMERIC'),amount='5.5%',unit='%')
        x=self.audit(c,None)
        self.assertEqual(x['regulatory_missing_unit_count'],0)
        self.assertFalse(x['actual_financial_truth_approved'])
    def test_provisional_conclusion_not_certified_even_when_no_risk(self):
        x=self.audit()
        self.assertTrue(x['risk_based_review_checks_clear'])
        self.assertFalse(x['research_integration_quality_approved'])
        self.assertFalse(x['independent_real_semantic_recall_certified'])
    def test_public_audit_does_not_copy_private_propositions(self):
        x=self.audit(first(),later())
        self.assertNotIn('향후 7년',str(x))
        self.assertNotIn('25만 원',str(x))
        self.assertEqual(len(x['issues'][0]['source_quotes_sha256']),64)
    def test_bounded_prior_window_prevents_unrelated_distant_match(self):
        q=FakeQueue({'W00001':{'claims':[first()]},'W00030':{'claims':[later()]}})
        self.assertEqual(audit_claim_quality(q)['risk_count'],0)
    def test_immutable_output_receipt_saved_without_source_text(self):
        import tempfile,pathlib,json
        with tempfile.TemporaryDirectory() as root:
            # The private directory must exist with owner-only permissions.
            path=pathlib.Path(root)/'sealed';path.mkdir(mode=0o700)
            x=self.audit(first(),later())
            saved=save_private_quality_report(x,str(path))
            self.assertTrue(pathlib.Path(saved).exists())
            self.assertEqual(json.loads(pathlib.Path(saved).read_text())['report_sha256'],x['report_sha256'])
            with self.assertRaises(FileExistsError):
                save_private_quality_report(x,str(path))

if __name__=='__main__':unittest.main()