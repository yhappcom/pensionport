"""V173: final E4 verification as an independent, NON-PUBLISHING operation.

Does not call V126/V128 knowledge publication, create a knowledge store, or
turn OPEN into PASS. Replays every child through the frozen V123/E4 gate,
then checks the native V127 parent/seams and explicit ChatGPT parent semantic
review before optionally producing an externally signed E4-only certificate.
The *current chat host* must supply the real source, original official bytes
and actual signed/reviewed data. Synthetic fixtures do not prove real E4.
"""
from __future__ import annotations

from datetime import date
import hashlib
import hmac

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from v166_e4_primary_approval_gate import assess_e4_primary_authority_gate
from v128_atomic_parent_knowledge import _validate_release

SCHEMA = 'IRE_V173_SOURCE_BOUND_STANDALONE_E4_VIDEO_REVIEW_V1'
SEAL_SCHEMA = 'IRE_V173_E4_ONLY_EXTERNALLY_SIGNED_CERTIFICATE_V1'


def _need(cond, code):
    if not cond:
        raise InvalidInput('V173_E4_ONLY_'+code)


def run_e4_only_parent(checkpoint, *, review_or_load_child,
                       primary_manifest_for_child, typed_inventory_for_child,
                       typed_manifest_for_child, review_seams, review_parent,
                       now_as_of, expected_scope_count=13,
                       expected_owner_source_sha256=None):
    """Verify all original children even after a HOLD; never publish knowledge.

    This performs a read-only all-scope E4 preflight, then (only if every child
    E4 PASS) creates/replays V127.1 review checkpoint events, checks the full
    V127 parent assembly/seams, and verifies an explicit host-authored V128
    parent review using its *validation* function, not its publication path.

    An affirmative result is E4-verifiable evidence awaiting external owner
    signing; it is NEVER authorization to run E5 in this function.
    """
    _need(type(expected_scope_count) is int and 1 <= expected_scope_count <= 10000,
          'EXPECTED_SCOPE_COUNT')
    ids = getattr(checkpoint, 'child_ids', None)
    manifests = getattr(checkpoint, 'child_manifests', None)
    _need(type(ids) in (tuple,list) and type(manifests) in (tuple,list) and
          len(ids)==len(manifests)==expected_scope_count and
          len(set(ids)) == len(ids), 'COMPLETE_CHILD_SCOPE_CENSUS')
    _need(all(callable(c) for c in (
        review_or_load_child, primary_manifest_for_child,
        typed_inventory_for_child, typed_manifest_for_child,
        review_seams, review_parent)), 'CHAT_AND_AUTHORITY_HOST_REQUIRED')
    _need(type(now_as_of) is str and
          date.fromisoformat(now_as_of).isoformat()==now_as_of,
          'REVIEW_DATE')
    original_raw=checkpoint.raw
    owner_sha=sha256(original_raw)
    _need(getattr(checkpoint.parent, 'source_sha256', None)==owner_sha,
          'OWNER_SOURCE_CHANGED')
    _need(type(expected_owner_source_sha256) is str and
          expected_owner_source_sha256==owner_sha,
          'EXTERNALLY_PINNED_OWNER_SOURCE_REQUIRED')
    checkpoint.progress()  # Ensure original checkpoints are internally valid.
    before_head=checkpoint.progress()['checkpoint_head_sha256']
    scoped=[]; supplied={}; e4_digests=[]; child_input_pins={}
    for sid, manifest in zip(ids,manifests):
        status='E4_CHILD_VERIFIER_ERROR'; reason='UNKNOWN'; native=None
        digest=None
        try:
            packet=review_or_load_child(sid,manifest,'E4_VERIFY_ONLY',original_raw)
            _need(type(packet) is dict and set(packet)=={
                'case','relation_decisions','original_host_batch_replay_args',
                'explicit_hold_revision'}, 'CHILD_PACKET_SCHEMA')
            case=packet['case']
            _need(type(case) is dict and case.get('manifest')==manifest and
                  case['source'].source_sha256==owner_sha,
                  'CHILD_FROZEN_SOURCE_OR_PLAN')
            assessment=assess_e4_primary_authority_gate(
                case,primary_manifest_for_child(sid,case),now_as_of=now_as_of,
                typed_inventory=typed_inventory_for_child(sid,case),
                typed_manifest=typed_manifest_for_child(sid,case))
            status=assessment['status']
            _need(status in {'E4_PASS_RESEARCH_CANDIDATES_ONLY',
                             'E4_HOLD_INELIGIBLE_APPROVAL'},
                  'UNKNOWN_E4_GATE_STATUS')
            reason=assessment.get('reason_code')
            native=assessment.get('native_chat_decision')
            if status=='E4_PASS_RESEARCH_CANDIDATES_ONLY':
                digest=json_digest(assessment)
                child_input_pins[sid]={
                    'exchange_sha':json_digest(case['exchange']),
                    'review_sha':json_digest(case['chat_review']),
                    'host_event_sha':case['host_receipt']['event_sha256'],
                    'official_bytes_sha':{k:sha256(v) for k,v in
                        case['official_evidence_bodies'].items()},
                }
                supplied[sid]=packet
        except Exception as exc:
            # The only recorded exception datum is its type, never private
            # source/issuer text or model notes. Continue inspecting all scopes.
            status='E4_CHILD_VERIFIER_ERROR'
            reason=type(exc).__name__
        e4_digests.append(digest)
        scoped.append({'segment_id':sid,'e4_status':status,
                       'reason_code':reason,'native_chat_decision':native,
                       'e4_approval_receipt_sha256':digest})
    blocked=[r['segment_id'] for r in scoped
             if r['e4_status']!='E4_PASS_RESEARCH_CANDIDATES_ONLY']
    root={
        'schema':SCHEMA,
        'owner_source_sha256':owner_sha,
        'original_source_cue_count':len(checkpoint.parent.cues),
        'owner_manifest_sha256':checkpoint.parent.manifest_sha256,
        'child_count':len(ids),
        'children_examined':len(scoped),
        'child_reviews':scoped,
        'blocked_segment_ids':blocked,
        'as_of':now_as_of,
        'e4_origin_and_scope_tested_using_frozen_gate':True,
        'e5_publication_called':False,
        'e5_authorized':False,
        'knowledge_published':False,
        'personal_advice_approved':False,
        'actual_chat_identity_cryptographically_attested':False,
        'independent_semantic_recall_certified':False,
    }
    if blocked:
        return {**root,'status':'E4_HOLD_ALL_SEGMENTS_EXAMINED',
                'parent_source_semantic_review_verified':False,
                'e4_externally_certified':False,
                'e4_ready_to_seal':False}
    # Do not continue if another process advanced the checkpoint during
    # preflight; such a revision requires fresh whole-video E4 verification.
    _need(checkpoint.progress()['checkpoint_head_sha256']==before_head,
          'CHECKPOINT_CHANGED_DURING_E4_PREFLIGHT')
    packets=[]
    try:
        for sid in ids:
            packet=supplied[sid]
            case=packet['case']
            original=child_input_pins[sid]
            _need(original=={
                'exchange_sha':json_digest(case['exchange']),
                'review_sha':json_digest(case['chat_review']),
                'host_event_sha':case['host_receipt']['event_sha256'],
                'official_bytes_sha':{k:sha256(v) for k,v in
                    case['official_evidence_bodies'].items()},
            }, 'CHILD_INPUT_CHANGED_AFTER_PRIMARY_E4_PASS')
            cp=checkpoint.progress()
            checkpoint.record(sid,packet['case'],
                expected_checkpoint_head=cp['checkpoint_head_sha256'],
                allow_hold_revision=packet['explicit_hold_revision'])
            packets.append({k:packet[k] for k in (
                'case','relation_decisions','original_host_batch_replay_args')})
        cases=[p['case'] for p in packets]
        seams=review_seams(checkpoint,cases)
        _need(type(seams) is list,'CHAT_SEAM_LIST_REQUIRED')
        head=checkpoint.progress()['checkpoint_head_sha256']
        assembly=checkpoint.assemble(cases,seams,expected_checkpoint_head=head)
        parent_review=review_parent(checkpoint,assembly,seams,packets)
        parent_review_sha=_validate_release(
            parent_review,assembly,head,seams,packets)
    except (InvalidInput,QualityNotProven,ValueError,TypeError,KeyError,
            AttributeError) as exc:
        return {**root,'status':'E4_PARENT_SEMANTIC_HOLD_NO_PUBLICATION',
                'parent_error_type':type(exc).__name__,
                'parent_source_semantic_review_verified':False,
                'e4_externally_certified':False,
                'e4_ready_to_seal':False}
    # These are digest-only data: no owner text, model notes, issuer bodies,
    # DB writes, or key material. A separate external owner key must seal it.
    result={**root,
        'status':'E4_ALL_CHILDREN_AND_PARENT_VERIFIED_AWAIT_OWNER_SEAL',
        'blocked_segment_ids':[],
        'parent_source_semantic_review_verified':True,
        'checkpoint_head_sha256':head,
        'parent_replay_sha256':assembly['parent_replay_sha256'],
        'seams_digest_sha256':json_digest(seams),
        'chat_parent_review_sha256':parent_review_sha,
        'e4_externally_certified':False,
        'e4_ready_to_seal':True,
    }
    return {**result,'e4_result_sha256':json_digest(result)}


def seal_e4_only(e4_result, *, owner_signing_key, independent_owner_source_sha256,
                 independently_pinned_child_count, independent_parent_manifest_sha256):
    """Explicit stand-alone owner authorization; never opens a V126 store.

    Keep the HMAC signing key OUTSIDE the source bundle, Git repo and SQLite.
    This returns a deterministic certificate and an externally pin-able digest
    without storing either. The owner must retain the digest separately.
    """
    _need(type(e4_result) is dict and
          e4_result.get('schema')==SCHEMA and
          e4_result.get('status')==
             'E4_ALL_CHILDREN_AND_PARENT_VERIFIED_AWAIT_OWNER_SEAL' and
          e4_result.get('e4_ready_to_seal') is True and
          e4_result.get('parent_source_semantic_review_verified') is True and
          e4_result.get('e4_result_sha256')==json_digest({
              k:v for k,v in e4_result.items() if k!='e4_result_sha256'}),
          'ONLY_UNALTERED_PARENT_APPROVED_E4_ELIGIBLE')
    _need(not e4_result['blocked_segment_ids'] and
          e4_result['children_examined']==e4_result['child_count'] and
          e4_result['e5_publication_called'] is False and
          e4_result['knowledge_published'] is False,
          'E4_RESULT_HAS_HOLD_OR_KNOWLEDGE_WRITE')
    _need(type(owner_signing_key) is bytes and len(owner_signing_key)>=32,
          'EXTERNAL_OWNER_SIGNING_KEY_REQUIRED')
    _need(type(independent_owner_source_sha256) is str and
          independent_owner_source_sha256 == e4_result['owner_source_sha256'],
          'EXTERNAL_SOURCE_PIN_MISMATCH')
    _need(type(independently_pinned_child_count) is int and
          independently_pinned_child_count == e4_result['child_count'],
          'INDEPENDENT_FULL_VIDEO_SCOPE_COUNT_MISMATCH')
    _need(type(independent_parent_manifest_sha256) is str and
          independent_parent_manifest_sha256 == e4_result['owner_manifest_sha256'],
          'INDEPENDENT_PARENT_MANIFEST_MISMATCH')
    data={'schema':SEAL_SCHEMA,'e4_result_sha256':e4_result['e4_result_sha256'],
          'owner_source_sha256':independent_owner_source_sha256,
          'child_count':independently_pinned_child_count,
          'parent_manifest_sha256':independent_parent_manifest_sha256,
          'all_children_and_parent_verified':True,
          'e5_authorized':False,'knowledge_published':False,
          'personal_advice_approved':False}
    doc={'payload':data,'signature':hmac.new(owner_signing_key,
         canonical(data),hashlib.sha256).hexdigest()}
    return {'certificate':doc,'external_owner_pin_sha256':sha256(canonical(doc)),
            'e4_standalone_certificate_generated':True,
            'e5_publication_called':False,'e5_authorized':False}


def verify_e4_only_seal(certified, *, owner_signing_key, externally_pinned_certificate_sha256,
                        independently_pinned_child_count, independent_parent_manifest_sha256):
    _need(type(certified) is dict and set(certified)=={'payload','signature'}
          and type(certified['payload']) is dict and
          certified['payload'].get('schema')==SEAL_SCHEMA and
          certified['payload'].get('e5_authorized') is False,
          'CERTIFICATE_SCHEMA')
    _need(type(owner_signing_key) is bytes and len(owner_signing_key)>=32,
          'EXTERNAL_OWNER_SIGNING_KEY_REQUIRED')
    _need(sha256(canonical(certified))==externally_pinned_certificate_sha256,
          'EXTERNAL_OWNER_PIN_MISMATCH')
    _need(type(independently_pinned_child_count) is int and
          certified['payload'].get('child_count')==independently_pinned_child_count,
          'EXTERNAL_WHOLE_VIDEO_CHILD_COUNT_MISMATCH')
    _need(type(independent_parent_manifest_sha256) is str and
          certified['payload'].get('parent_manifest_sha256')==independent_parent_manifest_sha256,
          'EXTERNAL_PARENT_MANIFEST_MISMATCH')
    mac=hmac.new(owner_signing_key,canonical(certified['payload']),hashlib.sha256).hexdigest()
    _need(hmac.compare_digest(mac,certified['signature']),
          'EXTERNAL_OWNER_MAC_INVALID')
    return {'status':'E4_CERTIFIED_ONLY_NO_E5',
            'owner_source_sha256':certified['payload']['owner_source_sha256'],
            'e4_result_sha256':certified['payload']['e4_result_sha256'],
            'knowledge_published':False,'e5_authorized':False}