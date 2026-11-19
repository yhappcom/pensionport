"""V185: fail-closed E3 parent-boundary and qualifier-provenance diagnostics.

All semantic alignments are *possible* links, never equivalence verdicts. An
adjudicator must inspect original video/source before fixing V176 atoms. This
module is read-only; it neither alters the owner journal nor invokes E4.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from typing import Mapping

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput

SCHEMA='IRE_V185_E3_PARENT_QUALIFIER_DIAGNOSTIC_UNAPPROVED_V1'
POSSIBLE_KIND_REPHRASINGS={'OPINION','RECOMMENDATION'}


def _need(ok, message):
    if not ok:
        raise InvalidInput('V185_E3_'+message)


def _one_claims(rows: Mapping):
    result=[]
    for idx in sorted(rows):
        for num, c in enumerate(rows[idx][1]['claims'],1):
            result.append({'cue_index':idx,'ordinal':num,'claim':c})
    return result


def _num_equivalent(a,b):
    # Never treat an empty number list as equivalent to a nonempty list.
    return sorted(set(a['numeric_tokens']))==sorted(set(b['numeric_tokens']))


def _possible_parent_match(a,b,max_cue_shift):
    i=a['cue_index'];j=b['cue_index']
    if i==j or abs(i-j)>max_cue_shift or not _num_equivalent(a['claim'],b['claim']):
        return False
    ka=a['claim']['kind']; kb=b['claim']['kind']
    if ka!=kb and not ({ka,kb}<=POSSIBLE_KIND_REPHRASINGS):
        return False
    left=set(a['claim']['context_cue_indices'])
    right=set(b['claim']['context_cue_indices'])
    return j in left or i in right or len(left&right)>=2


def _qualifier_classification(claim,cues):
    """Literal traceability only; nonmatch is NOT proof of false source meaning."""
    indices=claim['context_cue_indices']
    context=' '.join(cues[n-1].text for n in indices)
    normalized_context=' '.join(context.split())
    result=[]
    for field in ('conditions','exceptions'):
        for item in claim[field]:
            normalized_term=' '.join(item.split())
            literal=(len(normalized_term)>=4 and normalized_term in normalized_context)
            result.append({'field':field,
                           'term_sha256':sha256(item.encode('utf-8')),
                           'verbatim_in_cited_cues':bool(literal),
                           'origin_verified':False})
    return result


def analyze_source_journals(first,second,cues,*,pinned_first_head,pinned_second_head,
                            adjudications=None,pinned_adjudication_head=None,
                            max_cue_shift=4):
    """Return hash-only source-aware *diagnostics*, not a correctness score.

    `first`/`second` are V176/V183 audited snapshots with
    cue-index => (event_sha, verdict). `adjudications` is V184's audited
    (event_sha, classification) map. Snapshot and source pins must have been
    checked by their owner journal readers first; never accept public input.
    """
    _need(type(max_cue_shift) is int and 1<=max_cue_shift<=12,
          'MAX_CUE_SHIFT_RANGE')
    _need(len(cues)>0 and len(first)==len(cues)
          and sorted(first)==list(range(1,len(cues)+1))
          and set(second)<=set(first),'SOURCE_CENSUS_INCOMPLETE')
    for head in (pinned_first_head,pinned_second_head):
        _need(type(head) is str and len(head)==64 and
              all(x in '0123456789abcdef' for x in head), 'JOURNAL_HEAD_NOT_PINNED')
    if adjudications is not None:
        _need(type(pinned_adjudication_head) is str and
              len(pinned_adjudication_head)==64,'ADJUDICATION_HEAD_NOT_PINNED')
        _need(set(adjudications)<=set(second),'ADJUDICATION_WITHOUT_SECOND_REVIEW')
    owner_claims=_one_claims(first)
    second_claims=_one_claims(second)
    first_by_anchor=defaultdict(list)
    second_by_anchor=defaultdict(list)
    for record in owner_claims:
        first_by_anchor[record['cue_index']].append(record)
    for record in second_claims:
        second_by_anchor[record['cue_index']].append(record)
    f_by_cue={i:first_by_anchor[i] for i in second}
    s_by_cue={i:second_by_anchor[i] for i in second}
    possible=[]
    for i in sorted(second):
        a=f_by_cue[i];b=s_by_cue[i]
        if bool(a)==bool(b):
            continue
        if a:
            for f in a:
                for j in range(max(1,i-max_cue_shift),min(len(cues),i+max_cue_shift)+1):
                  for s in second_by_anchor[j]:
                    if _possible_parent_match(f,s,max_cue_shift):
                        possible.append({'cue_index':i,'first_anchor':f['cue_index'],
                          'second_anchor':s['cue_index'],
                          'first_claim_ordinal':f['ordinal'],
                          'second_claim_ordinal':s['ordinal'],
                          'cross_cue_numeric_tokens_preserved':True,
                          'same_kind':f['claim']['kind']==s['claim']['kind'],
                          'semantic_equivalence_proven':False})
        else:
            for s in b:
                for j in range(max(1,i-max_cue_shift),min(len(cues),i+max_cue_shift)+1):
                  for f in first_by_anchor[j]:
                    if _possible_parent_match(f,s,max_cue_shift):
                        possible.append({'cue_index':i,'first_anchor':f['cue_index'],
                          'second_anchor':s['cue_index'],
                          'first_claim_ordinal':f['ordinal'],
                          'second_claim_ordinal':s['ordinal'],
                          'cross_cue_numeric_tokens_preserved':True,
                          'same_kind':f['claim']['kind']==s['claim']['kind'],
                          'semantic_equivalence_proven':False})
    # Stable order, private words never emitted.
    possible.sort(key=lambda x:(x['cue_index'],abs(x['first_anchor']-x['second_anchor']),
                                 x['first_anchor'],x['second_anchor'],x['first_claim_ordinal'],
                                 x['second_claim_ordinal']))
    candidate_counts=Counter(x['cue_index'] for x in possible)
    source_terms=[t for x in owner_claims for t in _qualifier_classification(x['claim'],cues)]
    second_terms=[t for x in second_claims for t in _qualifier_classification(x['claim'],cues)]
    def split_term_counts(terms):
        return {'total_terms':len(terms),
                'exact_original_substring_terms':sum(x['verbatim_in_cited_cues'] for x in terms),
                'not_literal_or_unanchored_terms':sum(not x['verbatim_in_cited_cues'] for x in terms),
                'terms_proven_source_spoken':0}
    categories=Counter()
    if adjudications is not None:
        for _,row in adjudications.values():
            categories[row['category']]+=1
    missed_by_exact_cue=sum(bool(f_by_cue[i])!=bool(s_by_cue[i]) for i in second)
    output={'schema':SCHEMA,
       'pinned_first_journal_head_sha256':pinned_first_head,
       'pinned_second_journal_head_sha256':pinned_second_head,
       'pinned_adjudication_head_sha256':pinned_adjudication_head,
       'source_cues':len(cues),'second_reviewed_cues':len(second),
       'unreviewed_cues':len(cues)-len(second),
       'owner_provisional_claims':len(owner_claims),
       'second_provisional_claims_in_reviewed_subset':len(second_claims),
       'cue_level_claim_presence_differences':missed_by_exact_cue,
       'possible_cross_cue_parent_alignment_cues':len(candidate_counts),
       'possible_cross_cue_parent_alignments':len(possible),
       'ambiguous_alignment_cues':sum(v>1 for v in candidate_counts.values()),
       'possible_parent_links':possible,
       'first_qualifier_provenance':split_term_counts(source_terms),
       'second_qualifier_provenance':split_term_counts(second_terms),
       'adjudicated_causes':dict(sorted(categories.items())),
       'all_reviewed_source_qualifiers_verified':False,
       'source_spoken_and_reviewer_added_qualifiers_separated_in_native_v6':False,
       'accuracy_precision_certified':False,'accuracy_recall_certified':False,
       'independent_gold_certified':False,'e3_quality_certified':False,
       'v123_approved':False,'e4_approved':False,'e5_published':False}
    return output


def analyze_live_owner(adjudication,*,max_cue_shift=4):
    """Execute V176+V183+V184 existing full hash-chain audits read-only."""
    second=adjudication.second
    owner=second._owner_snapshot()
    with second._db() as db:
        second_head,reviewed=second._audit(db)
    with adjudication._db() as db:
        adj_head,adjudicated=adjudication._audit(db)
    return analyze_source_journals(
        owner,reviewed,second.engine.source.cues,
        pinned_first_head=second.expected_owner_head,pinned_second_head=second_head,
        adjudications=adjudicated,pinned_adjudication_head=adj_head,
        max_cue_shift=max_cue_shift)