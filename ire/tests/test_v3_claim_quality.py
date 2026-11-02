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
    def test_full_queue_audit_exposes_quality_subreport(self):
        # Integration on a fresh synthetic original, not a fake queue.
        import tempfile,pathlib,json
        from ire.v3_orchestrator import ChatBatchQueue
        from ire.source import sha256
        with tempfile.TemporaryDirectory() as root:
            src=pathlib.Path(root)/"source.srt"
            raw=b"1\n00:00:00,000 --> 00:00:02,000\nHello.\n"
            src.write_bytes(raw)
            q=ChatBatchQueue({'schema':'IRE_V2_CHAT_BATCH_V1',
                 'research_as_of':'2026-11-02','videos':[{
                 'video_id':VID,'original_srt_path':str(src),
                 'source_sha256':sha256(raw),
                 'private_chat_sessions_path':str(pathlib.Path(root)/'session'),
                 'window_strategy':'V3_ADAPTIVE'}]})
            packet=q.next_work(max_packets=1,max_chars=18000)
            data=packet['packets'][0]['packet']
            answer={'schema':'IRE_CHAT_WINDOW_ANSWER_V1',
              'session_id':data['session_id'],'window_id':data['window_id'],
              'packet_sha256':data['packet_sha256'],'claims':[],
              'cue_dispositions':[{'cue_index':1,'status':'NONCLAIM_CANDIDATE',
                                   'reason':'Synthetic greeting only'}]}
            q.accept({'schema':'IRE_V3_CHAT_SUBMISSION_V1',
                      'batch_sha256':packet['batch_sha256'],
                      'max_packets':1,'max_chars':18000,
                      'answers':[{'video_id':VID,'submission':answer}]})
            report=q.audit_semantic_coverage()
            self.assertEqual(report['cross_window_claim_quality']['risk_count'],0)
            self.assertEqual(report['checked_windows'],1)
            from unittest.mock import patch
            from ire.v3_release import completion_gate
            fake_quality=dict(report['cross_window_claim_quality'])
            fake_quality.update(risk_count=2,material_unresolved_causal_count=1,
                regulatory_missing_unit_count=1)
            with patch.object(q,'audit_semantic_coverage',return_value={
                       **report,'cross_window_claim_quality':fake_quality}):
                gated=completion_gate(q)
                self.assertFalse(gated['source_semantic_census_complete'])
                self.assertIn('P0_UNSEPARATED_FINANCIAL_CAUSAL_BASIS',gated['blockers'])
                self.assertIn('P0_REGULATORY_NUMERIC_UNIT_NOT_SOURCE_ESTABLISHED',gated['blockers'])
                self.assertEqual(gated['cross_window_financial_causal_review_count'],1)
                out=q.finalize(str(pathlib.Path(root)/'kb'),
                               str(pathlib.Path(root)/'audit'))
                self.assertIsNone(out['knowledge_snapshot_sha256'])
                self.assertEqual(out['quality_gate'],
                    'V3_CROSS_WINDOW_CAUSAL_AND_REGULATORY_REVIEW_BLOCKED')
                self.assertFalse((pathlib.Path(root)/'kb').exists())
                # Legacy V2 CLI must not bypass a V3_ADAPTIVE quality block.
                from ire.v2_run import finalize_batch
                with patch('ire.v3_claim_quality.audit_claim_quality',
                           return_value=fake_quality):
                    blocked=finalize_batch(q.manifest,None,
                        str(pathlib.Path(root)/'legacy_kb'),
                        str(pathlib.Path(root)/'legacy_audit'))
                self.assertEqual(blocked['final_research_status'],
                                 'INCOMPLETE_REQUIRES_RESUME')
                self.assertIn('V3_ADAPTIVE_CROSS_WINDOW_CLAIM_QUALITY_PENDING',
                              blocked['blockers'])
                self.assertIsNone(blocked['knowledge_next_snapshot_sha256'])

    def test_effective_answer_revision_changes_audit_hash_without_changing_risk(self):
        c=first();q=FakeQueue({'W00001':{'claims':[c]},'W00002':{'claims':[later()]}})
        a=audit_claim_quality(q)
        c['proposition']='향후 7년간 보험료 추가 납부 시 연금 증가분이 25만 원으로 추정'
        b=audit_claim_quality(q)
        self.assertEqual((a['risk_count'],b['risk_count']),(1,1))
        self.assertNotEqual(a['report_sha256'],b['report_sha256'])
        self.assertNotEqual(a['audited_effective_answer_set_sha256'],
                            b['audited_effective_answer_set_sha256'])
        self.assertEqual(a['issues'][0]['source_quotes_sha256'],
                         b['issues'][0]['source_quotes_sha256'])
        self.assertNotEqual(a['issues'][0]['conditional_effective_answer_sha256'],
                            b['issues'][0]['conditional_effective_answer_sha256'])
        self.assertNotIn('향후 7년',str(b))

    def test_stale_report_cannot_be_sealed_after_corrected_answer(self):
        import tempfile,pathlib
        c=first();q=FakeQueue({'W00001':{'claims':[c]},'W00002':{'claims':[later()]}})
        a=audit_claim_quality(q)
        c['proposition']='향후 7년 보험료를 추가 납부하면 연금 증가액은 25만 원'
        with tempfile.TemporaryDirectory() as root:
            folder=pathlib.Path(root)/'sealed';folder.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError,'STALE_OR_NOT_SOURCE_REPRODUCIBLE'):
                save_private_quality_report(a,str(folder),q)
            self.assertEqual(list(folder.iterdir()),[])
            b=audit_claim_quality(q)
            self.assertTrue(pathlib.Path(save_private_quality_report(b,str(folder),q)).exists())

    def test_forged_self_consistent_quality_receipt_does_not_pass_source_replay(self):
        import tempfile,pathlib
        from ire.v3_claim_quality import _canon
        q=FakeQueue({'W00001':{'claims':[first()]},'W00002':{'claims':[later()]}})
        x=audit_claim_quality(q)
        y=dict(x);y['risk_count']=0;y['issues']=[]
        y['report_sha256']=sha256(_canon({k:v for k,v in y.items() if k!='report_sha256'}))
        with tempfile.TemporaryDirectory() as root:
            folder=pathlib.Path(root)/'sealed';folder.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError,'STALE_OR_NOT_SOURCE_REPRODUCIBLE'):
                save_private_quality_report(y,str(folder),q)
            self.assertEqual(list(folder.iterdir()),[])

    def test_nonrisk_answer_revision_also_changes_audit_identity(self):
        c=claim('해당 영상에서 사례 설명',types=('OPINION',),amount='1만 원')
        q=FakeQueue({'W00001':{'claims':[c]}})
        a=audit_claim_quality(q)
        self.assertEqual(a['risk_count'],0)
        c['proposition']='해당 영상에서는 다른 사례를 설명'
        b=audit_claim_quality(q)
        self.assertEqual(b['risk_count'],0)
        self.assertNotEqual(a['report_sha256'],b['report_sha256'])

    def test_immutable_output_receipt_saved_without_source_text(self):
        import tempfile,pathlib,json
        with tempfile.TemporaryDirectory() as root:
            # The private directory must exist with owner-only permissions.
            path=pathlib.Path(root)/'sealed';path.mkdir(mode=0o700)
            x=self.audit(first(),later())
            saved=save_private_quality_report(x,str(path),FakeQueue({'W00001':{'claims':[first()]},'W00002':{'claims':[later()]}}))
            self.assertTrue(pathlib.Path(saved).exists())
            self.assertEqual(json.loads(pathlib.Path(saved).read_text())['report_sha256'],x['report_sha256'])
            with self.assertRaises(FileExistsError):
                save_private_quality_report(x,str(path),FakeQueue({'W00001':{'claims':[first()]},'W00002':{'claims':[later()]}}))

if __name__=='__main__':unittest.main()