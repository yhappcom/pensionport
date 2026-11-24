"""Constrained development successor for numeric roles and lexical defects.

No new claim, unit, source anchor, or approval is inferred. Legacy decisions
remain pinned to their original graph. Changed edges have explicit hash lineage.
"""
from copy import deepcopy
from .codec import json_digest, require_hash, sha256
from .semantic_source_graph import compile_graph, BOUNDARY_PACKET, _rows_digest
from .semantic_obligation_review import need
from .semantic_reconciliation import verify_reconciliation_plan
from .qualifier_gap_review import draft_qualifier_gaps
from .obligation_ledger import _run


def numeric_successor(source, packet, old, candidates, events, rows, scopes, plan, amendments, *, expected_plan_sha256, **pins):
    """Recompile pinned parent and derive a limited V2 successor.

    A role refinement is allowed only on an existing exact source edge.
    Cross-node assignment remains a draft, never an automatic equivalence.
    Invalid legacy tokens are retained as OPEN with a lexical warning link.
    """
    verify_reconciliation_plan(plan, source, packet, old, candidates, events, rows, scopes,
                               expected_plan_sha256=expected_plan_sha256, **pins)
    draft, _ = draft_qualifier_gaps(source, packet, old, candidates, events, rows, scopes,
                     expected_head=pins['expected_head'], **{k:v for k,v in pins.items() if k not in ('expected_head','expected_gap_receipt_sha256')})
    parent = compile_graph(source, draft)
    new = deepcopy(draft); new['schema'] = BOUNDARY_PACKET
    prospective = compile_graph(source, new)
    om = {json_digest(x):x['obligation'] for x in old}
    opens = {x['old_sha256']:x for x in plan['open_items']}
    _, single, _, _, _, _ = _run(source, packet, old, candidates, events,
                       {k:v for k,v in pins.items() if k not in ('expected_head','expected_gap_receipt_sha256')})
    seen=set(); changes={}; links=[]
    need(type(amendments) is list and bool(amendments), 'SUCCESSOR_ROWS')
    for a in amendments:
        need(type(a) is dict and set(a)=={'old_sha256','prior_review_sha256','action','node_id','edge_index','role','reason'}, 'SUCCESSOR_ROW')
        k=a['old_sha256']; role=a['role']; node=a['node_id']; idx=a['edge_index']
        need(k in opens and k not in seen and om[k]['type']=='NUMBER', 'SUCCESSOR_OPEN_NUMERIC')
        seen.add(k); o=om[k]; q=opens[k]
        need(a['prior_review_sha256']==q['prior_review_sha256'] and type(a['reason']) is str and 10<=len(a['reason'].strip())<=2000, 'SUCCESSOR_PRIOR')
        need(o['position_status']=='EXACT_UNIQUE' and len(o['positions'])==1, 'SUCCESSOR_POSITION')
        span=o['positions'][0]; i,l,r=span
        need(source.cues[i-1].text[l:r]==o['raw']['token'], 'SUCCESSOR_LITERAL')
        if a['action']=='LEXICAL_OPEN':
            need(node is None and idx is None and role=='UNKNOWN', 'SUCCESSOR_LEXICAL_SHAPE')
            matches=[w for w in prospective['numeric_boundary_warnings'] if w['legacy_span']==span]
            need(len(matches)==1, 'SUCCESSOR_LEXICAL_WARNING')
            links.append({**a,'warning':matches[0],'status':'OPEN'});continue
        need(a['action']=='ROLE_DRAFT' and role in ('AMOUNT','RATE','DURATION','COUNT','DATE','RATIO') and node in parent['nodes'] and type(idx) is int and 1<=idx<=len(parent['nodes'][node]['numbers']), 'SUCCESSOR_TARGET')
        edge=parent['nodes'][node]['numbers'][idx-1]
        need(edge['parts']==[span] and edge['literal']==o['raw']['token'] and not edge['cross_cue'], 'SUCCESSOR_EDGE')
        need(edge['function'] in ('OTHER',role), 'SUCCESSOR_ROLE_CONFLICT')
        # An exact coordinate does not prove an owner relationship. Record
        # candidate changes explicitly, and retain the old OPEN status.
        key=(node,idx);need(key not in changes or changes[key]==role,'SUCCESSOR_ROLE_CONFLICT');changes[key]=role
        links.append({**a,'old_edge_sha256':json_digest(edge),'candidate_expansion':node not in q['candidate_nodes'],'status':'OPEN_PENDING_SEMANTIC_REVIEW'})
    for (node,idx),role in changes.items():new['nodes'][int(node[1:])-1]['numbers'][idx-1]['function']=role
    final=compile_graph(source,new)
    need(parent['census']==final['census'] and parent['character_dispositions']==final['character_dispositions'], 'SUCCESSOR_CENSUS')
    need(parent['unbound_numeric_spans']==final['unbound_numeric_spans'], 'SUCCESSOR_UNBOUND')
    edge_lineage=[]
    for (node,idx),role in sorted(changes.items()):
        before=parent['nodes'][node]['numbers'][idx-1];after=final['nodes'][node]['numbers'][idx-1]
        need({k:v for k,v in before.items() if k!='function'}=={k:v for k,v in after.items() if k!='function'}, 'SUCCESSOR_EDGE_DRIFT')
        old_hash=json_digest(before);new_hash=json_digest(after)
        impacted=[]
        for row in single:
            e=row.get('edge')
            if e and e['node_id']==node and e['edge_index']==idx and e['edge_sha256']==old_hash:
                impacted.append({'old_sha256':row['old_sha256'],'prior_review_sha256':json_digest(row),'decision':row['decision'],'role':row['role'],'status':'HISTORICAL_PIN_RETAINED'})
        edge_lineage.append({'node_id':node,'edge_index':idx,'old_edge_sha256':old_hash,'new_edge_sha256':new_hash,'prior_references':impacted})
    for x in links:
        if x['action']=='ROLE_DRAFT':x['new_edge_sha256']=json_digest(final['nodes'][x['node_id']]['numbers'][x['edge_index']-1])
    return new, {'schema':'IRE_V3_NUMERIC_SUCCESSOR_DRAFT_V1','source_sha256':source.source_sha256,'parent_head':pins['expected_head'],
        'parent_plan_sha256':expected_plan_sha256,'parent_packet_sha256':parent['packet_sha256'],'successor_packet_sha256':final['packet_sha256'],
        'amendments_sha256':_rows_digest(amendments),'links':links,'edge_lineage':edge_lineage,'obligation_count':plan['obligation_count'],
        'open_obligations':len(opens),'scope_drafts':sum(len(x['obligation_ids']) for x in plan['scope_items']),
        'original_scores_unchanged':True,'semantic_conservation_verified':False,'financial_approval':False,'ready_for_e3':False,'publication_authorized':False}


def verify_numeric_successor(successor, receipt, *args, expected_receipt_sha256, **kwargs):
    require_hash(expected_receipt_sha256,'SUCCESSOR_RECEIPT')
    p,r=numeric_successor(*args,**kwargs)
    need(p==successor and r==receipt and json_digest(r)==expected_receipt_sha256,'SUCCESSOR_REPLAY')
    return expected_receipt_sha256
