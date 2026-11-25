"""Repeated successor and byte-chain cache tests using a synthetic source."""
import copy, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_graph_journal import GraphJournal, plan_for, successor_amendment, _edges
from ire.v6.tests import test_general_successor as gen
from ire.v6.tests import test_qualifier_gap_review as fixture

class SuccessorAmendmentTests(unittest.TestCase):
    def setUp(self):
        t=fixture.QualifierGapReviewTests();t.setUp();_,r=t.check()
        g=gen.GeneralSuccessorTests();g.setUp();self.g=g;self.source=t.f.s
        pins=dict(expected_head=t.head,expected_gap_receipt_sha256=json_digest(r),**t.pins)
        self.legacy=dict(packet=t.packet,old=t.f.old,candidates=t.c,events=[],rows=t.rows,scopes=t.scopes,pins=pins,plan=g.plan,plan_sha256=json_digest(g.plan))
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'journal.sqlite'
        self.mock=patch('ire.v6.semantic_graph_journal.verify_source',return_value=self.source);self.mock.start();self.addCleanup(self.mock.stop)
        self.kw=dict(source_sha=self.source.source_sha256,manifest_sha=self.source.manifest_sha256)
        self.j=GraphJournal(self.path,b'',{},create=True,**self.kw)
        self.j.append('REGISTER',plan_for(self.source,campaign_id='synthetic-amendment',engine_commit='a'*40,registered_at='2026-11-25T08:13:00+09:00',purpose='DEVELOPMENT'))
        self.j.append('LEGACY_RECONCILIATION',self.legacy)
        self.packet=g.packet
        self.j.append('SUCCESSOR',dict(packet=self.packet,lineage=g.lineage,new_edges=[],receipt=g.run_revision()))

    def proposal(self, label):
        c=self.j.amendment_context();p=copy.deepcopy(self.packet)
        p['nodes'][0]['predicate']=label
        lin=[dict(old_ids=[n],new_ids=[n],operation='REVISE',reason='Synthetic successive predicate review.',losses=[],carries=[dict(old_id=n,new_id=n,edge_sha256=h,reason='Synthetic unchanged source edge.') for h in _edges(v)]) for n,v in c['parent']['nodes'].items()]
        r=successor_amendment(self.source,c['parent'],c['projected_plan'],c['prior_receipt'],p,lin,[])
        return dict(packet=p,lineage=lin,new_edges=[],receipt=r)

    def test_repeat_and_reopen(self):
        first=self.proposal('첫 번째 합성 재검토 문장');h=self.j.append('SUCCESSOR_AMENDMENT',first);self.packet=first['packet']
        self.assertEqual(self.j.append('SUCCESSOR_AMENDMENT',first),h)
        second=self.proposal('두 번째 합성 재검토 문장');end=self.j.append('SUCCESSOR_AMENDMENT',second)
        self.assertNotEqual(end,h);self.assertEqual(self.j.snapshot()['event_count'],5)
        self.assertEqual(second['receipt']['prior_receipt_sha256'],json_digest(first['receipt']))
        self.assertEqual(self.j.snapshot()['successor']['scope_drafts'],1)
        reopened=GraphJournal(self.path,b'',{},expected_head=end,**self.kw)
        self.assertEqual(reopened.snapshot(),self.j.snapshot())
        with self.assertRaises(InvalidInput):self.j.append('SUCCESSOR_AMENDMENT',first)

    def test_mutable_inputs_and_outputs(self):
        v=self.proposal('합성 재검토 결과 문장');self.j.append('SUCCESSOR_AMENDMENT',v)
        v['receipt']['ready_for_e3']=True
        s=self.j.snapshot();s['successor']['ready_for_e3']=True
        c=self.j.amendment_context();c['prior_receipt']['ready_for_e3']=True
        self.assertFalse(self.j.snapshot()['successor']['ready_for_e3'])

    def test_cached_prefix_tamper_rejected(self):
        self.j.snapshot()
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER immutable_update')
            db.execute('UPDATE events SET payload=? WHERE seq=2',(b'{}',))
        with self.assertRaises(InvalidInput):self.j.snapshot()

    def test_failed_amendment_keeps_state(self):
        v=self.proposal('합성 재검토 새 문장');v['receipt']['prior_receipt_sha256']='0'*64
        before=self.j.snapshot()
        with self.assertRaises(InvalidInput):self.j.append('SUCCESSOR_AMENDMENT',v)
        self.assertEqual(self.j.snapshot(),before)
