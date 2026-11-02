"""Bounded, independently fetched candidate-primary-document evidence.

Do not confuse an allowlisted institution domain with issuer certification.
This module deliberately does NOT parse PDFs or execute JavaScript. Unfetched,
unsupported, redirected, private-network, or altered source documents remain
unverified. No previous research documents or conclusions are imported.
"""
from __future__ import annotations

from datetime import datetime,timezone
from html.parser import HTMLParser
import io
import ipaddress
import os
from pathlib import Path
import re
import socket
import urllib.error
import urllib.request
from urllib.parse import urlsplit,urljoin

from .source import require,sha256,text_norm
from .checkpoint import safe_private_directory

# A candidate domain is a network safety *allowlist*, not a legal endorsement.
# All entries must be independently checked against the issuing institution.
CANDIDATE_ISSUER_DOMAINS={
    "bok.or.kr":"BANK_OF_KOREA",
    "law.go.kr":"KR_NATIONAL_LEGISLATION_INFORMATION_CENTER",
    "nps.or.kr":"NATIONAL_PENSION_SERVICE",
    "nts.go.kr":"NATIONAL_TAX_SERVICE",
    "fsc.go.kr":"FINANCIAL_SERVICES_COMMISSION_KR",
    "fss.or.kr":"FINANCIAL_SUPERVISORY_SERVICE_KR",
    "krx.co.kr":"KOREA_EXCHANGE",
    "kofia.or.kr":"KOREA_FINANCIAL_INVESTMENT_ASSOCIATION",
    "kdic.or.kr":"KOREA_DEPOSIT_INSURANCE_CORPORATION",
    "moef.go.kr":"KOREA_MINISTRY_FINANCE",
    "gov.kr":"KOREA_GOVERNMENT_PORTAL",
    "sec.gov":"SEC_US",
    "investor.gov":"SEC_INVESTOR_EDUCATION",
    "irs.gov":"IRS_US",
    "treasury.gov":"US_TREASURY",
    "federalreserve.gov":"US_FED",
    "finra.org":"FINRA_US",
    "oecd.org":"OECD",
    "bis.org":"BIS",
    "imf.org":"IMF",
    "worldbank.org":"WORLD_BANK",
}
MAX_DOCUMENT_BYTES=10_000_000
MAX_EXTRACTED_TEXT=160_000
MAX_MODEL_EXCERPT=22_000

def issuer_for(url: str) -> str | None:
    if not isinstance(url,str) or len(url)>2048:
        return None
    try:
        value=urlsplit(url)
        host=(value.hostname or "").lower().rstrip(".")
        if value.scheme!="https" or not host or (
            value.username is not None or value.password is not None
            or value.port not in (None,443)):
            return None
        if not re.fullmatch(r"[a-z0-9.-]+",host) or ".." in host:
            return None
        if host=="localhost":
            return None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            return None
        for suffix,issuer in CANDIDATE_ISSUER_DOMAINS.items():
            if host==suffix or host.endswith("."+suffix):
                return issuer
        return None
    except ValueError:
        return None


def _check_public_dns(url: str) -> None:
    host=urlsplit(url).hostname
    require(bool(host),"EVIDENCE_HOST_MISSING")
    try:
        records=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    except (OSError,socket.gaierror):
        raise ValueError("EVIDENCE_DNS_UNAVAILABLE") from None
    require(bool(records),"EVIDENCE_DNS_EMPTY")
    for record in records:
        try:
            addr=ipaddress.ip_address(record[4][0])
        except ValueError:
            raise ValueError("EVIDENCE_DNS_INVALID_ADDRESS") from None
        require(addr.is_global,"EVIDENCE_PRIVATE_OR_RESERVED_NETWORK_DENIED")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        return None


def _restricted_get(url: str) -> tuple[bytes,str,str]:
    """Follow at most 3 same-issuer HTTPS redirects; deny cross-site hops."""
    original_issuer=issuer_for(url)
    require(original_issuer is not None,"EVIDENCE_URL_NOT_IN_INSTITUTION_ALLOWLIST")
    opener=urllib.request.build_opener(
        _NoRedirect(),urllib.request.ProxyHandler({}))
    current=url
    for _ in range(4):
        _check_public_dns(current)
        request=urllib.request.Request(current,
            headers={"User-Agent":"IRE-IndependentEvidenceVerifier/0.2",
                     "Accept":"text/html,text/plain,application/pdf;q=0.8",
                     "Accept-Encoding":"identity"},method="GET")
        try:
            with opener.open(request,timeout=20) as response:
                final=response.geturl()
                require(final==current,"EVIDENCE_UNSCREENED_REDIRECT_DENIED")
                mime=response.headers.get("Content-Type","").lower()
                raw=response.read(MAX_DOCUMENT_BYTES+1)
            return raw,mime,current
        except urllib.error.HTTPError as exc:
            if exc.code in (301,302,303,307,308):
                location=exc.headers.get("Location","")
                target=urljoin(current,location)
                require(target!=current and
                        issuer_for(target)==original_issuer,
                        "EVIDENCE_REDIRECT_CROSS_ISSUER_DENIED")
                current=target
                continue
            raise ValueError("EVIDENCE_HTTP_ERROR_"+str(exc.code)) from None
        except (urllib.error.URLError,TimeoutError,OSError):
            raise ValueError("EVIDENCE_NETWORK_UNAVAILABLE") from None
    raise ValueError("EVIDENCE_TOO_MANY_REDIRECTS")

class _VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.hidden=0
        self.skip={"script","style","svg","noscript"}
        self.separator={"p","br","div","section","li","h1","h2","h3",
                        "h4","h5","h6","td","th","tr","article"}

    def handle_starttag(self,tag,attrs):
        if tag in self.skip:
            self.hidden+=1
        if self.hidden==0 and tag in self.separator:
            self.parts.append(" ")

    def handle_endtag(self,tag):
        if tag in self.skip and self.hidden>0:
            self.hidden-=1
        if self.hidden==0 and tag in self.separator:
            self.parts.append(" ")

    def handle_data(self,data):
        if self.hidden==0:
            self.parts.append(data)


def _extract(raw: bytes, content_type: str) -> tuple[str,bool]:
    mime=content_type.split(";",1)[0].strip().lower()
    require(mime in ("text/html","text/plain","application/xhtml+xml",
                     "application/pdf"),
            "EVIDENCE_UNSUPPORTED_DOCUMENT_MIME")
    if mime=="application/pdf":
        require(raw.startswith(b"%PDF-") and len(raw)<=MAX_DOCUMENT_BYTES,
                "EVIDENCE_PDF_MAGIC_OR_SIZE_INVALID")
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("EVIDENCE_PDF_PARSER_UNAVAILABLE") from None
        try:
            reader=PdfReader(io.BytesIO(raw),strict=True)
            require(not reader.is_encrypted and 1<=len(reader.pages)<=200,
                    "EVIDENCE_PDF_ENCRYPTED_OR_PAGE_COUNT_INVALID")
            pieces=[]
            size=0
            for page in reader.pages:
                segment=page.extract_text() or ""
                require(len(segment)<=1_000_000,
                        "EVIDENCE_PDF_PAGE_TEXT_OVERSIZE")
                size+=len(segment)
                pieces.append(segment)
                if size>MAX_EXTRACTED_TEXT:
                    break
            text=text_norm(" ".join(pieces))
            require(len(text)>=20,"EVIDENCE_PDF_SCANNED_OR_EMPTY")
            was_cut=size>MAX_EXTRACTED_TEXT or len(text)>MAX_EXTRACTED_TEXT
            return text[:MAX_EXTRACTED_TEXT],was_cut
        except Exception:
            raise ValueError("EVIDENCE_PDF_READ_FAILED") from None
    charset="utf-8"
    match=re.search(r"\bcharset\s*=\s*[\"']?([\w-]+)",
                    content_type,re.IGNORECASE)
    if match:
        charset=match.group(1).lower()
    require(charset in ("utf-8","utf8","euc-kr","cp949","iso-8859-1"),
            "EVIDENCE_UNSUPPORTED_CHARSET")
    try:
        value=raw.decode(charset,errors="strict")
    except UnicodeError:
        raise ValueError("EVIDENCE_DOCUMENT_DECODE_FAILED") from None
    if mime in ("text/html","application/xhtml+xml"):
        parser=_VisibleHTML()
        try:
            parser.feed(value)
            parser.close()
        except ValueError:
            raise ValueError("EVIDENCE_HTML_PARSING_FAILED") from None
        value=" ".join(parser.parts)
    text=text_norm(value)
    require(len(text)>=20,"EVIDENCE_DOCUMENT_EMPTY_OR_UNREADABLE")
    was_cut=len(text)>MAX_EXTRACTED_TEXT
    return text[:MAX_EXTRACTED_TEXT],was_cut


def independently_fetch_candidate(url: str,read_fn=None,
                                  fetched_at: str | None = None,
                                  private_evidence_dir: str | None = None) -> dict:
    """Live default fetch with injected reader only for synthetic tests.

    read_fn(url) returns exactly (raw bytes, MIME, final HTTPS URL).
    """
    issuer=issuer_for(url)
    require(issuer is not None,"EVIDENCE_URL_NOT_IN_INSTITUTION_ALLOWLIST")
    result=(read_fn(url) if read_fn is not None else _restricted_get(url))
    require(type(result) is tuple and len(result)==3,
            "EVIDENCE_FETCH_RESULT_INVALID")
    raw,mime,final=result
    require(type(raw) is bytes and 0<len(raw)<=MAX_DOCUMENT_BYTES,
            "EVIDENCE_SOURCE_BYTES_INVALID_OR_OVERSIZE")
    require(type(mime) is str and isinstance(final,str) and
            issuer_for(final)==issuer,
            "EVIDENCE_FETCH_REDIRECT_OR_MIME_INVALID")
    visible,truncated=_extract(raw,mime)
    checked_time=fetched_at or datetime.now(timezone.utc).isoformat()
    snapshot=None
    if private_evidence_dir is not None:
        root=safe_private_directory(private_evidence_dir)
        path=root/(sha256(raw)+".official_source")
        if path.exists():
            require(sha256(path.read_bytes())==sha256(raw),
                    "EVIDENCE_PRIVATE_SNAPSHOT_HASH_CHANGED")
        else:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            try:
                with os.fdopen(fd,"wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            except Exception:
                path.unlink(missing_ok=True)
                raise
        snapshot=str(path)
    return {
        "schema":"IRE_INDEPENDENT_DOCUMENT_V1",
        "requested_candidate_url":url,
        "canonical_url":final,
        "same_issuer_redirected":final!=url,
        "issuer_domain_category":issuer,
        "raw_sha256":sha256(raw),
        "raw_byte_size":len(raw),
        "content_type":mime.split(";",1)[0],
        "retrieved_at_utc":checked_time,
        "visible_text":visible,
        "visible_text_sha256":sha256(visible.encode("utf-8")),
        "extracted_text_truncated":truncated,
        "origin_domain_safety_allowlisted":True,
        "actual_publisher_identity_cryptographically_verified":False,
        "effective_date_of_rules_verified":False,
        "independent_financial_fact_approved":False,
        "private_immutable_source_snapshot":snapshot,
        "source_read_mode":"INJECTED_SYNTHETIC_READER" if read_fn
                           else "LIVE_NETWORK_FETCH"
    }


def select_evidence_excerpt(document: dict, claim: dict,
                            max_chars: int = MAX_MODEL_EXCERPT) -> dict:
    """Deterministic claim-specific text excerpts, without inventing quotes."""
    require(document.get("schema")=="IRE_INDEPENDENT_DOCUMENT_V1"
            and type(claim) is dict and type(claim.get("proposition")) is str,
            "EVIDENCE_EXCERPT_SOURCE_INVALID")
    value=document["visible_text"]
    require(type(value) is str and bool(value),"EVIDENCE_TEXT_MISSING")
    require(2000<=max_chars<=MAX_MODEL_EXCERPT,
            "EVIDENCE_EXCERPT_LIMIT_INVALID")
    if len(value)<=max_chars:
        excerpt=value
        offset=0
    else:
        terms=set(re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}|\d+(?:[.,]\d+)*",
                             claim["proposition"].lower()))
        segments=range(0,len(value),max_chars)
        ranked=[]
        for begin in segments:
            sample=value[begin:begin+max_chars]
            low=sample.lower()
            score=sum(1 for t in terms if t in low)
            ranked.append((-score,begin))
        offset=sorted(ranked)[0][1]
        excerpt=value[offset:offset+max_chars]
    return {
        "excerpt":excerpt,
        "excerpt_sha256":sha256(excerpt.encode("utf-8")),
        "offset":offset,
        "excerpt_is_entire_document":len(value)<=max_chars,
        "source_document_sha256":document["raw_sha256"],
        "source_document_text_sha256":document["visible_text_sha256"],
    }