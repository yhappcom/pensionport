"""Source-pinned ChatGPT self-reference arithmetic, NEVER independent blind gold."""
from __future__ import annotations
import re
from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest, sha256
from .errors import InvalidInput
from .evaluation import CATEGORIES, HIGH_RISK, _ratio, _wilson95

REF_ID = re.compile(r"G[0-9]{5,8}\Z")

def score_chat_internal_reference(source, exchange, references, alignment):
    """Strict 1:1 accounting of self-authored labels. Never a research GO gate."""
    audit=audit_host_atomic_exchange(source,exchange)
    required={'schema','video_id','source_sha256','manifest_sha256','claims'}
    if (type(references) is not dict or set(references)!=required or
        references['schema']!='IRE_V6_CHAT_INTERNAL_REFERENCE_V1' or
        references['video_id']!=source.video_id or
        references['source_sha256']!=source.source_sha256 or
        references['manifest_sha256']!=source.manifest_sha256):
        raise InvalidInput('CHAT_REFERENCE_SOURCE_OR_SCHEMA_INVALID')
    claims=references['claims']
    if type(claims) is not list or not 1<=len(claims)<=2000:
        raise InvalidInput('CHAT_REFERENCE_CLAIMS_REQUIRED')
    allowed=set(range(source.scope_first_cue,source.scope_last_cue+1))
    ref={}
    for item in claims:
        if type(item) is not dict or set(item)!={'ref_id','category','proposition','cue_indices','cue_text_sha256'}:
            raise InvalidInput('CHAT_REFERENCE_ATOM_SCHEMA_INVALID')
        gid=item['ref_id']
        if (type(gid) is not str or not REF_ID.fullmatch(gid) or gid in ref or
            item['category'] not in CATEGORIES or type(item['proposition']) is not str or
            len(item['proposition'].strip())<5):
            raise InvalidInput('CHAT_REFERENCE_FRAME_INVALID')
        indices=item['cue_indices']
        if (type(indices) is not list or not 1<=len(indices)<=80 or
            any(type(i) is not int or i not in allowed for i in indices) or
            indices!=sorted(set(indices)) or
            item['cue_text_sha256'] != [sha256(source.cues[i-1].text.encode('utf-8')) for i in indices]):
            raise InvalidInput('CHAT_REFERENCE_ORIGINAL_CUE_PIN_DRIFT')
        ref[gid]=item
    if (type(alignment) is not dict or set(alignment)!={
        'schema','reference_sha256','candidate_sha256','exact_pairs','partial_pairs',
        'unmatched_reference_ids','all_claims_compared'} or
        alignment['schema']!='IRE_V6_CHAT_INTERNAL_ALIGNMENT_V1' or
        alignment['reference_sha256']!=json_digest(references) or
        alignment['candidate_sha256']!=audit['atom_candidate_digest'] or
        alignment['all_claims_compared'] is not True):
        raise InvalidInput('CHAT_REFERENCE_ALIGNMENT_NOT_PINNED')
    pred={item['claim_id'] for item in exchange['atoms']}
    seen_g=set();seen_p=set();exact=[]
    if type(alignment['exact_pairs']) is not list or type(alignment['partial_pairs']) is not list:
        raise InvalidInput('CHAT_REFERENCE_PAIR_LIST_INVALID')
    for item in alignment['exact_pairs']:
        if type(item) is not dict or set(item)!={'ref_id','claim_id'}:
            raise InvalidInput('CHAT_REFERENCE_EXACT_SHAPE_INVALID')
        gid,cid=item['ref_id'],item['claim_id']
        if gid not in ref or cid not in pred or gid in seen_g or cid in seen_p:
            raise InvalidInput('CHAT_REFERENCE_EXACT_DUPLICATE_OR_FOREIGN')
        seen_g.add(gid);seen_p.add(cid);exact.append((gid,cid))
    for item in alignment['partial_pairs']:
        if type(item) is not dict or set(item)!={'claim_id','ref_ids','reason'}:
            raise InvalidInput('CHAT_REFERENCE_PARTIAL_SHAPE_INVALID')
        cid,gids=item['claim_id'],item['ref_ids']
        if (cid not in pred or cid in seen_p or type(gids) is not list or
            not gids or gids!=sorted(set(gids)) or any(g not in ref or g in seen_g for g in gids) or
            type(item['reason']) is not str or len(item['reason'].strip())<5):
            raise InvalidInput('CHAT_REFERENCE_PARTIAL_INVALID')
        seen_p.add(cid);seen_g.update(gids)
    missing=alignment['unmatched_reference_ids']
    if (type(missing) is not list or missing!=sorted(set(missing)) or
        any(g not in ref or g in seen_g for g in missing)):
        raise InvalidInput('CHAT_REFERENCE_UNMATCHED_INVALID')
    seen_g.update(missing)
    if seen_g!=set(ref) or seen_p!=pred:
        raise InvalidInput('CHAT_REFERENCE_CLAIM_CENSUS_INCOMPLETE')
    tp=len(exact);pn=len(pred);gn=len(ref)
    high={gid for gid,x in ref.items() if x['category'] in HIGH_RISK}
    high_tp=sum(gid in high for gid,_ in exact)
    return {
        'schema':'IRE_V6_CHAT_INTERNAL_SCORE_V1','video_id':source.video_id,
        'source_sha256':source.source_sha256,
        'reference_sha256':json_digest(references),
        'candidates_sha256':audit['atom_candidate_digest'],
        'alignment_sha256':json_digest(alignment),
        'counts':{'tp':tp,'fp':pn-tp,'fn':gn-tp,'candidate_atoms':pn,
                  'self_reference_atoms':gn,'partial_pairs':len(alignment['partial_pairs']),
                  'high_risk_tp':high_tp,'high_risk_self_reference_atoms':len(high)},
        'precision':_ratio(tp,pn),'recall':_ratio(tp,gn),
        'high_risk_recall':_ratio(high_tp,len(high)),
        'precision_wilson_95':_wilson95(tp,pn),
        'recall_wilson_95':_wilson95(tp,gn),
        'high_risk_recall_wilson_95':_wilson95(high_tp,len(high)),
        'min_reference_50_reached':gn>=50,
        'min_high_risk_reference_30_reached':len(high)>=30,
        'reference_independence_verified':False,'human_adjudication_verified':False,
        'ground_truth_certified':False,'financial_truth_certified':False,
        'full_corpus_recall_certified':False,'p0_go':False,
        'status':'CHAT_ONLY_SELF_REFERENCE_DEVELOPMENT_SCORE_NOT_GOLD'}
