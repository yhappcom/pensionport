import copy, tempfile, unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_authoring_protocol import PROTOCOL_SHA256
from ire.v6.source_first_audit import AUDIT_SHA256, audit_bidirectional
from ire.v6.semantic_graph_journal import (GraphJournal,plan_for,prospective_diagnostic,PROSPECTIVE_PURPOSE,PROSPECTIVE_SHA256,PROSPECTIVE_EXPOSED_IDS,PROSPECTIVE_EXPOSED_SHAS)
from ire.v6.tests.test_source_first_audit import fixture
from ire.v6.tests.test_source_audit_completion import repeat_fixture
from ire.v6.source_first_audit import freeze_source_ledger

class ProspectiveAuditTests(unittest.TestCase):
    def setUp(self):self.s,self.a,self.g,self.r,self.l,self.lr,self.q=fixture()
    def plan(self,source=None,**kw):
        return plan_for(source or self.s,**(dict(campaign_id='prospective-diagnostic',engine_commit='a'*40,registered_at='2026-11-25T08:00:00+09:00',purpose=PROSPECTIVE_PURPOSE,protocol_sha256=PROTOCOL_SHA256,audit_sha256=AUDIT_SHA256,screening_sha256='b'*64)|kw))
    def test_plan_pins_and_exposed_ids_hashes(self):
        self.assertEqual(self.plan()['prospective_policy_sha256'],PROSPECTIVE_SHA256)
        for v in (None,'0'*64,'wrong'):
            with self.subTest(v=v),self.assertRaisesRegex(InvalidInput,'PROSPECTIVE_SCREENING_PIN'):self.plan(screening_sha256=v)
        for v in PROSPECTIVE_EXPOSED_IDS:
            with self.subTest(v=v),self.assertRaisesRegex(InvalidInput,'PROSPECTIVE_EXPOSED_SOURCE'):self.plan(replace(self.s,video_id=v))
        for v in PROSPECTIVE_EXPOSED_SHAS:
            with self.subTest(v=v),self.assertRaisesRegex(InvalidInput,'PROSPECTIVE_EXPOSED_SOURCE'):self.plan(replace(self.s,source_sha256=v))
        with self.assertRaisesRegex(InvalidInput,'PROSPECTIVE_AUDIT_REQUIRED'):self.plan(audit_sha256=None)
        with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_PROSPECTIVE_NOT_AUTHORIZED'):self.plan(purpose='HOLDOUT',screening_sha256=None)
    def test_high_risk_and_repeat_blockers(self):
        score=audit_bidirectional(self.s,self.g,self.a,self.r,self.l,self.lr,self.q)
        self.assertTrue(prospective_diagnostic(self.s,self.plan(),self.l,score,[])['diagnostic_thresholds_met'])
        l=copy.deepcopy(self.l);l['obligations'][0]['risk']='NORMAL';lr=freeze_source_ledger(self.s,l)
        q=copy.deepcopy(self.q);q['ledger_sha256']=lr['ledger_sha256'];score=audit_bidirectional(self.s,self.g,self.a,self.r,l,lr,q)
        self.assertFalse(prospective_diagnostic(self.s,self.plan(),l,score,[])['diagnostic_thresholds_met'])
        s,l,rows=repeat_fixture();lr=freeze_source_ledger(s,l)
        # Standalone diagnostic input is a synthetic score stub; real journal recomputes score.
        score={'ledger_sha256':lr['ledger_sha256'],'internal_thresholds_met':True}
        with self.assertRaisesRegex(InvalidInput,'REPEAT_CENSUS'):prospective_diagnostic(s,self.plan(s),l,score,[])
        rows[0]['verdict']='OPEN';rows[0]['axes']['conditions']=False
        self.assertFalse(prospective_diagnostic(s,self.plan(s),l,score,rows)['diagnostic_thresholds_met'])
    def test_journal_prospective_replay_no_release(self):
        with tempfile.TemporaryDirectory() as d,patch('ire.v6.semantic_graph_journal.verify_source',return_value=self.s):
            p=Path(d)/'j.sqlite';pins=dict(source_sha=self.s.source_sha256,manifest_sha=self.s.manifest_sha256)
            j=GraphJournal(p,b'',{},create=True,**pins);plan=self.plan();j.append('REGISTER',plan)
            j.append('FIRST',dict(user_ref='first user turn',observed_at='2026-11-25T08:01:00+09:00',authored=self.a,receipt=self.r))
            with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_LEDGER_REQUIRED'):j.source_audit_context()
            j.append('SOURCE_AUDIT_LEDGER',dict(user_ref='second user turn',observed_at='2026-11-25T08:02:00+09:00',ledger=self.l,receipt=self.lr))
            score=audit_bidirectional(self.s,self.g,self.a,self.r,self.l,self.lr,self.q)
            v=dict(user_ref='second user turn',observed_at='2026-11-25T08:03:00+09:00',assessment=self.q,result=score)
            h=j.head
            with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_SCORE_SHAPE'):j.append('SOURCE_AUDIT_SCORE',v)
            self.assertEqual(j.head,h)
            v.update(repeat_reviews=[],diagnostic=prospective_diagnostic(self.s,plan,self.l,score,[]))
            bad=copy.deepcopy(v);bad['diagnostic']['publication_authorized']=True
            with self.assertRaisesRegex(InvalidInput,'PROSPECTIVE_DIAGNOSTIC_DRIFT'):j.append('SOURCE_AUDIT_SCORE',bad)
            h=j.append('SOURCE_AUDIT_SCORE',v);snap=j.snapshot()
            self.assertEqual(snap,GraphJournal(p,b'',{},expected_head=h,**pins).snapshot())
            self.assertTrue(snap['prospective_diagnostic']['diagnostic_thresholds_met']);self.assertFalse(snap['publication_authorized']);self.assertFalse(snap['operational_release_authorized'])
            with self.assertRaises(InvalidInput):j.append('REVISION',{})
