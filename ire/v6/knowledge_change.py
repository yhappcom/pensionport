"""Evidence-bound, unapproved knowledge change proposals; never a merge gate."""
from .codec import json_digest, require_hash
from .errors import InvalidInput
from .atomic_exchange import _digest_rows


def audit_knowledge_change(previous, current, predecessor_sha, prior_digest, rows, plan):
    """Require exact source/target identity and unchanged native relation rows.

    External evidence is a reference, not an authenticated finance fact.
    The plan cannot release quarantine or rewrite source/active knowledge.
    """
    def need(ok, code):
        if not ok:
            raise InvalidInput('HOST_KNOWLEDGE_CHANGE_' + code)
    require_hash(predecessor_sha)
    require_hash(prior_digest)
    need(previous == current, 'SOURCE_RECORD_CHANGED')
    need(_digest_rows(rows) == prior_digest, 'PRIOR_ROWS_CHANGED')
    need(type(plan) is dict and set(plan) == {'schema','predecessor_event_sha256','rows'} and plan['schema'] == 'IRE_V6_KNOWLEDGE_CHANGE_PLAN_V1' and plan['predecessor_event_sha256'] == predecessor_sha, 'PLAN_SCHEMA_OR_HEAD')
    pending = plan['rows']
    need(type(pending) is list and 0 < len(pending) <= 20000, 'CENSUS')
    indexed = {json_digest(r):r for r in rows if r['relationship'] == 'OPEN'}
    atoms = {r['claim_id']:r for r in current['exchange']['atoms']}
    quarantine = {r['claim_id'] for r in current['ledger']['quarantine_atoms']}
    seen = set()
    counts = {'EXTEND':0, 'CORRECT_SOURCE_CANDIDATE':0, 'RETAIN_OPEN':0}
    for r in pending:
        need(type(r) is dict and set(r) == {'prior_row_sha256','native_atom_sha256','operation','reason','evidence_urls'}, 'ROW_SCHEMA')
        key = require_hash(r['prior_row_sha256'])
        need(key in indexed and key not in seen, 'ROW_IDENTITY')
        seen.add(key)
        cid = indexed[key]['claim_id']
        need(r['native_atom_sha256'] == json_digest(atoms[cid]), 'ATOM_DRIFT')
        op = r['operation']
        need(type(op) is str and op in counts, 'OPERATION')
        need(type(r['reason']) is str and 8 <= len(r['reason'].strip()) <= 2000, 'REASON')
        urls = r['evidence_urls']
        need(type(urls) is list and len(urls) <= 20 and all(type(u) is str and u.startswith('https://') and 12 < len(u) <= 2000 for u in urls) and len(set(urls)) == len(urls), 'EVIDENCE_REFERENCE')
        if op != 'RETAIN_OPEN':
            need(cid not in quarantine and bool(urls), 'QUARANTINE_OR_EVIDENCE')
        counts[op] += 1
    need(seen == set(indexed), 'OPEN_CENSUS_LOSS')
    return {'schema':'IRE_V6_KNOWLEDGE_CHANGE_RECEIPT_V1', 'predecessor_event_sha256':predecessor_sha, 'prior_relation_digest':prior_digest, 'plan_sha256':json_digest(plan), 'counts':counts, 'finance_evidence_authenticated':False, 'active_knowledge_changed':False, 'formal_v123_input_authorized':False, 'p0_go':False}
