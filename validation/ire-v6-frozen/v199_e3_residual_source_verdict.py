"""V199 E3 post-failure source verdicts for six actual held CMA atoms.

Public deterministic validation only. ChatGPT authors source verdicts in the current
conversation; no LLM API, no automatic speech transcription, no E3/E4 approval.
No owner SRT, owner judgments, or private evidence content is bundled here.
"""
from __future__ import annotations
from collections import Counter
from contextlib import contextmanager
import os, re, sqlite3, stat, json
from pathlib import Path

from ire.v6.errors import InvalidInput
from v196_e3_second_review_repair import _sha, _canonical
from v198_e3_final_correction_adjudication import (
    E3CorrectionAdjudication, build_effective_unapproved_view,
    build_84_evidence_triage,
)

PACKET = 'IRE_V199_E3_SIX_SOURCE_RESIDUAL_PACKET_V1'
ROW = 'IRE_V199_E3_SIX_SOURCE_RESIDUAL_VERDICT_V1'
EVENT = 'IRE_V199_E3_SIX_SOURCE_RESIDUAL_EVENT_V1'
CONFIG = 'IRE_V199_E3_SIX_SOURCE_RESIDUAL_CONFIG_V1'
VIEW = 'IRE_V199_E3_RESIDUAL_6_AND_84_BLOCKED_VIEW_V1'
ZERO = '0'*64
HEX = re.compile(r'^[0-9a-f]{64}$')

# For financial-context screening, these are verified web-rendered pages, not
# an independent issuer raw-byte archive or a representation of effective law.
PUBLIC_WEB_CONTEXT = {
 'KOFIA_CMA_GUIDELINE': {
   'url':'https://law.kofia.or.kr/service/law/lawFullScreenContent.do?historySeq=1379&seq=285',
   'issuer':'금융투자협회','scope':'CMA RP/MMF/발행어음 위험고지 및 적합성; 회사별 약관 아님'},
 'MERITZ_MMW_NOTICE': {
   'url':'https://www.imeritz.com/meritzcma/CmaMmw.do',
   'issuer':'메리츠증권','scope':'MMW 일임형 랩 계약, 한국증권금융 예수금, 실적배당 및 수수료; 메리츠 사례'},
 'KIS_CMA_GUIDE': {
   'url':'https://file.truefriend.com/Storage/customer/guide/regards/cma_instruction.htm',
   'issuer':'한국투자증권','scope':'2021.07.30 설명서; 회사별 발행어음 자동매매·MMW 운용 및 출금 조건의 과거 예시'},
 'KIS_WRAP_GUIDE': {
   'url':'https://securities.koreainvestment.com/main/mall/opentrustwrap/WrapInfo.jsp?category=M&cmd=TF02eb010100',
   'issuer':'한국투자증권','scope':'MMW형 CMA와 별도 랩 유형 구별; 전체 랩 일반화 금지'},
 'FSC_REMOTE_MMW': {
   'url':'https://www.fsc.go.kr/no010101/86810',
   'issuer':'금융위원회','scope':'2026.04.29 한국투자증권 MMW-CMA 비대면 설명 특례; 모든 회사 일반화 금지'},
}

# These *semantic source* statuses never remove a recorded financial warning.
RULES = {
 20: ('PARENT_SAME_GENERALIZATION_PROVISIONAL_KEEP_BOTH',19),
 28: ('MULTI_CLAIM_SOURCE_SPLIT_PROPOSED_HOLD',None),
 31: ('ASR_TERM_PROVISIONAL_AUDIO_REQUIRED',None),
 68: ('DAILY_PAYMENT_ACCRUAL_COMPOUNDING_OPEN',None),
 82: ('PARENT_CHILD_FLOW_VS_INVESTMENT_KEEP_BOTH',81),
 112: ('SPOKEN_EQUIVALENCE_RETAIN_UNVERIFIED_TRUTH',None),
}
AUDIO_UNRESOLVED = {31,68}
PARENT_ISSUES = {20,82}


def _require(ok,reason):
    if not ok: raise InvalidInput('V199_E3_'+reason)


class E3SixResidualVerdicts:
    def __init__(self, v198: E3CorrectionAdjudication, db_path, *, expected_v198_head, create=False):
        _require(isinstance(v198,E3CorrectionAdjudication),'V198_AUDIT_REQUIRED')
        _require(isinstance(expected_v198_head,str) and HEX.fullmatch(expected_v198_head),
                 'PINNED_V198_HEAD_REQUIRED')
        self.v198=v198;self.path=Path(db_path);self.expected_v198_head=expected_v198_head
        status=v198.status()
        _require(status['adjudication_head_sha256']==expected_v198_head and status['reviewed']==16,
                 'V198_FINAL_16_VERDICTS_NOT_PINNED')
        self.v198_rows=v198.decisions()
        self.effective=build_effective_unapproved_view(v198)
        self.risks=build_84_evidence_triage(v198)
        _require(len(self.effective['records'])==120 and len(self.risks['risk_cases'])==84 and
                 self.effective['all_original_high_risk_blocked']==84 and
                 self.effective['old_quarantines_preserved']==28 and
                 self.risks['all_risk_cases_blocked'] is True,
                 'FROZEN_120_OR_HIGH_RISK_84_INCOMPLETE')
        for serial in RULES:
            _require(self.v198_rows[serial]['decision'] in (
                'HOLD_PARENT_EQUIVALENCE','REJECT_UNFAITHFUL_REWRITE','HOLD_AUDIO_OR_CONTEXT'),
                'NOT_A_REAL_V198_UNRESOLVED_SERIAL')
        self.config={'schema':CONFIG,'source_sha256':v198.config['source_sha256'],
             'v194_first_head_sha256':status['first_frozen_head'],
             'v195_second_head_sha256':status['second_frozen_head'],
             'v196_repair_head_sha256':status['v196_proposal_head'],
             'v198_adjudication_head_sha256':expected_v198_head,
             'effective_120_sha256':_sha(self.effective),
             'risk_84_sha256':_sha(self.risks),
             'web_context_registry_sha256':_sha(PUBLIC_WEB_CONTEXT),
             'official_issuer_raw_bytes_certified':False,'host_message_id_verified':False,
             'e3_approved':False,'e4_approved':False,'e5_published':False}
        _require(not self.path.is_symlink(),'DB_SYMLINK_FORBIDDEN')
        if self.path.exists():
            _require(not create and self.path.is_file() and not(stat.S_IMODE(self.path.stat().st_mode)&0o077),
                     'EXISTING_PRIVATE_DB_REQUIRED_NO_RESET')
        else:
            _require(create,'EXPLICIT_CREATE_REQUIRED')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_WRONLY|os.O_EXCL|os.O_CREAT,0o600);os.close(fd)
        with self._db() as con:
            con.execute('CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,previous_sha TEXT NOT NULL,event_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS decisions(serial INTEGER PRIMARY KEY,verdict_sha TEXT NOT NULL,payload TEXT NOT NULL)')
            r=con.execute('SELECT value FROM config WHERE id=1').fetchone()
            if r: _require(json.loads(r[0])==self.config,'PINNED_CONFIG_MISMATCH')
            else: con.execute('INSERT INTO config VALUES(1,?)',(_canonical(self.config).decode(),))

    @contextmanager
    def _db(self):
        con=sqlite3.connect(self.path,timeout=15)
        con.row_factory=sqlite3.Row
        try:
            yield con
            con.commit()
        except BaseException:
            con.rollback();raise
        finally:
            con.close()

    def _frozen(self):
        s=self.v198.status()
        _require(s['adjudication_head_sha256']==self.expected_v198_head and
                 self.v198.decisions()==self.v198_rows and
                 _sha(build_effective_unapproved_view(self.v198))==self.config['effective_120_sha256'] and
                 _sha(build_84_evidence_triage(self.v198))==self.config['risk_84_sha256'] and
                 _sha(PUBLIC_WEB_CONTEXT)==self.config['web_context_registry_sha256'],
                 'PRIOR_JOURNAL_OR_FINANCIAL_SOURCE_CHANGED')

    def _audit(self,con):
        head=ZERO;rows={};n=0
        for r in con.execute('SELECT * FROM events ORDER BY seq'):
            event=json.loads(r['payload'])
            _require(r['seq']==n+1 and r['previous_sha']==head and
                     r['event_sha']==_sha(event) and _canonical(event).decode()==r['payload'] and
                     event['seq']==n+1 and event['previous_sha']==head and
                     event['schema']==EVENT and event['source_sha256']==self.config['source_sha256'] and
                     event['v198_adjudication_head_sha256']==self.expected_v198_head and
                     all(event[k] is False for k in ('e3_approved','e4_approved','e5_published')),
                     'EVENT_HASH_CHAIN_TAMPER')
            _require(event['serials']==[a['serial'] for a in event['decisions']] and
                     event['serials']==sorted(set(event['serials'])),'EVENT_ROWS_OR_ORDER_CHANGED')
            for answer in event['decisions']:
                self._validate(answer)
                serial=answer['serial'];_require(serial not in rows,'DUPLICATE_EVENT_SERIAL')
                rows[serial]=answer
            head=r['event_sha'];n+=1
        dbrows=con.execute('SELECT * FROM decisions ORDER BY serial').fetchall()
        _require([r['serial'] for r in dbrows]==sorted(rows),'DECISION_TABLE_KEYS_DRIFT')
        for r in dbrows:
            a=rows[r['serial']]
            _require(r['verdict_sha']==_sha(a) and r['payload']==_canonical(a).decode(),
                     'VERDICT_TABLE_HASH_TAMPER')
        return head,rows,n

    def _challenge(self,serials):
        atom_list=self.v198.review.atoms;cues=self.v198.review.cues
        output=[]
        for s in serials:
            claim=atom_list[s-1];adj=self.v198_rows[s];ix=claim['cue_index']
            neighbors=[{'cue_index':j,'source_text':cues[j]} for j in range(max(1,ix-5),
                                             min(len(cues),ix+5)+1)]
            output.append({'serial':s,'kind':claim['kind'],
               'original_proposition':claim['proposition'],
               'original_claim_sha256':_sha(claim),
               'v198_verdict_sha256':_sha(adj),
               'v198_decision':adj['decision'],
               'allowed_conclusion':RULES[s][0],
               'related_parent_serial':RULES[s][1],
               'original_context':neighbors})
        result={'schema':PACKET,'source_sha256':self.config['source_sha256'],
           'v194_first_head_sha256':self.config['v194_first_head_sha256'],
           'v195_second_head_sha256':self.config['v195_second_head_sha256'],
           'v198_adjudication_head_sha256':self.expected_v198_head,
           'public_web_context':PUBLIC_WEB_CONTEXT,
           'serials':serials,'items':output,'e3_approved':False}
        result['packet_sha256']=_sha(result)
        return result

    def prepare(self,serials):
        self._frozen();_require(type(serials)==list and serials==sorted(set(serials)) and
              1<=len(serials)<=6 and all(type(s)==int and s in RULES for s in serials),
              'TARGET_SERIALS_INVALID')
        with self._db() as con:_,rows,_=self._audit(con)
        _require(not any(s in rows for s in serials),'ALREADY_REVIEWED')
        return self._challenge(serials)

    def _validate(self,v):
        keys={'schema','serial','original_claim_sha256','v198_verdict_sha256',
              'conclusion','parent_serial','source_clauses','official_context_refs',
              'review_rationale','next_evidence_task','audio_verified',
              'raw_issuer_bytes_verified','financial_fact_verified',
              'first_journal_unchanged','second_journal_unchanged','v198_journal_unchanged',
              'risk_84_blocked','quarantines_28_preserved',
              'independent_gold','e3_approved','e4_approved','e5_published'}
        _require(type(v)==dict and set(v)==keys and v['schema']==ROW,'VERDICT_SCHEMA_INVALID')
        s=v['serial'];_require(type(s)==int and s in RULES,'VERDICT_SERIAL_UNKNOWN')
        atom=self.v198.review.atoms[s-1];cues=self.v198.review.cues
        _require(v['original_claim_sha256']==_sha(atom) and
                 v['v198_verdict_sha256']==_sha(self.v198_rows[s]) and
                 v['conclusion']==RULES[s][0] and v['parent_serial']==RULES[s][1],
                 'WRONG_ORIGINAL_OR_PREVIOUS_OR_CONCLUSION')
        _require(type(v['source_clauses'])==list and 1<=len(v['source_clauses'])<=3,
                 'ORIGINAL_CLAUSES_REQUIRED')
        src_indices=[]
        for clause in v['source_clauses']:
            _require(type(clause)==dict and set(clause)=={'cue_index','source_quote','source_paraphrase'},
                     'CLAUSE_SCHEMA_INVALID')
            i=clause['cue_index'];src_indices.append(i)
            _require(type(i)==int and abs(i-atom['cue_index'])<=5 and i in cues and
                    clause['source_quote']==cues[i] and
                    type(clause['source_paraphrase'])==str and len(clause['source_paraphrase'])>=12,
                    'FABRICATED_OR_NONLOCAL_CUE_QUOTE')
        _require(src_indices==sorted(set(src_indices)),'DUPLICATE_OR_DISORDERED_CUE_CLAUSES')
        _require(len(v['source_clauses'])>=2 if s in (28,112) else True,
                 'MUST_PRESERVE_BOTH_SPOKEN_PROPOSITIONS')
        _require(type(v['official_context_refs'])==list and
                 v['official_context_refs']==sorted(set(v['official_context_refs'])) and
                 1<=len(v['official_context_refs'])<=4 and
                 all(r in PUBLIC_WEB_CONTEXT for r in v['official_context_refs']),
                 'UNTRUSTED_OR_FORGED_FINANCIAL_SOURCE')
        _require(type(v['review_rationale'])==str and len(v['review_rationale'].strip())>=35 and
                 type(v['next_evidence_task'])==str and len(v['next_evidence_task'].strip())>=25,
                 'MISSING_EXPLANATION_OR_REMAINING_TASK')
        _require(all(v[k] is False for k in ('audio_verified','raw_issuer_bytes_verified',
                  'financial_fact_verified','independent_gold','e3_approved','e4_approved','e5_published')) and
                 all(v[k] is True for k in ('first_journal_unchanged','second_journal_unchanged',
                    'v198_journal_unchanged','risk_84_blocked','quarantines_28_preserved')),
                 'ILLEGAL_APPROVAL_OR_UNVERIFIED_EVIDENCE_PROMOTION')

    def submit(self,packet,verdicts):
        self._frozen();_require(type(packet)==dict and type(packet.get('serials'))==list,
                               'PACKET_INVALID')
        serials=packet['serials']
        _require(serials==sorted(set(serials)) and all(s in RULES for s in serials) and
                 packet==self._challenge(serials),'STALE_OR_FORGED_PACKET')
        _require(type(verdicts)==list and [v.get('serial') for v in verdicts]==serials,
                 'VERDICT_LIST_INCOMPLETE_OR_WRONG_ORDER')
        for v in verdicts:self._validate(v)
        with self._db() as con:
            head,rows,n=self._audit(con)
            _require(not any(s in rows for s in serials),'ALREADY_REVIEWED')
            ev={'schema':EVENT,'seq':n+1,'previous_sha':head,
                'source_sha256':self.config['source_sha256'],
                'v198_adjudication_head_sha256':self.expected_v198_head,
                'serials':serials,'decisions':verdicts,
                'e3_approved':False,'e4_approved':False,'e5_published':False}
            digest=_sha(ev)
            con.execute('INSERT INTO events VALUES(?,?,?,?)',
                        (n+1,head,digest,_canonical(ev).decode()))
            for v in verdicts:
                con.execute('INSERT INTO decisions VALUES(?,?,?)',
                           (v['serial'],_sha(v),_canonical(v).decode()))
        return self.status()

    def decisions(self):
        self._frozen()
        with self._db() as con:_,rows,_=self._audit(con)
        return rows

    def status(self):
        self._frozen()
        with self._db() as con:head,rows,n=self._audit(con)
        return {'schema':'IRE_V199_E3_REMAINING_SIX_SOURCE_VERDICT_HOLD_V1',
             'source_sha256':self.config['source_sha256'],
             'v198_adjudication_head_sha256':self.expected_v198_head,
             'v199_head_sha256':head,'events':n,
             'reviewed':len(rows),'remaining':6-len(rows),
             'outcomes':dict(Counter(v['conclusion'] for v in rows.values())),
             'audio_source_holds':len([s for s in rows if s in AUDIO_UNRESOLVED]),
             'parent_source_provisional':len([s for s in rows if s in PARENT_ISSUES]),
             'all_original_candidates_preserved':120,
             'high_risk_84_blocked':True,'quarantines_28_preserved':True,
             'issuer_raw_bytes_certified':False,'financial_truth_verified':False,
             'gold_precision':None,'gold_recall':None,
             'host_turn_ids_certified':False,
             'e3_approved':False,'e4_approved':False,'e5_published':False,
             'decision':'E3_HOLD_SIX_RESIDUAL_REVIEW_ONLY'}


def build_84_contextual_risk_view(v199:E3SixResidualVerdicts):
    """Attach useful issuer-specific WEB CONTEXT, never certify 84 claims."""
    z=v199.status();_require(z['remaining']==0,'SIX_REVIEWS_MUST_BE_COMPLETE')
    rows=v199.risks['risk_cases'];bycase=v199.decisions()
    context={
     'PRODUCT_PROVIDER_TERMS':['KOFIA_CMA_GUIDELINE','KIS_CMA_GUIDE','MERITZ_MMW_NOTICE'],
     'INVESTMENT_LOSS_OR_CREDIT_RISK':['KOFIA_CMA_GUIDELINE','MERITZ_MMW_NOTICE'],
     'RATE_COMPARISON_OR_UNASSESSED_SWITCH':['KOFIA_CMA_GUIDELINE','KIS_CMA_GUIDE'],
     'HISTORICAL_SCREEN_DATA':['KIS_CMA_GUIDE'],
     'SOURCE_SPOKEN_NOT_CURRENT_FACT':['KOFIA_CMA_GUIDELINE'],
     'PERSONAL_APPLICABILITY':['KOFIA_CMA_GUIDELINE'],
    }
    result=[]
    for r in rows:
        _require(r['financial_use_blocked'] is True,'RISK_STATUS_UNEXPECTEDLY_OPENED')
        s=r['serial'];
        references=sorted(context[r['risk_family']])
        # These pointers are topic leads, never individual investment evidence.
        result.append({'serial':s,'claim_sha256':r['claim_sha256'],
           'prior_risk_family':r['risk_family'],
           'web_text_source_candidates':references,
           'v199_source_review_conclusion':bycase[s]['conclusion'] if s in bycase else None,
           'claim_current_financial_truth_certified':False,
           'company_terms_verified':False,'effective_date_verified':False,
           'raw_official_document_bytes_sha256':None,
           'all_web_text_is_topic_context_only':True,
           'financial_use_blocked':True,'e3_approved':False,'e4_approved':False,'e5_published':False})
    _require(len(result)==84 and len(set(x['serial'] for x in result))==84,
             'RISK_84_CENSUS_CHANGED')
    return {'schema':VIEW,'source_sha256':z['source_sha256'],
       'v198_head_sha256':z['v198_adjudication_head_sha256'],
       'v199_head_sha256':z['v199_head_sha256'],
       'public_issuer_web_context':PUBLIC_WEB_CONTEXT,
       'web_text_is_not_authenticated_raw_issuer_source':True,
       'risk_records':result,'risk_count':84,'quarantines':28,
       'financial_truth_approved_count':0,'e3_approved':False,
       'e4_approved':False,'e5_published':False}

SPOT_CHECKS = (19,20,28,34,52,65,68,76,79,88,112,113)
SPOT_SCHEMA = 'IRE_V199_TWELVE_HIGHRISK_ISSUER_WEB_TEXT_SPOT_CHECKS_V1'
SPOT_FINDINGS = {'CONTRADICTS_UNQUALIFIED_SPEAKER_SAFETY_OR_RATE',
                 'ISSUER_SCOPE_EXCEPTION_FOUND',
                 'COMPANY_EXAMPLE_NEEDS_CLAIM_SCOPE',
                 'INSUFFICIENT_ISSUER_EVIDENCE'}

def validate_web_text_spot_checks(v199:E3SixResidualVerdicts,packet:dict):
    """Web-text-vs-speaker check is NOT issuer raw bytes or 84-claim gold.

    This blocks fabricated sources and missing examples, not semantic errors in
    a ChatGPT-written interpretation. A finance fact is never approved here.
    """
    v199._frozen()
    _require(type(packet)==dict and set(packet)=={'schema','source_sha256',
             'v199_head_sha256','cases','issuer_raw_sha256_certified','financial_truth_certified',
             'e3_approved','e4_approved','e5_published'},'SPOT_CHECK_SCHEMA')
    _require(packet['schema']==SPOT_SCHEMA and
             packet['source_sha256']==v199.config['source_sha256'] and
             packet['v199_head_sha256']==v199.status()['v199_head_sha256'] and
             all(packet[k] is False for k in ('issuer_raw_sha256_certified',
                 'financial_truth_certified','e3_approved','e4_approved','e5_published')),
             'SPOT_CHECK_SCOPE_OR_FALSE_CERTIFICATION')
    _require(type(packet['cases'])==list and
             [c.get('serial') for c in packet['cases']]==list(SPOT_CHECKS),
             'TWELVE_REAL_HIGH_RISK_SAMPLES_REQUIRED')
    risk_by_id={r['serial']:r for r in v199.risks['risk_cases']}
    for case in packet['cases']:
        req={'serial','claim_sha256','source_cue_index','source_quote',
             'web_text_refs','finding','analysis','issuer_scope_limit',
             'official_raw_bytes_sha256','product_terms_individually_verified',
             'financial_use_blocked','e3_approved','e4_approved','e5_published'}
        _require(type(case)==dict and set(case)==req,'SPOT_ROW_SCHEMA')
        s=case['serial'];atom=v199.v198.review.atoms[s-1]
        _require(s in risk_by_id and case['claim_sha256']==_sha(atom) and
                 case['claim_sha256']==risk_by_id[s]['claim_sha256'] and
                 case['source_cue_index']==atom['cue_index'] and
                 case['source_quote']==v199.v198.review.cues[atom['cue_index']],
                 'SPOT_QUOTE_OR_CLAIM_HASH_TAMPER')
        refs=case['web_text_refs']
        _require(type(refs)==list and 1<=len(refs)<=4 and
                 refs==sorted(set(refs)) and all(x in PUBLIC_WEB_CONTEXT for x in refs),
                 'SPOT_UNREGISTERED_ISSUER_SOURCE')
        _require(case['finding'] in SPOT_FINDINGS and
                 type(case['analysis'])==str and len(case['analysis'].strip())>=35 and
                 type(case['issuer_scope_limit'])==str and len(case['issuer_scope_limit'].strip())>=25,
                 'SPOT_SCOPE_OR_ANALYSIS_MISSING')
        _require(case['official_raw_bytes_sha256'] is None and
                 case['product_terms_individually_verified'] is False and
                 case['financial_use_blocked'] is True and
                 all(case[k] is False for k in ('e3_approved','e4_approved','e5_published')),
                 'SPOT_ILLEGAL_FINANCIAL_CERTIFICATION')
    return {'schema':'IRE_V199_HIGH_RISK_WEB_TEXT_SPOT_CHECK_VALIDATION_V1',
         'source_sha256':v199.config['source_sha256'],
         'v199_head_sha256':v199.status()['v199_head_sha256'],
         'sample_size':12,'total_original_high_risk':84,
         'risk_cases_not_covered_by_spot_check':72,
         'official_primary_text_context_checked':True,
         'issuer_raw_bytes_sha256_certified':False,
         'financial_truth_certified':False,
         'e3_approved':False,'e4_approved':False,'e5_published':False}