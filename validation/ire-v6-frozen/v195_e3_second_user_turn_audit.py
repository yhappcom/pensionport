"""V195 final ChatGPT E3 *second user-command* audit over V194 frozen owner journal.

No model API; accepts ONLY ChatGPT-written source-specific private adjudications.
Checks the old V194 source/owner checkpoint against external hashes on each open,
replays each signed-content append-only second-review event, rejects invented
quotes, changed original judgments, false E3/gold/E4/E5 authority, and refuses
self-certification of ChatGPT host message IDs. Records HOLD/QUARANTINE ONLY.

PRIVATE: do not publish SRT, user-specific review JSON, or this journal SQLite.
"""
from __future__ import annotations
from collections import Counter
from contextlib import contextmanager
import hashlib, json, os, re, sqlite3, stat, zipfile
from pathlib import Path

from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v194_e3_turn1_freeze import restore_verify
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt

SCHEMA='IRE_V195_ACTUAL_USER_TURN2_CMA_CHATGPT_SEMANTIC_REVIEW_V1'
EVENT_SCHEMA='IRE_V195_CMA_FINAL_CHATGPT_SECOND_USER_REVIEW_EVENT_V1'
JOURNAL_SCHEMA='IRE_V195_CMA_PRIVATE_ACTUAL_SECOND_USER_REVIEW_JOURNAL_V1'
STATUS=('HOLD_SOURCE_SPOKEN_FINANCIAL_TRUTH_UNCERTIFIED',
'HOLD_SOURCE_MEANING_REPAIR','QUARANTINE_UNSAFE_INVESTMENT_ADVICE',
'HOLD_EXTERNAL_AUDIO_VISUAL_OR_PRODUCT_EVIDENCE',
'HOLD_REMOVE_FALSE_ATOM_CANDIDATE')
FINANCIAL=('EXAGGERATED_SAFETY_OR_IGNORED_LOSS_RISK','UNIVERSAL_RATE_OR_SWITCH_ADVICE_UNSUPPORTED',
'HISTORICAL_DATE_OR_UNREAD_SCREEN_DATA','PRODUCT_TERMS_OR_PROVIDER_SCOPE_NOT_VERIFIED',
'ILLUSTRATIVE_NOT_CURRENT_RETURN','INVESTOR_APPLICABILITY_UNASSESSED',
'SOURCE_QUOTE_ONLY_NOT_FACT_CERTIFIED')
FLAGS=('NOT_ATOMIC','OVERREACH','CONDITION_LOSS','STANCE_DIFF','SCREEN_ONLY',
'POSSIBLE_DUPLICATE','ASR_OR_PROVIDER_SCOPE_OPEN',
'SPOKEN_POSITION_RETAINED_PENDING_EVIDENCE')
HEX=re.compile(r'^[0-9a-f]{64}$')
ZERO='0'*64

def _need(value,code):
    if not value:raise InvalidInput('V195_E3_'+code)

def _canon(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')
def _hash(obj):return sha256(_canon(obj))
def _hex(x):return isinstance(x,str) and HEX.fullmatch(x) is not None

def original_cues(raw):
    cues={}
    for block in re.split(r'\n\s*\n',raw.decode('utf-8-sig').strip()):
        part=block.strip().splitlines()
        _need(len(part)>=3 and part[0].isdigit(),'ORIGINAL_SRT_CUE_FORMAT')
        i=int(part[0]);_need(i not in cues,'DUPLICATE_SOURCE_CUE')
        cues[i]=' '.join(part[2:]).strip()
    _need(list(cues)==list(range(1,len(cues)+1)),'SOURCE_CUE_SEQUENCE_INVALID')
    return cues

class E3ActualSecondUserAudit:
    def __init__(self,*,frozen_archive:Path,external_receipt:dict,private_db:Path,
                 second_user_ref:str,second_user_message_sha256:str,create=False):
        self.archive=Path(frozen_archive);self.receipt=external_receipt;self.path=Path(private_db)
        self.second_user_ref=second_user_ref;self.second_user_sha=second_user_message_sha256
        _need(_hex(second_user_message_sha256) and isinstance(second_user_ref,str)
              and second_user_ref.startswith('user:') and len(second_user_ref)>5,
              'SECOND_USER_COMMAND_OBSERVATION_MISSING')
        _need(isinstance(external_receipt,dict) and
              external_receipt.get('schema')=='IRE_V194_TURN1_SOURCE_FROZEN_SHA_ONLY_RECEIPT_V1',
              'V194_EXACT_RECEIPT_REQUIRED')
        x=restore_verify(archive_path=self.archive,
          expected_archive_sha256=external_receipt['archive_sha256'],
          expected_manifest_sha256=external_receipt['manifest_sha256'],
          expected_source_sha256=external_receipt['source_sha256'],
          expected_owner_head_sha256=external_receipt['owner_head_sha256'])
        _need(x['phase']=='AWAIT_SEPARATE_USER_VERIFICATION_COMMAND' and
              not x['turn2_review_performed'],'FIRST_FROZEN_OWNER_STATE_INVALID')
        with zipfile.ZipFile(self.archive) as z:
            self.original=z.read('cma_original.srt')
            self.study=json.loads(z.read('cma_first_research.json'))
            self.manifest=json.loads(z.read('turn1_manifest.json'))
        self.cues=original_cues(self.original)
        self.atoms=self.study['claims'];self.parents=self.study['parents']
        self.parent_for={i:p['parent_id'] for p in self.parents for i in range(p['start_cue'],p['end_cue']+1)}
        _need(len(self.cues)==self.study['cue_count'] and
              len(self.atoms)==self.study['claim_count'] and
              self.manifest['turn1_research_sha256']==_hash(self.study) and
              external_receipt['unresolved_tasks']==len(self.study['unresolved_cue_issues']) and
              external_receipt['claim_count']==len(self.atoms),
              'FROZEN_RESEARCH_SHA_OR_CENSUS')
        _need(external_receipt.get('untrusted_manual_first_user_ref')!=second_user_ref,
              'SAME_USER_MESSAGE_REUSED')
        self.config={
          'schema':JOURNAL_SCHEMA,'video_id':self.study['video_id'],
          'source_sha256':external_receipt['source_sha256'],
          'frozen_owner_head_sha256':external_receipt['owner_head_sha256'],
          'frozen_first_study_sha256':self.manifest['turn1_research_sha256'],
          'first_user_ref_unverified':external_receipt['untrusted_manual_first_user_ref'],
          'first_user_text_sha256':external_receipt['first_turn_text_sha256'],
          'second_user_ref_unverified':second_user_ref,
          'second_user_text_sha256':second_user_message_sha256,
          'host_two_turn_identity_verified':False,'e3_approved':False,
          'v123_approved':False,'e4_approved':False,'e5_published':False}
        _need(not self.path.is_symlink(),'PRIVATE_DB_SYMLINK')
        if self.path.exists():
            _need(not create and self.path.is_file() and
              not(stat.S_IMODE(self.path.stat().st_mode)&0o077),
              'PRIVATE_DB_PERMISSIONS_OR_NO_OVERWRITE')
        else:
            _need(create,'EXPLICIT_NEW_AUDIT_REQUIRED')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, previous TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS judgments (serial INTEGER PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL)')
            r=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if r:_need(json.loads(r[0])==self.config,'FROZEN_TURN_CONFIG_CHANGED')
            else:db.execute('INSERT INTO config VALUES (1,?)',(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        con=sqlite3.connect(self.path,timeout=20)
        con.row_factory=sqlite3.Row
        try:yield con;con.commit()
        except BaseException:con.rollback();raise
        finally:con.close()

    def _audit(self,db):
        last=ZERO;rows={}
        for n,r in enumerate(db.execute('SELECT * FROM events ORDER BY seq'),1):
            j=json.loads(r['payload'])
            _need(type(j)==dict and r['seq']==n and r['previous']==last and
                  j.get('seq')==n and j.get('previous')==last and
                  j.get('schema')==EVENT_SCHEMA and
                  j.get('source_sha256')==self.config['source_sha256'] and
                  j.get('first_turn_owner_head_sha256')==self.config['frozen_owner_head_sha256'] and
                  j.get('second_user_sha256')==self.second_user_sha and
                  r['payload']==_canon(j).decode() and r['digest']==_hash(j),
                  'EVENT_HASH_CHAIN_TAMPER')
            _need(len(j['reviews'])>=1 and len(j['reviews'])<=20,
                  'EVENT_BATCH_SIZE_INVALID')
            for row in j['reviews']:
                self._validate_one(row)
                serial=row['claim_serial'];_need(serial not in rows,'DUPLICATE_REVIEW_SERIAL')
                rows[serial]=row
            last=r['digest']
        stored=list(db.execute('SELECT * FROM judgments ORDER BY serial'))
        _need(len(stored)==len(rows) and
              [r['serial'] for r in stored]==sorted(rows),
              'JUDGMENT_CENSUS_OR_TAMPER')
        for r in stored:
            obj=json.loads(r['payload'])
            _need(obj==rows[r['serial']] and
                  _canon(obj).decode()==r['payload'] and
                  r['digest']==_hash(obj),'JUDGMENT_RECORD_TAMPER')
        _need(sorted(rows)==list(range(1,len(rows)+1)),'REVIEW_SEQUENCE_OR_GAP')
        return last,rows,n if stored else 0

    def _validate_one(self,row):
        _need(type(row)==dict and
              set(row)=={'claim_serial','cue_index','parent_id','first_turn_quote_sha256',
                        'first_turn_proposition_sha256','first_turn_kind','first_turn_high_risk_flag',
                        'review_uses_exact_original_cue_quote','source_fidelity_flags',
                        'financial_problem','source_specific_rationale','official_public_text_refs',
                        'e3_disposition','independent_gold','finance_fact_approved',
                        'v123_approved','e4_approved','e5_published'},
              'REVIEW_KEYS_OR_AUTHORITY')
        serial=row['claim_serial']
        _need(type(serial)==int and 1<=serial<=len(self.atoms),'REVIEW_ATOM_SERIAL_INVALID')
        atom=self.atoms[serial-1];i=atom['cue_index'];src=self.cues[i]
        _need(row['cue_index']==i and row['parent_id']==self.parent_for[i] and
              row['first_turn_quote_sha256']==sha256(src.encode()) and
              row['first_turn_proposition_sha256']==sha256(atom['proposition'].encode()) and
              row['first_turn_kind']==atom['kind'] and
              row['first_turn_high_risk_flag'] is atom['high_risk'] and
              row['review_uses_exact_original_cue_quote'] is True,
              'CLAIM_SOURCE_ANCHOR_FORGED')
        flags=row['source_fidelity_flags'];
        _need(type(flags)==list and len(flags)==1 and flags[0] in FLAGS,
              'SOURCE_FIDELITY_ISSUE_INVALID')
        _need(row['financial_problem'] in FINANCIAL and row['e3_disposition'] in STATUS and
              type(row['source_specific_rationale'])==str and
              len(row['source_specific_rationale'].strip())>=35,
              'REVIEW_JUDGMENT_INCOMPLETE')
        refs=row['official_public_text_refs']
        _need(isinstance(refs,list) and len(refs)==len(set(refs)) and
              set(refs)<={'kofia_cma','fsc_deposits','fsc_mmw','bok_rate','mirae_issuer'},
              'UNVERIFIED_FINANCIAL_SOURCE_INJECTED')
        _need(all(row[k] is False for k in
              ('independent_gold','finance_fact_approved','v123_approved','e4_approved','e5_published')),
              'ILLEGAL_APPROVAL_IN_TURN2')

    def submit(self,reviews):
        _need(isinstance(reviews,list) and 1<=len(reviews)<=20,'SUBMISSION_SIZE')
        with self._db() as db:
            last,existing,eventcount=self._audit(db)
            expected=list(range(len(existing)+1,len(existing)+1+len(reviews)))
            _need([x.get('claim_serial') for x in reviews]==expected and
                  max(expected)<=len(self.atoms),'STALE_DUPLICATE_OR_SKIPPED_REVIEWS')
            for r in reviews:self._validate_one(r)
            obj={'schema':EVENT_SCHEMA,'seq':eventcount+1,'previous':last,
                 'source_sha256':self.config['source_sha256'],
                 'first_turn_owner_head_sha256':self.config['frozen_owner_head_sha256'],
                 'second_user_sha256':self.second_user_sha,'reviews':reviews,
                 'e3_approved':False,'e4_approved':False,'e5_published':False}
            digest=_hash(obj)
            db.execute('INSERT INTO events VALUES (?,?,?,?)',
              (obj['seq'],last,digest,_canon(obj).decode()))
            for r in reviews:
                db.execute('INSERT INTO judgments VALUES (?,?,?)',
                           (r['claim_serial'],_hash(r),_canon(r).decode()))
        return self.status()

    def status(self):
        with self._db() as db:
            head,rows,eventcount=self._audit(db)
        if rows:
            # Counts derive solely from audited primary-source, private E3 human authored judgments.
            c=Counter(x['e3_disposition'] for x in rows.values())
            flag=Counter(x['source_fidelity_flags'][0] for x in rows.values())
            finance=Counter(x['financial_problem'] for x in rows.values())
        else:c=Counter();flag=Counter();finance=Counter()
        second=None
        if len(rows)==len(self.atoms):
            second={'phase':'CHATGPT_FINAL_SEMANTIC_VERIFICATION',
              'user_message_ref':self.second_user_ref,
              'user_message_sha256':self.second_user_sha,
              'source_sha256':self.config['source_sha256'],
              'owner_head_sha256':self.config['frozen_owner_head_sha256'],
              'review_recorded':True,'review_head_sha256':head}
        first={'phase':'RESEARCH_AND_FREEZE','user_message_ref':self.config['first_user_ref_unverified'],
               'user_message_sha256':self.config['first_user_text_sha256'],
               'source_sha256':self.config['source_sha256'],
               'owner_head_sha256':self.config['frozen_owner_head_sha256'],
               'research_frozen':True}
        receipt=validate_manual_turn_receipt(first=first,second=second,
          source_sha256=self.config['source_sha256'],
          owner_head_sha256=self.config['frozen_owner_head_sha256'],
          batch_count=eventcount)
        return {'schema':'IRE_V195_ACTUAL_SECOND_CHAT_REVIEW_STATUS_V1',
          'video_id':self.config['video_id'],'source_cue_count':len(self.cues),
          'source_sha256':self.config['source_sha256'],
          'first_turn_frozen_owner_head_sha256':self.config['frozen_owner_head_sha256'],
          'source_parent_count':len(self.parents),
          'first_turn_atomic_candidates':len(self.atoms),
          'second_turn_claims_reviewed':len(rows),'unreviewed_claims':len(self.atoms)-len(rows),
          'second_turn_events':eventcount,'review_head_sha256':head,
          'first_turn_open_cue_count':self.receipt['open_cues'],
          'first_turn_unresolved_tasks_count':self.receipt['unresolved_tasks'],
          'first_turn_nonclaim_or_open_cues_count':len(self.cues)-len(self.atoms),
          'second_turn_dispositions':dict(c),'source_fidelity_flags':dict(flag),
          'financial_problem_flags':dict(finance),'manual_phase_receipt':receipt,
          'actual_separate_user_commands_observed_in_chat':len(rows)==len(self.atoms),
          'host_message_identity_verified':False,'independent_gold':False,
          'precision':None,'recall':None,'high_risk_miss_rate':None,
          'official_issuer_raw_bytes_verified':False,
          'e3_accuracy_certified':False,'v123_e4_authorized':False,'e5_published':False,
          'decision':'E3_HOLD_WITH_HIGH_RISK_QUARANTINE_AND_SOURCE_REPAIR'}

def verify_full_private_response(review:dict,ledger:E3ActualSecondUserAudit):
    """Enforce a complete, source-pinned final ChatGPT E3 reviewer packet."""
    _need(type(review)==dict and review.get('schema')==SCHEMA and
          review.get('phase')=='CHATGPT_FINAL_SEMANTIC_VERIFICATION',
          'RESPONSE_SCHEMA_OR_PHASE')
    _need(review.get('video_id')==ledger.study['video_id'] and
          review.get('source_sha256')==ledger.config['source_sha256'] and
          review.get('frozen_first_turn_owner_head_sha256')==ledger.config['frozen_owner_head_sha256'] and
          review.get('frozen_first_turn_research_sha256')==ledger.config['frozen_first_study_sha256'] and
          review.get('first_turn_archive_sha256')==ledger.receipt['archive_sha256'] and
          review.get('first_user_message_text_sha256')==ledger.config['first_user_text_sha256'] and
          review.get('second_user_message_text_sha256')==ledger.second_user_sha and
          review.get('manual_first_user_ref')==ledger.config['first_user_ref_unverified'] and
          review.get('manual_second_user_ref')==ledger.second_user_ref and
          review.get('platform_user_turn_id_verification')=='NOT_AVAILABLE_SELF_REPORTED_OBSERVATION',
          'SECOND_USER_SOURCE_OR_TURN_PIN_MISMATCH')
    _need(review.get('original_cues_read')==len(ledger.cues) and
          review.get('first_claims_reviewed')==len(ledger.atoms) and
          review.get('parent_units_inspected')==len(ledger.parents),
          'NO_REAL_FULL_REVIEW_CENSUS')
    a=review.get('judgments');_need(isinstance(a,list) and len(a)==len(ledger.atoms),
                                   'FINAL_JUDGMENT_CENSUS')
    for serial,row in enumerate(a,1):
        _need(row.get('claim_serial')==serial,'FINAL_REVIEW_SEQUENCE')
        ledger._validate_one(row)
    stored=review.get('first_turn_issues_preserved')
    _need(isinstance(stored,list) and len(stored)==len(ledger.study['unresolved_cue_issues']) and
          all(p.get('cue_index')==q['cue_index'] and p.get('first_turn_task')==q['task'] and
                  p.get('turn2_status')=='STILL_OPEN_NOT_AUTO_CLEARED' and
                  p.get('evidence_required') is True
                 for p,q in zip(stored,ledger.study['unresolved_cue_issues'])),
          'OPEN_FIRST_TURN_ISSUE_SILENTLY_ERASED')
    extra=review.get('additional_turn2_source_tasks')
    _need(isinstance(extra,list) and extra and
          len(extra)==len({r.get('cue_index') for r in extra}) and
          all(r.get('cue_index') in ledger.cues and type(r.get('task'))==str and
                  len(r['task'])>=30 for r in extra),
          'SECOND_TURN_SOURCE_REPAIR_TASKS_MISSING')
    refs=review.get('official_primary_public_text')
    _need(isinstance(refs,dict) and refs and
          all(x.get('verification') in ('PUBLIC_WEB_TEXT_READ_NO_ISSUER_RAW_SHA_OR_EFFECTIVE_DATE_CUSTODY',
                                      'PUBLIC_SEARCH_SNIPPET_ONLY_RAW_PDF_NOT_VERIFIED')
              and isinstance(x.get('url'),str) and x['url'].startswith('https://')
              for x in refs.values()),'ISSUER_WEB_TEXT_FALSE_CUSTODY')
    _need(review.get('decision')=='E3_HOLD_WITH_HIGH_RISK_QUARANTINE_AND_SOURCE_REPAIR' and
          review.get('nonclaim_cue_review',{}).get('original_cues_covered')==len(ledger.cues) and
          review.get('nonclaim_cue_review',{}).get('completeness_independently_proven') is False and
          review.get('official_issuer_raw_bytes_sha256_verified') is False and
          review.get('financial_fact_accuracy_certified') is False and
          all(review.get(x) is None for x in ('precision','recall','high_risk_miss_rate')) and
          all(review.get(x) is False for x in ('e3_approved','v123_approved','e4_approved','e5_published')),
          'E3_FINANCIAL_APPROVAL_FALSE_CLAIM')
    return {'validated_reviews':len(a),'source_cues':len(ledger.cues),
            'review_bytes_sha256':_hash(review),'e3_approved':False}