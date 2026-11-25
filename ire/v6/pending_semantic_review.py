"""Explicit source-link re-review of a pinned current graph, not certification.

Historical obligations and scores are immutable. A supported relation may be
recorded as source-reviewed, but never as a financial fact or as equivalence.
A new graph needs a new review; no automatic carry of these judgments.
"""
from .codec import json_digest, sha256
from .semantic_source_graph import _span, _rows_digest, numeric_binding
from .semantic_obligation_review import need


def pending_review(source, graph, plan, old, rows, prior_rows=()):
    need(graph['grid']['source_sha256']==source.source_sha256 and
         plan['source_sha256']==source.source_sha256 and
         plan['draft_packet_sha256']==graph['packet_sha256'], 'PENDING_GRAPH_PIN')
    om={json_digest(x):x['obligation'] for x in old}
    need(len(om)==len(old)==plan['obligation_count'], 'PENDING_OLD_CENSUS')
    nums={x['old_sha256']:x for x in plan['open_items']}
    scopes={x['scope_id']:x for x in plan['scope_items']}
    need(len(nums)==len(plan['open_items']) and len(scopes)==len(plan['scope_items']), 'PENDING_CENSUS')
    sids=[k for q in scopes.values() for k in q['obligation_ids']]
    need(len(sids)==len(set(sids)) and not set(sids)&set(nums) and set(sids)|set(nums)<=set(om), 'PENDING_PARTITION')
    def evidence(e):
        need(type(e) is dict and set(e)=={'span','text_sha256'},'PENDING_EVIDENCE')
        i,a,b=_span(source,e['span']);need(sha256(source.cues[i-1].text[a:b].encode())==e['text_sha256'],'PENDING_BYTES')
        return [i,a,b]
    def inside(a,b):return a[0]==b[0] and b[1]<=a[1]<a[2]<=b[2]
    seen=set();supported=set();reviewed_scopes=set();scope_supported=set();numeric_supported=set()
    need(type(rows) is list and bool(rows) and type(prior_rows) in (list,tuple),'PENDING_ROWS')
    # A later explicit review may replace HOLD only; a confirmed source link
    # cannot be silently reversed on the same graph. Full history is hashed.
    effective={}
    for batch in (prior_rows, rows):
        local=set() if batch is rows else None
        for r in batch:
            need(type(r) is dict and 'kind' in r and 'id' in r and 'decision' in r,'PENDING_ROW')
            key=(r['kind'],r['id'])
            need((local is None or key not in local) and (key not in effective or (effective[key]['decision']=='HOLD' and effective[key]!=r)),'PENDING_ALREADY_REVIEWED')
            if local is not None:local.add(key)
            effective[key]=r
    for r in effective.values():
        need(type(r) is dict and set(r)=={'kind','id','prior_sha256','decision','node_id','role','edge_index','edge_sha256','evidence','reason'},'PENDING_ROW')
        kind,k=r['kind'],r['id'];key=(kind,k);decision=r['decision']
        need(key not in seen and type(r['reason']) is str and 10<=len(r['reason'].strip())<=2000,'PENDING_DUPLICATE_OR_REASON');seen.add(key)
        need(type(r['evidence']) is list and bool(r['evidence']),'PENDING_EVIDENCE_LIST')
        ev=[evidence(x) for x in r['evidence']]
        node=r['node_id'];role=r['role'];idx=r['edge_index'];h=r['edge_sha256']
        if kind=='NUMBER':
            need(k in nums and k in om and om[k]['type']=='NUMBER','PENDING_NUMBER_ID')
            o=om[k];q=nums[k]
            need(r['prior_sha256']==q['prior_review_sha256'] and any(inside(p,e) for p in o['positions'] for e in ev),'PENDING_PRIOR_OR_ANCHOR')
            if decision=='HOLD':
                need(node is None and role=='UNKNOWN' and idx is None and h is None,'PENDING_HOLD_SHAPE');continue
            need(decision=='SOURCE_LINK_REVIEWED' and node in graph['nodes'] and role in ('AMOUNT','RATE','DURATION','COUNT','DATE','RATIO') and type(idx) is int and 1<=idx<=len(graph['nodes'][node]['numbers']),'PENDING_NUMBER_TARGET')
            n=graph['nodes'][node];edge=n['numbers'][idx-1]
            need(o['position_status']=='EXACT_UNIQUE' and len(o['positions'])==1 and edge['parts']==o['positions'] and edge['literal']==o['raw']['token'] and edge['function']==role and not edge['cross_cue'] and json_digest(edge)==h,'PENDING_NUMBER_EDGE')
            numeric_binding(source,edge['parts'],boundary_policy=True)
            need(all(any(inside(p,d) for d in n['direct']) for p in edge['parts']),'PENDING_DIRECT_OWNER')
            # Candidate expansion must be a separate explicit judgment, not an
            # inferred equivalence. Source ownership is the only claim here.
            if node not in q['candidate_nodes']:
                need('후보 확장:' in r['reason'],'PENDING_EXPANSION_REASON')
            numeric_supported.add(k);supported.add(k)
        elif kind=='QUALIFIER':
            need(k in nums and k in om and om[k]['type'] in ('CONDITION','EXCEPTION'),'PENDING_QUALIFIER_ID')
            o=om[k];q=nums[k]
            need(r['prior_sha256']==q['prior_review_sha256'] and decision=='HOLD' and node is None and role=='UNKNOWN' and idx is None and h is None,'PENDING_QUALIFIER_HOLD')
            if o['positions']:
                need(any(inside(p,e) for p in o['positions'] for e in ev),'PENDING_QUALIFIER_ANCHOR')
            else:
                # Context anchors for coordinate-less reviews are not a source
                # qualifier. They only document why this obligation stays open.
                direct=[d for n in q['candidate_nodes'] for d in graph['nodes'][n]['direct']]
                need(any(inside(e,d) for e in ev for d in direct),'PENDING_QUALIFIER_CONTEXT')
        elif kind=='SCOPE':
            need(k in scopes,'PENDING_SCOPE_ID');q=scopes[k];reviewed_scopes.add(k)
            need(r['prior_sha256']==q['review_sha256'] and idx is None and h is None,'PENDING_SCOPE_PRIOR')
            required=[evidence(e) for e in q['antecedent']]+[evidence(q['consequent'])]
            need(all(any(inside(a,b) for b in ev) for a in required),'PENDING_SCOPE_EVIDENCE')
            if decision=='HOLD':
                need(node is None and role=='UNKNOWN','PENDING_HOLD_SHAPE');continue
            need(decision=='SOURCE_LINK_REVIEWED' and node in q.get('candidate_nodes',[q['node_id']]) and node in graph['nodes'] and role==q['role'],'PENDING_SCOPE_OWNER')
            n=graph['nodes'][node]
            need(all(any(e['type']==q['type'] and e['span']==a for e in n['qualifiers']) for a in required[:-1]) and any(inside(required[-1],d) for d in n['direct']),'PENDING_SCOPE_EDGE')
            if role=='QUESTION_PREMISE':need(n['kind']=='QUESTION','PENDING_SCOPE_QUESTION')
            scope_supported.add(k);supported.update(q['obligation_ids'])
        else:need(False,'PENDING_KIND')
    return {'schema':'IRE_V3_PENDING_SOURCE_LINK_REVIEW_V1','graph_sha256':graph['packet_sha256'],
            'plan_sha256':json_digest(plan),'review_rows_sha256':_rows_digest(list(prior_rows)+rows),
            'number_reviewed':sum(k=='NUMBER' for k,_ in seen),'number_links_reviewed':len(numeric_supported),
            'open_qualifiers_reviewed':sum(k=='QUALIFIER' for k,_ in seen),
            'scope_groups_reviewed':len(reviewed_scopes),'scope_groups_source_reviewed':len(scope_supported),
            'scope_obligations_source_reviewed':len(supported)-len(numeric_supported),
            'historical_open_obligations':len(nums),'historical_scope_drafts':len(sids),
            'remaining_open_obligations':len(nums)-len(numeric_supported),'remaining_scope_drafts':len(sids)-(len(supported)-len(numeric_supported)),
            'reviewed_id_sha256':json_digest(sorted(supported)),'claim_semantic_equivalence_certified':False,
            'semantic_conservation_verified':False,'financial_approval':False,'ready_for_e3':False,'publication_authorized':False}
