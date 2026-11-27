import copy
import tempfile
import unittest
from pathlib import Path
from engine import digest
from d4_quality import ContextEngine, assess, FIELDS

class Tests(unittest.TestCase):
    def atom(self, id, risk='H'):
        return dict(id=id,cues=[1],risk=risk,**{f:'explicit '+f for f in FIELDS})
    def packet(self, atoms):
        return dict(source_id='source',unit='ATOM',atomization_reviewed=True,atoms=atoms)
    def review(self,o,r,partial=None):
        return dict(output=o,reference=r,reason='manual fixture',fields={f:f!=partial for f in FIELDS})
    def score(self, r, o, m):
        return assess(r,o,m,digest(r),'source',1)
    def test_exact(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')])
        self.assertTrue(self.score(r,o,[self.review('o','r')])['threshold_met'])
    def test_partial_high_risk(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')])
        s=self.score(r,o,[self.review('o','r','exceptions')]); self.assertEqual(s['recall'],0); self.assertEqual(s['high_risk_missed'],['r'])
    def test_duplicate(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o1'),self.atom('o2')])
        s=self.score(r,o,[self.review('o1','r'),self.review('o2','r')]); self.assertEqual(s['precision'],.5); self.assertEqual(s['recall'],1)
    def test_added_claim(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o1'),self.atom('o2')])
        self.assertEqual(self.score(r,o,[self.review('o1','r'),self.review('o2',None)])['extra'],['o2'])
    def test_group_rejected(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')]); r['unit']='GROUP'
        with self.assertRaises(ValueError): self.score(r,o,[self.review('o','r')])
    def test_unreviewed(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')])
        with self.assertRaises(ValueError): self.score(r,o,[])
    def test_changed_reference(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')])
        with self.assertRaises(ValueError): assess(r,o,[self.review('o','r')],'wrong','source',1)
    def test_invalid_anchor(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')]); o['atoms'][0]['cues']=[2]
        with self.assertRaises(ValueError): self.score(r,o,[self.review('o','r')])
    def test_duplicate_id(self):
        r,o=self.packet([self.atom('r'),self.atom('r')]),self.packet([self.atom('o')])
        with self.assertRaises(ValueError): self.score(r,o,[self.review('o','r')])
    def test_missing_field(self):
        r,o=self.packet([self.atom('r')]),self.packet([self.atom('o')]); m=self.review('o','r'); del m['fields']['exceptions']
        with self.assertRaises(ValueError): self.score(r,o,[m])
    def test_context_graph(self):
        with tempfile.TemporaryDirectory() as d:
            e=ContextEngine(Path(d)/'test.db','test')
            # Isolate graph logic; real stored records are tested separately.
            cat={k:dict(qualified_id=k,knowledge=k,topic=k,conditions=[],exceptions=[],relations=[],depends_on=[],verdict='APPROVE') for k in ['seed','context','limit','unrelated']}
            cat['hold']=dict(cat['limit'],qualified_id='hold',verdict='HOLD')
            e.catalog=lambda c:cat
            def edge(a,b): return {'from':a,'to':b,'kind':'CONDITION','reason':'fixture','from_sha':digest(cat[a]),'to_sha':digest(cat[b])}
            reg=dict(head=e.status()['head'],reviewed=True,edges=[edge('seed','context'),edge('context','limit'),edge('limit','seed')])
            result=e.query_context(['seed'],reg)
            self.assertEqual({x['qualified_id'] for x in result['context']},{'context','limit'})
            self.assertEqual(e.query_context(['no-match'],reg)['context'],[])
            self.assertEqual(e.query_context(['unrelated'],reg)['context'],[])
            for bad in [dict(reg,head='stale'),dict(reg,reviewed=False),dict(reg,edges=[edge('seed','hold')]),dict(reg,edges=[dict(edge('seed','context'),to_sha='wrong')]),dict(reg,edges=[dict(edge('seed','context'),kind='DISTINCT')]),dict(reg,edges=[edge('seed','context')]*2)]:
                with self.assertRaises(ValueError): e.query_context(['seed'],bad)

if __name__=='__main__': unittest.main()
