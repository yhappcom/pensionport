"""Shared prospective authoring contract. Explicit reviewer judgments, not NLP.

Derives the V2 graph from typed decisions, checks source-wide disposition and
numeric occurrence custody, and preserves richer meanings in a pinned receipt.
Old graph packets and scores are never rewritten.
"""
from copy import deepcopy
import re
from .codec import json_digest
from .errors import InvalidInput
from .semantic_source_graph import (BOUNDARY_PACKET, source_grid, compile_graph,
    numeric_token_ranges, numeric_binding, _span, _spans, _contained, _text, _note, _rows_digest)

ROLE_MAP = {'AMOUNT':'AMOUNT','CONTRIBUTION_BASE':'AMOUNT','TAX_AMOUNT':'AMOUNT',
 'RATE':'RATE','RETURN_RATE':'RATE','TAX_RATE':'RATE','DURATION':'DURATION',
 'COUNT':'COUNT','CONSUMPTION_COUNT':'COUNT','PAYMENT_COUNT':'COUNT','DATE':'DATE','PAYMENT_MONTH':'DATE',
 'BIRTH_YEAR':'DATE','FORECAST_YEAR':'DATE','AGE':'OTHER','RATIO':'RATIO',
 'IDENTIFIER':'OTHER','UNKNOWN':'OTHER'}
PROTOCOL = {'id':'IRE_SHARED_SEMANTIC_AUTHORING_V1','graph_schema':BOUNDARY_PACKET,
 'order':['source_disposition','minimal_predicate','typed_scope','source_numeric_census','compile'],
 'content':['FACT','OPINION','MATH','NOT_APPLICABLE'],'scenario':['ACTUAL','HYPOTHETICAL','UNRESOLVED'],
 'certainty':['ASSERTED','ESTIMATED','SPECULATIVE','UNRESOLVED','NOT_APPLICABLE'],
 'temporal':['RECORDING','OBSERVATION','FORECAST_TARGET','LEGAL_EFFECTIVE','CALCULATION_PERIOD','BIRTH_THRESHOLD'],
 'roles':ROLE_MAP,'unit_anchor_policy':'literal suffix, adjacent suffix, or explicit same-cue comma-separated numeric list; no unrelated unit',
 'relation_policy':'one grouped premise and consequence per relation; legacy projection flattens only the fragments',
 'no_auto_semantic_inference':True,'legacy_scores_immutable':True}
PROTOCOL_SHA256 = json_digest(PROTOCOL)


def need(ok,code):
    if not ok:raise InvalidInput('AUTHORING_'+code)


def _within(source,raw,scope):
    sp=_span(source,raw);need(_contained(sp,scope),'ANCHOR_OUTSIDE_OWNER');return sp


def _cells(source,sp):
    i,a,b=sp;return {(i,k) for k in range(a,b) if not source.cues[i-1].text[k].isspace()}


def occurrence_inventory(source):
    """Mechanical candidates, not quantities or semantic labels."""
    return [[i,a,b] for i,c in enumerate(source.cues,1)
            for a,b in numeric_token_ranges(c.text,boundary_policy=True)[0]]


def _unit_anchored(source, literal, parts, anchor, unit):
    """Require suffix evidence at the token or a contiguous numeric list."""
    if not unit or unit=="UNKNOWN" or any(ch.isdecimal() for ch in unit):return False
    if literal.rstrip().endswith(unit):return True
    i,_,b=parts[-1];text=source.cues[i-1].text
    for j,l,r in anchor:
        if j!=i or not l<=b<=r:continue
        tail=text[b:r];pos=tail.find(unit)
        if pos<0:continue
        lead=tail[:pos]
        if not lead.strip() or re.fullmatch(r"(?:\s*[,·ㆍ/、]\s*[+−-]?\d+(?:\.\d+)?)+\s*",lead):return True
    return False


def compile_authoring(source, authored):
    need(type(authored) is dict and set(authored)=={'protocol_sha256','grid_sha256','segments','atoms','occurrences'},'SCHEMA')
    need(authored['protocol_sha256']==PROTOCOL_SHA256 and authored['grid_sha256']==json_digest(source_grid(source)),'PIN')
    for field in ('segments','atoms','occurrences'):need(type(authored[field]) is list,'LIST')
    cells={};residual=[]
    for row in authored['segments']:
        need(type(row) is dict and set(row)=={'span','status','reason'} and row['status'] in ('DIRECT','SUPPORT','NONCLAIM','OPEN') and _note(row['reason']),'SEGMENT')
        sp=_span(source,row['span']);cs=_cells(source,sp)
        need(bool(cs) and not cs&cells.keys(),'SEGMENT_OVERLAP')
        cells.update((c,row['status']) for c in cs)
        if row['status'] in ('NONCLAIM','OPEN'):residual.append(deepcopy(row))
    allcells={(i,k) for i,c in enumerate(source.cues,1) for k,ch in enumerate(c.text) if not ch.isspace()}
    need(cells.keys()==allcells,'SEGMENT_CENSUS')
    nodes=[];typed=[];bindings={};uncertain=set();continuations=set()
    for pos,row in enumerate(authored['atoms'],1):
        aid=f'A{pos:05d}'
        need(type(row) is dict and set(row)=={'node','content_type','scenario','certainty','temporal','relations','quantities'},'ATOM')
        n=deepcopy(row['node']);need(type(n) is dict and set(n)=={'predicate','atomicity_reason','utterance_act','speaker','attribution','attributed_participant','polarity','correction','direct','context','risk','risk_reason'},'NODE_FIELDS')
        c,s,e=(row[x] for x in ('content_type','scenario','certainty'))
        need(c in PROTOCOL['content'] and s in PROTOCOL['scenario'] and e in PROTOCOL['certainty'],'TYPED_LABEL')
        act=n['utterance_act'];direct=_spans(source,n['direct'],nonempty=True);context=_spans(source,n['context'])
        need(act!='EVALUATION' or c=='OPINION','EVALUATION_TYPE')
        need(act!='CALCULATION' or c=='MATH','CALCULATION_TYPE')
        directive=act in ('QUESTION','RECOMMENDATION')
        need((c=='NOT_APPLICABLE')==directive and (e=='NOT_APPLICABLE')==directive,'DIRECTIVE_FIELDS')
        need(c!='FACT' or e!='SPECULATIVE','SPECULATION_NOT_FACT')
        for field in ('temporal','relations','quantities'):need(type(row[field]) is list,'ATOM_LIST')
        qualifiers=[];qscope=[]
        for q in row['relations']:
            need(type(q) is dict and set(q)=={'type','premise','consequent','reason'} and q['type'] in ('CONDITION','EXCEPTION') and _note(q['reason']),'RELATION')
            premise=_spans(source,q['premise'],nonempty=True);consequent=_spans(source,q['consequent'],nonempty=True)
            need(all(_contained(z,direct) for z in consequent),'CONSEQUENT_OWNER')
            pc=set().union(*(_cells(source,p) for p in premise));zc=set().union(*(_cells(source,z) for z in consequent))
            need(bool(pc) and bool(zc) and not pc&zc,'PREMISE_CONSEQUENT_OVERLAP')
            qscope.extend(premise)
            qualifiers.extend({'type':q['type'],'span':list(p),'reason':q['reason']} for p in premise)
        kind=('QUESTION' if act=='QUESTION' else 'RECOMMENDATION' if act=='RECOMMENDATION' else 'HYPOTHETICAL' if s=='HYPOTHETICAL' else c)
        modality=('QUESTION' if act=='QUESTION' else 'HYPOTHETICAL' if s=='HYPOTHETICAL' else 'CONDITIONAL' if any(q['type']=='CONDITION' for q in qualifiers) else 'UNRESOLVED' if s=='UNRESOLVED' or e in ('SPECULATIVE','UNRESOLVED') else 'ASSERTED')
        governing=direct+qscope;ts=[]
        for t in row['temporal']:
            need(type(t) is dict and set(t)=={'type','span','reason'} and t['type'] in PROTOCOL['temporal'] and _note(t['reason']),'TIME')
            # No inherited topic date from context alone.
            sp=_within(source,t['span'],governing);ts.append((t['type'],_text(source,sp)))
        need(len(ts)==len(set(ts)),'TIME_DUPLICATE')
        numbers=[]
        for v in row['quantities']:
            need(type(v) is dict and set(v)=={'parts','role','unit','anchor','reason'} and v['role'] in ROLE_MAP and _note(v['reason']) and type(v['unit']) is str,'QUANTITY')
            val=numeric_binding(source,v['parts'],boundary_policy=True);parts=[tuple(x) for x in val['parts']]
            need(all(_contained(x,governing) for x in parts),'NUMBER_OWNER')
            anchor=_spans(source,v['anchor'],nonempty=True)
            need(all(_contained(x,governing) for x in anchor) and all(_contained(x,anchor) for x in parts),'NUMBER_ANCHOR')
            literal=' '.join(_text(source,x) for x in anchor)
            role=v['role'];unit=v['unit']
            if role=='IDENTIFIER':
                # This version supports a literal attached Latin-letter code;
                # other identifier forms remain OPEN instead of guessed.
                def attached_code(part):
                    i,a,b=part;t=source.cues[i-1].text
                    def latin(ch):return ch.isascii() and ch.isalpha()
                    return any(j==i and ((l<a and latin(t[a-1])) or (b<r and latin(t[b]))) for j,l,r in anchor)
                need(unit=='' and not val['cross_cue'] and attached_code(parts[0]),'IDENTIFIER_CONTEXT')
            elif role=='UNKNOWN':
                need(unit=='UNKNOWN','UNKNOWN_UNIT');uncertain.add(aid)
            else:
                need(_unit_anchored(source,val['literal'],parts,anchor,unit),'UNIT_NOT_VERBATIM')
            if role=='AGE':need(unit=='세','AGE_UNIT')
            if role in ('BIRTH_YEAR','FORECAST_YEAR'):need(unit=='년','YEAR_UNIT')
            if role=='PAYMENT_MONTH':need(unit=='월','MONTH_UNIT')
            for part in parts:
                key=(aid,part);need(key not in bindings,'DUPLICATE_OWNER');bindings[key]=role
                # A validated cross-cue unit-only continuation is not an
                # independent per-cue numeric occurrence. Keep its binding.
                if val['cross_cue'] and not any(ch.isdecimal() for ch in _text(source,part)):
                    continuations.add(key)
            numbers.append({'parts':v['parts'],'function':ROLE_MAP[role],'reason':v['reason']})
        need(type(n['speaker']) is dict and 'status' in n['speaker'],'SPEAKER')
        if s=='UNRESOLVED' or e=='UNRESOLVED' or n['speaker']['status']=='UNRESOLVED' or n['attribution']=='UNRESOLVED' or n['attributed_participant']=='UNKNOWN':uncertain.add(aid)
        n.update(kind=kind,modality=modality,as_of='; '.join(f'{k}:{v}' for k,v in sorted(ts)) or None,qualifiers=qualifiers,numbers=numbers)
        nodes.append(n);typed.append({'atom_id':aid,'content_type':c,'scenario':s,'certainty':e,'temporal':row['temporal'],'relations':row['relations'],'quantities':row['quantities']})
    packet={'schema':BOUNDARY_PACKET,'grid_sha256':authored['grid_sha256'],'nodes':nodes,'residual':residual}
    graph=compile_graph(source,packet)
    actual={c:r['status'] for r in graph['census'] for c in _cells(source,tuple(r['span']))}
    need(actual==cells,'DISPOSITION_DRIFT')
    expected={tuple(s) for s in occurrence_inventory(source)};seen=set();open_tokens=0
    for r in authored['occurrences']:
        need(type(r) is dict and set(r)=={'span','disposition','owners','reason'} and _note(r['reason']),'OCCURRENCE')
        sp=_span(source,r['span']);need(sp in expected and sp not in seen,'OCCURRENCE_CENSUS');seen.add(sp)
        owners=r['owners'];need(type(owners) is list and owners==sorted(set(owners)) and all(x in graph['nodes'] for x in owners),'OCCURRENCE_OWNERS')
        found={aid:role for (aid,p),role in bindings.items() if _contained(sp,[p])}
        d=r['disposition'];states={cells[x] for x in _cells(source,sp)}
        if d in ('QUANTITY','IDENTIFIER'):
            need(bool(found) and set(found)==set(owners) and all((role=='IDENTIFIER')==(d=='IDENTIFIER') and role!='UNKNOWN' for role in found.values()),'OCCURRENCE_BINDING')
        elif d=='OPEN':
            need(set(found)==set(owners),'OPEN_OWNER');open_tokens+=1
        elif d in ('SUPPORT','NONCLAIM'):
            need(not found and not owners and states=={d},'OCCURRENCE_DISPOSITION')
        else:need(False,'OCCURRENCE_DISPOSITION')
    need(seen==expected,'OCCURRENCE_CENSUS')
    # A bound token must be represented in the inventory, including across cues.
    need(all((aid,part) in continuations or any(_contained(sp,[part]) for sp in expected) for aid,part in bindings),'BINDING_WITHOUT_OCCURRENCE')
    receipt={'schema':'IRE_SHARED_AUTHORING_RECEIPT_V1','protocol_sha256':PROTOCOL_SHA256,
       'grid_sha256':authored['grid_sha256'],'segments_sha256':_rows_digest(authored['segments']),
       'typed_atoms_sha256':_rows_digest(typed),'occurrences_sha256':_rows_digest(authored['occurrences']),
       'graph_sha256':graph['packet_sha256'],'source_cues':len(source.cues),'atoms':len(nodes),
       'numeric_occurrences':len(expected),'open_numeric_occurrences':open_tokens,'uncertain_atoms':sorted(uncertain),
       'character_dispositions':graph['character_dispositions'],'unbound_numeric_spans':len(graph['unbound_numeric_spans']),
       'boundary_warnings':len(graph['numeric_boundary_warnings']),'semantic_truth_certified':False,'publication_authorized':False}
    return packet,receipt


def comparison_diagnostic(source, first, second, alignment, first_receipt, second_receipt):
    """Reject asserted equality contradicting richer typed records; no score credit."""
    def atom(rows, aid):return rows['atoms'][int(aid[1:])-1]
    def numeric(row):
        return sorted((v['role'],v['unit'],''.join(numeric_binding(source,v['parts'],boundary_policy=True)['literal'].split())) for v in row['quantities'])
    def temporal(row):return sorted((t['type'],_text(source,_span(source,t['span']))) for t in row['temporal'])
    counts={k:0 for k in ('content_type','certainty','scenario','numeric_role_unit','temporal_role','condition_groups','exception_groups')}
    for p in alignment['pairs']:
        x=atom(first,p['prediction_id']);y=atom(second,p['reference_id']);d=p['axes']
        def group_count(row,typ):return sum(q['type']==typ for q in row['relations'])
        diffs={'content_type':x['content_type']!=y['content_type'],'certainty':x['certainty']!=y['certainty'],'scenario':x['scenario']!=y['scenario'],
               'numeric_role_unit':numeric(x)!=numeric(y),'temporal_role':temporal(x)!=temporal(y),
               'condition_groups':group_count(x,'CONDITION')!=group_count(y,'CONDITION'),
               'exception_groups':group_count(x,'EXCEPTION')!=group_count(y,'EXCEPTION')}
        for k,v in diffs.items():counts[k]+=int(v)
        for k,axis in (('content_type','claim_kind'),('certainty','speaker_and_stance'),('scenario','hypothetical_or_actual_scope'),('numeric_role_unit','numeric_value_and_unit'),('temporal_role','temporal_scope')):
            need(not (diffs[k] and d[axis]),'CONTRADICTORY_MATCH_'+k.upper())
    return {'schema':'IRE_SHARED_AUTHORING_COMPARISON_V1','protocol_sha256':PROTOCOL_SHA256,
            'first_receipt_sha256':json_digest(first_receipt),'second_receipt_sha256':json_digest(second_receipt),
            'typed_differences':counts,'open_numeric_occurrences':first_receipt['open_numeric_occurrences']+second_receipt['open_numeric_occurrences'],
            'uncertain_atoms':len(first_receipt['uncertain_atoms'])+len(second_receipt['uncertain_atoms']),
            'semantic_equivalence_certified':False,'publication_authorized':False}
