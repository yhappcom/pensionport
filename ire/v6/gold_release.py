"""P205 production evidence transition: distinct host-attested blind drafts.

The previous gold_eval.py is intentionally diagnostic-only.  This release
checker is a separate positive route, but cannot be used on current ETF250:
no trusted reviewer/host keys or independent review exports are enrolled.
A registry hash must be pinned *in reviewed repository code before review*;
callers cannot self-supply or compute it from their submission.

Source-only reviewer exports, host session receipts, consensus and later
alignment are separately signed.  Signatures prove custody/identity, not the
truth of the reviewers' financial interpretation.  Release is E2 assessment
readiness only; E3/E4/E5 remain separately gated.
"""
from __future__ import annotations
import base64
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from .codec import canonical,json_digest,sha256
from .errors import InvalidInput
from .gold_eval import evaluate_atomic_gold, _original_quote_valid
from .gold_traceability import verify_gold_cue_trace
from .source import parse_srt

# This is deliberately *not* enrolled. A future approved preregistration
# commit may pin the independently verified public-key registry SHA here.
# Never set it from incoming files, caller data, or a CI runtime flag.
PINNED_P205_HOST_REVIEW_REGISTRY_SHA256 = None
ROLES=('reviewer_one','reviewer_two','neutral_host')


def _date(value):
    if type(value) is not str:
        raise ValueError('timestamp not text')
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:
        raise ValueError('timestamp must have offset')
    return d


def _verify(role,body,sig_b64,keys):
    try:
        pub=base64.b64decode(keys[role],validate=True)
        sig=base64.b64decode(sig_b64,validate=True)
        if len(pub)!=32 or len(sig)!=64:
            return False
        Ed25519PublicKey.from_public_bytes(pub).verify(sig,canonical(body))
        return True
    except (ValueError,TypeError,KeyError,InvalidSignature,InvalidInput):
        return False


def _hold(reason,diagnostic=None):
    report={
      'schema':'IRE_P205_PRODUCTION_ATOMIC_GOLD_RELEASE_GATE_V1',
      'status':reason,'production_trust_registry_verified':False,
      'two_blind_reviews_host_attested':False,
      'gold_consensus_locked_before_alignment':False,
      'independent_gold_verified':False,
      'independent_precision':None,'independent_recall':None,
      'independent_high_risk_false_negative_count':None,
      'e2_accuracy_thresholds_met':False,'ready_for_p0_2_06':False,
      'e3_e4_e5_knowledge_approved':False,
      'personalized_advice_authorized':False,
      'synthetic_or_self_signed_input_must_not_certify':True,
    }
    if diagnostic:
        report['diagnostic_gold_claim_count']=diagnostic.get('gold_atom_count')
    return report


def evaluate_production_gold(plan,original_srt:bytes,frozen_native:bytes,
                             *,gold=None,alignment=None,registry=None,
                             reviewer_submissions=None,consensus=None,
                             alignment_receipt=None):
    """Fail closed until a separately pinned host key and two records exist."""
    basic=evaluate_atomic_gold(plan,original_srt,frozen_native,gold=gold,alignment=alignment)
    if gold is None or alignment is None:
        return _hold('HOLD_NO_ATOMIC_GOLD_OR_ALIGNMENT')
    if basic.get('status')=='HOLD_UNRESOLVED_BLIND_GOLD_CUES':
        return _hold('HOLD_OPEN_CUES_CANNOT_PASS',basic)
    if basic.get('tp') is None or basic.get('gold_traceability',{}).get('traceability_valid') is not True:
        return _hold('HOLD_GOLD_TRACEABILITY_NOT_READY',basic)
    pin=PINNED_P205_HOST_REVIEW_REGISTRY_SHA256
    if type(pin) is not str or len(pin)!=64:
        return _hold('HOLD_NO_PRE_REVIEW_PRODUCTION_HOST_REGISTRY_PIN',basic)
    if type(registry) is not dict or json_digest(registry)!=pin:
        return _hold('HOLD_REGISTRY_NOT_IDENTICAL_TO_PREREGISTERED_TRUST_ROOT',basic)
    if set(registry)!={'schema','enrolled_at','plan_sha256','source_srt_sha256',
                       'native_prediction_sha256','source_only_packet_sha256','public_keys'} or \
       registry.get('schema')!='IRE_P205_PINNED_REVIEW_REGISTRY_V1' or \
       registry['plan_sha256']!=json_digest(plan) or \
       registry['source_srt_sha256']!=sha256(original_srt) or \
       registry['native_prediction_sha256']!=sha256(frozen_native):
        return _hold('HOLD_WRONG_PINNED_SOURCE_OR_PREREGISTRATION',basic)
    keys=registry['public_keys']
    if (type(keys) is not dict or set(keys)!=set(ROLES) or
        any(type(v) is not str for v in keys.values()) or
        len(set(keys.values()))!=3):
        return _hold('HOLD_UNTRUSTED_DISTINCT_SIGNER_KEYS',basic)
    try:
        enrolled=_date(registry['enrolled_at'])
    except ValueError:
        return _hold('HOLD_REGISTRY_ENROLLMENT_TIME_INVALID',basic)
    if type(reviewer_submissions) is not list or len(reviewer_submissions)!=2:
        return _hold('HOLD_TWO_INDEPENDENT_SOURCE_ONLY_SUBMISSIONS_ABSENT',basic)
    cues=parse_srt(original_srt)
    reviews_by_role={}
    sessions=set();review_end=[];review_gold_digests=[]
    for review in reviewer_submissions:
        if type(review) is not dict or set(review)!={'body','reviewer_signature','neutral_host_signature'}:
            return _hold('HOLD_REVIEW_SUBMISSION_SIGNED_SCHEMA_INVALID',basic)
        body=review['body']
        if type(body) is not dict or set(body)!={'schema','role','session_id',
            'source_srt_sha256','source_only_packet_sha256','predictions_exposed',
            'began_at','submitted_at','draft_gold'}:
            return _hold('HOLD_REVIEW_BODY_SCHEMA_INVALID',basic)
        role=body['role'];sess=body['session_id']
        if (role not in ROLES[:2] or role in reviews_by_role or
            type(sess) is not str or len(sess)<12 or sess in sessions or
            body['schema']!='IRE_P205_HOST_BLIND_REVIEW_SUBMISSION_V1' or
            body['source_srt_sha256']!=sha256(original_srt) or
            body['source_only_packet_sha256']!=registry['source_only_packet_sha256'] or
            body['predictions_exposed'] is not False):
            return _hold('HOLD_REVIEWER_NOT_SEPARATELY_HOST_ATTESTED_SOURCE_ONLY',basic)
        try:
            start=_date(body['began_at']);finish=_date(body['submitted_at'])
        except ValueError:
            return _hold('HOLD_REVIEW_TIMESTAMPS_INVALID',basic)
        if not (enrolled < start < finish):
            return _hold('HOLD_REVIEWS_NOT_AFTER_TRUST_ROOT_ENROLLMENT',basic)
        draft=body['draft_gold']
        if type(draft) is not dict or draft.get('source_srt_sha256')!=sha256(original_srt):
            return _hold('HOLD_DRAFT_NOT_SOURCE_PINNED',basic)
        try:
            trace=verify_gold_cue_trace(cues,draft)
            if trace['cue_open_uncertain'] or not trace['gold_atom_count']:
                return _hold('HOLD_DRAFT_NOT_FULLY_SOURCE_REVIEWED',basic)
            if any(not _original_quote_valid(cues,ref)
                   for claim in draft['atomic_gold_claims']
                   for ref in claim['source_refs']):
                return _hold('HOLD_DRAFT_NON_SOURCE_ATOMIC_CLAIM',basic)
        except (InvalidInput,KeyError,TypeError):
            return _hold('HOLD_DRAFT_ATOMIC_SOURCE_TRACE_INVALID',basic)
        if not _verify(role,body,review['reviewer_signature'],keys) or \
           not _verify('neutral_host',body,review['neutral_host_signature'],keys):
            return _hold('HOLD_NOT_AUTHENTICATED_REVIEWER_AND_HOST_SESSION',basic)
        sessions.add(sess);reviews_by_role[role]=json_digest(body)
        review_gold_digests.append(json_digest(draft));review_end.append(finish)
    if set(reviews_by_role)!=set(ROLES[:2]):
        return _hold('HOLD_TWO_DISTINCT_REVIEWERS_REQUIRED',basic)
    # The host must attest genuine isolation; differing file hashes alone are
    # not proof of independence, and identical drafts do not prove collusion.
    if type(consensus) is not dict or set(consensus)!={'body','signatures'}:
        return _hold('HOLD_CONSENSUS_NOT_SIGNED',basic)
    body=consensus['body'];signatures=consensus['signatures']
    if type(body) is not dict or set(body)!={'schema','reviewer_submission_sha256',
                  'gold_sha256','disagreements_count','resolved_disagreements_count',
                  'gold_frozen_at'} or \
       body.get('schema')!='IRE_P205_TWO_REVIEWER_ATOMIC_CONSENSUS_V1' or \
       body.get('reviewer_submission_sha256')!=reviews_by_role or \
       body.get('gold_sha256')!=json_digest(gold) or \
       type(body.get('disagreements_count')) is not int or \
       type(body.get('resolved_disagreements_count')) is not int or \
       body['disagreements_count']<0 or \
       body['resolved_disagreements_count']!=body['disagreements_count'] or \
       type(signatures) is not dict or set(signatures)!=set(ROLES) or \
       any(not _verify(role,body,signatures[role],keys) for role in ROLES):
        return _hold('HOLD_DISAGREEMENTS_OR_CONSENSUS_SIGNING_NOT_COMPLETE',basic)
    if len(set(review_gold_digests))>1 and body['disagreements_count']==0:
        return _hold('HOLD_DIVERGENT_DRAFTS_WITH_ZERO_RECONCILIATION',basic)
    try:
        freeze=_date(body['gold_frozen_at'])
    except ValueError:
        return _hold('HOLD_GOLD_LOCK_TIMESTAMP_INVALID',basic)
    if not max(review_end) < freeze:
        return _hold('HOLD_GOLD_FROZEN_BEFORE_REVIEW_ENDED',basic)
    if type(alignment_receipt) is not dict or set(alignment_receipt)!={'body','host_signature'}:
        return _hold('HOLD_ALIGNMENT_EVIDENCE_NOT_SIGNED',basic)
    body=alignment_receipt['body']
    if type(body) is not dict or set(body)!={'schema','gold_sha256','alignment_sha256','aligned_at'} or \
       body.get('schema')!='IRE_P205_POST_GOLD_ALIGNMENT_LOCK_V1' or \
       body.get('gold_sha256')!=json_digest(gold) or \
       body.get('alignment_sha256')!=json_digest(alignment) or \
       not _verify('neutral_host',body,alignment_receipt['host_signature'],keys):
        return _hold('HOLD_GOLD_TO_PREDICTION_ALIGNMENT_NOT_HOST_SIGNED',basic)
    try:
        aligned=_date(body['aligned_at'])
    except ValueError:
        return _hold('HOLD_ALIGNMENT_TIMESTAMP_INVALID',basic)
    if not freeze < aligned:
        return _hold('HOLD_ALIGNMENT_PERFORMED_BEFORE_GOLD_FROZEN',basic)
    precision=basic['diagnostic_precision'];recall=basic['diagnostic_recall']
    fn=basic['diagnostic_high_risk_fn'];tp=basic['tp']
    pred=basic['frozen_prediction_atom_count'];gcount=basic['gold_atom_count']
    thresholds=plan['assessment']['thresholds']
    if not all(type(thresholds.get(k)) is int for k in (
           'atomic_precision_min_bp','atomic_recall_min_bp',
           'high_risk_false_negative_max')):
        return _hold('HOLD_NOT_AN_INTEGER_PREREGISTERED_THRESHOLD',basic)
    meets=(tp*10000>=pred*thresholds['atomic_precision_min_bp'] and
           tp*10000>=gcount*thresholds['atomic_recall_min_bp'] and
           fn<=thresholds['high_risk_false_negative_max'])
    out=_hold('VERIFIED_SOURCE_FIRST_INDEPENDENT_GOLD_THRESHOLDS_PASS' if meets
              else 'HOLD_MEASURED_INDEPENDENT_GOLD_BELOW_THRESHOLDS',basic)
    out.update({
     'production_trust_registry_verified':True,
     'two_blind_reviews_host_attested':True,
     'gold_consensus_locked_before_alignment':True,
     'independent_gold_verified':True,
     'independent_precision':precision,
     'independent_recall':recall,
     'independent_high_risk_false_negative_count':fn,
     'e2_accuracy_thresholds_met':bool(meets),
     'ready_for_p0_2_06':bool(meets),
     'synthetic_or_self_signed_input_must_not_certify':False,
    })
    return out
