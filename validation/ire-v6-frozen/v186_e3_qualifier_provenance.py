"""V186: original-cue-pinned E3 qualifier provenance, separate append-only journal.

Treat a reviewer caution as reviewer-added, never a speaker-uttered V6
condition or exception. Every judgment is supplied by active ChatGPT and
remains a proposal, not an independent gold label or V123/E4 approval.
"""
from __future__ import annotations

import json
import os
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import ZERO, _canon, _digest

PACKET_SCHEMA = 'IRE_V186_E3_QUALIFIER_SOURCE_PACKET_V1'
ANSWER_SCHEMA = 'IRE_V186_E3_CHAT_QUALIFIER_SOURCE_ANSWER_V1'
EVENT_SCHEMA = 'IRE_V186_E3_APPEND_ONLY_QUALIFIER_REVIEW_EVENT_V1'
CONFIG_SCHEMA = 'IRE_V186_E3_QUALIFIER_SOURCE_JOURNAL_PIN_V1'
ORIGINS = {'SOURCE_EXPLICIT','SOURCE_CONTEXT','REVIEWER_ADDED','UNRESOLVED'}
RESPONSE_KEYS = {'term_id','term_sha256','origin','source_quote','source_cue_indices',
                 'semantic_rationale','e3_certified','v123_approved','e4_approved',
                 'e5_published'}


def _need(condition, reason):
    if not condition:
        raise InvalidInput('V186_E3_'+reason)


class E3QualifierProvenance:
    def __init__(self, engine, db_path, *, expected_owner_head, create=False):
        self.engine = engine
        self.path = Path(db_path)
        self.expected_owner_head = expected_owner_head
        _need(isinstance(expected_owner_head,str) and len(expected_owner_head)==64
              and all(c in '0123456789abcdef' for c in expected_owner_head),
              'OWNER_HEAD_PIN_REQUIRED')
        _need(self.path != engine.path and not self.path.is_symlink(),
              'QUALIFIER_DB_MUST_BE_SEPARATE_AND_NOT_SYMLINK')
        _need(engine.path.is_file() and not engine.path.is_symlink()
              and stat.S_IMODE(engine.path.stat().st_mode)&0o077==0,
              'OWNER_JOURNAL_PRIVATE_PERMISSIONS')
        self.terms = self._owner_terms()
        self.config = {'schema':CONFIG_SCHEMA,
                       'source_sha256':engine.source.source_sha256,
                       'manifest_sha256':engine.source.manifest_sha256,
                       'video_id':engine.source.video_id,
                       'owner_journal_head_sha256':expected_owner_head,
                       'qualifier_registry_sha256':_digest([
                           {'id':k,'term_sha256':v['term_sha256'],
                            'claim_sha256':v['claim_sha256']}
                           for k,v in self.terms.items()]),
                       'e3_certified':False,'e4_approved':False,'e5_published':False}
        if self.path.exists():
            _need(not create,'EXISTING_QUALIFIER_JOURNAL_MUST_RESUME')
            _need(self.path.is_file() and
                  stat.S_IMODE(self.path.stat().st_mode)&0o077==0,
                  'QUALIFIER_DB_PRIVATE_PERMISSIONS')
        else:
            _need(create,'QUALIFIER_DB_NOT_FOUND_NO_AUTORESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
            os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config '
                       '(id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events '
                       '(seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL, '
                       'event_sha TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS judgments '
                       '(term_id TEXT PRIMARY KEY, event_sha TEXT NOT NULL, record TEXT NOT NULL)')
            row=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if row:
                _need(json.loads(row[0])==self.config,
                      'QUALIFIER_PIN_OR_REGISTRY_CHANGED')
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

    def _owner_terms(self):
        _need(self.engine.progress()['checkpoint_head_sha256']==self.expected_owner_head
              and self.engine.progress()['source_first_review_complete'],
              'OWNER_JOURNAL_CHANGED_OR_INCOMPLETE')
        with self.engine._connect() as con:
            head,rows=self.engine._audit(con)
        _need(head==self.expected_owner_head,'OWNER_EVENT_CHAIN_MISMATCH')
        entries={}
        for cue_index in sorted(rows):
            record=rows[cue_index][1]
            for ordinal,claim in enumerate(record.get('claims',[]),1):
                for field in ('conditions','exceptions'):
                    for term_ordinal,term in enumerate(claim[field],1):
                        tid=f'{cue_index:04d}:{ordinal:02d}:{field}:{term_ordinal:02d}'
                        entries[tid]={'term_id':tid,'cue_index':cue_index,
                                      'claim_ordinal':ordinal,'field':field,
                                      'term_ordinal':term_ordinal,'term':term,
                                      'term_sha256':sha256(term.encode()),
                                      'claim_sha256':_digest(claim),
                                      'claim_quote':claim['quote'],
                                      'claim_proposition':claim['proposition'],
                                      'source_context_cue_indices':claim['context_cue_indices']}
        return entries

    def _source_quote_valid(self, answer, target):
        origin=answer['origin']
        quote=answer['source_quote']
        refs=answer['source_cue_indices']
        if origin in {'SOURCE_EXPLICIT','SOURCE_CONTEXT'}:
            if not(type(quote) is str and len(quote.strip())>=3 and
                   type(refs) is list and len(refs)>=1 and
                   all(type(k) is int for k in refs) and
                   refs==sorted(set(refs)) and
                   set(refs)<=set(target['source_context_cue_indices']) and
                   refs==list(range(refs[0],refs[-1]+1))):
                return False
            source=' '.join(self.engine.source.cues[k-1].text for k in refs)
            return ' '.join(quote.split()) in ' '.join(source.split())
        return quote is None and refs==[]

    def _validate_answer(self, packet, answer):
        _need(type(answer) is dict and set(answer)=={
                  'schema','challenge_sha256','review_executor','responses'}
              and answer['schema']==ANSWER_SCHEMA
              and answer['challenge_sha256']==packet['challenge_sha256']
              and answer['review_executor']=='CHATGPT_IN_CHAT'
              and type(answer['responses']) is list
              and len(answer['responses'])==len(packet['term_ids']),
              'QUALIFIER_ANSWER_SCHEMA')
        for term_id,ans in zip(packet['term_ids'],answer['responses']):
            target=self.terms[term_id]
            _need(type(ans) is dict and set(ans)==RESPONSE_KEYS
                  and ans['term_id']==term_id
                  and ans['term_sha256']==target['term_sha256']
                  and type(ans['origin']) is str and ans['origin'] in ORIGINS
                  and type(ans['semantic_rationale']) is str
                  and len(ans['semantic_rationale'].strip())>=40
                  and self._source_quote_valid(ans,target)
                  and all(ans[k] is False for k in (
                     'e3_certified','v123_approved','e4_approved','e5_published')),
                  'QUALIFIER_SOURCE_OR_AUTHORITY_INVALID')

    def _audit(self, db):
        # Recheck owner first, then verify every preserved source and answer.
        self._owner_terms()
        config=db.execute('SELECT value FROM config WHERE id=1').fetchone()
        _need(config and json.loads(config['value'])==self.config,
              'QUALIFIER_CONFIG_TAMPER')
        previous=ZERO
        entries={}
        for index,row in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            data=json.loads(row['payload'])
            _need(row['seq']==index and row['prev_sha']==previous
                  and _canon(data).decode()==row['payload']
                  and row['event_sha']==_digest(data)
                  and data['schema']==EVENT_SCHEMA
                  and data['seq']==index and data['prev_sha']==previous
                  and data['source_sha256']==self.engine.source.source_sha256
                  and data['owner_journal_head_sha256']==self.expected_owner_head
                  and data['e3_certified'] is False
                  and data['v123_approved'] is False
                  and data['e4_approved'] is False
                  and data['e5_published'] is False,
                  'QUALIFIER_EVENT_CHAIN_OR_APPROVAL_TAMPER')
            dummy={'term_ids':[r['term_id'] for r in data['responses']],
                   'challenge_sha256':data['challenge_sha256']}
            self._validate_answer(dummy,{
                'schema':ANSWER_SCHEMA,
                'challenge_sha256':data['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT',
                'responses':data['responses']})
            for ans in data['responses']:
                tid=ans['term_id']
                _need(tid not in entries,'QUALIFIER_DUPLICATE_EVENT_TAMPER')
                entries[tid]=(row['event_sha'],ans)
            previous=row['event_sha']
        stored=db.execute('SELECT * FROM judgments').fetchall()
        _need(len(stored)==len(entries),'QUALIFIER_JUDGMENT_COUNT_TAMPER')
        for row in stored:
            _need(row['term_id'] in entries
                  and row['event_sha']==entries[row['term_id']][0]
                  and json.loads(row['record'])==entries[row['term_id']][1],
                  'QUALIFIER_JUDGMENT_ROW_TAMPER')
        return previous,entries

    def prepare(self, *, term_ids=None,limit=16,context_radius=4):
        _need(type(limit) is int and 1<=limit<=20
              and type(context_radius) is int and 1<=context_radius<=12,
              'QUALIFIER_PACKET_SIZE')
        self._owner_terms()
        with self._db() as db:
            head,done=self._audit(db)
        if term_ids is None:
            selected=[i for i in self.terms if i not in done][:limit]
        else:
            _need(type(term_ids) is list and term_ids==sorted(set(term_ids))
                  and 1<=len(term_ids)<=limit
                  and all(i in self.terms and i not in done for i in term_ids),
                  'QUALIFIER_SELECTION_INVALID')
            selected=term_ids
        if not selected:
            return {'type':'E3_QUALIFIER_REVIEW_COMPLETE_UNAPPROVED',
                    'reviewed':len(done),'total':len(self.terms),
                    'e3_certified':False,'e4_approved':False,'e5_published':False}
        ctx=set()
        for tid in selected:
            i=self.terms[tid]['cue_index']
            ctx.update(range(max(1,i-context_radius),
                             min(len(self.engine.source.cues),i+context_radius)+1))
        packet={'schema':PACKET_SCHEMA,'type':'E3_QUALIFIER_SOURCE_PROVENANCE',
                'source_sha256':self.engine.source.source_sha256,
                'owner_journal_head_sha256':self.expected_owner_head,
                'qualifier_registry_sha256':self.config['qualifier_registry_sha256'],
                'qualifier_audit_head_sha256':head,
                'term_ids':selected,'context_radius':context_radius,
                'targets':[self.terms[t] for t in selected],
                'original_context':[{'cue_index':i,
                    'text':self.engine.source.cues[i-1].text,
                    'source_text_sha256':sha256(self.engine.source.cues[i-1].text.encode())}
                    for i in sorted(ctx)],
                'source_spoken_only_if_directly_attested':True,
                'reviewer_warning_not_a_source_condition':True,
                'e3_certified':False,'e4_approved':False,'e5_published':False}
        return {**packet,'challenge_sha256':_digest(packet)}

    def submit(self, packet, answer):
        _need(type(packet) is dict and packet.get('type')=='E3_QUALIFIER_SOURCE_PROVENANCE'
              and packet.get('schema')==PACKET_SCHEMA
              and packet.get('challenge_sha256')==_digest({k:v for k,v in packet.items()
                                                          if k!='challenge_sha256'}),
              'QUALIFIER_PACKET_TAMPER')
        current=self.prepare(term_ids=packet['term_ids'],limit=len(packet['term_ids']),
                             context_radius=packet['context_radius'])
        _need(current==packet,'QUALIFIER_PACKET_NOT_ENGINE_ISSUED_OR_STALE')
        self._validate_answer(packet,answer)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,done=self._audit(db)
            _need(head==packet['qualifier_audit_head_sha256']
                  and not(set(done)&set(packet['term_ids'])),
                  'QUALIFIER_CONCURRENT_UPDATE_OR_DUPLICATE')
            seq=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1
            frame={'schema':EVENT_SCHEMA,'seq':seq,'prev_sha':head,
                   'source_sha256':self.engine.source.source_sha256,
                   'owner_journal_head_sha256':self.expected_owner_head,
                   'challenge_sha256':packet['challenge_sha256'],
                   'responses':answer['responses'],
                   'e3_certified':False,'v123_approved':False,
                   'e4_approved':False,'e5_published':False}
            event_sha=_digest(frame)
            db.execute('INSERT INTO events VALUES (?,?,?,?)',
                       (seq,head,event_sha,_canon(frame).decode()))
            for ans in answer['responses']:
                db.execute('INSERT INTO judgments VALUES (?,?,?)',
                           (ans['term_id'],event_sha,_canon(ans).decode()))
            db.commit()
        return {'status':'E3_QUALIFIER_PROVENANCE_RECORDED_UNAPPROVED',
                'reviewed_terms':len(answer['responses']),
                'journal_head_sha256':event_sha,
                'e3_certified':False,'e4_approved':False,'e5_published':False}

    def audited_map(self):
        self._owner_terms()
        with self._db() as db:
            head,done=self._audit(db)
        decisions={tid:r[1] for tid,r in done.items()}
        return head,decisions

    def status(self):
        head,done=self.audited_map()
        counts={k:sum(x['origin']==k for x in done.values()) for k in sorted(ORIGINS)}
        return {'schema':'IRE_V186_QUALIFIER_SOURCE_STATUS_UNAPPROVED_V1',
                'journal_head_sha256':head,
                'owner_journal_head_sha256':self.expected_owner_head,
                'total_terms':len(self.terms),'reviewed_terms':len(done),
                'remaining_terms':len(self.terms)-len(done),
                'reviewed_origin_counts':counts,
                'fully_covered':len(done)==len(self.terms),
                'source_condition_anchors_certified_by_independent_gold':False,
                'e3_quality_certified':False,'e4_approved':False,'e5_published':False}

    def projected_source_anchors(self):
        """Only source-explicit original qualifiers may enter *draft* V6 indices.

        E3 source-context citations, reviewer cautions and unresolved terms
        remain outside speaker-spoken source condition/exception anchor fields.
        """
        head,done=self.audited_map()
        anchors={}
        for tid,item in self.terms.items():
            ans=done.get(tid)
            key=(item['cue_index'],item['claim_ordinal'])
            if key not in anchors:
                anchors[key]={'conditions':set(),'exceptions':set(),
                              'source_explicit_terms':0,'source_explicit_condition_terms':0,'source_explicit_exception_terms':0,'unmapped_terms':0,
                              'reviewer_added_terms':0,'source_context_terms':0,
                              'reviewed_terms':0}
            target=anchors[key]
            if ans is None:
                target['unmapped_terms']+=1
                continue
            target['reviewed_terms']+=1
            if ans['origin']=='SOURCE_EXPLICIT':
                target[item['field']].update(ans['source_cue_indices'])
                target['source_explicit_terms']+=1
                target['source_explicit_condition_terms' if item['field']=='conditions'
                       else 'source_explicit_exception_terms']+=1
            else:
                target['unmapped_terms']+=1
                target['reviewer_added_terms']+=int(ans['origin']=='REVIEWER_ADDED')
                target['source_context_terms']+=int(ans['origin']=='SOURCE_CONTEXT')
        results={}
        for key,vals in anchors.items():
            results[key]={k:sorted(v) if isinstance(v,set) else v for k,v in vals.items()}
        return {'head':head,'status':self.status(),'by_claim':results}