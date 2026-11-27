"""Executable structural tests. Fixture manual judgments, not semantic inference."""
import copy, tempfile, unittest, sqlite3
from pathlib import Path
from engine import Engine, digest, sha
from d4_gate import GateEngine, FIN_FIELDS
from d4_quality import FIELDS
from d4_gate_v2 import ObligationGate, output_units, evaluate, render, reconcile_nonclaim, METHOD, CORE, QUAL
from test_d4_gate import raw, claim, packet, query, edge


def fields(token):
    return dict(proposition=token,subject='fixture subject',speaker_stance='fixture FACT',polarity='affirmed',conditions='fixture condition',exceptions='NONE',numbers_units='NONE',time_scope='fixture only')
def part(u,cues,token=None,subset=None):
    f=fields(token or u); f={k:v for k,v in f.items() if subset is None or k in subset}
    return dict(unit=u,fields=f,cues=cues,risk='H' if CORE<=set(f) else None)
def row(k,parts,verdict='CONTEXT',token=None,**kw):
    x=claim(k,parts[0]['cues'][0],token or k,verdict=verdict,**kw); x.pop('source_atom'); x['source_components']=parts; x['cues']=sorted({i for p in parts for i in p['cues']}); x['statement']=render(parts); return x
def refresh(x):x['statement']=render(x['source_components'])
def ref(u,cues,token=None,risk='H'):
    return dict(id='R'+u,**fields(token or u),cues=cues,risk=risk)
def refs(p,atoms):
    return dict(source_id=p['source_id'],unit='ATOM',method=METHOD,atomization_reviewed=True,atoms=atoms,nonclaim_cues=[i for x in p['nonclaim'] for i in x['cues']])
def review(p,r,overrides=None):
    lookup={x['id']:x for x in r['atoms']}; out=output_units(p,2)['atoms']; result=[]
    for a in out:
        k=a['id']; match=lookup.get('R'+k); v=dict(output=k,reference=match['id'] if match else None,output_sha=digest(a),reference_sha=digest(match) if match else None,reason='synthetic manual judgment',fields={f: bool(match and a[f]==match[f]) for f in FIELDS},anchor_sufficient=bool(match and set(a['cues'])==set(match['cues'])))
        if overrides and k in overrides:v.update(overrides[k])
        result.append(v)
    return result

def finance(p):
    return {a['owner']:dict(claim_sha=digest(next(x for x in p['claims'] if x['id']==a['owner'])),meaning_sha=digest(a),reason='synthetic evidence checks',checks={f:True for f in FIN_FIELDS}) for a in output_units(p,2)['atoms'] if next(x for x in p['claims'] if x['id']==a['owner'])['verdict'] in {'APPROVE','CORRECT','DUPLICATE'}}

class V2Tests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.path=Path(self.t.name)/'v2.db';self.e=ObligationGate.create(self.path,'test');self.e.bootstrap_registry([],[],'fixture empty baseline')
    def prep(self,rows=None,atoms=None,label='first',queries=None,freeze=True):
        rows=rows or [row('a',[part('u',[1],'seedtoken')],'APPROVE','seedtoken'),row('b',[part('v',[2],'contexttoken')],'APPROVE','contexttoken')]
        atoms=atoms or [ref('u',[1],'seedtoken'),ref('v',[2],'contexttoken')]
        p=packet(self.e.prepare(raw(label),[]),rows);p.pop('atomization_reviewed');p['meaning_reviewed']=True
        p['draft_sha']=self.e.save_draft(p);r=refs(p,atoms)
        q=queries or [query('positive','seedtoken',['Ru','Rv']),query('negative','impossible-token',no=True)]
        if freeze:self.e.freeze_reference(p['source_id'],r,q,'source first fixture')
        return p,r,q
    def plan(self,p,add=None,remove=None,active=None):
        with self.e.db() as c:old=self.e._registry(c);prior=self.e.eligible(self.e.catalog(c))
        keys=sorted(prior|{p['source_id']+':'+x['id'] for x in p['claims'] if x['verdict'] in {'APPROVE','CORRECT'}}) if active is None else active
        return dict(prior_sha=digest(old),review_note='fixture',reviewed_ids=keys,add=add or [],remove=remove or [])
    def finish(self,p,r,plan=None,reviews=None,financial=None):
        return self.e.finalize(p,review(p,r) if reviews is None else reviews,finance(p) if financial is None else financial,plan or self.plan(p))
    def snap(self):
        with self.e.db() as c:return {t:c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall() for t in ['meta','videos','items','gate_state','gate_freeze','gate_audit']}
    def reject(self,fn):
        s=self.snap();before=sha(self.path.read_bytes())
        with self.assertRaises((ValueError,KeyError,TypeError,sqlite3.IntegrityError)):fn()
        self.assertEqual(s,self.snap());self.assertEqual(before,sha(self.path.read_bytes()))
    def seed(self):
        p,r,_=self.prep(); sid=p['source_id'];plan=self.plan(p,[edge(sid+':a',sid+':b')]);rec=self.finish(p,r,plan);return p,r,plan,rec
    def test_success_and_replay(self):
        p,r,plan,rec=self.seed();sid=p['source_id'];self.assertEqual(rec,self.finish(p,r,plan));self.assertEqual(self.e.audit(sid)['score']['matched'],{'Ru':'u','Rv':'v'});self.assertEqual(self.e.query(['seedtoken'])['context'][0]['qualified_id'],sid+':b');self.reject(lambda:self.finish(dict(p,review_note='change'),r,plan))
    def test_legacy_modes_blocked(self):
        for cls in [GateEngine,Engine]:
            with self.assertRaises(ValueError):cls(self.path,'test')
    def test_source_first(self):
        p,r,q=self.prep(freeze=False);sid=p['source_id'];self.reject(lambda:self.e.resume(sid,[]));self.reject(lambda:self.e.prepare(raw('first'),[]));self.e.freeze_reference(sid,r,q,'fixture');self.assertEqual(self.e.resume(sid,[])['draft_sha'],p['draft_sha']);self.reject(lambda:self.e.save_draft(p));self.reject(lambda:self.e.freeze_reference(sid,r,q,'fixture'))
    def test_multiple_meanings_and_cross_row(self):
        old,_,_,_=self.seed();sid=old['source_id']; rows=[row('a',[part('u',[1],'one',CORE),part('v',[1],'two')]),row('b',[part('u',[2],'one',QUAL),part('w',[2],'three')])]; p,r,_=self.prep(rows,[ref('u',[1,2],'one'),ref('v',[1],'two'),ref('w',[2],'three')],'many',[query('prior','seedtoken',prior=[sid+':a']),query('none','never-found',no=True)]);self.finish(p,r);audit=self.e.audit(p['source_id']);self.assertEqual(audit['score']['reference_count'],3);self.assertEqual(audit['score']['output_count'],3);self.assertEqual(audit['score']['recall'],1);self.assertEqual(len(audit['output']['atoms'][0]['components']),2);self.assertEqual(self.e.status()['active'],2)
    def test_no_implicit_link(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][0]['source_components'][0]['fields'].pop('conditions');refresh(x['claims'][0]);self.reject(lambda:self.finish(x,r))
    def test_conflicting_component(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][1]['source_components'].append(part('u',[2],'seedtoken',QUAL));refresh(x['claims'][1]);self.reject(lambda:self.finish(x,r))
    def test_orphan_component(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][1]['source_components'].append(part('z',[2],'orphan',QUAL));refresh(x['claims'][1]);self.reject(lambda:self.finish(x,r))
    def test_hidden_statement(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][0]['statement']+=' unreviewed proposition';self.reject(lambda:self.finish(x,r))
    def test_unreviewed_component_row(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][0]['source_components']=[];self.reject(lambda:self.finish(x,r))
    def test_row_cue_mismatch(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][0]['cues']=[1,2];self.reject(lambda:self.finish(x,r))
    def test_mixed_publishable_compound(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][0]['source_components'].append(part('z',[1],'other'));refresh(x['claims'][0]);self.reject(lambda:self.finish(x,r))
    def test_publishable_cross_row_rejected(self):
        p,r,_=self.prep();x=copy.deepcopy(p);a=x['claims'][0];b=x['claims'][1];a['source_components']=[part('u',[1],'seedtoken',CORE)];b['verdict']='CONTEXT';b['knowledge']='';b['source_components'].append(part('u',[2],'seedtoken',QUAL));refresh(a);refresh(b);self.reject(lambda:self.finish(x,r))
    def test_source_kind_mismatch(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'][0]['kind']='QUESTION';self.reject(lambda:self.finish(x,r))
    def test_partial_or_wrong_anchor_high_risk(self):
        p,r,_=self.prep();m=review(p,r);m[0]['fields']['conditions']=False;self.reject(lambda:self.finish(p,r,reviews=m));m=review(p,r);m[0]['anchor_sufficient']=False;self.reject(lambda:self.finish(p,r,reviews=m))
    def test_wrong_number_polarity_stance_or_time(self):
        p,r,_=self.prep()
        for field in ['numbers_units','polarity','speaker_stance','time_scope','exceptions']:
            m=review(p,r);m[0]['fields'][field]=False;self.reject(lambda:self.finish(p,r,reviews=m))
    def test_review_content_hash(self):
        p,r,_=self.prep();m=review(p,r);x=copy.deepcopy(p);x['claims'][0]['source_components'][0]['fields']['conditions']='changed';refresh(x['claims'][0]);self.reject(lambda:self.finish(x,r,reviews=m))
    def test_financial_digest_and_missing(self):
        p,r,_=self.prep();f=finance(p);f['a']['meaning_sha']='wrong';self.reject(lambda:self.finish(p,r,financial=f));self.reject(lambda:self.finish(p,r,financial={}))
    def test_duplicate_not_double_credit(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'].append(row('c',[part('z',[1],'seedtoken')]));m=review(x,r);a=output_units(x,2)['atoms'][-1];m[-1]=dict(output='z',reference='Ru',output_sha=digest(a),reference_sha=digest(r['atoms'][0]),reason='duplicate fixture',fields={f:True for f in FIELDS},anchor_sufficient=True);s=evaluate(r,output_units(x,2),m,digest(r),x['source_id'],2);self.assertEqual(s['precision'],2/3);self.assertEqual(s['extra'],['z']);self.reject(lambda:self.finish(x,r,reviews=m))
    def test_additional_meaning_not_credited(self):
        p,r,_=self.prep();x=copy.deepcopy(p);x['claims'].append(row('c',[part('z',[1],'invented')]));self.reject(lambda:self.finish(x,r))
    def test_missing_output_review(self):
        p,r,_=self.prep();self.reject(lambda:self.finish(p,r,reviews=review(p,r)[:-1]))
    def test_query_failure_rollback(self):
        p,r,_=self.prep();self.reject(lambda:self.finish(p,r));self.assertIsNone(self.e.audit(p['source_id']))
    def test_duplicate_query_resolves_existing_target(self):
        old,_,_,_=self.seed();sid=old['source_id'];rows=[row('a',[part('u',[1],'seedtoken')],'DUPLICATE','seedtoken',relations=[dict(type='SAME',target=sid+':a',reason='fixture equivalence')])];p,r,_=self.prep(rows,[ref('u',[1],'seedtoken')],'dup',[query('duplicate','seedtoken',['Ru']),query('none','impossible-token',no=True)]);self.finish(p,r);a=self.e.audit(p['source_id']);self.assertEqual(a['queries'][0]['required'],[sid+':a']);self.assertEqual(self.e.status()['active'],2)
    def test_invalid_registry_rolls_back(self):
        p,r,_=self.prep();self.reject(lambda:self.finish(p,r,self.plan(p,[edge(p['source_id']+':a','missing')])))
    def test_audit_failure_rolls_back(self):
        p,r,_=self.prep();sid=p['source_id'];plan=self.plan(p,[edge(sid+':a',sid+':b')]);
        with self.e.db(True) as c:c.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON gate_audit BEGIN SELECT RAISE(ABORT,'forced'); END")
        self.reject(lambda:self.finish(p,r,plan))
    def test_nonclaim_boundary_review(self):
        rows=[row('a',[part('u',[1],'seedtoken')],'APPROVE','seedtoken')]
        p,r,q=self.prep(rows,[ref('u',[1,2],'seedtoken')],queries=[query('positive','seedtoken',['Ru']),query('negative','impossible-token',no=True)],freeze=False)
        r['nonclaim_cues']=[];self.e.freeze_reference(p['source_id'],r,q,'fixture')
        m=review(p,r);m[0]['anchor_sufficient']=True
        self.reject(lambda:self.finish(p,r,reviews=m))
        p['nonclaim_reviews']=[dict(cue=2,reference_role='CLAIM',output_role='NONCLAIM',reason='fixture cue 1 independently sufficient; cue 2 incidental',reviewed=True)]
        self.finish(p,r,reviews=m);self.assertEqual(self.e.audit(p['source_id'])['nonclaim']['reviews'],p['nonclaim_reviews'])
    def test_nonclaim_cannot_hide_missing_meaning(self):
        p=dict(nonclaim=[dict(cues=[2],reason='fixture')],nonclaim_reviews=[dict(cue=2,reference_role='CLAIM',output_role='NONCLAIM',reason='fixture',reviewed=True)])
        r=dict(nonclaim_cues=[],atoms=[ref('u',[1]),ref('v',[2])]);out=dict(atoms=[dict(id='u',cues=[1])]);score=dict(matched={'Ru':'u'})
        with self.assertRaisesRegex(ValueError,'unmatched meaning'):reconcile_nonclaim(p,r,out,score)
    def test_nonclaim_extra_review_rejected(self):
        p,r,_=self.prep();p['nonclaim_reviews']=[dict(cue=1,reference_role='CLAIM',output_role='NONCLAIM',reason='fixture',reviewed=True)];self.reject(lambda:self.finish(p,r))
    def test_migrate_v1_candidate(self):
        v1=Path(self.t.name)/'v1.db';g=GateEngine.create(v1,'test');g.bootstrap_registry([],[],'fixture');h=sha(v1.read_bytes());target=Path(self.t.name)/'migrated.db';g2=ObligationGate.migrate(v1,target,h,'test');self.assertEqual(g.status()['head'],g2.status()['head']);self.assertEqual(h,sha(v1.read_bytes()));self.assertEqual(g.query(['x']),g2.query(['x']))
    def test_migrate_unfinished_v1_rejected(self):
        v1=Path(self.t.name)/'v1.db';g=GateEngine.create(v1,'test');g.bootstrap_registry([],[],'fixture');g.prepare(raw('unfinished'),[]);h=sha(v1.read_bytes());
        with self.assertRaises(ValueError):ObligationGate.migrate(v1,Path(self.t.name)/'migrated.db',h,'test')
        self.assertEqual(h,sha(v1.read_bytes()));self.assertFalse((Path(self.t.name)/'migrated.db').exists())
if __name__=='__main__':unittest.main()
