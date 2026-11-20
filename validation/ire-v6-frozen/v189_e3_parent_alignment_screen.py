"""V189 E3 parent alignment source-screen: a *candidate* is never semantic identity.

The V185 numeric/kind/context heuristic has documented false matches. This
source-pinned review requires ChatGPT to inspect both propositions and the
original near each cue. It cannot certify equivalence, E3 quality, or E4.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import _digest
from v185_e3_parent_qualifier_audit import analyze_source_journals

PACKET_SCHEMA='IRE_V189_E3_PARENT_CANDIDATE_SOURCE_SCREEN_V1'
ANSWER_SCHEMA='IRE_V189_E3_PARENT_IN_CHAT_SCREEN_RESPONSE_V1'
ASSESSMENTS={'PROVISIONAL_SAME_PARENT','OVERLAPPING_DISTINCT_FACTS',
             'MULTIPLE_CANDIDATES_UNRESOLVED','NO_CANDIDATE_UNRESOLVED'}
KEYS={'cue_index','assessment','source_quote','source_quote_cue_index',
      'pair_ref','semantic_rationale','semantic_equivalence_certified',
      'independent_gold_certified','e3_certified','e4_approved','e5_published'}
PAIR_KEYS={'first_anchor','second_anchor','first_claim_ordinal','second_claim_ordinal'}

def _need(ok,why):
    if not ok:raise InvalidInput('V189_PARENT_'+why)

def generate_packet(adjudication,*,max_cue_shift=8):
    second=adjudication.second
    engine=second.engine
    first=second._owner_snapshot()
    with second._db() as db:sh,reviewed=second._audit(db)
    with adjudication._db() as db:ah,entries=adjudication._audit(db)
    source=engine.source.cues
    _need(len(first)==len(reviewed)==len(source), 'SOURCE_CENSUS_NOT_FULL')
    diagnostic=analyze_source_journals(first,reviewed,source,
        pinned_first_head=second.expected_owner_head,pinned_second_head=sh,
        adjudications=entries,pinned_adjudication_head=ah,max_cue_shift=max_cue_shift)
    bycue=defaultdict(list)
    for item in diagnostic['possible_parent_links']:
        bycue[item['cue_index']].append(item)
    targets=sorted(i for i,(_,x) in entries.items()
                   if x['category']=='CLAIM_BOUNDARY_DISAGREEMENT')
    _need(len(targets)>0, 'NO_PARENT_CANDIDATES')
    cases=[]
    for i in targets:
        matches=[]
        for c in bycue[i]:
            fc=first[c['first_anchor']][1]['claims'][c['first_claim_ordinal']-1]
            sc=reviewed[c['second_anchor']][1]['claims'][c['second_claim_ordinal']-1]
            ref={k:c[k] for k in PAIR_KEYS}
            matches.append({'ref':ref,'first_claim_sha256':_digest(fc),
                            'second_claim_sha256':_digest(sc),
                            'first_proposition':fc['proposition'],
                            'second_proposition':sc['proposition'],
                            'first_context_indices':fc['context_cue_indices'],
                            'second_context_indices':sc['context_cue_indices'],
                            'first_numeric_tokens':fc['numeric_tokens'],
                            'second_numeric_tokens':sc['numeric_tokens']})
        cases.append({'cue_index':i,
                      'cue_text':source[i-1].text,
                      'source_text_sha256':sha256(source[i-1].text.encode()),
                      'candidate_pairs':matches,
                      'candidate_count':len(matches),
                      'heuristic_links_are_not_equivalence_proof':True})
    counts=Counter('UNMATCHED' if x['candidate_count']==0 else
                   'UNIQUE' if x['candidate_count']==1 else 'AMBIGUOUS' for x in cases)
    p={'schema':PACKET_SCHEMA,'source_sha256':engine.source.source_sha256,
       'first_head':second.expected_owner_head,'second_head':sh,
       'adjudication_head':ah,'max_cue_shift':max_cue_shift,
       'cases':cases,'source_quote_must_be_from_original':True,
       'independent_gold':False,'e3_certified':False,'e4_approved':False,'e5_published':False,
       'structural_triage_counts':dict(sorted(counts.items()))}
    return {**p,'packet_sha256':_digest(p)}

def validate_answer(packet,answer,source_cues):
    _need(type(packet) is dict and packet.get('packet_sha256')==_digest({k:v for k,v in packet.items() if k!='packet_sha256'}),'PACKET_SELF_HASH')
    _need(type(answer) is dict and set(answer)=={'schema','packet_sha256','review_executor','reviews'}
          and answer['schema']==ANSWER_SCHEMA and
          answer['packet_sha256']==packet['packet_sha256'] and
          answer['review_executor']=='CHATGPT_IN_CHAT' and
          type(answer['reviews']) is list and
          len(answer['reviews'])==len(packet['cases']),'ANSWER_COUNT_OR_PIN')
    results=Counter()
    for case,resp in zip(packet['cases'],answer['reviews']):
        _need(type(resp) is dict and set(resp)==KEYS and
              resp['cue_index']==case['cue_index'] and resp['assessment'] in ASSESSMENTS and
              all(resp[k] is False for k in ('semantic_equivalence_certified','independent_gold_certified',
                  'e3_certified','e4_approved','e5_published')) and
              type(resp['semantic_rationale']) is str and len(resp['semantic_rationale'].strip())>=65,
              'RESPONSE_SCHEMA_OR_AUTHORITY')
        i=case['cue_index']; q=resp['source_quote_cue_index']
        _need(type(q) is int and 1<=q<=len(source_cues) and abs(q-i)<=8 and
              type(resp['source_quote']) is str and len(resp['source_quote'].strip())>=3 and
              ' '.join(resp['source_quote'].split()) in ' '.join(source_cues[q-1].text.split()),
              'SOURCE_QUOTE_UNVERIFIED')
        pair=resp['pair_ref']
        if case['candidate_count']==0:
            _need(resp['assessment']=='NO_CANDIDATE_UNRESOLVED' and pair is None,
                  'NO_MATCH_CANNOT_PROVE_EQUIVALENCE')
        elif case['candidate_count']>1:
            _need(resp['assessment']=='MULTIPLE_CANDIDATES_UNRESOLVED' and pair is None,
                  'MULTIPLE_MATCH_NOT_RESOLVED')
        else:
            _need(resp['assessment'] in ('PROVISIONAL_SAME_PARENT','OVERLAPPING_DISTINCT_FACTS') and
                  type(pair) is dict and set(pair)==PAIR_KEYS and
                  pair==case['candidate_pairs'][0]['ref'],
                  'UNIQUE_MATCH_REFERENCE_INVALID')
        results[resp['assessment']]+=1
    return {'schema':'IRE_V189_E3_PARENT_SCREEN_STATUS_NO_GOLD_V1',
            'source_sha256':packet['source_sha256'],
            'first_head':packet['first_head'],'second_head':packet['second_head'],
            'adjudication_head':packet['adjudication_head'],
            'packet_sha256':packet['packet_sha256'],
            'review_count':len(answer['reviews']),
            'assessments':dict(sorted(results.items())),
            'source_pinned':True,'semantic_equivalence_certified':False,
            'independent_gold_certified':False,'e3_quality_certified':False,
            'e4_approved':False,'e5_published':False}

def validate_live(adjudication,packet,answer,*,max_cue_shift=8):
    """Only trust an engine-regenerated source-backed challenge, never self-hash alone."""
    regenerated=generate_packet(adjudication,max_cue_shift=max_cue_shift)
    _need(packet==regenerated,'STALE_OR_FORGED_REGENERATED_PACKET')
    result=validate_answer(packet,answer,adjudication.second.engine.source.cues)
    # Reread original and both reviewer journal heads after model adjudication.
    _need(generate_packet(adjudication,max_cue_shift=max_cue_shift)==regenerated,
          'JOURNAL_CHANGED_DURING_REVIEW')
    return result