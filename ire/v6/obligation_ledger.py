"""Replay legacy obligation tranches and shared-scope amendments in one chain.

Development migration only: not an actual V3 two-turn journal or approval.
An independently retained head binds the exact history on reopen.
"""
from collections import Counter
from copy import deepcopy
from .codec import json_digest, require_hash
from .semantic_source_graph import compile_graph, _rows_digest
from .semantic_obligation_review import review_batch, need
from .shared_qualifier_review import review_shared_qualifiers


def _run(source, packet, old, candidates, events, pins):
    g = compile_graph(source, packet)
    single = []
    shared = {}
    effective = {}
    head = json_digest({'schema': 'IRE_V3_LEGACY_OBLIGATION_LEDGER_V1',
                        'source_sha256': source.source_sha256, 'pins': pins})
    receipt = review_batch(source, g, old, candidates, single, **pins)
    for i, event in enumerate(events, 1):
        need(type(event) is dict and set(event) == {'kind', 'previous', 'rows', 'receipt_sha256', 'head'}, 'LEDGER_EVENT')
        need(event['previous'] == head and type(event['rows']) is list and bool(event['rows']), 'LEDGER_CHAIN')
        rows = event['rows']
        keys = [r['old_sha256'] for r in rows]
        need(len(keys) == len(set(keys)), 'LEDGER_DUPLICATE')
        if event['kind'] == 'SINGLE':
            need(not set(keys) & set(effective), 'LEDGER_ALREADY_REVIEWED')
            single += rows
            receipt = review_batch(source, g, old, candidates, single, **pins)
            result = receipt
            for row in rows:
                effective[row['old_sha256']] = row['decision']
        elif event['kind'] == 'SHARED':
            need(not set(keys) & set(shared), 'LEDGER_SHARED_ALREADY_REVIEWED')
            result = review_shared_qualifiers(source, packet, old, candidates, single, receipt, rows,
                                               expected_prior_receipt_sha256=json_digest(receipt), **pins)
            for row in result['results']:
                k = row['old_sha256']
                shared[k] = row
                effective[k] = 'OPEN' if row['status'] == 'OPEN' else ('MULTI_TARGET' if len(row['applied_edges']) > 1 else 'CARRY_SOURCE_EDGE')
        else:
            need(False, 'LEDGER_KIND')
        need(event['receipt_sha256'] == json_digest(result), 'LEDGER_RECEIPT')
        head = json_digest({'seq': i, 'kind': event['kind'], 'previous': head,
                            'rows_sha256': _rows_digest(rows), 'receipt_sha256': event['receipt_sha256']})
        need(event['head'] == head, 'LEDGER_HEAD')
    return g, single, receipt, effective, shared, head


def replay(source, packet, old, candidates, events, *, expected_head, **pins):
    require_hash(expected_head, 'OBLIGATION_LEDGER_EXTERNAL_HEAD')
    g, _, _, effective, shared, head = _run(source, packet, old, candidates, events, pins)
    need(head == expected_head, 'LEDGER_EXTERNAL_HEAD')
    counts = dict(Counter(effective.values()))
    return {'head': head, 'events': len(events), 'reviewed': len(effective),
            'remaining': len(old)-len(effective), 'effective_counts': counts,
            'shared_obligations': len(shared), 'open_characters': g['character_dispositions'].get('OPEN', 0),
            'unbound_numeric_spans': len(g['unbound_numeric_spans']),
            'actual_two_turn_verified': False, 'semantic_conservation_verified': False,
            'publication_authorized': False, 'ready_for_e3': False}


def genesis(source, **pins):
    return json_digest({'schema': 'IRE_V3_LEGACY_OBLIGATION_LEDGER_V1',
                        'source_sha256': source.source_sha256, 'pins': pins})


def append(source, packet, old, candidates, events, kind, rows, *, expected_head, **pins):
    require_hash(expected_head, 'OBLIGATION_LEDGER_EXTERNAL_HEAD')
    g, single, receipt, effective, shared, head = _run(source, packet, old, candidates, events, pins)
    need(head == expected_head, 'LEDGER_EXTERNAL_HEAD')
    need(type(rows) is list and bool(rows), 'LEDGER_ROWS')
    keys = [r['old_sha256'] for r in rows]
    need(len(keys) == len(set(keys)), 'LEDGER_DUPLICATE')
    if kind == 'SINGLE':
        need(not set(keys) & set(effective), 'LEDGER_ALREADY_REVIEWED')
        result = review_batch(source, g, old, candidates, single + rows, **pins)
    elif kind == 'SHARED':
        need(not set(keys) & set(shared), 'LEDGER_SHARED_ALREADY_REVIEWED')
        result = review_shared_qualifiers(source, packet, old, candidates, single, receipt, rows,
                                           expected_prior_receipt_sha256=json_digest(receipt), **pins)
    else:
        need(False, 'LEDGER_KIND')
    digest = json_digest(result)
    new_head = json_digest({'seq': len(events)+1, 'kind': kind, 'previous': head,
                            'rows_sha256': _rows_digest(rows), 'receipt_sha256': digest})
    new_events = deepcopy(events) + [{'kind': kind, 'previous': head, 'rows': deepcopy(rows),
                                     'receipt_sha256': digest, 'head': new_head}]
    replay(source, packet, old, candidates, new_events, expected_head=new_head, **pins)
    return new_events, new_head
