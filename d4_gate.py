"""Versioned D4 research gate. Manual semantic judgments, transactional storage.
Legacy Engine cannot open the migrated database in its supported modes.
Not a security boundary against arbitrary SQL or trusted-code modification.
"""
import json
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from engine import Engine, ACTIVE, digest, dump, sha, require, nonempty, parse_srt, strings
from d4_quality import ContextEngine, assess, ids, KINDS

SCHEMA = 'D4_GATE_1'
FIN_FIELDS = {'evidence', 'scope', 'date', 'conditions', 'exceptions', 'numbers', 'dependencies'}
SUPPLEMENT = {'subject', 'speaker_stance', 'polarity', 'conditions', 'exceptions', 'numbers_units', 'risk'}


def now():
    return datetime.now(timezone.utc).isoformat()


def output_from(packet):
    atoms = []
    for claim in packet['claims']:
        a = claim['source_atom']
        require(set(a) == SUPPLEMENT, 'source atom fields required')
        require(nonempty(claim['speaker']) and claim['speaker'] in a['speaker_stance'], 'speaker not bound')
        require(claim['kind'] in a['speaker_stance'], 'claim kind not bound')
        atoms.append(dict(a, id=claim['id'], cues=claim['cues'], proposition=claim['statement'], time_scope=claim['time_scope']))
    return dict(source_id=packet['source_id'], unit='ATOM', atomization_reviewed=packet.get('atomization_reviewed') is True, atoms=atoms)


def edge_key(e):
    return e['from'], e['to']


class GateEngine(ContextEngine):
    """Use only this entrypoint for new candidate runs; legacy DB is untouched."""
    def __init__(self, path, mode='research'):
        self.path, self.mode = str(path), mode
        self._tx = None
        require(mode in {'research','test'}, 'invalid mode')
        require(Path(path).is_file(), 'use create or migrate')
        with self.db() as c:
            require(c.execute('SELECT version FROM gate_state').fetchall() == [(SCHEMA,)], 'wrong gate schema')

    @classmethod
    def create(cls, path, mode='research'):
        require(not Path(path).exists(), 'destination exists')
        Engine(path, mode)
        return cls._upgrade(path, mode)

    @classmethod
    def migrate(cls, source, target, expected_sha, mode='research'):
        require(not Path(target).exists(), 'destination exists')
        require(sha(Path(source).read_bytes()) == expected_sha, 'legacy source changed')
        with closing(sqlite3.connect(Path(source).resolve().as_uri()+'?mode=ro', uri=True)) as s, closing(sqlite3.connect(target)) as t:
            require(s.execute('SELECT mode FROM meta').fetchall() == [(mode,)], 'legacy mode mismatch')
            s.backup(t)
        require(sha(Path(source).read_bytes()) == expected_sha, 'legacy source changed during copy')
        return cls._upgrade(target, mode)

    @classmethod
    def _upgrade(cls, path, mode):
        with closing(sqlite3.connect(path)) as c, c:
            c.execute('BEGIN IMMEDIATE')
            require(c.execute('SELECT mode FROM meta').fetchall() == [(mode,)], 'legacy mode mismatch')
            c.execute('UPDATE meta SET mode=?', (SCHEMA+':'+mode,))
            c.execute('CREATE TABLE gate_state(version TEXT NOT NULL, registry TEXT)')
            c.execute('INSERT INTO gate_state VALUES (?,NULL)', (SCHEMA,))
            c.execute('CREATE TABLE gate_freeze(sid TEXT PRIMARY KEY REFERENCES videos(id), data TEXT NOT NULL)')
            c.execute('CREATE TABLE gate_audit(sid TEXT PRIMARY KEY REFERENCES videos(id), data TEXT NOT NULL)')
        return cls(path, mode)

    @contextmanager
    def db(self, write=False):
        if self._tx is not None:
            c, writable = self._tx
            require(not write or writable, 'cannot upgrade read transaction')
            yield c
            return
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            require(c.execute('SELECT mode FROM meta').fetchall() == [(SCHEMA+':'+self.mode,)], 'database mode mismatch')
            self._tx = (c, write)
            try:
                yield c
            finally:
                self._tx = None

    def _registry(self, c):
        row = c.execute('SELECT registry FROM gate_state').fetchone()
        require(row is not None and row[0] is not None, 'baseline context review required')
        reg=json.loads(row[0])
        require(reg['head']==self.head(c), 'stale stored registry')
        return reg

    def _build_registry(self, c, specs, reviewed_ids):
        cat = self.catalog(c)
        active = self.eligible(cat)
        require(len(reviewed_ids) == len(set(reviewed_ids)) and set(reviewed_ids) == active, 'review all active context endpoints')
        edges = []
        for e in specs:
            require(set(e) == {'from','to','kind','reason'}, 'invalid edge spec')
            a,b = edge_key(e)
            require(a in active and b in active and a != b, 'inactive/unknown context edge')
            require(e['kind'] in KINDS and nonempty(e['reason']), 'invalid context edge')
            edges.append(dict(e, from_sha=digest(cat[a]), to_sha=digest(cat[b])))
        require(len({edge_key(e) for e in edges}) == len(edges), 'duplicate context edge')
        return dict(head=self.head(c), reviewed=True, reviewed_ids=sorted(reviewed_ids), edges=sorted(edges,key=edge_key))

    def bootstrap_registry(self, specs, reviewed_ids, review_note):
        require(nonempty(review_note), 'baseline review note required')
        with self.db(True) as c:
            require(c.execute('SELECT registry FROM gate_state').fetchone()[0] is None, 'registry already initialized')
            reg = self._build_registry(c, specs, reviewed_ids)
            reg['baseline_note'] = review_note
            c.execute('UPDATE gate_state SET registry=?', (dump(reg),))
            return digest(reg)

    def query(self, terms):
        with self.db() as c:
            return super().query_context(terms, self._registry(c))

    def query_context(self, terms, registry=None):
        require(registry is None, 'external registry forbidden')
        return self.query(terms)

    def prepare(self, raw, terms):
        with self.db(True) as c:
            self._registry(c)
            row = c.execute('SELECT draft FROM videos WHERE id=?',(sha(raw),)).fetchone()
            require(row is None or row[0] is None, 'use source_only then freeze then resume')
            p = super().prepare(raw, terms)
            p['context_query'] = self.query(terms)
            return p

    def source_only(self, sid):
        with self.db() as c:
            cues, _, _ = self.source(c, sid)
            return dict(source_id=sid, cues=cues, head=self.head(c))

    def save_draft(self, packet):
        with self.db(True) as c:
            self._registry(c)
            require(not c.execute('SELECT 1 FROM gate_freeze WHERE sid=?',(packet['source_id'],)).fetchone(), 'reference frozen; draft locked')
            return super().save_draft(packet)

    def freeze_reference(self, sid, reference, queries, review_note):
        require(nonempty(review_note), 'reference review note required')
        with self.db(True) as c:
            self._registry(c)
            cues,draft,final = self.source(c,sid)
            require(draft is not None and final is None, 'draft required; no final permitted')
            require(reference['source_id']==sid and reference['unit']=='ATOM' and reference['atomization_reviewed'] is True, 'atomic reference required')
            refs=ids(reference['atoms'])
            require(refs, 'empty reference')
            covered={i for a in refs.values() for i in a['cues']}
            nc=reference['nonclaim_cues']
            require(all(type(i) is int for i in nc) and len(nc)==len(set(nc)), 'invalid nonclaim list')
            require(not covered & set(nc) and covered | set(nc)=={x['id'] for x in cues}, 'reference source coverage incomplete')
            cat=self.catalog(c); active=self.eligible(cat)
            qids=set(); pos=neg=False
            for q in queries:
                require(nonempty(q['id']) and q['id'] not in qids, 'duplicate query id')
                qids.add(q['id'])
                require(strings(q['terms']) and q['terms'], 'query terms required')
                for field,allowed in [('required_refs',set(refs)),('required_prior',active),('forbidden_refs',set(refs)),('forbidden_prior',active)]:
                    require(strings(q[field]) and len(q[field])==len(set(q[field])) and set(q[field])<=allowed, 'invalid query expectation')
                require(type(q['no_match']) is bool, 'query intent required')
                require(not set(q['required_refs'])&set(q['forbidden_refs']) and not set(q['required_prior'])&set(q['forbidden_prior']), 'contradictory query')
                if q['no_match']:
                    require(not q['required_refs'] and not q['required_prior'], 'negative query has required items'); neg=True
                else:
                    require(q['required_refs'] or q['required_prior'], 'positive query missing expectations'); pos=True
            require(pos and neg, 'positive and negative query tests required')
            obj=dict(reference=reference,reference_sha=digest(reference),queries=queries,head=self.head(c),registry_sha=digest(self._registry(c)),review_note=review_note,frozen_at=now(),draft_sha=digest(json.loads(draft)))
            require(not c.execute('SELECT 1 FROM gate_freeze WHERE sid=?',(sid,)).fetchone(), 'reference already frozen')
            c.execute('INSERT INTO gate_freeze VALUES (?,?)',(sid,dump(obj)))
            return digest(obj)

    def resume(self, sid, terms):
        with self.db() as c:
            self._registry(c)
            _,draft,final=self.source(c,sid)
            require(draft is None or final is not None or c.execute('SELECT 1 FROM gate_freeze WHERE sid=?',(sid,)).fetchone(), 'freeze reference before opening draft')
            p=super().resume(sid,terms)
            p['context_query']=self.query(terms)
            return p

    def _updated_registry(self,c,old,plan):
        require(plan['prior_sha']==digest(old) and nonempty(plan['review_note']), 'registry plan stale or unreviewed')
        specs={edge_key(e):{k:e[k] for k in ('from','to','kind','reason')} for e in old['edges']}
        removed=set()
        for e in plan['remove']:
            k=edge_key(e)
            require(k in specs and k not in removed and nonempty(e['reason']), 'invalid edge removal')
            del specs[k]; removed.add(k)
        for e in plan['add']:
            k=edge_key(e)
            require(k not in specs, 'duplicate context edge')
            specs[k]=e
        return self._build_registry(c,list(specs.values()),plan['reviewed_ids'])

    def finalize(self, packet, reviews=None, financial=None, registry_plan=None):
        require(reviews is not None and financial is not None and registry_plan is not None, 'quality gate inputs required')
        sid=packet['source_id']
        req_sha=digest([packet,reviews,financial,registry_plan])
        with self.db(True) as c:
            old_audit=c.execute('SELECT data FROM gate_audit WHERE sid=?',(sid,)).fetchone()
            if old_audit:
                audit=json.loads(old_audit[0]); require(audit['request_sha']==req_sha, 'different finalized request')
                return audit['receipt']
            old=self._registry(c)
            row=c.execute('SELECT data FROM gate_freeze WHERE sid=?',(sid,)).fetchone()
            require(row is not None, 'reference not frozen')
            f=json.loads(row[0]); require(f['head']==self.head(c) and f['registry_sha']==digest(old) and packet['draft_sha']==f['draft_sha'], 'stale frozen review')
            cues,_,_=self.source(c,sid)
            output=output_from(packet)
            outs=ids(output['atoms']); refs=ids(f['reference']['atoms'])
            for review in reviews:
                o,r=review['output'],review['reference']
                require(o in outs and review['output_sha']==digest(outs[o]), 'output review changed')
                require((r is None and review['reference_sha'] is None) or (r in refs and review['reference_sha']==digest(refs[r])), 'reference review changed')
            score=assess(f['reference'],output,reviews,f['reference_sha'],sid,len(cues))
            require(score['threshold_met'], 'atomic quality threshold failed')
            require(set(f['reference']['nonclaim_cues'])=={i for x in packet['nonclaim'] for i in x['cues']}, 'nonclaim discrepancy')
            eligible={x['id']:x for x in packet['claims'] if x['verdict'] in ACTIVE|{'DUPLICATE'}}
            require(set(financial)==set(eligible), 'financial reviews incomplete')
            require(set(eligible)<=set(score['matched'].values()), 'unmatched approved output')
            new_active={k for k,x in eligible.items() if x['verdict'] in ACTIVE}
            if new_active:
                tested={score['matched'][r] for q in f['queries'] for r in q['required_refs'] if r in score['matched']}
                require(bool(tested & new_active), 'new active knowledge query required')
            for k,v in financial.items():
                require(v['claim_sha']==digest(eligible[k]) and nonempty(v['reason']) and set(v['checks'])==FIN_FIELDS and all(x is True for x in v['checks'].values()), 'financial review failed')
            receipt=super().finalize(packet)
            reg=self._updated_registry(c,old,registry_plan)
            c.execute('UPDATE gate_state SET registry=?',(dump(reg),))
            matched=score['matched']; outcomes=[]
            for q in f['queries']:
                require(set(q['required_refs'])<=set(matched), 'required reference not matched')
                required=set(q['required_prior'])|{sid+':'+matched[x] for x in q['required_refs']}
                forbidden=set(q['forbidden_prior'])|{sid+':'+matched[x] for x in q['forbidden_refs'] if x in matched}
                res=self.query(q['terms'])
                actual={x['item']['qualified_id'] for x in res['direct']}|{x['qualified_id'] for x in res['context']}
                require((not actual if q['no_match'] else required<=actual and not forbidden&actual), 'query failed: '+q['id'])
                outcomes.append(dict(id=q['id'],required=sorted(required),forbidden=sorted(forbidden),actual=sorted(actual),query_sha=digest(res)))
            audit=dict(request_sha=req_sha,receipt=receipt,packet_sha=digest(packet),freeze_sha=digest(f),score=score,reviews=reviews,financial=financial,registry_plan=registry_plan,registry_before=old,registry_after=reg,queries=outcomes,committed_at=now(),scope='MANUAL_INTERNAL_ONLY')
            c.execute('INSERT INTO gate_audit VALUES (?,?)',(sid,dump(audit)))
            return receipt

    def audit(self,sid):
        with self.db() as c:
            row=c.execute('SELECT data FROM gate_audit WHERE sid=?',(sid,)).fetchone()
            return json.loads(row[0]) if row else None
