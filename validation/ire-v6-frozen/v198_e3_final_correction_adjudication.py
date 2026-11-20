"""V198: actual ChatGPT source adjudication of V196 correction proposals.

Separate, append-only PRIVATE E3 review. The original V194 research, V195 review,
V196 proposals and V197 read-model remain frozen. A source-form acceptance is NOT
financial truth verification and MUST NOT authorize E4 or E5. Public tests are
synthetic only; real CMA statements and judgments never belong in GitHub.
"""
from __future__ import annotations
import json,os,re,sqlite3,stat
from pathlib import Path
from contextlib import contextmanager
from collections import Counter
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay,_sha,_canonical
from v197_e3_repaired_source_projection import _read_pinned,validate_risk_register,make_risk_register,build_review_view

CONFIG='IRE_V198_PRIVATE_SOURCE_CORRECTION_ADJUDICATION_CONFIG_V1'
EVENT='IRE_V198_SOURCE_CORRECTION_ADJUDICATION_APPEND_EVENT_V1'
PACKET='IRE_V198_SOURCE_CORRECTION_REVIEW_PACKET_V1'
VERDICT='IRE_V198_SOURCE_CORRECTION_VERDICT_V1'
VIEW='IRE_V198_CORRECTION_ADJUDICATION_UNAPPROVED_120_VIEW_V1'
BACKLOG='IRE_V198_ALL_84_RISK_PRIMARY_EVIDENCE_TRIAGE_V1'
ZERO='0'*64
HEX=re.compile(r'^[0-9a-f]{64}$')
ALLOWED={
 'SOURCE_REWRITE_PROPOSED':{'ACCEPT_SOURCE_FORM_ONLY','REJECT_UNFAITHFUL_REWRITE','HOLD_AUDIO_OR_CONTEXT'},
 'PRESERVE_QUARANTINE_SOURCE_REPHRASE':{'ACCEPT_SOURCE_FORM_ONLY','REJECT_UNFAITHFUL_REWRITE','HOLD_AUDIO_OR_CONTEXT'},
 'REMOVE_NONATOMIC_PROPOSED':{'ACCEPT_NONATOMIC_EXCLUSION_FROM_PROVISIONAL_VIEW','REJECT_NONATOMIC_EXCLUSION','HOLD_AUDIO_OR_CONTEXT'},
 'PARENT_RELATION_REVIEW_REQUIRED':{'HOLD_PARENT_EQUIVALENCE','REJECT_PARENT_MERGE'},
}
# URLs are official public pages found in this ChatGPT turn. They are NOT
# authenticated issuer raw bytes, applicability/snapshot or product terms.
PUBLIC_PRIMARY_CONTEXT={
 'KOFIA_CMA_GUIDELINE': 'https://law.kofia.or.kr/service/law/lawFullScreenContent.do?historySeq=1379&seq=285',
 'FSC_DEPOSIT_PROTECTION_FAQ':'https://www.fsc.go.kr/po020201/84975',
 'FSC_MMW_REMOTE_EXCEPTION':'https://www.fsc.go.kr/no010101/86810',
}
EVIDENCE_WORK={
 'INVESTMENT_LOSS_OR_CREDIT_RISK':('KOFIA_CMA_GUIDELINE','CMA 유형별 RP 담보권·MMF 실적배당·발행어음 발행사 신용위험과 개별 상품 약관·발행사 자료 확인'),
 'RATE_COMPARISON_OR_UNASSESSED_SWITCH':('KOFIA_CMA_GUIDELINE','기준일·세전/세후·수익률 변동·이전 비용·고객 투자 목적과 상품별 적용 조건 확인'),
 'PRODUCT_PROVIDER_TERMS':('KOFIA_CMA_GUIDELINE','회사별 가입/환매/이자지급/수수료 약관·원음/화면·MMW 비대면 가입 예외 확인'),
 'HISTORICAL_SCREEN_DATA':('KOFIA_CMA_GUIDELINE','해당 날짜 화면 원표·수익률 기준일·회사/상품명과 현재 적용 금리를 분리 확인'),
 'PERSONAL_APPLICABILITY':('KOFIA_CMA_GUIDELINE','적합성·원금손실 감내·보유기간·예금자보호 필요성과 이용 목적 확인'),
 'SOURCE_SPOKEN_NOT_CURRENT_FACT':('KOFIA_CMA_GUIDELINE','영상 발언 확인과 현재 금융 사실 근거/시행일/상품 범위 확인을 분리'),
 'ILLUSTRATIVE_RETURN_NOT_CURRENT':('KOFIA_CMA_GUIDELINE','가상 계산과 실제 현재 상품 수익률·세율·일수 계산 분리'),
}

def _need(ok,code):
    if not ok: raise InvalidInput('V198_E3_'+code)

def _shahex(s):return type(s)==str and HEX.fullmatch(s) is not None

class E3CorrectionAdjudication:
    def __init__(self,review,repair,path,*,expected_repair_head,risk_register,create=False):
        self.review=review;self.repair=repair;self.path=Path(path)
        _need(isinstance(repair,E3SecondReviewRepairOverlay) and repair.reviewer is review,
              'REPAIR_LEDGER_IDENTITY_REQUIRED')
        _need(_shahex(expected_repair_head),'PINNED_REPAIR_HEAD_REQUIRED')
        self.risk_register=risk_register
        self.v195,self.v196,self.old,self.amend=_read_pinned(review,repair,expected_repair_head)
        validate_risk_register(review,self.old,risk_register)
        _need(len(self.amend)==16 and len(self.risk_register['risk_records'])==84,
              'COMPLETE_16_AND_84_CENSUS_REQUIRED')
        self.config={'schema':CONFIG,'source_sha256':self.v195['source_sha256'],
             'first_owner_head_sha256':self.v195['first_turn_frozen_owner_head_sha256'],
             'second_review_head_sha256':self.v195['review_head_sha256'],
             'repair_proposal_head_sha256':expected_repair_head,
             'risk_register_sha256':_sha(risk_register),
             'source_review_only':True,'host_message_identity_verified':False,
             'independent_gold':False,'e3_approved':False,'e4_approved':False,'e5_published':False}
        _need(not self.path.is_symlink(),'DB_SYMLINK_REJECTED')
        if self.path.exists():
            _need(not create and self.path.is_file() and not(stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  'EXISTING_DB_PRIVATE_REQUIRED_NO_RESET')
        else:
            _need(create,'EXPLICIT_CREATE_REQUIRED')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,previous TEXT NOT NULL,event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS verdicts(serial INTEGER PRIMARY KEY,verdict_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            r=db.execute('SELECT value FROM config WHERE id=1').fetchone()
            if r:_need(json.loads(r[0])==self.config,'PINNED_CONFIG_MISMATCH')
            else:db.execute('INSERT INTO config VALUES(1,?)',(_canonical(self.config).decode(),))

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path,timeout=20);db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()

    def _pinned(self):
        a,b,old,amend=_read_pinned(self.review,self.repair,self.config['repair_proposal_head_sha256'])
        validate_risk_register(self.review,old,self.risk_register)
        _need(a['review_head_sha256']==self.config['second_review_head_sha256'] and
              b['repair_overlay_head_sha256']==self.config['repair_proposal_head_sha256'] and
              _sha(self.risk_register)==self.config['risk_register_sha256'] and
              amend==self.amend and old==self.old,
              'STALE_OR_TAMPERED_FROZEN_SOURCE')

    def packet(self,serials):
        self._pinned()
        _need(type(serials)==list and 1<=len(serials)<=16 and serials==sorted(set(serials)) and
              all(type(s)==int and s in self.amend for s in serials),'SERIAL_SELECTION_INVALID')
        with self._db() as db:_,done,_=self._audit(db)
        _need(not set(serials)&set(done),'ALREADY_ADJUDICATED')
        items=[]
        for s in serials:
            a=self.amend[s];atom=self.review.atoms[s-1];anchor=a['source_quote_cue_index']
            cues=[{'cue_index':i,'text':self.review.cues[i]} for i in range(max(1,anchor-3),
                 min(len(self.review.cues),anchor+3)+1)]
            items.append({'serial':s,'first_claim_sha256':_sha(atom),
              'second_judgment_sha256':_sha(self.old[s]),'proposal_sha256':_sha(a),
              'repair_kind':a['repair_kind'],'source_quote_cue_index':anchor,
              'source_quote':a['source_quote'],'original_claim':atom['proposition'],
              'suggested_proposition':a['corrected_proposition'],
              'old_disposition':self.old[s]['e3_disposition'],
              'first_high_risk':atom['high_risk'],
              'related_serial':a['related_serial'],'original_context':cues})
        packet={'schema':PACKET,'source_sha256':self.config['source_sha256'],
          'first_head_sha256':self.config['first_owner_head_sha256'],
          'second_head_sha256':self.config['second_review_head_sha256'],
          'proposal_head_sha256':self.config['repair_proposal_head_sha256'],
          'serials':serials,'items':items,'e3_approved':False}
        packet['packet_sha256']=_sha(packet)
        return packet

    def _validate(self,row):
        required={'schema','serial','first_claim_sha256','second_judgment_sha256','proposal_sha256',
                  'source_quote_cue_index','source_quote','decision','accepted_source_form_only',
                  'review_rationale','next_evidence_task','old_quarantine_retained',
                  'first_research_unchanged','second_review_unchanged','repair_proposal_unchanged',
                  'financial_fact_approved','independent_gold','e3_approved','e4_approved','e5_published'}
        _need(type(row)==dict and set(row)==required and row['schema']==VERDICT,'VERDICT_SCHEMA')
        s=row['serial'];_need(type(s)==int and s in self.amend,'UNKNOWN_CORRECTION_SERIAL')
        a=self.amend[s];atom=self.review.atoms[s-1];old=self.old[s]
        _need(row['first_claim_sha256']==_sha(atom) and
              row['second_judgment_sha256']==_sha(old) and
              row['proposal_sha256']==_sha(a) and
              row['source_quote_cue_index']==a['source_quote_cue_index'] and
              row['source_quote']==a['source_quote'] and
              self.review.cues[a['source_quote_cue_index']]==a['source_quote'],
              'ORIGINAL_QUOTE_OR_HASH_MISMATCH')
        _need(row['decision'] in ALLOWED[a['repair_kind']],'DECISION_FOR_REPAIR_KIND_INVALID')
        accept=row['decision']=='ACCEPT_SOURCE_FORM_ONLY'
        _need(row['accepted_source_form_only'] is accept,'ACCEPTED_FORM_ONLY_FLAG_INVALID')
        _need(type(row['review_rationale'])==str and len(row['review_rationale'].strip())>=35 and
              type(row['next_evidence_task'])==str and len(row['next_evidence_task'].strip())>=25,
              'REASONS_OR_PENDING_TASK_MISSING')
        _need(all(row[k] is True for k in ('old_quarantine_retained','first_research_unchanged',
             'second_review_unchanged','repair_proposal_unchanged')) and
             all(row[k] is False for k in ('financial_fact_approved','independent_gold',
                  'e3_approved','e4_approved','e5_published')),
             'ILLEGAL_APPROVAL_OR_HISTORY_MUTATION')
        if row['decision']=='ACCEPT_NONATOMIC_EXCLUSION_FROM_PROVISIONAL_VIEW':
            _need(not atom['high_risk'] and old['e3_disposition']=='HOLD_REMOVE_FALSE_ATOM_CANDIDATE',
                  'NONATOMIC_EXCLUSION_MUST_NOT_DISCARD_RISK')
        return True

    def _audit(self,db):
        head=ZERO;results={};count=0
        for stored in db.execute('SELECT * FROM events ORDER BY seq'):
            count+=1;item=json.loads(stored['payload'])
            _need(stored['seq']==count and stored['previous']==head and
                  item.get('seq')==count and item.get('previous')==head and
                  item.get('schema')==EVENT and
                  item.get('source_sha256')==self.config['source_sha256'] and
                  item.get('repair_head_sha256')==self.config['repair_proposal_head_sha256'] and
                  item.get('e3_approved') is False and
                  stored['payload']==_canonical(item).decode() and
                  stored['event_sha']==_sha(item),'EVENT_HASH_CHAIN_TAMPER')
            _need(type(item.get('verdicts'))==list and 1<=len(item['verdicts'])<=16,
                  'EVENT_VERDICT_BATCH_INVALID')
            for v in item['verdicts']:
                self._validate(v)
                _need(v['serial'] not in results,'DUPLICATE_VERDICT')
                results[v['serial']]=v
            head=stored['event_sha']
        saved=list(db.execute('SELECT * FROM verdicts ORDER BY serial'))
        _need(len(saved)==len(results) and [v['serial'] for v in saved]==sorted(results),
              'VERDICT_TABLE_CENSUS_TAMPER')
        for v in saved:
            obj=json.loads(v['payload'])
            _need(obj==results[v['serial']] and v['verdict_sha']==_sha(obj) and
                  v['payload']==_canonical(obj).decode(),'VERDICT_TABLE_HASH_TAMPER')
        return head,results,count

    def submit(self,packet,verdicts):
        _need(type(packet)==dict and type(verdicts)==list and 1<=len(verdicts)<=16,
              'SUBMISSION_SCHEMA')
        serials=[x.get('serial') for x in verdicts if type(x)==dict]
        _need(len(serials)==len(verdicts) and serials==sorted(set(serials)),
              'SUBMISSION_CENSUS_OR_ORDER')
        regenerated=self.packet(serials)
        _need(packet==regenerated,'STALE_OR_FORGED_SOURCE_PACKET')
        for x in verdicts:self._validate(x)
        with self._db() as db:
            prev,done,n=self._audit(db)
            _need(not set(done)&set(serials),'DUPLICATE_COMMIT')
            event={'schema':EVENT,'seq':n+1,'previous':prev,
                  'source_sha256':self.config['source_sha256'],
                  'repair_head_sha256':self.config['repair_proposal_head_sha256'],
                  'verdicts':verdicts,'e3_approved':False}
            digest=_sha(event)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',(n+1,prev,digest,_canonical(event).decode()))
            for row in verdicts:
                db.execute('INSERT INTO verdicts VALUES(?,?,?)',
                           (row['serial'],_sha(row),_canonical(row).decode()))
        return self.status()

    def decisions(self):
        self._pinned()
        with self._db() as db:_,rows,_=self._audit(db)
        return rows

    def status(self):
        self._pinned()
        with self._db() as db:head,rows,n=self._audit(db)
        counts=Counter(v['decision'] for v in rows.values())
        return {'schema':'IRE_V198_CMA_E3_SOURCE_ADJUDICATION_HOLD_V1',
           'source_sha256':self.config['source_sha256'],
           'first_frozen_head':self.config['first_owner_head_sha256'],
           'second_frozen_head':self.config['second_review_head_sha256'],
           'v196_proposal_head':self.config['repair_proposal_head_sha256'],
           'adjudication_head_sha256':head,'events':n,'reviewed':len(rows),
           'unreviewed':16-len(rows),'decisions':dict(counts),
           'original_candidates_preserved':120,'high_risk_blocked':84,
           'quarantined_preserved':28,'risk_source_census_preserved':84,
           'first_turn_open_cues_preserved':14,'first_turn_tasks_preserved':34,
           'financial_gold_precision':None,'financial_gold_recall':None,
           'host_turn_ids_verified':False,'e3_approved':False,'e4_approved':False,
           'e5_published':False,'decision':'E3_HOLD_CORRECTION_REVIEW_ONLY'}


def build_effective_unapproved_view(adjudication):
    """Provisional *research* projection only. Never serves investment advice."""
    z=adjudication
    decisions=z.decisions()
    _need(sorted(decisions)==sorted(z.amend),'ALL_16_DECISIONS_REQUIRED')
    old_view=build_review_view(z.review,z.repair,expected_overlay_head=z.config['repair_proposal_head_sha256'],
                               risk_register=z.risk_register)
    rows=[]
    for r in old_view['records']:
        s=r['serial'];v=decisions.get(s);patch=z.amend.get(s)
        accepted=v and v['decision']=='ACCEPT_SOURCE_FORM_ONLY'
        excluded=v and v['decision']=='ACCEPT_NONATOMIC_EXCLUSION_FROM_PROVISIONAL_VIEW'
        row={**r,'v198_correction_decision':v['decision'] if v else None,
          'source_attributed_revision_only':patch['corrected_proposition'] if accepted else None,
          'excluded_from_effective_provisional_atoms_only':bool(excluded),
          'original_frozen_row_still_preserved':True,
          'financial_truth_approved':False,'safe_for_financial_answers':False,
          'e3_approved':False,'e4_approved':False,'e5_published':False}
        _need(not (excluded and r['first_turn_high_risk']),'NO_HIGH_RISK_EXCLUSION')
        rows.append(row)
    ex=sum(r['excluded_from_effective_provisional_atoms_only'] for r in rows)
    hr=sum(r['first_turn_high_risk'] and not r['safe_for_financial_answers'] for r in rows)
    _need(len(rows)==120 and ex==2 and hr==84 and
          sum(r['old_quarantine_enforced'] for r in rows)==28 and
          all(not r['financial_truth_approved'] for r in rows),
          'READ_MODEL_DROPPED_A_RISK_OR_FROZEN_CLAIM')
    return {'schema':VIEW,'source_sha256':z.config['source_sha256'],
         'v198_decision_head_sha256':z.status()['adjudication_head_sha256'],
         'frozen_original_candidates':120,'effective_provisional_nonatomic_exclusions':ex,
         'effective_provisional_candidates_unapproved':120-ex,
         'all_original_high_risk_blocked':hr,'old_quarantines_preserved':28,
         'records':rows,'finance_gold_certified':False,'e3_approved':False,
         'e4_approved':False,'e5_published':False}


def build_84_evidence_triage(adjudication):
    """Web text checked for broad topic relevance only, no per-atom certification."""
    z=adjudication;z._pinned();risk=z.risk_register['risk_records']
    _need(len(risk)==84,'HIGH_RISK_84_REQUIRED')
    cases=[]
    for row in risk:
        family=row['risk_family'];_need(family in EVIDENCE_WORK,'UNKNOWN_FINANCIAL_RISK_FAMILY')
        ref,task=EVIDENCE_WORK[family]
        cases.append({'serial':row['serial'],'claim_sha256':row['claim_sha256'],
          'source_text_sha256':row['source_text_sha256'],
          'prior_judgment_sha256':row['prior_judgment_sha256'],
          'risk_family':family,'candidate_primary_topic':ref,
          'required_financial_fact_check':task,
          'official_web_text_candidate_url':PUBLIC_PRIMARY_CONTEXT[ref],
          'web_reference_is_topic_context_only':True,
          'official_raw_byte_snapshot_verified':False,
          'issuer_or_product_specific_evidence_verified':False,
          'effective_date_and_scope_verified':False,
          'claim_correctness_verified':False,'financial_use_blocked':True,
          'e3_approved':False,'e4_approved':False,'e5_published':False})
    _need(len(set(c['serial'] for c in cases))==84 and
          sum(c['serial'] in [r['serial'] for r in risk if r['old_disposition']==
             'QUARANTINE_UNSAFE_INVESTMENT_ADVICE'] for c in cases)==28,
          'RISK_84_OR_QUARANTINE_COVERAGE')
    return {'schema':BACKLOG,'source_sha256':z.config['source_sha256'],
          'v198_adjudication_head_sha256':z.status()['adjudication_head_sha256'],
          'source_risk_register_sha256':_sha(z.risk_register),
          'official_primary_public_web_text_candidate_only':True,
          'issuer_raw_bytes_verified':False,'complete_current_financial_evidence':False,
          'risk_cases':cases,'risk_family_counts':dict(Counter(c['risk_family'] for c in cases)),
          'original_risk_total':84,'quarantines_retained':28,
          'all_risk_cases_blocked':True,
          'e3_approved':False,'e4_approved':False,'e5_published':False}