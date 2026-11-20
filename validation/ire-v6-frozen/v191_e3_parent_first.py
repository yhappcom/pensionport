"""V191: owner-source parent-utterance-first E3 reviewer journal (NOT E4).

This is a genuine semantic input/workflow boundary, not a segmentation heuristic.
ChatGPT first identifies a parent span from the ORIGINAL SRT, and writes distinct
source-quoted atomic statements inside it. Existing first/second atomic verdicts
are not included in a review packet. An independent gold set remains absent.
"""
from __future__ import annotations
import json
import os
import sqlite3
import stat
from pathlib import Path
from contextlib import contextmanager
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import ZERO, _canon, _digest, EngineChatSession

PACKET='IRE_V191_E3_PARENT_FIRST_CHALLENGE_V1'
ANSWER='IRE_V191_E3_PARENT_FIRST_CHAT_ANSWER_V1'
EVENT='IRE_V191_E3_PARENT_FIRST_APPEND_ONLY_EVENT_V1'
CONFIG='IRE_V191_E3_PARENT_FIRST_SESSION_V1'
INTENT={'INTRO','EXPLANATION','OPINION','RECOMMENDATION','QUESTION',
        'HYPOTHETICAL_EXAMPLE','SUMMARY','TRANSITION','OTHER'}
KINDS={'FACT','OPINION','QUESTION','RECOMMENDATION','HYPOTHETICAL','MATH','ANECDOTE'}
ROLE={'HOST','GUEST','NARRATOR','UNKNOWN'}
PROVENANCE={'SOURCE_SPOKEN'}
ISSUES={'AUDIO_ASR','SCREEN_CHART','HISTORICAL_SCOPE','FACT_SCOPE','MISSING_SOURCE','OTHER'}


def _need(x, reason):
    if not x:raise InvalidInput('V191_PARENT_FIRST_'+reason)


def _quoted(source, index, quote):
    return type(index) is int and 1<=index<=len(source.cues) and \
      type(quote) is str and len(quote.strip())>=2 and \
      ' '.join(quote.split()) in ' '.join(source.cues[index-1].text.split())

class E3ParentFirst:
    def __init__(self, owner:EngineChatSession, second, db_path, *,
                 expected_owner_head, expected_second_head, create=False, max_span=14):
        self.owner,self.second=owner,second
        self.source=owner.source
        self.path=Path(db_path)
        _need(1<=max_span<=20,'MAX_SPAN')
        self.max_span=max_span
        _need(self.path not in (owner.path,second.path) and not self.path.is_symlink(),
              'MUST_USE_SEPARATE_PRIVATE_DB')
        self.config={'schema':CONFIG,'source_sha256':self.source.source_sha256,
                     'video_id':self.source.video_id,'owner_head':expected_owner_head,
                     'second_head':expected_second_head,
                     'cue_count':len(self.source.cues),'max_span':max_span,
                     'independent_gold':False,'e3_certified':False,
                     'v123_approved':False,'e4_approved':False,'e5_published':False}
        self._check_pins()
        if self.path.exists():
            _need(not create and self.path.is_file() and
                  not (stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  'EXISTING_PRIVATE_DB_REQUIRED')
        else:
            _need(create,'CANNOT_AUTO_RESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL, event_sha TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS parent_units (start_cue INTEGER PRIMARY KEY, end_cue INTEGER UNIQUE NOT NULL, event_sha TEXT NOT NULL, record TEXT NOT NULL)')
            row=db.execute('SELECT data FROM config WHERE id=1').fetchone()
            if row:_need(json.loads(row[0])==self.config,'CONFIG_TAMPER')
            else:db.execute('INSERT INTO config VALUES(1,?)',(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15)
        db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()

    def _check_pins(self):
        _need(self.owner.progress()['checkpoint_head_sha256']==self.config['owner_head'],
              'OWNER_HEAD_CHANGED')
        s=self.second.status()
        _need(self.owner.progress()['cue_remaining']==0 and s['unreviewed_cues']==0,
              'PRIOR_FULL_CENSUS_REQUIRED')
        _need(s['second_review_audit_head_sha256']==self.config['second_head'],
              'SECOND_HEAD_CHANGED')
        _need(self.source.source_sha256==self.config['source_sha256'],
              'OWNER_SOURCE_CHANGED')

    def _check_parent(self, rec, start, stop):
        _need(type(rec) is dict and set(rec)=={'start_cue','end_cue','parent_intent','speaker_role',
                'parent_summary','claims','claim_relations','scope_links','open_issues','analysis',
                'independent_gold_certified','e3_certified','v123_approved','e4_approved','e5_published'}
                and rec['start_cue']==start and rec['end_cue']==stop
                and rec['parent_intent'] in INTENT and rec['speaker_role'] in ROLE
                and isinstance(rec['parent_summary'],str) and len(rec['parent_summary'].strip())>=8
                and isinstance(rec['analysis'],str) and len(rec['analysis'].strip())>=35
                and all(rec[k] is False for k in ['independent_gold_certified','e3_certified',
                    'v123_approved','e4_approved','e5_published']),
              'RESPONSE_SHAPE_OR_APPROVAL_FORGERY')
        claims=rec['claims']; _need(type(claims) is list and len(claims)<=12,'CLAIM_COUNT')
        for claim in claims:
            _need(type(claim) is dict and set(claim)=={'kind','proposition','quote','quote_cue',
                    'evidence_cues','numbers','spoken_conditions','spoken_exceptions',
                    'reviewer_caveats','high_risk','needs_official_source','source_truth_certified'}
                    and claim['kind'] in KINDS and type(claim['proposition']) is str
                    and len(claim['proposition'].strip())>=12
                    and type(claim['quote_cue']) is int and start<=claim['quote_cue']<=stop
                    and _quoted(self.source,claim['quote_cue'],claim['quote'])
                    and type(claim['evidence_cues']) is list
                    and bool(claim['evidence_cues'])
                    and all(type(c) is int and start<=c<=stop for c in claim['evidence_cues'])
                    and claim['evidence_cues']==sorted(set(claim['evidence_cues']))
                    and claim['quote_cue'] in claim['evidence_cues']
                    and type(claim['numbers']) is list
                    and type(claim['spoken_conditions']) is list
                    and type(claim['spoken_exceptions']) is list
                    and type(claim['reviewer_caveats']) is list
                    and all(type(x) is str and len(x.strip())>=6 for x in claim['reviewer_caveats'])
                    and type(claim['high_risk']) is bool
                    and type(claim['needs_official_source']) is bool
                    and claim['source_truth_certified'] is False,
                  'CLAIM_UNGROUNDED_OR_BAD_SCHEMA')
            for x in claim['numbers']:
                _need(type(x) is dict and set(x)=={'cue_index','token'}
                    and type(x['token']) is str and len(x['token'])>0
                    and type(x['cue_index']) is int and x['cue_index'] in claim['evidence_cues']
                    and x['token'] in self.source.cues[x['cue_index']-1].text,
                    'NUMBER_NOT_IN_SOURCE')
            for group in ['spoken_conditions','spoken_exceptions']:
                for x in claim[group]:
                    _need(type(x) is dict and set(x)=={'cue_index','quote','provenance'}
                         and x['provenance'] in PROVENANCE
                         and type(x['cue_index']) is int
                         and x['cue_index'] in claim['evidence_cues']
                         and _quoted(self.source,x['cue_index'],x['quote']),
                         'SPOKEN_QUALIFIER_NOT_IN_SOURCE')
        _need(type(rec['claim_relations']) is list and len(rec['claim_relations'])<=20,
              'CLAIM_RELATION_COUNT')
        for relation in rec['claim_relations']:
            _need(type(relation) is dict and set(relation)=={'from_claim','to_claim','relation'}
                  and relation['relation'] in {'DISTINCT_FROM','ELABORATES','CONTRASTS','CONDITION_FOR'}
                  and type(relation['from_claim']) is int
                  and type(relation['to_claim']) is int
                  and 1<=relation['from_claim']<=len(claims)
                  and 1<=relation['to_claim']<=len(claims)
                  and relation['from_claim']!=relation['to_claim'],
                  'CLAIM_RELATION_INVALID')
        _need(type(rec['scope_links']) is list and len(rec['scope_links'])<=15,'SCOPE_LINK_COUNT')
        for link in rec['scope_links']:
            _need(type(link) is dict and set(link)=={'antecedent_cue','antecedent_quote',
                   'applies_to_claim_indices','relation'}
                  and link['relation'] in {'HYPOTHETICAL_EXAMPLE','INDEX_SCOPE','AS_OF_LIMIT'}
                  and type(link['antecedent_cue']) is int
                  and max(1,start-32)<=link['antecedent_cue']<start
                  and _quoted(self.source,link['antecedent_cue'],link['antecedent_quote'])
                  and type(link['applies_to_claim_indices']) is list
                  and bool(link['applies_to_claim_indices'])
                  and link['applies_to_claim_indices']==sorted(set(link['applies_to_claim_indices']))
                  and all(type(n) is int and 1<=n<=len(claims)
                          for n in link['applies_to_claim_indices']),
                  'UNSUPPORTED_UPSTREAM_SCOPE')
        _need(type(rec['open_issues']) is list,'ISSUE_SCHEMA')
        for issue in rec['open_issues']:
            _need(type(issue) is dict and set(issue)=={'cue_index','issue_kind','reason'}
                and type(issue['cue_index']) is int and start<=issue['cue_index']<=stop
                and issue['issue_kind'] in ISSUES
                and type(issue['reason']) is str and len(issue['reason'].strip())>=14,
                'ISSUE_NOT_GROUNDED')

    def _audit(self,db):
        self._check_pins()
        config=db.execute('SELECT data FROM config WHERE id=1').fetchone()
        _need(config and json.loads(config[0])==self.config,'CONFIG_TAMPER')
        records=[];prev=ZERO;cursor=1
        for n,row in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            event=json.loads(row['payload'])
            _need(row['seq']==n and row['prev_sha']==prev
                  and event.get('schema')==EVENT and event.get('seq')==n
                  and event.get('prev_sha')==prev and event.get('config_sha256')==_digest(self.config)
                  and event.get('source_sha256')==self.config['source_sha256']
                  and _canon(event).decode()==row['payload'] and _digest(event)==row['event_sha'],
                  'EVENT_CHAIN_TAMPER')
            rec=event.get('review')
            _need(type(rec) is dict and rec.get('start_cue')==cursor
                  and type(rec.get('end_cue')) is int and cursor<=rec['end_cue']<=len(self.source.cues)
                  and rec['end_cue']-cursor+1<=self.max_span,
                  'SPAN_COVERAGE_TAMPER')
            self._check_parent(rec,cursor,rec['end_cue'])
            records.append((row['event_sha'],rec))
            cursor=rec['end_cue']+1
            prev=row['event_sha']
        saved=db.execute('SELECT * FROM parent_units ORDER BY start_cue').fetchall()
        _need(len(saved)==len(records),'PARENT_RECORD_COUNT_TAMPER')
        for row,(sha,rec) in zip(saved,records):
            _need(row['start_cue']==rec['start_cue'] and row['end_cue']==rec['end_cue']
                and row['event_sha']==sha and json.loads(row['record'])==rec,
                'PARENT_RECORD_TAMPER')
        return prev,records,cursor

    def prepare(self,span_end,*,context_radius=3):
        _need(type(span_end) is int and type(context_radius) is int and 1<=context_radius<=8,
              'SPAN_END_REQUIRED_BY_CHATGPT')
        with self._db() as db:head,rows,cursor=self._audit(db)
        return self._make_packet(span_end,context_radius,head,rows,cursor)

    def _make_packet(self,span_end,context_radius,head,rows,cursor):
        _need(cursor<=len(self.source.cues),'ALL_PARENTS_ALREADY_REVIEWED')
        _need(cursor<=span_end<=min(len(self.source.cues),cursor+self.max_span-1),
              'OUT_OF_ORDER_OR_TOO_LONG')
        contexts=range(max(1,cursor-context_radius),min(len(self.source.cues),span_end+context_radius)+1)
        packet={'schema':PACKET,'type':'E3_PARENT_FIRST_SOURCE_ONLY',
                'source_sha256':self.config['source_sha256'],
                'owner_manifest_sha256':self.source.manifest_sha256,
                'review_head':head,'parent_seq':len(rows)+1,
                'context_radius':context_radius,'start_cue':cursor,'end_cue':span_end,
                'original_cues':[{'cue_index':i,'text':self.source.cues[i-1].text,
                                  'text_sha256':sha256(self.source.cues[i-1].text.encode())}
                                 for i in range(cursor,span_end+1)],
                'surrounding_original_only':[{'cue_index':i,'text':self.source.cues[i-1].text}
                                             for i in contexts if i<cursor or i>span_end],
                'previous_verdicts_or_atoms_exposed':False,
                'independent_gold_certified':False,'e3_certified':False,
                'v123_approved':False,'e4_approved':False,'e5_published':False}
        packet['challenge_sha256']=_digest(packet)
        return packet

    def submit(self,packet,answer):
        _need(type(packet) is dict and type(answer) is dict
            and set(answer)=={'schema','challenge_sha256','review_executor','parent'}
            and answer['schema']==ANSWER and answer['review_executor']=='CHATGPT_IN_CHAT'
            and answer['challenge_sha256']==packet.get('challenge_sha256'),
            'ANSWER_WRAPPER')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,records,cursor=self._audit(db)
            _need(type(packet.get('end_cue')) is int and cursor<=packet['end_cue']
                and type(packet.get('context_radius')) is int
                and 1<=packet['context_radius']<=8
                and packet==self._make_packet(packet['end_cue'],packet['context_radius'],
                                              head,records,cursor),
                'STALE_OR_FORGED_CHALLENGE')
            r=answer['parent'];self._check_parent(r,cursor,packet['end_cue'])
            event={'schema':EVENT,'seq':len(records)+1,'prev_sha':head,
                   'config_sha256':_digest(self.config),
                   'source_sha256':self.config['source_sha256'],
                   'packet_sha256':packet['challenge_sha256'],'review':r,
                   'e3_certified':False,'v123_approved':False,
                   'e4_approved':False,'e5_published':False}
            event_sha=_digest(event)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',
                       (event['seq'],head,event_sha,_canon(event).decode()))
            db.execute('INSERT INTO parent_units VALUES(?,?,?,?)',
                       (r['start_cue'],r['end_cue'],event_sha,_canon(r).decode()))
        return self.status()

    def status(self):
        with self._db() as db:head,rows,cursor=self._audit(db)
        return {'schema':'IRE_V191_E3_PARENT_FIRST_STATUS_V1',
                'source_sha256':self.source.source_sha256,
                'owner_head':self.config['owner_head'],
                'second_head':self.config['second_head'],
                'parent_head':head,'parent_count':len(rows),
                'reviewed_cues':cursor-1,'cue_total':len(self.source.cues),
                'candidate_claims':sum(len(r['claims']) for _,r in rows),
                'open_issues':sum(len(r['open_issues']) for _,r in rows),
                'parent_first_full_census':cursor>len(self.source.cues),
                'independent_gold_certified':False,'e3_quality_certified':False,
                'v123_approved':False,'e4_approved':False,'e5_published':False}

    def compare_unapproved(self):
        """Diagnostic only: parent location and old cue-local claim occurrence."""
        with self._db() as db:_,records,_=self._audit(db)
        with self.owner._connect() as conn:
            _,effective=self.owner._audit(conn)
        with self.second._db() as conn:
            _,second_reviews=self.second._audit(conn)
        out=[]
        for sha,rec in records:
            first=sum(len(effective[i][1]['claims']) for i in range(rec['start_cue'],rec['end_cue']+1))
            second=sum(len(second_reviews[i][1]['claims']) for i in range(rec['start_cue'],rec['end_cue']+1))
            out.append({'parent_event_sha256':sha,
                        'parent_id':f"P{rec['start_cue']:04d}_{rec['end_cue']:04d}_{sha[:12]}",
                        'start_cue':rec['start_cue'],'end_cue':rec['end_cue'],
                        'new_parent_atom_candidates':len(rec['claims']),
                        'candidate_atom_ids':[f"P{rec['start_cue']:04d}_A{n:03d}_{sha[:12]}"
                                              for n in range(1,len(rec['claims'])+1)],
                        'first_cue_local_candidates':first,'second_cue_local_candidates':second,
                        'quantitative_accuracy_claimed':False,'semantic_equivalence_certified':False})
        return out