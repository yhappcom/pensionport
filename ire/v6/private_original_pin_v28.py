"""V28: independently pin private-original SRT bytes before any source/answer replay.

No private text or source ZIP is committed or returned.  The caller supplies
the *precommitted* archive and member SHA256, not values calculated from
the untrusted file inside this function.  Exact raw-source provenance and
semantic correctness are different claims.
"""
from __future__ import annotations

import hashlib
import re
import stat
import zipfile
from pathlib import Path

from .atomic_exchange import audit_host_atomic_exchange
from .codec import json_digest, sha256
from .errors import InvalidInput
from .source import parse_srt, verify_source

_HEX64=re.compile(r'[a-f0-9]{64}\Z')
_ID=re.compile(r'[a-zA-Z0-9_-]{11}\Z')
_MAX_ARCHIVE=48*1024*1024
_MAX_SRT=32*1024*1024


def _pinned(value,name):
    if type(value) is not str or not _HEX64.fullmatch(value):
        raise InvalidInput('V28_'+name+'_SHA256_INVALID')
    return value


def _file_sha256(path, max_bytes):
    h=hashlib.sha256()
    n=0
    with path.open('rb') as stream:
        while True:
            data=stream.read(1024*1024)
            if not data:
                break
            n+=len(data)
            if n>max_bytes:
                raise InvalidInput('V28_ORIGINAL_ARCHIVE_TOO_LARGE')
            h.update(data)
    return h.hexdigest(),n


def verify_private_original_archive(zip_path: Path, *, member_name: str,
                                    expected_zip_sha256: str,
                                    expected_srt_sha256: str,
                                    expected_video_id: str,
                                    expected_cue_count: int,
                                    source_manifest: dict | None = None,
                                    expected_manifest_sha256: str | None = None,
                                    exchange: dict | None = None) -> dict:
    """Read a private original, returning only non-text provenance.

    Does not self-pin the source. Optional full-video source/atomic attestations
    still do not establish independently correct meaning or complete recall.
    """
    zpin=_pinned(expected_zip_sha256,'ARCHIVE')
    spin=_pinned(expected_srt_sha256,'SRT')
    if (type(member_name) is not str or len(member_name)>256 or
        '\\' in member_name or member_name.startswith('/') or
        member_name.endswith('/') or '..' in member_name.split('/') or
        member_name.startswith('__MACOSX/')):
        raise InvalidInput('V28_UNSAFE_OR_INVALID_ZIP_MEMBER')
    if type(expected_video_id) is not str or not _ID.fullmatch(expected_video_id):
        raise InvalidInput('V28_VIDEO_ID_INVALID')
    if (type(expected_cue_count) is not int or
        not 1<=expected_cue_count<=50000):
        raise InvalidInput('V28_CUE_COUNT_INVALID')
    if not member_name.endswith('/youtube-transcript-'+expected_video_id+'.srt'):
        raise InvalidInput('V28_VIDEO_MEMBER_ID_MISMATCH')
    path=Path(zip_path)
    if not path.is_file() or path.is_symlink():
        raise InvalidInput('V28_PRIVATE_ZIP_FILE_NOT_FOUND')
    zsha,zbytes=_file_sha256(path,_MAX_ARCHIVE)
    if zsha!=zpin:
        raise InvalidInput('V28_ORIGINAL_ARCHIVE_BYTES_MISMATCH')
    with zipfile.ZipFile(path) as archive:
        matches=[x for x in archive.infolist() if x.filename==member_name]
        if len(matches)!=1:
            raise InvalidInput('V28_MISSING_OR_DUPLICATE_SRT')
        info=matches[0]
        if (info.is_dir() or info.file_size==0 or info.file_size>_MAX_SRT or
            (info.external_attr>>16)&0o170000==stat.S_IFLNK):
            raise InvalidInput('V28_UNSAFE_OR_OVERSIZED_SRT_MEMBER')
        try:
            raw=archive.read(info)
        except (OSError,RuntimeError,zipfile.BadZipFile) as exc:
            raise InvalidInput('V28_ORIGINAL_ZIP_CRC_OR_READ_FAILURE') from exc
    if sha256(raw)!=spin:
        raise InvalidInput('V28_ORIGINAL_SRT_BYTES_MISMATCH')
    cues=parse_srt(raw)
    if len(cues)!=expected_cue_count:
        raise InvalidInput('V28_ORIGINAL_SRT_CUE_COUNT_MISMATCH')
    if (source_manifest is None)!=(expected_manifest_sha256 is None):
        raise InvalidInput('V28_SOURCE_PLAN_PIN_REQUIRED')
    if exchange is not None and source_manifest is None:
        raise InvalidInput('V28_EXCHANGE_WITHOUT_SOURCE_PLAN')
    receipt={
        'schema':'IRE_V6_V28_PINNED_PRIVATE_SOURCE_RECEIPT',
        'archive_sha256':zsha,'archive_size_bytes':zbytes,
        'video_id':expected_video_id,'srt_sha256':spin,
        'srt_size_bytes':len(raw),'original_cue_count':len(cues),
        'source_plan_verified':False,'atomic_exchange_verified':False,
        'private_full_v27_answer_path_executed':False,
        'original_source_semantic_recall_independently_proven':False,
        'current_financial_law_independently_authenticated':False,
        'personal_trade_or_tax_approved':False,'p0_go':False,
        'status':'V28_ACTUAL_PRIVATE_ORIGINAL_BYTES_VERIFIED_ONLY',
    }
    if source_manifest is not None:
        plan_sha=_pinned(expected_manifest_sha256,'MANIFEST')
        source=verify_source(
            raw,source_manifest,expected_source_sha256=spin,
            expected_manifest_sha256=plan_sha)
        if source.video_id!=expected_video_id:
            raise InvalidInput('V28_PLAN_VIDEO_ID_MISMATCH')
        if (source.scope_first_cue!=1 or
            source.scope_last_cue!=len(cues)):
            raise InvalidInput('V28_FULL_VIDEO_SCOPE_REQUIRED')
        receipt['source_plan_verified']=True
        receipt['source_plan_sha256']=plan_sha
        receipt['source_cue_census_sha256']=source.cue_census_sha256
        if exchange is not None:
            check=audit_host_atomic_exchange(source,exchange)
            receipt['atomic_exchange_verified']=True
            receipt['atomic_candidate_count']=check['proposed_atomic_claims']
            receipt['unresolved_original_cues']=check['unresolved_cues']
            receipt['suspicious_no_atom_cues']=check['suspicious_no_atom_cues']
            receipt['atomic_candidate_digest']=check['atom_candidate_digest']
            receipt['status']='V28_PRIVATE_ORIGINAL_STRUCTURAL_EXCHANGE_CHECKED_ONLY'
    return receipt


def evaluate_private_original_v27(root, question, *, zip_path, member_name,
                                  expected_zip_sha256, expected_srt_sha256,
                                  expected_video_id, expected_cue_count,
                                  source_manifest, expected_manifest_sha256,
                                  exchange, current_as_of, primary_evidence,
                                  chat_decisions, selected_claim_ids,
                                  relevance_decisions, candidate_dispositions,
                                  scenario=None, isa_law_review=None):
    """Execute actual V27/V26/V25/V5 only with the private original bound.

    This intentionally requires an *already reviewed complete* host exchange
    and current-law evidence; never synthesizes same-chat legal labels.
    """
    receipt=verify_private_original_archive(
        zip_path,member_name=member_name,
        expected_zip_sha256=expected_zip_sha256,
        expected_srt_sha256=expected_srt_sha256,
        expected_video_id=expected_video_id,
        expected_cue_count=expected_cue_count,
        source_manifest=source_manifest,
        expected_manifest_sha256=expected_manifest_sha256,
        exchange=exchange)
    if receipt['suspicious_no_atom_cues'] or receipt['unresolved_original_cues']:
        raise InvalidInput('V28_INCOMPLETE_PRIVATE_ORIGINAL_ATOMS')
    # The API evaluates the same source/exchange again; nothing is implicitly
    # approved by validating exact original bytes.
    with zipfile.ZipFile(Path(zip_path)) as archive:
        raw=archive.read(member_name)
    source=verify_source(
        raw,source_manifest,expected_source_sha256=receipt['srt_sha256'],
        expected_manifest_sha256=receipt['source_plan_sha256'])
    from .source_facet_audit_v27 import evaluate_current_question_v27
    result=evaluate_current_question_v27(
        Path(root),question,source=source,exchange=exchange,
        current_as_of=current_as_of,primary_evidence=primary_evidence,
        chat_decisions=chat_decisions,selected_claim_ids=selected_claim_ids,
        relevance_decisions=relevance_decisions,
        candidate_dispositions=candidate_dispositions,
        scenario=scenario,isa_law_review=isa_law_review)
    if result.get('p0_go') is not False or result.get('personal_trade_or_tax_approval') is not False:
        raise InvalidInput('V28_UNSAFE_FINAL_FINANCE_APPROVAL')
    return {**result,'schema':'IRE_V6_V28_PRIVATE_ORIGINAL_V27_FULL_PATH_RECEIPT',
            'private_original_receipt_sha256':json_digest(receipt),
            'private_original_bytes_verified_for_this_call':True,
            'private_full_v27_answer_path_executed':True,
            'independent_semantic_correctness_proven':False,
            'p0_go':False}
