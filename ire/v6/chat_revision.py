"""Compile actual ChatGPT semantic edits into a new, unapproved V6 exchange.

The reviewer supplies meaning; the engine handles IDs, ownership, cue links,
legacy stance projection and revision lineage. This is not a classifier,
independent gold, financial evidence verification, or a publication route.
All outputs are private except aggregate receipts. No original is mutated.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from .atomic_exchange import (KINDS, _digest_rows, audit_host_atomic_exchange,
                              audit_complete_numeric_references)
from .claim_census import QUALIFIER
from .codec import json_digest
from .errors import InvalidInput

_FRAME_KEYS = {
    'proposition', 'kind', 'source_refs', 'context_cue_indices',
    'condition_cue_indices', 'exception_cue_indices', 'numeric_references', 'as_of',
    'role', 'attribution', 'polarity', 'modality', 'correction', 'meaning_reason',
}
_ROLES = {'NARRATOR', 'GUEST', 'QUESTIONER', 'UNKNOWN'}
_ATTRIBUTIONS = {'DIRECT', 'REPORTED', 'UNRESOLVED'}
_POLARITIES = {'AFFIRMED', 'NEGATED', 'UNRESOLVED'}
_MODALITIES = {'ASSERTED', 'CONDITIONAL', 'HYPOTHETICAL', 'QUESTION', 'UNRESOLVED'}


def _need(test, label):
    if not test:
        raise InvalidInput('CHAT_REVISION_' + label)


def _reason(value):
    return type(value) is str and 4 <= len(value.strip()) <= 1000


def _indices(values, allowed):
    _need(type(values) is list and all(type(i) is int and i in allowed for i in values)
          and values == sorted(set(values)), 'CUE_SCOPE')
    return set(values)


def _project(source, frame, cid):
    _need(type(frame) is dict and set(frame) == _FRAME_KEYS, 'FRAME_SCHEMA')
    for key, choices in (('kind', KINDS), ('role', _ROLES),
                         ('attribution', _ATTRIBUTIONS), ('polarity', _POLARITIES),
                         ('modality', _MODALITIES)):
        _need(type(frame[key]) is str and frame[key] in choices, 'FRAME_' + key.upper())
    _need(type(frame['correction']) is bool and _reason(frame['meaning_reason']),
          'MEANING_REASON')
    _need(type(frame['proposition']) is str and 5 <= len(frame['proposition'].strip()) <= 3000,
          'PROPOSITION')
    allowed = set(range(source.scope_first_cue, source.scope_last_cue + 1))
    context = _indices(frame['context_cue_indices'], allowed)
    conditions = _indices(frame['condition_cue_indices'], allowed)
    exceptions = _indices(frame['exception_cue_indices'], allowed)
    refs = frame['source_refs']
    _need(type(refs) is list and refs and all(type(r) is dict and set(r) == {'cue_index','quote'}
          and type(r['cue_index']) is int and r['cue_index'] in context
          and type(r['quote']) is str and len(r['quote'].strip()) >= 2
          and r['quote'] in source.cues[r['cue_index']-1].text for r in refs), 'VERBATIM_REFS')
    anchors = [r['cue_index'] for r in refs]
    _need(anchors == sorted(set(anchors)) and conditions | exceptions <= context,
          'ANCHOR_OR_QUALIFIER_SCOPE')
    modality = frame['modality']
    _need((modality != 'CONDITIONAL' or bool(conditions)) and
          (modality != 'QUESTION' or frame['kind'] == 'QUESTION') and
          (frame['kind'] != 'QUESTION' or modality in {'QUESTION','UNRESOLVED'}) and
          (modality != 'HYPOTHETICAL' or frame['kind'] in {'HYPOTHETICAL','MATH','QUESTION'}),
          'MODALITY_KIND_OR_CONDITION')
    _need(not (frame['correction'] and frame['attribution'] == 'REPORTED'),
          'CORRECTION_REQUIRES_OWN_SPEECH')
    # Keep attribution and polarity independent in the private typed review.
    # A quoted negative, for example, is not the presenter's own negation.
    speaker = 'QUOTED_SOURCE' if frame['attribution'] == 'REPORTED' else (
        frame['role'] if frame['attribution'] == 'DIRECT' else 'UNKNOWN')
    projection_note = 'EXACT_NATIVE_CATEGORY'
    if frame['attribution'] == 'REPORTED':
        stance = 'QUOTED'
    elif frame['attribution'] == 'UNRESOLVED' or modality == 'UNRESOLVED' or frame['polarity'] == 'UNRESOLVED':
        stance = 'UNRESOLVED'
        projection_note = 'REVIEW_UNRESOLVED'
    elif modality == 'QUESTION':
        stance = 'UNRESOLVED'
        projection_note = 'NATIVE_HAS_NO_QUESTION_STANCE'
    elif frame['correction']:
        stance = 'CORRECTED'
    elif frame['polarity'] == 'NEGATED':
        stance = 'NEGATED'
    elif conditions:
        stance = 'CONDITIONAL'
    elif modality == 'HYPOTHETICAL':
        stance = 'UNRESOLVED'
        projection_note = 'NATIVE_HAS_NO_UNCONDITIONAL_HYPOTHETICAL_STANCE'
    elif any(QUALIFIER.search(source.cues[i-1].text) for i in context):
        # Do not remove the neighboring source just to get AFFIRMED through
        # the existing strict atomic audit. Keep the typed review and HOLD.
        stance = 'UNRESOLVED'
        projection_note = 'NATIVE_QUALIFIER_COMPATIBILITY_REVIEW_REQUIRED'
    else:
        stance = 'AFFIRMED'
    atom = {k: deepcopy(frame[k]) for k in (
        'proposition','kind','source_refs','context_cue_indices',
        'condition_cue_indices','exception_cue_indices','numeric_references','as_of')}
    atom.update(claim_id=cid, owner_window_id=source.owner(anchors[0]),
                speaker=speaker, stance=stance)
    audit_complete_numeric_references(source, atom)
    typed = {k: frame[k] for k in ('role','attribution','polarity','modality','correction','meaning_reason')}
    typed.update(claim_id=cid, identity_status='NOT_AUDIO_AUTHENTICATED',
                 native_projection_note=projection_note, atom_sha256=json_digest(atom))
    return atom, typed


def compile_chat_atom_revision(source, before, *, edits, cue_reviews=()):
    """Compile reviewer-authored ADD/REVISE/SPLIT/MERGE edits, without changing before.

    Each edit is {prior_claim_ids, replacements, reason}. Empty prior IDs means
    ADD; one-to-one REVISE, one-to-many SPLIT, many-to-one MERGE. Old claims
    may not disappear without replacements; unresolved and quarantined claims
    stay in the draft until a later authorized final decision. Old evidence
    and qualifier links must survive collectively in the replacements; any
    qualifier not inherited by a particular split child needs an explicit
    scoped exclusion reason. No
    automatic semantic inference or automatic NO_ATOM conversion occurs.

    cue_reviews explicitly covers non-primary cues as CONTEXT_ONLY, NO_ATOM
    or UNRESOLVED; untouched cues retain their earlier status. CONTEXT_ONLY
    retains a private back-link and maps to native NO_ATOM, whose risk audit
    still applies. Any newly orphaned anchor without a review stays OPEN.
    """
    base = audit_host_atomic_exchange(source, before)
    _need(type(edits) is list and bool(edits), 'EDIT_LIST')
    _need(type(cue_reviews) in (list, tuple), 'CUE_REVIEW_LIST')
    old = {a['claim_id']: a for a in before['atoms']}
    retired, replacements, typed, lineage = set(), [], [], []
    next_id = max((int(cid[1:]) for cid in old), default=0) + 1
    for edit in edits:
        _need(type(edit) is dict and {'prior_claim_ids','replacements','reason'} <= set(edit)
              and set(edit) <= {'prior_claim_ids','replacements','reason','qualifier_exclusions'}
              and _reason(edit['reason']), 'EDIT_SCHEMA')
        ids, frames = edit['prior_claim_ids'], edit['replacements']
        _need(type(ids) is list and all(type(x) is str and x in old and x not in retired for x in ids)
              and ids == sorted(set(ids)) and type(frames) is list and bool(frames), 'EDIT_LINEAGE')
        _need(not (len(ids) > 1 and len(frames) > 1), 'AMBIGUOUS_MANY_TO_MANY')
        group, typed_group = [], []
        for frame in frames:
            _need(next_id <= 99999999, 'ID_EXHAUSTED')
            atom, role = _project(source, frame, f'C{next_id:05d}')
            next_id += 1
            group.append(atom); typed_group.append(role)
        # An accidental duplicate proposition is not a valid split.
        keys = [(a['kind'], a['speaker'], a['stance'], ' '.join(a['proposition'].split())) for a in group]
        _need(len(keys) == len(set(keys)), 'DUPLICATE_REPLACEMENT')
        old_context = {i for cid in ids for i in old[cid]['context_cue_indices']}
        new_context = {i for a in group for i in a['context_cue_indices']}
        _need(old_context <= new_context, 'PRIOR_CONTEXT_LOST')
        missing_qualifiers = set()
        for field in ('condition_cue_indices','exception_cue_indices'):
            prior_qualifiers = {i for cid in ids for i in old[cid][field]}
            _need(prior_qualifiers <= {i for a in group for i in a[field]}, 'PRIOR_QUALIFIER_LOST')
            for pos, atom in enumerate(group):
                missing_qualifiers.update((pos, field, i) for i in prior_qualifiers - set(atom[field]))
        exclusions = edit.get('qualifier_exclusions', [])
        _need(type(exclusions) is list, 'QUALIFIER_EXCLUSIONS')
        declared = set()
        for row in exclusions:
            _need(type(row) is dict and set(row) == {'replacement_index','field','cue_index','reason'}
                  and type(row['replacement_index']) is int and type(row['field']) is str
                  and type(row['cue_index']) is int and _reason(row['reason']), 'QUALIFIER_EXCLUSION_SCHEMA')
            key = (row['replacement_index'], row['field'], row['cue_index'])
            _need(key in missing_qualifiers and key not in declared, 'QUALIFIER_EXCLUSION_NOT_NEEDED')
            declared.add(key)
        _need(declared == missing_qualifiers, 'CHILD_QUALIFIER_SCOPE_UNREVIEWED')
        retired.update(ids); replacements.extend(group); typed.extend(typed_group)
        operation = ('ADD' if not ids else 'MERGE' if len(ids)>1 else
                     'SPLIT' if len(group)>1 else 'REVISE')
        lineage.append({'operation': operation, 'prior_claim_ids': ids[:],
                        'prior_atom_sha256': [json_digest(old[c]) for c in ids],
                        'new_claim_ids': [a['claim_id'] for a in group],
                        'qualifier_exclusions': deepcopy(exclusions), 'reason': edit['reason']})
    atoms = [deepcopy(a) for a in before['atoms'] if a['claim_id'] not in retired] + replacements
    anchors, contexts = defaultdict(list), defaultdict(list)
    for a in atoms:
        for r in a['source_refs']:
            anchors[r['cue_index']].append(a['claim_id'])
        for i in a['context_cue_indices']:
            contexts[i].append(a['claim_id'])
    explicit = {}
    for row in cue_reviews:
        _need(type(row) is dict and set(row) == {'cue_index','status','reason'} and _reason(row['reason']),
              'CUE_REVIEW_SCHEMA')
        i, status = row['cue_index'], row['status']
        _need(type(i) is int and source.scope_first_cue <= i <= source.scope_last_cue and
              i not in explicit and not anchors[i] and type(status) is str and
              status in {'CONTEXT_ONLY','NO_ATOM','UNRESOLVED'}, 'CUE_REVIEW_CONFLICT')
        _need(status != 'CONTEXT_ONLY' or bool(contexts[i]), 'CONTEXT_WITHOUT_CARRIER')
        _need(status != 'NO_ATOM' or not contexts[i], 'CONTEXT_SILENCED_AS_NONCLAIM')
        explicit[i] = row
    cue_rows, cue_lineage = [], []
    for row in before['cue_dispositions']:
        i = row['cue_index']; revised = deepcopy(row)
        revised['claim_ids'] = sorted(anchors[i])
        if anchors[i]:
            revised.update(disposition='CANDIDATES', note='')
        elif i in explicit:
            item = explicit[i]
            revised.update(disposition='UNRESOLVED' if item['status']=='UNRESOLVED' else 'NO_ATOM',
                           note=item['reason'][:256])
            cue_lineage.append({**item, 'context_claim_ids': sorted(contexts[i])})
        elif row['disposition']=='CANDIDATES':
            revised.update(disposition='UNRESOLVED', note='Former primary anchor requires explicit source review.')
        cue_rows.append(revised)
    after = {**before, 'atoms': atoms, 'cue_dispositions': cue_rows}
    audited = audit_host_atomic_exchange(source, after)
    # Project the revised atoms into the existing V6 host/proof input schema.
    # A later host call still needs current owner inventory, reviewed prior
    # relations and any required unresolved-cue prequarantine; not generated here.
    models, reviews = {}, {}
    for wid, _, _ in source.primary_windows:
        claims = []
        for atom in atoms:
            if atom['owner_window_id'] != wid:
                continue
            refs = atom['source_refs']
            claim = {k: deepcopy(atom[k]) for k in (
                'claim_id','proposition','kind','owner_window_id','source_refs')}
            claim.update(context_first_cue=refs[0]['cue_index'],
                         context_last_cue=refs[-1]['cue_index'])
            claims.append(claim)
        models[wid] = {'schema':'IRE_V6_ATOMIC_MODEL_V1','claims':claims}
        reviews[wid] = {'schema':'IRE_V6_STRUCTURAL_REVIEW_V1',
                        'review_scope':'SOURCE_ANCHORS_ONLY',
                        'reviewed_claim_ids':sorted(c['claim_id'] for c in claims),
                        'independent_gold_verified':False}
    return {'exchange': after, 'window_models': models, 'window_reviews': reviews,
            'typed_reviews': typed, 'edit_lineage': lineage,
            'cue_review_lineage': cue_lineage, 'receipt': {
                'schema':'IRE_V6_CHAT_ATOM_REVISION_RECEIPT_V1',
                'source_sha256':source.source_sha256,
                'before_atom_digest':base['atom_candidate_digest'],
                'after_atom_digest':audited['atom_candidate_digest'],
                'after_cue_digest':audited['cue_disposition_digest'],
                'typed_review_digest':_digest_rows(typed),
                'edit_lineage_digest':_digest_rows(lineage),
                'cue_review_digest':_digest_rows(cue_lineage),
                'before_atoms':len(old), 'after_atoms':len(atoms),
                'retired_atoms':len(retired), 'new_atoms':len(replacements),
                'remaining_unresolved_cues':audited['unresolved_cues'],
                'native_unknown_speakers':sum(a['speaker']=='UNKNOWN' for a in atoms),
                'native_unresolved_stances':sum(a['stance']=='UNRESOLVED' for a in atoms),
                'independent_gold_verified':False, 'financial_truth_verified':False,
                'research_complete':False, 'publication_authorized':False,
            }}
