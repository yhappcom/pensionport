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


def prepare_host_knowledge_change_review(store, *, scope_id, run_id, raw,
                                         manifest, inventory_bytes,
                                         expected_inventory_sha256,
                                         review, evidence_inputs):
    """Materialize a review-only change draft from the current *native* seal.

    A source interpretation correction is not authority to edit its routed
    Master/P4 target. Official captures are checked for bytes, URL, quote and
    effective date, without claiming independent origin or semantic truth.
    Neither this function nor its returned packet is an approval/publisher.
    """
    from .host_batch import read_host_typed_staging
    from .finance import audit_official_candidate

    def need(ok, code):
        if not ok:
            raise InvalidInput('HOST_KNOWLEDGE_REVIEW_' + code)

    staged = read_host_typed_staging(store, scope_id=scope_id, run_id=run_id,
        raw=raw, manifest=manifest, inventory_bytes=inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256)
    pin = staged.get('knowledge_change_pin')
    plan = staged.get('knowledge_change_plan')
    native_rows = staged.get('knowledge_change_rows')
    need(type(pin) is dict and type(plan) is dict and type(native_rows) is list,
         'PENDING_NATIVE_PLAN_REQUIRED')
    record = staged['record']
    need(audit_knowledge_change(record, record, pin['predecessor_event_sha256'],
        pin['prior_relation_digest'], native_rows, plan) == pin, 'PLAN_REPLAY_DRIFT')
    need(type(review) is dict and set(review) == {
        'schema','host_event_sha256','plan_sha256','as_of','rows'} and
        review['schema'] == 'IRE_V6_KNOWLEDGE_CHANGE_REVIEW_DRAFT_V1' and
        review['host_event_sha256'] == staged['event_sha256'] and
        review['plan_sha256'] == pin['plan_sha256'], 'PLAN_OR_CURRENT_HEAD')
    from .finance import _as_date
    _as_date(review['as_of'], 'HOST_KNOWLEDGE_REVIEW_AS_OF')
    need(type(review['rows']) is list and type(evidence_inputs) is dict,
         'INPUT_SCHEMA')
    indexed = {json_digest(r):r for r in native_rows}
    atoms = {a['claim_id']:a for a in record['exchange']['atoms']}
    plans = {r['prior_row_sha256']:r for r in plan['rows']}
    projections = {r['claim_id']:r for r in record['ledger']['projection_rows']}
    typed_atoms = {f'A{i:05d}':a for i,a in enumerate(record['ledger']['authored']['atoms'],1)}
    seen, output, used = set(), [], set()
    captures, missing, missing_urls = 0, 0, 0
    for row in review['rows']:
        need(type(row) is dict and set(row) == {'prior_row_sha256','operation',
             'proposed_proposition','scope_note','evidence_refs'}, 'ROW_SCHEMA')
        key = require_hash(row['prior_row_sha256'])
        need(key in plans and key not in seen, 'ROW_IDENTITY')
        seen.add(key)
        pending, prior = plans[key], indexed[key]
        cid, op = prior['claim_id'], pending['operation']
        need(row['operation'] == op, 'OPERATION_DRIFT')
        atom = atoms[cid]
        refs = row['evidence_refs']
        need(type(refs) is list and len(refs)<=20 and all(type(v) is str for v in refs)
             and len(set(refs))==len(refs), 'EVIDENCE_REFS')
        need(type(row['scope_note']) is str and 8<=len(row['scope_note'].strip())<=2000,
             'SCOPE_NOTE_REQUIRED')
        if op == 'RETAIN_OPEN':
            need(row['proposed_proposition'] is None and not refs,
                 'OPEN_CANNOT_EMIT_KNOWLEDGE')
        else:
            need(type(row['proposed_proposition']) is str and
                 8<=len(row['proposed_proposition'].strip())<=3000,
                 'PROPOSED_KNOWLEDGE_REQUIRED')
        receipts, bound_urls = [], set()
        for ref in refs:
            need(ref in evidence_inputs and ref not in used, 'EVIDENCE_IDENTITY')
            item = evidence_inputs[ref]
            need(type(item) is dict and set(item)=={'document_raw','document_sha256',
                 'proposal','capture_kind','evidence_role'} and
                 item['capture_kind'] in {'DECODED_HTML_CAPTURE','DECLARED_ORIGIN_HTTP_BYTES'} and
                 item['evidence_role'] in {'SUPPORT','COUNTEREXAMPLE','SCOPE_LIMIT'},
                 'EVIDENCE_SCHEMA')
            prop = item['proposal']
            need(type(prop) is dict and prop.get('claim_id')==cid and
                 prop.get('url') in pending['evidence_urls'], 'EVIDENCE_WRONG_CLAIM_OR_URL')
            need(op!='EXTEND' or item['evidence_role']!='COUNTEREXAMPLE',
                 'EVIDENCE_ROLE_MISMATCH')
            result = audit_official_candidate(item['document_raw'],prop,
                        expected_document_sha256=item['document_sha256'],as_of=review['as_of'])
            need(result['effective_at_as_of'], 'EVIDENCE_DATE_NOT_APPLICABLE')
            receipts.append({'capture_kind':item['capture_kind'],
                'role':item['evidence_role'],'candidate_audit':result})
            bound_urls.add(prop['url']); used.add(ref); captures+=1
        if op != 'RETAIN_OPEN':
            missing+=int(not receipts)
            missing_urls+=len(set(pending['evidence_urls'])-bound_urls)
        typed=typed_atoms[projections[cid]['typed_id']]
        output.append({'prior_row_sha256':key,'claim_id':cid,
            'source_atom_sha256':json_digest(atom),
            'typed_atom_sha256':json_digest(typed),
            'prior_target_id':prior['target_id'],
            'prior_target_content_sha256':prior['target_content_sha256'],
            'operation':op,'proposed_proposition':row['proposed_proposition'],
            'scope_note':row['scope_note'],'source_context_cue_indices':atom['context_cue_indices'],
            'condition_cue_indices':atom['condition_cue_indices'],
            'exception_cue_indices':atom['exception_cue_indices'],
            'typed_relation_sha256s':[json_digest(x) for x in typed['relations']],
            'numeric_references':atom['numeric_references'],'as_of':atom['as_of'],
            'capture_audits':receipts,'prior_target_mutation_authorized':False,
            'approved':False})
    need(seen==set(plans) and used==set(evidence_inputs), 'CENSUS_OR_UNUSED_EVIDENCE')
    output.sort(key=lambda x:x['prior_row_sha256'])
    # A read-only draft is tied to a particular native seal. No fresh approval
    # may rely on it without a new replay of that seal and the final gate.
    need(store.snapshot(scope_id)['ledger_head_sha256']==staged['event_sha256'], 'STALE_HEAD')
    receipt=staged['receipt']
    return {'schema':'IRE_V6_KNOWLEDGE_CHANGE_REVIEW_DRAFT_RECEIPT_V1',
            'host_event_sha256':staged['event_sha256'],'plan_sha256':pin['plan_sha256'],
            'review_sha256':json_digest(review),'draft_rows_sha256':json_digest(output),
            'rows':output,'counts':pin['counts'],'captured_evidence_audits':captures,
            'change_rows_without_capture':missing,'unreplayed_planned_url_links':missing_urls,
            'native_open_rows':sum(r['relationship']=='OPEN' for r in native_rows),
            'quarantined_atoms':len(receipt['quarantined_claim_ids']),
            'quarantined_cues':len(receipt['quarantined_cue_indices']),
            'open_numeric_occurrences':receipt['open_numeric_occurrences'],
            'reviewed_support_cues':receipt['reviewed_support_cue_indices'],
            'finance_evidence_authenticated':False,'formal_v123_input_authorized':False,
            'active_knowledge_changed':False,'p0_go':False}
