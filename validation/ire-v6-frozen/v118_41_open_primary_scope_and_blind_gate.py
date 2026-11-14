"""V118 — strict secondary evidence triage and independent-gold *intake* scaffold.

Receives an owner-private V117 atom graph and original docket. Re-evaluates every
existing OPEN item against as-of-dated issuer-classed references, but never
approves source truth, legal applicability, an investment action or recall.

Only a separate assessor's unexposed original-only packet MAY later inform an
independent truth set. This code does not invoke an LLM or independent assessor.
"""
from __future__ import annotations
import hashlib, json, re
from datetime import date
from urllib.parse import urlsplit
from time import perf_counter_ns

class OpenEvidenceFailure(ValueError): pass

def _must(condition, code):
    if not condition: raise OpenEvidenceFailure('V118_'+code)

def sha(payload):
    if isinstance(payload,str):payload=payload.encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def digest(obj):
    return sha(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',',':'),allow_nan=False))

SHA_RE=re.compile(r'[0-9a-f]{64}\Z'); ATOM_RE=re.compile(r'A\d{3,6}\Z')
CLASSES={
 'GENERAL_SUPPORT_PENDING_LEGAL_FINAL',
 'COUNTEREVIDENCE_OR_OVERGENERALIZATION',
 'QUALIFICATION_REQUIRED',
 'HYPOTHETICAL_BRANCH_NOT_FACT',
 'PRODUCT_ACCOUNT_TAX_SCOPE_MISSING'
}
ISSUERS={
 'EXCHANGE_PRIMARY_WEB':('krx.co.kr',),
 'EXCHANGE_OLD_REVISION':('krx.co.kr',),
 'INDEPENDENT_RESEARCH_SECONDARY':('kcmi.re.kr',),
 'GOV_REGULATOR_PRIMARY_WEB':('fsc.go.kr',),
 'LEGISLATIVE_PRIMARY_WEB':('law.go.kr',),
 'EXCHANGE_PRODUCT_DISCLOSURE':('krx.co.kr',),
 'FISCAL_SECONDARY':('nabo.go.kr',),
 'ISSUER_PRODUCT_DISCLOSURE':('samsungfund.com',)
}
# Explicit validation avoids a website that calls itself 'official' or redirects to adware.
RETRIEVAL={
 'LIVE_PAGE_READ','INDEXED_CURRENT_CLAUSE','INDEXED_2026_CLAUSE',
 'INDEXED_2022_ONLY','DIRECT_INDEXED','INDEXED_PAGE',
 'INDEXED_PRODUCT_DOCUMENT','NO_PRODUCT_BINDING'
}
SAFE_FIELDS={
 'schema','video_id','as_of','v117_graph_sha256','v117_docket_sha256',
 'authority_register','rows','independent_gold','all_finance_facts_approved',
 'primary_full_http_body_sha_verified','formal_closed_items','pending_items',
 'personal_advice_authorized'
}
ROW_FIELDS={
 'atom_id','source_cue_indices','source_span_sha256','proposition_digest_sha256',
 'risk','review_class','authority_keys','reviewer_reason_private',
 'source_date_as_of','original_docket_status','primary_body_frozen_exact_bytes',
 'independent_source_adjudicated','current_rule_version_fully_verified',
 'financial_fact_approved','personal_application_approved','final_status'
}
REG_FIELDS={
 'id','url','issuer_class','retrieval','scope_summary','issuer_http_body_sha256',
 'legal_version_fully_verified','finance_approved','checked_as_of'
}
BLOCKED_IDS=frozenset({'A003','A012','A017','A021','A022','A028','A042','A044'})
# This is an *internal risk watch*, not a gold label or a fact-veracity certification.
CRITICAL_ATOM_OBLIGATIONS={
 'A003': 'VENUE_2025_STOCK_NOT_ETF',
 'A012': 'TRACKING_VS_PREMIUM_DISCOUNT',
 'A017': 'SIZE_BOTH_AMOUNTS_AND_HALF_YEAR',
 'A021': 'DELISTING_VS_CORPORATE_LIQUIDATION',
 'A022': 'ETF_BOND_ASSET_TYPE_EXCEPTION',
 'A028': 'SECONDARY_SALE_VS_REDEMPTION',
 'A042': 'SEPARATE_CUSTODY_NOT_LOSS_GUARANTEE',
 'A044': 'NON_DERIVATIVE_RISK_NOT_ZERO'
}

def _official_url(value,issuer):
    _must(type(value) is str and len(value)<=1400,'URL_LENGTH')
    try:v=urlsplit(value)
    except ValueError as exc:raise OpenEvidenceFailure('V118_URL_PARSE') from exc
    _must(v.scheme=='https' and v.username is None and v.password is None and
          v.port is None and v.hostname and not v.fragment,'URL_HTTPS')
    _must(any(v.hostname==host or v.hostname.endswith('.'+host)
              for host in ISSUERS[issuer]),'URL_NOT_ISSUER')
    return value

def audit_open_41(*,graph,original_docket,ledger,expected_date='2026-11-15'):
    t0=perf_counter_ns()
    _must(type(graph) is dict and type(original_docket) is list and type(ledger) is dict,'INPUT_TYPES')
    _must(set(ledger)==SAFE_FIELDS and ledger.get('schema')=='V118_PRIVATE_41_OPEN_ATOM_OFFICIAL_SCOPE_TRIAGE_V1','LEDGER_SCHEMA')
    _must(ledger.get('video_id')==graph.get('video_id')=='Yb_5prWaqhk','VIDEO_SCOPE')
    _must(ledger.get('as_of')==expected_date and date.fromisoformat(expected_date).isoformat()==expected_date,'AS_OF_DATE')
    _must(ledger.get('v117_graph_sha256')==digest(graph) and
          ledger.get('v117_docket_sha256')==digest(original_docket),'SOURCE_LEDGER_DIGEST')
    for k,expected in {'independent_gold':False,'all_finance_facts_approved':False,
                      'primary_full_http_body_sha_verified':False,
                      'formal_closed_items':0,'pending_items':41,
                      'personal_advice_authorized':False}.items():
        _must(type(ledger.get(k)) is type(expected) and ledger[k]==expected,'FALSE_GO_'+k)
    reference={}; attempted=set()
    for s in ledger['authority_register']:
        _must(type(s) is dict and set(s)==REG_FIELDS,'REGISTRY_FIELDS')
        key=s.get('id');cls=s.get('issuer_class')
        _must(type(key) is str and 3<=len(key)<=80 and key not in reference and cls in ISSUERS,'REGISTRY_DUPLICATE_OR_UNTRUSTED')
        _official_url(s['url'],cls)
        _must(s['retrieval'] in RETRIEVAL and s['checked_as_of']==expected_date and
              type(s['scope_summary']) is str and len(s['scope_summary'])>12,
              'REGISTRY_SOURCE_SCOPE')
        _must(s['issuer_http_body_sha256'] is None and s['legal_version_fully_verified'] is False and
              s['finance_approved'] is False,'UNPINNED_PRIMARY_FALSE_GO')
        if cls=='EXCHANGE_OLD_REVISION':
            _must(s['retrieval']=='INDEXED_2022_ONLY','OLD_KRX_MISCLASSIFIED_CURRENT')
        if cls=='FISCAL_SECONDARY' or cls=='ISSUER_PRODUCT_DISCLOSURE':
            _must(s['retrieval']=='NO_PRODUCT_BINDING','TAX_PERSONAL_FALSE_SCOPE')
        reference[key]=s
    _must(len(reference)>=8,'INSUFFICIENT_FAMILY_EVIDENCE')
    atom={x['atom_id']:x for x in graph.get('atoms',[])}
    finance_ids={a['atom_id'] for a in atom.values() if a.get('evidence_key')!='NONE'}
    docket={x['atom_id']:x for x in original_docket}
    _must(len(docket)==len(original_docket)==len(finance_ids)==41 and set(docket)==finance_ids,
          'V117_41_DOCKET_NOT_EXHAUSTIVE')
    _must(type(ledger.get('rows')) is list and len(ledger['rows'])==41,'REVIEW_41_CENSUS')
    modes={};url_links=0;_risk_high=0
    for a in ledger['rows']:
        _must(type(a) is dict and set(a)==ROW_FIELDS,'TRIAGE_ROW_FIELDS')
        aid=a.get('atom_id');_must(type(aid) is str and ATOM_RE.fullmatch(aid) and aid in finance_ids and aid not in attempted,'TRIAGE_DUPLICATE_OR_UNKNOWN_ATOM')
        attempted.add(aid)
        original=atom[aid];d=docket[aid]
        _must(a.get('source_cue_indices')==original['cue_indices']==d['cue_indices'] and
              a.get('source_span_sha256')==original['source_span_sha256'] and
              a.get('proposition_digest_sha256')==sha(original['proposition_private']) and
              a.get('risk')==original['risk'],'TRIAGE_SOURCE_SEMANTIC_REBIND')
        _must(a.get('source_date_as_of')==expected_date and
              a.get('original_docket_status')==d['evidence_status']==
              'OPEN_PRIMARY_BODY_AND_APPLICABILITY','ORIGINAL_OPEN_DRIFT')
        _must(a.get('review_class') in CLASSES and type(a.get('reviewer_reason_private')) is str and
              12<=len(a['reviewer_reason_private'])<=400,'TRIAGE_EXPLANATION_REQUIRED')
        _must(a.get('final_status')=='OPEN_NOT_FOR_PERSONAL_ADVICE' and
              all(a.get(k) is False for k in ('primary_body_frozen_exact_bytes',
                    'independent_source_adjudicated','current_rule_version_fully_verified',
                    'financial_fact_approved','personal_application_approved')),
              'UNSUPPORTED_FINANCE_APPROVAL')
        refs=a.get('authority_keys');_must(type(refs) is list and refs and len(refs)<=5 and
              len(refs)==len(set(refs)) and all(x in reference for x in refs),
              'ISSUER_KEY_MISSING')
        url_links+=len(refs)
        if aid in BLOCKED_IDS:
            _must(a['review_class']=='COUNTEREVIDENCE_OR_OVERGENERALIZATION',
                  'HIGH_RISK_COUNTEREVIDENCE_SILENCED')
        if aid=='A032':
            _must(a['review_class']=='PRODUCT_ACCOUNT_TAX_SCOPE_MISSING' and
                  {'NABO_TAX_POINTER','ISSUER_TAX_POINTER'}<=set(refs),'TAX_SCOPE_FABRICATED')
        if aid in ('A017','A018'):
            _must('KRX_CURRENT_ETF_LISTING' in refs,'KRX_50_BOTH_AND_HALFYEAR_LOST')
        if aid in ('A034','A035','A036','A042'):
            _must('LAW_246_2026_CURRENT' in refs,'CUSTODIAN_LAW_MISSING')
        if aid in ('A003','A004'):
            _must('FSC_NXT_2025' in refs,'ATS_STOCK_MARKET_SPLIT_MISSING')
        if aid=='A012':
            _must('KRX_PRICE_TRACK' in refs,'PRICE_GAP_VS_TRACKING_LOST')
        if aid=='A028':
            _must('KCMI_2026_RESEARCH' in refs,'REDEMPTION_VS_MARKET_SALE_LOST')
        if a['risk'] in ('HIGH','CRITICAL'):_risk_high+=1
        modes[a['review_class']]=modes.get(a['review_class'],0)+1
    _must(attempted==finance_ids,'OPEN_41_REVIEW_COVERAGE')
    return {'schema':'V118_PUBLIC_OPEN41_CUSTODY_TRIAGE_NO_INDEPENDENT_GOLD_V1',
       'video_id':graph['video_id'],'source_41_reviewed':41,
       'primary_body_byte_sha_verified':False,'formal_finance_approvals':0,
       'new_independent_gold':False,'precision':None,'recall':None,
       'financial_remaining_open':41,'high_risk_items_reviewed':_risk_high,
       'source_authorities':len(reference),'evidence_row_authority_links':url_links,
       'review_class_counts':modes,'v117_graph_sha256':digest(graph),
       'review_artifact_sha256':digest(ledger),'internal_assessment_only':True,
       'model_review_wall_ns':None,'structural_audit_wall_ns':perf_counter_ns()-t0,
       'ready_for_personal_advice':False,'p0_go':False}

def blind_packet(raw_srt,source_sha256,video_id):
    """Original-only cues for a separate assessor; never include V117 labels or claims."""
    _must(type(raw_srt) is bytes and sha(raw_srt)==source_sha256,'BLIND_SOURCE_PIN')
    # Source stays in owner's *private* archive; packet header has no V117 annotations.
    # Caller keeps bytes isolated. Return only non-semantic metadata for public receipt.
    # Parse SRT using same shared implementation as the V117 custody gate.
    from v115_full_video_bridge import parse_exact_srt
    cues=parse_exact_srt(raw_srt)
    _must(len(cues)==173 and video_id=='Yb_5prWaqhk','BLIND_VIDEO_CENSUS')
    return {'schema':'V118_SOURCE_ONLY_BLIND_PACKET_HEADER_V1',
            'video_id':video_id,'source_srt_sha256':source_sha256,
            'cue_count':173,'window_ranges':[[i,min(i+39,173)] for i in range(1,174,40)],
            'previous_model_annotations_included':False,
            'previous_risk_scores_included':False,
            'gold_labels_included':False,'independent_assessor_received':False,
            'independent_adjudicated':False}

def compare_against_synthetic_gold(*,gold,predicted):
    """Sanity-check scorer arithmetic ONLY; cannot certify independent provenance."""
    _must(all(type(x) is set for x in (gold,predicted)) and len(gold)>0,'SCORE_SET_REQUIRED')
    tp=len(gold&predicted);fp=len(predicted-gold);fn=len(gold-predicted)
    return {'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,
            'recall':tp/(tp+fn)}
