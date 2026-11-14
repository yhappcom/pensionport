"""V22: compare pinned OLD VIDEO atoms against CURRENT effective law.

For investment-advice use, as_of is the response's current Korean calendar date,
NOT the original upload date. Historic validity remains in the V21 archive.
No browser/model API or implicit legal interpretation: present official evidence
and get a current-ChatGPT source-grounded scope judgment. Unreviewed atoms wait.
Neither a host judgment nor a site URL proves publisher authenticity, individual
eligibility, investment suitability or independently labeled semantic truth.
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlsplit

from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest, sha256
from .errors import InvalidInput
from .temporal_finance_gate import _day

_ALLOWED_DOMAINS = frozenset({
    'law.go.kr','www.law.go.kr','nts.go.kr','www.nts.go.kr',
    'taxlaw.nts.go.kr','www.moel.go.kr','moel.go.kr',
    'regulation.krx.co.kr','www.krx.co.kr','krx.co.kr',
    'www.fsc.go.kr','fsc.go.kr','www.nps.or.kr','nps.or.kr',
})
_RULE = re.compile(r'[A-Z0-9_:-]{6,100}\Z')
_REGULATED_FACT = re.compile(r'(?=.*(?:IRP|연금저축|ETF|증여|세액공제|국민연금))(?=.*(?:세금|과세|공제|인출|중도|매매수익|매매차익|세율|납입한도))', re.I)
_CLASSES = frozenset({
    'CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL',
    'CURRENT_RULE_SCOPE_MISSING',
    'CURRENT_RULE_CONTRADICTS_SOURCE',
    'CURRENT_FACT_OR_APPLICABILITY_UNKNOWN',
    'NOT_A_REGULATORY_CLAIM',
})


def _official_url(value):
    if not isinstance(value,str) or len(value)>1500:
        raise InvalidInput('CURRENT_LAW_URL_INVALID')
    u=urlsplit(value)
    if (u.scheme!='https' or u.hostname not in _ALLOWED_DOMAINS or
        u.username is not None or u.password is not None or u.port is not None or
        not u.path or u.fragment or len(value)>1500):
        raise InvalidInput('CURRENT_LAW_NOT_ALLOWLISTED_PRIMARY_URL')
    return value


def _rules(as_of, evidence):
    if type(evidence) is not list or not 1<=len(evidence)<=35:
        raise InvalidInput('CURRENT_LAW_EVIDENCE_LIST_REQUIRED')
    found={}
    for row in evidence:
        keys={'rule_id','source_url','effective_from','effective_to',
              'retrieved_on','excerpt','excerpt_sha256','document_body_sha256',
              'scope_note'}
        if type(row) is not dict or set(row)!=keys:
            raise InvalidInput('CURRENT_LAW_EVIDENCE_SCHEMA_INVALID')
        rid=row['rule_id']
        if type(rid) is not str or not _RULE.fullmatch(rid) or rid in found:
            raise InvalidInput('CURRENT_LAW_RULE_ID_DUPLICATE_OR_INVALID')
        url=_official_url(row['source_url'])
        start=_day(row['effective_from'],'CURRENT_LAW_START')
        end=_day(row['effective_to'],'CURRENT_LAW_END') if row['effective_to'] is not None else None
        retrieved=_day(row['retrieved_on'],'CURRENT_LAW_RETRIEVAL')
        if (end is not None and end<=start) or retrieved>as_of:
            raise InvalidInput('CURRENT_LAW_VERSION_OR_RETRIEVAL_INVALID')
        excerpt=row['excerpt']
        if type(excerpt) is not str or not 20<=len(excerpt)<=5000:
            raise InvalidInput('CURRENT_LAW_EXCERPT_INVALID')
        if row['excerpt_sha256']!=sha256(excerpt.encode('utf-8')):
            raise InvalidInput('CURRENT_LAW_EXCERPT_SHA_MISMATCH')
        document_sha=row['document_body_sha256']
        if document_sha is not None and (type(document_sha) is not str or not re.fullmatch(r'[a-f0-9]{64}',document_sha)):
            raise InvalidInput('CURRENT_LAW_DOCUMENT_HASH_FORMAT_INVALID')
        note=row['scope_note']
        if type(note) is not str or not 15<=len(note)<=600:
            raise InvalidInput('CURRENT_LAW_SCOPE_REQUIRED')
        # A dated legal amendment is not necessarily effective as of today.
        if as_of<start:
            status='FUTURE_NOT_CURRENT'
        elif end is not None and as_of>=end:
            status='EXPIRED_NOT_CURRENT'
        elif (as_of-retrieved).days>30:
            status='STALE_CURRENT_RECHECK_REQUIRED'
        else:
            status='EFFECTIVE_ON_CURRENT_ASOF_CHAT_PRIMARY_EXCERPT_ONLY'
        found[rid]={'url':url,'status':status,'effective_from':start.isoformat(),
                    'effective_to':end.isoformat() if end else None,
                    'retrieved_on':retrieved.isoformat(),
                    'excerpt_sha256':row['excerpt_sha256'],
                    'document_body_sha256':document_sha,
                    'primary_body_externally_authenticated':False,
                    'source_scope_sha256':sha256(note.encode('utf-8'))}
    return found


def audit_current_law_reassessment(source, exchange, *, current_as_of,
                                   primary_evidence, chat_decisions):
    """Pure host gate; date-valid law compares against TODAY, not video date.

    Every candidate atom gets either a documented chat judgment or an OPEN
    review queue entry. A semantic judgment cannot be inferred from a URL/hash.
    The public return value has no source transcript or legal excerpt text.
    """
    audit=audit_host_atomic_exchange(source,exchange)
    as_of=_day(current_as_of,'CURRENT_ADVISORY_ASOF')
    rules=_rules(as_of,primary_evidence)
    if type(chat_decisions) is not list or len(chat_decisions)>len(exchange['atoms']):
        raise InvalidInput('CURRENT_CHAT_DECISIONS_INVALID')
    atoms={a['claim_id']:a for a in exchange['atoms']}
    rows={}
    for d in chat_decisions:
        required={'claim_id','proposition_sha256','classification','rule_ids','reason',
                  'missing_conditions','reviewer','reviewed_as_of'}
        if type(d) is not dict or set(d)!=required:
            raise InvalidInput('CURRENT_CHAT_DECISION_SCHEMA_INVALID')
        cid=d['claim_id']
        if type(cid) is not str or cid not in atoms or cid in rows:
            raise InvalidInput('CURRENT_CHAT_CLAIM_UNKNOWN_OR_DUPLICATE')
        proposition_sha=sha256(atoms[cid]['proposition'].encode('utf-8'))
        if d['proposition_sha256']!=proposition_sha:
            raise InvalidInput('CURRENT_CHAT_SOURCE_PROPOSITION_DRIFT')
        if d['reviewer']!='CHATGPT_CURRENT_TURN' or d['reviewed_as_of']!=as_of.isoformat():
            raise InvalidInput('CURRENT_CHAT_REVIEWER_DATE_INVALID')
        cls=d['classification']
        if cls not in _CLASSES or type(cls) is not str:
            raise InvalidInput('CURRENT_CHAT_CLASS_INVALID')
        rids=d['rule_ids']
        if (type(rids) is not list or len(rids)>15 or rids!=sorted(set(rids)) or
            any(type(r) is not str or r not in rules for r in rids)):
            raise InvalidInput('CURRENT_CHAT_REFERENCE_LIST_INVALID')
        reason=d['reason']
        if type(reason) is not str or not 20<=len(reason)<=900:
            raise InvalidInput('CURRENT_CHAT_REASON_REQUIRED')
        missing=d['missing_conditions']
        if (type(missing) is not list or len(missing)>20 or
            any(type(x) is not str or not 2<=len(x)<=160 for x in missing) or
            missing!=sorted(set(missing))):
            raise InvalidInput('CURRENT_CHAT_CONDITIONS_INVALID')
        if cls=='NOT_A_REGULATORY_CLAIM':
            if rids or missing:
                raise InvalidInput('CURRENT_CHAT_NONREGULATORY_HARD_BLOCK')
            if (atoms[cid]['kind'] in ('FACT','RECOMMENDATION') and
                    _REGULATED_FACT.search(atoms[cid]['proposition'])):
                # Defend against a model relabeling an explicit statutory claim
                # as generic advice to escape the current-law review gate.
                raise InvalidInput('CURRENT_CHAT_LEGAL_FACT_FALSE_NONREGULATORY')
        elif not rids:
            # Still permissible to mark unresolved without a rule, never to assert a regulatory finding.
            if cls!='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN':
                raise InvalidInput('CURRENT_CHAT_REGULATORY_JUDGMENT_NO_RULE')
        if cls=='CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL' and not missing:
            raise InvalidInput('CURRENT_CHAT_UNCONDITIONAL_LEGAL_APPROVAL_FORBIDDEN')
        referenced_states=[rules[r]['status'] for r in rids]
        # Never use a future/expired/stale rule as a CURRENT decision predicate.
        if cls not in ('NOT_A_REGULATORY_CLAIM','CURRENT_FACT_OR_APPLICABILITY_UNKNOWN') and any(s!='EFFECTIVE_ON_CURRENT_ASOF_CHAT_PRIMARY_EXCERPT_ONLY' for s in referenced_states):
            raise InvalidInput('CURRENT_CHAT_REFERENCED_RULE_NOT_CURRENT')
        # With a stale/out-of-window evidence mark the judgment OPEN, not effective.
        if cls=='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN':
            status='OPEN_CHAT_OR_SOURCE_APPLICABILITY' 
        elif cls=='NOT_A_REGULATORY_CLAIM':
            status='NOT_REGULATORY'
        else:
            status='CHAT_REVIEWED_CURRENT_RULE_CONDITIONAL_NOT_CERTIFIED'
        rows[cid]={'claim_id':cid,'proposition_sha256':proposition_sha,
                   'classification':cls,'rule_ids':rids,
                   'reason_sha256':sha256(reason.encode('utf-8')),
                   'missing_conditions_count':len(missing),'status':status,
                   'claim_cue_hashes':[sha256(source.cues[r['cue_index']-1].text.encode('utf-8'))
                                      for r in atoms[cid]['source_refs']]}
    for cid,a in atoms.items():
        if cid not in rows:
            rows[cid]={'claim_id':cid,
                       'proposition_sha256':sha256(a['proposition'].encode('utf-8')),
                       'classification':'CURRENT_FACT_OR_APPLICABILITY_UNKNOWN',
                       'rule_ids':[],'reason_sha256':None,'missing_conditions_count':0,
                       'status':'CHATGPT_REVIEW_REQUIRED',
                       'claim_cue_hashes':[sha256(source.cues[r['cue_index']-1].text.encode('utf-8'))
                                          for r in a['source_refs']]}
    results=[rows[c] for c in sorted(rows)]
    flags=[r for r in results if r['status']=='CHATGPT_REVIEW_REQUIRED']
    return {
       'schema':'IRE_V6_CURRENT_LAW_REASSESSMENT_V22',
       'mode':'CURRENT_ADVISORY_ASOF_NOT_HISTORICAL_SPEECH',
       'current_as_of':as_of.isoformat(),
       'video_id':source.video_id,'source_sha256':source.source_sha256,
       'exchange_candidate_digest':audit['atom_candidate_digest'],
       'official_references':rules,
       'claim_review':results,
       'count_claims':len(results),'chat_reviewed_claims':len(chat_decisions),
       'open_chat_review_claims':len(flags),
       'outstanding_claim_ids':[r['claim_id'] for r in flags],
       'review_sha256':json_digest(results),
       'video_publication_date_not_used_as_current_law_gate':True,
       'same_chat_reference_is_not_independent_gold':True,
       'official_primary_bytes_identity_not_independently_verified':True,
       'general_rule_chat_comparison_only':True,
       'individual_tax_or_pension_application_approved':False,
       'independent_semantic_precision_recall_measured':False,
       'approved_advisory_knowledge':False,
       'p0_go':False,
    }


def prepare_private_current_law_chat_packet(source, exchange, *, current_as_of,
                                            primary_evidence, max_claims=25):
    """Private in-chat fallback when deterministic engine cannot decide meaning.

    Return raw excerpts/source claims ONLY to authorized chat execution, never
    to GitHub, issue comments, public logs, or an unrelated retrieval service.
    """
    audit_host_atomic_exchange(source,exchange)
    as_of=_day(current_as_of,'CURRENT_ADVISORY_ASOF')
    rules=_rules(as_of,primary_evidence)
    if type(max_claims) is not int or not 1<=max_claims<=50:
        raise InvalidInput('CURRENT_CHAT_PACKET_LIMIT_INVALID')
    subset=exchange['atoms'][:max_claims]
    return {'schema':'IRE_V6_PRIVATE_CURRENT_LAW_CHAT_PACKET_V22',
            'instruction':'Compare these historical video claims with the rules currently effective on current_as_of; do NOT assume filming date is the legal as-of. Cite source evidence, dates and exceptions. Uncertain -> OPEN. Never claim independent gold.',
            'current_as_of':as_of.isoformat(),
            'video_id':source.video_id,
            'original_claims':[{'claim_id':a['claim_id'],'proposition':a['proposition'],
                                'stance':a['stance'],'original_cues':[{'cue_index':r['cue_index'],
                                'quote':r['quote']} for r in a['source_refs']]}
                               for a in subset],
            'official_law_evidence':[{'rule_id':e['rule_id'],'url':e['source_url'],
                                      'effective_from':e['effective_from'],
                                      'effective_to':e['effective_to'],
                                      'current_time_status':rules[e['rule_id']]['status'],
                                      'excerpt':e['excerpt'],'scope_note':e['scope_note']}
                                     for e in primary_evidence],
            'remaining_claim_count':len(exchange['atoms'])-len(subset),
            'private_not_for_public_storage':True,
            'independent_gold':False,'p0_go':False}
