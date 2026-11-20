"""V192: preregister a private SOURCE-ONLY reference before running a candidate.

A SHA-pinned reference written by ChatGPT is NOT independent/external gold.
No approval can be inferred from a seal, and metrics are intentionally absent
until separate source-bound candidate predictions and adjudication are supplied.
"""
from __future__ import annotations
import os,json,stat
from pathlib import Path
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256
from v176_chat_engine_loop import _canon,_digest,make_original_plan

SCHEMA='IRE_V192_E3_PRIVATE_INTERNAL_REFERENCE_V1'
CATEGORIES={'FACT','OPINION','RECOMMENDATION','HYPOTHETICAL','QUESTION'}


def _need(ok,why):
    if not ok:raise InvalidInput('V192_REFERENCE_'+why)


def _quotes(source_cues,idx,quote):
    return type(idx) is int and 1<=idx<=len(source_cues) and type(quote) is str and len(quote.strip())>=2 and ' '.join(quote.split()) in ' '.join(source_cues[idx-1].text.split())


def prepare_reference(*,source_bytes,source_cues,video_id,entries,
                      evaluation_scope,reviewer='CHATGPT_IN_CHAT'):
    """Strictly source-only annotation. No tested engine outputs accepted."""
    _need(type(source_bytes) is bytes and len(source_cues)>=2 and isinstance(video_id,str) and len(video_id)>5
          and type(entries) is list and 1<=len(entries)<=100
          and type(evaluation_scope) is dict and set(evaluation_scope)=={'start_cue','end_cue'}
          and reviewer=='CHATGPT_IN_CHAT','SCOPE_OR_EXECUTOR')
    # A caller must not provide an unrelated array of 'cue texts' under an
    # authentic SRT byte SHA. Reparse the original bytes and compare every cue.
    reconstructed,_=make_original_plan(source_bytes,video_id,
        expected_source_sha256=sha256(source_bytes),window_size=60)
    _need(len(reconstructed.cues)==len(source_cues)
          and all(a.text==b.text for a,b in zip(reconstructed.cues,source_cues)),
          'ORIGINAL_SRT_CUE_MISMATCH')
    lo,hi=evaluation_scope['start_cue'],evaluation_scope['end_cue']
    _need(type(lo) is int and type(hi) is int and 1<=lo<=hi<=len(source_cues),'CUE_RANGE')
    seen=set();clean=[]
    for idx,c in enumerate(entries,1):
        _need(type(c) is dict and set(c)=={'claim_id','kind','proposition','quote_cue',
                 'quote','evidence_cues','source_spoken_conditions','source_spoken_exceptions',
                 'independent_truth_confirmed','high_risk','requires_external_evidence'}
              and c['claim_id']==f'REF{idx:03d}'
              and c['kind'] in CATEGORIES
              and type(c['proposition']) is str and len(c['proposition'].strip())>=15
              and type(c['evidence_cues']) is list and c['evidence_cues']==sorted(set(c['evidence_cues']))
              and all(type(i) is int and lo<=i<=hi for i in c['evidence_cues'])
              and c['quote_cue'] in c['evidence_cues']
              and _quotes(source_cues,c['quote_cue'],c['quote'])
              and type(c['high_risk']) is bool and type(c['requires_external_evidence']) is bool
              and c['independent_truth_confirmed'] is False,
              'CLAIM_REF_OR_SOURCE_CUE_INVALID')
        for group in ('source_spoken_conditions','source_spoken_exceptions'):
            _need(type(c[group]) is list,'QUALIFIER_SCHEMA')
            for x in c[group]:
                _need(type(x) is dict and set(x)=={'cue_index','quote'}
                      and x['cue_index'] in c['evidence_cues']
                      and _quotes(source_cues,x['cue_index'],x['quote']),
                      'SPOKEN_QUALIFIER_UNGROUNDED')
        _need(c['claim_id'] not in seen,'DUPLICATE_CLAIM')
        seen.add(c['claim_id']);clean.append(c)
    r={'schema':SCHEMA,'video_id':video_id,'source_sha256':sha256(source_bytes),
       'source_cue_count':len(source_cues),'scope':evaluation_scope,
       'reference_claims':clean,'reviewer':reviewer,
       'reference_created_before_candidate_for_this_benchmark':True,
       'no_engine_predictions_used_as_reference_input':True,
       'external_reviewer_independence_verified':False,
       'independent_gold_certified':False,'quality_metrics_certified':False,
       'e3_certified':False,'v123_approved':False,
       'e4_approved':False,'e5_published':False}
    return r


def seal_reference(path,reference):
    _need(type(reference) is dict and reference.get('schema')==SCHEMA
          and all(reference.get(x) is False for x in
             ('external_reviewer_independence_verified','independent_gold_certified',
              'quality_metrics_certified','e3_certified','v123_approved',
              'e4_approved','e5_published')),
          'MUST_BE_UNAPPROVED_SOURCE_REFERENCE')
    path=Path(path)
    _need(not path.exists() and not path.is_symlink(),'NO_OVERWRITE_OR_RESET')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'wb') as out:
            out.write(_canon(reference));out.flush();os.fsync(out.fileno())
    except BaseException:
        try: path.unlink()
        except OSError: pass
        raise
    return {'source_sha256':reference['source_sha256'],
            'reference_sha256':sha256(_canon(reference)),
            'reference_count':len(reference['reference_claims']),
            'external_independence_certified':False,
            'precision':None,'recall':None,'e3_certified':False,
            'v123_approved':False,'e4_approved':False,'e5_published':False}


def verify_reference(path,*,expected_reference_sha256,expected_source_sha256):
    p=Path(path)
    _need(p.is_file() and not p.is_symlink() and not (stat.S_IMODE(p.stat().st_mode)&0o077),
          'PRIVATE_REFERENCE_PERMISSION')
    raw=p.read_bytes()
    _need(sha256(raw)==expected_reference_sha256,'REFERENCE_DIGEST_CHANGED')
    document=json.loads(raw)
    _need(_canon(document)==raw and document.get('schema')==SCHEMA
          and document.get('source_sha256')==expected_source_sha256
          and document.get('external_reviewer_independence_verified') is False
          and document.get('quality_metrics_certified') is False
          and document.get('e3_certified') is False
          and document.get('e4_approved') is False
          and document.get('e5_published') is False,
          'REFERENCE_DATA_OR_AUTHORITY_CHANGED')
    return document


def score_without_gold(reference,predictions=None):
    """A sealed ChatGPT reference may aid diagnostics, never certify E3 quality."""
    _need(reference.get('schema')==SCHEMA and reference.get('independent_gold_certified') is False,
          'NO_INDEPENDENT_GOLD')
    _need(predictions is None,'UNADJUDICATED_PREDICTIONS_CANNOT_BE_SCORED_AS_GOLD')
    return {'schema':'IRE_V192_INTERNAL_REFERENCE_NOT_GOLD_HOLD_V1',
            'reference_claims':len(reference['reference_claims']),
            'actual_predictions_submitted':0,
            'internal_precision':None,'internal_recall':None,
            'certified_precision':None,'certified_recall':None,
            'certified_high_risk_misses':None,
            'independent_gold_certified':False,'e3_certified':False,
            'v123_approved':False,'e4_approved':False,'e5_published':False,
            'decision':'E3_HOLD_PREREGISTERED_INTERNAL_REFERENCE_IS_NOT_GOLD'}