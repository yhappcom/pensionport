"""V166 E4 factual context from Berkshire's ORIGINAL corporate letters index.

B0001 C00009 compares the scope of books/letter compilations. Berkshire's
issuer index is first-party for which annual letters exist, but DOES NOT prove
which third-party anthology is being discussed or the video's subjective
'after wealth scaled' interpretation. C00010 about 1950s partnerships cannot
be certified from the Berkshire 1977+ index.
"""
from __future__ import annotations

import re
import ssl
from urllib.parse import urlsplit
from urllib.request import Request,urlopen

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput,QualityNotProven

URL="https://www.berkshirehathaway.com/letters/letters.html"
SCHEMA="IRE_V166_E4_BERKSHIRE_CORPORATE_ARCHIVE_CONTEXT_ONLY_V1"


def _validate_url(url):
    p=urlsplit(url)
    if (type(url) is not str or p.scheme!="https"
        or p.hostname not in ("www.berkshirehathaway.com","berkshirehathaway.com")
        or p.port not in (None,443) or p.username is not None
        or p.password is not None or p.fragment
        or p.path!="/letters/letters.html"):
        raise InvalidInput("V166_E4_COMPANY_PRIMARY_ORIGIN_INVALID")
    return p.hostname


def fetch_official_berkshire_letters_index(url=URL):
    hostname=_validate_url(url)
    req=Request(url,headers={"User-Agent":"IRE-V166-E4-primary-context/1.0",
                             "Accept":"text/html","Accept-Encoding":"identity"})
    ctx=ssl.create_default_context()
    try:
        with urlopen(req,timeout=18,context=ctx) as response:
            if _validate_url(response.geturl())!=hostname or response.status!=200:
                raise QualityNotProven("V166_E4_COMPANY_PRIMARY_REDIRECT_OR_STATUS")
            body=response.read(2*1024*1024+1)
    except (OSError,TimeoutError) as exc:
        raise QualityNotProven("V166_E4_COMPANY_PRIMARY_HTTPS_UNAVAILABLE") from exc
    if not 200<len(body)<=2*1024*1024:
        raise QualityNotProven("V166_E4_COMPANY_PRIMARY_BYTES_INVALID")
    return body


def audit_berkshire_letters_catalogue_only(body, *, source_sha256,
                                           b0001_statuses):
    if (type(body) is not bytes or len(body)<200 or
        type(source_sha256) is not str or
        re.fullmatch(r"[0-9a-f]{64}",source_sha256) is None or
        type(b0001_statuses) is not dict or
        b0001_statuses!={"C00009":"OPEN","C00010":"OPEN"}):
        raise InvalidInput("V166_E4_COMPANY_B0001_ATOM_STATUS_REQUIRED")
    source=body.decode("utf-8",errors="replace").lower()
    if not all(token in source for token in
               ("berkshire", "shareholder letters", "1977", "1965", "2024")):
        raise QualityNotProven("V166_E4_COMPANY_CORPORATE_LETTER_SCOPE_NOT_IN_ORIGINAL")
    return {
        "schema":SCHEMA,
        "original_official_company_url":URL,
        "original_company_index_sha256":sha256(body),
        "original_source_sha256":source_sha256,
        "first_listed_official_company_annual_letter_year":1977,
        "official_book_compilation_mentions_earliest_letter_year":1965,
        "official_book_compilation_mentions_latest_letter_year":2024,
        "only_corporate_archive_range_supported":True,
        "third_party_book_volume_composition_authenticated":False,
        "early_partnership_investment_style_authenticated":False,
        "C00009_native_v123_status_after_context":"OPEN",
        "C00010_native_v123_status_after_context":"OPEN",
        "current_financial_regulation_verified":False,
        "real_owner_knowledge_autoapproved":False,
        "independent_gold_certified":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
