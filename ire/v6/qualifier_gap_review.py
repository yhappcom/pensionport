"""Source-bound draft patches for legacy qualifiers with no existing edge.

Original graph and externally pinned legacy ledger are replayed unchanged.
Explicit review is supplied by ChatGPT; neither a source position nor a patch
certifies semantic equivalence. Output is a new provisional graph only.
"""
from collections import Counter
from copy import deepcopy
from .codec import json_digest, sha256
from .semantic_source_graph import compile_graph, _span, _rows_digest
from .semantic_obligation_review import need
from .obligation_ledger import replay


def draft_qualifier_gaps(source, packet, old, candidates, ledger, rows, scopes, *, expected_head, **pins):
    original = compile_graph(source, packet)
    prior = replay(source, packet, old, candidates, ledger, expected_head=expected_head, **pins)
    seen = {r['old_sha256'] for event in ledger for r in event['rows']}
    om = {json_digest(r): r['obligation'] for r in old}
    cm = {r['old_obligation_sha256']: r for r in candidates}
    need(len(om) == len(old) == len(cm) == len(candidates), 'GAP_PARENT_CENSUS')
    pending = {k for k in om if k not in seen and om[k]['type'] in ('CONDITION', 'EXCEPTION')}
    def note(s): return type(s) is str and 10 <= len(s.strip()) <= 2000
    def overlap(a,b): return a[0] == b[0] and max(a[1],b[1]) < min(a[2],b[2])
    def inside(a,b): return a[0] == b[0] and b[1] <= a[1] < a[2] <= b[2]
    def evidence(e):
        need(type(e) is dict and set(e) == {'span','text_sha256'}, 'GAP_EVIDENCE')
        i,a,b = _span(source,e['span'])
        need(sha256(source.cues[i-1].text[a:b].encode()) == e['text_sha256'], 'GAP_EVIDENCE_BYTES')
        return [i,a,b]
    sm = {}; covered = {}; new = deepcopy(packet)
    need(type(scopes) is list and type(rows) is list and bool(rows), 'GAP_ROWS')
    for q in scopes:
        need(type(q) is dict and set(q) == {'scope_id','node_id','type','role','parts','consequent','reason'}, 'GAP_SCOPE')
        sid = q['scope_id']; node = q['node_id']
        need(type(sid) is str and sid and sid not in sm and node in original['nodes'] and note(q['reason']), 'GAP_SCOPE_ID')
        need(q['type'] in ('CONDITION','EXCEPTION') and q['role'] in ('SOURCE_CONDITION','HYPOTHETICAL_PREMISE','QUESTION_PREMISE'), 'GAP_SCOPE_ROLE')
        parts = [evidence(e) for e in q['parts']]; con = evidence(q['consequent'])
        n = original['nodes'][node]
        need(bool(parts) and parts == sorted(parts) and len({tuple(p) for p in parts}) == len(parts), 'GAP_SCOPE_PARTS')
        need(any(inside(con,d) for d in n['direct']) and not any(overlap(con,p) for p in parts), 'GAP_CONSEQUENT')
        need(not any(overlap(a,b) for i,a in enumerate(parts) for b in parts[i+1:]), 'GAP_OVERLAPPING_PARTS')
        if q['role'] == 'QUESTION_PREMISE': need(n['kind']=='QUESTION','GAP_QUESTION')
        if q['role'] == 'HYPOTHETICAL_PREMISE': need(n['kind'] in ('HYPOTHETICAL','MATH','QUESTION','FACT','RECOMMENDATION'), 'GAP_PREMISE')
        sm[sid]=(q,parts,con); covered[sid]=set()
    reviewed=set(); counts=Counter()
    for r in rows:
        need(type(r) is dict and set(r)=={'old_sha256','decision','scope_id','evidence','reason'}, 'GAP_ROW')
        k=r['old_sha256']; need(type(k) is str and k in pending and k not in reviewed and note(r['reason']), 'GAP_OLD_ID')
        reviewed.add(k); o=om[k]; c=cm[k]; d=r['decision']; sid=r['scope_id']
        need(d in ('SCOPE_DRAFT','CONTEXT_ONLY','OPEN') and type(r['evidence']) is list and bool(r['evidence']), 'GAP_DECISION')
        ev=[evidence(x) for x in r['evidence']]
        need(o['positions'] and any(inside(p,z) for p in ev for z in o['positions']), 'GAP_OLD_SOURCE')
        if d=='SCOPE_DRAFT':
            need(sid in sm and c['qualifier_separation'] is None and o['position_status'] in ('EXACT_UNIQUE','CUE_ONLY'), 'GAP_NOT_SOURCE_SCOPE')
            q,parts,con=sm[sid]
            need(q['node_id'] in c['candidate_group_nodes'] and q['type']==o['type'], 'GAP_FOREIGN_NODE')
            matched={tuple(p) for p in parts if any(inside(p,z) for z in o['positions']) and any(inside(p,e) for e in ev)}
            need(bool(matched),'GAP_UNRELATED_SCOPE_PART'); covered[sid].update(matched)
        else: need(sid is None,'GAP_UNEXPECTED_SCOPE')
        counts[d]+=1
    need(reviewed==pending,'GAP_PENDING_CENSUS')
    added=0
    for sid,(q,parts,con) in sm.items():
        need(covered[sid]=={tuple(x) for x in parts},'GAP_UNACCOUNTED_SCOPE_PART')
        node=new['nodes'][int(q['node_id'][1:])-1]
        for p in parts:
            need(not any(x['type']==q['type'] and x['span']==p for x in node['qualifiers']),'GAP_EXISTING_EDGE')
            node['qualifiers'].append({'type':q['type'],'span':p,'reason':q['role']+': '+q['reason']});added+=1
    compiled=compile_graph(source,new)
    need(len(compiled['nodes'])==len(original['nodes']),'GAP_NODE_COUNT')
    # Existing graph is immutable: patch is separate, and cannot rewrite prior review.
    return new, {'schema':'IRE_V3_QUALIFIER_GAP_DRAFT_V1','parent_head':expected_head,'parent_packet_sha256':original['packet_sha256'],
                 'draft_packet_sha256':compiled['packet_sha256'],'rows_sha256':_rows_digest(rows),'scopes_sha256':_rows_digest(scopes),
                 'prior_reviewed':prior['reviewed'],'new_reviewed':len(reviewed),'decisions':dict(counts),
                 'scope_bundles':len(sm),'new_qualifier_edges':added,'draft_unbound_numeric_spans':len(compiled['unbound_numeric_spans']),
                 'draft_open_characters':compiled['character_dispositions'].get('OPEN',0),
                 'original_score_changed':False,'semantic_conservation_verified':False,'ready_for_e3':False,'publication_authorized':False}
