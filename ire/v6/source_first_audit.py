"""Source-first, bidirectional *internal* audit, not an independent gold set.

Source obligations are frozen before the audit mapping is admitted. A reviewer
supplies elemental propositions and evidence; code checks custody, reciprocal
coverage and typed edges. It cannot establish entailment or exhaustive meaning.
"""
from .codec import json_digest
from .errors import InvalidInput
from .gold_eval import MATCH_FIELDS
from .semantic_source_graph import source_grid, _rows_digest, _span, _spans, _note, _contained, numeric_binding
from .semantic_authoring_protocol import occurrence_inventory, ROLE_MAP, PROTOCOL_SHA256

AUDIT_SPEC = {'id':'IRE_SOURCE_FIRST_AUDIT_V1','authoring':PROTOCOL_SHA256,
    'source_unit':'elemental meaning obligation, repeats explicitly linked',
    'prediction_unit':'elemental proposition with parent and typed-edge custody',
    'mapping':'one-to-one elemental pairs; parent nodes may split or merge',
    'thresholds':{'precision_bp':9500,'recall_bp':9800,'high_risk_unresolved_max':0},
    'axes':list(MATCH_FIELDS),'relation_matching':'explicit reciprocal grouped relation mapping with evidence','unresolved':'explicit OPEN blocks perfect match','internal_only':True}
AUDIT_SHA256 = json_digest(AUDIT_SPEC)


def need(ok, label):
    if not ok: raise InvalidInput('SOURCE_AUDIT_'+label)


def cells(source, spans):
    return {(i,k) for i,a,b in spans for k in range(a,b) if not source.cues[i-1].text[k].isspace()}


def spans(source, values):
    s=_spans(source,values,nonempty=True)
    need(bool(cells(source,s)),'EMPTY_EVIDENCE')
    return s


def _attrs(row):
    need(type(row) is dict and set(row)==set(MATCH_FIELDS) and all(_note(v) for v in row.values()),'AXIS_DESCRIPTIONS')


def _edge_sig(source, field, edge):
    if field=='quantities':
        need(type(edge) is dict and set(edge)=={'parts','role','unit','anchor','reason'} and edge['role'] in ROLE_MAP and type(edge['unit']) is str and _note(edge['reason']),'QUANTITY')
        v=numeric_binding(source,edge['parts'],boundary_policy=True)
        from .semantic_authoring_protocol import _unit_anchored
        p=[tuple(x) for x in v['parts']];a=spans(source,edge['anchor'])
        need(all(_contained(x,a) for x in p),'QUANTITY_ANCHOR')
        if edge['role']=='UNKNOWN': need(edge['unit']=='UNKNOWN','UNKNOWN_UNIT')
        elif edge['role']=='IDENTIFIER':
            i,l,r=p[0];t=source.cues[i-1].text
            need(len(p)==1 and edge['unit']=='' and any(j==i and ((x<l and t[l-1].isascii() and t[l-1].isalpha()) or (r<y and t[r].isascii() and t[r].isalpha())) for j,x,y in a),'IDENTIFIER')
        else: need(_unit_anchored(source,v['literal'],p,a,edge['unit']),'UNIT')
        return (edge['role'],edge['unit'],''.join(v['literal'].split()))
    if field=='temporal':
        from .semantic_authoring_protocol import PROTOCOL
        need(type(edge) is dict and set(edge)=={'type','span','reason'} and edge['type'] in PROTOCOL['temporal'] and _note(edge['reason']),'TIME')
        i,a,b=_span(source,edge['span']);return (edge['type'],source.cues[i-1].text[a:b])
    need(type(edge) is dict and set(edge)=={'type','premise','consequent','reason'} and edge['type'] in ('CONDITION','EXCEPTION') and _note(edge['reason']),'RELATION')
    p=spans(source,edge['premise']);c=spans(source,edge['consequent'])
    need(not cells(source,p)&cells(source,c),'RELATION_OVERLAP')
    return (edge['type'],)


def _anchors(field,e):
    return e['anchor'] if field=='quantities' else [e['span']] if field=='temporal' else e['premise']+e['consequent']


def freeze_source_ledger(source, ledger):
    need(type(ledger) is dict and set(ledger)=={'audit_sha256','grid_sha256','segments','obligations','occurrences'} and ledger['audit_sha256']==AUDIT_SHA256 and ledger['grid_sha256']==json_digest(source_grid(source)),'LEDGER_PIN')
    need(all(type(ledger[k]) is list for k in ('segments','obligations','occurrences')),'LEDGER_LIST')
    ob={};owner_cells={};num_owners={};unknown=set()
    for n,row in enumerate(ledger['obligations'],1):
        k=f'O{n:05d}'
        need(type(row) is dict and set(row)=={'id','predicate','nucleus','context','risk','reason','resolution','axes','quantities','relations','temporal'} and row['id']==k and _note(row['predicate']) and _note(row['reason']) and row['risk'] in ('HIGH','NORMAL'),'OBLIGATION')
        need(row['resolution'] in ('RESOLVED','OPEN'),'OBLIGATION_RESOLUTION')
        if row['resolution']=='OPEN':unknown.add(k)
        _attrs(row['axes']);nucleus=spans(source,row['nucleus']);context=_spans(source,row['context']);scope=nucleus+context
        owner_cells[k]=cells(source,nucleus);ob[k]=row
        for field in ('quantities','relations','temporal'):
            need(type(row[field]) is list and len({json_digest(e) for e in row[field]})==len(row[field]),'EDGE_LIST')
            for edge in row[field]:
                _edge_sig(source,field,edge)
                need(all(_contained(_span(source,s),scope) for s in _anchors(field,edge)),'EDGE_OUTSIDE_OBLIGATION')
                if field=='relations':need(all(_contained(_span(source,s),nucleus) for s in edge['consequent']),'CONSEQUENT_OWNER')
                if field=='quantities':
                    if edge['role']=='UNKNOWN':unknown.add(k)
                    for p in edge['parts']:
                        part=tuple(p);owners=num_owners.setdefault(part,{})
                        need(k not in owners,'DUPLICATE_NUMERIC_OWNER');owners[k]=edge['role']
    need(bool(ob),'NO_OBLIGATIONS')
    covered={};open_chars=0;linked=set()
    for row in ledger['segments']:
        need(type(row) is dict and set(row)=={'span','status','owners','reason'} and _note(row['reason']),'SEGMENT')
        cs=cells(source,[_span(source,row['span'])]);ids=row['owners'];status=row['status']
        need(bool(cs) and not cs&covered.keys() and type(ids) is list and ids==sorted(set(ids)) and set(ids)<=ob.keys(),'SEGMENT_CENSUS')
        if status=='OBLIGATION':
            need(bool(ids) and all(cs<=owner_cells[k] for k in ids),'NUCLEUS_OWNER');linked.update(ids)
        elif status in ('CONTEXT','REPEAT'):
            need(bool(ids) and all(cs<=cells(source,_spans(source,ob[k]['context'])) for k in ids),'CONTEXT_OWNER')
        elif status in ('NONCLAIM','OPEN'):
            need(not ids,'RESIDUAL_OWNER');open_chars+=len(cs) if status=='OPEN' else 0
        else: need(False,'SEGMENT_STATUS')
        covered.update((x,status) for x in cs)
    need(covered.keys()=={(i,k) for i,c in enumerate(source.cues,1) for k,ch in enumerate(c.text) if not ch.isspace()} and linked==ob.keys(),'SOURCE_CENSUS')
    for k,row in ob.items():
        need(all(covered[x]=='OBLIGATION' for x in owner_cells[k]),'NUCLEUS_DISPOSITION')
        need(all(covered[x] in ('CONTEXT','REPEAT','OBLIGATION') for x in cells(source,_spans(source,row['context']))),'CONTEXT_DISPOSITION')
    expected={tuple(s) for s in occurrence_inventory(source)};seen=set();open_numbers=0
    for r in ledger['occurrences']:
        need(type(r) is dict and set(r)=={'span','status','owners','reason'} and _note(r['reason']),'OCCURRENCE')
        sp=_span(source,r['span']);ids=r['owners'];status=r['status']
        need(sp in expected and sp not in seen and type(ids) is list and ids==sorted(set(ids)),'OCCURRENCE_CENSUS');seen.add(sp)
        found={k:role for p,owners in num_owners.items() if _contained(sp,[p]) for k,role in owners.items()}
        need(set(ids)==found.keys(),'OCCURRENCE_OWNER')
        if status=='OPEN':open_numbers+=1
        elif status in ('QUANTITY','IDENTIFIER'):
            need(bool(found) and all(role!='UNKNOWN' and (role=='IDENTIFIER')==(status=='IDENTIFIER') for role in found.values()),'OCCURRENCE_BINDING')
        elif status in ('NONCLAIM','CONTEXT','REPEAT'):
            need(not found and {covered[x] for x in cells(source,[sp])}=={status},'OCCURRENCE_DISPOSITION')
        else:need(False,'OCCURRENCE_STATUS')
    need(seen==expected,'OCCURRENCE_CENSUS')
    for part in num_owners:
        i,a,b=part
        need(any(_contained(sp,[part]) for sp in expected) or not any(ch.isdecimal() for ch in source.cues[i-1].text[a:b]),'BINDING_WITHOUT_OCCURRENCE')
    return {'schema':'IRE_SOURCE_AUDIT_LEDGER_RECEIPT_V1','audit_sha256':AUDIT_SHA256,'grid_sha256':ledger['grid_sha256'],
        'ledger_sha256':_rows_digest([{'audit':AUDIT_SHA256,'grid':ledger['grid_sha256']},*ledger['segments'],*ledger['obligations'],*ledger['occurrences']]),
        'obligations':len(ob),'numeric_occurrences':len(expected),'open_numeric_occurrences':open_numbers,'open_source_characters':open_chars,
        'uncertain_obligations':sorted(unknown),'semantic_completeness_certified':False}


def _first_elements(source, first, authored, elements):
    need(type(elements) is list and bool(elements),'FIRST_ELEMENTS')
    nodes=first['nodes'];parents={k:[] for k in nodes};out={}
    for i,r in enumerate(elements,1):
        k=f'P{i:05d}'
        need(type(r) is dict and set(r)=={'id','parent_id','predicate','evidence','risk','reason','axes','edge_ids'} and r['id']==k and r['parent_id'] in nodes and _note(r['predicate']) and _note(r['reason']),'FIRST_ELEMENT')
        p=r['parent_id'];node=nodes[p];_attrs(r['axes']);ev=spans(source,r['evidence'])
        scope=[tuple(s) for s in node['direct']+node['context']+[q['span'] for q in node['qualifiers']]]
        need(all(_contained(s,scope) for s in ev) and bool(cells(source,ev)&cells(source,[tuple(s) for s in node['direct']])),'FIRST_ELEMENT_EVIDENCE')
        need(r['risk'] in ('HIGH','NORMAL') and (node['risk']!='HIGH' or r['risk']=='HIGH'),'RISK_DOWNGRADE')
        ids=r['edge_ids'];need(type(ids) is list and ids==sorted(set(ids)),'FIRST_EDGE_IDS')
        typed=authored['atoms'][int(p[1:])-1];edges={json_digest({'field':f,'edge':e}):(f,e) for f in ('quantities','relations','temporal') for e in typed[f]}
        need(set(ids)<=edges.keys(),'FIRST_EDGE_UNKNOWN')
        for h in ids:need(all(_contained(_span(source,s),ev) for s in _anchors(*edges[h])),'FIRST_EDGE_EVIDENCE')
        parents[p].append(r);out[k]=(r,edges)
    for p,rows in parents.items():
        need(bool(rows),'FIRST_PARENT_CENSUS')
        typed=authored['atoms'][int(p[1:])-1];required={json_digest({'field':f,'edge':e}) for f in ('quantities','relations','temporal') for e in typed[f]}
        need(set(h for r in rows for h in r['edge_ids'])==required,'FIRST_EDGE_CENSUS')
        direct=cells(source,[tuple(s) for s in nodes[p]['direct']]);actual=set().union(*(cells(source,spans(source,r['evidence'])) for r in rows))
        need(direct<=actual,'FIRST_DIRECT_CENSUS')
    return out


def audit_bidirectional(source, first, authored, first_receipt, ledger, ledger_receipt, assessment):
    need(freeze_source_ledger(source,ledger)==ledger_receipt,'LEDGER_RECEIPT')
    need(type(assessment) is dict and set(assessment)=={'first_graph_sha256','first_receipt_sha256','ledger_sha256','elements','pairs','source_unmatched','first_unmatched'},'ASSESSMENT')
    need(assessment['first_graph_sha256']==first['packet_sha256'] and assessment['first_receipt_sha256']==json_digest(first_receipt) and assessment['ledger_sha256']==ledger_receipt['ledger_sha256'],'ASSESSMENT_PIN')
    ob={r['id']:r for r in ledger['obligations']};pred=_first_elements(source,first,authored,assessment['elements']);seen_o=set();seen_p=set();tp=0;high_o=set();high_p=set()
    need(all(type(assessment[k]) is list for k in ('pairs','source_unmatched','first_unmatched')),'ASSESSMENT_LIST')
    for r in assessment['pairs']:
        need(type(r) is dict and set(r)=={'source_id','first_id','axes','reasons','source_evidence','first_evidence','source_verdict','first_verdict','relation_pairs'},'PAIR')
        o,p=r['source_id'],r['first_id'];need(o in ob and p in pred and o not in seen_o and p not in seen_p,'PAIR_PARTITION');seen_o.add(o);seen_p.add(p)
        a,b=ob[o],pred[p][0];axes=r['axes'];need(type(axes) is dict and set(axes)==set(MATCH_FIELDS) and all(type(v) is bool for v in axes.values()),'PAIR_AXES');_attrs(r['reasons'])
        ev_o=spans(source,r['source_evidence']);ev_p=spans(source,r['first_evidence'])
        need(cells(source,_spans(source,a['nucleus']))<=cells(source,ev_o) and cells(source,_spans(source,b['evidence']))<=cells(source,ev_p),'PAIR_EVIDENCE')
        need(all(_contained(s,_spans(source,a['nucleus'])+_spans(source,a['context'])) for s in ev_o) and all(_contained(s,_spans(source,b['evidence'])) for s in ev_p),'PAIR_EVIDENCE_SCOPE')
        good=all(axes.values());need(not good or (o not in ledger_receipt['uncertain_obligations'] and b['parent_id'] not in first_receipt['uncertain_atoms']),'UNRESOLVED_MATCH')
        for f,axis in (('quantities','numeric_value_and_unit'),('temporal','temporal_scope'),('relations','conditions')):
            for edge in a[f]:
                ax=('exceptions' if edge['type']=='EXCEPTION' else 'conditions') if f=='relations' else axis
                if axes[ax]:need(all(_contained(_span(source,z),ev_o) for z in _anchors(f,edge)),'PAIR_EDGE_EVIDENCE')
        need((r['source_verdict']=='PRESERVED')==good and (r['first_verdict']=='SUPPORTED')==good and r['source_verdict'] in ('PRESERVED','CONFLICT','OPEN') and r['first_verdict'] in ('SUPPORTED','CONFLICT','OPEN'),'RECIPROCAL_VERDICT')
        for field,axis in (('quantities','numeric_value_and_unit'),('temporal','temporal_scope'),('relations','conditions')):
            old=[e for h,(f,e) in pred[p][1].items() if h in b['edge_ids'] and f==field]
            left=sorted(_edge_sig(source,field,e) for e in old);right=sorted(_edge_sig(source,field,e) for e in a[field])
            if field=='relations':
                for typ,ax in (('CONDITION','conditions'),('EXCEPTION','exceptions')):
                    need(not axes[ax] or left.count((typ,))==right.count((typ,)),'CONTRADICTORY_RELATION')
            else:need(not axes[axis] or left==right,'CONTRADICTORY_'+field.upper())
        old_rel={h:e for h,(f,e) in pred[p][1].items() if f=='relations' and h in b['edge_ids']}
        new_rel={json_digest(e):e for e in a['relations']};seen_old=set();seen_new=set()
        need(type(r['relation_pairs']) is list,'RELATION_PAIRS')
        for link in r['relation_pairs']:
            need(type(link) is dict and set(link)=={'first_edge_sha256','source_edge_sha256','reason'} and _note(link['reason']),'RELATION_PAIR')
            x,y=link['first_edge_sha256'],link['source_edge_sha256']
            need(x in old_rel and y in new_rel and x not in seen_old and y not in seen_new and old_rel[x]['type']==new_rel[y]['type'],'RELATION_PAIR_CUSTODY');seen_old.add(x);seen_new.add(y)
            typ=old_rel[x]['type'];need(axes['conditions' if typ=='CONDITION' else 'exceptions'],'RELATION_PAIR_FALSE_AXIS')
        for typ,ax in (('CONDITION','conditions'),('EXCEPTION','exceptions')):
            if axes[ax]:need({x for x,e in old_rel.items() if e['type']==typ}<=seen_old and {y for y,e in new_rel.items() if e['type']==typ}<=seen_new,'RELATION_PAIR_CENSUS')
        if good:tp+=1
        else:
            if a['risk']=='HIGH':high_o.add(o)
            if b['risk']=='HIGH':high_p.add(p)
    for field,rows,seen,high,allowed in (('source_unmatched',ob,seen_o,high_o,('MISSING','OPEN')),('first_unmatched',{k:v[0] for k,v in pred.items()},seen_p,high_p,('UNSUPPORTED','OPEN'))):
        for r in assessment[field]:
            need(type(r) is dict and set(r)=={'id','verdict','reason','evidence'} and r['id'] in rows and r['id'] not in seen and r['verdict'] in allowed and _note(r['reason']),'UNMATCHED')
            k=r['id'];a=rows[k];seen.add(k);base=a.get('nucleus',a.get('evidence'));ev=spans(source,r['evidence'])
            need(cells(source,_spans(source,base))<=cells(source,ev),'UNMATCHED_EVIDENCE')
            if a['risk']=='HIGH':high.add(k)
        need(seen==rows.keys(),'BIDIRECTIONAL_CENSUS')
    precision=tp*10000//len(pred);recall=tp*10000//len(ob)
    blockers={'source_open_chars':ledger_receipt['open_source_characters'],'source_open_numeric':ledger_receipt['open_numeric_occurrences'],'source_uncertain':len(ledger_receipt['uncertain_obligations']),
      'first_open_chars':first_receipt['character_dispositions'].get('OPEN',0),'first_open_numeric':first_receipt['open_numeric_occurrences'],'first_uncertain':len(first_receipt['uncertain_atoms']), 'first_unbound_numeric':first_receipt['unbound_numeric_spans'],'first_boundary_warnings':first_receipt['boundary_warnings']}
    return {'schema':'IRE_SOURCE_AUDIT_INTERNAL_SCORE_V1','ledger_sha256':ledger_receipt['ledger_sha256'],'first_graph_sha256':first['packet_sha256'],
      'assessment_sha256':_rows_digest([*assessment['elements'],*assessment['pairs'],*assessment['source_unmatched'],*assessment['first_unmatched']]),
      'tp':tp,'fp':len(pred)-tp,'fn':len(ob)-tp,'precision_bp':precision,'recall_bp':recall,'high_risk_source_unmatched_or_conflict':len(high_o),'high_risk_first_unmatched_or_conflict':len(high_p),
      'blockers':blockers,'internal_thresholds_met':precision>=9500 and recall>=9800 and not high_o and not high_p and not any(blockers.values()),
      'independent_gold_verified':False,'semantic_truth_certified':False,'operational_release_authorized':False,'publication_authorized':False}
