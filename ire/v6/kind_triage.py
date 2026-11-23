"""P0-2-05 private same-chat diagnostic: check 11 label discrepancies without fake gold.

This is a custody/quotation/reconciliation validator, NOT a semantic adjudicator.
Types at topic-only crosswalk edges do not imply identical atomic propositions.
All source/native text stays private. Public output contains hash/counts only.
"""
from __future__ import annotations

from collections import Counter
from .codec import sha256, require_hash
from .errors import InvalidInput
from .source_first_review import (_raw_json, _source_digest_cues,
                                  verify_source_first_draft,
                                  verify_diagnostic_topic_crosswalk)

SCHEMA = 'IRE_P205_PRIVATE_11_KIND_DISAGREEMENT_SOURCE_GROUNDED_SAME_CHAT_DIAGNOSTIC_V1'
GROUPS = {
    'DISTINCT_PROPOSITION_TOPIC_ONLY': 'separate_topic_relation_from_atomic_identity',
    'EVALUATION_PLUS_GUIDANCE': 'split_proposition_kind_from_speech_act',
    'EMPIRICAL_UTTERANCE_NOT_VERIFIED': 'distinguish_claim_form_from_evidential_verification',
    'META_REPORTING_VS_EMBEDDED_CLAIM': 'distinguish_reported_speech_from_utterance_meaning',
}


def _reject(code: str):
    raise InvalidInput('P205_KIND_TRIAGE_' + code)


def verify_kind_disagreement_triage(original_srt: bytes, native_raw: bytes,
                                    source_first_raw: bytes, crosswalk_raw: bytes,
                                    triage_raw: bytes, *,
                                    expected_source_sha256: str,
                                    expected_native_sha256: str,
                                    expected_source_first_sha256: str,
                                    expected_crosswalk_sha256: str,
                                    expected_triage_sha256: str,
                                    expected_source_cues: int | None = None,
                                    expected_triaged_pairs: int | None = None) -> dict:
    """All identity and source quote rules are enforced; no truth labels inferred.

    expected_* SHA values MUST be pinned by an independent public receipt.
    User-authored triage decisions are not treated as verified ground truth.
    """
    verify_source_first_draft(original_srt, source_first_raw,
                              expected_source_sha256=expected_source_sha256,
                              expected_candidate_sha256=expected_source_first_sha256,
                              expected_cues=expected_source_cues)
    verify_diagnostic_topic_crosswalk(native_raw, source_first_raw, crosswalk_raw,
                                      expected_native_sha256=expected_native_sha256,
                                      expected_candidate_sha256=expected_source_first_sha256,
                                      expected_crosswalk_sha256=expected_crosswalk_sha256)
    t = _raw_json(triage_raw, expected_sha256=expected_triage_sha256, label='KIND_TRIAGE')
    source = _raw_json(source_first_raw, expected_sha256=expected_source_first_sha256,
                       label='SOURCE_DRAFT')
    native = _raw_json(native_raw, expected_sha256=expected_native_sha256,
                       label='NATIVE_PREDICTION')
    cross = _raw_json(crosswalk_raw, expected_sha256=expected_crosswalk_sha256,
                       label='TOPIC_CROSSWALK')
    cues, _ = _source_digest_cues(original_srt,
                                  expected_source_sha256=expected_source_sha256)
    if t.get('schema') != SCHEMA or not all([
        t.get('original_source_sha256') == expected_source_sha256,
        t.get('provisional_source_json_sha256') == expected_source_first_sha256,
        t.get('native_json_sha256') == expected_native_sha256,
        t.get('crosswalk_json_sha256') == expected_crosswalk_sha256,
    ]):
        _reject('SOURCE_PREDICTION_CROSSWALK_PIN_DRIFT')
    if (t.get('reviewer_context') != 'SAME_CHATGPT_PRIOR_EVIDENCE_EXPOSED_NOT_INDEPENDENT'
            or type(t.get('independent_reviewer_sessions_authenticated')) is not int
            or t['independent_reviewer_sessions_authenticated'] != 0
            or t.get('crosswalk_means_atom_identity') is not False
            or t.get('group_counts_are_accuracy_metrics') is not False
            or t.get('independent_gold_atom_count') != 0
            or t.get('truly_semantically_disagreeing_pairs_gold_verified') is not None
            or t.get('P205_status') != 'HOLD'
            or t.get('P206_status') != 'BLOCKED'
            or t.get('E2_release') is not False
            or t.get('E3_E4_E5_release') is not False
            or t.get('no_owner_original_files_modified') is not True
            or any(t.get(x) is not None for x in ('precision', 'recall', 'high_risk_FN'))):
        _reject('FALSE_INDEPENDENT_TRUTH_OR_STAGE_APPROVAL')
    sources = {r['candidate_id']:r for r in source.get('provisional_atoms', [])}
    natives = {r['claim_id']:r for r in native.get('atoms', [])}
    original_pairs = cross.get('provisional_kind_disagreement_pairs', [])
    expected = {(r['source_candidate_id'], r['native_claim_id']) for r in original_pairs}
    if len(expected) != len(original_pairs) or not expected:
        _reject('ORIGINAL_PAIR_SET_EMPTY_OR_DUPLICATE')
    rows = t.get('provisional_11_pair_triage')
    if (type(rows) is not list or len(rows) != len(expected)
            or (expected_triaged_pairs is not None and len(rows) != expected_triaged_pairs)
            or type(t.get('total_related_label_discrepancies')) is not int
            or t['total_related_label_discrepancies'] != len(expected)):
        _reject('PAIR_TRIAGE_SCOPE_LOST')
    seen=set(); counts=Counter()
    for r in rows:
        if type(r) is not dict:
            _reject('PAIR_NOT_DICT')
        pair=(r.get('source_candidate_id'), r.get('native_claim_id'))
        if pair not in expected or pair in seen:
            _reject('PAIR_MISSING_DUPLICATE_OR_INVENTED')
        seen.add(pair)
        s=sources[pair[0]]; n=natives[pair[1]]
        if r.get('source_kind') != s.get('kind') or r.get('native_kind') != n.get('kind'):
            _reject('PAIR_CLAIM_KIND_CHANGE')
        for k,proposition in [('source_proposition',s.get('source_proposition')),
                              ('native_proposition',n.get('proposition'))]:
            if r.get(k) != proposition:
                _reject('PAIR_PROPOSITION_REPLACED')
        anchor=s.get('primary_quote',{})
        if (type(r.get('source_quoted_cue')) is not int
                or r.get('source_quoted_cue') != anchor.get('cue_index')
                or not 1 <= r['source_quoted_cue'] <= len(cues)
                or r.get('source_quote') != cues[r['source_quoted_cue']-1].text
                or r.get('source_quote') != anchor.get('quote')
                or r.get('source_quote_sha256') != sha256(r['source_quote'].encode('utf8'))):
            _reject('SOURCE_QUOTE_OR_ANCHOR_MISMATCH')
        nr=n.get('source_refs')
        if type(nr) is not list or not nr:
            _reject('NATIVE_ORIGINAL_ANCHOR_MISSING')
        nref=nr[0]
        idx=r.get('native_quote_cue')
        quote=r.get('native_quote')
        if (type(idx) is not int or not 1 <= idx <= len(cues)
                or idx != nref.get('cue_index') or quote != nref.get('quote')
                or not isinstance(quote, str) or not quote.strip()
                or ' '.join(quote.split()).casefold() not in
                   ' '.join(cues[idx-1].text.split()).casefold()
                or r.get('native_quote_sha256') != sha256(quote.encode('utf8'))):
            _reject('NATIVE_QUOTE_OR_ANCHOR_MISMATCH')
        category=r.get('provisional_reconciliation_kind')
        if category not in GROUPS or r.get('engine_repair_tag') != GROUPS[category]:
            _reject('UNSUPPORTED_TRIAGE_GROUP_OR_REPAIR')
        if any(not isinstance(r.get(k),str) or len(r[k].strip()) < 12
               for k in ('same_chat_reasoning','remain_open_risk')):
            _reject('TRIAGE_REASON_OR_OPEN_RISK_MISSING')
        if any(r.get(k) is not False for k in (
            'speaker_audio_verified','meaning_match_verified_by_independent_gold',
            'native_label_is_proven_wrong','source_label_is_proven_correct',
            'financial_truth_certified','eligible_as_gold')) or r.get('requires_independent_followup') is not True:
            _reject('PAIR_FALSE_GOLD_OR_SEMANTIC_VERDICT')
        counts[category]+=1
    if dict(counts)!=t.get('counts'):
        _reject('TRIAGE_COUNTS_FORGED')
    if set(seen)!=expected:
        _reject('INCOMPLETE_TRIAGE_PAIR_COVERAGE')
    q=t.get('high_risk_issue_queue')
    pre=cross.get('high_risk_issue_review_queue')
    if type(q) is not list or type(pre) is not list or len(q)!=len(pre):
        _reject('RISK_QUEUE_CENSUS_CHANGED')
    for current, old in zip(q,pre):
        if (current.get('id')!=old.get('id') or current.get('issue')!=old.get('issue')
                or current.get('source_candidate_numbers')!=old.get('source')
                or current.get('native_ids')!=old.get('native')
                or current.get('review_status')!='OPEN_NOT_INDEPENDENTLY_RESOLVED'):
            _reject('HIGH_RISK_QUEUE_SILENTLY_CLOSED_OR_REWRITTEN')
    if (t.get('source_candidates_without_separate_native_topic_link') !=
            cross.get('source_only_separate_claim_missing_in_native')):
        _reject('STANDALONE_CANDIDATES_DROPPED')
    return {
        'schema':'IRE_V6_P205_LABEL_MISMATCH_DIAGNOSTIC_RECEIPT_V1',
        'source_sha256':expected_source_sha256,
        'native_prediction_sha256':expected_native_sha256,
        'source_first_sha256':expected_source_first_sha256,
        'crosswalk_sha256':expected_crosswalk_sha256,
        'triage_sha256':expected_triage_sha256,
        'raw_label_different_topic_pairs_reviewed':len(rows),
        'provisional_interpretations_by_kind':dict(sorted(counts.items())),
        'risk_queue_remains_open':len(q),
        'all_pair_quotes_and_native_anchors_reverified':True,
        'same_chat_triage_is_independent':False,
        'semantically_proven_wrong_label_pairs':None,
        'gold_source_atoms':0,
        'precision':None,'recall':None,'high_risk_false_negative_count':None,
        'E2_real_gold_pass':False,'E3_E4_E5_pass':False,
        'next_item_blocked':'P0-2-06',
        'status':'TRIAGE_INTEGRITY_PASS_SEMANTIC_GOLD_HOLD',
    }
