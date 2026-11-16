"""V33 source-bound ChatGPT host finance-evidence / legacy116 comparison custody.

This checks hash, cue scope, official URL/retrieval date and master identity.
The ChatGPT host alone evaluates the semantics. Deterministic validation
CANNOT transform self-reviewed judgments into blind human-certified gold.
The public receipt excludes original SRT, reviewed statements and reasons.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlsplit
from .codec import json_digest,sha256
from .atomic_exchange import audit_host_atomic_exchange
from .errors import InvalidInput

_VERDICTS={
    'QUESTION_NOT_VERIFIED_FACT',
    'CURRENT_LAW_SCOPE_CORRECTION',
    'CURRENT_LAW_CONDITIONAL_EDUCATION',
    'HISTORICAL_ILLUSTRATION_ONLY',
    'INVESTMENT_BEHAVIOR_EDUCATION_ONLY',
    'FORECAST_OR_YIELD_NOT_GUARANTEED',
    'PRODUCT_OPERATION_REVIEW_OPEN',
    'ASR_UNCERTAINTY_REVIEW_OPEN',
}
_OFFICIAL={'law.go.kr','www.law.go.kr','nts.go.kr','www.nts.go.kr',
           'fsc.go.kr','www.fsc.go.kr','regulation.krx.co.kr',
           'nps.or.kr','www.nps.or.kr'}
_NEEDS_LEGAL={'CURRENT_LAW_SCOPE_CORRECTION','CURRENT_LAW_CONDITIONAL_EDUCATION'}
_RELATIONS={'NO_VERIFIED_PRIOR_MATCH','SUPPORTS_PRIOR_CHAT_REVIEW',
            'REFINES_PRIOR_CHAT_REVIEW','POSSIBLE_CONFLICT_REQUIRES_REVIEW'}


def audit_source_bound_chat_reviews_v33(sources, draft_exchanges, reviews,
                                         master_116, *,current_as_of):
    """Check actual V6 source-bound review rows, don't grade their meaning."""
    if (type(sources) is not dict or type(draft_exchanges) is not dict or
        set(sources)!=set(draft_exchanges) or type(reviews) is not list or
        not reviews or type(master_116) is not list or len(master_116)!=116):
        raise InvalidInput('V33_SOURCE_HOST_REVIEW_OR_MASTER_REQUIRED')
    try: asof=date.fromisoformat(current_as_of)
    except (TypeError,ValueError) as e:
        raise InvalidInput('V33_INVALID_CURRENT_ASOF') from e
    masters={row['claim_id']:row for row in master_116}
    if len(masters)!=116:
        raise InvalidInput('V33_MASTER116_ID_DUPLICATE')
    byvideo={}
    for vid,src in sources.items():
        audit_host_atomic_exchange(src,draft_exchanges[vid])
        byvideo[vid]={a['claim_id']:a for a in draft_exchanges[vid]['atoms']}
    seen=set();outputs=[]
    required={'review_id','video_id','source_cue_indices','source_cue_sha256',
              'draft_candidate_ids','reviewed_claim','review_reason',
              'speaker_role','meaning_verdict','risk_level',
              'official_evidence','knowledge_relation','reviewer','current_as_of'}
    for row in reviews:
        if type(row) is not dict or set(row)!=required:
            raise InvalidInput('V33_HOST_REVIEW_ROW_SCHEMA_INVALID')
        vid=row['video_id'];rid=row['review_id']
        if (vid not in sources or type(rid) is not str or not rid or
            (vid,rid) in seen):
            raise InvalidInput('V33_HOST_REVIEW_DUPLICATE_OR_FOREIGN_ID')
        seen.add((vid,rid));src=sources[vid];ex=draft_exchanges[vid]
        cited=row['source_cue_indices']
        if (type(cited) is not list or not cited or len(cited)>80 or
            cited!=sorted(set(cited)) or any(type(i) is not int or not 1<=i<=len(src.cues) for i in cited)):
            raise InvalidInput('V33_REVIEW_SOURCE_CUE_INDICES_INVALID')
        grounded=[sha256(src.cues[i-1].text.encode('utf-8')) for i in cited]
        if row['source_cue_sha256']!=grounded:
            raise InvalidInput('V33_REVIEW_ORIGINAL_CUE_SHA_TAMPER')
        expected=sorted({cid for d in ex['cue_dispositions'] if d['cue_index'] in cited for cid in d['claim_ids']})
        if row['draft_candidate_ids']!=expected or not expected:
            raise InvalidInput('V33_REVIEW_DRAFT_SOURCE_CANDIDATE_LINK_MISMATCH')
        if (type(row['reviewed_claim']) is not str or
            not 15<=len(row['reviewed_claim'].strip())<=1800 or
            type(row['review_reason']) is not str or
            not 35<=len(row['review_reason'].strip())<=2000 or
            row['speaker_role'] not in {'QUESTIONER','HOST_INTERPRETATION','UNRESOLVED'} or
            row['meaning_verdict'] not in _VERDICTS or
            row['risk_level'] not in {'HIGH','MEDIUM','LOW'} or
            row['reviewer']!='CHATGPT_CURRENT_TURN' or row['current_as_of']!=current_as_of):
            raise InvalidInput('V33_HOST_REVIEW_MEANING_METADATA_INVALID')
        evi=row['official_evidence']
        if type(evi) is not list or len(evi)>5:
            raise InvalidInput('V33_OFFICIAL_REVIEW_EVIDENCE_SHAPE_INVALID')
        if row['meaning_verdict'] in _NEEDS_LEGAL and not evi:
            raise InvalidInput('V33_CURRENT_LAW_REQUIRES_OFFICIAL_EVIDENCE')
        refrows=[]
        for source in evi:
            if type(source) is not dict or set(source)!={'source_url','retrieved_on','rule_effective_on','scope_note','document_sha256_authenticated'}:
                raise InvalidInput('V33_OFFICIAL_EVIDENCE_ROW_SCHEMA_INVALID')
            try:
                u=urlsplit(source['source_url']);rd=date.fromisoformat(source['retrieved_on'])
                effect=date.fromisoformat(source['rule_effective_on'])
            except (TypeError,ValueError) as exc:
                raise InvalidInput('V33_OFFICIAL_URL_OR_DATE_INVALID') from exc
            if (u.scheme!='https' or u.hostname not in _OFFICIAL or not u.path or
                rd>asof or effect>asof or
                type(source['scope_note']) is not str or len(source['scope_note'].strip())<20 or
                source['document_sha256_authenticated'] is not False):
                raise InvalidInput('V33_OFFICIAL_EVIDENCE_NOT_CURRENT_OR_AUTHENTICATED')
            refrows.append({'source_url_sha256':sha256(source['source_url'].encode()),
                            'effective_on':effect.isoformat(),
                            'retrieved_on':rd.isoformat(),
                            'scope_note_sha256':sha256(source['scope_note'].encode()),
                            'verified_original_publisher_fullbody':False})
        k=row['knowledge_relation']
        if type(k) is not dict or set(k)!={'relation','master_claim_id','master_claim_sha256','reason'}:
            raise InvalidInput('V33_MASTER_RELATION_SCHEMA_INVALID')
        if k['relation'] not in _RELATIONS or type(k['reason']) is not str or len(k['reason'].strip())<25:
            raise InvalidInput('V33_MASTER_RELATION_METADATA_INVALID')
        master_id=k['master_claim_id']
        if k['relation']=='NO_VERIFIED_PRIOR_MATCH':
            if master_id is not None or k['master_claim_sha256'] is not None:
                raise InvalidInput('V33_UNKNOWN_MASTER_RELATION_CANNOT_INCLUDE_ANCHOR')
        else:
            if master_id not in masters or k['master_claim_sha256']!=json_digest(masters[master_id]):
                raise InvalidInput('V33_MASTER116_ROW_HASH_MISMATCH')
        open_item=row['meaning_verdict'] in {'ASR_UNCERTAINTY_REVIEW_OPEN','PRODUCT_OPERATION_REVIEW_OPEN'} or k['relation']=='POSSIBLE_CONFLICT_REQUIRES_REVIEW'
        outputs.append({
            'review_id':rid,'video_id':vid,
            'source_cue_count':len(cited),
            'source_cue_reference_digest':json_digest([{'cue_index':i,'sha256':v} for i,v in zip(cited,grounded)]),
            'draft_candidate_ids':expected,
            'statement_sha256':sha256(row['reviewed_claim'].encode('utf-8')),
            'reason_sha256':sha256(row['review_reason'].encode('utf-8')),
            'speaker_role':row['speaker_role'],'risk_level':row['risk_level'],
            'meaning_verdict':row['meaning_verdict'],
            'official_evidence':refrows,
            'master_relation':k['relation'],
            'master_claim_id':master_id,
            'master116_row_hash':k['master_claim_sha256'],
            'master_relation_reason_sha256':sha256(k['reason'].encode('utf-8')),
            'review_open':open_item,
            'research_approved':False,
            'knowledge_auto_merge_approved':False,
        })
    result={'schema':'IRE_V6_V33_CHAT_HOST_REVIEW_HASH_ONLY_CUSTODY',
        'current_as_of':current_as_of,
        'source_video_count':len(sources),
        'host_review_claim_count':len(outputs),
        'host_open_items':sum(int(x['review_open']) for x in outputs),
        'host_source_verified_rows':len(outputs),
        'master_116_identity_reproduced':len(masters)==116,
        'reviewed_claims':outputs,
        'all_draft_utterances_chat_reviewed':False,
        'full_original_atomic_claim_recall_certified':False,
        'official_publisher_body_authenticated':False,
        'independent_gold_precision_recall_measured':False,
        'master116_or_p4_auto_merge':False,
        'personal_tax_trade_approval':False,
        'p0_go':False}
    result['receipt_sha256']=json_digest(result)
    return result
