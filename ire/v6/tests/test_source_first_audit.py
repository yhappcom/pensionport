import copy, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.semantic_authoring_protocol import PROTOCOL_SHA256, compile_authoring
from ire.v6.semantic_graph_journal import GraphJournal, plan_for
from ire.v6.semantic_source_graph import compile_graph,source_grid
from ire.v6.source_first_audit import AUDIT_SHA256,freeze_source_ledger,audit_bidirectional
from ire.v6.tests.test_semantic_authoring_protocol import source,packet,full


def descriptions():return dict.fromkeys(MATCH_FIELDS,'Explicit synthetic reviewed dimension.')

def fixture():
    s=source('매월 100만 원을 납입한다.')
    authored=packet(s);p,r=compile_authoring(s,authored);g=compile_graph(s,p);a=authored['atoms'][0]
    row=dict(id='O00001',predicate=a['node']['predicate'],nucleus=a['node']['direct'],context=[],risk='HIGH',resolution='RESOLVED',reason='Synthetic elementary source obligation.',axes=descriptions(),quantities=a['quantities'],relations=[],temporal=[])
    ledger=dict(audit_sha256=AUDIT_SHA256,grid_sha256=json_digest(source_grid(s)),obligations=[row],segments=[dict(span=full(s,1),status='OBLIGATION',owners=['O00001'],reason='Synthetic source nucleus.')],occurrences=[dict(span=q['span'],status='QUANTITY',owners=['O00001'],reason='Synthetic quantity owner.') for q in authored['occurrences']])
    lr=freeze_source_ledger(s,ledger)
    el=dict(id='P00001',parent_id='A00001',predicate=a['node']['predicate'],evidence=a['node']['direct'],risk='HIGH',reason='Synthetic proposition decomposition.',axes=descriptions(),edge_ids=sorted(json_digest({'field':'quantities','edge':q}) for q in a['quantities']))
    pair=dict(source_id='O00001',first_id='P00001',axes=dict.fromkeys(MATCH_FIELDS,True),reasons=descriptions(),source_evidence=row['nucleus'],first_evidence=el['evidence'],source_verdict='PRESERVED',first_verdict='SUPPORTED',relation_pairs=[])
    assessment=dict(first_graph_sha256=g['packet_sha256'],first_receipt_sha256=json_digest(r),ledger_sha256=lr['ledger_sha256'],elements=[el],pairs=[pair],source_unmatched=[],first_unmatched=[])
    return s,authored,g,r,ledger,lr,assessment

class SourceAuditTests(unittest.TestCase):
    def setUp(self):self.s,self.a,self.g,self.r,self.l,self.lr,self.q=fixture()
    def check(self,q=None,l=None,lr=None):return audit_bidirectional(self.s,self.g,self.a,self.r,self.l if l is None else l,self.lr if lr is None else lr,self.q if q is None else q)
    def test_complete_pair_not_release(self):
        r=self.check();self.assertEqual(r['tp'],1);self.assertTrue(r['internal_thresholds_met']);self.assertFalse(r['publication_authorized']);self.assertFalse(r['independent_gold_verified'])
    def test_source_censuses(self):
        for k in ('segments','obligations','occurrences'):
            l=copy.deepcopy(self.l);l[k]=[]
            with self.subTest(k=k),self.assertRaises(InvalidInput):freeze_source_ledger(self.s,l)
    def test_both_directions_and_custody(self):
        for k in ('elements','pairs'):
            q=copy.deepcopy(self.q);q[k]=[]
            with self.subTest(k=k),self.assertRaises(InvalidInput):self.check(q)
        q=copy.deepcopy(self.q);q['elements'][0]['edge_ids']=[]
        with self.assertRaisesRegex(InvalidInput,'FIRST_EDGE_CENSUS'):self.check(q)
        q=copy.deepcopy(self.q);q['elements'][0]['risk']='NORMAL'
        with self.assertRaisesRegex(InvalidInput,'RISK_DOWNGRADE'):self.check(q)
        q=copy.deepcopy(self.q);q['pairs'][0]['first_verdict']='OPEN'
        with self.assertRaisesRegex(InvalidInput,'RECIPROCAL_VERDICT'):self.check(q)
    def test_wrong_role_no_match(self):
        l=copy.deepcopy(self.l);l['obligations'][0]['quantities'][0]['role']='TAX_AMOUNT';lr=freeze_source_ledger(self.s,l)
        q=copy.deepcopy(self.q);q['ledger_sha256']=lr['ledger_sha256']
        with self.assertRaisesRegex(InvalidInput,'CONTRADICTORY_QUANTITIES'):self.check(q,l,lr)
        q['pairs'][0]['axes']['numeric_value_and_unit']=False;q['pairs'][0].update(source_verdict='CONFLICT',first_verdict='CONFLICT')
        r=self.check(q,l,lr);self.assertEqual((r['tp'],r['fp'],r['fn']),(0,1,1));self.assertFalse(r['internal_thresholds_met'])
    def test_missing_unsupported_separate(self):
        q=copy.deepcopy(self.q);q['pairs']=[]
        q['source_unmatched']=[dict(id='O00001',verdict='MISSING',reason='Synthetic missing meaning.',evidence=[full(self.s,1)])]
        q['first_unmatched']=[dict(id='P00001',verdict='UNSUPPORTED',reason='Synthetic unsupported addition.',evidence=[full(self.s,1)])]
        r=self.check(q);self.assertEqual((r['tp'],r['fp'],r['fn']),(0,1,1));self.assertEqual(r['high_risk_source_unmatched_or_conflict'],1);self.assertEqual(r['high_risk_first_unmatched_or_conflict'],1)
    def test_open_never_passes(self):
        l=copy.deepcopy(self.l);l['occurrences'][0]['status']='OPEN';lr=freeze_source_ledger(self.s,l);q=copy.deepcopy(self.q);q['ledger_sha256']=lr['ledger_sha256'];r=self.check(q,l,lr)
        self.assertEqual(r['tp'],1);self.assertFalse(r['internal_thresholds_met'])
    def test_journal_gate_order_replay(self):
        with tempfile.TemporaryDirectory() as d,patch('ire.v6.semantic_graph_journal.verify_source',return_value=self.s):
            p=Path(d)/'journal.sqlite';pins=dict(source_sha=self.s.source_sha256,manifest_sha=self.s.manifest_sha256)
            j=GraphJournal(p,b'',{},create=True,**pins)
            plan=plan_for(self.s,campaign_id='source-audit',engine_commit='a'*40,registered_at='2026-11-25T08:00:00+09:00',purpose='DEVELOPMENT',protocol_sha256=PROTOCOL_SHA256,audit_sha256=AUDIT_SHA256)
            j.append('REGISTER',plan);j.append('FIRST',dict(user_ref='first turn',observed_at='2026-11-25T08:01:00+09:00',authored=self.a,receipt=self.r))
            with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_LEDGER_REQUIRED'):j.source_audit_context()
            with self.assertRaises(InvalidInput):j.append('SECOND',{})
            with self.assertRaises(InvalidInput):j.append('SOURCE_AUDIT_SCORE',{})
            v=dict(user_ref='second turn',observed_at='2026-11-25T08:02:00+09:00',ledger=self.l,receipt=self.lr)
            with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_TURN_ORDER'):j.append('SOURCE_AUDIT_LEDGER',{**v,'user_ref':'first turn'})
            j.append('SOURCE_AUDIT_LEDGER',v);self.assertEqual(j.source_audit_context()['first'],self.g)
            r=self.check();v=dict(user_ref='second turn',observed_at='2026-11-25T08:03:00+09:00',assessment=self.q,result=r)
            with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_SAME_SECOND_TURN'):j.append('SOURCE_AUDIT_SCORE',{**v,'user_ref':'third turn'})
            h=j.append('SOURCE_AUDIT_SCORE',v);self.assertEqual(j.snapshot(),GraphJournal(p,b'',{},expected_head=h,**pins).snapshot());self.assertIsNone(j.snapshot()['score']);self.assertEqual(j.snapshot()['source_audit_score'],r)
            with self.assertRaises(InvalidInput):j.append('REVISION',{})
    def test_grouped_condition_and_exception_custody(self):
        s=source('소득이 있다면','매월 납입한다.')
        a=packet(s);a['atoms'][0]['quantities']=[];a['atoms'][0]['node']['direct']=[full(s,2)];a['segments'][0]['status']='SUPPORT'
        edge=dict(type='CONDITION',premise=[full(s,1)],consequent=[full(s,2)],reason='Synthetic condition applies to payment.')
        a['atoms'][0]['relations']=[edge]
        p,r=compile_authoring(s,a);g=compile_graph(s,p)
        o=dict(id='O00001',predicate='소득이 있다면 납입한다.',nucleus=[full(s,2)],context=[full(s,1)],risk='HIGH',resolution='RESOLVED',reason='Synthetic grouped condition.',axes=descriptions(),quantities=[],relations=[edge],temporal=[])
        l=dict(audit_sha256=AUDIT_SHA256,grid_sha256=json_digest(source_grid(s)),obligations=[o],segments=[dict(span=full(s,1),status='CONTEXT',owners=['O00001'],reason='Synthetic premise.'),dict(span=full(s,2),status='OBLIGATION',owners=['O00001'],reason='Synthetic consequence.')],occurrences=[])
        lr=freeze_source_ledger(s,l);h=json_digest({'field':'relations','edge':edge})
        el=dict(id='P00001',parent_id='A00001',predicate=o['predicate'],evidence=[full(s,1),full(s,2)],risk='HIGH',reason='Synthetic first proposition.',axes=descriptions(),edge_ids=[h])
        pair=dict(source_id='O00001',first_id='P00001',axes=dict.fromkeys(MATCH_FIELDS,True),reasons=descriptions(),source_evidence=[full(s,1),full(s,2)],first_evidence=el['evidence'],source_verdict='PRESERVED',first_verdict='SUPPORTED',relation_pairs=[dict(first_edge_sha256=h,source_edge_sha256=json_digest(edge),reason='Explicit same condition and consequence.')])
        q=dict(first_graph_sha256=g['packet_sha256'],first_receipt_sha256=json_digest(r),ledger_sha256=lr['ledger_sha256'],elements=[el],pairs=[pair],source_unmatched=[],first_unmatched=[])
        self.assertTrue(audit_bidirectional(s,g,a,r,l,lr,q)['internal_thresholds_met'])
        for field,value,reason in [('source_evidence',[full(s,2)],'PAIR_EDGE_EVIDENCE'),('relation_pairs',[],'RELATION_PAIR_CENSUS')]:
            bad=copy.deepcopy(q);bad['pairs'][0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(InvalidInput,reason):audit_bidirectional(s,g,a,r,l,lr,bad)
        wrong=copy.deepcopy(l);wrong['obligations'][0]['relations'][0]['type']='EXCEPTION';wr=freeze_source_ledger(s,wrong);bad=copy.deepcopy(q);bad['ledger_sha256']=wr['ledger_sha256']
        with self.assertRaisesRegex(InvalidInput,'CONTRADICTORY_RELATION'):audit_bidirectional(s,g,a,r,wrong,wr,bad)
    def test_unresolved_cannot_be_perfect(self):
        l=copy.deepcopy(self.l);l['obligations'][0]['resolution']='OPEN';lr=freeze_source_ledger(self.s,l);q=copy.deepcopy(self.q);q['ledger_sha256']=lr['ledger_sha256']
        with self.assertRaisesRegex(InvalidInput,'UNRESOLVED_MATCH'):self.check(q,l,lr)
    def test_duplicate_pairs_rejected(self):
        q=copy.deepcopy(self.q);q['pairs'].append(q['pairs'][0])
        with self.assertRaisesRegex(InvalidInput,'PAIR_PARTITION'):self.check(q)
    def test_no_prospective_gate_yet(self):
        with self.assertRaisesRegex(InvalidInput,'SOURCE_AUDIT_PROSPECTIVE_NOT_AUTHORIZED'):plan_for(self.s,campaign_id='new-holdout',engine_commit='a'*40,registered_at='2026-11-25T08:00:00+09:00',purpose='HOLDOUT',protocol_sha256=PROTOCOL_SHA256,audit_sha256=AUDIT_SHA256)
