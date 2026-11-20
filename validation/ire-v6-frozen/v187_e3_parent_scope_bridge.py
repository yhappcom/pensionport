"""V187: append-only source-antecedent scope linkage, E3 PROVISIONAL ONLY.

A source-spoken hypothetical qualifier can occur before an atomic claim's
original local source_context. This is a checked ChatGPT-authored relation,
not automatic coreference inference or financial/advisory certification.
"""
from __future__ import annotations

import json
import os
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path

from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import ZERO, _canon, _digest

CONFIG = 'IRE_V187_E3_SCOPED_ANTECEDENT_PIN_V1'
PACKET = 'IRE_V187_E3_SCOPED_ANTECEDENT_CHALLENGE_V1'
ANSWER = 'IRE_V187_E3_SCOPED_ANTECEDENT_CHAT_ANSWER_V1'
EVENT = 'IRE_V187_E3_SCOPED_ANTECEDENT_AUDIT_EVENT_V1'
SCOPE = 'HYPOTHETICAL_EXAMPLE'
RESPONSE_FIELDS = {'term_id','term_sha256','scope_type','parent_cue_index',
                   'parent_source_quote','bridging_cue_index','bridging_source_quote',
                   'target_claim_quote','semantic_scope_rationale',
                   'source_scope_provisional','e3_certified','v123_approved',
                   'e4_approved','e5_published'}


def _need(ok, message):
    if not ok:
        raise InvalidInput('V187_SCOPE_'+message)


def _in_cue(quote, cue):
    return (type(quote) is str and len(quote.strip())>=4 and
            ' '.join(quote.split()) in ' '.join(cue.text.split()))


class E3ParentScopeBridge:
    def __init__(self, engine, qualifier_provenance, db_path, *,
                 expected_owner_head, expected_qualifier_head, create=False):
        self.engine = engine
        self.qualifier_provenance = qualifier_provenance
        self.path = Path(db_path)
        self.expected_owner_head = expected_owner_head
        self.expected_qualifier_head = expected_qualifier_head
        _need(qualifier_provenance.engine is engine and
              qualifier_provenance.expected_owner_head == expected_owner_head and
              engine.progress()['checkpoint_head_sha256'] == expected_owner_head,
              'OWNER_SOURCE_JOURNAL_PIN_CHANGED')
        self._require_qualifier_head()
        _need(self.path not in {engine.path, qualifier_provenance.path} and
              not self.path.is_symlink() and
              engine.path.is_file() and
              stat.S_IMODE(engine.path.stat().st_mode)&0o077 == 0,
              'SEPARATE_OWNER_PRIVATE_DATABASE_REQUIRED')
        self.config = {'schema':CONFIG,
                       'video_id':engine.source.video_id,
                       'owner_source_sha256':engine.source.source_sha256,
                       'owner_manifest_sha256':engine.source.manifest_sha256,
                       'owner_head_sha256':expected_owner_head,
                       'qualifier_head_sha256':expected_qualifier_head,
                       'eligible_terms_sha256':_digest(self._eligible_terms()),
                       'e3_certified':False,'v123_approved':False,
                       'e4_approved':False,'e5_published':False}
        if self.path.exists():
            _need(not create and self.path.is_file() and
                  stat.S_IMODE(self.path.stat().st_mode)&0o077 == 0,
                  'EXISTING_SCOPE_JOURNAL_MUST_RESUME_PRIVATELY')
        else:
            _need(create,'SCOPE_DATABASE_MISSING_NO_AUTO_RESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config '
                       '(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events '
                       '(seq INTEGER PRIMARY KEY,prev_sha TEXT NOT NULL,'
                       'event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS accepted_links '
                       '(term_id TEXT PRIMARY KEY,event_sha TEXT NOT NULL,record TEXT NOT NULL)')
            row=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if row:
                _need(json.loads(row['value'])==self.config,
                      'CONFIG_OR_SOURCE_PROVENANCE_CHANGED')
            else:
                db.execute('INSERT INTO config VALUES(1,?)',
                           (_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        con=sqlite3.connect(self.path,timeout=20)
        con.row_factory=sqlite3.Row
        try:
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def _require_qualifier_head(self):
        statv=self.qualifier_provenance.status()
        _need(statv['journal_head_sha256']==self.expected_qualifier_head and
              statv['owner_journal_head_sha256']==self.expected_owner_head and
              statv['fully_covered'] is True,
              'QUALIFIER_JOURNAL_CHANGED_OR_NOT_FULLY_REVIEWED')
        return statv

    def _eligible_terms(self):
        self._require_qualifier_head()
        _,responses=self.qualifier_provenance.audited_map()
        return [{'term_id':tid,'term_sha256':term['term_sha256'],
                 'claim_sha256':term['claim_sha256'],
                 'cue_index':term['cue_index']}
                for tid,term in self.qualifier_provenance.terms.items()
                if term['field']=='conditions' and
                responses[tid]['origin']=='UNRESOLVED']

    def _validate_response(self, response, term):
        _need(type(response) is dict and set(response)==RESPONSE_FIELDS and
              response['term_id']==term['term_id'] and
              response['term_sha256']==term['term_sha256'] and
              response['scope_type']==SCOPE and
              response['source_scope_provisional'] is True and
              all(response[k] is False for k in ('e3_certified','v123_approved',
                                                  'e4_approved','e5_published')),
              'RESPONSE_SCHEMA_OR_APPROVAL_FORGERY')
        parent=response['parent_cue_index']
        bridge=response['bridging_cue_index']
        target=term['cue_index']
        _need(type(parent) is int and type(bridge) is int and
              1<=parent<bridge<=target<=len(self.engine.source.cues) and
              target-parent<=20 and
              _in_cue(response['parent_source_quote'],self.engine.source.cues[parent-1]) and
              _in_cue(response['bridging_source_quote'],self.engine.source.cues[bridge-1]) and
              any(s in response['parent_source_quote'] for s in ('가상','예시')) and
              response['target_claim_quote']==term['claim_quote'] and
              type(response['semantic_scope_rationale']) is str and
              len(response['semantic_scope_rationale'].strip())>=85,
              'SOURCE_SCOPE_NOT_PROVEN_BY_ORIGINAL')
        _need(parent not in term['source_context_cue_indices'],
              'SCOPE_ALREADY_IN_CLAIM_CONTEXT_USE_V186_INSTEAD')

    def _audit(self, db):
        self._require_qualifier_head()
        config=db.execute('SELECT value FROM config WHERE id=1').fetchone()
        _need(config and json.loads(config['value'])==self.config,'CONFIG_TAMPER')
        eligible={t['term_id'] for t in self._eligible_terms()}
        prev=ZERO
        assembled={}
        for num,row in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            frame=json.loads(row['payload'])
            _need(type(frame) is dict and set(frame)=={
                  'schema','seq','prev_sha','owner_source_sha256',
                  'owner_head_sha256','qualifier_head_sha256','challenge_sha256',
                  'responses','e3_certified','v123_approved','e4_approved',
                  'e5_published'},'EVENT_FIELDS_TAMPER')
            _need(row['seq']==num and row['prev_sha']==prev and
                  _canon(frame).decode()==row['payload'] and
                  row['event_sha']==_digest(frame) and
                  frame['schema']==EVENT and frame['seq']==num and
                  frame['prev_sha']==prev and
                  frame['owner_source_sha256']==self.engine.source.source_sha256 and
                  frame['owner_head_sha256']==self.expected_owner_head and
                  frame['qualifier_head_sha256']==self.expected_qualifier_head and
                  all(frame[k] is False for k in ('e3_certified','v123_approved',
                                                 'e4_approved','e5_published')),
                  'EVENT_CHAIN_OR_AUTHORITY_TAMPER')
            for item in frame['responses']:
                tid=item.get('term_id')
                _need(tid in eligible and tid not in assembled,
                      'DUPLICATE_OR_UNAUTHORIZED_SCOPE')
                self._validate_response(item,self.qualifier_provenance.terms[tid])
                assembled[tid]=(row['event_sha'],item)
            prev=row['event_sha']
        table=db.execute('SELECT * FROM accepted_links').fetchall()
        _need(len(table)==len(assembled),'SCOPE_ROW_COUNT_TAMPER')
        for row in table:
            _need(row['term_id'] in assembled and
                  row['event_sha']==assembled[row['term_id']][0] and
                  json.loads(row['record'])==assembled[row['term_id']][1],
                  'SCOPE_LINK_ROW_TAMPER')
        return prev,assembled

    def prepare(self, *, term_ids, parent_cue_index, bridging_cue_index):
        _need(type(term_ids) is list and 1<=len(term_ids)<=12 and
              term_ids==sorted(set(term_ids)) and
              type(parent_cue_index) is int and
              type(bridging_cue_index) is int,
              'PACKET_SELECTION_INVALID')
        elig={x['term_id'] for x in self._eligible_terms()}
        with self._db() as db:
            head,completed=self._audit(db)
        _need(all(t in elig and t not in completed for t in term_ids),
              'PACKET_ALREADY_REVIEWED_OR_NOT_UNRESOLVED')
        targets=[self.qualifier_provenance.terms[tid] for tid in term_ids]
        _need(all(1<=parent_cue_index<bridging_cue_index<=t['cue_index'] and
                  t['cue_index']-parent_cue_index<=20 and
                  parent_cue_index not in t['source_context_cue_indices']
                  for t in targets),'PACKET_SCOPE_POSITION_INVALID')
        pkt={'schema':PACKET,'type':'E3_PARENT_HYPOTHETICAL_SCOPE_LINK',
             'source_sha256':self.engine.source.source_sha256,
             'owner_head_sha256':self.expected_owner_head,
             'qualifier_head_sha256':self.expected_qualifier_head,
             'scope_journal_head_sha256':head,
             'scope_type':SCOPE,'term_ids':term_ids,
             'parent_cue_index':parent_cue_index,
             'bridging_cue_index':bridging_cue_index,
             'parent_original_text':self.engine.source.cues[parent_cue_index-1].text,
             'bridging_original_text':self.engine.source.cues[bridging_cue_index-1].text,
             'targets':[{'term_id':t['term_id'],
                         'term_sha256':t['term_sha256'],
                         'claim_quote':t['claim_quote'],
                         'cue_index':t['cue_index'],
                         'original_cue_text':self.engine.source.cues[t['cue_index']-1].text,
                         'original_claim_context_indices':t['source_context_cue_indices']}
                        for t in targets],
             'prior_qualifier_values_hidden':False,
             'e3_certified':False,'e4_approved':False,'e5_published':False}
        return {**pkt,'challenge_sha256':_digest(pkt)}

    def submit(self,packet,answer):
        _need(type(packet) is dict and packet.get('schema')==PACKET and
              packet.get('type')=='E3_PARENT_HYPOTHETICAL_SCOPE_LINK' and
              packet.get('challenge_sha256')==_digest({k:v for k,v in packet.items()
                                                     if k!='challenge_sha256'}),
              'PACKET_HASH_INVALID')
        regen=self.prepare(term_ids=packet['term_ids'],
                           parent_cue_index=packet['parent_cue_index'],
                           bridging_cue_index=packet['bridging_cue_index'])
        _need(regen==packet,'PACKET_NOT_ENGINE_ISSUED_OR_STALE')
        _need(type(answer) is dict and set(answer)=={
                  'schema','challenge_sha256','review_executor','responses'} and
              answer['schema']==ANSWER and answer['challenge_sha256']==packet['challenge_sha256'] and
              answer['review_executor']=='CHATGPT_IN_CHAT' and
              type(answer['responses']) is list and
              [r.get('term_id') for r in answer['responses']]==packet['term_ids'],
              'ANSWER_SCHEMA_OR_ORDER_INVALID')
        for r,tid in zip(answer['responses'],packet['term_ids']):
            self._validate_response(r,self.qualifier_provenance.terms[tid])
            _need(r['parent_cue_index']==packet['parent_cue_index'] and
                  r['bridging_cue_index']==packet['bridging_cue_index'],
                  'ANSWER_SOURCE_POSITION_CHANGED')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,done=self._audit(db)
            _need(head==packet['scope_journal_head_sha256'] and
                  not set(packet['term_ids'])&set(done),
                  'CONCURRENT_OR_DUPLICATE_SCOPE_REVIEW')
            seq=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1
            frame={'schema':EVENT,'seq':seq,'prev_sha':head,
                   'owner_source_sha256':self.engine.source.source_sha256,
                   'owner_head_sha256':self.expected_owner_head,
                   'qualifier_head_sha256':self.expected_qualifier_head,
                   'challenge_sha256':packet['challenge_sha256'],
                   'responses':answer['responses'],
                   'e3_certified':False,'v123_approved':False,
                   'e4_approved':False,'e5_published':False}
            ev=_digest(frame)
            db.execute('INSERT INTO events VALUES (?,?,?,?)',
                       (seq,head,ev,_canon(frame).decode()))
            for item in answer['responses']:
                db.execute('INSERT INTO accepted_links VALUES (?,?,?)',
                           (item['term_id'],ev,_canon(item).decode()))
        return {'status':'E3_SOURCE_SCOPE_PROVISIONAL_ONLY',
                'new_scope_links':len(answer['responses']),
                'head_sha256':ev,
                'e3_certified':False,'e4_approved':False,'e5_published':False}

    def status(self):
        with self._db() as db:
            head,items=self._audit(db)
        return {'schema':'IRE_V187_SCOPE_LINK_STATUS_PROVISIONAL_V1',
                'source_sha256':self.engine.source.source_sha256,
                'owner_head_sha256':self.expected_owner_head,
                'qualifier_head_sha256':self.expected_qualifier_head,
                'journal_head_sha256':head,
                'linked_term_count':len(items),
                'eligible_unresolved_condition_terms':len(self._eligible_terms()),
                'e3_certified':False,'v123_approved':False,
                'e4_approved':False,'e5_published':False}

    def projected_source_anchors(self):
        with self._db() as db:
            _,items=self._audit(db)
        result={}
        for term_id,(_,entry) in items.items():
            term=self.qualifier_provenance.terms[term_id]
            key=(term['cue_index'],term['claim_ordinal'])
            values=result.setdefault(key,{'conditions':set(),'inherited_explicit_terms':0})
            values['conditions'].add(entry['parent_cue_index'])
            values['inherited_explicit_terms']+=1
        return {key:{'conditions':sorted(v['conditions']),
                     'inherited_explicit_terms':v['inherited_explicit_terms']}
                for key,v in result.items()}