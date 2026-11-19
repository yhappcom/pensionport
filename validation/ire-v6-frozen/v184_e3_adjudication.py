"""Source-grounded E3 adjudication, separate from both owner and blind E3 journals.

A disagreement is a review *trigger*, not proof of an error. Each human/model-authored
interpretation must distinguish speaker-uttered constraints from reviewer's safety
caveats. This module does not rewrite either pass, certify quality, or invoke E4.
"""
from __future__ import annotations
import json, os, sqlite3, stat
from contextlib import contextmanager
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import ZERO, _digest, _canon

PACKET_SCHEMA='IRE_V184_E3_DISAGREEMENT_ADJUDICATION_PACKET_V1'
ANSWER_SCHEMA='IRE_V184_E3_CHAT_ADJUDICATION_RESPONSE_V1'
EVENT_SCHEMA='IRE_V184_E3_APPEND_ONLY_ADJUDICATION_EVENT_V1'
CONFIG_SCHEMA='IRE_V184_E3_ADJUDICATION_SOURCE_PIN_V1'
CATEGORIES={
 'CONFIRMED_FIRST_PASS_OMISSION',
 'CONFIRMED_SECOND_PASS_OMISSION',
 'SEMANTIC_EQUIVALENCE_WORDING',
 'CLAIM_BOUNDARY_DISAGREEMENT',
 'SOURCE_CLAIM_SCOPE_OPEN',
 'REVIEWER_QUALIFIER_ADDITION',
 'MISSING_AUDIO_VISUAL',
 'UNRESOLVED_NEEDS_REVIEW',
}
QUALIFIER_ORIGINS={'NONE','SOURCE_SPOKEN','REVIEWER_ADDED','MIXED','UNVERIFIED'}
NEXT_ACTIONS={'REPAIR_FIRST_PASS','REVIEW_SECOND_PASS','KEEP_OPEN_WITH_EVIDENCE_TASK',
              'PRESERVE_BOTH_WITH_PARENT_LINK','NO_SOURCE_CHANGE','SOURCE_AUDIO_VISUAL_REVIEW'}
RESPONSE_KEYS={'cue_index','source_text_sha256','source_quote','related_cue_indices',
               'category','qualifier_origin','semantic_rationale','next_action',
               'independent_gold_certified','v123_e4_approved','e5_authorized'}


def _need(ok,why):
    if not ok:
        raise InvalidInput('V184_E3_'+why)


class E3Adjudication:
    """Reconcile dual-pass judgments using source text; append-only and NO approval."""
    def __init__(self,second_pass,audit_db,*,create=False):
        self.second=second_pass
        self.engine=second_pass.engine
        self.path=Path(audit_db)
        self.config={'schema':CONFIG_SCHEMA,
                     'source_sha256':self.engine.source.source_sha256,
                     'video_id':self.engine.source.video_id,
                     'first_pass_head_sha256':second_pass.expected_owner_head,
                     'quality_certified':False,'e4_approved':False,'e5_published':False}
        _need(self.path!=second_pass.path and self.path!=self.engine.path,
              'ADJUDICATION_MUST_BE_SEPARATE_DB')
        _need(not self.path.is_symlink(),'ADJUDICATION_SYMLINK_REJECTED')
        if self.path.exists():
            _need(not create,'ADJUDICATION_EXISTING_DB_MUST_RESUME')
            _need(self.path.is_file() and not (stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  'ADJUDICATION_PRIVATE_DB_PERMISSIONS')
        else:
            _need(create,'ADJUDICATION_NO_AUTORESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_EXCL|os.O_WRONLY|os.O_CREAT,0o600)
            os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL, event_sha TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS judgments (cue_index INTEGER PRIMARY KEY, event_sha TEXT NOT NULL, record TEXT NOT NULL)')
            row=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if row:
                _need(json.loads(row[0])==self.config,'ADJUDICATION_CONFIG_MISMATCH')
            else:
                db.execute('INSERT INTO config VALUES (1,?)',(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=20)
        db.row_factory=sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _source_pair(self,i):
        first=self.second._owner_snapshot()
        with self.second._db() as db:
            _,second=self.second._audit(db)
        _need(i in second,'SECOND_PASS_CUE_NOT_REVIEWED')
        return first[i][1],second[i][1]

    def _audit(self,db):
        self.second._owner_snapshot()
        with self.second._db() as s:
            _,second_rows=self.second._audit(s)
        first_rows=self.second._owner_snapshot()
        prev=ZERO
        entries={}
        for n,row in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            data=json.loads(row['payload'])
            _need(row['seq']==n and row['prev_sha']==prev
                  and data['seq']==n and data['prev_sha']==prev
                  and data['schema']==EVENT_SCHEMA
                  and data['source_sha256']==self.engine.source.source_sha256
                  and data['first_pass_head_sha256']==self.second.expected_owner_head
                  and data['quality_certified'] is False
                  and data['e4_approved'] is False
                  and data['e5_published'] is False
                  and _canon(data).decode()==row['payload']
                  and _digest(data)==row['event_sha'],
                  'ADJUDICATION_EVENT_CHAIN_OR_AUTHORITY_TAMPER')
            for ans in data['answers']:
                i=ans['cue_index']
                _need(i not in entries and i in second_rows
                      and data['comparison_pins'][str(i)]==_digest({
                          'first':first_rows[i][1],
                          'second':second_rows[i][1]})
                      and ans['source_text_sha256']==sha256(self.engine.source.cues[i-1].text.encode()),
                      'ADJUDICATION_SOURCE_PAIR_OR_DUPLICATE_TAMPER')
                entries[i]=(row['event_sha'],ans)
            prev=row['event_sha']
        records=db.execute('SELECT * FROM judgments').fetchall()
        _need(len(records)==len(entries),'ADJUDICATION_RECORD_COUNT_TAMPER')
        for row in records:
            _need(row['cue_index'] in entries and
                  row['event_sha']==entries[row['cue_index']][0] and
                  json.loads(row['record'])==entries[row['cue_index']][1],
                  'ADJUDICATION_RECORD_TAMPER')
        return prev,entries

    def prepare(self,*,cue_indices=None,limit=12,context_radius=4):
        _need(type(limit) is int and 1<=limit<=20 and type(context_radius) is int
              and 2<=context_radius<=12,'ADJUDICATION_PACKET_SIZE')
        status=self.second.status()
        queue={x['cue_index'] for x in status['adjudication_queue']}
        with self._db() as db:
            head,done=self._audit(db)
        if cue_indices is None:
            selected=sorted(queue-set(done))[:limit]
        else:
            _need(type(cue_indices) is list and cue_indices==sorted(set(cue_indices))
                  and 0<len(cue_indices)<=limit and all(type(i) is int for i in cue_indices)
                  and set(cue_indices)<=(queue-set(done)),
                  'ADJUDICATION_SELECTION_INVALID')
            selected=cue_indices
        if not selected:
            return {'schema':PACKET_SCHEMA,'type':'E3_ADJUDICATION_NO_PENDING_DISAGREEMENTS',
                    'e3_quality_certified':False,'e4_approved':False,'e5_published':False}
        ctx=set()
        for i in selected:
            ctx.update(range(max(1,i-context_radius),min(len(self.engine.source.cues),i+context_radius)+1))
        first=self.second._owner_snapshot()
        with self.second._db() as db:
            _,second=self.second._audit(db)
        packet={'schema':PACKET_SCHEMA,'type':'E3_COMPARE_BOTH_PASSES_WITH_SOURCE',
                'source_sha256':self.engine.source.source_sha256,
                'first_pass_head_sha256':self.second.expected_owner_head,
                'second_pass_audit_head_sha256':status['second_review_audit_head_sha256'],
                'adjudication_head_sha256':head,
                'cue_indices':selected,'context_radius':context_radius,
                'surrounding_source':[{'cue_index':k,'text':self.engine.source.cues[k-1].text,
                    'source_text_sha256':sha256(self.engine.source.cues[k-1].text.encode())}
                    for k in sorted(ctx)],
                'pair': [{'cue_index':i,
                          'source_text_sha256':sha256(self.engine.source.cues[i-1].text.encode()),
                          'first_pass':first[i][1], 'second_pass':second[i][1],
                          'difference_codes':self.second._compare(first[i][1],second[i][1])}
                          for i in selected],
                'blind_review_already_completed':True,
                'adjudicator_must_not_claim_independent_gold':True,
                'quality_certified':False,'v123_e4_approved':False,'e5_published':False}
        return {**packet,'challenge_sha256':_digest(packet)}

    def _validate(self,packet,answer):
        _need(type(answer) is dict and set(answer)=={
            'schema','challenge_sha256','review_executor','answers'}
              and answer['schema']==ANSWER_SCHEMA
              and answer['challenge_sha256']==packet['challenge_sha256']
              and answer['review_executor']=='CHATGPT_IN_CHAT'
              and type(answer['answers']) is list
              and len(answer['answers'])==len(packet['cue_indices']),
              'ADJUDICATION_ANSWER_SCHEMA')
        context={x['cue_index'] for x in packet['surrounding_source']}
        for i,a in zip(packet['cue_indices'],answer['answers']):
            cue=self.engine.source.cues[i-1]
            _need(type(a) is dict and set(a)==RESPONSE_KEYS
                  and a['cue_index']==i and type(a['cue_index']) is int
                  and a['source_text_sha256']==sha256(cue.text.encode())
                  and type(a['source_quote']) is str and
                  len(a['source_quote'].strip())>=3
                  and ' '.join(a['source_quote'].split()) in ' '.join(cue.text.split())
                  and type(a['related_cue_indices']) is list
                  and a['related_cue_indices']==sorted(set(a['related_cue_indices']))
                  and i in a['related_cue_indices']
                  and set(a['related_cue_indices'])<=context
                  and a['category'] in CATEGORIES
                  and a['qualifier_origin'] in QUALIFIER_ORIGINS
                  and type(a['semantic_rationale']) is str
                  and len(a['semantic_rationale'].strip())>=40
                  and a['next_action'] in NEXT_ACTIONS
                  and a['independent_gold_certified'] is False
                  and a['v123_e4_approved'] is False
                  and a['e5_authorized'] is False,
                  'ADJUDICATION_SOURCE_OR_SEMANTIC_GUARD')
            if a['category']=='MISSING_AUDIO_VISUAL':
                _need(a['next_action']=='SOURCE_AUDIO_VISUAL_REVIEW',
                      'AUDIO_VISUAL_MUST_STAY_OPEN')
            if a['category']=='CONFIRMED_FIRST_PASS_OMISSION':
                _need(a['next_action']=='REPAIR_FIRST_PASS',
                      'FIRST_PASS_OMISSION_REPAIR_PENDING')
            if a['category']=='CONFIRMED_SECOND_PASS_OMISSION':
                _need(a['next_action']=='REVIEW_SECOND_PASS',
                      'SECOND_PASS_OMISSION_REVIEW_PENDING')

    def submit(self,packet,answer):
        _need(type(packet) is dict and packet.get('type')=='E3_COMPARE_BOTH_PASSES_WITH_SOURCE'
              and packet.get('schema')==PACKET_SCHEMA
              and packet.get('challenge_sha256')==_digest({k:v for k,v in packet.items()
                                                       if k!='challenge_sha256'}),
              'ADJUDICATION_PACKET_TAMPER')
        # Full regeneration rejects attacker-authored self-hash, forged source or stale head.
        current=self.prepare(cue_indices=packet['cue_indices'],
                             limit=len(packet['cue_indices']),
                             context_radius=packet['context_radius'])
        _need(current==packet,'ADJUDICATION_STALE_OR_FORGED_PACKET')
        self._validate(packet,answer)
        self.second._owner_snapshot()
        with self.second._db() as s:
            _,second=self.second._audit(s)
        first=self.second._owner_snapshot()
        pins={str(i):_digest({'first':first[i][1], 'second':second[i][1]})
              for i in packet['cue_indices']}
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,done=self._audit(db)
            _need(head==packet['adjudication_head_sha256']
                  and not(set(done)&set(packet['cue_indices'])),
                  'ADJUDICATION_STALE_OR_DUPLICATE')
            seq=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1
            frame={'schema':EVENT_SCHEMA,'seq':seq,'prev_sha':head,
                   'source_sha256':self.engine.source.source_sha256,
                   'first_pass_head_sha256':self.second.expected_owner_head,
                   'second_pass_head_at_review':packet['second_pass_audit_head_sha256'],
                   'challenge_sha256':packet['challenge_sha256'],
                   'comparison_pins':pins,'answers':answer['answers'],
                   'quality_certified':False,'e4_approved':False,'e5_published':False}
            event_sha=_digest(frame)
            db.execute('INSERT INTO events VALUES (?,?,?,?)',
                       (seq,head,event_sha,_canon(frame).decode()))
            for a in answer['answers']:
                db.execute('INSERT INTO judgments VALUES (?,?,?)',
                           (a['cue_index'],event_sha,_canon(a).decode()))
            db.commit()
        return {'schema':'IRE_V184_E3_ADJUDICATION_RECORDED_NOT_GOLD_V1',
                'reviewed':len(answer['answers']),
                'categories':{k:sum(a['category']==k for a in answer['answers'])
                              for k in sorted({x['category'] for x in answer['answers']})},
                'event_sha256':event_sha,'e3_quality_certified':False,
                'e4_approved':False,'e5_published':False}

    def status(self):
        review=self.second.status()
        with self._db() as db:
            head,entries=self._audit(db)
            n=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        categories={}
        for _,r in entries.values():
            categories[r['category']]=categories.get(r['category'],0)+1
        pending=[i['cue_index'] for i in review['adjudication_queue']
                 if i['cue_index'] not in entries]
        evidence_pending=[i for i,(_,r) in entries.items()
                          if r['category'] in {'MISSING_AUDIO_VISUAL','SOURCE_CLAIM_SCOPE_OPEN',
                            'UNRESOLVED_NEEDS_REVIEW'}]
        return {'schema':'IRE_V184_E3_ADJUDICATION_STATUS_UNAPPROVED_V1',
                'source_sha256':self.engine.source.source_sha256,
                'original_journal_head_sha256':self.second.expected_owner_head,
                'second_pass_head_sha256':review['second_review_audit_head_sha256'],
                'adjudication_head_sha256':head,
                'adjudication_events':n,'adjudicated_cues':len(entries),
                'pending_adjudication_cues':pending,
                'evidence_still_open_cues':sorted(evidence_pending),
                'categorized_findings':categories,
                'second_reviewed_cues':review['second_reviewed_cues'],
                'unreviewed_cues':review['unreviewed_cues'],
                'first_owner_journal_modified':False,
                'independent_gold_certified':False,'e3_quality_certified':False,
                'v123_approved':False,'e4_approved':False,'e5_published':False}