"""V189 E3 omission-candidate correction overlay: source-bound, append-only, NO approvals.

An earlier model's `CONFIRMED_*_OMISSION` category is a *hypothesis*.
Before issuing any patch, inspect BOTH complete first/second journals for other-cue
coverage. Save E3 semantic source-only candidate repairs in a separate private
journal. No original review, frozen V6, V123, E4 or E5 is modified.

A claim ref is an immutable pointer to an already-written provisional claim,
not independent ground truth. A cross-cue coverage conclusion is model-authored,
never an automatically certified semantic equivalence.
"""
from __future__ import annotations
import json,os,stat,sqlite3
from pathlib import Path
from contextlib import contextmanager
from collections import Counter
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import ZERO,_canon,_digest

CONFIG_SCHEMA='IRE_V189_E3_OMISSION_OVERLAY_CONFIG_V1'
PACKET_SCHEMA='IRE_V189_E3_OMISSION_SOURCE_REPAIR_PACKET_V1'
ANSWER_SCHEMA='IRE_V189_E3_OMISSION_CHAT_REPAIR_RESPONSE_V1'
EVENT_SCHEMA='IRE_V189_E3_OMISSION_APPEND_ONLY_EVENT_V1'
TARGET_TYPES={'CONFIRMED_FIRST_PASS_OMISSION':'FIRST',
              'CONFIRMED_SECOND_PASS_OMISSION':'SECOND'}
RESOLUTIONS={'PROVISIONAL_NEW_CLAIM','COVERED_AT_DIFFERENT_ANCHOR',
             'CLAIM_BOUNDARY_OR_SCOPE_UNRESOLVED','NOT_AN_INDEPENDENT_ATOM'}
RESPONSE_FIELDS={'cue_index','original_category','resolution','reviewed_source_quote',
                 'source_quote_cue_index','source_context_cue_indices',
                 'other_pass_claim_ref','covered_pass_claim_ref','semantic_rationale',
                 'claim_truth_certified','independent_gold_certified','e3_certified',
                 'v123_approved','e4_approved','e5_published'}
REF_FIELDS={'pass','cue_index','ordinal','claim_sha256'}

def _need(v,msg):
    if not v: raise InvalidInput('V189_E3_'+msg)

def _sourcequote(t,q):
    return isinstance(q,str) and len(q.strip())>=3 and ' '.join(q.split()) in ' '.join(t.split())

class E3OmissionOverlay:
    def __init__(self, adjudication, db_path, *, create=False):
        self.adj=adjudication
        self.second=adjudication.second
        self.engine=self.second.engine
        self.path=Path(db_path)
        _need(self.path not in (self.engine.path,self.second.path,self.adj.path), 'SEPARATE_DB_REQUIRED')
        _need(not self.path.is_symlink(),'SYMLINK_REJECTED')
        source=self.engine.source
        with self.second._db() as db: sh,second=self.second._audit(db)
        with self.adj._db() as db: ah,adj=self.adj._audit(db)
        first=self.second._owner_snapshot()
        _need(len(first)==len(second)==len(source.cues) and len(adj)>=1,
              'REQUIRES_COMPLETE_DUAL_REVIEW_AND_ADJUDICATION')
        self.config={'schema':CONFIG_SCHEMA,'source_sha256':source.source_sha256,
                     'manifest_sha256':source.manifest_sha256,
                     'first_head':self.second.expected_owner_head,'second_head':sh,
                     'adjudication_head':ah,'video_id':source.video_id,
                     'quality_certified':False,'v123_approved':False,
                     'e4_approved':False,'e5_published':False}
        if self.path.exists():
            _need(not create,'EXISTING_DB_MUST_RESUME')
            _need(self.path.is_file() and not (stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  'PRIVATE_DB_PERMISSIONS')
        else:
            _need(create,'NO_AUTORESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL, event_sha TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS judgments(cue_index INTEGER PRIMARY KEY, event_sha TEXT NOT NULL, record TEXT NOT NULL)')
            row=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if row:
                _need(json.loads(row[0])==self.config,'CONFIG_TAMPER')
            else:
                db.execute('INSERT INTO config VALUES(1,?)',(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=20)
        db.row_factory=sqlite3.Row
        try:
            yield db;db.commit()
        except BaseException:
            db.rollback();raise
        finally:
            db.close()

    def _data(self):
        _need(self.engine.progress()['checkpoint_head_sha256']==self.config['first_head'],
              'FIRST_SOURCE_HEAD_CHANGED')
        first=self.second._owner_snapshot()
        with self.second._db() as db: sh,second=self.second._audit(db)
        with self.adj._db() as db: ah,adj=self.adj._audit(db)
        _need(sh==self.config['second_head'] and ah==self.config['adjudication_head'],
              'SECOND_OR_ADJUDICATION_HEAD_CHANGED')
        targets={i:x[1]['category'] for i,x in adj.items() if x[1]['category'] in TARGET_TYPES}
        _need(len(targets)>0 and len(first)==len(second)==len(self.engine.source.cues),
              'SOURCE_TARGET_CENSUS_CHANGED')
        return first,second,targets

    def _refs(self,rows,i,radius=8):
        out=[]
        for k in range(max(1,i-radius),min(len(self.engine.source.cues),i+radius)+1):
            for ordinal,claim in enumerate(rows[k][1]['claims'],1):
                out.append({'pass':None,'cue_index':k,'ordinal':ordinal,
                            'claim_sha256':_digest(claim),'claim':claim})
        return out

    def _valid_ref(self,ref,first,second):
        if ref is None:return False
        _need(type(ref) is dict and set(ref)==REF_FIELDS and ref['pass'] in ('FIRST','SECOND')
              and type(ref['cue_index']) is int and type(ref['ordinal']) is int,
              'CLAIM_REFERENCE_SHAPE')
        rows=first if ref['pass']=='FIRST' else second
        i=ref['cue_index'];n=ref['ordinal']
        _need(i in rows and 1<=n<=len(rows[i][1]['claims'])
              and ref['claim_sha256']==_digest(rows[i][1]['claims'][n-1]),
              'CLAIM_REFERENCE_SOURCE_MISMATCH')
        return True

    def _audit(self,db):
        first,second,targets=self._data()
        config=db.execute('SELECT value FROM config WHERE id=1').fetchone()
        _need(config and json.loads(config[0])==self.config,'CONFIG_CHANGED')
        prev=ZERO;present={}
        for j,r in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            frame=json.loads(r['payload'])
            _need(r['seq']==j and r['prev_sha']==prev and
                  frame.get('seq')==j and frame.get('prev_sha')==prev and
                  frame.get('schema')==EVENT_SCHEMA and
                  frame.get('source_sha256')==self.config['source_sha256'] and
                  frame.get('first_head')==self.config['first_head'] and
                  frame.get('second_head')==self.config['second_head'] and
                  frame.get('adjudication_head')==self.config['adjudication_head'] and
                  frame.get('e3_certified') is False and
                  frame.get('v123_approved') is False and
                  frame.get('e4_approved') is False and frame.get('e5_published') is False and
                  _canon(frame).decode()==r['payload'] and
                  _digest(frame)==r['event_sha'],'EVENT_CHAIN_OR_AUTHORITY_TAMPER')
            for a in frame['answers']:
                i=a['cue_index']
                _need(i in targets and i not in present and
                      a['original_category']==targets[i],
                      'EVENT_TARGET_INVALID_OR_DUPLICATE')
                self._validate_one(a,first,second,targets)
                present[i]=(r['event_sha'],a)
            prev=r['event_sha']
        table=db.execute('SELECT * FROM judgments').fetchall()
        _need(len(table)==len(present),'JUDGMENT_COUNT_TAMPER')
        for row in table:
            _need(row['cue_index'] in present and
                  row['event_sha']==present[row['cue_index']][0] and
                  json.loads(row['record'])==present[row['cue_index']][1],
                  'JUDGMENT_RECORD_TAMPER')
        return prev,present

    def prepare(self,*,cue_indices=None,limit=12,context_radius=5):
        _need(type(limit) is int and 1<=limit<=12 and
              type(context_radius) is int and 2<=context_radius<=12,
              'REVIEW_WINDOW_INVALID')
        first,second,targets=self._data()
        with self._db() as db: head,done=self._audit(db)
        remaining=sorted(set(targets)-set(done))
        if cue_indices is None:selected=remaining[:limit]
        else:
            _need(type(cue_indices) is list and 0<len(cue_indices)<=limit and
                  cue_indices==sorted(set(cue_indices)) and
                  set(cue_indices)<=set(remaining),'TARGET_SELECTION_INVALID')
            selected=cue_indices
        if not selected:return {'type':'E3_OMISSION_REVIEW_FINISHED_STILL_HOLD',
                                'e3_certified':False,'e4_approved':False,'e5_published':False}
        allctx=set()
        for i in selected:
            allctx.update(range(max(1,i-context_radius),min(len(self.engine.source.cues),i+context_radius)+1))
        qs=[]
        for i in selected:
            qs.append({'cue_index':i,'original_category':targets[i],
                       'first_pass_local':first[i][1], 'second_pass_local':second[i][1],
                       'first_nearby_claims':[dict(x,**{'pass':'FIRST'}) for x in self._refs(first,i)],
                       'second_nearby_claims':[dict(x,**{'pass':'SECOND'}) for x in self._refs(second,i)],
                       'source_text_sha256':sha256(self.engine.source.cues[i-1].text.encode())})
        packet={'schema':PACKET_SCHEMA,'type':'E3_RECHECK_OMISSION_LABEL_BEFORE_PATCH',
                'source_sha256':self.config['source_sha256'],
                'first_head':self.config['first_head'],'second_head':self.config['second_head'],
                'adjudication_head':self.config['adjudication_head'],
                'repair_head':head,'cue_indices':selected,'context_radius':context_radius,
                'source_context':[{'cue_index':i,'text':self.engine.source.cues[i-1].text}
                                  for i in sorted(allctx)],
                'targets':qs,'no_gold_or_financial_approval':True}
        return {**packet,'challenge_sha256':_digest(packet)}

    def _validate_one(self,record,first,second,targets):
        _need(type(record) is dict and set(record)==RESPONSE_FIELDS,
              'ANSWER_FIELDS')
        i=record['cue_index'];original=targets.get(i)
        _need(original is not None and record['original_category']==original and
              record['resolution'] in RESOLUTIONS and
              all(record[k] is False for k in ('claim_truth_certified','independent_gold_certified',
                  'e3_certified','v123_approved','e4_approved','e5_published')) and
              type(record['semantic_rationale']) is str and len(record['semantic_rationale'].strip())>=75,
              'ANSWER_TARGET_OR_AUTHORITY')
        idx=record['source_quote_cue_index'];ctx=record['source_context_cue_indices']
        _need(type(idx) is int and 1<=idx<=len(self.engine.source.cues) and
              abs(idx-i)<=8 and type(ctx) is list and ctx==sorted(set(ctx)) and
              1<=len(ctx)<=16 and all(type(k) is int and 1<=k<=len(self.engine.source.cues)
                     and abs(k-i)<=12 for k in ctx) and idx in ctx and i in ctx and
              _sourcequote(self.engine.source.cues[idx-1].text,record['reviewed_source_quote']),
              'SOURCE_QUOTE_OR_CONTEXT_NOT_PINNED')
        other=record['other_pass_claim_ref']; covered=record['covered_pass_claim_ref']
        if other is not None:self._valid_ref(other,first,second)
        if covered is not None:self._valid_ref(covered,first,second)
        missing_pass=TARGET_TYPES[original]
        if record['resolution']=='PROVISIONAL_NEW_CLAIM':
            _need(other is not None and other['pass']!=missing_pass and covered is None and
                  abs(other['cue_index']-i)<=8 and
                  i in (first if other['pass']=='FIRST' else second)[other['cue_index']][1]['claims'][other['ordinal']-1]['context_cue_indices'],
                  'REPAIR_MUST_POINT_TO_OTHER_PASS_SOURCE_CLAIM')
        elif record['resolution']=='COVERED_AT_DIFFERENT_ANCHOR':
            _need(other is None and covered is not None and covered['pass']==missing_pass and
                  abs(covered['cue_index']-i)<=8 and
                  i in (first if missing_pass=='FIRST' else second)[covered['cue_index']][1]['claims'][covered['ordinal']-1]['context_cue_indices'],
                  'COVERAGE_MUST_REFERENCE_ALREADY_PRESENT_PARENT')
        else:
            _need(other is None and covered is None,'UNRESOLVED_MUST_NOT_EMIT_PATCH')

    def submit(self,packet,answer):
        _need(type(packet) is dict and packet.get('type')=='E3_RECHECK_OMISSION_LABEL_BEFORE_PATCH' and
              packet.get('challenge_sha256')==_digest({k:v for k,v in packet.items() if k!='challenge_sha256'}),
              'PACKET_DIGEST_INVALID')
        regen=self.prepare(cue_indices=packet.get('cue_indices'),limit=len(packet.get('cue_indices',[])),
                           context_radius=packet.get('context_radius'))
        _need(regen==packet,'STALE_OR_FORGED_PACKET')
        _need(type(answer) is dict and set(answer)=={'schema','challenge_sha256','review_executor','answers'}
              and answer['schema']==ANSWER_SCHEMA and answer['challenge_sha256']==packet['challenge_sha256']
              and answer['review_executor']=='CHATGPT_IN_CHAT' and
              type(answer['answers']) is list and len(answer['answers'])==len(packet['cue_indices']),
              'RESPONSE_SCHEMA')
        first,second,targets=self._data()
        for i,v in zip(packet['cue_indices'],answer['answers']):
            _need(v['cue_index']==i,'ANSWER_CUE_ORDER')
            self._validate_one(v,first,second,targets)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,done=self._audit(db)
            _need(head==packet['repair_head'] and not set(packet['cue_indices'])&set(done),
                  'STALE_OR_DUPLICATE_EVENT')
            seq=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1
            frame={'schema':EVENT_SCHEMA,'seq':seq,'prev_sha':head,
                   'source_sha256':self.config['source_sha256'],
                   'first_head':self.config['first_head'],
                   'second_head':self.config['second_head'],
                   'adjudication_head':self.config['adjudication_head'],
                   'challenge_sha256':packet['challenge_sha256'],
                   'answers':answer['answers'],'e3_certified':False,
                   'v123_approved':False,'e4_approved':False,'e5_published':False}
            event_sha=_digest(frame)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',
                       (seq,head,event_sha,_canon(frame).decode()))
            for entry in answer['answers']:
                db.execute('INSERT INTO judgments VALUES(?,?,?)',
                           (entry['cue_index'],event_sha,_canon(entry).decode()))
        return self.status()

    def status(self):
        with self._db() as db:head,rows=self._audit(db)
        counts=Counter(row['resolution'] for _,row in rows.values())
        return {'schema':'IRE_V189_E3_OMISSION_CANDIDATE_STATUS_HOLD_V1',
                'source_sha256':self.config['source_sha256'],
                'first_head':self.config['first_head'],'second_head':self.config['second_head'],
                'adjudication_head':self.config['adjudication_head'],
                'overlay_head':head,'targets':len(self._data()[2]),'reviewed':len(rows),
                'pending_cue_indices':sorted(set(self._data()[2])-set(rows)),
                'cause_corrections':dict(sorted(counts.items())),
                'provisional_additions':sum(x['resolution']=='PROVISIONAL_NEW_CLAIM' for _,x in rows.values()),
                'owner_journals_immutable':True,'financial_claims_approved':0,
                'independent_gold_certified':False,'e3_quality_certified':False,
                'e4_approved':False,'e5_published':False}