"""V41 private V40-checkpoint to V6-shaped atomic-proposal preflight.

Checks source-anchored *proposal* coverage, never semantic truth. The old
V6 final atomic exchange and advisory approval are not bypassed or invoked.
Requires an actual private V40 store and an exact replay of each selected
V40 checkpoint group before inspecting candidate-to-atom mappings.
Do not publish raw_srt, host_rows, atomic propositions or explanations.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import re

from .codec import json_digest, sha256
from .errors import InvalidInput, LedgerCorrupted
from .host_semantic_custody_v39 import audit_host_semantic_custody_v39
from .atomic_exchange import NUMBER
from .source import parse_srt

_CID = re.compile(r'C\d{5,8}\Z')
_WIN = re.compile(r'W\d{5}\Z')
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_KINDS = {'FACT', 'HYPOTHETICAL', 'QUESTION', 'OPINION', 'RECOMMENDATION', 'MATH'}
_STANCES = {'AFFIRMED', 'NEGATED', 'CORRECTED', 'CONDITIONAL', 'QUOTED', 'UNRESOLVED'}
_SPEAKERS = {'NARRATOR', 'GUEST', 'QUESTIONER', 'QUOTED_SOURCE', 'UNKNOWN'}
_ATOM_KEYS = {'claim_id', 'owner_window_id', 'proposition', 'kind', 'stance',
              'speaker', 'source_refs', 'context_cue_indices',
              'condition_cue_indices', 'exception_cue_indices',
              'numeric_references', 'as_of'}
_LINK_KEYS = {'video_id', 'window_id', 'candidate_id', 'note_index',
              'disposition', 'atom_ids', 'reason'}
_DISPOSITIONS = {'PROPOSE_ATOMS', 'OPEN_REQUIRES_REVIEW', 'CONTEXT_ONLY'}


def _indices(x, max_i, *, allow_empty=True):
    return (type(x) is list and (allow_empty or bool(x)) and
            all(type(k) is int and 1 <= k <= max_i for k in x) and
            x == sorted(set(x)))


def _replay_private_v40(v40_store, originals, source_pins, window_pins, host_rows):
    """Replay exactly each recorded V40 batch: no unpinned/uncommitted window."""
    if v40_store is None or not hasattr(v40_store, 'verify_chain') or not hasattr(v40_store, '_connect'):
        raise InvalidInput('V41_REAL_PRIVATE_V40_LEDGER_REQUIRED')
    pins_by_video = {x['video_id']: x for x in source_pins}
    if len(pins_by_video) != len(source_pins):
        raise InvalidInput('V41_DUPLICATE_SOURCE_PIN')
    meta = {}
    by_win = defaultdict(dict)
    for w in window_pins:
        if w['window_id'] in by_win[w['video_id']]:
            raise InvalidInput('V41_DUPLICATE_V40_WINDOW_PIN')
        by_win[w['video_id']][w['window_id']] = w
    for vid, vpin in pins_by_video.items():
        if vid not in originals or vid not in by_win:
            raise InvalidInput('V41_ORIGINAL_VIDEO_OR_WINDOW_NOT_SUPPLIED')
        chain = v40_store.verify_chain(vid, vpin['original_srt_sha256'])
        if not chain['all_window_receipts_integrity_passed']:
            raise LedgerCorrupted('V41_V40_CHECKPOINT_CHAIN_NOT_VALIDATED')
        with v40_store._connect() as con:
            checkpoints = [dict(r) for r in con.execute(
                'SELECT * FROM v40_checkpoints WHERE video_id=? AND original_source_sha256=? ORDER BY sequence',
                (vid, vpin['original_srt_sha256']))]
        if not checkpoints:
            raise InvalidInput('V41_MISSING_V40_CHECKPOINT')
        selected = set(by_win[vid])
        accounted = set()
        for cp in checkpoints:
            group = json.loads(cp['window_ids_json'])
            used = selected.intersection(group)
            if not used:
                continue
            if set(group) != used:
                raise InvalidInput('V41_PARTIAL_V40_CHECKPOINT_GROUP_NOT_REPLAYED')
            group_pins = [by_win[vid][wid] for wid in group]
            group_rows = [r for r in host_rows if r['video_id'] == vid and r['window_id'] in used]
            child = audit_host_semantic_custody_v39({vid: originals[vid]}, [vpin],
                                                      group_pins, group_rows)
            if (child['receipt_sha256'] != cp['semantic_receipt_sha256'] or
                cp['reviewed_windows'] != len(group) or
                cp['reviewed_candidates'] != child['host_reviewed_candidates'] or
                cp['semantic_notes_including_questions'] != child['chat_review_items_including_questions']):
                raise InvalidInput('V41_V40_CHECKPOINT_NOT_SAME_CHAT_REVIEW_SOURCE')
            accounted.update(used)
        if accounted != selected:
            raise InvalidInput('V41_UNCOMMITTED_OR_UNKNOWN_V40_WINDOW')
        meta[vid] = {'checkpoint_groups_replayed': len([cp for cp in checkpoints if set(
            json.loads(cp['window_ids_json'])) & selected]),
                     'checkpoint_head_sha256': chain['head_sha256']}
    return meta


def audit_v40_to_v6_atom_handoff_v41(v40_store, original_srt_bytes, source_pins,
                                      window_pins, host_rows, target_windows,
                                      proposed_atoms, note_links):
    """Fail-closed mapping from all V39 notes in selected windows to atom frames.

    The caller MUST bring all private V40 checkpoint batch windows (and all
    corresponding host rows) for replay, but may atomize a selected subset.
    A review-only/open note remains OPEN. Even complete mappings are proposals,
    NOT final V6 atom exchange, publisher-verified facts or blind gold.
    """
    if (type(source_pins) is not list or len(source_pins)!=1 or
        type(target_windows) is not list or not target_windows or
        type(proposed_atoms) is not list or type(note_links) is not list or
        type(original_srt_bytes) is not dict):
        raise InvalidInput('V41_ATOMIC_HANDOFF_INPUTS_REQUIRED')
    source_v39 = audit_host_semantic_custody_v39(original_srt_bytes,
                                                source_pins, window_pins, host_rows)
    chains = _replay_private_v40(v40_store, original_srt_bytes, source_pins,
                                 window_pins, host_rows)
    targets = set()
    available = {(w['video_id'], w['window_id']) for w in window_pins}
    for t in target_windows:
        if (type(t) is not dict or set(t) != {'video_id','window_id'} or
            (t['video_id'], t['window_id']) not in available or
            (t['video_id'], t['window_id']) in targets):
            raise InvalidInput('V41_TARGET_WINDOW_NOT_V40_VERIFIED_OR_DUPLICATE')
        targets.add((t['video_id'], t['window_id']))
    candidates = {}
    needed = set()
    for r in host_rows:
        key = (r['video_id'],r['window_id'])
        if key in targets:
            cid = r['claim_id']
            candidates[(r['video_id'], r['window_id'], cid)] = r
            needed.update((r['video_id'],r['window_id'],cid,i)
                          for i in range(len(r['semantic_notes'])))
    if not candidates or not needed:
        raise InvalidInput('V41_TARGET_HAS_NO_V39_SEMANTIC_NOTES')
    parsed = {vid:parse_srt(raw) for vid,raw in original_srt_bytes.items()}
    atoms = {}
    for atom in proposed_atoms:
        if type(atom) is not dict or set(atom) != _ATOM_KEYS:
            raise InvalidInput('V41_ATOM_FRAME_SCHEMA_INVALID')
        cid = atom['claim_id']
        if (type(cid) is not str or not _CID.fullmatch(cid) or cid in atoms or
            type(atom['owner_window_id']) is not str or
            not _WIN.fullmatch(atom['owner_window_id']) or
            type(atom['proposition']) is not str or
            not 5 <= len(atom['proposition'].strip()) <= 3000 or
            atom['kind'] not in _KINDS or atom['stance'] not in _STANCES or
            atom['speaker'] not in _SPEAKERS or
            (atom['as_of'] is not None and not (type(atom['as_of']) is str and
                re.fullmatch(r'\d{4}-\d{2}-\d{2}',atom['as_of'])))):
            raise InvalidInput('V41_DUPLICATE_OR_INVALID_ATOM')
        atoms[cid] = atom
    if not proposed_atoms:
        raise InvalidInput('V41_NO_FINAL_ATOM_PROPOSALS')
    linked = set()
    seen = set()
    open_notes = 0
    safe = []
    for row in note_links:
        if type(row) is not dict or set(row) != _LINK_KEYS:
            raise InvalidInput('V41_NOTE_LINK_SCHEMA_INVALID')
        key = (row['video_id'],row['window_id'],row['candidate_id'],row['note_index'])
        if (key not in needed or key in seen or type(row['note_index']) is not int):
            raise InvalidInput('V41_UNEXPECTED_OR_DUPLICATE_NOTE_LINK')
        seen.add(key)
        host = candidates[key[:3]]
        note = host['semantic_notes'][key[3]]
        disposition = row['disposition']
        ids = row['atom_ids']
        if (disposition not in _DISPOSITIONS or type(ids) is not list or
            ids != sorted(set(ids)) or
            type(row['reason']) is not str or not 20<=len(row['reason'].strip())<=1500):
            raise InvalidInput('V41_NOTE_DISPOSITION_OR_REASON_INVALID')
        if note['kind']=='F' and (disposition!='CONTEXT_ONLY' or ids):
            raise InvalidInput('V41_CONTEXT_FRAGMENT_CANNOT_BECOME_ATOM')
        if note['kind']!='F' and disposition=='CONTEXT_ONLY':
            raise InvalidInput('V41_NON_FRAGMENT_SILENTLY_DISCARDED')
        if disposition=='PROPOSE_ATOMS' and not ids:
            raise InvalidInput('V41_CLAIM_NOTE_HAS_NO_ATOM')
        if disposition!='PROPOSE_ATOMS' and ids:
            raise InvalidInput('V41_OPEN_OR_CONTEXT_NOTE_MUST_NOT_LINK_ATOM')
        if disposition=='OPEN_REQUIRES_REVIEW':
            open_notes += 1
        for aid in ids:
            if aid not in atoms:
                raise InvalidInput('V41_UNDECLARED_V6_ATOM_ID')
            atom=atoms[aid]
            if atom['owner_window_id']!=row['window_id']:
                raise InvalidInput('V41_ATOM_WINDOW_OWNER_DRIFT')
            # A separate safeguard, not a meaning classifier. Preserve
            # explicit negation, question, historical hypotheticals and advice.
            if (note['kind']=='Q' and atom['kind']!='QUESTION' or
                note['kind']=='H' and atom['kind'] not in ('HYPOTHETICAL','MATH') or
                note['kind']=='R' and atom['kind']!='RECOMMENDATION' or
                note['kind']=='X' and atom['stance'] not in ('NEGATED','CORRECTED','UNRESOLVED') or
                note['kind']=='U' and atom['stance']=='AFFIRMED' or
                note['kind']=='D' and atom['speaker']=='NARRATOR' and atom['stance']!='QUOTED'):
                raise InvalidInput('V41_SPEAKER_HYPOTHESIS_QUESTION_STANCE_INVERTED')
            refs=atom['source_refs']
            if (type(refs) is not list or not refs or len(refs)>80 or
                any(type(ref) is not dict or set(ref)!={'cue_index','quote'} for ref in refs)):
                raise InvalidInput('V41_ATOM_SOURCE_REF_SCHEMA_INVALID')
            idxs=[ref['cue_index'] for ref in refs]
            if (not _indices(idxs,len(parsed[row['video_id']]),allow_empty=False) or
                not set(idxs).intersection(host['cue_indices'])):
                raise InvalidInput('V41_ATOM_NOT_ANCHORED_TO_SOURCE_CANDIDATE')
            for ref in refs:
                cue=parsed[row['video_id']][ref['cue_index']-1].text
                quote=ref['quote']
                if (type(quote) is not str or len(quote.strip())<2 or
                    ' '.join(quote.casefold().split()) not in ' '.join(cue.casefold().split())):
                    raise InvalidInput('V41_ATOM_QUOTE_NOT_IN_PRIVATE_SRT')
            context=atom['context_cue_indices']
            conditions=atom['condition_cue_indices']
            exceptions=atom['exception_cue_indices']
            if (not _indices(context,len(parsed[row['video_id']]),allow_empty=False) or
                not _indices(conditions,len(parsed[row['video_id']])) or
                not _indices(exceptions,len(parsed[row['video_id']])) or
                not set(idxs+conditions+exceptions).issubset(context) or
                atom['stance']=='CONDITIONAL' and not conditions):
                raise InvalidInput('V41_CONDITION_EXCEPTION_CONTEXT_NOT_GROUNDED')
            nums=atom['numeric_references']
            if type(nums) is not list or any(type(n) is not dict or
                set(n)!={'cue_index','token'} or n['cue_index'] not in context or
                type(n['token']) is not str or n['token'] not in parsed[row['video_id']][n['cue_index']-1].text
                for n in nums):
                raise InvalidInput('V41_NUMERIC_REFERENCE_NOT_IN_SOURCE')
            all_source_tokens=[]
            for n in nums:
                if n['token'] not in NUMBER.findall(parsed[row['video_id']][n['cue_index']-1].text):
                    raise InvalidInput('V41_NUMERIC_TOKEN_NOT_VERBATIM')
                all_source_tokens.append(re.sub(r'\s+','',n['token']))
            if any(re.sub(r'\s+','',token) not in all_source_tokens
                   for token in NUMBER.findall(atom['proposition'])):
                raise InvalidInput('V41_PROPOSITION_NUMBER_UNGROUNDED')
            linked.add(aid)
        safe.append({'video_id':row['video_id'],'window_id':row['window_id'],
                     'candidate_id':row['candidate_id'],'note_index':row['note_index'],
                     'disposition':disposition, 'atom_ids':ids,
                     'reason_sha256':sha256(row['reason'].encode('utf-8'))})
    if seen!=needed:
        raise InvalidInput('V41_NOT_ALL_SEMANTIC_NOTES_DISPOSITIONED')
    if linked!=set(atoms):
        raise InvalidInput('V41_ORPHAN_ATOM_WITHOUT_SOURCE_NOTE')
    # The same proposed atom may only be referenced by a single V39 note.
    references=Counter(aid for x in safe for aid in x['atom_ids'])
    if references and any(n != 1 for n in references.values()):
        raise InvalidInput('V41_DUPLICATE_ATOM_NOTE_OWNERSHIP')
    # Crosswalk is local and non-independent. The entire proposal remains
    # blocked from authoritative V6 atomic batch until *full* cue coverage.
    result={'schema':'IRE_V6_V41_V40_TO_V6_PRE_ATOMIC_CROSSWALK_HASH_ONLY',
            'v39_full_replay_receipt_sha256':source_v39['receipt_sha256'],
            'real_v40_checkpoint_groups_replayed':sum(x['checkpoint_groups_replayed'] for x in chains.values()),
            'selected_source_window_count':len(targets),
            'source_v33_utterances_mapped':len(candidates),
            'all_v39_review_notes_dispositioned':len(needed),
            'proposed_atomic_frames':len(atoms),
            'open_notes':open_notes,
            'source_bound_atom_mapping_sha256':json_digest(sorted(safe,key=lambda x:(x['video_id'],x['window_id'],x['candidate_id'],x['note_index']))),
            'proposed_atom_frames_sha256':json_digest(sorted(atoms.values(),key=lambda x:x['claim_id'])),
            'private_source_or_semantic_prose_published':False,
            'v6_atomic_exchange_complete_and_approved':False,
            'independent_financial_semantic_truth_verified':False,
            'final_model_commit_authorized':False,'p0_go':False}
    result['receipt_sha256']=json_digest(result)
    return result
