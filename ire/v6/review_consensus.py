"""Strict, auditable two-draft atomic consensus lineage for P0-2-05.

Validates structural source-cue disagreements and final gold provenance only.
It cannot prove a reviewer's interpretation correct or their sessions isolated;
those require separate host-verified independent provenance.
"""
from __future__ import annotations

from .codec import json_digest
from .errors import InvalidInput

_SEMANTIC = (
    'kind', 'risk', 'proposition', 'speaker_stance', 'as_of',
    'high_risk_reason', 'source_refs', 'conditions', 'exceptions',
    'numeric_evidence',
)
_DISPOSITIONS = {'BOTH_SUPPORTED', 'RECONCILED_VARIANT',
                 'REVIEWER_ONE_ONLY', 'REVIEWER_TWO_ONLY'}


def _fail(code: str):
    raise InvalidInput('P205_CONSENSUS_' + code)


def _nonempty(x):
    return type(x) is str and len(x.strip()) >= 8


def _claim_sig(claim):
    return json_digest({k: claim.get(k) for k in _SEMANTIC})


def _indices(claim):
    return {r['cue_index'] for r in claim['source_refs']}


def verify_two_review_consensus_lineage(drafts: dict, gold: dict,
                                        body: dict) -> dict:
    """Require signed consensus body to enumerate all substantive draft diffs.

    Inputs have already been source-quote-verified and reviewer-host signed by
    the production gate. The body is signed *after* these fields are prepared.
    """
    if type(drafts) is not dict or set(drafts) != {'reviewer_one', 'reviewer_two'}:
        _fail('REVIEWER_DRAFTS_MISSING')
    if type(gold) is not dict or type(body) is not dict:
        _fail('CONSENSUS_NOT_STRUCTURED')
    reviews={};byid={};bycue={};status={}
    for role,draft in {**drafts,'gold':gold}.items():
        if (type(draft) is not dict or type(draft.get('atomic_gold_claims')) is not list
                or type(draft.get('reviewed_cues')) is not list):
            _fail('DRAFT_OR_FINAL_GOLD_MALFORMED')
        atom_list=draft['atomic_gold_claims']
        atoms={a.get('gold_id'):a for a in atom_list}
        if len(atoms)!=len(atom_list) or any(type(k) is not str or not k for k in atoms):
            _fail('DRAFT_CLAIM_IDS_INVALID')
        byid[role]=atoms
        reviews[role]=draft['reviewed_cues']
        bycue[role]={};status[role]={}
        for cue in draft['reviewed_cues']:
            idx=cue.get('cue_index')
            if type(idx) is not int or idx in bycue[role]:
                _fail('DRAFT_CUE_INDICES_INVALID')
            ids=cue.get('gold_atom_ids')
            if type(ids) is not list or any(type(i) is not str or i not in atoms for i in ids):
                _fail('DRAFT_CUE_CLAIM_REFERENCES_INVALID')
            if not _nonempty(cue.get('reason')):
                _fail('DRAFT_CUE_REASON_REQUIRED')
            bycue[role][idx]=set(ids)
            status[role][idx]=cue.get('status')
    cues=set(bycue['gold'])
    if (set(bycue['reviewer_one'])!=cues or set(bycue['reviewer_two'])!=cues
            or cues != set(range(1,len(cues)+1))):
        _fail('REVIEWER_CUE_SETS_DIFFER')

    disputed=set()
    for idx in cues:
        sems=[]
        for role in ('reviewer_one','reviewer_two'):
            sems.append((status[role][idx],
                         sorted(_claim_sig(byid[role][gid]) for gid in bycue[role][idx])))
        if sems[0]!=sems[1]:
            disputed.add(idx)

    resolutions=body.get('disagreement_resolutions')
    if type(resolutions) is not list:
        _fail('PER_CUE_RESOLUTIONS_MISSING')
    seen=set()
    for rec in resolutions:
        if (type(rec) is not dict or set(rec)!={'cue_index',
                'reviewer_one_gold_ids','reviewer_two_gold_ids','final_gold_ids',
                'reason','resolution'}):
            _fail('RESOLUTION_ROW_SHAPE_INVALID')
        idx=rec['cue_index']
        if type(idx) is not int or idx in seen or idx not in disputed:
            _fail('RESOLUTION_CUE_NOT_ACTUALLY_DISPUTED')
        seen.add(idx)
        if (not _nonempty(rec['reason']) or not _nonempty(rec['resolution'])
                or any(type(rec[key]) is not list or len(rec[key])!=len(set(rec[key]))
                        for key in ('reviewer_one_gold_ids','reviewer_two_gold_ids','final_gold_ids'))):
            _fail('RESOLUTION_NOT_EXPLAINED')
        for key,role in (('reviewer_one_gold_ids','reviewer_one'),
                         ('reviewer_two_gold_ids','reviewer_two'),
                         ('final_gold_ids','gold')):
            if set(rec[key]) != bycue[role][idx]:
                _fail('RESOLUTION_SOURCE_CUE_CLAIM_IDS_WRONG')
    if disputed != seen:
        _fail('UNRECORDED_REVIEWER_DISAGREEMENT')
    if (type(body.get('disagreements_count')) is not int or
        type(body.get('resolved_disagreements_count')) is not int or
        body['disagreements_count']!=len(disputed) or
        body['resolved_disagreements_count']!=len(seen)):
        _fail('RECONCILIATION_COUNTS_NOT_DERIVED')

    origins=body.get('final_gold_provenance')
    if type(origins) is not list or len(origins)!=len(byid['gold']):
        _fail('FINAL_GOLD_LINEAGE_INCOMPLETE')
    seen_gold=set();used={'reviewer_one':set(),'reviewer_two':set()}
    for row in origins:
        if (type(row) is not dict or set(row)!={'gold_id','reviewer_one_gold_ids',
              'reviewer_two_gold_ids','disposition','reason'}):
            _fail('FINAL_GOLD_LINEAGE_ROW_INVALID')
        gid=row['gold_id']
        if type(gid) is not str or gid in seen_gold or gid not in byid['gold']:
            _fail('FINAL_GOLD_LINEAGE_ID_INVALID')
        seen_gold.add(gid)
        final=byid['gold'][gid]
        final_indices=_indices(final)
        if not _nonempty(row['reason']):
            _fail('FINAL_GOLD_LINEAGE_REASON_REQUIRED')
        refs={}
        for role in ('reviewer_one','reviewer_two'):
            ids=row[role+'_gold_ids']
            if (type(ids) is not list or len(ids)!=len(set(ids)) or
                  any(type(k) is not str or k not in byid[role] for k in ids)):
                _fail('FINAL_GOLD_LINEAGE_REVIEWER_ID_INVALID')
            for k in ids:
                if not final_indices.intersection(_indices(byid[role][k])):
                    _fail('FINAL_GOLD_LINEAGE_SOURCE_CUE_NOT_SHARED')
            used[role].update(ids)
            refs[role]=ids
        if not any(refs.values()):
            _fail('UNSUPPORTED_NEW_GOLD_ATOM_NEEDS_TWO_NEW_REVIEWS')
        disposition=row['disposition']
        if disposition not in _DISPOSITIONS:
            _fail('FINAL_GOLD_LINEAGE_DISPOSITION_INVALID')
        all_equal=(refs['reviewer_one'] and refs['reviewer_two'] and
                   all(_claim_sig(byid[role][k])==_claim_sig(final)
                       for role in ('reviewer_one','reviewer_two') for k in refs[role]))
        if disposition=='BOTH_SUPPORTED' and not all_equal:
            _fail('FALSE_UNANIMOUS_GOLD_SUPPORT')
        if disposition=='REVIEWER_ONE_ONLY' and not (refs['reviewer_one'] and not refs['reviewer_two']):
            _fail('FALSE_REVIEWER_ONE_ONLY')
        if disposition=='REVIEWER_TWO_ONLY' and not (refs['reviewer_two'] and not refs['reviewer_one']):
            _fail('FALSE_REVIEWER_TWO_ONLY')
        if disposition=='RECONCILED_VARIANT' and not (refs['reviewer_one'] and refs['reviewer_two'] and not all_equal):
            _fail('FALSE_CONSENSUS_VARIANT')
        if disposition!='BOTH_SUPPORTED' and not final_indices.intersection(disputed):
            _fail('CHANGED_GOLD_WITHOUT_REVIEWER_DISPUTE')
    if seen_gold != set(byid['gold']):
        _fail('SILENTLY_UNACCOUNTED_FINAL_GOLD_CLAIMS')

    dropped=body.get('excluded_draft_claims')
    if type(dropped) is not list:
        _fail('EXCLUDED_REVIEWER_CLAIMS_LEDGER_MISSING')
    exclusions={'reviewer_one':set(),'reviewer_two':set()}
    for row in dropped:
        if (type(row) is not dict or set(row)!={'role','gold_id','reason'}):
            _fail('EXCLUDED_REVIEWER_CLAIM_SHAPE_INVALID')
        role=row['role'];gid=row['gold_id']
        if (role not in exclusions or type(gid) is not str or
            gid not in byid[role] or gid in used[role] or gid in exclusions[role] or
            not _nonempty(row['reason'])):
            _fail('EXCLUDED_REVIEWER_CLAIM_INVALID')
        if not _indices(byid[role][gid]).intersection(disputed):
            _fail('SILENT_DISCARD_OF_UNCONTESTED_DRAFT_CLAIM')
        exclusions[role].add(gid)
    for role in ('reviewer_one','reviewer_two'):
        if used[role] | exclusions[role] != set(byid[role]):
            _fail('DRAFT_GOLD_CLAIMS_SILENTLY_DROPPED')
    return {
        'disputed_cue_count':len(disputed),
        'resolved_cue_count':len(seen),
        'final_gold_claims_traced':len(seen_gold),
        'excluded_draft_claims':len(dropped),
        'reviewer_claims_fully_accounted':True,
        'semantic_gold_truth_verified':False,
    }
