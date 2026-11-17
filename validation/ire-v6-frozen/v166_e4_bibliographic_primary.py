"""V166 E4 original-book bibliography authority, NOT investment effectiveness.

Wiley is original publisher for The Dhandho Investor. An original publisher
can attest title/author/ISBN, but not contemporary tax law or personal advice.
Any chat review still needs source-language/ASR semantic adjudication.
"""
from __future__ import annotations

import re
import ssl
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput,QualityNotProven

WILEY_ORIGINAL = (
    "https://www.wiley.com/en-us/"
    "The%2BDhandho%2BInvestor%3A%2BThe%2BLow%2BRisk%2BValue%2BMethod"
    "%2Bto%2BHigh%2BReturns-p-9780470043899")
BIBLIOGRAPHY_SCHEMA="IRE_V166_E4_PUBLISHER_BOOK_BIBLIOGRAPHY_ONLY_V1"
EXPECTED = {
    "original_english_title": "The Dhandho Investor",
    "original_author": "Mohnish Pabrai",
    "hardcover_isbn_digits": "9780470043899",
}


def _validate_publisher_url(url):
    if type(url) is not str:
        raise InvalidInput("V166_E4_PUBLISHER_URL_INVALID")
    p=urlsplit(url)
    if (p.scheme!="https" or p.hostname!="www.wiley.com"
        or p.username is not None or p.password is not None
        or p.port not in (None,443) or p.fragment
        or "/en-us/" not in p.path):
        raise InvalidInput("V166_E4_UNTRUSTED_PUBLISHER_ORIGIN")
    return p.hostname


def fetch_wiley_publisher_bytes(url=WILEY_ORIGINAL):
    _validate_publisher_url(url)
    request=Request(url,headers={
        "User-Agent":"IRE-V166-E4-bibliographic-custody/1.0",
        "Accept":"text/html,text/plain,application/xhtml+xml",
        "Accept-Encoding":"identity",
    })
    ctx=ssl.create_default_context()
    try:
        with urlopen(request,timeout=18,context=ctx) as response:
            _validate_publisher_url(response.geturl())
            if response.status != 200:
                raise QualityNotProven("V166_E4_PUBLISHER_HTTP_UNAVAILABLE")
            body=response.read(3*1024*1024+1)
    except (OSError,TimeoutError) as exc:
        raise QualityNotProven("V166_E4_PUBLISHER_LIVE_TLS_UNAVAILABLE") from exc
    if type(body) is not bytes or not 150<len(body)<=3*1024*1024:
        raise QualityNotProven("V166_E4_PUBLISHER_BODY_NOT_SOURCE_BOUND")
    return body


def audit_original_publisher_book_metadata(body, *,
                                            original_owner_source_sha256=None):
    if type(body) is not bytes or len(body)<150:
        raise InvalidInput("V166_E4_PUBLISHER_BYTES_REQUIRED")
    text=body.decode("utf-8",errors="replace")
    title="The Dhandho Investor" in text
    author="Mohnish Pabrai" in text
    isbn=EXPECTED["hardcover_isbn_digits"] in re.sub(r"[^0-9]","",text)
    # Real Wiley page may encode book titles in rich HTML, but must still
    # contain the canonical title, author and 13-digit hardcover ISBN.
    if not (title and author and isbn):
        raise QualityNotProven("V166_E4_PUBLISHER_BIBLIOGRAPHIC_ELEMENTS_MISSING")
    if (original_owner_source_sha256 is not None and
        (type(original_owner_source_sha256) is not str or
         re.fullmatch("[0-9a-f]{64}",original_owner_source_sha256) is None)):
        raise InvalidInput("V166_E4_OWNER_SOURCE_PIN_INVALID")
    return {
        "schema":BIBLIOGRAPHY_SCHEMA,
        "publisher_name":"Wiley",
        "official_publisher_url":WILEY_ORIGINAL,
        "official_original_body_sha256":sha256(body),
        "original_english_title":EXPECTED["original_english_title"],
        "original_author":EXPECTED["original_author"],
        "hardcover_isbn_digits":EXPECTED["hardcover_isbn_digits"],
        "owner_source_sha256":original_owner_source_sha256,
        "source_language_asr_corrected":False,
        "korean_translation_publisher_verified":False,
        "investment_principle_effectiveness_verified":False,
        "historical_buffett_performance_verified":False,
        "financial_legal_evidence":False,
        "research_final_approval":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
