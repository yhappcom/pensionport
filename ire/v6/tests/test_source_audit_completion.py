import copy, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.semantic_source_graph import compile_graph,source_grid
from ire.v6.semantic_authoring_protocol import compile_authoring,PROTOCOL_SHA256,occurrence_inventory
from ire.v6.source_first_audit import AUDIT_SHA256,freeze_source_ledger,audit_bidirectional
from ire.v6.source_audit_completion import (COMPLETION_SHA256,review_repeats,correction_candidate,typed_lineage)
from ire.v6.semantic_graph_journal import GraphJournal,plan_for,_edges
from ire.v6.tests.test_source_first_audit import fixture,descriptions
from ire.v6.tests.test_semantic_authoring_protocol import source,full


def correction_fixture():
    s,a,g,fr,l,lr,q=fixture()
    original=a['atoms'][0]['quantities'][0];assert original['role']=='CONTRIBUTION_BASE'
    a0=copy.deepcopy(a);a0['atoms'][0]['quantities'][0]['role']='TAX_AMOUNT'
    p,r0=compile_authoring(s,a0);g0=compile_graph(s,p)
    q0=copy.deepcopy(q);q0.update(first_graph_sha256=g0['packet_sha256'],first_receipt_sha256=json_digest(r0));q0['elements'][0]['edge_ids']=[json_digest({'field':'quantities','edge':a0['atoms'][0]['quantities'][0]})];q0['pairs'][0]['axes']['numeric_value_and_unit']=False;q0['pairs'][0].update(source_verdict='CONFLICT',first_verdict='CONFLICT')
    initial=audit_bidirectional(s,g0,a0,r0,l,lr,q0)
    h=next(iter(_edges(g0['nodes']['A00001'])));assert h in _edges(g['nodes']['A00001'])
    # Legacy projection identical but typed role changes; graph KEEP is not semantic approval.
    gl=[dict(old_ids=['A00001'],new_ids=['A00001'],operation='KEEP',reason='Legacy graph projection unchanged; typed correction tracked separately.',losses=[],carries=[dict(old_id='A00001',new_id='A00001',edge_sha256=h,reason='Literal edge unchanged.')])]
    tl=[dict(old=['A00001',q0['elements'][0]['edge_ids'][0]],new=['A00001',q['elements'][0]['edge_ids'][0]],verdict='REVIEW_CHANGED',reason='Correct erroneous tax amount role to contribution base.',evidence=[full(s,1)])]
    v=dict(completion_sha256=COMPLETION_SHA256,initial_score_sha256=json_digest(initial),ledger_sha256=lr['ledger_sha256'],authored=a,receipt=fr,assessment=q,graph_lineage=gl,typed_lineage=tl,repeat_reviews=[])
    return s,a0,g0,r0,l,lr,q0,initial,v


def repeat_fixture():
    s=source('매월 100만 원을 납입한다.','매월 100만 원을 납입한다.')
    ss=[full(s,1),full(s,2)];sp1,sp2=occurrence_inventory(s)
    q=dict(parts=[sp1],role='CONTRIBUTION_BASE',unit='원',anchor=[sp1],reason='Synthetic identical contribution amount.')
    ob=dict(id='O00001',predicate='매월 100만 원 납입.',nucleus=[ss[0]],context=[ss[1]],risk='HIGH',resolution='RESOLVED',reason='Synthetic repeated source obligation.',axes=descriptions(),quantities=[q],relations=[],temporal=[])
    l=dict(audit_sha256=AUDIT_SHA256,grid_sha256=json_digest(source_grid(s)),obligations=[ob],segments=[dict(span=ss[0],status='OBLIGATION',owners=['O00001'],reason='Synthetic original statement.'),dict(span=ss[1],status='REPEAT',owners=['O00001'],reason='Synthetic repeated statement.')],occurrences=[dict(span=sp1,status='QUANTITY',owners=['O00001'],reason='Synthetic original quantity.'),dict(span=sp2,status='REPEAT',owners=[],reason='Synthetic repeated quantity.')])
    rows=[dict(spans=[ss[1]],owner_ids=['O00001'],verdict='EQUIVALENT',axes=dict.fromkeys(MATCH_FIELDS,True),reasons=descriptions(),reason='Synthetic exact repeated statement, same role and scope.',numbers=[dict(span=sp2,owner_id='O00001',edge_sha256=json_digest(q),reason='Same literal contribution amount.')])]
    return s,l,rows

class CompletionTests(unittest.TestCase):
    def test_repeat_requires_review_and_numeric(self):
        s,l,r=repeat_fixture();self.assertEqual(review_repeats(s,l,r)['open_segments'],0)
        with self.assertRaisesRegex(InvalidInput,'REPEAT_CENSUS'):review_repeats(s,l,[])
        b=copy.deepcopy(r);b[0]['numbers']=[]
        with self.assertRaisesRegex(InvalidInput,'REPEAT_NUMBER_CENSUS'):review_repeats(s,l,b)
        b[0]['verdict']='DISTINCT';b[0]['axes']['conditions']=False
        self.assertEqual(review_repeats(s,l,b)['open_segments'],1)
    def test_repeat_changed_amount_not_equivalent(self):
        s,l,r=repeat_fixture();s=source('매월 100만 원을 납입한다.','매월 200만 원을 납입한다.');l['grid_sha256']=json_digest(source_grid(s))
        with self.assertRaisesRegex(InvalidInput,'REPEAT_NUMBER_LITERAL'):review_repeats(s,l,r)
    def test_repeat_unknown_owner_not_match(self):
        s,l,r=repeat_fixture();l['obligations'][0]['resolution']='OPEN'
        with self.assertRaisesRegex(InvalidInput,'REPEAT_UNCERTAIN_OWNER'):review_repeats(s,l,r)
    def test_correction_retains_initial_and_no_release(self):
        s,a,g,fr,l,lr,q,initial,v=correction_fixture();r=correction_candidate(s,g,a,fr,l,lr,initial,v)
        self.assertEqual(initial['tp'],0);self.assertEqual(r['corrected_score']['tp'],1);self.assertTrue(r['candidate_internal_thresholds_met']);self.assertFalse(r['original_score_changed']);self.assertFalse(r['publication_authorized'])
    def test_correction_pin_and_edge_census(self):
        s,a,g,fr,l,lr,q,initial,v=correction_fixture()
        for field,val,err in [('initial_score_sha256','0'*64,'CORRECTION_PINS'),('typed_lineage',[],'TYPED_LINEAGE_CENSUS'),('receipt',{},'CORRECTION_RECEIPT')]:
            bad={**v,field:val}
            with self.subTest(field=field),self.assertRaisesRegex(InvalidInput,err):correction_candidate(s,g,a,fr,l,lr,initial,bad)
        bad=copy.deepcopy(v);bad['typed_lineage'][0]['verdict']='CARRY'
        with self.assertRaisesRegex(InvalidInput,'TYPED_LINEAGE_FALSE_CARRY'):correction_candidate(s,g,a,fr,l,lr,initial,bad)
    def test_correction_risk_downgrade_blocked(self):
        s,a,g,fr,l,lr,q,initial,v=correction_fixture();v=copy.deepcopy(v)
        v['authored']['atoms'][0]['node']['risk']='NORMAL'
        p,v['receipt']=compile_authoring(s,v['authored']);gg=compile_graph(s,p)
        v['graph_lineage'][0]['operation']='REVISE'
        with self.assertRaisesRegex(InvalidInput,'CORRECTION_RISK_DOWNGRADE'):correction_candidate(s,g,a,fr,l,lr,initial,v)
    def test_correction_journal_and_rollback(self):
        s,a,g,fr,l,lr,q,initial,v=correction_fixture();r=correction_candidate(s,g,a,fr,l,lr,initial,v)
        with tempfile.TemporaryDirectory() as d,patch('ire.v6.semantic_graph_journal.verify_source',return_value=s):
            p=Path(d)/'j.sqlite';pins=dict(source_sha=s.source_sha256,manifest_sha=s.manifest_sha256)
            j=GraphJournal(p,b'',{},create=True,**pins);j.append('REGISTER',plan_for(s,campaign_id='completion-fixture',engine_commit='a'*40,registered_at='2026-11-25T08:00:00+09:00',purpose='DEVELOPMENT',protocol_sha256=PROTOCOL_SHA256,audit_sha256=AUDIT_SHA256));j.append('FIRST',dict(user_ref='first fixture',observed_at='2026-11-25T08:01:00+09:00',authored=a,receipt=fr));j.append('SOURCE_AUDIT_LEDGER',dict(user_ref='second fixture',observed_at='2026-11-25T08:02:00+09:00',ledger=l,receipt=lr));j.append('SOURCE_AUDIT_SCORE',dict(user_ref='second fixture',observed_at='2026-11-25T08:03:00+09:00',assessment=q,result=initial))
            before=j.snapshot();event=dict(user_ref='second fixture',observed_at='2026-11-25T08:04:00+09:00',candidate=v,result=r)
            with self.assertRaisesRegex(InvalidInput,'SAME_SECOND_TURN'):j.append('SOURCE_AUDIT_CANDIDATE',{**event,'user_ref':'third fixture'})
            self.assertEqual(j.snapshot(),before)
            h=j.append('SOURCE_AUDIT_CANDIDATE',event);snap=j.snapshot();self.assertEqual(snap['source_audit_score'],initial);self.assertEqual(snap['source_audit_candidate'],r);self.assertEqual(snap,GraphJournal(p,b'',{},expected_head=h,**pins).snapshot())
            with self.assertRaises(InvalidInput):j.append('REVISION',{})
