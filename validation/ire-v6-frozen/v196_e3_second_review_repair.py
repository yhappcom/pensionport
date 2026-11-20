"""V196 fail-closed, source-pinned *second-turn* repair overlay.

NO mutation of first-turn V194 study, second-turn V195 verdicts, or final financial
approval. Requires a fully audited V195 first+second snapshot and preserves all
open issues and unsafe advice quarantines. A third message may author amendments
within the E3 verification stage; it does not retroactively change V195 HOLD.
Only code/synthetic tests are public. Actual SRT, verdicts and SQLite are PRIVATE.
"""
from __future__ import annotations
import json,os,re,sqlite3,stat
from pathlib import Path
from contextlib import contextmanager
from collections import Counter
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256

PACKET='IRE_V196_SOURCE_PINNED_SECOND_TURN_REPAIR_PACKET_V1'
ANSWER='IRE_V196_SOURCE_PINNED_SECOND_TURN_REPAIR_ANSWER_V1'
CONFIG='IRE_V196_E3_SECOND_REVIEW_CORRECTION_OVERLAY_CONFIG_V1'
EVENT='IRE_V196_E3_SECOND_REVIEW_REPAIR_APPEND_EVENT_V1'
ZERO='0'*64
KINDS={'SOURCE_REWRITE_PROPOSED','REMOVE_NONATOMIC_PROPOSED',
       'PARENT_RELATION_REVIEW_REQUIRED','PRESERVE_QUARANTINE_SOURCE_REPHRASE'}
TARGETS={'HOLD_SOURCE_MEANING_REPAIR','HOLD_REMOVE_FALSE_ATOM_CANDIDATE',
         'QUARANTINE_UNSAFE_INVESTMENT_ADVICE'}
NUM=re.compile(r'(?<![\d.])\d+(?:\.\d+)?(?:%p|%|p)?')

def _need(flag,code):
    if not flag:raise InvalidInput('V196_E3_'+code)

def _canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _sha(x):return sha256(_canonical(x))
def _validsha(x):return type(x)==str and bool(re.fullmatch(r'[a-f0-9]{64}',x))

class E3SecondReviewRepairOverlay:
    """One source-specific set of second-turn repair proposals, append-only."""
    def __init__(self,reviewer,private_db,*,expected_second_head,create=False):
        # reviewer is an actual V195 E3ActualSecondUserAudit with its V194
        # archive, receipt, original and second-turn SQLite already reverified.
        self.reviewer=reviewer
        self.path=Path(private_db)
        _need(_validsha(expected_second_head),'SECOND_HEAD_REQUIRED')
        status=reviewer.status()
        _need(status['review_head_sha256']==expected_second_head and
              status['second_turn_claims_reviewed']==status['first_turn_atomic_candidates'] and
              status['unreviewed_claims']==0,'ORIGINAL_SECOND_REVIEW_NOT_FROZEN')
        _need(not status['e3_accuracy_certified'] and not status['v123_e4_authorized'] and
              not status['e5_published'],'REPAIR_MUST_NOT_CHANGE_APPROVAL')
        with reviewer._db() as con:
            _,past,_=reviewer._audit(con)
        self.past=past
        self.config={'schema':CONFIG,'source_sha256':status['source_sha256'],
           'video_id':status['video_id'],'owner_head_sha256':status['first_turn_frozen_owner_head_sha256'],
           'second_head_sha256':expected_second_head,
           'research_sha256':reviewer.config['frozen_first_study_sha256'],
           'first_turn_atoms':status['first_turn_atomic_candidates'],
           'prior_reviewed':len(past),'prior_open_cues':status['first_turn_open_cue_count'],
           'prior_source_tasks':status['first_turn_unresolved_tasks_count'],
           'prior_quarantined':status['second_turn_dispositions'].get('QUARANTINE_UNSAFE_INVESTMENT_ADVICE',0),
           'independent_gold':False,'e3_approved':False,'v123_e4_approved':False,'e5_published':False}
        _need(not self.path.is_symlink(),'PRIVATE_DB_SYMLINK')
        if self.path.exists():
            _need(not create and self.path.is_file() and
                  not (stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  'PRIVATE_DB_PERMISSION_OR_RESET')
        else:
            _need(create,'EXPLICIT_PRIVATE_NEW_DB_REQUIRED')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,prior_sha TEXT NOT NULL,event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS amendments(serial INTEGER PRIMARY KEY,event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            r=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if r:_need(json.loads(r[0])==self.config,'PINNED_OWNER_OR_SECOND_CHANGED')
            else:db.execute('INSERT INTO config VALUES(1,?)',(_canonical(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=15);db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()

    def _original_pinned(self):
        s=self.reviewer.status()
        _need(s['source_sha256']==self.config['source_sha256'] and
          s['review_head_sha256']==self.config['second_head_sha256'] and
          s['first_turn_frozen_owner_head_sha256']==self.config['owner_head_sha256'] and
          s['second_turn_claims_reviewed']==self.config['prior_reviewed'] and
          s['second_turn_dispositions'].get('QUARANTINE_UNSAFE_INVESTMENT_ADVICE',0)==self.config['prior_quarantined'],
          'ORIGINAL_V195_REVIEW_CHANGED')

    def _audit(self,db):
        prior=ZERO;amend={};seq=0
        for r in db.execute('SELECT * FROM events ORDER BY seq'):
            seq+=1;j=json.loads(r['payload'])
            _need(type(j)==dict and r['seq']==seq and r['prior_sha']==prior and
                  j.get('seq')==seq and j.get('prior_sha')==prior and
                  j.get('schema')==EVENT and
                  j.get('second_head_sha256')==self.config['second_head_sha256'] and
                  r['payload']==_canonical(j).decode() and r['event_sha']==_sha(j) and
                  type(j.get('amendments'))==list and 1<=len(j['amendments'])<=20 and
                  j.get('e3_approved') is False,
                  'EVENT_CHAIN_TAMPER')
            for x in j['amendments']:
                self._validate_one(x)
                _need(x['serial'] not in amend,'DUPLICATE_AMENDMENT')
                amend[x['serial']]=x
            prior=r['event_sha']
        stored=list(db.execute('SELECT * FROM amendments ORDER BY serial'))
        _need(len(stored)==len(amend) and
              [r['serial'] for r in stored]==sorted(amend),'AMENDMENT_CENSUS_TAMPER')
        for r in stored:
            x=json.loads(r['payload'])
            _need(x==amend[r['serial']] and r['payload']==_canonical(x).decode() and
                  r['event_sha']==_sha(x),'AMENDMENT_RECORD_TAMPER')
        return prior,amend,seq

    def prepare(self,serials):
        self._original_pinned()
        _need(type(serials)==list and 1<=len(serials)<=20 and
              all(type(x)==int for x in serials) and serials==sorted(set(serials)),
              'TARGET_SELECTION_INVALID')
        with self._db() as db:_,done,_=self._audit(db)
        t=[]
        for i in serials:
            _need(i in self.past and i not in done and
                  self.past[i]['e3_disposition'] in TARGETS,'TARGET_NOT_HOLD_OR_ALREADY_REPAIRED')
            atom=self.reviewer.atoms[i-1]
            source=[{'cue_index':j,'text':self.reviewer.cues[j]}
                    for j in atom['evidence_cues']]
            t.append({'serial':i,'first_claim_sha256':_sha(atom),
                      'prior_second_judgment_sha256':_sha(self.past[i]),
                      'first_kind':atom['kind'],'first_proposition':atom['proposition'],
                      'prior_status':self.past[i]['e3_disposition'],
                      'source_evidence':source})
        packet={'schema':PACKET,'source_sha256':self.config['source_sha256'],
           'owner_head_sha256':self.config['owner_head_sha256'],
           'second_head_sha256':self.config['second_head_sha256'],
           'targets':t,'e3_approved':False}
        packet['packet_sha256']=_sha(packet)
        return packet

    def _validate_one(self,x):
        fields={'serial','first_claim_sha256','prior_second_judgment_sha256',
           'repair_kind','source_quote_cue_index','source_quote',
           'corrected_proposition','related_serial','rationale','remaining_evidence_task',
           'original_quarantine_retained','first_turn_unchanged','second_turn_unchanged',
           'independent_gold','finance_fact_approved','e3_approved','e4_approved','e5_published'}
        _need(type(x)==dict and set(x)==fields,'CORRECTION_FIELDS_INVALID')
        i=x['serial']
        _need(type(i)==int and i in self.past,'ATOM_NOT_IN_OLD_REVIEW')
        atom=self.reviewer.atoms[i-1];old=self.past[i]
        _need(x['first_claim_sha256']==_sha(atom) and
              x['prior_second_judgment_sha256']==_sha(old),'ORIGINAL_CLAIM_OR_VERDICT_FORGED')
        _need(x['repair_kind'] in KINDS,'REPAIR_KIND_INVALID')
        _need(type(x['source_quote_cue_index'])==int and
              x['source_quote_cue_index'] in atom['evidence_cues'] and
              type(x['source_quote'])==str and len(x['source_quote'].strip())>=5 and
              x['source_quote'] in self.reviewer.cues[x['source_quote_cue_index']],
              'SOURCE_QUOTE_FORGED_OR_WRONG_CUE')
        _need(type(x['rationale'])==str and len(x['rationale'].strip())>=25 and
              type(x['remaining_evidence_task'])==str and
              len(x['remaining_evidence_task'].strip())>=20,
              'REPAIR_REASON_OR_REMAINING_TASK_MISSING')
        _need(all(x[k] is False for k in ('independent_gold','finance_fact_approved',
             'e3_approved','e4_approved','e5_published')) and
              x['first_turn_unchanged'] is True and x['second_turn_unchanged'] is True and
              x['original_quarantine_retained'] is True,
              'ILLEGAL_APPROVAL_OR_ORIGINAL_STATUS_MUTATION')
        if x['repair_kind']=='REMOVE_NONATOMIC_PROPOSED':
            _need(old['e3_disposition']=='HOLD_REMOVE_FALSE_ATOM_CANDIDATE' and
                  x['corrected_proposition'] is None and x['related_serial'] is None,
                  'REMOVE_REQUIRES_OLD_NONATOM')
        elif x['repair_kind']=='PARENT_RELATION_REVIEW_REQUIRED':
            r=x['related_serial']
            _need(type(r)==int and r!=i and 1<=r<=len(self.reviewer.atoms) and
                  abs(atom['cue_index']-self.reviewer.atoms[r-1]['cue_index'])<=12 and
                  x['corrected_proposition'] is None,
                  'PARENT_RELATION_CANNOT_AUTOMERGE')
        else:
            _need(x['repair_kind']!='PRESERVE_QUARANTINE_SOURCE_REPHRASE' or
                  old['e3_disposition']=='QUARANTINE_UNSAFE_INVESTMENT_ADVICE',
                  'QUARANTINE_REPHRASE_REQUIRES_QUARANTINE')
            p=x['corrected_proposition']
            _need(type(p)==str and len(p.strip())>=20 and
                  p!=atom['proposition'] and x['related_serial'] is None,
                  'CORRECTED_SOURCE_PROPOSITION_REQUIRED')
            context=' '.join(self.reviewer.cues[j] for j in atom['evidence_cues'])
            numeric=[t for t in NUM.findall(p) if not t.isdigit() or len(t)>1]
            # Exact numeric representations are particularly high risk: 0.5%p
            # cannot be silently inferred from the source 0.5%.
            _need(all(t in context for t in numeric),'PROPOSED_NUMERIC_UNIT_NOT_IN_ORIGINAL')
            if '항상' in p and '항상' not in context:
                raise InvalidInput('V196_E3_INVENTED_ABSOLUTE_QUALIFIER')
        return True

    def submit(self,packet,answer):
        _need(type(packet)==dict and type(answer)==dict and
              packet.get('schema')==PACKET and answer.get('schema')==ANSWER,
              'PACKET_OR_ANSWER_SCHEMA')
        _need(type(answer.get('amendments'))==list and
              1<=len(answer['amendments'])<=20 and
              [x.get('serial') for x in answer['amendments']]==
                [x['serial'] for x in packet.get('targets',[])],
              'ANSWER_SELECTION_INVALID')
        expected=self.prepare([x['serial'] for x in packet['targets']])
        _need(expected==packet and
              answer.get('packet_sha256')==packet.get('packet_sha256') and
              packet['packet_sha256']==_sha({k:v for k,v in packet.items() if k!='packet_sha256'}),
              'STALE_OR_FORGED_SOURCE_PACKET')
        _need(answer.get('review_executor')=='CHATGPT_IN_CHAT' and
              all(answer.get(k) is False for k in ('independent_gold','e3_approved','e4_approved','e5_published')),
              'FALSE_REVIEW_AUTHORITY')
        for x in answer['amendments']:self._validate_one(x)
        with self._db() as db:
            prev,done,n=self._audit(db)
            _need(not set(x['serial'] for x in answer['amendments'])&set(done),
                  'DUPLICATE_CORRECTION')
            obj={'schema':EVENT,'seq':n+1,'prior_sha':prev,
                 'second_head_sha256':self.config['second_head_sha256'],
                 'amendments':answer['amendments'],'e3_approved':False}
            h=_sha(obj)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',
                       (obj['seq'],prev,h,_canonical(obj).decode()))
            for x in answer['amendments']:
                db.execute('INSERT INTO amendments VALUES(?,?,?)',
                           (x['serial'],_sha(x),_canonical(x).decode()))
        return self.status()

    def status(self):
        self._original_pinned()
        with self._db() as db:head,records,n=self._audit(db)
        counts=Counter(x['repair_kind'] for x in records.values())
        return {'schema':'IRE_V196_E3_SECOND_REVIEW_CORRECTION_HOLD_STATUS_V1',
                'video_id':self.config['video_id'],
                'source_sha256':self.config['source_sha256'],
                'first_turn_owner_head_sha256':self.config['owner_head_sha256'],
                'v195_second_review_head_sha256':self.config['second_head_sha256'],
                'repair_overlay_head_sha256':head,'repair_events':n,
                'proposed_corrections':len(records),'correction_types':dict(counts),
                'old_120_reviews_preserved':True,
                'original_quarantined_retained':self.config['prior_quarantined'],
                'original_open_cues_preserved':self.config['prior_open_cues'],
                'original_source_tasks_preserved':self.config['prior_source_tasks'],
                'independent_gold':False,'accuracy_metrics_measured':False,
                'host_user_turn_ids_verified':False,
                'e3_approved':False,'e4_approved':False,'e5_published':False,
                'decision':'E3_HOLD_SECOND_REVIEW_CORRECTION_PROPOSED'}