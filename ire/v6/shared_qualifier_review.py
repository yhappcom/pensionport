"""Explicit multi-successor qualifier review; never an automatic semantic approval.

Replay the frozen single-edge review and recompile the source graph. Each
candidate receives a separate, source-linked decision, including exclusions.
An amendment cannot edit prior rows or change any original score.
"""
from .codec import json_digest,sha256
from .semantic_source_graph import compile_graph,_span,_rows_digest
from .semantic_obligation_review import review_batch,need


def review_shared_qualifiers(source,packet,old,candidates,prior_rows,prior_receipt,rows,*,
                             expected_prior_receipt_sha256,**pins):
    g=compile_graph(source,packet)
    need(json_digest(prior_receipt)==expected_prior_receipt_sha256,'SHARED_PRIOR_PIN')
    need(review_batch(source,g,old,candidates,prior_rows,**pins)==prior_receipt,'SHARED_PRIOR_REPLAY')
    om={json_digest(x):x['obligation'] for x in old}
    cm={x['old_obligation_sha256']:x for x in candidates}
    prior={x['old_sha256']:x for x in prior_rows};seen=set();results=[]
    def overlaps(p,q):return p[0]==q[0] and max(p[1],q[1])<min(p[2],q[2])
    def evidence(ev):
        need(type(ev) is dict and set(ev)=={'span','text_sha256'},'SHARED_EVIDENCE_SCHEMA')
        i,a,b=_span(source,ev['span'])
        need(sha256(source.cues[i-1].text[a:b].encode())==ev['text_sha256'],'SHARED_EVIDENCE_BYTES')
        return [i,a,b]
    def note(x):return type(x) is str and 10<=len(x.strip())<=2000
    need(type(rows) is list and bool(rows),'SHARED_ROWS')
    for row in rows:
        need(type(row) is dict and set(row)=={'old_sha256','prior_row_sha256','reason','targets'},'SHARED_ROW')
        k=row['old_sha256'];need(type(k) is str and k in om and k not in seen,'SHARED_OLD_ID');seen.add(k)
        o=om[k];c=cm[k];p=prior.get(k)
        need(row['prior_row_sha256']==(json_digest(p) if p else None),'SHARED_AMENDMENT_PIN')
        need(p is None or p['decision'] in ('OPEN','CARRY_SOURCE_EDGE'),'SHARED_PRIOR_DECISION')
        need(o['type'] in ('CONDITION','EXCEPTION') and o['position_status'] in ('EXACT_UNIQUE','CUE_ONLY') and
             c['qualifier_separation'] is None and bool(o['positions']) and note(row['reason']),'SHARED_SOURCE_SCOPE')
        edges={json_digest(e):e for e in c['candidate_edges']}
        need(len(edges)==len(c['candidate_edges']) and len({e['node_id'] for e in edges.values()})>=2,'SHARED_CANDIDATES')
        need(type(row['targets']) is list and len(row['targets'])==len(edges),'SHARED_TARGET_CENSUS')
        used=set();applied=[];opened=0
        for t in row['targets']:
            need(type(t) is dict and set(t)=={'edge','decision','reason','condition_evidence','predicate_evidence'},'SHARED_TARGET')
            e=t['edge'];h=json_digest(e)
            need(h in edges and e==edges[h] and h not in used and e['node_id'] in c['candidate_group_nodes'],'SHARED_FOREIGN_OR_DUPLICATE')
            used.add(h);n=g['nodes'][e['node_id']];idx=e['edge_index']
            need(type(idx) is int and 1<=idx<=len(n['qualifiers']),'SHARED_EDGE_INDEX')
            q=n['qualifiers'][idx-1]
            need(json_digest(q)==e['edge_sha256'] and q['type']==o['type'] and q['span'] in o['positions'],'SHARED_EDGE_SCOPE')
            need(t['decision'] in ('APPLY','EXCLUDE','OPEN') and note(t['reason']),'SHARED_DECISION')
            need(evidence(t['condition_evidence'])==q['span'],'SHARED_CONDITION_EVIDENCE')
            s=evidence(t['predicate_evidence'])
            # Evidence must include the specific consequent, not just a reused condition.
            need(any(overlaps(s,d) for d in n['direct']) and not any(overlaps(s,v['span']) for v in n['qualifiers']),
                 'SHARED_PREDICATE_EVIDENCE')
            if t['decision']=='APPLY':applied.append(e)
            opened+=t['decision']=='OPEN'
        need(used==set(edges),'SHARED_TARGET_CENSUS')
        if p and p['decision']=='CARRY_SOURCE_EDGE':
            need(p['edge'] in applied,'SHARED_PRIOR_CARRY_LOST')
        need(bool(applied) or opened>0,'SHARED_ALL_EXCLUDED')
        results.append({'old_sha256':k,'previous_decision':p['decision'] if p else None,
                        'applied_edges':applied,'open_targets':opened,
                        'status':'OPEN' if opened else 'REVIEWED_SOURCE_SCOPE',
                        'row_sha256':json_digest(row)})
    return {'schema':'IRE_V3_SHARED_QUALIFIER_AMENDMENT_V1','prior_receipt_sha256':expected_prior_receipt_sha256,
            'packet_sha256':g['packet_sha256'],'reviewed_obligations':len(results),
            'new_obligations':sum(x['previous_decision'] is None for x in results),
            'reviewed_existing':sum(x['previous_decision'] is not None for x in results),
            'open_obligations':sum(x['status']=='OPEN' for x in results),
            'applied_edges':sum(len(x['applied_edges']) for x in results),
            'rows_sha256':_rows_digest(rows),'results_sha256':_rows_digest(results),'results':results,
            'prior_rows_unchanged':True,'semantic_equivalence_certified':False,
            'financial_approval':False,'publication_authorized':False}
