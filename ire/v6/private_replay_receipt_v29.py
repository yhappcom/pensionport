"""V29: source-ellipsis guard and hash-only receipt for real private V28->V5 replay.

Additive: historical V5, V22..V28 source files remain unchanged.  This is a
current-ChatGPT source interpretation, NOT human-independent semantic gold.
No raw SRT, original excerpts, user question, or answer body in the receipt.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest, sha256
from .errors import InvalidInput
from .private_original_pin_v28 import (verify_private_original_archive,
                                      evaluate_private_original_v27)
from .semantic_finance_decision_v25 import _facet
from .source import verify_source

_VALID_BLOB = re.compile(r'[0-9a-f]{40}\Z')


def audit_elided_pension_basis_v29(source, exchange, question, selected_claim_ids):
    """Detect one high-risk Korean ASR account-elision omission.

    A financial account name can be split across two subtitle cues, then
    omitted in a follow-on claim about excluded-basis withdrawals. V27 only
    checks literal facets on the proposition, which can miss that claim.
    Only block suspicious omissions: no automatic proposition rewrite, and
    no claim of exhaustive semantic entailment.
    """
    audit_host_atomic_exchange(source, exchange)
    if type(question) is not str or type(selected_claim_ids) is not list:
        raise InvalidInput('V29_CONTEXT_REVIEW_INPUT_INVALID')
    selected=set(selected_claim_ids)
    if len(selected)!=len(selected_claim_ids):
        raise InvalidInput('V29_SELECTED_DUPLICATE_CLAIM')
    cases=[]
    if 'PENSION_EXCLUDED_BASIS' in _facet(question):
        for atom in exchange['atoms']:
            if atom['claim_id'] in selected:
                continue
            prop=atom['proposition']
            if not (re.search(r'세액공제|과세제외|비공제|원금',prop)
                    and re.search(r'인출|꺼내|언제든|찾아',prop)):
                continue
            refs=[r['cue_index'] for r in atom['source_refs']]
            lo=max(source.scope_first_cue,min(refs)-3)
            hi=min(source.scope_last_cue,max(refs)+1)
            # Exact original cues. ASR can omit spaces BETWEEN cue words.
            contextual=''.join(source.cues[i-1].text for i in range(lo,hi+1))
            contextual=re.sub(r'\s+','',contextual)
            if '연금저축' in contextual:
                cases.append(atom['claim_id'])
    if cases:
        raise InvalidInput('V29_PENSION_BASIS_CONTEXT_ELISION_UNSELECTED')
    return {
        'schema':'IRE_V6_V29_SOURCE_ELLIPSIS_RESIDUAL_AUDIT',
        'selected_count':len(selected),
        'question_facet_count':len(_facet(question)),
        'suspicious_elided_unselected_count':0,
        'source_semantic_completeness_independently_proven':False,
        'p0_go':False,
        'context_receipt_sha256':json_digest({
            'source_sha256':source.source_sha256,
            'question_sha256':sha256(question.encode('utf-8')),
            'exchange_candidate_digest':json_digest(exchange['atoms']),
            'selected_claim_ids':sorted(selected),
        })
    }


def attest_v29_code_blobs(root: Path, expected_git_blobs: dict) -> dict:
    """Verify configured source file bytes via Git's blob hashing without .git.

    Cannot by itself establish a complete tracked-tree/third-party dependency
    attestation; callers should additionally pin the export artifact digest.
    """
    if type(expected_git_blobs) is not dict or not 1<=len(expected_git_blobs)<=80:
        raise InvalidInput('V29_CODE_PIN_MAP_REQUIRED')
    root=Path(root)
    if not root.is_dir() or root.is_symlink():
        raise InvalidInput('V29_CODE_ROOT_INVALID')
    for name,wanted in sorted(expected_git_blobs.items()):
        if (type(name) is not str or not name.endswith('.py') or
            name.startswith('/') or '\\' in name or
            '..' in name.split('/') or
            not (name.startswith('ire/v5/') or name.startswith('ire/v6/')) or
            type(wanted) is not str or not _VALID_BLOB.fullmatch(wanted)):
            raise InvalidInput('V29_CODE_PIN_FORMAT_INVALID')
        path=root / name
        if not path.is_file() or path.is_symlink():
            raise InvalidInput('V29_CODE_PINNED_FILE_MISSING')
        data=path.read_bytes()
        got=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if got!=wanted:
            raise InvalidInput('V29_CODE_BLOB_SHA_MISMATCH')
    return {'verified_git_blob_count':len(expected_git_blobs),
            'pinned_files_sha256':json_digest(expected_git_blobs),
            'entire_repo_or_dependencies_independently_attested':False}


def evaluate_private_original_v29(root,question,*,zip_path,member_name,
                                  expected_zip_sha256,expected_srt_sha256,
                                  expected_video_id,expected_cue_count,
                                  source_manifest,expected_manifest_sha256,
                                  exchange,current_as_of,primary_evidence,
                                  chat_decisions,selected_claim_ids,
                                  relevance_decisions,candidate_dispositions,
                                  expected_git_blobs,scenario=None,
                                  isa_law_review=None):
    """Actual pinned private SRT -> V28 -> V27/V26/V25/V24 -> real V5 P3.

    A public-safe hash-chain receipt is emitted in the result. The host must
    persist *only that receipt*, not the embedded answer or raw exchange.
    """
    code=attest_v29_code_blobs(root,expected_git_blobs)
    original=verify_private_original_archive(
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
    context=audit_elided_pension_basis_v29(
        source,exchange,question,selected_claim_ids)
    result=evaluate_private_original_v27(
        root,question,zip_path=zip_path,member_name=member_name,
        expected_zip_sha256=expected_zip_sha256,
        expected_srt_sha256=expected_srt_sha256,
        expected_video_id=expected_video_id,
        expected_cue_count=expected_cue_count,
        source_manifest=source_manifest,
        expected_manifest_sha256=expected_manifest_sha256,
        exchange=exchange,current_as_of=current_as_of,
        primary_evidence=primary_evidence,
        chat_decisions=chat_decisions,
        selected_claim_ids=selected_claim_ids,
        relevance_decisions=relevance_decisions,
        candidate_dispositions=candidate_dispositions,
        scenario=scenario,isa_law_review=isa_law_review)
    if not (result.get('v5_p3_executed') is True and
            result.get('private_original_bytes_verified_for_this_call') is True and
            result.get('private_full_v27_answer_path_executed') is True and
            result.get('p0_go') is False and
            result.get('personal_trade_or_tax_approval') is False):
        raise InvalidInput('V29_FINAL_PATH_OR_SAFETY_FLAGS_INVALID')
    hash_payload={
        'schema':'IRE_V6_V29_PRIVATE_ORIGINAL_HASH_CHAIN_RECEIPT',
        'source_archive_sha256':original['archive_sha256'],
        'source_srt_sha256':original['srt_sha256'],
        'source_cue_census_sha256':original['source_cue_census_sha256'],
        'source_plan_sha256':original['source_plan_sha256'],
        'source_candidate_digest':original['atomic_candidate_digest'],
        'exchange_sha256':json_digest(exchange),
        'code_blob_attestation_sha256':code['pinned_files_sha256'],
        'code_blob_count':code['verified_git_blob_count'],
        'question_sha256':sha256(question.encode('utf-8')),
        'current_as_of':current_as_of,
        'selected_claim_ids':sorted(selected_claim_ids),
        'primary_evidence_sha256':json_digest(primary_evidence),
        'chat_review_sha256':json_digest(chat_decisions),
        'relevance_review_sha256':json_digest(relevance_decisions),
        'candidate_dispositions_sha256':json_digest(candidate_dispositions),
        'source_context_receipt_sha256':context['context_receipt_sha256'],
        'v5_legacy_answer_sha256':result['v5_p3_legacy_answer_sha256'],
        'current_law_reassessment_sha256':result['current_law_reassessment_sha256'],
        'final_answer_sha256':sha256(result['answer_text'].encode('utf-8')),
        'v5_p3_executed':True,
        'actual_private_original_verified':True,
        'independent_semantic_gold_verified':False,
        'official_primary_body_externally_authenticated':False,
        'whole_repository_dependencies_attested':False,
        'personal_trade_or_tax_approval':False,
        'p0_go':False,
    }
    return {**result,
            'schema':'IRE_V6_V29_PRIVATE_ORIGINAL_HASH_CHAIN_ANSWER',
            'hash_only_public_receipt':{
                **hash_payload,
                'receipt_sha256':json_digest(hash_payload),
            },
            'p0_go':False,
            'status':'V29_REAL_PRIVATE_SOURCE_E2E_RECORDED_SEMANTIC_P0_NO_GO'}
