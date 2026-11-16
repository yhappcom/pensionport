"""V146: reject self-attested meaning quality on unidentified/ambiguous V6 claims.

Original transcript may not identify an actual speaker. In that case a ChatGPT
source-first review may still identify its speech act, context and quotation
relationship; it must not invent a personal identity or launder a source claim
into a verified external fact. This validates pinned structure, never semantic
truth or independent precision/recall.
"""
from __future__ import annotations
from ire.v6.codec import json_digest, sha256, require_hash
from ire.v6.errors import InvalidInput

SCHEMA = 'IRE_V146_EXPLICIT_SOURCE_MEANING_PROVENANCE_V1'
ALLOWED_ROLES = frozenset({'HOST','GUEST','INTERVIEWER','NARRATOR','UNATTRIBUTED_VIDEO_SPEAKER','SOURCE_BOOK_QUOTE'})
ALLOWED_ACTS = frozenset({'ASSERTION','OPINION','HYPOTHESIS','QUESTION','QUOTE','REBUTTAL','CONDITIONAL_ASSERTION','CORRECTION','ILLUSTRATIVE_ANALOGY'})


def _check(condition, key):
    if not condition:
        raise InvalidInput('V146_SEMANTIC_PROVENANCE_' + key)


def _source_anchor_hash(source, cue_indices):
    _check(type(cue_indices) is list and len(cue_indices)>0 and
           all(type(n) is int and source.scope_first_cue <= n <= source.scope_last_cue for n in cue_indices) and
           cue_indices == sorted(set(cue_indices)), 'INVALID_CUE_ANCHORS')
    return json_digest([{'cue_index':n,
                         'original_cue_text_sha256':sha256(source.cues[n-1].text.encode('utf-8'))}
                        for n in cue_indices])


def audit_source_meaning_provenance(source, exchange, review):
    """Validate all *accepted* atoms with unidentified speaker/stance in V6.

    A missing optional ledger is allowed only if *no accepted claim* needs it;
    excluded/open atoms never masquerade as accepted research.
    """
    atoms={a['claim_id']:a for a in exchange['atoms']}
    selected={r['claim_id'] for r in review['atom_verdicts']
              if r['status']=='ACCEPT_FOR_RESEARCH' and
              (atoms[r['claim_id']]['speaker']=='UNKNOWN' or
               atoms[r['claim_id']]['stance']=='UNRESOLVED')}
    ledger=review.get('source_meaning_provenance')
    if ledger is None:
        _check(not selected,'LEDGER_REQUIRED_FOR_ACCEPTED_UNKNOWN')
        return None
    required={'schema','source_sha256','manifest_sha256','review_executor',
              'atom_rows','private_chat_source_meaning_sha256'}
    _check(type(ledger) is dict and set(ledger)==required and
           ledger['schema']==SCHEMA and
           ledger['source_sha256']==source.source_sha256 and
           ledger['manifest_sha256']==source.manifest_sha256 and
           ledger['review_executor']=='CHATGPT_IN_CHAT' and
           type(ledger['atom_rows']) is list,
           'SOURCE_OR_SCHEMA_MISMATCH')
    require_hash(ledger['private_chat_source_meaning_sha256'],
                 'V146_CHAT_MEANING_NOTE')
    seen=set()
    for row in ledger['atom_rows']:
        _check(type(row) is dict and set(row)=={
            'claim_id','atom_sha256','source_cue_indices','source_context_sha256',
            'resolved_speaker_role','resolved_speech_act',
            'speaker_identity_not_inferred','source_condition_exception_checked',
            'private_review_note_sha256'},'ROW_SCHEMA')
        cid=row['claim_id']
        _check(type(cid) is str and cid in selected and cid not in seen and
               row['atom_sha256']==json_digest(atoms[cid]) and
               row['resolved_speaker_role'] in ALLOWED_ROLES and
               row['resolved_speech_act'] in ALLOWED_ACTS and
               row['speaker_identity_not_inferred'] is True and
               row['source_condition_exception_checked'] is True,
               'UNANCHORED_OR_UNRESOLVED_ATOM')
        cues=row['source_cue_indices']
        _check(cues==sorted(set(atoms[cid]['context_cue_indices'])) and
               row['source_context_sha256']==_source_anchor_hash(source,cues),
               'CHANGED_OR_PARTIAL_SOURCE_CONTEXT')
        # A named speaker is not inferred solely because a chat flag is True.
        # Source-book quotations explicitly remain attributed to the book.
        if row['resolved_speaker_role']=='SOURCE_BOOK_QUOTE':
            _check(row['resolved_speech_act'] in {'QUOTE','OPINION','CONDITIONAL_ASSERTION'},
                   'BOOK_QUOTE_CONVERTED_INTO_SPEAKER_FACT')
        require_hash(row['private_review_note_sha256'],'V146_ATOM_NOTE')
        seen.add(cid)
    _check(seen==selected,'ACCEPTED_UNKNOWN_ATOM_LEDGER_CENSUS')
    return {'ledger_hash_sha256':json_digest(ledger),
            'source_identity_unresolved_claims_reviewed':len(seen),
            'external_source_authenticity_certified':False,
            'independent_semantic_accuracy_certified':False}
