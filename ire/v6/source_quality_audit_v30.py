"""V30 optional, original-source-bound financial candidate repair and numeric coverage.

This verifies *source/cue/token accounting* and explicitly recorded same-chat
semantic alert remodelling. It does not self-certify recall, legal correctness
or independent blinded precision/recall. No original transcript in receipts.
"""
from __future__ import annotations

from .atomic_exchange import NUMBER, audit_host_atomic_exchange
from .codec import canonical, json_digest, sha256
from .errors import InvalidInput
from .semantic_risk import audit_semantic_risks
from .stage_repair import review_chat_risk_cases


def _all_numeric_occurrences(source, exchange):
    """Every *occurrence* in source, including repeat tokens, is accounted for."""
    atoms=exchange['atoms']
    result=[]
    for idx in range(source.scope_first_cue,source.scope_last_cue+1):
        cue=source.cues[idx-1]
        for ordinal,token in enumerate(NUMBER.findall(cue.text)):
            owners=sorted(a['claim_id'] for a in atoms if any(
                r['cue_index']==idx and r['token']==token
                for r in a['numeric_references']))
            result.append({'cue_index':idx,'token_ordinal':ordinal,
                           'token_sha256':sha256(token.encode('utf-8')),
                           'linked_claim_ids':owners,
                           'source_cue_sha256':sha256(cue.text.encode('utf-8'))})
    return result


def audit_private_source_repairs_v30(source, before, after, decisions,
                                     *, reviewed_changed_claim_ids,
                                     approved_new_claim_ids, approved_revised_atom_sha256):
    """Require verified cue closure, exact risk docket, and number grounding.

    The 'reviewed' fields are same-chat assertions only. If source cues repeat
    a numeric token, occurrence accounting is conserved; claim attribution to
    multiple overlapping frames is allowed when grounded in cited context.
    """
    orig=audit_host_atomic_exchange(source,before)
    post=audit_host_atomic_exchange(source,after)
    if (type(approved_revised_atom_sha256) is not dict or
        not approved_revised_atom_sha256):
        raise InvalidInput('V30_REPAIR_CLAIM_SHA_PINS_REQUIRED')
    if (type(reviewed_changed_claim_ids) is not list or
        reviewed_changed_claim_ids != sorted(set(reviewed_changed_claim_ids)) or
        type(approved_new_claim_ids) is not list or
        approved_new_claim_ids != sorted(set(approved_new_claim_ids))):
        raise InvalidInput('V30_REPAIR_REVIEW_LIST_INVALID')
    old={a['claim_id']:a for a in before['atoms']}
    new={a['claim_id']:a for a in after['atoms']}
    if not set(old).issubset(new):
        raise InvalidInput('V30_SILENT_DELETED_ATOM')
    added=sorted(set(new)-set(old))
    changed=sorted(cid for cid in old if canonical(old[cid])!=canonical(new[cid]))
    if (added!=approved_new_claim_ids or changed!=reviewed_changed_claim_ids or
        not set(added).isdisjoint(old) or
        set(approved_revised_atom_sha256)!=set(changed+added) or
        any(approved_revised_atom_sha256.get(cid)!=json_digest(new[cid])
            for cid in changed+added)):
        raise InvalidInput('V30_UNREVIEWED_CANDIDATE_CHANGE')
    if (post['unresolved_cues'] or post['suspicious_no_atom_cues'] or
        post['original_scoped_cues_enumerated'] !=
            source.scope_last_cue-source.scope_first_cue+1):
        raise InvalidInput('V30_SOURCE_CUE_COVERAGE_UNRESOLVED')
    if any(d['disposition']!='CANDIDATES' for d in after['cue_dispositions']):
        # This V30 quality level demands a meaning frame for every original cue.
        # A future source with nonfinancial noise needs an explicit carveout
        # receipt rather than pretending all original claims were extracted.
        raise InvalidInput('V30_UNANCHORED_CUE_NOT_QUALITY_CERTIFIED')
    prior=audit_semantic_risks(source,before)
    revised=audit_semantic_risks(source,after)
    adjudicated=review_chat_risk_cases(source,before,after,decisions)
    if (len(decisions)!=prior['review_case_count'] or
        prior['review_case_count']<1 or
        adjudicated['outstanding_chat_triage_count'] or
        adjudicated['directly_remodeled_alerts']!=len(decisions) or
        revised['review_case_count']):
        raise InvalidInput('V30_UNRESOLVED_OR_UNSUPPORTED_SEMANTIC_ALERT')
    # Preserve provenance: reviewed cases must be source-cue bound and
    # labelled as genuine contextual remodelling, never silently removed.
    if any(d['decision'] not in ('REMODELED_CONDITION','REMODELED_EXCEPTION')
           for d in decisions):
        raise InvalidInput('V30_UNSUPPORTED_RISK_DISPOSITION')
    numeric=_all_numeric_occurrences(source,after)
    misses=[(r['cue_index'],r['token_ordinal']) for r in numeric
            if not r['linked_claim_ids']]
    if not numeric or misses:
        raise InvalidInput('V30_ORIGINAL_NUMERIC_TOKEN_RECALL_GAP')
    return {
        'schema':'IRE_V6_V30_PRIVATE_SOURCE_QUALITY_CHAT_REVIEW_RECEIPT',
        'source_sha256':source.source_sha256,
        'manifest_sha256':source.manifest_sha256,
        'before_exchange_sha256':json_digest(before),
        'after_exchange_sha256':json_digest(after),
        'original_claim_count':orig['proposed_atomic_claims'],
        'revised_candidate_claim_count':post['proposed_atomic_claims'],
        'reviewed_changed_claim_ids':changed,
        'newly_added_claim_ids':added,
        'reviewed_atom_sha256_commitment':json_digest(approved_revised_atom_sha256),
        'scoped_source_cue_count':post['original_scoped_cues_enumerated'],
        'source_cues_linked_to_candidate':post['cues_with_candidates'],
        'source_numeric_token_count':len(numeric),
        'source_numeric_tokens_with_atom_anchor':len(numeric)-len(misses),
        'source_numeric_token_census_sha256':json_digest(numeric),
        'original_semantic_risk_count':prior['review_case_count'],
        'revised_semantic_risk_count':revised['review_case_count'],
        'source_cue_review_decisions_sha256':json_digest(decisions),
        'context_adjudication_receipt_sha256':adjudicated['decision_digest'],
        'unreviewed_semantic_cases':adjudicated['outstanding_chat_triage_count'],
        'all_source_numeric_occurrences_structurally_accounted':True,
        'independently_correct_numeric_units_or_scope':False,
        'independent_human_gold_provided':False,
        'blind_semantic_precision_recall_measured':False,
        'full_atomic_claim_recall_certified':False,
        'approved_knowledge_ingestion':False,
        'personal_tax_or_trade_approved':False,
        'p0_go':False,
        'status':'V30_SOURCE_FRAME_AND_NUMERIC_CENSUS_CHAT_REVIEW_NOT_GOLD',
    }


def evaluate_private_original_v30(root, question, *, zip_path, member_name,
                                  expected_zip_sha256,expected_srt_sha256,
                                  expected_video_id,expected_cue_count,
                                  source_manifest,expected_manifest_sha256,
                                  before_exchange,exchange,source_review_decisions,
                                  reviewed_changed_claim_ids,approved_new_claim_ids,
                                  approved_revised_atom_sha256,
                                  expected_git_blobs,current_as_of,primary_evidence,
                                  chat_decisions,selected_claim_ids,
                                  relevance_decisions,candidate_dispositions,
                                  scenario=None,isa_law_review=None):
    """Opt-in real E2E, fail closed if repaired original source is not audited.

    `exchange` is the revised, source-bound set; the pre-repair exchange and
    each original semantic alert must be supplied and explicitly reviewed.
    Source input/answer text are never included in the hash-only receipt.
    """
    from pathlib import Path
    import zipfile
    from .private_original_pin_v28 import verify_private_original_archive
    from .source import verify_source
    from .private_replay_receipt_v29 import evaluate_private_original_v29
    if 'ire/v6/source_quality_audit_v30.py' not in expected_git_blobs:
        raise InvalidInput('V30_OWN_CODE_PIN_REQUIRED')
    orig=verify_private_original_archive(
        zip_path,member_name=member_name,
        expected_zip_sha256=expected_zip_sha256,
        expected_srt_sha256=expected_srt_sha256,
        expected_video_id=expected_video_id,
        expected_cue_count=expected_cue_count,
        source_manifest=source_manifest,
        expected_manifest_sha256=expected_manifest_sha256,
        exchange=exchange)
    with zipfile.ZipFile(Path(zip_path)) as archive:
        raw=archive.read(member_name)
    source=verify_source(raw,source_manifest,
        expected_source_sha256=expected_srt_sha256,
        expected_manifest_sha256=expected_manifest_sha256)
    reviewed=audit_private_source_repairs_v30(
        source,before_exchange,exchange,source_review_decisions,
        reviewed_changed_claim_ids=reviewed_changed_claim_ids,
        approved_new_claim_ids=approved_new_claim_ids,
        approved_revised_atom_sha256=approved_revised_atom_sha256)
    base=evaluate_private_original_v29(
        root,question,zip_path=zip_path,member_name=member_name,
        expected_zip_sha256=expected_zip_sha256,
        expected_srt_sha256=expected_srt_sha256,
        expected_video_id=expected_video_id,
        expected_cue_count=expected_cue_count,
        source_manifest=source_manifest,
        expected_manifest_sha256=expected_manifest_sha256,
        exchange=exchange,current_as_of=current_as_of,
        primary_evidence=primary_evidence,
        chat_decisions=chat_decisions,selected_claim_ids=selected_claim_ids,
        relevance_decisions=relevance_decisions,
        candidate_dispositions=candidate_dispositions,
        expected_git_blobs=expected_git_blobs,
        scenario=scenario,isa_law_review=isa_law_review)
    if (orig['atomic_candidate_count']!=reviewed['revised_candidate_claim_count'] or
        base['hash_only_public_receipt']['source_candidate_digest']!=
            orig['atomic_candidate_digest']):
        raise InvalidInput('V30_PRIVATE_SOURCE_RECEIPT_DRIFT')
    record={**base['hash_only_public_receipt']}
    record.pop('receipt_sha256',None)
    record['schema']='IRE_V6_V30_REPAIRED_SOURCE_PRIVATE_E2E_HASH_RECEIPT'
    record['v30_source_quality_review_sha256']=json_digest(reviewed)
    record['v30_before_exchange_sha256']=reviewed['before_exchange_sha256']
    record['v30_after_exchange_sha256']=reviewed['after_exchange_sha256']
    record['v30_structural_numeric_token_count']=reviewed['source_numeric_token_count']
    record['v30_revised_semantic_alerts']=reviewed['revised_semantic_risk_count']
    record['v30_independent_semantic_gold_verified']=False
    record['p0_go']=False
    return {**base,
            'schema':'IRE_V6_V30_REPAIRED_PRIVATE_ORIGINAL_ANSWER',
            'v30_source_quality_audit':reviewed,
            'hash_only_public_receipt':{**record,
                'receipt_sha256':json_digest(record)},
            'p0_go':False,
            'status':'V30_SOURCE_STRUCTURAL_QUALITY_REPAIRED_INDEPENDENT_GOLD_OPEN'}
