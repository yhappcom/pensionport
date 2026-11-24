"""Validate explicit, source-edge-level legacy obligation review, not claim truth.

Inputs must be the externally pinned old obligation/candidate records and a
recompiled V3 graph. Keep the frozen graph and old scores unchanged. Reviewer
judgment is supplied, never inferred from a coordinate match. A reviewer note
is a separate downstream review object, never an original-source qualifier.
"""
from collections import Counter
from .codec import json_digest,sha256
from .errors import InvalidInput
from .semantic_source_graph import _span,_rows_digest

DECISIONS={'CARRY_SOURCE_EDGE','REBIND_SOURCE_FRAGMENT','CONTEXT_ONLY','REVIEWER_NOTE','OPEN'}
ROLES={'AMOUNT','RATE','DURATION','COUNT','DATE','RATIO','CONDITION','EXCEPTION','CONTEXT','REVIEW_NOTE','UNKNOWN'}

def need(ok,label):
    if not ok:raise InvalidInput('OBLIGATION_REVIEW_'+label)

def review_batch(source,graph,old,candidates,rows,*,expected_old_digest,expected_candidate_digest,expected_packet_sha):
    """Partial appendable review tranche; unreviewed obligations remain pending."""
    need(graph['grid']['source_sha256']==source.source_sha256 and graph['packet_sha256']==expected_packet_sha,'GRAPH_PIN')
    need(_rows_digest(old)==expected_old_digest and _rows_digest(candidates)==expected_candidate_digest,'PARENT_PIN')
    om={json_digest(x):x for x in old}; cm={x['old_obligation_sha256']:x for x in candidates}
    need(len(om)==len(old)==len(cm)==len(candidates) and set(om)==set(cm),'PARENT_CENSUS')
    seen=set();counts=Counter();out=[]
    for row in rows:
        need(type(row) is dict and set(row)=={'old_sha256','decision','role','edge','evidence','reason','review_note'},'ROW')
        key=row['old_sha256'];need(type(key) is str and key in om and key not in seen,'OLD_ID');seen.add(key)
        o=om[key]['obligation'];c=cm[key];d=row['decision'];role=row['role'];edge=row['edge']
        need(d in DECISIONS and role in ROLES and type(row['reason']) is str and 10<=len(row['reason'].strip())<=2000,'DECISION')
        need(type(row['evidence']) is list and bool(row['evidence']),'EVIDENCE')
        spans=[]
        for ev in row['evidence']:
            need(type(ev) is dict and set(ev)=={'span','text_sha256'},'EVIDENCE_ROW')
            i,a,b=_span(source,ev['span']);need(sha256(source.cues[i-1].text[a:b].encode())==ev['text_sha256'],'EVIDENCE_BYTES')
            spans.append([i,a,b])
        def intersects(p,q):return p[0]==q[0] and max(p[1],q[1])<min(p[2],q[2])
        if o['positions']:
            need(any(intersects(p,q) for p in o['positions'] for q in spans),'UNRELATED_EVIDENCE')
        if d=='REVIEWER_NOTE':
            group_spans=[z for k in c['candidate_group_nodes'] for z in graph['nodes'][k]['direct']]
            need(any(intersects(p,q) for p in group_spans for q in spans),'NOTE_UNRELATED_EVIDENCE')
            need(c['qualifier_separation']=='REVIEW_NOTE' and o['position_status']=='SEMANTIC_ONLY_NO_EXPLICIT_COORDINATE' and role=='REVIEW_NOTE' and edge is None and row['review_note']==o['raw'],'NOTE_NOT_SOURCE')
        else:
            need(row['review_note'] is None,'NOTE_FIELD')
            if d=='OPEN':need(edge is None and role=='UNKNOWN','OPEN_SHAPE')
            else:
                need(type(edge) is dict and edge in c['candidate_edges'] and edge['node_id'] in c['candidate_group_nodes'],'EDGE_NOT_CANDIDATE')
                n=graph['nodes'][edge['node_id']];v=n['numbers' if o['type']=='NUMBER' else 'qualifiers'][edge['edge_index']-1]
                need(json_digest(v)==edge['edge_sha256'],'EDGE_DIGEST')
                anchors=v['parts'] if o['type']=='NUMBER' else [v['span']]
                need(any(intersects(p,q) for p in anchors for q in spans),'EDGE_EVIDENCE')
                if d=='CONTEXT_ONLY':need(o['type']=='NUMBER' and role=='CONTEXT','CONTEXT_SHAPE')
                elif o['type']=='NUMBER':
                    need(role in {'AMOUNT','RATE','DURATION','COUNT','DATE','RATIO'} and o['position_status']=='EXACT_UNIQUE','NUMERIC_ROLE_OR_POSITION')
                    if d=='CARRY_SOURCE_EDGE':
                        need(not v['cross_cue'] and len(anchors)==1 and anchors[0] in o['positions'] and v['literal']==o['raw']['token'],'NOT_EXACT_NUMBER')
                    else:
                        need(d=='REBIND_SOURCE_FRAGMENT' and v['cross_cue'] and any(p[0]==q[0] and q[1]<=p[1] and p[2]<=q[2] for p in o['positions'] for q in anchors),'NOT_CROSS_CUE_FRAGMENT')
                else:
                    need(d=='CARRY_SOURCE_EDGE' and role==o['type']==v['type'] and v['span'] in o['positions'],'QUALIFIER_MISMATCH')
        counts[d]+=1
        out.append({'old_sha256':key,'decision':d,'role':role,'review_sha256':json_digest(row),
                    'claim_semantic_equivalence_certified':False,'financial_approval':False})
    return {'reviewed':len(seen),'remaining_unreviewed':len(om)-len(seen),'decisions':dict(counts),
            'rows_sha256':_rows_digest(rows),'output_sha256':_rows_digest(out),'packet_sha256':expected_packet_sha,
            'claim_semantic_equivalence_certified':False,'financial_approval':False,'publication_authorized':False}
