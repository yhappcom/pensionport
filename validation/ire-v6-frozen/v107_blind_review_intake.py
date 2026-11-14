"""V107 owner-private independent-review handoff and intake verification.

No human reviewer is available to this module. It prepares source-only blinded
packets and validates *structure*, never credentials, independent authorship,
finance correctness or gold. Real scores require a trusted out-of-band identity
provider, separate adjudication and semantic equivalence before unsealing.

Public source code contains no owner's transcript text or evaluator judgments.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from hashlib import sha256
import json
import re

SOURCE_ARCHIVE_SHA256 = '00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V105_PACKET_SHA256 = 'ea9020d688917ce11272b45033b8160b68f9680eae9974770eb7ad6549efea81'
V105_LOCK_SCHEMA = 'V105_UNSEEN_OWNER_SOURCE_PRE_REVIEW_LOCK_V1'
V105_PACKET_SCHEMA = 'V105_EXTERNAL_BLIND_GOLD_NOT_CREATED_V1'
BLIND_PACKET_SCHEMA = 'V107_SOURCE_ONLY_BLIND_REVIEW_PACKET_PRIVATE_V1'
FORM_SCHEMA = 'V107_BLIND_REVIEW_SUBMISSION_TEMPLATE_PRIVATE_V1'
REVIEWER_SLOTS = ('REVIEWER_A', 'REVIEWER_B')
VERDICTS = {'CLAIM', 'NO_FINANCIAL_CLAIM', 'OPEN_SOURCE_AUDIO'}
STANCES = {'FACT_CANDIDATE','QUESTION','OPINION','HYPOTHESIS','CONDITION','EXCEPTION','REBUTTAL','UNCERTAIN'}
RISKS = {'HIGH', 'MEDIUM', 'LOW', 'NONE'}
SHA256_PATTERN = re.compile(r'^[0-9a-f]{64}$')
FORBIDDEN_LEAK_TOKENS = ('prediction', 'engine_output', 'model_annotation', 'risk_signal', 'v93_risk', 'v96_', 'v97_', 'v103_', 'gold_label', 'expected_truth')


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError('V107_' + code)


def canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(value: str | bytes) -> str:
    return sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def digest(value) -> str:
    return sha(canonical(value))


def verify_owner_source_packet(lock: dict, source_packet: dict, *, actual_owner_archive_sha256: str) -> dict:
    """Recheck all 160 source cue bytes and prior V105 cohort; no model labels."""
    require(type(lock) is dict and type(source_packet) is dict, 'SOURCE_TYPES')
    require(actual_owner_archive_sha256 == SOURCE_ARCHIVE_SHA256, 'OWNER_ARCHIVE_CHANGED')
    require(lock.get('schema') == V105_LOCK_SCHEMA, 'LOCK_SCHEMA')
    require(lock.get('source_zip_sha256') == SOURCE_ARCHIVE_SHA256, 'LOCK_ARCHIVE')
    require(source_packet.get('schema') == V105_PACKET_SCHEMA, 'PACKET_SCHEMA')
    require(source_packet.get('source_archive_sha256') == SOURCE_ARCHIVE_SHA256, 'PACKET_ARCHIVE')
    require(source_packet.get('packet_sha256') == V105_PACKET_SHA256, 'PACKET_PIN')
    require(source_packet.get('blind_view') is True and source_packet.get('prediction_disclosed') is False, 'LEAKED_PREDICTIONS')
    require(source_packet.get('independent_gold') is False and source_packet.get('p0_go') is False, 'FALSE_GOLD')
    require(lock.get('independent_gold') is False and lock.get('p0_go') is False, 'FALSE_LOCK_GOLD')
    windows = lock.get('selected')
    require(type(windows) is list and len(windows) == 4 and lock.get('cue_count') == 160, 'LOCK_WINDOWS')
    keys = set()
    for w in windows:
        k = (w.get('video_id'), w.get('window_id'))
        require(k not in keys and type(k[0]) is str and re.fullmatch('W[0-9]{5}', k[1] or '') is not None, 'SCOPE_DUP')
        require(type(w.get('first_cue')) is int and type(w.get('last_cue')) is int and w['last_cue'] - w['first_cue'] + 1 == 40, 'WINDOW_LENGTH')
        keys.add(k)
    rows = source_packet.get('owner_private_cues')
    require(type(rows) is list and len(rows) == 160, 'SOURCE_CUE_COUNT')
    by_window = defaultdict(list)
    seen = set()
    for row in rows:
        require(type(row) is dict, 'SOURCE_CUE_ROW')
        k = (row.get('video_id'), row.get('window_id'))
        cue = row.get('cue_index')
        require(k in keys and type(cue) is int and (k[0], cue) not in seen, 'SOURCE_IDENTITY')
        seen.add((k[0], cue))
        require(type(row.get('text_private')) is str and bool(row['text_private']), 'SOURCE_TEXT')
        require(row.get('cue_sha256') == sha(row['text_private']), 'SOURCE_CUE_SHA')
        require(type(row.get('start_ms')) is int and type(row.get('end_ms')) is int and row['start_ms'] <= row['end_ms'], 'SOURCE_TIME')
        by_window[k].append(row)
    for w in windows:
        k = (w['video_id'], w['window_id'])
        r = by_window.get(k)
        require(r is not None and len(r) == 40, 'WINDOW_SOURCE_MISSING')
        cue_ids = [x['cue_index'] for x in r]
        require(cue_ids == list(range(w['first_cue'], w['last_cue']+1)), 'SOURCE_ORDER_CHANGED')
        require(sha(' '.join(x['text_private'] for x in r)) == w['source_window_sha256'], 'WINDOW_SHA_CHANGED')
    exact_digest = digest([[r['video_id'], r['cue_index'], r['cue_sha256']] for r in rows])
    require(exact_digest == source_packet['packet_sha256'], 'PACKET_DIGEST')
    return {
        'schema': 'V107_VERIFIED_BLIND_SOURCE_ONLY_COHORT_SHA_ONLY_V1',
        'source_archive_sha256': SOURCE_ARCHIVE_SHA256,
        'source_packet_sha256': exact_digest,
        'window_count': len(windows),
        'source_cue_count': len(rows),
        'source_read_without_model_predictions': True,
        'reviewer_submissions_received': 0,
        'independent_gold': False,
        'p0_go': False,
    }


def build_blind_reviewer_materials(lock: dict, source_packet: dict, slot: str, *, actual_owner_archive_sha256: str) -> tuple[dict, dict]:
    verification = verify_owner_source_packet(lock, source_packet, actual_owner_archive_sha256=actual_owner_archive_sha256)
    require(slot in REVIEWER_SLOTS, 'REVIEWER_SLOT')
    source_rows = source_packet['owner_private_cues']
    # Do not leak selection-stratum, past engine alerts, parents or internal reviews to a reviewer.
    public_to_reviewer = [{key: row[key] for key in ('video_id', 'window_id', 'cue_index', 'start_ms', 'end_ms', 'text_private', 'cue_sha256')} for row in source_rows]
    source_only_packet = {
        'schema': BLIND_PACKET_SCHEMA,
        'review_slot': slot,
        'source_packet_sha256': verification['source_packet_sha256'],
        'source_cue_count': 160,
        'instructions_ko': (
            '다른 검토자와 협의하지 말고 원본 자막 160개를 모두 확인하십시오. 각 자막을 주장/비금융/원음확인 필요로 판정한 뒤, '\
            '주장마다 화자 입장·근거 자막·숫자와 단위·기간·조건·예외·반박 및 위험도를 별도 원자 항목으로 기록하십시오. '\
            '자동 탐지 결과나 이전 검토 결과를 요청하거나 참조하지 마십시오. 서명·독립성 검증은 별도 관리됩니다.'),
        'source_cues_private': public_to_reviewer,
        'no_engine_predictions': True,
        'no_existing_reviews': True,
        'independent_gold': False,
    }
    empty_form = {
        'schema': FORM_SCHEMA,
        'review_slot': slot,
        'source_packet_sha256': verification['source_packet_sha256'],
        'prediction_disclosed': False,
        'reviewer_id': None,
        'review_started_at_utc': None,
        'review_finished_at_utc': None,
        'reviewer_independence_externally_attested': False,
        'cue_verdicts': [{'video_id': r['video_id'], 'cue_index': r['cue_index'], 'status': 'UNREVIEWED', 'atomic_ids': []} for r in source_rows],
        'atomic_claims': [],
        'reviewer_signature_hex': None,
        'external_identity_authority_receipt': None,
        'gold_approved': False,
        'p0_go': False,
    }
    require(not any(token in canonical(source_only_packet).lower() for token in FORBIDDEN_LEAK_TOKENS if token not in ('prediction',)), 'PACKET_METADATA_LEAK')
    # These are *packaging* receipts, not cryptographic reviewer identity attestations.
    return source_only_packet, empty_form


def validate_submitted_form(form: dict, blind_packet: dict) -> dict:
    """Validate complete *structural* annotations; never certify reviewer identity.

    A self-completed form, even one claiming an external reviewer, is not gold.
    """
    require(type(form) is dict and type(blind_packet) is dict, 'SUBMISSION_TYPES')
    require(blind_packet.get('schema') == BLIND_PACKET_SCHEMA and blind_packet.get('source_cue_count') == 160, 'BLIND_PACKET_SCHEMA')
    require(form.get('schema') == FORM_SCHEMA and form.get('review_slot') == blind_packet.get('review_slot'), 'SUBMISSION_SCHEMA')
    require(form.get('source_packet_sha256') == blind_packet.get('source_packet_sha256'), 'SUBMISSION_SOURCE_DRIFT')
    require(form.get('prediction_disclosed') is False and form.get('gold_approved') is False and form.get('p0_go') is False, 'FALSE_INDEPENDENT_APPROVAL')
    rows = blind_packet.get('source_cues_private')
    require(type(rows) is list and len(rows) == 160 and len({(x['video_id'], x['cue_index']) for x in rows}) == 160, 'PACKET_CUE_IDS')
    source = {(r['video_id'], r['cue_index']): r for r in rows}
    verdicts = form.get('cue_verdicts')
    require(type(verdicts) is list and len(verdicts) == 160, 'VERDICT_COUNT')
    verdict_map = {}
    for r in verdicts:
        k = (r.get('video_id'), r.get('cue_index'))
        require(k in source and k not in verdict_map, 'VERDICT_SCOPE_OR_DUPLICATE')
        require(r.get('status') in VERDICTS, 'VERDICT_NOT_COMPLETED')
        assert_ids = r.get('atomic_ids')
        require(type(assert_ids) is list and len(assert_ids) == len(set(assert_ids)), 'VERDICT_ATOM_IDS')
        if r['status'] != 'CLAIM': require(not assert_ids, 'NON_CLAIM_WITH_ATOMS')
        else: require(bool(assert_ids), 'CLAIM_WITHOUT_ATOM_ID')
        verdict_map[k] = r
    require(set(verdict_map) == set(source), 'NOT_ALL_CUES_REVIEWED')
    claims = form.get('atomic_claims')
    require(type(claims) is list, 'CLAIM_LIST')
    atom_to_claim = {}
    by_cue = defaultdict(set)
    for claim in claims:
        aid = claim.get('atomic_id')
        require(type(aid) is str and bool(aid) and aid not in atom_to_claim, 'DUPLICATE_ATOM_ID')
        v, win = claim.get('video_id'), claim.get('window_id')
        indices = claim.get('cue_indices')
        require(type(indices) is list and bool(indices) and len(indices) == len(set(indices)) and all(type(x) is int for x in indices), 'ATOM_SPAN')
        referents = [source.get((v, i)) for i in indices]
        require(all(r is not None and r['window_id'] == win for r in referents), 'ATOM_CROSS_WINDOW_OR_MISSING_SOURCE')
        require(claim.get('cue_source_sha256') == digest([[v, i, source[(v, i)]['cue_sha256']] for i in indices]), 'ATOM_SPAN_SHA')
        require(claim.get('stance') in STANCES and claim.get('risk') in RISKS, 'ATOM_STANCE_OR_RISK')
        require(type(claim.get('proposition_private')) is str and len(claim['proposition_private'].strip()) >= 12, 'ATOM_NO_MEANING')
        require(type(claim.get('conditions')) is list and type(claim.get('exceptions')) is list, 'ATOM_SCOPE_REQUIRED')
        require(type(claim.get('amounts_periods')) is list, 'ATOM_NUMERIC_SCOPE_REQUIRED')
        require(type(claim.get('reviewer_reason_private')) is str and len(claim['reviewer_reason_private'].strip()) >= 12, 'ATOM_NO_REASON')
        atom_to_claim[aid] = claim
        for i in indices: by_cue[(v, i)].add(aid)
    for k, row in verdict_map.items():
        require(set(row['atomic_ids']) == by_cue.get(k, set()), 'VERDICT_CLAIM_LINK_MISMATCH')
    open_audio = [k for k, row in verdict_map.items() if row['status'] == 'OPEN_SOURCE_AUDIO']
    require(len(open_audio) == 0 or all(row['status']!='OPEN_SOURCE_AUDIO' for k,row in verdict_map.items() if k not in open_audio), 'OPEN_SCOPE_INTERNAL')
    # External people/independence are impossible to authenticate merely from the form.
    return {
        'schema': 'V107_REVIEW_SUBMISSION_STRUCTURE_ONLY_NO_INDEPENDENT_GOLD_V1',
        'review_slot': form['review_slot'],
        'source_cue_count': 160,
        'all_cue_statuses_complete': True,
        'candidate_claim_count': len(claims),
        'open_audio_cue_count': len(open_audio),
        'claim_cue_count': sum(x['status']=='CLAIM' for x in verdicts),
        'submission_content_sha256': digest({'verdicts':verdicts, 'claims':claims}),
        'independent_human_verified': False,
        'independent_gold': False,
        'certified_precision': None,
        'certified_recall': None,
        'high_risk_recall': None,
        'p0_go': False,
    }


def create_disagreement_docket(submission_a: dict, submission_b: dict, pack_a: dict, pack_b: dict) -> dict:
    """Only form-status disagreement; claim meaning equivalence requires a human adjudicator."""
    a=validate_submitted_form(submission_a,pack_a)
    b=validate_submitted_form(submission_b,pack_b)
    require(a['review_slot']=='REVIEWER_A' and b['review_slot']=='REVIEWER_B','INDEPENDENT_SLOT_MISMATCH')
    require(pack_a['source_packet_sha256']==pack_b['source_packet_sha256'],'DIFFERENT_SOURCE_COHORT')
    aa={(x['video_id'], x['cue_index']):x for x in submission_a['cue_verdicts']}
    bb={(x['video_id'], x['cue_index']):x for x in submission_b['cue_verdicts']}
    disagreements=[{'video_id':v,'cue_index':i,'reviewer_a_status':aa[(v,i)]['status'],'reviewer_b_status':bb[(v,i)]['status']} for v,i in sorted(aa) if aa[(v,i)]['status']!=bb[(v,i)]['status']]
    return {'schema':'V107_BLIND_DOUBLE_READ_DISAGREEMENT_NOT_GOLD_V1',
            'source_packet_sha256':pack_a['source_packet_sha256'],
            'cue_status_agreement_only':160-len(disagreements),
            'cue_status_disagreement_count':len(disagreements),
            'cue_status_disagreements_private':disagreements,
            'atomic_claim_equivalence_independently_adjudicated':False,
            'reviewers_identity_externally_authenticated':False,
            'gold_locked':False,'independent_gold':False,
            'certified_precision':None,'certified_recall':None,'high_risk_recall':None,'p0_go':False}


def require_external_identity_and_gold(*, review_a=None, review_b=None, adjudicator=None, external_trust_anchor=None) -> dict:
    """No actual external identity records are supplied or inferred by chat.

    A safe readiness report, not a bypass. A future *separate* authenticated
    signing/identity service must establish independence before scoring via
    the already-gated V105 downstream path.
    """
    present = sum(x is not None for x in (review_a,review_b,adjudicator))
    # A self-supplied trust key, text claim of independence, or agent persona
    # cannot establish real-world reviewer identity.
    if external_trust_anchor is not None:
        require(type(external_trust_anchor) is dict and external_trust_anchor.get('owner_supplied_self_attestation') is not True, 'SELF_ASSERTED_TRUST_ANCHOR')
    return {
        'schema':'V107_INDEPENDENT_HUMAN_GOLD_INPUT_GATE_NO_SCORE_V1',
        'external_roles_submitted':present,
        'external_roles_required':3,
        'external_verified_roles':0,
        'trust_anchor_verified_by_out_of_band_authority':False,
        'readiness':'BLOCKED_EXTERNAL_VERIFIED_PEOPLE_AND_ADJUDICATION',
        'independent_gold':False,
        'tp':None,'fp':None,'fn':None,
        'precision':None,'recall':None,'high_risk_recall':None,
        'human_review_hours':None,
        'p0_go':False,
    }