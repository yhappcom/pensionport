"""Fail-closed video-publication provenance and high-risk financial scope checks.

Only structural/date arithmetic and conservative lexical challenges. They cannot
prove an upload equals recording date, issuer authenticity, source semantic truth,
independent human gold or regulatory applicability to an individual.
No network, model API, private source text, personally identifiable data or trades.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from .codec import VIDEO, json_digest, require_hash
from .errors import InvalidInput

_KST = timezone(timedelta(hours=9))
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_URL = re.compile(r"https://(?:www\.)?youtube\.com/(?:watch\?v=|shorts/)([A-Za-z0-9_-]{11})(?:\Z|[&#?])")
_SAFE_RULE = re.compile(r"[A-Z0-9_:-]{6,100}\Z")
_MONEY = re.compile(r"(?:ETF|상장지수펀드)", re.I)
_IRP = re.compile(r"IRP|개인형퇴직연금", re.I)


def _day(value, name):
    if type(value) is not str or not _ISO_DATE.fullmatch(value):
        raise InvalidInput(name + '_DATE_FORMAT')
    try:
        d=date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidInput(name + '_INVALID_REAL_DATE') from exc
    return d


def publication_temporal_rule_gate(*, video_id, source_sha256, youtube_url,
                                   date_published, roster_date,
                                   law_versions):
    """Review effective windows against native YouTube publish timestamp.

    Fails dates newer than a video's *publication*, not necessarily than
    recording. Even a matching date and a SHA-pinned law do NOT issue approval.
    The roster date is collected context, not independently signed chronology.
    """
    if type(video_id) is not str or not VIDEO.fullmatch(video_id):
        raise InvalidInput('PUB_VIDEO_ID_INVALID')
    require_hash(source_sha256, 'PUB_SOURCE_SHA256')
    match=_URL.fullmatch(youtube_url) if type(youtube_url) is str else None
    if match is None or match.group(1)!=video_id:
        raise InvalidInput('PUB_NATIVE_URL_VIDEO_ID_MISMATCH')
    if type(date_published) is not str or len(date_published)>40:
        raise InvalidInput('PUB_TIMESTAMP_INVALID')
    try:
        observed=datetime.fromisoformat(date_published)
    except (ValueError,TypeError) as exc:
        raise InvalidInput('PUB_TIMESTAMP_INVALID') from exc
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise InvalidInput('PUB_TIMESTAMP_MUST_HAVE_UTC_OFFSET')
    if not -(14*3600)<=observed.utcoffset().total_seconds()<=14*3600:
        raise InvalidInput('PUB_TIMESTAMP_BAD_OFFSET')
    local_publish=observed.astimezone(_KST)
    roster=_day(roster_date,'ROSTER') if roster_date is not None else None
    if type(law_versions) is not list or not 1<=len(law_versions)<=30:
        raise InvalidInput('PUB_RULE_LIST_REQUIRED')
    rows=[];keys=set()
    for item in law_versions:
        if type(item) is not dict or set(item)!={
            'rule_id','effective_from','effective_to','law_body_sha256'}:
            raise InvalidInput('PUB_RULE_SCHEMA_INVALID')
        rid=item['rule_id']
        if type(rid) is not str or not _SAFE_RULE.fullmatch(rid) or rid in keys:
            raise InvalidInput('PUB_RULE_ID_INVALID_OR_DUPLICATE')
        keys.add(rid)
        start=_day(item['effective_from'],'RULE_START')
        end=_day(item['effective_to'],'RULE_END') if item['effective_to'] is not None else None
        if end is not None and end<=start:
            raise InvalidInput('PUB_RULE_END_INVALID')
        pinned=item['law_body_sha256']
        if pinned is not None:require_hash(pinned,'PUB_LAW_BODY_SHA')
        if local_publish.date()<start:
            status='FUTURE_RULE_NOT_VALID_AT_PUBLICATION'
        elif end is not None and local_publish.date()>=end:
            status='SUPERSEDED_RULE_NOT_VALID_AT_PUBLICATION'
        elif pinned is None:
            status='DATE_POTENTIALLY_COMPATIBLE_UNPINNED_PRIMARY_BYTES'
        else:
            status='DATE_COMPATIBLE_PINNED_BODY_RECORDING_TIME_UNKNOWN'
        rows.append({'rule_id':rid,'effective_from':start.isoformat(),
                     'effective_to':end.isoformat() if end else None,
                     'law_body_sha256':pinned,'temporal_status':status,
                     'rule_semantics_verified':False,
                     'applied_to_speaker_or_individual':False})
    return {
        'schema':'IRE_V6_PUBLICATION_TEMPORAL_RULE_GATE_V1',
        'video_id':video_id,'source_sha256':source_sha256,
        'youtube_url':youtube_url,'published_native_offset':observed.isoformat(),
        'published_utc':observed.astimezone(timezone.utc).isoformat(),
        'published_kst':local_publish.isoformat(),
        'roster_date':roster_date,
        'roster_matches_native_offset_calendar_date':(
            observed.date()==roster if roster is not None else None),
        'native_youtube_metadata_observed_not_signed':True,
        'recording_time_independently_known':False,
        'rule_assessments':rows,
        'assessment_sha256':json_digest(rows),
        'source_semantics_independently_verified':False,
        'individual_tax_or_pension_application_approved':False,
        'p0_go':False
    }


def _positive_money(value, name):
    if type(value) is not int or not 1<=value<=10**14:
        raise InvalidInput(name+'_POSITIVE_INT_WON_REQUIRED')
    return Decimal(value)


def _rate(value):
    if type(value) is not str or not re.fullmatch(r'(?:[0-9]{1,2})(?:\.[0-9]{1,4})?',value):
        raise InvalidInput('PAYOUT_RATE_DECIMAL_PERCENT_REQUIRED')
    try:d=Decimal(value)
    except InvalidOperation as exc:raise InvalidInput('PAYOUT_RATE_INVALID') from exc
    if d<=0 or d>=100:raise InvalidInput('PAYOUT_RATE_OUT_OF_RANGE')
    return d


def audit_rate_frequency(*, principal_won, yield_percent, claimed_rate_period,
                         expected_monthly_payout_won, tolerance_percent='1'):
    """Detect '월 6%' vs an annual 6%/12 payout arithmetic contradiction.

    Mathematical compatibility is NOT cash-distribution certainty, total return,
    withdrawal permission, dividend stability or investment suitability.
    """
    p=_positive_money(principal_won,'PAYOUT_PRINCIPAL')
    amount=_positive_money(expected_monthly_payout_won,'PAYOUT_EXPECTED')
    rate=_rate(yield_percent)
    if claimed_rate_period not in ('MONTH','YEAR') or type(claimed_rate_period) is not str:
        raise InvalidInput('PAYOUT_RATE_PERIOD_INVALID')
    tol=_rate(tolerance_percent)
    monthly=p*rate/Decimal(100)
    annual_monthly=monthly/Decimal(12)
    match_monthly=abs(amount-monthly)<=monthly*tol/Decimal(100)
    match_annual=abs(amount-annual_monthly)<=annual_monthly*tol/Decimal(100)
    match='MONTH' if match_monthly and not match_annual else 'YEAR' if match_annual and not match_monthly else 'AMBIGUOUS' if match_monthly and match_annual else 'NEITHER'
    conflict=match in ('YEAR','MONTH') and match!=claimed_rate_period
    return {
        'schema':'IRE_V6_FINANCE_RATE_FREQUENCY_AUDIT_V1',
        'principal_won':principal_won,
        'claimed_rate_percent':yield_percent,
        'claimed_rate_period':claimed_rate_period,
        'reported_monthly_payout_won':expected_monthly_payout_won,
        'theoretical_monthly_if_monthly_rate_won':str(monthly),
        'theoretical_monthly_if_annual_rate_won':str(annual_monthly),
        'reported_payout_matches_rate_period':match,
        'period_conflict':conflict,
        'status':'RATE_PERIOD_CONTRADICTION_REVIEW' if conflict else 'NO_PROVEN_ARITHMETIC_CONFLICT' if match==claimed_rate_period else 'SCOPE_OR_ROUNDING_REVIEW',
        'principal_loss_possible':True,'monthly_dividend_guaranteed':False,
        'financial_factual_truth_approved':False,
        'p0_go':False
    }


def flag_legal_scope_overgeneralization(text):
    """Conservative source phrase scanner, not a law or entailment verifier."""
    if type(text) is not str or len(text)>4000:
        raise InvalidInput('LEGAL_SCOPE_TEXT_INVALID')
    flags=[]
    if (_MONEY.search(text) and re.search(r'매매\s*(?:차익|수익)|매도\s*수익',text)
        and re.search(r'15\s*\.\s*4\s*%',text)
        and not re.search(r'국내주식형|국내\s*주식\s*ETF\s*제외|비과세\s*예외',text)):
        flags.append('ETF_GAINS_TAX_TYPE_SCOPE_MISSING')
    if (_IRP.search(text) and re.search(r'중도\s*(?:인출|출금)',text)
        and re.search(r'아예|전혀|절대|불가능|못\s*합니다|안\s*돼',text)
        and not re.search(r'법정\s*사유|예외\s*사유|특정\s*사유',text)):
        flags.append('IRP_MIDTERM_WITHDRAWAL_LEGAL_EXCEPTIONS_MISSING')
    return {'schema':'IRE_V6_LEGAL_SCOPE_REVIEW_V1',
            'source_phrase_sha256':json_digest({'text':text}),
            'review_flags':flags,'source_meaning_independently_verified':False,
            'official_law_applicability_approved':False,'p0_go':False}
