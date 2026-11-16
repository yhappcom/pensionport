"""V146 public SHA-only status gate for owner real-source semantic review.

A sample of source-reviewed correction dockets must never count as certified
TP/FP/FN, 13/13 V123 approval, current official issuer evidence, or an
authorized parent V128 knowledge commit. No owner-private text is embedded.
"""
from __future__ import annotations
import re
from ire.v6.errors import InvalidInput

SCHEMA='V146_SOURCE_PINNED_CHATGPT_MEANING_PARTIAL_REVIEW_HOLD_PUBLIC_V1'
SOURCE_SHA='638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d'
SHA_RE=re.compile('^[0-9a-f]{64}$')


def assess_v146_public_receipt(row):
    if type(row) is not dict or row.get('schema')!=SCHEMA:
        raise InvalidInput('V146_PUBLIC_SCHEMA')
    expected={'source_sha256':SOURCE_SHA,'original_cues':1481,
      'baseline_v6_host_scopes':13,'baseline_atoms':274,
      'targeted_semantic_source_context_review_count':72,
      'untriaged_source_semantic_claim_count':202,
      'triaged_newly_from_v123_open':70,
      'formally_open_v123_baseline_claims':272,
      'baseline_excluded_claims':2,
      'speaker_unknown_baseline_claims':274,
      'baseline_stance_unresolved':178,
      'baseline_explicit_condition_atoms':10,
      'baseline_explicit_exception_atoms':2,
      'official_web_corporate_claims_checked':1,
      'official_issuer_original_body_bytes_cryptographically_verified':0,
      'v123_formally_passed_scopes':0,'v128_durable_knowledge_items':0,
      'all_video_v123_pass':False,
      'independent_semantic_precision_recall_measured':False,
      'formal_financial_advice_approved':False,'p0_go':False,
      'status':'PARTIAL_SOURCE_MEANING_REVIEW_WITH_NO_V123_APPROVAL'}
    for key,expected_value in expected.items():
        if key not in row or type(row[key]) is not type(expected_value) or row[key]!=expected_value:
            raise InvalidInput('V146_FALSE_COMPLETION_OR_DRIFT_'+key)
    if not isinstance(row.get('private_rows_sha256'),str) or not SHA_RE.fullmatch(row['private_rows_sha256']):
        raise InvalidInput('V146_PRIVATE_HASH_MISSING')
    cases=row.get('targeted_issue_categories')
    if type(cases) is not dict or not cases or any(type(v) is not int or v<=0 for v in cases.values()) or sum(cases.values())!=72:
        raise InvalidInput('V146_TARGETED_CASE_CENSUS')
    return {'schema':'V146_P0_SEMANTIC_QUALITY_HOLD_GUARD',
            'status':'V123_SEMANTIC_REVIEW_NOT_FINAL',
            'actual_targeted_source_meant_claims':72,
            'v123_formal_open_unchanged':272,
            'new_knowledge_entries':0,'not_independent_gold':True,
            'next_required':'AUTHOR_SOURCE_BOUND_CORRECTIONS_AND_REPLAY_V6_HOST_THEN_V123',
            'p0_go':False}
