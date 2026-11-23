"""Source-to-gold bidirectional traceability, without claiming independent truth.

The 250 cue dispositions and every atomic gold claim must reference each other
exactly.  This blocks laundering a blank/NO_ATOM census into a full-gold score.
Only source bytes, not reviewer assertions, establish cue hash/quote identity.
"""
from __future__ import annotations

from .codec import sha256
from .errors import InvalidInput


def verify_gold_cue_trace(cues, gold: dict) -> dict:
    """Validate the *shape and bidirectional evidence graph* of a reviewer gold.

    This cannot detect unextracted propositions; two genuinely isolated reviews
    and their host provenance remain a separate and mandatory trust boundary.
    """
    if type(gold) is not dict:
        raise InvalidInput('P205_GOLD_TRACE_DOCUMENT_REQUIRED')
    atoms = gold.get('atomic_gold_claims')
    reviews = gold.get('reviewed_cues')
    if type(atoms) is not list or type(reviews) is not list:
        raise InvalidInput('P205_GOLD_TRACE_ATOMS_AND_CUES_REQUIRED')
    if len(reviews) != len(cues):
        raise InvalidInput('P205_GOLD_TRACE_CUE_CENSUS_INCOMPLETE')
    by_cue: dict[int, set[str]] = {i:set() for i in range(1,len(cues)+1)}
    ids=set()
    for claim in atoms:
        if type(claim) is not dict or type(claim.get('gold_id')) is not str or not claim['gold_id'].strip():
            raise InvalidInput('P205_GOLD_TRACE_CLAIM_ID_INVALID')
        gid=claim['gold_id']
        if gid in ids:
            raise InvalidInput('P205_GOLD_TRACE_DUPLICATE_CLAIM_ID')
        ids.add(gid)
        refs=claim.get('source_refs')
        if type(refs) is not list or not refs:
            raise InvalidInput('P205_GOLD_TRACE_MISSING_SOURCE_REFS')
        seen=set()
        for ref in refs:
            if type(ref) is not dict or type(ref.get('cue_index')) is not int:
                raise InvalidInput('P205_GOLD_TRACE_REF_SCHEMA_INVALID')
            idx=ref['cue_index']
            if not 1<=idx<=len(cues) or idx in seen:
                raise InvalidInput('P205_GOLD_TRACE_REF_DUPLICATE_OR_OUT_OF_RANGE')
            seen.add(idx)
            by_cue[idx].add(gid)
    count={'REVIEWED_ATOM':0,'NO_ATOM':0,'OPEN_UNCERTAIN':0}
    for i,row in enumerate(reviews,1):
        if type(row) is not dict or row.get('cue_index') != i:
            raise InvalidInput('P205_GOLD_TRACE_CUE_INDEX_NOT_CONTIGUOUS')
        if row.get('source_quote_sha256') != sha256(cues[i-1].text.encode('utf8')):
            raise InvalidInput('P205_GOLD_TRACE_CUE_HASH_MISMATCH')
        kind=row.get('status')
        if kind not in count:
            raise InvalidInput('P205_GOLD_TRACE_STATUS_UNKNOWN')
        cited=row.get('gold_atom_ids')
        if (type(cited) is not list or any(type(x) is not str for x in cited)
                or len(cited)!=len(set(cited))):
            raise InvalidInput('P205_GOLD_TRACE_CUE_GOLD_ID_LIST_INVALID')
        if set(cited) != by_cue[i]:
            raise InvalidInput('P205_GOLD_TRACE_CUE_CLAIM_GRAPH_MISMATCH')
        if kind=='REVIEWED_ATOM' and not cited:
            raise InvalidInput('P205_GOLD_TRACE_CLAIMLESS_REVIEWED_CUE')
        if kind=='NO_ATOM' and cited:
            raise InvalidInput('P205_GOLD_TRACE_HIDDEN_CLAIM_IN_NO_ATOM_CUE')
        if kind=='OPEN_UNCERTAIN' and cited:
            # Unresolved source may still have candidate claims; never certify.
            pass
        count[kind]+=1
    return {
      'cue_count':len(cues), 'gold_atom_count':len(ids),
      'source_ref_edges':sum(len(x) for x in by_cue.values()),
      'cue_reviewed_atom':count['REVIEWED_ATOM'],
      'cue_no_atom':count['NO_ATOM'],
      'cue_open_uncertain':count['OPEN_UNCERTAIN'],
      'traceability_valid':True,
      'independent_semantic_truth_certified':False,
    }
