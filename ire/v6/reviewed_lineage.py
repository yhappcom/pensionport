"""Source-level adjudication and loss-accounted candidate lineage.

Native typed custody is the input, not an approved knowledge store. This
compiler does not authorize a V123 release or mutate Master/P4. A retired
candidate remains in the immutable predecessor; outputs are new candidates.
"""
from .codec import json_digest, require_hash
from .errors import InvalidInput

STATUSES={'SOURCE_ONLY','NON_KNOWLEDGE','FINANCE_PENDING','CORRECT','SPLIT','MERGE','QUARANTINE'}
OPS={'CORRECT','RETIRE','SPLIT','MERGE'}

def _need(ok, code):
    if not ok: raise InvalidInput('REVIEWED_LINEAGE_'+code)


def compile_reviewed_lineage(record, head, review, operations, change_rows):
    """Compile exactly enumerated dispositions; inherit all parent coordinates.

    Callers must obtain record/change_rows from the native read/replay APIs.
    Structural checks are not semantic truth or final financial approval.
    """
    require_hash(head)
    atoms={a['claim_id']:a for a in record['exchange']['atoms']}
    quarantine={a['claim_id'] for a in record['ledger']['quarantine_atoms']}
    typed={r['claim_id']:r['typed_sha256'] for r in record['ledger']['projection_rows']}
    _need(set(typed)==set(atoms),'TYPED_CENSUS')
    _need(type(review) is list and type(operations) is list and type(change_rows) is list,'SCHEMA')
    seen={}
    for r in review:
        _need(type(r) is dict and set(r)=={'claim_id','atom_sha256','status','reason'},'REVIEW_SCHEMA')
        cid=r['claim_id'];_need(type(cid) is str and cid in atoms and cid not in seen,'REVIEW_IDENTITY')
        _need(r['atom_sha256']==json_digest(atoms[cid]) and r['status'] in STATUSES,'REVIEW_ATOM_OR_STATUS')
        _need((cid in quarantine)==(r['status']=='QUARANTINE'),'QUARANTINE_DRIFT')
        _need(type(r['reason']) is str and 8<=len(r['reason'].strip())<=2000,'REASON')
        seen[cid]=r
    _need(set(seen)==set(atoms),'REVIEW_CENSUS')
    expected={c for c,r in seen.items() if r['status'] in {'CORRECT','SPLIT','MERGE','NON_KNOWLEDGE'}}
    used=set(); derived=[]; edges=[]; changed={r['claim_id']:r for r in change_rows if r['operation']=='CORRECT_SOURCE_CANDIDATE'}
    for op in operations:
        _need(type(op) is dict and set(op)=={'operation','parents','propositions','reason'},'OP_SCHEMA')
        k=op['operation'];p=op['parents'];v=op['propositions']
        _need(type(k) is str and k in OPS and type(p) is list and all(type(c) is str for c in p) and p==sorted(set(p)) and not used.intersection(p) and set(p)<=expected,'OP_PARENTS')
        _need(type(v) is list and all(type(x) is str and 8<=len(x.strip())<=3000 for x in v) and len(set(v))==len(v),'OUTPUT_TEXT')
        _need(type(op['reason']) is str and 8<=len(op['reason'].strip())<=2000,'OP_REASON')
        status='NON_KNOWLEDGE' if k=='RETIRE' else k
        _need(all(seen[c]['status']==status for c in p),'OP_STATUS')
        _need((k=='CORRECT' and len(p)==len(v)==1) or (k=='RETIRE' and len(p)==1 and not v) or (k=='SPLIT' and len(p)==1 and len(v)>=2) or (k=='MERGE' and len(p)>=2 and len(v)==1),'OP_CARDINALITY')
        if k=='CORRECT':
            _need(p[0] in changed and changed[p[0]]['source_atom_sha256']==json_digest(atoms[p[0]]) and changed[p[0]]['proposed_proposition']==v[0],'CORRECTION_DRAFT_DRIFT')
        used.update(p)
        # Never replace a source assertion with external corrected wording in its original atom.
        parent_rows=[atoms[c] for c in p]; anchors={}
        for f in ('context_cue_indices','condition_cue_indices','exception_cue_indices'):
            anchors[f]=sorted({i for a in parent_rows for i in a[f]})
        for f in ('source_refs','numeric_references'):
            refs={json_digest(x):x for a in parent_rows for x in a[f]};anchors[f]=[refs[h] for h in sorted(refs)]
        lineage={'operation':k,'parent_ids':p,'parent_sha256s':[json_digest(a) for a in parent_rows],'typed_parent_sha256s':[require_hash(typed[c]) for c in p], 'reason':op['reason'],'review_status':'UNAPPROVED_CANDIDATE'}
        outputs=[]
        for text in v:
            out={**lineage,**anchors,'proposition':text,'source_metadata':[{'kind':a['kind'],'speaker':a['speaker'],'stance':a['stance'],'as_of':a['as_of']} for a in parent_rows]}
            out['candidate_sha256']=json_digest(out); derived.append(out); outputs.append(out['candidate_sha256'])
        edges.append({**lineage,'output_sha256s':outputs})
    _need(used==expected,'OP_CENSUS')
    # Every original row is represented exactly once, either unchanged or via lineage.
    remaining=sorted(set(atoms)-used)
    return {'schema':'IRE_V6_REVIEWED_LINEAGE_DRAFT_V1','host_event_sha256':head,'source_record_sha256':json_digest(record),'review_sha256':json_digest(review),'operations_sha256':json_digest(operations),'counts':{s:sum(r['status']==s for r in review) for s in sorted(STATUSES)},'unchanged_claim_ids':remaining,'edges':edges,'candidates':derived,'original_atoms_retained':len(atoms),'active_knowledge_changed':False,'formal_v123_input_authorized':False,'p0_go':False}


def prepare_reviewed_lineage(store, *, scope_id, run_id, raw, manifest,
        inventory_bytes, expected_inventory_sha256, expected_head,
        review, operations, change_review, evidence_inputs, origin_archive=None):
    """Read the actual current seal and replay change drafts, never publish."""
    from .host_batch import read_host_typed_staging
    from .knowledge_change import prepare_host_knowledge_change_review
    from .store import TransactionStore
    _need(isinstance(store,TransactionStore),'NATIVE_STORE_REQUIRED')
    kw=dict(scope_id=scope_id,run_id=run_id,raw=raw,manifest=manifest,
        inventory_bytes=inventory_bytes,expected_inventory_sha256=expected_inventory_sha256)
    s=read_host_typed_staging(store,**kw)
    _need(s['event_sha256']==expected_head,'HEAD_DRIFT')
    c=prepare_host_knowledge_change_review(store,**kw,review=change_review,
        evidence_inputs=evidence_inputs,origin_archive=origin_archive)
    _need(c['host_event_sha256']==expected_head and c['active_knowledge_changed'] is False and c['formal_v123_input_authorized'] is False,'CHANGE_DRIFT')
    result=compile_reviewed_lineage(s['record'],expected_head,review,operations,c['rows'])
    _need(store.snapshot(scope_id)['ledger_head_sha256']==expected_head,'HEAD_DRIFT')
    return {**result,'change_receipt_sha256':json_digest(c)}
