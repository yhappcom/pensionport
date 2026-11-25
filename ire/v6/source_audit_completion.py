"""Development audit completion: explicit repeat review, typed correction custody.
No release, independent certification, or automatic semantic equivalence.
V1 frozen scores and source ledgers are never rewritten.
"""
from .codec import json_digest
from .gold_eval import MATCH_FIELDS
from .semantic_source_graph import _rows_digest, _span, _spans, _contained, _note, compile_graph, numeric_binding
from .semantic_authoring_protocol import compile_authoring, occurrence_inventory
from .source_first_audit import (AUDIT_SHA256, need, cells, spans, freeze_source_ledger,
    audit_bidirectional, _edge_sig, _anchors)

COMPLETION_SPEC = {'id':'IRE_SOURCE_AUDIT_COMPLETION_DEV_V1','audit_sha256':AUDIT_SHA256,
    'initial_score_immutable':True,'same_frozen_source_ledger':True,
    'repeat_rule':'explicit all-axis source judgment and numeric occurrence custody; no automatic equivalence',
    'candidate_thresholds':{'precision_bp':9500,'recall_bp':9800,'high_risk_unmatched_or_conflict':0},
    'all_open_and_repeat_review_blockers_zero':True,'typed_edge_lineage_required':True,
    'financial_and_e3_e5_release_separate':True,'prospective_qualification_authorized':False}
COMPLETION_SHA256=json_digest(COMPLETION_SPEC)


def review_repeats(source, ledger, rows):
    """Every REPEAT segment has one explicit review; non-equivalence stays OPEN.
    The caller cannot turn a repeated number into an automatic semantic match.
    Conservative exact literal role matching; ambiguous/cross-cue repeats HOLD.
    """
    receipt=freeze_source_ledger(source,ledger)
    ob={x['id']:x for x in ledger['obligations']}
    required={tuple(x['span']):x for x in ledger['segments'] if x['status']=='REPEAT'}
    occurrences={tuple(x['span']) for x in ledger['occurrences'] if x['status']=='REPEAT'}
    need(type(rows) is list,'REPEAT_ROWS');seen=set();seen_num=set();opened=[]
    for r in rows:
        need(type(r) is dict and set(r)=={'spans','owner_ids','verdict','axes','reasons','reason','numbers'},'REPEAT_ROW')
        ss=spans(source,r['spans']);ids=r['owner_ids'];need(type(ids) is list and bool(ids) and ids==sorted(set(ids)),'REPEAT_OWNERS')
        need(all(s in required and s not in seen and required[s]['owners']==ids for s in ss),'REPEAT_PARTITION');seen.update(ss)
        need(r['verdict'] in ('EQUIVALENT','DISTINCT','OPEN') and _note(r['reason']),'REPEAT_VERDICT')
        need(type(r['axes']) is dict and set(r['axes'])==set(MATCH_FIELDS) and all(type(x) is bool for x in r['axes'].values()),'REPEAT_AXES')
        need(type(r['reasons']) is dict and set(r['reasons'])==set(MATCH_FIELDS) and all(_note(x) for x in r['reasons'].values()),'REPEAT_AXIS_REASONS')
        good=r['verdict']=='EQUIVALENT';need(good==all(r['axes'].values()),'REPEAT_EQUIVALENCE')
        if good:need(not set(ids)&set(receipt['uncertain_obligations']),'REPEAT_UNCERTAIN_OWNER')
        tokens={p for p in occurrences if _contained(p,ss)}
        need(type(r['numbers']) is list,'REPEAT_NUMBERS');local=set()
        for n in r['numbers']:
            need(type(n) is dict and set(n)=={'span','owner_id','edge_sha256','reason'} and _note(n['reason']),'REPEAT_NUMBER')
            p=_span(source,n['span']);need(p in tokens and p not in local and p not in seen_num and n['owner_id'] in ids,'REPEAT_NUMBER_OWNER')
            q={json_digest(e):e for e in ob[n['owner_id']]['quantities']};need(n['edge_sha256'] in q,'REPEAT_NUMBER_EDGE')
            target=q[n['edge_sha256']];old=numeric_binding(source,target['parts'],boundary_policy=True);new=numeric_binding(source,[list(p)],boundary_policy=True)
            need(target['role']!='UNKNOWN' and ''.join(old['literal'].split())==''.join(new['literal'].split()),'REPEAT_NUMBER_LITERAL')
            from .semantic_authoring_protocol import _unit_anchored
            if target['role']=='IDENTIFIER':
                i,l,b=p;t=source.cues[i-1].text
                need(any(j==i and ((a<l and t[l-1].isascii() and t[l-1].isalpha()) or (b<c and t[b].isascii() and t[b].isalpha())) for j,a,c in ss),'REPEAT_IDENTIFIER_CONTEXT')
            else:need(_unit_anchored(source,new['literal'],[p],ss,target['unit']),'REPEAT_UNIT')
            local.add(p);seen_num.add(p)
        if good:need(local==tokens,'REPEAT_NUMBER_CENSUS')
        else:opened.extend([list(s) for s in ss])
    need(seen==set(required),'REPEAT_CENSUS')
    # A token crossing review groups is not certified by partial matching.
    unreviewed=occurrences-seen_num
    return {'schema':'IRE_SOURCE_REPEAT_REVIEW_V1','ledger_sha256':receipt['ledger_sha256'],
        'repeat_review_sha256':_rows_digest(rows),'segments':len(required),'open_segments':len(opened),
        'repeat_numeric_occurrences':len(occurrences),'open_numeric_occurrences':len(unreviewed),
        'semantic_equivalence_certified':False}


def _typed_edges(authored):
    return {(f'A{i:05d}',json_digest({'field':field,'edge':e})):(field,e)
        for i,row in enumerate(authored['atoms'],1) for field in ('quantities','relations','temporal') for e in row[field]}


def typed_lineage(source, before, after, graph_lineage, rows):
    """All original typed edges and all successor edges must be accounted for.
    A changed role, unit, premise, or temporal meaning is not an exact carry.
    """
    old,new=_typed_edges(before),_typed_edges(after)
    families={x:set(r['new_ids']) for r in graph_lineage for x in r['old_ids']}
    need(type(rows) is list,'TYPED_LINEAGE_LIST');seen_o=set();seen_n=set();open_count=0
    for r in rows:
        need(type(r) is dict and set(r)=={'old','new','verdict','reason','evidence'} and _note(r['reason']),'TYPED_LINEAGE_ROW')
        a,b=r['old'],r['new'];need(type(a) is list and type(b) is list and len(a) in (0,2) and len(b) in (0,2) and (a or b),'TYPED_LINEAGE_SHAPE')
        a,b=tuple(a),tuple(b);v=r['verdict'];need(v in ('CARRY','REVIEW_CHANGED','RETIRED_UNSUPPORTED','OPEN','ADD'),'TYPED_LINEAGE_VERDICT')
        need((not a or a in old and a not in seen_o) and (not b or b in new and b not in seen_n),'TYPED_LINEAGE_PARTITION')
        need(not (a and b) or b[0] in families[a[0]],'TYPED_LINEAGE_FAMILY')
        if a and b:
            need(v in ('CARRY','REVIEW_CHANGED','OPEN') and old[a][0]==new[b][0],'TYPED_LINEAGE_PAIR')
            need(v!='CARRY' or old[a]==new[b],'TYPED_LINEAGE_FALSE_CARRY')
        elif a:need(v in ('RETIRED_UNSUPPORTED','OPEN'),'TYPED_LINEAGE_RETIRE')
        else:need(v in ('ADD','OPEN'),'TYPED_LINEAGE_ADD')
        ev=spans(source,r['evidence']);es=cells(source,ev)
        for edges,k in ((old,a),(new,b)):
            if k:
                f,e=edges[k];need(cells(source,[_span(source,z) for z in _anchors(f,e)])<=es,'TYPED_LINEAGE_EVIDENCE')
        if a:seen_o.add(a)
        if b:seen_n.add(b)
        open_count+=v=='OPEN'
    need(seen_o==old.keys() and seen_n==new.keys(),'TYPED_LINEAGE_CENSUS')
    return {'sha256':_rows_digest(rows),'old_edges':len(old),'new_edges':len(new),'open_edges':open_count}


def correction_candidate(source, first, authored, first_receipt, ledger, ledger_receipt, initial_score, value):
    from .semantic_graph_journal import _lineage
    need(type(value) is dict and set(value)=={'completion_sha256','initial_score_sha256','ledger_sha256','authored','receipt','assessment','graph_lineage','typed_lineage','repeat_reviews'},'CORRECTION_SCHEMA')
    need(value['completion_sha256']==COMPLETION_SHA256 and value['initial_score_sha256']==json_digest(initial_score) and value['ledger_sha256']==ledger_receipt['ledger_sha256'],'CORRECTION_PINS')
    need(initial_score['first_graph_sha256']==first['packet_sha256'] and initial_score['ledger_sha256']==ledger_receipt['ledger_sha256'],'CORRECTION_PARENT')
    packet,receipt=compile_authoring(source,value['authored']);need(receipt==value['receipt'],'CORRECTION_RECEIPT')
    final=compile_graph(source,packet);need(receipt!=first_receipt,'CORRECTION_UNCHANGED')
    graph=_lineage(source,first,final,value['graph_lineage'])
    for row in value['graph_lineage']:
        if any(first['nodes'][x]['risk']=='HIGH' for x in row['old_ids']):
            need(all(final['nodes'][x]['risk']=='HIGH' for x in row['new_ids']),'CORRECTION_RISK_DOWNGRADE')
    typed=typed_lineage(source,authored,value['authored'],value['graph_lineage'],value['typed_lineage'])
    repeat=review_repeats(source,ledger,value['repeat_reviews'])
    score=audit_bidirectional(source,final,value['authored'],receipt,ledger,ledger_receipt,value['assessment'])
    graph_open=sum(x['disposition']=='OPEN' for x in graph['escrow'])
    ready=score['internal_thresholds_met'] and not (typed['open_edges'] or graph_open or repeat['open_segments'] or repeat['open_numeric_occurrences'])
    return {'schema':'IRE_SOURCE_AUDIT_CORRECTION_CANDIDATE_V1','completion_sha256':COMPLETION_SHA256,
        'initial_score_sha256':json_digest(initial_score),'original_score_changed':False,
        'frozen_ledger_sha256':ledger_receipt['ledger_sha256'],'corrected_graph_sha256':final['packet_sha256'],
        'corrected_receipt_sha256':json_digest(receipt),'corrected_score':score,'graph_lineage':graph,
        'typed_lineage':typed,'repeat_review':repeat,'candidate_internal_thresholds_met':bool(ready),
        'requires_e3_review':True,'financial_approval':False,'independent_gold_verified':False,
        'operational_release_authorized':False,'publication_authorized':False}
