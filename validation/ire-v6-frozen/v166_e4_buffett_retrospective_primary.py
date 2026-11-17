"""First-party retrospective evidence on Buffett's partnership, not 1957
letter authentication and not a V123 status writer. Preserve BOTH relative
return goals and avoidance of permanent capital loss."""
import html
import io
import re
import ssl
from urllib.request import Request,urlopen
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput,QualityNotProven

URL_2001="https://www.berkshirehathaway.com/2001ar/2001letter.html"
URL_2020="https://www.berkshirehathaway.com/letters/2020ltr.pdf"
URLS={URL_2001,URL_2020}

def fetch_primary(url):
    if url not in URLS:
        raise InvalidInput("E4_BERKSHIRE_RETROSPECTIVE_ORIGIN")
    try:
        req=Request(url,headers={"User-Agent":"IRE-V166-issuer-evidence/1.0",
                                 "Accept-Encoding":"identity"})
        with urlopen(req,timeout=25,context=ssl.create_default_context()) as res:
            if res.status!=200 or res.geturl()!=url:
                raise QualityNotProven("E4_BERKSHIRE_RETROSPECTIVE_REDIRECT")
            body=res.read(8*1024*1024+1)
    except OSError as exc:
        raise QualityNotProven("E4_BERKSHIRE_RETROSPECTIVE_UNAVAILABLE") from exc
    if not 500<len(body)<=8*1024*1024:
        raise QualityNotProven("E4_BERKSHIRE_RETROSPECTIVE_BYTES")
    return body

def normalized(text):
    return re.sub(r"\s+"," ",text.replace("’","'")).lower().strip()

def audit_primary_retrospectives(body_2001,body_2020):
    """Machine checks of narrow excerpts; semantic judgment stays in ChatGPT.
    No claim about exact trading aggressiveness can be inferred.
    """
    from pypdf import PdfReader
    if (type(body_2001) is not bytes or type(body_2020) is not bytes
        or not body_2020.startswith(b"%PDF-") or
        any(not 500<len(b)<=8*1024*1024 for b in (body_2001,body_2020))):
        raise InvalidInput("E4_BERKSHIRE_RETROSPECTIVE_BODY_SCHEMA")
    data=html.unescape(re.sub(r"(?is)<(?:script|style)\b[^>]*>.*?</(?:script|style)>|<[^>]*>"," ",body_2001.decode("utf-8",errors="replace")))
    d1=normalized(data)
    try:
        pdf=PdfReader(io.BytesIO(body_2020))
        if len(pdf.pages)<10:
            raise ValueError("page count")
        # Printed pages 10 and 11 in the issuer's 2020 letter; PDF indices
        # 8 and 9, with preceding pages numbered differently.
        d2=normalized(" ".join((pdf.pages[i].extract_text() or "") for i in (8,9)))
    except Exception as exc:
        raise QualityNotProven("E4_BERKSHIRE_RETROSPECTIVE_PDF_PARSE") from exc
    markers1=("may 5, 1956","the ground rules",
              "relative results are what concern us",
              "i cannot promise results to partners")
    markers2=("the first three of those formed in 1956",
              "in 1962","amalgamated 12 partnerships",
              "annual threshold of 6%","shortfall was to be carried forward",
              "aversion to permanent loss of capital")
    if not all(x in d1 for x in markers1):
        raise QualityNotProven("E4_BERKSHIRE_2001_BENCHMARK_OR_NO_GUARANTEE_MISSING")
    if not all(x in d2 for x in markers2):
        raise QualityNotProven("E4_BERKSHIRE_2020_PARTNERSHIP_OR_LOSS_CAUTION_MISSING")
    return {
        "schema":"IRE_V166_E4_BUFFETT_FIRST_PARTY_RETROSPECTIVES_CONTEXT_ONLY_V1",
        "official_2001_url":URL_2001,
        "official_2001_body_sha256":sha256(body_2001),
        "official_2020_url":URL_2020,
        "official_2020_body_sha256":sha256(body_2020),
        "official_2020_body_bytes":len(body_2020),
        "official_2020_checked_printed_pages":[10,11],
        "founding_1956_relative_benchmark_and_no_return_promise_attested":True,
        "retrospective_1962_consolidation_and_compensation_threshold_attested":True,
        "permanent_capital_loss_aversion_attested":True,
        "six_percent_is_guaranteed_return":False,
        "actual_1957_original_letter_authenticated":False,
        "video_aggressive_investment_characterization_proven":False,
        "actual_initial_capital_amount_verified":False,
        "entire_partnership_performance_independently_audited":False,
        "source_video_native_v123_status_changed":False,
        "research_knowledge_release_authorized":False,
        "personal_advice_approved":False,
    }
