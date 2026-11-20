"""V192: private, source-anchored THREE-WAY semantic alignment of E3 candidates.

NOT an independent gold set and NOT a financial fact approval. The reviewer
must explicitly compare a parent-first atom to each of two cue-first passes.
No lexical similarity threshold is used to declare two finance facts identical.
Original journals are read only; all resulting assessments are append-only.
"""
from __future__ import annotations
import json, os, sqlite3, stat
from pathlib import Path
from contextlib import contextmanager
from collections import Counter
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import ZERO, _canon, _digest

PACKET='IRE_V192_E3_TRIPLET_SOURCE_CHALLENGE_V1'
ANSWER='IRE_V192_E3_TRIPLET_CHAT_RESPONSE_V1'
EVENT='IRE_V192_E3_TRIPLET_APPEND_EVENT_V1'
CONFIG='IRE_V192_E3_TRIPLET_CONFIG_V1'
REL={'EQUIVALENT_PROVISIONAL','PARENT_MORE_SPECIFIC','OLDER_MORE_SPECIFIC',
     'PARTIAL_OVERLAP_UNRESOLVED','MISSING_IN_OLDER','UNRESOLVED'}


def _need(ok, code):
    if not ok: raise InvalidInput('V192_E3_'+code)


def _priv(path):
    return path.is_file() and not path.is_symlink() and not (stat.S_IMODE(path.stat().st_mode)&0o077)


def _quote(cues,idx,quote):
    return type(idx) is int and 1<=idx<=len(cues) and type(quote) is str and len(quote.strip())>=2 and ' '.join(quote.split()) in ' '.join(cues[idx-1].text.split())


class E3TripletAlignment:
    def __init__(self, parent, path, *, expected_owner_head, expected_second_head,
                 expected_parent_head, create=False):
        self.parent=parent
        self.owner=parent.owner
        self.second=parent.second
        self.source=self.owner.source
        self.path=Path(path)
        self.config={
            'schema':CONFIG,'source_sha256':self.source.source_sha256,
            'owner_source_manifest_sha256':self.source.manifest_sha256,
            'owner_head':expected_owner_head,'second_head':expected_second_head,
            'parent_head':expected_parent_head,'video_id':self.source.video_id,
            'cue_total':len(self.source.cues),'independent_gold_certified':False,
            'e3_certified':False,'v123_approved':False,
            'e4_approved':False,'e5_published':False,
        }
        _need(self.path not in (self.owner.path,self.second.path,self.parent.path)
              and not self.path.is_symlink(),'SEPARATE_PRIVATE_JOURNAL_REQUIRED')
        self._pins()
        if self.path.exists():
            _need(not create and _priv(self.path),'JOURNAL_PERMISSIONS_OR_RESUME')
        else:
            _need(create,'NO_AUTO_RESET')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1),data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,prev_sha TEXT NOT NULL,event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS judgments(start_cue INTEGER PRIMARY KEY,event_sha TEXT NOT NULL,record TEXT NOT NULL)')
            x=db.execute('SELECT data FROM config WHERE id=1').fetchone()
            if x:_need(json.loads(x[0])==self.config,'CONFIG_PIN_TAMPER')
            else:db.execute('INSERT INTO config VALUES(1,?)',(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=20)
        db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()

    def _pins(self):
        _need(self.owner.progress()['checkpoint_head_sha256']==self.config['owner_head']
              and self.second.status()['second_review_audit_head_sha256']==self.config['second_head']
              and self.parent.status()['parent_head']==self.config['parent_head']
              and self.parent.status()['parent_first_full_census']
              and self.source.source_sha256==self.config['source_sha256'],
              'SOURCE_OR_JOURNAL_HEAD_CHANGED')

    def _snapshots(self):
        self._pins()
        with self.owner._connect() as db:_,first=self.owner._audit(db)
        with self.second._db() as db:_,second=self.second._audit(db)
        with self.parent._db() as db:_,par,_=self.parent._audit(db)
        _need(len(first)==len(second)==len(self.source.cues) and len(par)>0,'CENSUS_INCOMPLETE')
        return first,second,par

    def _ref(self,which,idx,ordinal,claim):
        return {'pass':which,'cue_index':idx,'ordinal':ordinal,
                'claim_sha256':_digest(claim)}

    def _rows(self):
        first,second,parents=self._snapshots()
        out=[]
        for sha,rec in parents:
            start,stop=rec['start_cue'],rec['end_cue']
            parent_refs=[{'ref':self._ref('PARENT',start,j,c),'kind':c['kind'],
                'proposition':c['proposition'],'source_quote':c['quote'],
                'quote_cue':c['quote_cue'],'evidence_cues':c['evidence_cues'],
                'numbers':c['numbers'],'reviewer_caveats':c['reviewer_caveats']}
                for j,c in enumerate(rec['claims'],1)]
            older={}
            for which,source in [('FIRST',first),('SECOND',second)]:
                old=[]
                for idx in range(start,stop+1):
                    for ordinal,c in enumerate(source[idx][1]['claims'],1):
                        old.append({'ref':self._ref(which,idx,ordinal,c),
                            'kind':c['kind'],'proposition':c['proposition'],
                            'source_quote':c['quote'],'quote_cue':idx,
                            'context_cues':c['context_cue_indices'],
                            'conditions_count':len(c['conditions']),
                            'exceptions_count':len(c['exceptions'])})
                older[which]=old
            out.append({'parent_id':f"P{start:04d}_{stop:04d}_{sha[:12]}",
                        'parent_event_sha256':sha,'start_cue':start,'end_cue':stop,
                        'parent_summary':rec['parent_summary'],
                        'parent_claims':parent_refs,'older_claims':older})
        return out

    def _audit(self, db, rows):
        x=db.execute('SELECT data FROM config WHERE id=1').fetchone()
        _need(x and json.loads(x[0])==self.config,'CONFIG_CHANGED')
        prev=ZERO;judged={};expected_start_idx=0
        expected_by_start={r['start_cue']:r for r in rows}
        for n,event in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            frame=json.loads(event['payload'])
            reviews=frame.get('reviews')
            _need(event['seq']==n and event['prev_sha']==prev
                  and frame.get('seq')==n and frame.get('prev_sha')==prev
                  and frame.get('schema')==EVENT
                  and frame.get('config_sha256')==_digest(self.config)
                  and frame.get('source_sha256')==self.config['source_sha256']
                  and all(frame.get(k) is False for k in
                      ('independent_gold_certified','e3_certified','v123_approved',
                       'e4_approved','e5_published'))
                  and _canon(frame).decode()==event['payload']
                  and _digest(frame)==event['event_sha']
                  and type(reviews) is list and 1<=len(reviews)<=8,
                  'EVENT_TAMPER_OR_REPLAY')
            for rec in reviews:
                i=rec.get('start_cue') if type(rec) is dict else None
                _need(expected_start_idx<len(rows) and
                      i==rows[expected_start_idx]['start_cue']
                      and i in expected_by_start and i not in judged,
                      'REVIEW_SEQUENCE_OR_GAP')
                self._validate_record(expected_by_start[i],rec)
                judged[i]=(event['event_sha'],rec)
                expected_start_idx+=1
            prev=event['event_sha']
        persisted=db.execute('SELECT * FROM judgments ORDER BY start_cue').fetchall()
        _need(len(persisted)==len(judged),'JUDGMENT_ROW_COUNT')
        for row in persisted:
            _need(row['start_cue'] in judged and
                  row['event_sha']==judged[row['start_cue']][0] and
                  json.loads(row['record'])==judged[row['start_cue']][1],
                  'JUDGMENT_TAMPER')
        return prev,judged

    def _validate_record(self,row,record):
        _need(type(record) is dict and set(record)=={
            'start_cue','parent_id','source_quote','source_quote_cue',
            'claim_alignments','unmatched_older_refs','review_rationale',
            'independent_gold_certified','e3_certified','v123_approved',
            'e4_approved','e5_published'} and
            record['start_cue']==row['start_cue'] and record['parent_id']==row['parent_id']
            and _quote(self.source.cues,record['source_quote_cue'],record['source_quote'])
            and row['start_cue']<=record['source_quote_cue']<=row['end_cue']
            and isinstance(record['review_rationale'],str)
            and len(record['review_rationale'].strip())>=45
            and all(record[x] is False for x in ['independent_gold_certified',
                'e3_certified','v123_approved','e4_approved','e5_published']),
            'REVIEW_FIELD_OR_AUTHORITY')
        parents=row['parent_claims']
        _need(type(record['claim_alignments']) is list and len(record['claim_alignments'])==len(parents),
              'EXHAUSTIVE_PARENT_CLAIMS_REQUIRED')
        permitted={key:{_digest(c['ref']):c for c in row['older_claims'][key]}
                   for key in ('FIRST','SECOND')}
        seen={key:set() for key in permitted}
        for j,a in enumerate(record['claim_alignments']):
            _need(type(a) is dict and set(a)=={'parent_claim_ref','first_refs','second_refs',
                    'first_relation','second_relation','meaning_rationale'}
                  and a['parent_claim_ref']==parents[j]['ref']
                  and a['first_relation'] in REL and a['second_relation'] in REL
                  and isinstance(a['meaning_rationale'],str)
                  and len(a['meaning_rationale'].strip())>=36,
                  'PARENT_CLAIM_ID_OR_MEANING')
            for key,field,rel in [('FIRST','first_refs','first_relation'),
                                  ('SECOND','second_refs','second_relation')]:
                _need(type(a[field]) is list and len(a[field])<=8,'MATCH_REF_COUNT')
                refs=[_digest(r) for r in a[field]]
                _need(len(refs)==len(set(refs)) and all(r in permitted[key] for r in refs),
                      'OLD_CLAIM_REF_FORGED')
                _need((not a[field]) if a[rel]=='MISSING_IN_OLDER'
                      else (bool(a[field]) if a[rel] not in ('UNRESOLVED',) else True),
                      'RELATION_REFERENCE_CONFLICT')
                seen[key].update(refs)
        unused={key:{hash:c['ref'] for hash,c in values.items() if hash not in seen[key]}
                for key,values in permitted.items()}
        _need(type(record['unmatched_older_refs']) is dict
              and set(record['unmatched_older_refs'])=={'FIRST','SECOND'},
              'UNMATCHED_SCHEMA')
        for key in ('FIRST','SECOND'):
            x=record['unmatched_older_refs'][key]
            _need(type(x) is list and all(type(ref) is dict for ref in x)
                  and {_digest(ref) for ref in x}==set(unused[key])
                  and len(x)==len(unused[key]),
                  'OLDER_CLAIM_CENSUS_INCOMPLETE')

    def _make_packet(self,rows,next_rows,head):
        cues=self.source.cues
        packets=[]
        for r in next_rows:
            start,stop=r['start_cue'],r['end_cue']
            packet=dict(r)
            packet['original_cues']=[{'cue_index':j,'text':cues[j-1].text,
                 'text_sha256':sha256(cues[j-1].text.encode())}
                 for j in range(max(1,start-3),min(len(cues),stop+3)+1)]
            packets.append(packet)
        response={'schema':PACKET,'source_sha256':self.source.source_sha256,
                  'owner_head':self.config['owner_head'],
                  'second_head':self.config['second_head'],
                  'parent_head':self.config['parent_head'],
                  'review_head':head,'target_parents':packets,
                  'independent_gold_certified':False,
                  'e3_certified':False,'v123_approved':False,
                  'e4_approved':False,'e5_published':False}
        response['challenge_sha256']=_digest(response)
        return response

    def prepare(self,limit=4):
        _need(type(limit) is int and 1<=limit<=8,'LIMIT')
        rows=self._rows()
        with self._db() as db:head,judged=self._audit(db,rows)
        remaining=[x for x in rows if x['start_cue'] not in judged]
        _need(bool(remaining),'FULL_CENSUS_ALREADY_COMPLETE')
        return self._make_packet(rows,remaining[:limit],head)

    def submit(self,packet,answer):
        _need(type(packet) is dict and type(answer) is dict and
              set(answer)=={'schema','challenge_sha256','review_executor','reviews'}
              and answer['schema']==ANSWER
              and answer['review_executor']=='CHATGPT_IN_CHAT'
              and answer['challenge_sha256']==packet.get('challenge_sha256')
              and type(answer['reviews']) is list,
              'ANSWER_WRAPPER')
        rows=self._rows()
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,judged=self._audit(db,rows)
            _need(type(packet.get('target_parents')) is list
                  and 1<=len(packet['target_parents'])<=8,
                  'TARGET_PACKET_INVALID')
            remaining=[x for x in rows if x['start_cue'] not in judged]
            expected=self._make_packet(rows,remaining[:len(packet['target_parents'])],head)
            _need(packet==expected,'STALE_OR_FORGED_CHALLENGE')
            _need(len(answer['reviews'])==len(expected['target_parents']),
                  'INCOMPLETE_REVIEW_BATCH')
            for row,record in zip(expected['target_parents'],answer['reviews']):
                self._validate_record(row,record)
            frame={'schema':EVENT,'seq':db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1,
                   'prev_sha':head,'config_sha256':_digest(self.config),
                   'source_sha256':self.source.source_sha256,
                   'packet_sha256':packet['challenge_sha256'],
                   'reviews':answer['reviews'],'independent_gold_certified':False,
                   'e3_certified':False,'v123_approved':False,
                   'e4_approved':False,'e5_published':False}
            digest=_digest(frame)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',
                       (frame['seq'],head,digest,_canon(frame).decode()))
            for item in answer['reviews']:
                db.execute('INSERT INTO judgments VALUES(?,?,?)',
                           (item['start_cue'],digest,_canon(item).decode()))
        return self.status()

    def status(self):
        rows=self._rows()
        with self._db() as db:head,judged=self._audit(db,rows)
        matched=Counter();kinds=Counter();newmissing=Counter();unmapped=Counter()
        for _,rec in judged.values():
            for a in rec['claim_alignments']:
                for passname,prefix in [('FIRST','first'),('SECOND','second')]:
                    rel=a[prefix+'_relation'];matched[(passname,rel)]+=1
                    if rel=='MISSING_IN_OLDER':newmissing[passname]+=1
                    if a[prefix+'_refs']:
                        # track when a prior stance/kind differs without promoting claim truth
                        parent_idx=next((j for j,p in enumerate(next(
                            r for r in rows if r['start_cue']==rec['start_cue'])['parent_claims'])
                           if p['ref']==a['parent_claim_ref']),None)
                        if parent_idx is not None:
                            pk=next(r for r in rows if r['start_cue']==rec['start_cue'])['parent_claims'][parent_idx]['kind']
                            prev=next(r for r in rows if r['start_cue']==rec['start_cue'])['older_claims'][passname]
                            for ref in a[prefix+'_refs']:
                                old=next(x for x in prev if x['ref']==ref)
                                if old['kind']!=pk:kinds[passname]+=1
            for x in ('FIRST','SECOND'):unmapped[x]+=len(rec['unmatched_older_refs'][x])
        return {'schema':'IRE_V192_E3_TRIPLET_ALIGN_STATUS_V1',
                'source_sha256':self.source.source_sha256,
                'first_head':self.config['owner_head'],'second_head':self.config['second_head'],
                'parent_head':self.config['parent_head'],'alignment_head':head,
                'reviewed_parents':len(judged),'parent_total':len(rows),
                'reviewed_parent_atoms':sum(len(r['claim_alignments']) for _,r in judged.values()),
                'parent_atoms_total':sum(len(r['parent_claims']) for r in rows),
                'relation_counts':{f'{a}:{b}':n for (a,b),n in sorted(matched.items())},
                'unmatched_older_claims':dict(unmapped),
                'kind_mismatch_links':dict(kinds),'provisional_missing_parent_claims':dict(newmissing),
                'unreviewed_parents':len(rows)-len(judged),
                'exact_parent_equality_or_financial_truth_certified':False,
                'independent_gold_certified':False,
                'precision':None,'recall':None,'high_risk_misses':None,
                'e3_quality_certified':False,'v123_approved':False,
                'e4_approved':False,'e5_published':False}