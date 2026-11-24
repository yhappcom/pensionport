"""Verbatim numeric-unit provenance audit for V6 source-ref candidates.

Checks original source token boundaries, not the financial truth of the content.
The numeric scanner intentionally cannot decide ASR errors such as '5차' vs
'오차' or a duplicated '2을'. Those require ChatGPT semantic review.
"""
from __future__ import annotations

from typing import Sequence

from .atomic_exchange import COMPLETE_NUMBER

_NUMERIC_UNIT_STARTS = ("억", "만", "천", "백", "십", "원", "주", "개", "년", "%", "kg", "km", "달러", "엔", "위안", "유로", "좌", "배", "억", "억원")
_PREFIX_CONTINUATION = set("0123456789.,천백십만억")


def audit_numeric_reference_boundaries(cues: Sequence, atoms: Sequence[dict]) -> list[dict]:
    """Flag source tokens split away from their contiguous numeric units.

    `cues` contains objects with `.text`.  Each flag is verifiable purely
    from a locally held original SRT; no external model or API is required.
    Partial units are *structural errors*; knowing which token is ASR debris
    still requires an explicit source-grounded reviewer correction.
    """
    flags=[]
    for atom in atoms:
        cid=atom.get('claim_id')
        refs=atom.get('numeric_references',[])
        if not isinstance(refs,list):
            flags.append({'claim_id':cid,'cue_index':None,'token':None,'reason':'NUMERIC_REFS_NOT_ARRAY'});continue
        for ref in refs:
            if not isinstance(ref,dict) or type(ref.get('cue_index')) is not int or type(ref.get('token')) is not str:
                flags.append({'claim_id':cid,'cue_index':None,'token':None,'reason':'INVALID_NUMERIC_REFERENCE'});continue
            i=ref['cue_index'];token=ref['token']
            if not (1<=i<=len(cues)) or not token:
                flags.append({'claim_id':cid,'cue_index':i,'token':token,'reason':'INVALID_CUE_OR_EMPTY_TOKEN'});continue
            text=cues[i-1].text
            starts=[j for j in range(len(text)) if text.startswith(token,j)]
            if not starts:
                flags.append({'claim_id':cid,'cue_index':i,'token':token,'reason':'NOT_VERBATIM_IN_ORIGINAL'});continue
            # A complete lexer match already includes the unit. A following
            # Korean particle (e.g. only/만) must not be mistaken for a
            # further magnitude. Conversely a partial span inside a complete
            # match is still rejected, including spaced units and decimals.
            spans=[m.span() for m in COMPLETE_NUMBER.finditer(text)]
            reasons=set()
            for j in starts:
                end=j+len(token)
                covering=[(a,b) for a,b in spans if a<=j and end<=b]
                if (j,end) in covering:
                    reasons.clear()
                    break
                if covering:
                    for a,b in covering:
                        if a<j:reasons.add('NUMERIC_TOKEN_MISSING_PREFIX')
                        if end<b:reasons.add('NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
                    continue
                prev=text[j-1] if j else ''
                suffix=text[j+len(token):]
                if prev in _PREFIX_CONTINUATION:
                    reasons.add('NUMERIC_TOKEN_MISSING_PREFIX')
                if any(suffix.startswith(s) for s in _NUMERIC_UNIT_STARTS):
                    reasons.add('NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
                if not prev or prev not in _PREFIX_CONTINUATION:
                    if not any(suffix.startswith(s) for s in _NUMERIC_UNIT_STARTS):
                        reasons.clear()
                        break
            for reason in sorted(reasons):
                flags.append({'claim_id':cid,'cue_index':i,'token':token,'reason':reason})
    return flags
