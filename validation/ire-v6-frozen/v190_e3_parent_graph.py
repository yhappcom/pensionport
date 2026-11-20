"""V190 E3 provisional parent-claim relation review, no semantic auto-merge.

A lexical/nearby candidate is only a retrieval hypothesis. This journal binds a
second source-grounded, ChatGPT-in-chat review to both unmodified V176/V183
journals, V184 cause ledger, V189 corrective overlay and V189 source-screen
packet. Reviewer comments cannot be promoted into V6 facts or E4 approvals.
"""
from __future__ import annotations
import json, os, sqlite3, stat
from collections import Counter
from pathlib import Path
from contextlib import contextmanager
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import ZERO, _canon, _digest
from v189_e3_parent_alignment_screen import generate_packet,validate_live

CONFIG='IRE_V190_E3_PARENT_GRAPH_CONFIG_V1'
CHALLENGE='IRE_V190_E3_PARENT_GRAPH_SOURCE_CHALLENGE_V1'
RESPONSE='IRE_V190_E3_PARENT_GRAPH_CHAT_RESPONSE_V1'
EVENT='IRE_V190_E3_PARENT_GRAPH_APPEND_ONLY_EVENT_V1'
DECISIONS={'PROVISIONAL_SAME_PROPOSITION','DISTINCT_PROPOSITIONS','PARENT_CHILD_RELATED',
           'MULTIPLE_POSSIBLE_KEEP_OPEN','NO_HEURISTIC_PAIR_KEEP_OPEN'}
ANSWER_KEYS={'cue_index','decision','pair_ref','first_quote','first_quote_cue',
             'second_quote','second_quote_cue','semantic_rationale',
             'independent_gold_certified','e3_certified','v123_approved','e4_approved','e5_published'}


def _need(cond,code):
    if not cond: raise InvalidInput('V190_PARENT_'+code)


def _matches(cue,quote):
    return isinstance(quote,str) and len(quote.strip())>=3 and \
        ' '.join(quote.split()) in ' '.join(cue.text.split())


class E3ParentGraphReview:
    def __init__(self,adjudication,omission,db_path,*,v189_screen_packet,v189_screen_answer,create=False):
        self.adj=adjudication
        self.omission=omission
        self.second=adjudication.second
        self.engine=self.second.engine
        self.path=Path(db_path)
        self.source=self.engine.source.cues
        _need(not self.path.is_symlink(),'DB_SYMLINK')
        _need(self.path not in (self.engine.path,self.second.path,adjudication.path,omission.path),
              'MUST_USE_SEPARATE_DB')
        regenerated=generate_packet(adjudication)
        _need(v189_screen_packet==regenerated,'V189_PACKET_NOT_REGENERATED')
        validate_live(adjudication,v189_screen_packet,v189_screen_answer)
        self.parent_packet=v189_screen_packet
        self.screen_answer=v189_screen_answer
        self.review_cases={c['cue_index']:c for c,r in zip(regenerated['cases'],v189_screen_answer['reviews'])
                           if r['assessment']!='PROVISIONAL_SAME_PARENT'}
        self.prior_assessments={r['cue_index']:r['assessment'] for r in v189_screen_answer['reviews']}
        _need(len(self.review_cases)>0,'NO_SOURCE_REVIEW_TARGETS')
        with omission._db() as d:
            self.omission_head,reviewed=omission._audit(d)
        _need(len(reviewed)>0,'OMISSION_OVERLAY_NOT_FROZEN')
        self.config={
            'schema':CONFIG,'source_sha256':self.engine.source.source_sha256,
            'first_head':self.second.expected_owner_head,
            'second_head':regenerated['second_head'],
            'adjudication_head':regenerated['adjudication_head'],
            'omission_head':self.omission_head,
            'v189_screen_packet_sha256':regenerated['packet_sha256'],
            'v189_screen_answer_sha256':_digest(v189_screen_answer),
            'review_scope':sorted(self.review_cases),
            'independent_gold_certified':False,'e3_certified':False,
            'v123_approved':False,'e4_approved':False,'e5_published':False,
        }
        if self.path.exists():
            _need(not create and self.path.is_file() and not(stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  'EXISTING_PRIVATE_DB_REQUIRED')
        else:
            _need(create,'NO_AUTO_RESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        with self._db() as d:
            d.execute('CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL)')
            d.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,prev_sha TEXT NOT NULL,event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            d.execute('CREATE TABLE IF NOT EXISTS judgments(cue_index INTEGER PRIMARY KEY,event_sha TEXT NOT NULL,record TEXT NOT NULL)')
            row=d.execute('SELECT value FROM config WHERE id=1').fetchone()
            if row:_need(json.loads(row[0])==self.config,'CONFIG_TAMPER')
            else:d.execute('INSERT INTO config VALUES(1,?)',(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=30)
        db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()

    def _pinned(self):
        _need(self.engine.progress()['checkpoint_head_sha256']==self.config['first_head'],
              'OWNER_CHANGED')
        pkt=generate_packet(self.adj)
        _need(pkt==self.parent_packet,'SECOND_OR_ADJUDICATION_CHANGED')
        with self.omission._db() as d:oh,_=self.omission._audit(d)
        _need(oh==self.config['omission_head'],'OMISSION_CHANGED')
        _need(_digest(self.screen_answer)==self.config['v189_screen_answer_sha256'],
              'SCREEN_ANSWER_CHANGED')

    def _check_one(self,a,case):
        _need(type(a) is dict and set(a)==ANSWER_KEYS and type(a['cue_index']) is int
              and a['cue_index']==case['cue_index'] and a['decision'] in DECISIONS
              and all(a[k] is False for k in ('independent_gold_certified','e3_certified',
                      'v123_approved','e4_approved','e5_published'))
              and isinstance(a['semantic_rationale'],str) and len(a['semantic_rationale'].strip())>=75,
              'VERDICT_SHAPE_AUTHORITY')
        candidates=case['candidate_pairs']
        if not candidates:
            _need(a['decision']=='NO_HEURISTIC_PAIR_KEEP_OPEN' and a['pair_ref'] is None
                  and a['first_quote'] is None and a['second_quote'] is None
                  and a['first_quote_cue'] is None and a['second_quote_cue'] is None,
                  'NO_HEURISTIC_PAIR_CANNOT_CREATE_A_PAIR')
            return
        if a['decision']=='MULTIPLE_POSSIBLE_KEEP_OPEN':
            _need(a['pair_ref'] is None and a['first_quote'] is None
                  and a['second_quote'] is None and a['first_quote_cue'] is None
                  and a['second_quote_cue'] is None,'AMBIGUOUS_REVIEW_MUST_NOT_PICK_PAIR')
            return
        selected=[p for p in candidates if p['ref']==a['pair_ref']]
        _need(len(selected)==1,'PAIR_NOT_IN_FROZEN_CANDIDATES')
        p=selected[0]
        for key,ixkey,allowed in (
            ('first_quote','first_quote_cue',p['first_context_indices']),
            ('second_quote','second_quote_cue',p['second_context_indices'])):
            i=a[ixkey]
            _need(type(i) is int and i in allowed and 1<=i<=len(self.source)
                  and _matches(self.source[i-1],a[key]),'PAIR_EVIDENCE_NOT_SOURCE_PINNED')
        _need(a['decision'] in ('PROVISIONAL_SAME_PROPOSITION','DISTINCT_PROPOSITIONS',
                                'PARENT_CHILD_RELATED'),'INVALID_PAIR_DECISION')

    def _audit(self,db):
        self._pinned()
        row=db.execute('SELECT value FROM config WHERE id=1').fetchone()
        _need(row and json.loads(row[0])==self.config,'DB_CONFIG_MODIFIED')
        prev=ZERO;by_cue={}
        for sequence,r in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            item=json.loads(r['payload'])
            _need(r['seq']==sequence and r['prev_sha']==prev and item.get('seq')==sequence
                  and item.get('prev_sha')==prev and item.get('schema')==EVENT
                  and item.get('source_sha256')==self.config['source_sha256']
                  and item.get('config_sha256')==_digest(self.config)
                  and item.get('e3_certified') is False
                  and item.get('e4_approved') is False and item.get('e5_published') is False
                  and _canon(item).decode()==r['payload'] and _digest(item)==r['event_sha'],
                  'EVENT_CHAIN_TAMPER')
            for a in item['answers']:
                i=a['cue_index']
                _need(i in self.review_cases and i not in by_cue,'EVENT_INVALID_TARGET')
                self._check_one(a,self.review_cases[i])
                by_cue[i]=(r['event_sha'],a)
            prev=r['event_sha']
        saved=db.execute('SELECT * FROM judgments').fetchall()
        _need(len(saved)==len(by_cue),'RESULT_COUNT_TAMPER')
        for r in saved:
            _need(r['cue_index'] in by_cue and r['event_sha']==by_cue[r['cue_index']][0]
                  and json.loads(r['record'])==by_cue[r['cue_index']][1],
                  'RESULT_ROW_TAMPER')
        return prev,by_cue

    def prepare(self,*,cue_indices=None,limit=8,radius=5):
        _need(type(limit) is int and 1<=limit<=12 and type(radius) is int and 2<=radius<=8,
              'REVIEW_LIMIT')
        with self._db() as d:head,done=self._audit(d)
        remaining=sorted(set(self.review_cases)-set(done))
        if cue_indices is None:chosen=remaining[:limit]
        else:
            _need(type(cue_indices) is list and len(cue_indices)>0 and len(cue_indices)<=limit
                  and cue_indices==sorted(set(cue_indices)) and set(cue_indices)<=set(remaining),
                  'INVALID_SELECTION')
            chosen=cue_indices
        if not chosen:return {'type':'E3_PARENT_REVIEW_COMPLETE_STILL_UNAPPROVED',**self.status()}
        contexts=set()
        for i in chosen:contexts.update(range(max(1,i-radius),min(len(self.source),i+radius)+1))
        payload={'schema':CHALLENGE,'type':'E3_SEMANTIC_PARENT_RELATION_REVIEW',
                 'source_sha256':self.config['source_sha256'],
                 'config_sha256':_digest(self.config),'review_head':head,
                 'cue_indices':chosen,'radius':radius,
                 'targets':[{'cue_index':i,'case':self.review_cases[i],
                             'prior_screen_assessment':self.prior_assessments[i]}
                            for i in chosen],
                 'source_context':[{'cue_index':i,'text':self.source[i-1].text,
                                    'sha256':sha256(self.source[i-1].text.encode())}
                                   for i in sorted(contexts)],
                 'meaning_not_certified':True,'e3_certified':False,
                 'e4_approved':False,'e5_published':False}
        return {**payload,'challenge_sha256':_digest(payload)}

    def submit(self,challenge,response):
        _need(type(challenge) is dict and challenge.get('type')=='E3_SEMANTIC_PARENT_RELATION_REVIEW'
              and challenge.get('challenge_sha256')==_digest({k:v for k,v in challenge.items() if k!='challenge_sha256'}),
              'CHALLENGE_HASH')
        regenerated=self.prepare(cue_indices=challenge['cue_indices'],
                                 limit=len(challenge['cue_indices']),radius=challenge['radius'])
        _need(challenge==regenerated,'CHALLENGE_NOT_ENGINE_ISSUED')
        _need(type(response) is dict and set(response)=={'schema','challenge_sha256',
              'review_executor','answers'} and response['schema']==RESPONSE
              and response['challenge_sha256']==challenge['challenge_sha256']
              and response['review_executor']=='CHATGPT_IN_CHAT'
              and type(response['answers']) is list
              and len(response['answers'])==len(challenge['cue_indices']),
              'RESPONSE_HEADER')
        for i,a in zip(challenge['cue_indices'],response['answers']):
            _need(a.get('cue_index')==i,'WRONG_CUE_ORDER')
            self._check_one(a,self.review_cases[i])
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,done=self._audit(db)
            _need(head==challenge['review_head']
                  and not(set(challenge['cue_indices'])&set(done)),
                  'STALE_OR_DUPLICATE')
            seq=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1
            frame={'schema':EVENT,'seq':seq,'prev_sha':head,
                   'source_sha256':self.config['source_sha256'],
                   'config_sha256':_digest(self.config),
                   'challenge_sha256':challenge['challenge_sha256'],
                   'answers':response['answers'],
                   'e3_certified':False,'e4_approved':False,'e5_published':False}
            h=_digest(frame)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',(seq,head,h,_canon(frame).decode()))
            for a in response['answers']:
                db.execute('INSERT INTO judgments VALUES(?,?,?)',
                           (a['cue_index'],h,_canon(a).decode()))
            return self.status(_trusted_db=db)

    def status(self,_trusted_db=None):
        if _trusted_db is None:
            with self._db() as db:head,done=self._audit(db)
        else:head,done=self._audit(_trusted_db)
        counts=Counter(x[1]['decision'] for x in done.values())
        return {'schema':'IRE_V190_E3_PARENT_GRAPH_REVIEW_STATUS_HOLD_V1',
                'source_sha256':self.config['source_sha256'],
                'parent_screen_sha256':self.config['v189_screen_packet_sha256'],
                'review_head':head,'targets':len(self.review_cases),
                'reviewed':len(done),'pending':len(self.review_cases)-len(done),
                'counts':dict(sorted(counts.items())),
                'no_automatic_claim_merge':True,
                'independent_gold_certified':False,'e3_certified':False,
                'v123_approved':False,'e4_approved':False,'e5_published':False}

    def provisional_new_claims(self):
        """Read-only six claim refs. Opinion != financial fact; E3 not certified."""
        self._pinned()
        first=self.second._owner_snapshot()
        with self.second._db() as db:_,second=self.second._audit(db)
        with self.omission._db() as db:_,reviewed=self.omission._audit(db)
        items=[]
        for i,(_,a) in sorted(reviewed.items()):
            if a['resolution']!='PROVISIONAL_NEW_CLAIM':continue
            ref=a['other_pass_claim_ref']
            rows=first if ref['pass']=='FIRST' else second
            claim=rows[ref['cue_index']][1]['claims'][ref['ordinal']-1]
            _need(_digest(claim)==ref['claim_sha256'],'OMISSION_REF_REBOUND')
            items.append({'cue_index':i,'source_quote':a['reviewed_source_quote'],
                          'candidate_ref':ref,'kind':claim['kind'],
                          'proposition':claim['proposition'],'conditions':claim['conditions'],
                          'exceptions':claim['exceptions'],
                          'high_risk_candidate':claim['high_risk'],
                          'source_quote_verified':True,
                          'source_financial_truth_certified':False,
                          'independent_gold_certified':False,
                          'addition_to_v176':False,'e3_certified':False,'e4_approved':False})
        _need(len(items)>0,'NO_PROVISIONAL_CANDIDATES')
        return items