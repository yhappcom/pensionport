"""Source-bound arithmetic sidecar. Arithmetic is not a financial-law verdict.

Only explicitly unit-bearing source literals are operands. Calendar conversion
is a separate fixed constant, not a fabricated source token. A unitless reported
result is kept unresolved; it is never overwritten with the derived value.
"""
import re
from fractions import Fraction
from .codec import json_digest, sha256
from .semantic_source_graph import compile_graph, _span, _rows_digest
from .semantic_obligation_review import need


def _value(literal):
    t = re.sub(r'\s+', '', literal)
    m = re.fullmatch(r'(\d+(?:\.\d+)?)%', t)
    if m:
        return 'RATE', Fraction(m[1])/100
    m = re.fullmatch(r'(\d{1,3}(?:,\d{3})+|\d+)(천만|백만|십만|만|천|백|십|억)?원', t)
    if m:
        scale = {None:1, '십':10, '백':100, '천':1000, '만':10000, '십만':100000,
                 '백만':1000000, '천만':10000000, '억':100000000}[m[2]]
        return 'KRW', Fraction(int(m[1].replace(',', ''))*scale)
    return 'UNRESOLVED', None


def verify_calculations(source, packet, rows, *, expected_packet_sha256):
    graph = compile_graph(source, packet)
    need(graph['packet_sha256'] == expected_packet_sha256, 'CALC_PACKET_PIN')
    need(type(rows) is list and bool(rows), 'CALC_ROWS')
    nodes = graph['nodes']; seen = set(); outputs = []
    def ref(r):
        need(type(r) is dict and set(r) == {'node_id','edge_index','edge_sha256'}, 'CALC_REF')
        k = r['node_id']; i = r['edge_index']
        need(k in nodes and type(i) is int and 1 <= i <= len(nodes[k]['numbers']), 'CALC_EDGE_INDEX')
        e = nodes[k]['numbers'][i-1]
        need(json_digest(e) == r['edge_sha256'], 'CALC_EDGE_PIN')
        return e, _value(e['literal'])
    for row in rows:
        need(type(row) is dict and set(row) == {'id','operation','inputs','reported','scope_evidence','reason'}, 'CALC_ROW')
        k = row['id']; op = row['operation']
        need(type(k) is str and k and k not in seen and type(row['reason']) is str and len(row['reason'].strip()) >= 10, 'CALC_ID'); seen.add(k)
        need(op in ('MULTIPLY_RATE','SUBTRACT','ADD','ANNUAL_TO_MONTHLY'), 'CALC_OPERATION')
        refs = row['inputs']; need(type(refs) is list and len(refs) == (1 if op=='ANNUAL_TO_MONTHLY' else 2), 'CALC_INPUT_COUNT')
        allrefs = refs+[row['reported']]
        pairs = [ref(r) for r in allrefs]
        need(len({json_digest(r) for r in allrefs}) == len(allrefs), 'CALC_DUPLICATE_EDGE')
        # A single physical source token cannot be counted twice via two nodes.
        tokens = [tuple(p) for e,_ in pairs for p in e['parts']]
        need(len(tokens)==len(set(tokens)), 'CALC_REUSED_SOURCE_TOKEN')
        # Repeated instances of the same literal are not summed automatically.
        inputs = [p[1] for p in pairs[:-1]]; reported = pairs[-1][1]
        need(inputs[0][0]=='KRW', 'CALC_INPUT_UNIT')
        a = inputs[0][1]
        scope = row['scope_evidence']; need(type(scope) is list and bool(scope), 'CALC_SCOPE')
        anchors = [p for e,_ in pairs for p in e['parts']]
        involved = [d for r in allrefs for d in nodes[r['node_id']]['direct']]
        scope_text=[]; scope_spans=[]
        for ev in scope:
            need(type(ev) is dict and set(ev)=={'span','text_sha256'}, 'CALC_SCOPE_SCHEMA')
            i,l,r = _span(source,ev['span']); t=source.cues[i-1].text[l:r]
            need(sha256(t.encode())==ev['text_sha256'], 'CALC_SCOPE_BYTES')
            need(any(i==j and max(l,x)<min(r,y) for j,x,y in anchors+involved), 'CALC_SCOPE_UNRELATED')
            scope_text.append(t); scope_spans.append([i,l,r])
        need(all(any(i==j and x<=l and r<=y for j,x,y in scope_spans) for i,l,r in anchors), 'CALC_MISSING_OPERAND_SCOPE')
        if op=='ANNUAL_TO_MONTHLY':
            need(any(re.search(r'(연\s*$|연간|1년)',t) for t in scope_text) and any('월' in t or '달' in t for t in scope_text),'CALC_PERIOD_EVIDENCE')
            result=a/12; constant={'kind':'CALENDAR_MONTHS_PER_YEAR','value':12}
        else:
            b=inputs[1][1]; constant=None
            need(inputs[1][0]==('RATE' if op=='MULTIPLY_RATE' else 'KRW'),'CALC_INPUT_UNIT')
            result=a*b if op=='MULTIPLY_RATE' else a-b if op=='SUBTRACT' else a+b
        status=('REPORTED_UNIT_UNRESOLVED' if reported[0]=='UNRESOLVED' else
                'ARITHMETIC_MATCH' if reported[0]=='KRW' and reported[1]==result else 'ARITHMETIC_MISMATCH')
        outputs.append({'id':k,'row_sha256':json_digest(row),'derived_krw_numerator':str(result.numerator),
                        'derived_krw_denominator':str(result.denominator),'reported_literal':pairs[-1][0]['literal'],
                        'status':status,'conversion_constant':constant,'financial_approval':False})
    return {'schema':'IRE_V3_CALCULATION_LINEAGE_V1','packet_sha256':expected_packet_sha256,
            'rows_sha256':_rows_digest(rows),'results':outputs,'semantic_conservation_verified':False,
            'publication_authorized':False,'financial_approval':False}
