"""E4 original publisher chapter-1: author says Gujarati, asymmetric risk.

Wiley's original Chapter 1 PDF is primary evidence of WHAT THE AUTHOR
WROTE, not independent certification of Gujarati etymology or a promise
that any strategy really achieves low losses or high investment returns.
Do not promote V123 OPEN, do not certify personal applicability.
"""
from __future__ import annotations

import io
import re
import ssl
from urllib.parse import urlsplit
from urllib.request import urlopen,Request

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput,QualityNotProven

CHAPTER_URL="https://catalogimages.wiley.com/images/db/pdf/9780470043899.excerpt.pdf"
SCHEMA="IRE_V166_E4_WILEY_BOOK_AUTHOR_CHAPTER_CUSTODY_V1"


def _need(ok,code):
    if not ok:
        raise InvalidInput("V166_E4_WILEY_CH1_"+code)


def _ensure_chapter_url(url):
    p=urlsplit(url)
    _need(type(url) is str and url==CHAPTER_URL and
          p.scheme=="https" and p.hostname=="catalogimages.wiley.com" and
          p.username is None and p.password is None and
          p.port in (None,443) and not p.fragment,
          "ORIGINAL_PUBLISHER_PDF_URL")
    return p.hostname


def fetch_wiley_original_chapter_pdf(url=CHAPTER_URL):
    _ensure_chapter_url(url)
    req=Request(url,headers={
        "User-Agent":"IRE-V166-E4-Wiley-original-chapter/1.0",
        "Accept":"application/pdf","Accept-Encoding":"identity"})
    try:
        with urlopen(req,timeout=18,context=ssl.create_default_context()) as res:
            _need(res.status==200 and res.geturl()==url,
                  "PUBLISHER_ORIGIN_REDIRECT_NOT_SAME_OR_HTTP")
            body=res.read(3*1024*1024+1)
    except (OSError,TimeoutError) as exc:
        raise QualityNotProven("V166_E4_WILEY_CH1_ORIGIN_UNAVAILABLE") from exc
    if not (type(body) is bytes and body.startswith(b"%PDF-")
            and 10000<=len(body)<=3*1024*1024):
        raise QualityNotProven("V166_E4_WILEY_CH1_RAW_BYTES_NOT_PDF")
    return body


def audit_author_original_chapter(body,*, owner_source_sha256):
    import pypdf
    _need(type(owner_source_sha256) is str and
          re.fullmatch(r"[0-9a-f]{64}",owner_source_sha256) is not None,
          "OWNER_SOURCE_SHA_REQUIRED")
    _need(type(body) is bytes and body.startswith(b"%PDF-")
          and 10000<=len(body)<=3*1024*1024,
          "PUBLISHER_ORIGINAL_PDF_BYTES_REQUIRED")
    try:
        reader=pypdf.PdfReader(io.BytesIO(body))
        _need(2<=len(reader.pages)<=100,"PDF_PAGE_CENSUS")
        source=" ".join((page.extract_text() or "") for page in reader.pages)
    except (ValueError,Exception) as exc:
        raise QualityNotProven("V166_E4_WILEY_CH1_PDF_TEXT_NOT_REPLAYABLE") from exc
    text=re.sub(r"\s+"," ",source).lower()
    dhandho=re.search(r"dhandho.{0,95}is a gujarati word",text) is not None
    asym=("heads, i win" in text and
          ("tails, i don" in text or "tails, i don’t" in text))
    caveat=("not a risk-free bet" in text or
            "possibility of going broke" in text)
    if not (dhandho and asym and caveat and
            "patel motel dhandho" in text):
        raise QualityNotProven("V166_E4_WILEY_CH1_AUTHOR_TOKENS_OR_CAVEATS_MISSING")
    return {
        "schema":SCHEMA,
        "original_publisher_pdf_url":CHAPTER_URL,
        "official_original_pdf_body_sha256":sha256(body),
        "pdf_page_count":len(reader.pages),
        "owner_source_sha256":owner_source_sha256,
        "original_author_calls_dhandho_a_gujarati_word":True,
        "original_author_describes_asymmetric_risk_reward":True,
        "original_author_also_discusses_nonzero_loss_risk":True,
        "independent_linguistic_etymology_certified":False,
        "real_world_loss_or_return_limits_certified":False,
        "book_author_quote_not_investment_guarantee":True,
        "full_owner_video_v123_final_pass":False,
        "personal_advice_approved":False,
        "p0_go":False,
    }
