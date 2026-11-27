import copy, tempfile, unittest
from pathlib import Path
from engine import Engine, digest, sha
from d4_quality import FIELDS
from d4_gate import GateEngine, FIN_FIELDS, output_from


def raw(label):
    return f'1\n00:00:00,000 --> 00:00:01,000\n{label}\n\n2\n00:00:01,000 --> 00:00:02,000\ncontext\n'.encode()


def claim(i, cue, token, verdict='APPROVE', **kwargs):
    active=verdict in {'APPROVE','CORRECT','DUPLICATE'}
    x=dict(id=i,cues=[cue],topic=token,statement=token,speaker='fixture',kind='FACT',time_scope='fixture only',reason='synthetic',verdict=verdict,knowledge=token if active else '',conditions=[],exceptions=[],numbers=[],depends_on=[],relations=[],evidence=[dict(issuer='fixture',title='fixture',url='https://example.invalid/test',checked_on='2026-11-27',applies_on='test',scope='test',excerpt='test',access='TEST')] if active else [],source_atom=dict(subject=token,speaker_stance='fixture FACT',polarity='affirmed',conditions='NONE',exceptions='NONE',numbers_units='NONE',risk='H'))
    x.update(kwargs); return x


def packet(p, claims):
    covered={i for x in claims for i in x['cues']}
    rest=[x['id'] for x in p['cues'] if x['id'] not in covered]
    return dict(mode=p['mode'],source_id=p['source_id'],head=p['head'],claims=claims,nonclaim=[dict(cues=rest,reason='fixture nonclaim')] if rest else [],review_note='synthetic fixture',atomization_reviewed=True)


def ref_for(p):
    r=output_from(p); r['nonclaim_cues']=[i for x in p['nonclaim'] for i in x['cues']]
    for a in r['atoms']: a['id']='ref_'+a['id']
    return r


def review_for(p):
    atoms=output_from(p)['atoms']
    return [dict(output=x['id'],reference='ref_'+x['id'],output_sha=digest(x),reference_sha=digest(dict(x,id='ref_'+x['id'])),reason='fixture manual',fields={f:True for f in FIELDS}) for x in atoms]


def financial_for(p):
    return {x['id']:dict(claim_sha=digest(x),reason='fixture',checks={f:True for f in FIN_FIELDS}) for x in p['claims'] if x['verdict'] in {'APPROVE','CORRECT','DUPLICATE'}}


def query(id, terms, req=(), prior=(), forbidden=(), no=False):
    return dict(id=id,terms=[terms],required_refs=list(req),required_prior=list(prior),forbidden_refs=list(forbidden),forbidden_prior=[],no_match=no)


def edge(a,b): return {'from':a,'to':b,'kind':'REQUIRED_CONTEXT','reason':'fixture verified context'}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'new.db'; self.e=GateEngine.create(self.path,'test'); self.e.bootstrap_registry([],[],'empty fixture')
    def prep(self,label='a',claims=None,queries=None,freeze=True):
        p=self.e.prepare(raw(label),[]); sid=p['source_id']; p=packet(p,claims or [claim('a',1,'seedtoken'),claim('b',2,'contexttoken')]); d=self.e.save_draft(p); p['draft_sha']=d
        r=ref_for(p); q=queries or [query('positive','seedtoken',['ref_a','ref_b']),query('negative','impossible-token',no=True)]
        if freeze: self.e.freeze_reference(sid,r,q,'source first fixture')
        return p,r,q
    def plan(self,p,add=None,remove=None,active=None):
        with self.e.db() as c:
            old=self.e._registry(c); prior=self.e.eligible(self.e.catalog(c))
        sid=p['source_id']; keys=sorted(prior|{sid+':'+x['id'] for x in p['claims'] if x['verdict'] in {'APPROVE','CORRECT'}}) if active is None else active
        return dict(prior_sha=digest(old),review_note='fixture review',reviewed_ids=keys,add=add or [],remove=remove or [])
    def finalize(self,p,plan): return self.e.finalize(p,review_for(p),financial_for(p),plan)
    def first(self):
        p,_,_=self.prep(); sid=p['source_id']; plan=self.plan(p,[edge(sid+':a',sid+':b')]); self.finalize(p,plan); return p,plan
    def snapshot(self):
        with self.e.db() as c:
            return {t:c.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall() for t in ['meta','videos','items','gate_state','gate_freeze','gate_audit']}
    def reject(self,fn):
        before=self.snapshot()
        with self.assertRaises((ValueError,KeyError,TypeError)): fn()
        self.assertEqual(before,self.snapshot())
    def test_legacy_entrypoint_blocked(self):
        with self.assertRaises(ValueError): Engine(self.path,'test')
    def test_migration_pending_and_legacy_preserved(self):
        legacy=Path(self.tmp.name)/'legacy.db'; old=Engine(legacy,'test'); h=sha(legacy.read_bytes()); target=Path(self.tmp.name)/'migrate.db'; g=GateEngine.migrate(legacy,target,h,'test')
        self.assertEqual(h,sha(legacy.read_bytes())); self.assertEqual(g.status()['head'],old.status()['head'])
        with self.assertRaises(ValueError): g.query(['x'])
        with self.assertRaises(ValueError): g.prepare(raw('new'),[])
        g.bootstrap_registry([],[],'empty fixture'); self.assertEqual(g.query(['x'])['context'],[])
    def test_resume_before_freeze_blocked(self):
        p,r,q=self.prep(freeze=False); sid=p['source_id']
        self.assertEqual(set(self.e.source_only(sid)),{'source_id','cues','head'})
        self.reject(lambda:self.e.resume(sid,[])); self.reject(lambda:self.e.prepare(raw('a'),[]))
        self.e.freeze_reference(sid,r,q,'fixture'); self.assertEqual(self.e.resume(sid,[])['draft_sha'],p['draft_sha']); self.reject(lambda:self.e.freeze_reference(sid,r,q,'fixture')); self.reject(lambda:self.e.save_draft(p))
    def test_success_reopen_retry(self):
        p,plan=self.first(); sid=p['source_id']; e=GateEngine(self.path,'test'); res=e.query(['seedtoken']); self.assertEqual({x['qualified_id'] for x in res['context']},{sid+':b'}); audit=e.audit(sid); self.assertEqual(audit['packet_sha'],digest(p)); self.assertEqual(audit['score']['matched'],{'ref_a':'a','ref_b':'b'}); self.assertEqual(len(audit['queries']),2); self.assertEqual(e.finalize(p,review_for(p),financial_for(p),plan),audit['receipt']); self.reject(lambda:e.finalize(dict(p,review_note='changed'),review_for(p),financial_for(p),plan))
    def test_quality_inputs_required(self):
        p,_,_=self.prep(); self.reject(lambda:self.e.finalize(p))
    def test_quality_failure_rollback(self):
        p,_,_=self.prep(); m=review_for(p); m[0]['fields']['exceptions']=False; self.reject(lambda:self.e.finalize(p,m,financial_for(p),self.plan(p)))
    def test_review_bound_to_atom_content(self):
        p,_,_=self.prep(); m=review_for(p); p['claims'][0]['statement']='changed'; self.reject(lambda:self.e.finalize(p,m,financial_for(p),self.plan(p)))
    def test_financial_claim_hash(self):
        p,_,_=self.prep(); f=financial_for(p); f['a']['claim_sha']='fake'; self.reject(lambda:self.e.finalize(p,review_for(p),f,self.plan(p)))
    def test_missing_financial(self):
        p,_,_=self.prep(); self.reject(lambda:self.e.finalize(p,review_for(p),{},self.plan(p)))
    def test_query_failure_rolls_back_final_and_registry(self):
        p,_,_=self.prep(); self.reject(lambda:self.finalize(p,self.plan(p))); self.assertIsNone(self.e.audit(p['source_id'])); self.assertEqual(self.e.status()['active'],0)
    def test_invalid_context_edge_rollback(self):
        p,_,_=self.prep(); self.reject(lambda:self.finalize(p,self.plan(p,[edge(p['source_id']+':a','missing')])))
    def test_registry_required_review_and_stale(self):
        p,_,_=self.prep(); sid=p['source_id']; plan=self.plan(p,[edge(sid+':a',sid+':b')]); self.reject(lambda:self.finalize(p,dict(plan,reviewed_ids=[]))); self.reject(lambda:self.finalize(p,dict(plan,prior_sha='wrong')))
    def test_external_registry_rejected(self):
        self.reject(lambda:self.e.query_context(['seedtoken'],{}))
    def test_reference_incomplete(self):
        p,r,q=self.prep(freeze=False); r['atoms'].pop(); self.reject(lambda:self.e.freeze_reference(p['source_id'],r,q,'fixture'))
    def test_registry_preserves_old_edges(self):
        p,_=self.first(); oldsid=p['source_id']; q,_,_=self.prep('second',[claim('a',1,'newtoken')],[query('new','newtoken',['ref_a']),query('old','seedtoken',prior=[oldsid+':a',oldsid+':b']),query('none','impossible-token',no=True)]); self.finalize(q,self.plan(q)); self.assertEqual({x['qualified_id'] for x in self.e.query(['seedtoken'])['context']},{oldsid+':b'})
    def test_deactivated_endpoint_requires_explicit_review(self):
        p,_=self.first(); sid=p['source_id']; claims=[claim('a',1,'replacement',verdict='CORRECT',relations=[dict(type='CORRECTS',target=sid+':b',reason='fixture correction')])]; q,_,_=self.prep('replacement',claims,[query('new','replacement',['ref_a']),query('none','impossible-token',no=True)]); keys=[sid+':a',q['source_id']+':a']; self.reject(lambda:self.finalize(q,self.plan(q,active=keys))); self.finalize(q,self.plan(q,add=[edge(sid+':a',q['source_id']+':a')],remove=[dict(edge(sid+':a',sid+':b'),reason='reviewed replacement')],active=keys)); self.assertEqual({x['qualified_id'] for x in self.e.query(['seedtoken'])['context']},{q['source_id']+':a'})
    def test_output_bound_to_packet(self):
        p,_,_=self.prep(); p['claims'][0].pop('source_atom'); self.reject(lambda:self.e.finalize(p,review_for(p),financial_for(p),self.plan(p)))
    def test_audit_insert_failure_rolls_back(self):
        p,_,_=self.prep(); sid=p['source_id']; plan=self.plan(p,[edge(sid+':a',sid+':b')]);
        with self.e.db(True) as c: c.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON gate_audit BEGIN SELECT RAISE(ABORT,'forced'); END")
        before=self.snapshot()
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError): self.finalize(p,plan)
        self.assertEqual(before,self.snapshot())

if __name__=='__main__': unittest.main()
