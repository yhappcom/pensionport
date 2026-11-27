"""Candidate F1: separate stored rows from meaning units; manual judgments only.
No change to GateEngine v1, frozen Engine, or previous results. Active/DUPLICATE
rows must be independently publishable, complete single units. Context/HOLD
rows may contain multiple units or explicit cross-row qualifier components.
"""
import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from engine import Engine, ACTIVE, digest, dump, sha, require, nonempty
from d4_quality import ids, FIELDS
from d4_gate import GateEngine, FIN_FIELDS, SCHEMA as V1, now

SCHEMA = 'D4_GATE_2'
CORE = {'proposition', 'subject', 'speaker_stance', 'polarity'}
QUAL = set(FIELDS) - CORE
PUBLISH = ACTIVE | {'DUPLICATE'}
METHOD = 'SOURCE_OBLIGATION_V2'


def render(parts):
    """Canonical statement is derived from the actual stored components."""
    return '\n'.join(f"[{p['unit']}] " + ' | '.join(f'{k}: {p["fields"][k]}' for k in FIELDS if k in p['fields']) for p in parts)


def output_units(packet, cue_count):
    require(packet.get('meaning_reviewed') is True, 'manual meaning inventory required')
    units, claims = {}, {}
    for row in packet['claims']:
        k = row['id']; require(k not in claims, 'duplicate storage row'); claims[k] = row
        parts = row['source_components']; require(isinstance(parts, list) and parts, 'empty source components')
        require(row['statement'] == render(parts), 'statement/component mismatch')
        require(len({p['unit'] for p in parts}) == len(parts), 'duplicate unit in row')
        covered = set()
        for p in parts:
            require(set(p) == {'unit','fields','cues','risk'}, 'invalid component keys')
            u, f, cues = p['unit'], p['fields'], p['cues']
            require(nonempty(u) and isinstance(f,dict) and f and set(f)<=set(FIELDS) and all(nonempty(v) for v in f.values()), 'invalid component fields')
            require(isinstance(cues,list) and cues and len(cues)==len(set(cues)) and all(type(i) is int and 1<=i<=cue_count for i in cues), 'invalid component cues')
            covered.update(cues)
            a = units.setdefault(u, dict(fields={}, cues=set(), rows=[], owner=None, risk=None))
            require(not set(f)&set(a['fields']), 'duplicate/conflicting meaning field')
            if set(f)&CORE:
                require(CORE<=set(f) and a['owner'] is None and p['risk'] in {'H','M','L'}, 'one complete core required')
                require(row['speaker'] in f['speaker_stance'] and row['kind'] in f['speaker_stance'], 'speaker/kind mismatch')
                a['owner']=k; a['risk']=p['risk']
            else:
                require(set(f)<=QUAL and p['risk'] is None, 'qualifier only component required')
            a['fields'].update(f); a['cues'].update(cues)
            a['rows'].append(dict(row=k, row_sha=digest(row), component_sha=digest(p)))
        require(covered==set(row['cues']), 'component/row source coverage mismatch')
    out=[]
    for u,a in sorted(units.items()):
        require(a['owner'] is not None and set(a['fields'])==set(FIELDS), 'incomplete/orphan meaning')
        owner=claims[a['owner']]; keys={x['row'] for x in a['rows']}
        require(all(claims[k]['speaker']==owner['speaker'] and claims[k]['kind']==owner['kind'] for k in keys), 'cross-row speaker/kind mismatch')
        if any(claims[k]['verdict'] in PUBLISH for k in keys):
            require(keys=={a['owner']} and len(owner['source_components'])==1, 'publishable meaning must be complete single row')
            require(owner['time_scope']==a['fields']['time_scope'], 'publishable time scope mismatch')
        out.append(dict(id=u, **a['fields'], cues=sorted(a['cues']), risk=a['risk'], owner=a['owner'], components=sorted(a['rows'],key=lambda x:x['row'])))
    require(out, 'empty meaning denominator')
    return dict(source_id=packet['source_id'],unit='ATOM',method=METHOD,atoms=out)


def evaluate(reference, output, reviews, frozen_sha, source_id, cue_count):
    require(digest(reference)==frozen_sha, 'reference changed')
    require(reference['source_id']==output['source_id']==source_id and reference.get('method')==output.get('method')==METHOD, 'meaning method/source mismatch')
    require(reference.get('atomization_reviewed') is True and reference['unit']==output['unit']=='ATOM', 'reference review required')
    refs, outs=ids(reference['atoms']), ids(output['atoms']); require(refs and outs, 'empty denominator')
    for a in list(refs.values())+list(outs.values()):
        require(len(a['cues'])==len(set(a['cues'])) and all(i<=cue_count for i in a['cues']), 'invalid meaning anchors')
    seen=set(); candidates={}
    for v in reviews:
        o,r=v['output'],v['reference']; require(o in outs and o not in seen and nonempty(v['reason']), 'invalid/duplicate review'); seen.add(o)
        require(v['output_sha']==digest(outs[o]), 'output review changed')
        require((r is None and v['reference_sha'] is None) or (r in refs and v['reference_sha']==digest(refs[r])), 'reference review changed')
        flags=v['fields']; require(set(flags)==set(FIELDS) and all(type(x) is bool for x in flags.values()) and type(v['anchor_sufficient']) is bool, 'manual field/anchor review required')
        if r is not None and all(flags.values()) and v['anchor_sufficient']:
            require(set(outs[o]['cues'])&set(refs[r]['cues']), 'no shared source anchor')
            candidates.setdefault(r,[]).append(o)
    require(seen==set(outs), 'unreviewed output meanings')
    matched={r:sorted(v)[0] for r,v in candidates.items()}
    missed=sorted(set(refs)-set(matched)); extra=sorted(set(outs)-set(matched.values())); high=[r for r in missed if refs[r]['risk']=='H']; n=len(matched)
    return dict(reference_count=len(refs),output_count=len(outs),matched=matched,missed=missed,extra=extra,high_risk_missed=high,precision=n/len(outs),recall=n/len(refs),threshold_met=100*n>=95*len(outs) and 100*n>=98*len(refs) and not high,assessment='MANUAL_INTERNAL_ONLY',output_sha=digest(output),review_sha=digest(reviews))


def reconcile_nonclaim(packet, reference, output, score):
    """Conservative manual boundary reconciliation, never excuses a missing meaning.
    The original reference and output classifications remain separately auditable.
    Engine.finalize still independently enforces full output source coverage.
    """
    old=set(reference['nonclaim_cues']); new={i for x in packet['nonclaim'] for i in x['cues']}
    diff=old^new; notes=packet.get('nonclaim_reviews',[])
    require(isinstance(notes,list), 'nonclaim review list required')
    by_cue={}
    for v in notes:
        require(set(v)=={'cue','reference_role','output_role','reason','reviewed'} and type(v['cue']) is int and v['cue'] not in by_cue, 'invalid nonclaim review')
        by_cue[v['cue']]=v
    require(set(by_cue)==diff, 'nonclaim discrepancy requires explicit review')
    matched=score['matched']; credited=set(matched.values())
    for i,v in by_cue.items():
        require(v['reference_role']==('NONCLAIM' if i in old else 'CLAIM') and v['output_role']==('NONCLAIM' if i in new else 'CLAIM') and v['reviewed'] is True and nonempty(v['reason']), 'invalid nonclaim adjudication')
        require(all(a['id'] in matched for a in reference['atoms'] if i in a['cues']) and all(a['id'] in credited for a in output['atoms'] if i in a['cues']), 'nonclaim review cannot hide unmatched meaning')
    return dict(reference=sorted(old),output=sorted(new),reviews=notes)


class ObligationGate(GateEngine):
    def __init__(self,path,mode='research'):
        self.path,self.mode=str(path),mode; self._tx=None
        require(mode in {'research','test'} and Path(path).is_file(), 'invalid mode/path')
        with self.db() as c:
            require(c.execute('SELECT version FROM gate_state').fetchall()==[(SCHEMA,)], 'wrong gate schema')
    @classmethod
    def create(cls,path,mode='research'):
        GateEngine.create(path,mode)
        return cls._upgrade_v2(path,mode)
    @classmethod
    def migrate(cls,source,target,expected_sha,mode='research'):
        require(not Path(target).exists() and sha(Path(source).read_bytes())==expected_sha,'invalid migration source/destination')
        # Copy only v1 candidate DB; preserve all existing knowledge and history.
        with closing(sqlite3.connect(Path(source).resolve().as_uri()+'?mode=ro',uri=True)) as s:
            require(s.execute('SELECT mode FROM meta').fetchall()==[(V1+':'+mode,)] and s.execute('SELECT version FROM gate_state').fetchall()==[(V1,)],'v1 source required')
            require(not s.execute('SELECT 1 FROM videos WHERE final IS NULL LIMIT 1').fetchone(),'unfinished v1 research cannot migrate')
            try:
                with closing(sqlite3.connect(target)) as t: s.backup(t)
                require(sha(Path(source).read_bytes())==expected_sha,'source changed during migration')
                return cls._upgrade_v2(target,mode)
            except Exception:
                Path(target).unlink(missing_ok=True)
                raise
    @classmethod
    def _upgrade_v2(cls,path,mode):
        with closing(sqlite3.connect(path)) as c,c:
            c.execute('BEGIN IMMEDIATE')
            require(c.execute('SELECT mode FROM meta').fetchall()==[(V1+':'+mode,)] and c.execute('SELECT version FROM gate_state').fetchall()==[(V1,)],'v1 source required')
            require(not c.execute('SELECT 1 FROM videos WHERE final IS NULL LIMIT 1').fetchone(),'unfinished v1 research cannot migrate')
            c.execute('UPDATE meta SET mode=?',(SCHEMA+':'+mode,)); c.execute('UPDATE gate_state SET version=?',(SCHEMA,))
        return cls(path,mode)
    @contextmanager
    def db(self,write=False):
        if self._tx is not None:
            c,writable=self._tx; require(not write or writable,'cannot upgrade read transaction'); yield c; return
        with closing(sqlite3.connect(self.path)) as c,c:
            c.execute('PRAGMA foreign_keys=ON'); c.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            require(c.execute('SELECT mode FROM meta').fetchall()==[(SCHEMA+':'+self.mode,)],'database mode mismatch')
            self._tx=(c,write)
            try: yield c
            finally: self._tx=None
    def freeze_reference(self,sid,reference,queries,review_note):
        require(reference.get('method')==METHOD,'v2 obligation reference required')
        return super().freeze_reference(sid,reference,queries,review_note)
    def save_draft(self,packet):
        # A draft may be incomplete, but cannot claim review without a valid inventory.
        if packet.get('meaning_reviewed') is True:
            with self.db() as c:
                cues,_,_=self.source(c,packet['source_id']); output_units(packet,len(cues))
        return super().save_draft(packet)
    def finalize(self,packet,reviews=None,financial=None,registry_plan=None):
        require(reviews is not None and financial is not None and registry_plan is not None,'quality gate inputs required')
        sid=packet['source_id']; req_sha=digest([packet,reviews,financial,registry_plan])
        with self.db(True) as c:
            old_audit=c.execute('SELECT data FROM gate_audit WHERE sid=?',(sid,)).fetchone()
            if old_audit:
                a=json.loads(old_audit[0]); require(a.get('method')==METHOD and a['request_sha']==req_sha,'different or legacy finalized request'); return a['receipt']
            old=self._registry(c); row=c.execute('SELECT data FROM gate_freeze WHERE sid=?',(sid,)).fetchone(); require(row is not None,'reference not frozen')
            f=json.loads(row[0]); require(f['head']==self.head(c) and f['registry_sha']==digest(old) and packet['draft_sha']==f['draft_sha'],'stale frozen review')
            cues,_,_=self.source(c,sid); output=output_units(packet,len(cues)); outs=ids(output['atoms'])
            score=evaluate(f['reference'],output,reviews,f['reference_sha'],sid,len(cues)); require(score['threshold_met'],'meaning quality threshold failed')
            nonclaim=reconcile_nonclaim(packet,f['reference'],output,score)
            rows={x['id']:x for x in packet['claims']}; eligible={k:x for k,x in rows.items() if x['verdict'] in PUBLISH}
            matched=score['matched']; credited=set(matched.values()); active_units={u:a for u,a in outs.items() if a['owner'] in eligible}
            require(set(active_units)<=credited,'unmatched publishable meaning')
            require(set(financial)==set(eligible),'financial reviews incomplete')
            for k,v in financial.items():
                a=next(a for a in active_units.values() if a['owner']==k)
                require(v['claim_sha']==digest(eligible[k]) and v['meaning_sha']==digest(a) and nonempty(v['reason']) and set(v['checks'])==FIN_FIELDS and all(x is True for x in v['checks'].values()),'financial review failed')
            def target(ref):
                if ref not in matched:return set()
                x=rows[outs[matched[ref]]['owner']]
                if x['verdict'] in ACTIVE:return {sid+':'+x['id']}
                if x['verdict']=='DUPLICATE':return {r['target'] for r in x['relations'] if r['type']=='SAME'}
                return set()
            new={sid+':'+k for k,x in eligible.items() if x['verdict'] in ACTIVE}
            if new:require(any(target(r)&new for q in f['queries'] for r in q['required_refs']),'new active knowledge query required')
            receipt=Engine.finalize(self,packet)
            reg=self._updated_registry(c,old,registry_plan); c.execute('UPDATE gate_state SET registry=?',(dump(reg),))
            outcomes=[]
            for q in f['queries']:
                require(all(target(r) for r in q['required_refs']),'required reference not publishable/matched')
                required=set(q['required_prior'])|{k for r in q['required_refs'] for k in target(r)}
                forbidden=set(q['forbidden_prior'])|{k for r in q['forbidden_refs'] for k in target(r)}
                res=self.query(q['terms']); actual={x['item']['qualified_id'] for x in res['direct']}|{x['qualified_id'] for x in res['context']}
                require((not actual if q['no_match'] else required<=actual and not forbidden&actual),'query failed: '+q['id'])
                outcomes.append(dict(id=q['id'],required=sorted(required),forbidden=sorted(forbidden),actual=sorted(actual),query_sha=digest(res)))
            audit=dict(method=METHOD,request_sha=req_sha,receipt=receipt,packet_sha=digest(packet),freeze_sha=digest(f),score=score,output=output,nonclaim=nonclaim,reviews=reviews,financial=financial,registry_plan=registry_plan,registry_before=old,registry_after=reg,queries=outcomes,committed_at=now(),scope='MANUAL_INTERNAL_ONLY')
            c.execute('INSERT INTO gate_audit VALUES (?,?)',(sid,dump(audit))); return receipt
