"""V188 synthetic full-census E3 readiness guards; not independent financial gold."""
import copy,os,sqlite3,tempfile,unittest
from ire.v6.errors import InvalidInput
from v183_e3_two_turn_audit import ANSWER_SCHEMA as SECOND_ANSWER
from v188_e3_quality_gate import evaluate_live,build_gate,SCHEMA
import test_v184_e3_adjudication as old

class TestV188E3QualityGate(unittest.TestCase):
    def setUp(self):
        # Reuse a prior synthetic hostile fixture without inheriting its tests.
        self.fix=old.TestAdjudication(methodName='test_packet_has_first_and_second_with_original_context')
        self.fix.setUp()
        self.addCleanup(self.fix.doCleanups)
        self.adj=self.fix.reviewer
        self.second=self.fix.audit
    def test_partial_source_census_cannot_certify(self):
        s=evaluate_live(self.adj)
        self.assertEqual(s['schema'],SCHEMA)
        self.assertEqual((s['source_cues'],s['second_cues'],s['second_unreviewed_cues']),(4,3,1))
        self.assertEqual(s['cause_labels_reviewed'],0)
        self.assertFalse(s['e3_accuracy_certified'])
        self.assertFalse(s['e4_invoked'])
    def test_zero_cause_backlog_is_not_accuracy_pass(self):
        p=self.adj.prepare(limit=2)
        self.adj.submit(p,self.fix.response(p))
        s=evaluate_live(self.adj)
        self.assertEqual(s['unclassified_disagreement_or_open_cues'],0)
        self.assertEqual(s['cause_labels_reviewed'],2)
        self.assertEqual(s['suspected_second_omission_cue_indices'],[1])
        self.assertIsNone(s['independent_gold_precision'])
        self.assertFalse(s['e3_accuracy_certified'])
        self.assertFalse(s['e4_approved'])
    def test_parent_candidates_not_automatically_equivalent(self):
        s=evaluate_live(self.adj)
        self.assertGreaterEqual(s['possible_parent_links'],0)
        self.assertTrue(s['first_and_second_original_journals_immutable'])
        self.assertTrue(s['open_issues_require_new_source_pinned_overlay'])
    def test_result_exposes_no_raw_owner_srt_or_financial_propositions(self):
        s=evaluate_live(self.adj)
        body=str(s)
        self.assertNotIn('ETF는 장점이 있습니다.',body)
        self.assertNotIn('손실이 있을 수',body)
        self.assertIn('source_sha256',s)
    def test_audit_does_not_touch_original_files(self):
        from pathlib import Path
        paths=[self.fix.owner,self.fix.second,self.fix.adj]
        stamps=[(Path(x).stat().st_size,Path(x).stat().st_mtime_ns) for x in paths]
        evaluate_live(self.adj)
        self.assertEqual(stamps,[(Path(x).stat().st_size,Path(x).stat().st_mtime_ns) for x in paths])
    def test_tamper_second_or_adjudication_detected(self):
        with sqlite3.connect(self.fix.second) as d:
            d.execute("UPDATE judgments SET record='{}' WHERE cue_index=1")
        with self.assertRaises(InvalidInput):evaluate_live(self.adj)
    def test_source_census_input_forgery_rejected(self):
        first=self.second._owner_snapshot()
        with self.second._db() as d: second_head,reviewed=self.second._audit(d)
        with self.adj._db() as d:adj_head,entries=self.adj._audit(d)
        kwargs=dict(source_cues=self.fix.eng.source.cues,first_rows=first,
             second_rows=reviewed,adjudication_rows=entries,
             source_sha256=self.fix.eng.source.source_sha256,
             first_head_sha256=self.second.expected_owner_head,
             second_head_sha256=second_head,adjudication_head_sha256=adj_head)
        with self.assertRaisesRegex(InvalidInput,'INDEPENDENCE_NOT_PROVEN'):
            build_gate(**kwargs,reviewer_source_independent=True)
        with self.assertRaisesRegex(InvalidInput,'CENSUS_OR_REVIEW_SUBSET_INVALID'):
            bad=dict(kwargs);bad['first_rows']={1:first[1]};build_gate(**bad)
    def test_second_can_complete_still_no_gold_or_E4(self):
        cue=self.second.prepare(limit=1)['target_cues'][0]
        p=self.second.prepare(limit=1)
        self.second.submit(p,{'schema':SECOND_ANSWER,'challenge_sha256':p['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':[{
              'cue_index':cue['cue_index'],'source_text_sha256':cue['source_text_sha256'],
              'disposition':'NON_RESEARCH','speaker_role':'HOST','claims':[],
              'analysis':'마지막 수사적 인사 문장이므로 독립 금융 사실로 추출하지 않았습니다.',
              'limitations_checked':True}]})
        s=evaluate_live(self.adj)
        self.assertEqual(s['second_unreviewed_cues'],0)
        self.assertFalse(s['e3_accuracy_certified'])
        self.assertFalse(s['e4_invoked'])
    def test_action_summary_is_stable_after_resume(self):
        p=self.adj.prepare(limit=2)
        self.adj.submit(p,self.fix.response(p))
        x=evaluate_live(self.adj)
        from v184_e3_adjudication import E3Adjudication
        y=evaluate_live(E3Adjudication(self.second,self.fix.adj))
        self.assertEqual(x,y)
if __name__=='__main__': unittest.main()