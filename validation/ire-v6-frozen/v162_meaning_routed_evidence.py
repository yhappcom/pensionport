"""V162 one-video evidence routing with explicit ChatGPT source-first decisions.

No LLM API. No change to historical V123. A route is not a source fact,
financial advice, original HTTP bytes, or a research release authorization.
"""
from __future__ import annotations
from datetime import date
from urllib.parse import urlsplit
import re

from ire.v6.codec import json_digest, sha256, require_hash
from ire.v6.errors import InvalidInput

SCHEMA="IRE_V162_CHATGPT_SOURCE_FIRST_EVIDENCE_ROUTING_REVIEW_V1"
RESULT_SCHEMA="IRE_V162_CORRECTED_FINANCE_ROUTER_HOLD_V1"
CATEGORIES=frozenset({
 "SOURCE_AUDIO_RECHECK", "CURRENT_LAW_EFFECTIVE_SCOPE",
 "CORPORATE_ISSUER_FACT", "BOOK_OR_HISTORICAL_SOURCE",
 "NUMERIC_ASSUMPTION_OR_EXTERNAL_FACT", "PERSONAL_RECOLLECTION",
 "GENERAL_INVESTMENT_MEANING"})
DISCOURSE={
 "HYPOTHETICAL_NUMERIC":"NUMERIC_ASSUMPTION_OR_EXTERNAL_FACT",
 "HISTORICAL_FX_ANECDOTE":"BOOK_OR_HISTORICAL_SOURCE",
 "BOOK_BIBLIOGRAPHIC_FACT":"BOOK_OR_HISTORICAL_SOURCE",
 "COMPANY_HISTORICAL_FACT":"CORPORATE_ISSUER_FACT",
 "REAL_CURRENT_LAW_CLAIM":"CURRENT_LAW_EFFECTIVE_SCOPE",
}
CUE_SUSPECT=frozenset({307,390,522,622,717,797,849,850,852,943,947,965,1221})
DATE = re.compile(r'^\d{4}-\d\d-\d\d$')


def _need(ok, reason):
    if not ok: raise InvalidInput('V162_'+reason)


def _cue_pin(source, indices):
    return json_digest([{'cue_index':i,
                         'cue_text_sha256':sha256(source.cues[i-1].text.encode('utf-8'))}
                        for i in indices])


def adjudicate_finance_ticket(source, atom, old_verdict, prior_ticket, chat_semantic_review=None):
    """Source-pin old V161 ticket, then apply only independently described
    original-cue-checked ChatGPT semantic decision. Other rows stay UNCHANGED.
    """
    cid=atom['claim_id']
    indices=sorted(set(atom['context_cue_indices']))
    _need(indices and all(type(i) is int and
                          source.scope_first_cue<=i<=source.scope_last_cue for i in indices),
          'SOURCE_CUE_SCOPE')
    cue_hash=_cue_pin(source,indices)
    _need(prior_ticket['claim_id']==cid and old_verdict['claim_id']==cid and
          prior_ticket['atom_sha256']==old_verdict['atom_sha256']==json_digest(atom),
          'ATOM_SOURCE_OR_PRIOR_TICKET_DRIFT')
    _need(prior_ticket['original_source_sha256']==source.source_sha256 and
          prior_ticket['manifest_sha256']==source.manifest_sha256 and
          prior_ticket['source_context_sha256']==cue_hash, 'SOURCE_CONTEXT_PIN_DRIFT')
    _need(old_verdict['status']=='OPEN' and old_verdict['financial_claim'] is True and
          prior_ticket['original_verdict_remains']=='OPEN' and
          prior_ticket['finance_evidence_approved'] is False,
          'ONLY_FINANCE_OPEN_MAY_BE_ROUTED')
    previous=prior_ticket['evidence_work_queue']
    _need(previous in CATEGORIES,'PRIOR_ROUTE_SCHEMA')
    if not chat_semantic_review:
        out=dict(prior_ticket)
        out.update(schema=RESULT_SCHEMA,review_status='NOT_REVIEWED_RETAINED_V161',
                   prior_evidence_work_queue=previous,route_changed=False,
                   source_first_chat_adjudicated=False,
                   evidence_body_bytes_authenticated=False,
                   primary_source_claim_matched=False,
                   research_candidate_approved=False,
                   v123_final_release_allowed=False,
                   v128_publish_allowed=False)
        return out
    r=chat_semantic_review
    required={'schema','claim_id','atom_sha256','original_source_sha256',
              'source_context_sha256','source_cue_indices','old_evidence_work_queue',
              'discourse_type','new_evidence_work_queue','review_executor',
              'review_as_of','private_review_note_sha256','evidence_limitations',
              'financial_fact_approved','personal_advice_approved',
              'primary_body_bytes_authenticated','p0_go'}
    _need(type(r) is dict and set(r)==required and r['schema']==SCHEMA,
          'EXACT_SOURCE_FIRST_REVIEW_SCHEMA')
    _need(r['claim_id']==cid and r['atom_sha256']==json_digest(atom) and
          r['original_source_sha256']==source.source_sha256 and
          r['source_context_sha256']==cue_hash and
          r['source_cue_indices']==indices and r['old_evidence_work_queue']==previous,
          'CHAT_REVIEW_PIN_DRIFT')
    _need(r['review_executor']=='CHATGPT_IN_CHAT' and
          type(r['review_as_of']) is str and DATE.fullmatch(r['review_as_of']) and
          date.fromisoformat(r['review_as_of']) <= date.today(),
          'REVIEW_DATE_OR_EXECUTOR')
    require_hash(r['private_review_note_sha256'],'V162_REVIEW_NOTE')
    _need(type(r['evidence_limitations']) is str and len(r['evidence_limitations'])>=30,
          'LIMITATION_MUST_BE_SPECIFIC')
    _need(all(r[k] is False for k in ('financial_fact_approved','personal_advice_approved',
                                     'primary_body_bytes_authenticated','p0_go')),
          'FALSE_FINANCIAL_OR_PERSONAL_APPROVAL')
    discourse=r['discourse_type']
    _need(discourse in DISCOURSE and
          r['new_evidence_work_queue']==DISCOURSE[discourse],
          'CLAIM_KIND_ROUTING_INCONSISTENT')
    raw=' '.join(source.cues[i-1].text for i in indices)
    if discourse=='HYPOTHETICAL_NUMERIC':
        _need(atom['kind']=='HYPOTHETICAL' and
              bool(atom['numeric_references'] or re.search(r'\d|금리|수익률|배당',raw)),
              'NUMERIC_HYPOTHETICAL_NOT_SUPPORTED_BY_SOURCE')
    elif discourse=='HISTORICAL_FX_ANECDOTE':
        _need(atom['kind'] in {'OPINION','FACT'} and
              bool(re.search(r'옛날|당시|예전|회상',raw)) and
              bool(re.search(r'환|터키|튀르키|명품|관광',raw)),
              'ANECDOTE_NOT_PRESENT_IN_SOURCE')
    elif discourse=='REAL_CURRENT_LAW_CLAIM':
        _need(atom['kind']=='FACT' and
              bool(re.search(r'과세|세율|세금|공제|비과세|금융소득|세법',raw)) and
              not re.search(r'가정|없다고 치고|만약|예를 들면',raw),
              'LAW_IS_NOT_AN_ATTESTED_CURRENT_LEGAL_FACT')
    elif discourse=='COMPANY_HISTORICAL_FACT':
        _need(atom['kind']=='FACT' and
              bool(re.search(r'삼성|하이닉스|기업|인텔|반도체',raw)),
              'COMPANY_FACT_NOT_ATTESTED_AS_FACT')
    elif discourse=='BOOK_BIBLIOGRAPHIC_FACT':
        _need(atom['kind'] in {'FACT','OPINION'} and
              bool(re.search(r'책|저자|단도|파브라이|목차|책제목|버핏',raw)),
              'BOOK_SOURCE_NOT_PRESENT')
    # Always preserve a warning when historical audio is unconfirmed.
    disputed=sorted(CUE_SUSPECT.intersection(indices))
    _need(not disputed, 'SUSPECT_AUDIO_CANNOT_BE_CLEARED_BY_ROUTER')
    out=dict(prior_ticket)
    out.update(schema=RESULT_SCHEMA,review_status='CHATGPT_SOURCE_FIRST_EVIDENCE_ROUTE_ONLY',
               prior_evidence_work_queue=previous,
               evidence_work_queue=r['new_evidence_work_queue'],
               discourse_type=discourse,
               route_changed=(previous!=r['new_evidence_work_queue']),
               chat_review_note_sha256=r['private_review_note_sha256'],
               source_first_chat_adjudicated=True,
               evidence_body_bytes_authenticated=False,
               primary_source_claim_matched=False,
               research_candidate_approved=False,
               v123_final_release_allowed=False,
               v128_publish_allowed=False)
    return out


def audit_evidence_page_match(source, atom, *, original_finance_open_row, match):
    """Record a checked web-page *text* support, NOT issuer raw bytes.

    Do not pretend publisher book bibliography validates profits or advice.
    """
    _need(original_finance_open_row['status']=='OPEN' and
          original_finance_open_row['financial_claim'] is True,
          'PAGE_MATCH_NEVER_APPROVES_NONOPEN_OR_NONFINANCE')
    ids=sorted(set(atom['context_cue_indices']))
    _need(match['claim_id']==atom['claim_id'] and
          match['atom_sha256']==json_digest(atom) and
          match['source_sha256']==source.source_sha256 and
          match['source_context_sha256']==_cue_pin(source,ids),
          'PAGE_MATCH_ATOM_CONTEXT_DRIFT')
    _need(match['review_executor']=='CHATGPT_IN_CHAT' and
          match['match_scope'] in {'BIBLIOGRAPHIC_ONLY','BOOK_TABLE_OF_CONTENTS_ONLY',
                                   'ISSUER_2017_HISTORICAL_RESULT_ONLY'},
          'PAGE_MATCH_SCOPE_INVALID')
    try:
        parsed=urlsplit(match['source_url'])
        hostname=parsed.hostname or ''
    except (TypeError, ValueError):
        hostname='';parsed=None
    _need(parsed is not None and parsed.scheme=='https' and
          parsed.username is None and parsed.password is None and
          hostname in {'www.wiley-vch.de','news.skhynix.com'} and
          parsed.port in {None,443} and not parsed.fragment,
          'OFFICIAL_HTTPS_ORIGIN_EXACT_HOST_REQUIRED')
    _need(type(match['support_description']) is str and len(match['support_description'])>=20,
          'EVIDENCE_NOT_DESCRIBED')
    _need(match['original_http_response_bytes_sha256'] is None and
          match['original_http_response_bytes_archived'] is False and
          match['v123_official_body_verified'] is False and
          match['finance_fact_approved'] is False and
          match['v123_final_approval'] is False and
          match['knowledge_publish_allowed'] is False,
          'WEB_CONTENT_NOT_ORIGINAL_BODY_OR_FINANCE_CERTIFICATE')
    _need((match['match_scope'] == 'ISSUER_2017_HISTORICAL_RESULT_ONLY') ==
          (hostname=='news.skhynix.com'),
          'ISSUER_MATCH_SCOPE_WRONG')
    return {'claim_id':atom['claim_id'],
            'page_evidence_attached':True,'match_scope':match['match_scope'],
            'v123_approved':False,'v128_approved':False,'source_page_url':match['source_url']}
