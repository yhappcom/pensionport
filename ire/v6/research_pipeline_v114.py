"""V114 ChatGPT-host research bridge: source-bound evidence checkpoints, never an LLM.

Public software may store ONLY numeric metadata and SHA digests. Actual ChatGPT
semantic review, original audio, verified law snapshots and personal tax inputs
must be supplied explicitly outside the journal; never inferred from a PASS.
The journal records the five gates with ACID/idempotent resume and fail-closed
prohibitions against financing, gold and research-complete self-certification.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from time import perf_counter_ns

STAGES = ('SOURCE', 'SEMANTIC', 'FINANCE', 'METRICS', 'KNOWLEDGE')
ZERO = '0' * 64
SCHEMA = 'IRE_V6_V114_PROVISIONAL_RESEARCH_CHAIN_V1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_:-]{0,95}\Z')


class UnsafeResearchStage(ValueError):
    pass


def _require(test, code):
    if not test:
        raise UnsafeResearchStage('V114_' + code)


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _sha(value, name):
    _require(type(value) is str and SHA.fullmatch(value) is not None, name + '_SHA')
    return value


def _nonnegative(value, name):
    _require(type(value) is int and value >= 0, name + '_NONNEGATIVE_INT')
    return value


# All user-written records are strictly projected to allowlisted public-safe fields.
# Private descriptions/quotes/cue text/personal account data never reach SQLite.
_FIELDS = {
    'SOURCE': {'source_cues', 'source_windows', 'source_sha256',
               'owner_private_replay_digest_sha256', 'unaccounted_source_cues',
               'structure_wall_ns'},
    'SEMANTIC': {'parents', 'semantic_units', 'classified_cues', 'unassigned_cues',
                 'open_units', 'meaning_review_approved', 'semantic_artifact_sha256',
                 'structure_wall_ns'},
    'FINANCE': {'financial_fact_candidates', 'official_reference_count',
                'official_reference_metadata_sha256', 'official_primary_snapshot_verified',
                'current_law_scope_checked', 'unresolved_evidence_units',
                'financial_fact_approved', 'personal_tax_approved',
                'finance_artifact_sha256', 'structure_wall_ns'},
    'METRICS': {'source_parse_wall_ns', 'semantic_structure_wall_ns',
                'finance_structure_wall_ns', 'p1_preview_wall_ns',
                'model_semantic_wall_ns', 'official_search_wall_ns',
                'open_resolution_wall_ns', 'independent_adjudication_wall_ns',
                'observed_artifact_sha256'},
    'KNOWLEDGE': {'candidate_relations', 'historical_overlap_positions',
                  'historical_reconciliation_complete', 'v75_identity_recovered',
                  'knowledge_merge_count', 'knowledge_preview_sha256',
                  'structure_wall_ns'},
}
_HASH_FIELDS = {k for fs in _FIELDS.values() for k in fs if k.endswith('_sha256')}
_BOOL_FIELDS = {'meaning_review_approved', 'official_primary_snapshot_verified',
                'current_law_scope_checked', 'personal_tax_approved',
                'historical_reconciliation_complete', 'v75_identity_recovered'}
_NULLABLE_TIME_FIELDS = {'model_semantic_wall_ns','official_search_wall_ns',
                         'open_resolution_wall_ns','independent_adjudication_wall_ns'}


def _validate(stage, payload):
    _require(stage in STAGES, 'UNKNOWN_STAGE')
    _require(type(payload) is dict and set(payload) == _FIELDS[stage],
             'PRIVATE_OR_UNEXPECTED_STAGE_FIELDS')
    for k, v in payload.items():
        if k in _HASH_FIELDS:
            _sha(v, k)
        elif k in _BOOL_FIELDS:
            _require(type(v) is bool, k + '_BOOL')
        elif k in _NULLABLE_TIME_FIELDS:
            if v is not None:
                _nonnegative(v, k)
        else:
            _nonnegative(v, k)
    for forbidden in ('approved_financial_fact','p0_go','independent_gold',
                      'research_complete','personal_advice_approved'):
        _require(forbidden not in payload, 'FORGED_GO_FIELD')
    if stage == 'SOURCE':
        _require(payload['source_cues'] > 0 and payload['source_windows'] > 0 and
                 payload['unaccounted_source_cues'] == 0, 'INCOMPLETE_SOURCE')
    elif stage == 'SEMANTIC':
        _require(payload['parents'] > 0 and payload['semantic_units'] > 0 and
                 payload['classified_cues'] > 0 and
                 not payload['meaning_review_approved'], 'SEMANTIC_APPROVAL_NOT_PROVEN')
    elif stage == 'FINANCE':
        _require(payload['financial_fact_approved'] == 0 and
                 not payload['personal_tax_approved'] and
                 payload['unresolved_evidence_units'] >= 0,
                 'FINANCIAL_APPROVAL_NOT_PROVEN')
    elif stage == 'KNOWLEDGE':
        _require(payload['knowledge_merge_count'] == 0 and
                 not payload['historical_reconciliation_complete'] and
                 not payload['v75_identity_recovered'], 'UNSUPPORTED_KNOWLEDGE_MERGE')
    return payload


def audit_source_unit_crosswalk(original_cues, source_ledger, overlay):
    """Actually reconcile private V109 cues, 52 V110 parents and V112 overlay.

    Hashes original cue text IN MEMORY; emits counts/digest only. This is a
    source/annotation crosswalk, not semantic correctness or missing-claim gold.
    """
    t0 = perf_counter_ns()
    _require(type(original_cues) is dict and type(source_ledger) is dict and
             type(overlay) is dict, 'PRIVATE_REPLAY_INPUT')
    _require(original_cues.get('source_archive_sha256') == source_ledger.get('source_archive_sha256') ==
             overlay.get('original_owner_source_sha256'), 'SOURCE_ARCHIVE_DRIFT')
    source_sha = _sha(original_cues['source_archive_sha256'], 'ORIGINAL_SOURCE')
    src={}
    for cue in original_cues['owner_private_cues']:
        key=(cue['video_id'],cue['cue_index'])
        _require(key not in src, 'DUPLICATED_CUE_IDENTITY')
        _require(hashlib.sha256(cue['text_private'].encode('utf-8')).hexdigest() ==
                 cue['cue_sha256'], 'SOURCE_TEXT_SHA_CHANGED')
        _require(type(cue['start_ms']) is int and
                 cue['end_ms']>=cue['start_ms'], 'SOURCE_CLOCK_INVALID')
        src[key]=(cue['window_id'],cue['cue_sha256'])
    seen_parent=set(); seen_unit=set(); assigned=set(); unit_map={}
    for parent in source_ledger['parents']:
        pid=(parent['video_id'], parent['draft_parent_id'])
        _require(pid not in seen_parent, 'DUPLICATE_PARENT')
        seen_parent.add(pid)
        pkeys={(parent['video_id'],i) for i in parent['source_cue_indices']}
        _require(pkeys and pkeys <= src.keys(), 'PARENT_CUE_MISSING')
        _require(all(src[k][0]==parent['window_id'] for k in pkeys),
                 'PARENT_WINDOW_MISMATCH')
        _require(not assigned.intersection(pkeys), 'PARENT_CUE_DUPLICATED')
        assigned.update(pkeys)
        for u in parent['units']:
            uid=u['unit_id']
            _require(uid not in seen_unit, 'DUPLICATE_SEMANTIC_UNIT')
            seen_unit.add(uid)
            keys={(parent['video_id'],i) for i in u['source_cue_indices']}
            _require(keys and keys <= pkeys, 'UNIT_CUE_OUT_OF_PARENT')
            actual_unit_digest=hashlib.sha256(''.join(
                src[(parent['video_id'],i)][1] for i in u['source_cue_indices']
            ).encode('utf-8')).hexdigest()
            _require(u['source_cues_digest_sha256']==actual_unit_digest,
                     'UNIT_CUE_HASH_NOT_REPLAYED')
            _require(u['independent_gold'] is False and
                     u['approved_financial_fact'] is False and
                     u['personal_advice_approved'] is False,
                     'FALSE_UNIT_FINANCE_APPROVAL')
            unit_map[uid]=(parent,u)
    gaps={}
    for gap in source_ledger['unassigned_cues']:
        key=(gap['video_id'],gap['cue_index'])
        _require(key in src and key not in gaps and
                 gap['cue_sha256']==src[key][1] and
                 gap['claim_absence_certified'] is False,
                 'SOURCE_GAP_FORGED')
        gaps[key]=1
    _require(assigned.isdisjoint(gaps) and assigned | gaps.keys() == src.keys(),
             'SOURCE_CUE_CENSUS_NOT_EXHAUSTIVE')
    statuses={}
    for row in overlay['rows']:
        uid=row['unit_id']
        _require(uid in unit_map and uid not in statuses, 'SHADOW_ID_MISSING_OR_DUPLICATED')
        p,u=unit_map[uid]
        _require((row['video_id'],row['window_id'],row['draft_parent_id'],
                  row['unit_role'],row['source_cue_indices'],row['source_cues_digest_sha256']) ==
                 (p['video_id'],p['window_id'],p['draft_parent_id'],
                  u['role'],u['source_cue_indices'],u['source_cues_digest_sha256']),
                 'SHADOW_SOURCE_UNIT_DRIFT')
        _require(row['finance_semantic_certified'] is False and
                 row['independent_gold'] is False and
                 row['p0_go'] is False and
                 row['personal_advice_approved'] is False,
                 'SHADOW_FALSE_APPROVAL')
        statuses[uid]=row['shadow_status']
    _require(statuses.keys()==unit_map.keys(), 'SHADOW_UNIT_CENSUS_DRIFT')
    open_status={'OPEN_AUDIO','OPEN_VISUAL','OPEN_ACCOUNT_VISUAL','OPEN_ACCOUNT_SCOPE'}
    _require(all(s in open_status | {'CONTEXT_RESOLVED','NOT_IN_V111_OPEN'}
                 for s in statuses.values()), 'UNKNOWN_SHADOW_STATUS')
    pending=sum(s in open_status for s in statuses.values())
    review_digest=_digest({
        'source_sha256':source_sha,
        'source_keys':sorted([v,i,h] for (v,i),(_,h) in src.items()),
        'units':sorted([uid,statuses[uid]] for uid in statuses),
        'parent_ids':sorted([v,p] for v,p in seen_parent),
    })
    return {
        'schema':'IRE_V6_V114_ACTUAL_PRIVATE_SOURCE_CROSSWALK_NO_GOLD_V1',
        'source_sha256':source_sha,
        'source_cues':len(src),'source_windows':len(set((vid,w) for (vid,_),(w,_) in src.items())),
        'unaccounted_source_cues':len(src.keys()-assigned-gaps.keys()),
        'parents':len(seen_parent), 'semantic_units':len(unit_map),
        'classified_cues':len(assigned), 'unassigned_cues':len(gaps),
        'open_units':pending,
        'context_resolved_units':sum(s=='CONTEXT_RESOLVED' for s in statuses.values()),
        'other_not_in_v111_open':sum(s=='NOT_IN_V111_OPEN' for s in statuses.values()),
        'fact_candidates':sum(u['role']=='FACT_CANDIDATE' for _,u in unit_map.values()),
        'semantic_artifact_sha256':review_digest,
        'structure_wall_ns':perf_counter_ns()-t0,
        'source_text_published':False,
        'semantic_recall_measured':False,'financial_fact_approved':0,'p0_go':False,
    }


class V114ResearchJournal:
    """SQLite WAL-independent ACID chained evidence stage record; no private text."""
    def __init__(self, db_path):
        self.db_path=str(Path(db_path))
        with closing(self._connect()) as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS events(
              project_id TEXT NOT NULL, run_id TEXT PRIMARY KEY,
              stage TEXT NOT NULL, ordinal INTEGER NOT NULL,
              prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              UNIQUE(project_id,ordinal));
            CREATE INDEX IF NOT EXISTS ix_v114_project ON events(project_id,ordinal);
            ''')

    def _connect(self):
        db=sqlite3.connect(self.db_path,timeout=8,isolation_level=None)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA busy_timeout=8000')
        return db

    def snapshot(self, project_id):
        _require(type(project_id) is str and ID.fullmatch(project_id), 'PROJECT_ID')
        with closing(self._connect()) as db:
            rows=db.execute('SELECT * FROM events WHERE project_id=? ORDER BY ordinal',
                            (project_id,)).fetchall()
        head=ZERO
        _require(len(rows)<=len(STAGES), 'JOURNAL_TOO_MANY_STAGES')
        for i,row in enumerate(rows):
            body={'schema':SCHEMA,'project_id':project_id,'run_id':row['run_id'],
                  'stage':row['stage'],'ordinal':i+1,'prev_hash':head,
                  'payload':json.loads(row['payload_json'])}
            _require(row['ordinal']==i+1 and row['stage']==STAGES[i] and
                     row['prev_hash']==head and row['event_hash']==_digest(body),
                     'JOURNAL_HASH_CHAIN_CORRUPT')
            head=row['event_hash']
        return {'schema':SCHEMA,'project_id':project_id,
                'stage':rows[-1]['stage'] if rows else 'NOT_STARTED',
                'completed_stages':len(rows),'head_sha256':head,
                'ready_for_next':STAGES[len(rows)] if len(rows)<len(STAGES) else None,
                'continuous_model_execution_proven':False,
                'independent_gold':False, 'p0_go':False,'research_complete':False}

    def submit(self, *, project_id, run_id, expected_head, stage, payload):
        _require(type(project_id) is str and ID.fullmatch(project_id), 'PROJECT_ID')
        _require(type(run_id) is str and ID.fullmatch(run_id), 'RUN_ID')
        _sha(expected_head,'EXPECTED_HEAD')
        _validate(stage,payload)
        self.snapshot(project_id)  # detect earlier corruption before any append/retry
        payload_json=json.dumps(payload,ensure_ascii=False,sort_keys=True,
                                separators=(',',':'),allow_nan=False)
        with closing(self._connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                prior=db.execute('SELECT * FROM events WHERE run_id=?',(run_id,)).fetchone()
                if prior:
                    _require(prior['project_id']==project_id and prior['stage']==stage and
                             prior['prev_hash']==expected_head and
                             prior['payload_json']==payload_json, 'IDEMPOTENCY_CONFLICT')
                    db.execute('COMMIT')
                    return {'new_head_sha256':prior['event_hash'], 'idempotent':True}
                last=db.execute('SELECT * FROM events WHERE project_id=? ORDER BY ordinal DESC LIMIT 1',
                                (project_id,)).fetchone()
                ordinal=last['ordinal']+1 if last else 1
                _require(ordinal<=len(STAGES) and STAGES[ordinal-1]==stage,
                         'STAGE_ORDER_INVALID')
                current=last['event_hash'] if last else ZERO
                _require(current==expected_head, 'CHECKPOINT_STALE')
                # First stage binds the project source; all successors remain
                # bound by the cryptographic event chain, not a mutable field.
                if ordinal==2:
                    source=json.loads(last['payload_json'])
                    _require(payload['classified_cues']+payload['unassigned_cues'] ==
                             source['source_cues'], 'SEMANTIC_SOURCE_CENSUS_DRIFT')
                if ordinal==3:
                    sem=json.loads(last['payload_json'])
                    _require(payload['unresolved_evidence_units']>=sem['open_units'],
                             'FINANCE_OPEN_UNIT_SILENTLY_CLOSED')
                event={'schema':SCHEMA,'project_id':project_id,'run_id':run_id,
                       'stage':stage,'ordinal':ordinal,'prev_hash':current,
                       'payload':payload}
                digest=_digest(event)
                db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)',
                           (project_id,run_id,stage,ordinal,current,digest,payload_json))
                db.execute('COMMIT')
                return {'new_head_sha256':digest,'idempotent':False}
            except Exception:
                db.execute('ROLLBACK')
                raise


def audit_official_fact_docket(source_ledger, docket, *, checked_date):
    """Require one evidence disposition for EACH 1st-pass fact candidate.

    Official URLs are HOST-CHECKED POINTERS only. No network, document body or
    actual law entailment check is performed here; all statuses remain OPEN.
    Do not mistake counterevidence to a universal statement for legal/tax advice.
    """
    from datetime import date
    from urllib.parse import urlparse
    try:
        as_of=date.fromisoformat(checked_date)
    except (ValueError,TypeError) as exc:
        raise UnsafeResearchStage('V114_OFFICIAL_CHECK_DATE_INVALID') from exc
    facts={u['unit_id'] for p in source_ledger['parents']
           for u in p['units'] if u['role']=='FACT_CANDIDATE'}
    _require(type(docket) is list and len(docket)==len(facts), 'FACT_DOCKET_CENSUS')
    allowed={'nts.go.kr','law.go.kr','fsc.go.kr','kofia.or.kr','fss.or.kr'}
    checked=set(); official_refs=0
    statuses={}
    for row in docket:
        _require(type(row) is dict and set(row)=={
                 'unit_id','status','source_evidence_urls','evidence_checked_date',
                 'official_body_sha256','personal_applicability_verified',
                 'financial_fact_approved'}, 'FACT_DOCKET_FIELDS')
        uid=row['unit_id']
        _require(uid in facts and uid not in checked, 'FACT_DOCKET_DUP_OR_UNKNOWN')
        checked.add(uid)
        status=row['status']
        _require(status in ('GENERAL_RULE_COUNTEREVIDENCE_OPEN',
                           'GENERAL_SCOPE_LIMIT_OPEN','SOURCE_FACT_OPEN'),
                 'FALSE_FACT_DISPOSITION')
        _require(row['financial_fact_approved'] is False and
                 row['personal_applicability_verified'] is False,
                 'FALSE_FACT_OR_PERSONAL_APPROVAL')
        urls=row['source_evidence_urls']
        _require(type(urls) is list and len(urls)<=12 and
                 urls==sorted(set(urls)), 'FACT_DOCKET_URLS')
        if urls:
            _require(row['evidence_checked_date']==checked_date,
                     'STALE_OFFICIAL_EVIDENCE_CHECK')
            _require(row['official_body_sha256'] is None or
                     (type(row['official_body_sha256']) is str and
                      SHA.fullmatch(row['official_body_sha256'])),
                     'OFFICIAL_BODY_PIN')
            for url in urls:
                _require(type(url) is str and len(url)<=1024, 'OFFICIAL_URL_TYPE')
                p=urlparse(url)
                host=(p.hostname or '').lower()
                _require(p.scheme=='https' and p.username is None and
                         p.password is None and p.port is None and
                         (host in allowed or any(host.endswith('.'+h) for h in allowed)) and
                         not url.endswith('#'), 'UNTRUSTED_OFFICIAL_URL')
            official_refs+=len(urls)
        else:
            _require(status=='SOURCE_FACT_OPEN' and
                     row['evidence_checked_date'] is None and
                     row['official_body_sha256'] is None,
                     'FAKE_FACT_EVIDENCE_WITHOUT_URL')
        statuses[uid]=status
    _require(checked==facts, 'FACT_DOCKET_NOT_EXHAUSTIVE')
    return {'schema':'IRE_V6_V114_PER_FACT_OFFICIAL_REFERENCE_DOCKET_NO_APPROVAL_V1',
            'fact_candidates':len(facts),'fact_rows':len(docket),
            'official_reference_count':official_refs,
            'general_rule_counterevidence_open':sum(s=='GENERAL_RULE_COUNTEREVIDENCE_OPEN' for s in statuses.values()),
            'general_rule_limited_open':sum(s=='GENERAL_SCOPE_LIMIT_OPEN' for s in statuses.values()),
            'source_fact_open':sum(s=='SOURCE_FACT_OPEN' for s in statuses.values()),
            'body_snapshot_hashes_declared_not_independently_verified':sum(bool(row['official_body_sha256']) for row in docket),
            'docket_digest_sha256':_digest(docket),
            'financial_fact_approved':0,'personal_applicability_verified':False,
            'independent_gold':False,'p0_go':False}
