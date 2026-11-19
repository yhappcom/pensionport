"""V188 fail-closed E3 full-census/reconciliation gate; never E4/E5 approval.

IMPORTANT: 250/250 source-first, 250/250 independently repeated source-only
judgments, or 149/149 disagreement cause labels are NOT semantic accuracy.
This module reads V176/V183/V184 hash-audited owner-private journals, confirms
coverage and bound cause labels, and emits only counts/IDs and pinned hashes.
It never changes any past judgment, infers claim equivalence, claims gold
independence, or turns provisional video knowledge into financial advice.
"""
from __future__ import annotations
from collections import Counter
from ire.v6.errors import InvalidInput
from v185_e3_parent_qualifier_audit import analyze_source_journals

SCHEMA='IRE_V188_E3_CENSUS_CAUSAL_READINESS_FAIL_CLOSED_V1'
CAUSE_ACTIONS={
 'CONFIRMED_FIRST_PASS_OMISSION': 'REPAIR_FIRST_PASS_ON_NEW_PINNED_OVERLAY',
 'CONFIRMED_SECOND_PASS_OMISSION': 'REPAIR_SECOND_PASS_ON_NEW_PINNED_OVERLAY',
 'CLAIM_BOUNDARY_DISAGREEMENT': 'ADJUDICATE_PARENT_CLAIM_IDENTITY',
 'REVIEWER_QUALIFIER_ADDITION': 'VERIFY_QUALIFIER_SOURCE_PROVENANCE',
 'MISSING_AUDIO_VISUAL': 'SOURCE_AUDIO_OR_SCREEN_EVIDENCE_REQUIRED',
 'SOURCE_CLAIM_SCOPE_OPEN': 'CHECK_SCOPE_AND_PRIMARY_SOURCE',
 'UNRESOLVED_NEEDS_REVIEW': 'MANUAL_SEMANTIC_RECHECK',
 'SEMANTIC_EQUIVALENCE_WORDING': 'VERIFY_EQUIVALENCE_WITH_FIXED_GOLD',
}
RANK={
 'CONFIRMED_FIRST_PASS_OMISSION':0,
 'CONFIRMED_SECOND_PASS_OMISSION':0,
 'MISSING_AUDIO_VISUAL':0,
 'SOURCE_CLAIM_SCOPE_OPEN':0,
 'UNRESOLVED_NEEDS_REVIEW':0,
 'CLAIM_BOUNDARY_DISAGREEMENT':1,
 'REVIEWER_QUALIFIER_ADDITION':1,
 'SEMANTIC_EQUIVALENCE_WORDING':2,
}

def _need(ok,code):
    if not ok:raise InvalidInput('V188_E3_'+code)

def build_gate(*,source_cues,first_rows,second_rows,adjudication_rows,
               source_sha256,first_head_sha256,second_head_sha256,
               adjudication_head_sha256,reviewer_source_independent=False,
               max_cue_shift=8):
    """Accept *already audited* journal dictionaries; untrusted callers must
    use evaluate_live() so snapshot integrity and source pins are checked.
    """
    total=len(source_cues)
    _need(total>0 and sorted(first_rows)==list(range(1,total+1)) and
          set(second_rows)<=set(first_rows) and
          set(adjudication_rows)<=set(second_rows),
          'CENSUS_OR_REVIEW_SUBSET_INVALID')
    _need(reviewer_source_independent is False, 'INDEPENDENCE_NOT_PROVEN')
    _need(type(max_cue_shift) is int and 1<=max_cue_shift<=12,
          'MAX_PARENT_SHIFT_INVALID')
    for h in (source_sha256,first_head_sha256,second_head_sha256,adjudication_head_sha256):
        _need(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),
              'ORIGINAL_JOURNAL_DIGEST_INVALID')
    differences={}
    for i in sorted(second_rows):
        first=first_rows[i][1]
        second=second_rows[i][1]
        diff=[]
        if first['disposition']!=second['disposition']:diff.append('DISPOSITION')
        if first['speaker_role']!=second['speaker_role']:diff.append('SPEAKER_ROLE')
        aa=first['claims'];bb=second['claims']
        if len(aa)!=len(bb):diff.append('ATOMIC_CLAIM_COUNT')
        for field in ('kind','proposition','quote','context_cue_indices','conditions',
                      'exceptions','numeric_tokens','high_risk','needs_official_source'):
            if [x[field] for x in aa]!=[x[field] for x in bb]:
                diff.append('CLAIM_'+field.upper())
        if diff or first['disposition']=='OPEN' or second['disposition']=='OPEN':
            differences[i]=diff
    _need(set(adjudication_rows)<=set(differences),
          'ADJUDICATION_FOR_UNFLAGGED_CUE')
    causes=Counter()
    action_items=[]
    for idx,(_,ans) in adjudication_rows.items():
        cause=ans['category']
        _need(cause in CAUSE_ACTIONS,'UNKNOWN_CAUSE_CATEGORY')
        causes[cause]+=1
        needs=bool(first_rows[idx][1]['claims'] or second_rows[idx][1]['claims'])
        action_items.append({'cue_index':idx,'cause':cause,'action':CAUSE_ACTIONS[cause],
                             'source_financial_claim_present':needs,
                             'priority':'P0' if RANK[cause]==0 else
                                        'P1' if RANK[cause]==1 else 'P2',
                             'source_financial_truth_certified':False,
                             'claim_identity_resolved':False})
    pending=sorted(set(differences)-set(adjudication_rows))
    diagnostic=analyze_source_journals(first_rows,second_rows,source_cues,
        pinned_first_head=first_head_sha256,pinned_second_head=second_head_sha256,
        adjudications=adjudication_rows,pinned_adjudication_head=adjudication_head_sha256,
        max_cue_shift=max_cue_shift)
    p0=sorted((x for x in action_items if x['priority']=='P0'),key=lambda x:x['cue_index'])
    # Cause labels and possible parent links are hypotheses, not gold evidence.
    # Even zero pending labels does not close any repair/evidence/action or E3.
    return {
      'schema':SCHEMA,'source_sha256':source_sha256,
      'first_journal_head_sha256':first_head_sha256,
      'second_journal_head_sha256':second_head_sha256,
      'adjudication_journal_head_sha256':adjudication_head_sha256,
      'source_cues':total,'first_cues':len(first_rows),
      'second_cues':len(second_rows),'second_unreviewed_cues':total-len(second_rows),
      'first_candidate_atoms':sum(len(x[1]['claims']) for x in first_rows.values()),
      'second_candidate_atoms':sum(len(x[1]['claims']) for x in second_rows.values()),
      'disagreement_or_open_cues':len(differences),
      'cause_labels_reviewed':len(adjudication_rows),
      'unclassified_disagreement_or_open_cues':len(pending),
      'unclassified_cue_indices':pending,
      'adjudicated_causes':dict(sorted(causes.items())),
      'suspected_first_omission_cue_indices':sorted(x['cue_index'] for x in action_items
        if x['cause']=='CONFIRMED_FIRST_PASS_OMISSION'),
      'suspected_second_omission_cue_indices':sorted(x['cue_index'] for x in action_items
        if x['cause']=='CONFIRMED_SECOND_PASS_OMISSION'),
      'possible_parent_links':diagnostic['possible_cross_cue_parent_alignments'],
      'possible_parent_alignment_cues':diagnostic['possible_cross_cue_parent_alignment_cues'],
      'ambiguous_parent_alignment_cues':diagnostic['ambiguous_alignment_cues'],
      'exact_cue_claim_presence_differences':diagnostic['cue_level_claim_presence_differences'],
      'priority_zero_actions':p0,
      'open_issues_require_new_source_pinned_overlay':True,
      'first_and_second_original_journals_immutable':True,
      'no_original_private_propositions_exported':True,
      'independent_gold_precision':None,'independent_gold_recall':None,
      'independent_gold_high_risk_misses':None,
      'model_reviewer_psychologically_independent_verified':False,
      'e3_accuracy_certified':False,'v123_invoked':False,
      'e4_invoked':False,'e4_approved':False,'e5_published':False,
      'decision':'E3_HOLD_E4_E5_BLOCKED_NEEDS_INDEPENDENT_GOLD_AND_SOURCE_REPAIRS'
    }

def evaluate_live(adjudication,*,max_cue_shift=8):
    """Read-only authenticated proof against three real private SQLite journals."""
    second=adjudication.second
    engine=second.engine
    first=second._owner_snapshot()
    with second._db() as db:
        second_head,reviewed=second._audit(db)
    with adjudication._db() as db:
        adj_head,adjudicated=adjudication._audit(db)
    result=build_gate(source_cues=engine.source.cues,
        first_rows=first,second_rows=reviewed,adjudication_rows=adjudicated,
        source_sha256=engine.source.source_sha256,
        first_head_sha256=second.expected_owner_head,
        second_head_sha256=second_head,adjudication_head_sha256=adj_head,
        max_cue_shift=max_cue_shift)
    _need(engine.progress()['checkpoint_head_sha256']==second.expected_owner_head,
          'OWNER_HEAD_CHANGED_DURING_EVALUATION')
    return result