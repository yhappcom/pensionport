"""Source-bound reconciliation plan, not semantic approval.

Preserve typed antecedent/consequent links lost by the legacy flat graph.
Group exact numeric evidence for review without merging legacy obligations.
All inputs replay against independent parent pins; no status is promoted.
"""
from collections import Counter, defaultdict
from .codec import json_digest, require_hash, sha256
from .semantic_source_graph import compile_graph, _rows_digest
from .semantic_obligation_review import need
from .obligation_ledger import _run
from .qualifier_gap_review import draft_qualifier_gaps


def _route(o, c):
    if o['type'] == 'NUMBER':
        return 'NUMERIC_COORDINATE_AMBIGUOUS' if o['position_status'] != 'EXACT_UNIQUE' else 'NUMERIC_ROLE_UNIT_SCOPE'
    if not o['positions']:
        return {'SOURCE_SCOPE':'SOURCE_SCOPE_UNLOCATED', 'MIXED':'SOURCE_REVIEWER_SPLIT'}.get(c['qualifier_separation'], 'QUALIFIER_UNLOCATED')
    return 'LOCATED_QUALIFIER_SCOPE'


def reconciliation_plan(source, packet, old, candidates, events, rows, scopes, *, expected_head, expected_gap_receipt_sha256, **pins):
    require_hash(expected_head, 'RECONCILE_HEAD')
    require_hash(expected_gap_receipt_sha256, 'RECONCILE_GAP_PIN')
    draft, receipt = draft_qualifier_gaps(source, packet, old, candidates, events, rows, scopes, expected_head=expected_head, **pins)
    need(json_digest(receipt)==expected_gap_receipt_sha256, 'RECONCILE_GAP_PIN')
    g, _, _, effective, _, head = _run(source, packet, old, candidates, events, pins)
    need(head==expected_head, 'RECONCILE_HEAD')
    om={json_digest(x):x for x in old}; cm={x['old_obligation_sha256']:x for x in candidates}
    decisions={**effective, **{r['old_sha256']:r['decision'] for r in rows}}
    need(set(decisions)==set(om) and len(effective)+len(rows)==len(om), 'RECONCILE_CENSUS')
    history={r['old_sha256']:json_digest(r) for e in events for r in e['rows']}
    history.update({r['old_sha256']:json_digest(r) for r in rows})
    members=defaultdict(list); open_items=[]; scope_items=[]; scope_members=defaultdict(list)
    for r in rows:
        if r['decision']=='SCOPE_DRAFT':scope_members[r['scope_id']].append(r['old_sha256'])
    def overlaps(a,b):return a[0]==b[0] and max(a[1],b[1])<min(a[2],b[2])
    for q in scopes:
        # Preserve typed role and the particular consequent rather than flattening them into a reason string.
        ids=sorted(scope_members[q['scope_id']]); n=g['nodes'][q['node_id']]
        overlapping=[x for x in n['qualifiers'] if any(overlaps(x['span'],p['span']) for p in q['parts'])]
        scope_items.append({'scope_id':q['scope_id'],'node_id':q['node_id'],'type':q['type'],'role':q['role'],
            'antecedent':q['parts'],'consequent':q['consequent'],'obligation_ids':ids,'review_sha256':json_digest(q),
            'existing_overlapping_edge_sha256':[json_digest(x) for x in overlapping], 'status':'DRAFT_PENDING_SEMANTIC_REVIEW'})
    need({k for x in scope_items for k in x['obligation_ids']}=={k for k,v in decisions.items() if v=='SCOPE_DRAFT'},'RECONCILE_SCOPE_CENSUS')
    for k in sorted(decisions):
        if decisions[k]!='OPEN':continue
        o=om[k]['obligation']; c=cm[k]; route=_route(o,c)
        # Only exact numeric source tokens may share evidence retrieval. Each old ID retains its own review.
        group_key={'source_sha256':source.source_sha256,'route':route,'positions':o['positions'],'token':o['raw']['token']} if route=='NUMERIC_ROLE_UNIT_SCOPE' and len(o['positions'])==1 else {'old_sha256':k,'route':route}
        group=json_digest(group_key);members[group].append(k)
        open_items.append({'old_sha256':k,'route':route,'evidence_group':group,'positions':o['positions'],'candidate_nodes':c['candidate_group_nodes'],
                          'prior_review_sha256':history[k],'status':'OPEN'})
    tasks=[{'group_sha256':k,'obligation_ids':v,'status':'REVIEW_REQUIRED'} for k,v in sorted(members.items())]
    compiled=compile_graph(source,draft)
    residual=[x for x in compiled['census'] if x['status']=='OPEN']
    numeric=[{**x,'text_sha256':sha256(source.cues[x['span'][0]-1].text[x['span'][1]:x['span'][2]].encode())} for x in compiled['unbound_numeric_spans']]
    return {'schema':'IRE_V3_SEMANTIC_RECONCILIATION_PLAN_V1','source_sha256':source.source_sha256,'parent_head':head,
            'draft_packet_sha256':receipt['draft_packet_sha256'],'gap_receipt_sha256':expected_gap_receipt_sha256,
            'obligation_count':len(om),'open_items':open_items,'evidence_tasks':tasks,'scope_items':scope_items,
            'residual_open':residual,'unbound_numeric':numeric,'routes':dict(Counter(x['route'] for x in open_items)),
            'open_items_sha256':_rows_digest(open_items),'scope_items_sha256':_rows_digest(scope_items),
            'semantic_conservation_verified':False,'financial_approval':False,'ready_for_e3':False,'publication_authorized':False}


def verify_reconciliation_plan(plan, *args, expected_plan_sha256, **kwargs):
    """Reject any change to evidence, role, consequent, or obligation membership."""
    require_hash(expected_plan_sha256,'RECONCILE_PLAN_PIN')
    expected=reconciliation_plan(*args, **kwargs)
    need(plan==expected and json_digest(expected)==expected_plan_sha256,'RECONCILE_PLAN_REPLAY')
    return expected_plan_sha256
